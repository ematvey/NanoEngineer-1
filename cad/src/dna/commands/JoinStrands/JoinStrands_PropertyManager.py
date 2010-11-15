# Copyright 2008 Nanorex, Inc.  See LICENSE file for details. 
"""
JoinStrands_PropertyManager.py

 The JoinStrands_PropertyManager class provides a Property Manager 
    for the B{Join Strands} command on the flyout toolbar in the 
    Build > Dna mode. 

@author: Ninad
@version: $Id: JoinStrands_PropertyManager.py 13122 2008-06-05 22:40:47Z ninadsathaye $
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details.


TODO: as of 2008-02-13:
- Remove 'Cancel' button -- This needs to be supported in transient done-cancel
button code (confirmation_corner)
- methods such as ok_btn_clicked need cleanup in the superclass. This workis 
pending because of some remaining things in GBC cleanup (such as 
NanotubeGenerator etc) 

Ninad 2008-06-04 - 2008-06-05: 
Revised and refactored arrowhead display code and moved part common to both 
Break and JoinStrands PMs into new module BreakOrJoinStrands_PropertyManager
"""

import sys
from PM.PM_GroupBox import PM_GroupBox

from utilities.prefs_constants import joinStrandsCommand_arrowsOnThreePrimeEnds_prefs_key
from utilities.prefs_constants import joinStrandsCommand_arrowsOnFivePrimeEnds_prefs_key 
from utilities.prefs_constants import joinStrandsCommand_useCustomColorForThreePrimeArrowheads_prefs_key 
from utilities.prefs_constants import joinStrandsCommand_dnaStrandThreePrimeArrowheadsCustomColor_prefs_key 
from utilities.prefs_constants import joinStrandsCommand_useCustomColorForFivePrimeArrowheads_prefs_key 
from utilities.prefs_constants import joinStrandsCommand_dnaStrandFivePrimeArrowheadsCustomColor_prefs_key 

from dna.command_support.BreakOrJoinStrands_PropertyManager import BreakOrJoinStrands_PropertyManager

_superclass = BreakOrJoinStrands_PropertyManager
class JoinStrands_PropertyManager( BreakOrJoinStrands_PropertyManager ):
    """
    The JoinStrands_PropertyManager class provides a Property Manager 
    for the B{Join Strands} command on the flyout toolbar in the 
    Build > Dna mode. 

    @ivar title: The title that appears in the property manager header.
    @type title: str

    @ivar pmName: The name of this property manager. This is used to set
                  the name of the PM_Dialog object via setObjectName().
    @type name: str

    @ivar iconPath: The relative path to the PNG file that contains a
                    22 x 22 icon image that appears in the PM header.
    @type iconPath: str
    """

    title         =  "Join Strands"
    pmName        =  title
    iconPath      =  "ui/actions/Command Toolbar/Join_Strands.png"
    
    def __init__( self, parentCommand ):
        """
        Constructor for the property manager.
        """
        
        _superclass.__init__(self, parentCommand)
        if sys.platform == 'darwin':
            leftMouseButtonString = 'mouse button'
        else:
            leftMouseButtonString = 'left mouse button'
            
                
        # Note: 
        msg = ("To join two strands, highlight a 3' arrowhead of one "\
               "strand, hold down the %s and then release it when the cursor "\
               "is over the 5' end of a different strand.") % \
            (leftMouseButtonString)
        
        self.updateMessage(msg)
        
 
    def _addGroupBoxes( self ):
        """
        Add the DNA Property Manager group boxes.
        """                  
        self._displayOptionsGroupBox = PM_GroupBox( self, title = "Display options" )
        self._loadDisplayOptionsGroupBox( self._displayOptionsGroupBox )  
        return
    
    
    #Return varius prefs_keys for arrowhead display options ui elements =======     
    def _prefs_key_arrowsOnThreePrimeEnds(self):
        """
        Return the appropriate KEY of the preference for whether to
        draw arrows on 3' strand ends of PAM DNA.
        """
        return joinStrandsCommand_arrowsOnThreePrimeEnds_prefs_key
    
    def _prefs_key_arrowsOnFivePrimeEnds(self):
        """
        Return the appropriate KEY of the preference for whether to
        draw arrows on 5' strand ends of PAM DNA.
        """
        return joinStrandsCommand_arrowsOnFivePrimeEnds_prefs_key
    
    def _prefs_key_useCustomColorForThreePrimeArrowheads(self):
        """
        Return the appropriate KEY of the preference for whether to use a
        custom color for 3' arrowheads (if they are drawn)
        or for 3' strand end atoms (if arrowheads are not drawn)
        """
        return joinStrandsCommand_useCustomColorForThreePrimeArrowheads_prefs_key
    
    def _prefs_key_useCustomColorForFivePrimeArrowheads(self):
        """
        Return the appropriate KEY of the preference for whether to use a
        custom color for 5' arrowheads (if they are drawn)
        or for 5' strand end atoms (if arrowheads are not drawn).        
        """
        return joinStrandsCommand_useCustomColorForFivePrimeArrowheads_prefs_key
    
    def _prefs_key_dnaStrandThreePrimeArrowheadsCustomColor(self):
        """
        Return the appropriate KEY of the preference for what custom color
        to use when drawing 3' arrowheads (if they are drawn)
        or 3' strand end atoms (if arrowheads are not drawn).
        """
        return joinStrandsCommand_dnaStrandThreePrimeArrowheadsCustomColor_prefs_key
    
    def _prefs_key_dnaStrandFivePrimeArrowheadsCustomColor(self):
        """
        Return the appropriate KEY of the preference for what custom color
        to use when drawing 5' arrowheads (if they are drawn)
        or 5' strand end atoms (if arrowheads are not drawn).
        """
        return joinStrandsCommand_dnaStrandFivePrimeArrowheadsCustomColor_prefs_key
    

    def _addWhatsThisText( self ):
        """
        What's This text for widgets in the DNA Property Manager.  
        """
        pass
                
    def _addToolTipText(self):
        """
        Tool Tip text for widgets in the DNA Property Manager.  
        """
        pass
    
    
    
        
        