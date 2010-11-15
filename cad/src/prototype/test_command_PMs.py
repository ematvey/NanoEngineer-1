# Copyright 2007 Nanorex, Inc.  See LICENSE file for details. 
"""
test_command_PMs.py - property manager classes for test_commands.py.
See that file for more info.

$Id: test_command_PMs.py 11951 2008-03-14 04:44:50Z ericmessick $
"""

from PM.PM_Dialog        import PM_Dialog
from PM.PM_GroupBox      import PM_GroupBox
from PM.PM_DoubleSpinBox import PM_DoubleSpinBox
from PM.PM_ComboBox      import PM_ComboBox

from command_support.GeneratorBaseClass import GeneratorBaseClass

import time

class PM_Dialog_with_example_widgets( PM_Dialog):
    """
    [private] PM_Dialog with some PM widgets common to several examples here
    """
    # NOTE: contains some code copied (and perhaps modified) from AtomGeneratorDialog.py

    # these class constants should be defined by each specific PM subclass
    # (we don't define them here, since we want errors to occur if you don't override them)
    #   title = "title"
    #   pmName = "pm" + title
    #   iconPath = "path-to-some-icon.png"

    #k all needed?
    _sMinCoordinateValue   = -30.0
    _sMaxCoordinateValue   =  30.0
    _sStepCoordinateValue  =  0.1
    _sCoordinateDecimals   =  4
    _sCoordinateUnit       =  'Angstrom'
    _sCoordinateUnits      =  _sCoordinateUnit + 's'
    _sElementSymbolList    =  ["H","O","C","S"]

    def __init__(self):
        PM_Dialog.__init__( self, self.pmName, self.iconPath, self.title )
               
        msg = "Example command created at %s" % time.asctime()
        
        # This causes the "Message" box to be displayed as well.
        self.MessageGroupBox.insertHtmlMessage( msg, setAsDefault = False )
        return

    def _addGroupBoxes(self):
        """
        Add group boxes to this Property Manager.
        """
        self.pmGroupBox1 = PM_GroupBox( self, title =  "Atom Parameters" )
        self._loadGroupBox1(self.pmGroupBox1)
        return
    
    def _loadGroupBox1(self, inPmGroupBox):
        """
        Load widgets into group box 1.
        """

        # User input to specify what type of element/atom to generate
        elementComboBoxItems  =  self._sElementSymbolList
        self.elementComboBox  =  \
            PM_ComboBox( inPmGroupBox,
                         label         =  "Elements :",
                         choices       =  elementComboBoxItems,
                         index         =  0,
                         setAsDefault  =  True,
                         spanWidth     =  False )
        
        # User input to specify x-coordinate 
        # of the generated atom's position.
        self.xCoordinateField  =  \
            PM_DoubleSpinBox( inPmGroupBox,
                              label         =  "x :",
                              value         =  0.0,
                              setAsDefault  =  True,
                              minimum       =  self._sMinCoordinateValue,
                              maximum       =  self._sMaxCoordinateValue,
                              singleStep    =  self._sStepCoordinateValue,
                              decimals      =  self._sCoordinateDecimals,
                              suffix        =  ' ' + self._sCoordinateUnits )
        return
        
    def _addWhatsThisText(self):
        """
        What's This text for some of the widgets in the Property Manager.
        """
        
        self.xCoordinateField.setWhatsThis("<b>x</b><p>: The x-coordinate (up to </p>"
                                           + str( self._sMaxCoordinateValue )
                                           + self._sCoordinateUnits
                                           + ") of the Atom in "
                                           + self._sCoordinateUnits + '.')
    pass # end of class PM_Dialog_with_example_widgets

# ==

class ExampleCommand1_PM( PM_Dialog_with_example_widgets): # these supers are needed (but 'object' is evidently not needed)
    """
    Property Manager for Example Command 1 -- simplest that doesn't use GBC; buttons are noops
    """
    
    # <title> - the title that appears in the property manager header.
    title = "Example Command 1"
    # <pmName> - the name of this property manager. This will be set to
    # the name of the PropMgr (this) object via setObjectName(). ###k used only for debugging??
    pmName = "pm" + title
    # <iconPath> - full path to PNG file that appears in the header.
    iconPath = "ui/actions/Toolbars/Smart/Deposit_Atoms.png" ###e REVISE

    # bruce added these to make it work w/o GBC.
    # (It doesn't need restore_defaults_btn_clicked because PropMgrBaseClass defines that itself.
    #  So does GBC, but to a noop method. So GBC better be inherited *after* PropMgrBaseClass!)
    
    def ok_btn_clicked(self):
        print "ok_btn_clicked, nim except for Done in", self
        self.commandrun.Done()
        pass
    
    def cancel_btn_clicked(self):
        #bruce 070814 bugfix -- renamed from abort_btn_clicked; new method name is needed by PM_Dialog.cancelButtonClicked
        print "cancel_btn_clicked, nim except for Cancel in", self
        self.commandrun.Cancel()
        pass
        
    def preview_btn_clicked(self):
        print "preview_btn_clicked", self
        pass
        
    def __init__(self, win, commandrun = None):
        print "creating", self ####
        self.commandrun = commandrun

        PM_Dialog_with_example_widgets.__init__( self ) ## ok before the next line? @@@
        if 1: # bruce added these, otherwise various AttributeErrors [still true??]
            self.win = win # needed in PropMgrBaseClass.show
            self.pw = win.activePartWindow() # same
        return
    
    pass # end of class ExampleCommand1_PM

class ExampleCommand2_PM( PM_Dialog_with_example_widgets, GeneratorBaseClass):
    """
    Property Manager for Example Command 2 -- simplest that uses GBC; generates a comment (ignores widget values)
    """
    
    title = "Example Command 2"
    pmName = "pm" + title
    iconPath = "ui/actions/Toolbars/Smart/Deposit_Atoms.png" #e REVISE

    # need these, at least to use Done:
    prefix = "Thing2" # for names created by GBC [required when create_name_from_prefix is true (not sure about otherwise)]
    cmdname = "Generate a Thing2" # Undo/history cmdname used by GBC [optional, but affects history messages]
    
    def __init__(self, win, commandrun = None):
        print "creating", self ####
        self.commandrun = commandrun

        PM_Dialog_with_example_widgets.__init__( self )
        GeneratorBaseClass.__init__( self, win)        
        return

    def gather_parameters(self): ###REVIEW: the exception from this gets printed but not as a traceback... 
        return (1,2) ###e not yet grabbed from the widgets

    def build_struct(self, name, params, position):
        """
        ... The return value should be the new structure, i.e. some flavor of a Node,
        which has not yet been added to the model. ...
           By convention ... the new node's name should be set to self.name,
        which the caller will have set to self.prefix appended with a serial number.
        """
        print "build_struct(", self, name, params, position, ")"###
        assert self.name == name # true by test and by examining GBC code
        # ignoring params and position for now
        assy = self.win.assy
        from model.Comment import Comment
        return Comment(assy, name, "comment created at " + time.asctime())

    #e bugs that remain:
    # - widget values not used for creating the thing
    # - preview for comment is not visible except in MT tab or history
    # - restore defaults does nothing useful
    # - whats this button does nothing
    # - when we leave this PM, the PM tab remains, tho it's empty

    def ok_btn_clicked(self):
        print "ok_btn_clicked, doing super then Done (kluge)", self
        GeneratorBaseClass.ok_btn_clicked(self)
        self.commandrun.Done() ###k both commandrun and Done -- and, kluge, instead GBC should call a done method in self.commandrun
        pass
    def cancel_btn_clicked(self):
        #bruce 070814 bugfix -- renamed from abort_btn_clicked; new method name is needed by PM_Dialog.cancelButtonClicked
        print "cancel_btn_clicked, doing super then Done (kluge)", self
        GeneratorBaseClass.cancel_btn_clicked(self)
        self.commandrun.Done()
        pass

    pass # end of class ExampleCommand2_PM

# end
