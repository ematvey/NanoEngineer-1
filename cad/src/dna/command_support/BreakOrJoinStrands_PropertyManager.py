# Copyright 2008 Nanorex, Inc.  See LICENSE file for details. 
"""

@author: Urmi, Ninad
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details.
@version:$Id: BreakOrJoinStrands_PropertyManager.py 13319 2008-07-03 01:24:10Z marksims $

History:
Ninad 2008-06-05: Revised and refactored code in JoinStrands_PropertyManager, 
and moved it to this class.
"""
import sys
from PyQt4.Qt import Qt
from PyQt4.Qt import SIGNAL
import foundation.env as env
from PM.PM_Dialog import PM_Dialog
from widgets.DebugMenuMixin import DebugMenuMixin
from PM.PM_GroupBox import PM_GroupBox
from PM.PM_CheckBox import PM_CheckBox
from PM.PM_ColorComboBox import PM_ColorComboBox

from PM.PM_Constants     import PM_DONE_BUTTON
from PM.PM_Constants     import PM_WHATS_THIS_BUTTON

from utilities.prefs_constants import arrowsOnBackBones_prefs_key
from utilities.prefs_constants import arrowsOnThreePrimeEnds_prefs_key
from utilities.prefs_constants import arrowsOnFivePrimeEnds_prefs_key
from utilities.prefs_constants import useCustomColorForThreePrimeArrowheads_prefs_key
from utilities.prefs_constants import useCustomColorForFivePrimeArrowheads_prefs_key
from utilities.prefs_constants import dnaStrandThreePrimeArrowheadsCustomColor_prefs_key
from utilities.prefs_constants import dnaStrandFivePrimeArrowheadsCustomColor_prefs_key

from widgets.prefs_widgets import connect_checkbox_with_boolean_pref

class BreakOrJoinStrands_PropertyManager(PM_Dialog, DebugMenuMixin):
    
    def __init__( self, parentCommand ):
        """
        Constructor for the property manager.
        """

        self.parentMode = parentCommand
        self.w = self.parentMode.w
        self.win = self.parentMode.w
        self.pw = self.parentMode.pw        
        self.o = self.win.glpane             
                        
        PM_Dialog.__init__(self, self.pmName, self.iconPath, self.title)
        
        DebugMenuMixin._init1( self )

        self.showTopRowButtons( PM_DONE_BUTTON | \
                                PM_WHATS_THIS_BUTTON)
        return
    
    def connect_or_disconnect_signals(self, isConnect):
        """
        Connect or disconnect widget signals sent to their slot methods.
        This can be overridden in subclasses. By default it does nothing.
        @param isConnect: If True the widget will send the signals to the slot 
                          method. 
        @type  isConnect: boolean
        """
        if isConnect:
            change_connect = self.win.connect
        else:
            change_connect = self.win.disconnect 
        
        # DNA Strand arrowhead display options signal-slot connections.
               
                   
        self._connect_checkboxes_to_global_prefs_keys(isConnect)    
        
        change_connect(self.fivePrimeEndColorChooser,
                       SIGNAL("editingFinished()"), 
                       self.chooseCustomColorOnFivePrimeEnds)
        
        change_connect(self.threePrimeEndColorChooser,
                       SIGNAL("editingFinished()"), 
                       self.chooseCustomColorOnThreePrimeEnds)
        
        change_connect(self.strandFivePrimeArrowheadsCustomColorCheckBox,
                       SIGNAL("toggled(bool)"),
                       self.allowChoosingColorsOnFivePrimeEnd)
        
        change_connect(self.strandThreePrimeArrowheadsCustomColorCheckBox,
                       SIGNAL("toggled(bool)"),
                       self.allowChoosingColorsOnThreePrimeEnd)
        return
    
    def show(self):
        """
        Shows the Property Manager. Overrides PM_Dialog.show.
        """
        PM_Dialog.show(self)        
        self.connect_or_disconnect_signals(isConnect = True)    
        return
                
    def close(self):
        """
        Closes the Property Manager. Overrides PM_Dialog.close.
        """
        # this is important since these pref keys are used in other command modes 
        # as well and we do not want to see the 5' end arrow in Inset DNA mode       
        
        self.connect_or_disconnect_signals(False)        
        PM_Dialog.close(self)
        
    def _connect_checkboxes_to_global_prefs_keys(self, isConnect = True):
        """
        #doc
        """
        if not isConnect:
            return       
        
        #ORDER of items in tuples checkboxes and prefs_keys is IMPORTANT!
        checkboxes = (
            self.arrowsOnThreePrimeEnds_checkBox,
            self.arrowsOnFivePrimeEnds_checkBox,
            self.strandThreePrimeArrowheadsCustomColorCheckBox,
            self.strandFivePrimeArrowheadsCustomColorCheckBox,
            self.arrowsOnBackBones_checkBox)
        
        prefs_keys = (
            self._prefs_key_arrowsOnThreePrimeEnds(),
            self._prefs_key_arrowsOnFivePrimeEnds(),
            self._prefs_key_useCustomColorForThreePrimeArrowheads(),
            self._prefs_key_useCustomColorForFivePrimeArrowheads(), 
            arrowsOnBackBones_prefs_key)
        
        for checkbox, prefs_key in zip(checkboxes, prefs_keys):
            connect_checkbox_with_boolean_pref(checkbox, prefs_key)
        
        return
    
    def ok_btn_clicked(self):
        """
        Slot for the OK button
        """      
        self.win.toolsDone()
        return
        
    #Load various widgets ====================
        
    def _loadDisplayOptionsGroupBox(self, pmGroupBox):
        """
        Load widgets in the display options groupbox
        """   
        title = "Arrowhead prefs in %s:"%self.parentMode.featurename
        self._arrowheadPrefsGroupBox = PM_GroupBox(
            pmGroupBox, 
            title = title)
        #load all the options
        self._load3PrimeEndArrowAndCustomColor(self._arrowheadPrefsGroupBox)
        self._load5PrimeEndArrowAndCustomColor(self._arrowheadPrefsGroupBox)
        self._loadArrowOnBackBone(pmGroupBox)
        return

    def _load3PrimeEndArrowAndCustomColor(self, pmGroupBox):
        """
        Loads 3' end arrow head and custom color checkbox and color chooser dialog
        """
        self.pmGroupBox3 = PM_GroupBox(pmGroupBox, title = "3' end:")
        
        self.arrowsOnThreePrimeEnds_checkBox = PM_CheckBox( self.pmGroupBox3,
                                                            text         = "Show arrowhead",
                                                            widgetColumn  = 0,
                                                            setAsDefault = True,
                                                            spanWidth = True )
        
        prefs_key = self._prefs_key_arrowsOnThreePrimeEnds()
        if env.prefs[prefs_key]:
            self.arrowsOnThreePrimeEnds_checkBox.setCheckState(Qt.Checked) 
        else:
            self.arrowsOnThreePrimeEnds_checkBox.setCheckState(Qt.Unchecked)
            
        self.strandThreePrimeArrowheadsCustomColorCheckBox = PM_CheckBox( self.pmGroupBox3,
                                                            text         = "Display custom color",
                                                            widgetColumn  = 0,
                                                            setAsDefault = True,
                                                            spanWidth = True)
        prefs_key = self._prefs_key_dnaStrandThreePrimeArrowheadsCustomColor()
        self.threePrimeEndColorChooser = \
            PM_ColorComboBox(self.pmGroupBox3,
                             color      = env.prefs[prefs_key])
        
        prefs_key = self._prefs_key_useCustomColorForThreePrimeArrowheads()
        if env.prefs[prefs_key]:
            self.strandThreePrimeArrowheadsCustomColorCheckBox.setCheckState(Qt.Checked) 
            self.threePrimeEndColorChooser.show()
        else:
            self.strandThreePrimeArrowheadsCustomColorCheckBox.setCheckState(Qt.Unchecked)
            self.threePrimeEndColorChooser.hide()
                    
        return 

    def _load5PrimeEndArrowAndCustomColor(self, pmGroupBox):
        """
        Loads 5' end custom color checkbox and color chooser dialog
        """
        self.pmGroupBox2 = PM_GroupBox(pmGroupBox, title = "5' end:")
        self.arrowsOnFivePrimeEnds_checkBox = PM_CheckBox( self.pmGroupBox2,
                                                            text         = "Show arrowhead",
                                                            widgetColumn  = 0,
                                                            setAsDefault = True,
                                                            spanWidth = True
                                                            )
        
        prefs_key = self._prefs_key_arrowsOnFivePrimeEnds()
        if env.prefs[prefs_key]:
            self.arrowsOnFivePrimeEnds_checkBox.setCheckState(Qt.Checked) 
        else:
            self.arrowsOnFivePrimeEnds_checkBox.setCheckState(Qt.Unchecked)
            
        self.strandFivePrimeArrowheadsCustomColorCheckBox = PM_CheckBox( self.pmGroupBox2,
                                                            text         = "Display custom color",
                                                            widgetColumn  = 0,
                                                            setAsDefault = True,
                                                            spanWidth = True )
        
        prefs_key = self._prefs_key_dnaStrandFivePrimeArrowheadsCustomColor()        
        self.fivePrimeEndColorChooser = \
            PM_ColorComboBox(self.pmGroupBox2,
                             color      = env.prefs[prefs_key]
                             )
        
        prefs_key = self._prefs_key_useCustomColorForFivePrimeArrowheads()
        if env.prefs[prefs_key]:
            self.strandFivePrimeArrowheadsCustomColorCheckBox.setCheckState(Qt.Checked) 
            self.fivePrimeEndColorChooser.show()
        else:
            self.strandFivePrimeArrowheadsCustomColorCheckBox.setCheckState(Qt.Unchecked)
            self.fivePrimeEndColorChooser.hide()
        
        return 

    def _loadArrowOnBackBone(self, pmGroupBox):
        """
        Loads Arrow on the backbone checkbox
        """
        self.pmGroupBox4 = PM_GroupBox(pmGroupBox, title = "Global preference:")
        self.arrowsOnBackBones_checkBox = PM_CheckBox( self.pmGroupBox4,
                                                       text         = "Show arrows on back bones",
                                                       widgetColumn  = 0,
                                                       setAsDefault = True,
                                                       spanWidth = True
                                                       )
        
        prefs_key = arrowsOnBackBones_prefs_key
        if env.prefs[prefs_key] == True:
            self.arrowsOnBackBones_checkBox.setCheckState(Qt.Checked) 
        else:
            self.arrowsOnBackBones_checkBox.setCheckState(Qt.Unchecked)
        return
            
    def allowChoosingColorsOnFivePrimeEnd(self, state):
        """
        Show or hide color chooser based on the 
        strandFivePrimeArrowheadsCustomColorCheckBox's state
        """
        if self.strandFivePrimeArrowheadsCustomColorCheckBox.isChecked():
            self.fivePrimeEndColorChooser.show()
        else:
            self.fivePrimeEndColorChooser.hide()
        return
    
    def allowChoosingColorsOnThreePrimeEnd(self, state):
        """
        Show or hide color chooser based on the 
        strandThreePrimeArrowheadsCustomColorCheckBox's state
        """
        if self.strandThreePrimeArrowheadsCustomColorCheckBox.isChecked():
            self.threePrimeEndColorChooser.show()
        else:
            self.threePrimeEndColorChooser.hide()
        return
    
    def chooseCustomColorOnThreePrimeEnds(self):
        """
        Choose custom color for 3' ends
        """
        color = self.threePrimeEndColorChooser.getColor()
        prefs_key = self._prefs_key_dnaStrandThreePrimeArrowheadsCustomColor()
        env.prefs[prefs_key] = color
        self.win.glpane.gl_update() 
        return
       
    def chooseCustomColorOnFivePrimeEnds(self):
        """
        Choose custom color for 5' ends
        """
        color = self.fivePrimeEndColorChooser.getColor()
        prefs_key = self._prefs_key_dnaStrandFivePrimeArrowheadsCustomColor()
        env.prefs[prefs_key] = color
        self.win.glpane.gl_update() 
        return
    
    #Return varius prefs_keys for arrowhead display options ui elements =======     
    def _prefs_key_arrowsOnThreePrimeEnds(self):
        """
        Return the appropriate KEY of the preference for whether to
        draw arrows on 3' strand ends of PAM DNA.
        """
        return arrowsOnThreePrimeEnds_prefs_key
    
    def _prefs_key_arrowsOnFivePrimeEnds(self):
        """
        Return the appropriate KEY of the preference for whether to
        draw arrows on 5' strand ends of PAM DNA.
        """
        return arrowsOnFivePrimeEnds_prefs_key
    
    def _prefs_key_useCustomColorForThreePrimeArrowheads(self):
        """
        Return the appropriate KEY of the preference for whether to use a
        custom color for 3' arrowheads (if they are drawn)
        or for 3' strand end atoms (if arrowheads are not drawn)
        """
        return useCustomColorForThreePrimeArrowheads_prefs_key
    
    def _prefs_key_useCustomColorForFivePrimeArrowheads(self):
        """
        Return the appropriate KEY of the preference for whether to use a
        custom color for 5' arrowheads (if they are drawn)
        or for 5' strand end atoms (if arrowheads are not drawn).        
        """
        return useCustomColorForFivePrimeArrowheads_prefs_key
    
    def _prefs_key_dnaStrandThreePrimeArrowheadsCustomColor(self):
        """
        Return the appropriate KEY of the preference for what custom color
        to use when drawing 3' arrowheads (if they are drawn)
        or 3' strand end atoms (if arrowheads are not drawn).
        """
        return dnaStrandThreePrimeArrowheadsCustomColor_prefs_key
    
    def _prefs_key_dnaStrandFivePrimeArrowheadsCustomColor(self):
        """
        Return the appropriate KEY of the preference for what custom color
        to use when drawing 5' arrowheads (if they are drawn)
        or 5' strand end atoms (if arrowheads are not drawn).
        """
        return dnaStrandFivePrimeArrowheadsCustomColor_prefs_key
    
