# Copyright 2007-2008 Nanorex, Inc.  See LICENSE file for details. 
"""
BuildNanotube_PropertyManager.py

@author: Ninad, Mark
@version: $Id: BuildNanotube_PropertyManager.py 14404 2008-10-02 19:51:44Z ninadsathaye $
@copyright: 2007-2008 Nanorex, Inc.  See LICENSE file for details.

History:
Ninad 2008-01-11: Created


TODO: as of 2008-01-11
- Needs more documentation and the file is subjected to heavy revision. 
This is an initial implementation of default Cnt edit mode.
- Methods such as callback_addSegments might be renamed.
- DEPRECATE THE self.sequenceEditor. (that code has been commented out) 
   see a comment in self,__init__
BUGS:
- Has bugs such as -- Flyout toolbar doesn't get updated when you return to 
  BuildNanotube_EditCommand from a a temporary command. 
- Just entering and leaving BuildNanotube_EditCommand creates an empty NanotubeGroup
"""
from utilities import debug_flags
from utilities.debug import print_compact_stack

from PyQt4.Qt import SIGNAL
from PyQt4.Qt import QString

from PM.PM_GroupBox      import PM_GroupBox
from PM.PM_PushButton    import PM_PushButton
from PM.PM_SelectionListWidget import PM_SelectionListWidget
from command_support.EditCommand_PM import EditCommand_PM

from PM.PM_Constants     import PM_DONE_BUTTON
from PM.PM_Constants     import PM_WHATS_THIS_BUTTON
from PM.PM_Constants     import PM_CANCEL_BUTTON
from PM.PM_Colors        import pmReferencesListWidgetColor
from utilities.Comparison import same_vals
from cnt.model.NanotubeSegment import NanotubeSegment

class BuildNanotube_PropertyManager(EditCommand_PM):
    """
    The BuildNanotube_PropertyManager class provides a Property Manager 
    for the B{Build > CNT } command.

    @ivar title: The title that appears in the property manager header.
    @type title: str

    @ivar pmName: The name of this property manager. This is used to set
                  the name of the PM_Dialog object via setObjectName().
    @type name: str

    @ivar iconPath: The relative path to the PNG file that contains a
                    22 x 22 icon image that appears in the PM header.
    @type iconPath: str
    """

    title         =  "Build Nanotube"
    pmName        =  title
    iconPath      =  "ui/actions/Tools/Build Structures/Nanotube.png"

    def __init__( self, command ):
        """
        Constructor for the Build Nanotube property manager.
        """
        
        #For self._update_UI_* check
        self._previousSelectionParams = None        
        self._previousStructureParams = None
        
        self._previous_model_change_indicator = None
                
        #see self.connect_or_disconnect_signals for comment about this flag
        self.isAlreadyConnected = False
        self.isAlreadyDisconnected = False
        
        self.sequenceEditor = None              
        
        EditCommand_PM.__init__( self, command)

        self.showTopRowButtons( PM_DONE_BUTTON | \
                                PM_WHATS_THIS_BUTTON)
    
    def connect_or_disconnect_signals(self, isConnect):
        """
        Connect or disconnect widget signals sent to their slot methods.
        This can be overridden in subclasses. By default it does nothing.
        @param isConnect: If True the widget will send the signals to the slot 
                          method. 
        @type  isConnect: boolean
        """
        #TODO: This is a temporary fix for a bug. When you invoke a temporary mode 
        # entering such a temporary mode keeps the signals of 
        #PM from the previous mode connected (
        #but while exiting that temporary mode and reentering the 
        #previous mode, it atucally reconnects the signal! This gives rise to 
        #lots  of bugs. This needs more general fix in Temporary mode API. 
        # -- Ninad 2008-01-09 (similar comment exists in MovePropertyManager.py
                
        if isConnect and self.isAlreadyConnected:
            if debug_flags.atom_debug:
                print_compact_stack("warning: attempt to connect widgets"\
                                    "in this PM that are already connected." )
            return 
        
        if not isConnect and self.isAlreadyDisconnected:
            if debug_flags.atom_debug:
                print_compact_stack("warning: attempt to disconnect widgets"\
                                    "in this PM that are already disconnected.")
            return
        
        self.isAlreadyConnected = isConnect
        self.isAlreadyDisconnected = not isConnect
        
        if isConnect:
            change_connect = self.win.connect     
        else:
            change_connect = self.win.disconnect 
        
        self.segmentListWidget.connect_or_disconnect_signals(isConnect)
        
        change_connect(self.editSegmentPropertiesButton,
                      SIGNAL("clicked()"),
                      self._editNanotubeSegment)
    
    def enable_or_disable_gui_actions(self, bool_enable = False):
        """
        Enable or disable some gui actions when this property manager is 
        opened or closed, depending on the bool_enable. 
        
        """
        #TODO: This is bad. It would have been much better to enable/disable 
        #gui actions using a API method in command/commandSequencer which gets 
        #called when you enter another command exiting or suspending the 
        #previous one. . At present. it doesn't exist (first needs cleanup in 
        #command/command sequencer (Done and other methods._)-- Ninad 2008-01-09
        if hasattr(self.command, 'flyoutToolbar') and \
           self.command.flyoutToolbar:            
            self.command.flyoutToolbar.exitModeAction.setEnabled(not bool_enable)
            
    #New command API method -- implemented on 2008-08-27
    def _update_UI_do_updates(self):
        """
        Overrides superclass method. 
        
        @see: Command_PropertyManager._update_UI_do_updates() for documentation        
        @see: self._currentStructureParams()
        """  
        currentSelectionParams = self._currentSelectionParams() 
        
        currentStructParams = self._currentStructureParams()
        
        selection_params_unchanged = same_vals(currentSelectionParams,
                                               self._previousSelectionParams)
        
        structure_params_unchanged = same_vals(currentStructParams,
                                               self._previousStructureParams)
        
        
        if selection_params_unchanged and structure_params_unchanged:
            #This second condition above fixes bug 2888
            return
        
        if not selection_params_unchanged and structure_params_unchanged:        
            self._previousSelectionParams = currentSelectionParams            
            selectedSegments = currentSelectionParams
            
            self.segmentListWidget.updateSelection(selectedSegments)
                    
            if len(selectedSegments) == 1:
                self.editSegmentPropertiesButton.setEnabled(True)
            else:
                self.editSegmentPropertiesButton.setEnabled(False)
                        
        #See self._currentStructureParams()
        if not structure_params_unchanged:
            self._previousStructureParams = currentStructParams
            #Update the list widget 
            self.updateListWidgets() 
            
                      
    def _currentSelectionParams(self):
        """
        Returns a tuple containing current selection parameters. These 
        parameters are then used to decide whether updating widgets
        in this property manager is needed when L{self._update_UI_do_updates()}
        method is called.
        
        @return: A tuple that contains following selection parameters
                   - Total number of selected atoms (int)
                   - Selected Atom if a single atom is selected, else None
                   - Position vector of the single selected atom or None
        @rtype:  tuple
        
        @NOTE: The method may be renamed in future. 
        It's possible that there are other groupboxes in the PM that need to be 
        updated when something changes in the glpane.        
        """
         
        selectedSegments = []
        selectedSegments = self.win.assy.getSelectedNanotubeSegments()
        ##if self.command is not None and self.command.hasValidStructure():
            ##selectedSegments = self.command.struct.getSelectedSegments()             
                    
        return (selectedSegments)
    
    def _currentStructureParams(self):
        """
        Return current structure parameters of interest to self._update_UI_*. 
        Right now it only returns the number of nanotube segments in the part
        (or None). 
        
        @ATTENTION: Is this a sufficient check? For optimization, it doesn't
        compare each and every nanotube in that list with a previously stored 
        set of nanotubes. In case of bugs, this method should return the list 
        itself instead of 'len(list)
        
        @see: self._update_UI_do_updates()
        """        
        params = None
        part = self.command.assy.part
        nanotubes = part.get_topmost_subnodes_of_class(self.command.assy.NanotubeSegment)
        params = len(nanotubes)
        return params 
    
    
    def close(self):
        """
        Closes the Property Manager. Overrides EditCommand_PM.close()
        """
        #Clear tags, if any, due to the selection in the self.strandListWidget.        
        if self.segmentListWidget:
            self.segmentListWidget.clear()
                   
        EditCommand_PM.close(self)
    
    def show(self):
        """
        Show this PM 
        As of 2007-11-20, it also shows the Sequence Editor widget and hides 
        the history widget. This implementation may change in the near future
        """
        EditCommand_PM.show(self)             
        self.updateMessage("Use appropriate command in the command "\
                           "toolbar to create or modify a CNT Object"\
                           "<br>" )
        
    
    def _editNanotubeSegment(self):
        """
        Edit the Nanotube segment. If multiple segments are selected, it 
        edits the first segment in the MT order which is selected
        """
        selectedSegments = self.win.assy.getSelectedNanotubeSegments()
        if len(selectedSegments) == 1:
            selectedSegments[0].edit()
        #Earlier implementation which used the segments in the 
        #'current Nanotube Group'. Deprecated as of 2008-05-05
        ##if self.command is not None and self.command.hasValidStructure(): 
            ##selectedSegments = self.command.struct.getSelectedSegments()
            ##if len(selectedSegments) == 1:
                ##selectedSegments[0].edit()
            
    def updateListWidgets(self):
        """
        Update the Cnt segment list widget in this property manager
        @see: self.updateSegmentListWidgets
        """
        self.updateSegmentListWidget()
        
    def updateSegmentListWidget(self):
        """
        Update the list of segments shown in the segments list widget
        @see: self.updateListWidgets, self.updateStrandListWidget
        """
        
        segmentList = []
         
        def func(node):
            if isinstance(node, NanotubeSegment):
                segmentList.append(node)    
                    
        self.win.assy.part.topnode.apply2all(func)
        self.segmentListWidget.insertItems(
            row = 0,
            items = segmentList)

            
    def _addGroupBoxes( self ):
        """
        Add the CNT Property Manager group boxes.
        """        
        #Unused 'References List Box' to be revided. (just commented out for the
        #time being. 
        ##self._pmGroupBox1 = PM_GroupBox( self, title = "Reference Plane" )
        ##self._loadGroupBox1( self._pmGroupBox1 )
                
        self._pmGroupBox2 = PM_GroupBox( self, title = "CNT Segments" )
        self._loadGroupBox2( self._pmGroupBox2 )
        
        
    def _loadGroupBox1(self, pmGroupBox):
        """
        load widgets in groupbox1
        """
        self.referencePlaneListWidget = PM_SelectionListWidget(
            pmGroupBox,
            self.win,
            label = "",
            color = pmReferencesListWidgetColor,
            heightByRows = 2)
        
    def _loadGroupBox2(self, pmGroupBox):
        """
        load widgets in groupbox3
        """
        
        self.segmentListWidget = PM_SelectionListWidget(pmGroupBox,
                                                       self.win,
                                                       label = "",
                                                       heightByRows = 12)
        self.segmentListWidget.setObjectName('Segment_list_widget')
        self.segmentListWidget.setTagInstruction('PICK_ITEM_IN_GLPANE')
        
    
        self.editSegmentPropertiesButton = PM_PushButton( 
            pmGroupBox,
            label = "",
            text  = "Edit Properties..." )
        self.editSegmentPropertiesButton.setEnabled(False)
    
 
    def _addWhatsThisText( self ):
        """
        What's This text for widgets in the CNT Property Manager.  
        """
        pass
                
    def _addToolTipText(self):
        """
        Tool Tip text for widgets in the CNT Property Manager.  
        """
        pass
