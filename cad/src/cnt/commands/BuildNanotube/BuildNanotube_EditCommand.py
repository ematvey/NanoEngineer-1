# Copyright 2007-2008 Nanorex, Inc.  See LICENSE file for details. 
"""
BuildNanotube_EditCommand.py

@author: Ninad
@version: $Id: BuildNanotube_EditCommand.py 13383 2008-07-10 17:30:29Z ninadsathaye $
@copyright: 2007-2008 Nanorex, Inc.  See LICENSE file for details.

History:
Ninad 2008-01-11: Created


TODO: as of 2008-01-11
- Needs more documentation and the file is subjected to heavy revision. 
This is an initial implementation of default Cnt edit mode.

BUGS:
- Has bugs such as -- Flyout toolbar doesn't get updated when you return to 
  BuildNanotube_EditCommand from a a temporary command. 
- Just entering and leaving BuildNanotube_EditCommand creates an empty NanotubeGroup
"""


from command_support.EditCommand import EditCommand
from cnt.model.NanotubeGroup import NanotubeGroup
from utilities.Log  import greenmsg
from command_support.GeneratorBaseClass import PluginBug, UserError

from utilities.constants import gensym

from ne1_ui.toolbars.Ui_NanotubeFlyout import NanotubeFlyout

from model.chem import Atom 
from model.chunk import Chunk
from model.bonds import Bond

##from SelectChunks_GraphicsMode import SelectChunks_GraphicsMode

from cnt.commands.BuildNanotube.BuildNanotube_GraphicsMode import BuildNanotube_GraphicsMode

class BuildNanotube_EditCommand(EditCommand):
    """
    BuildNanotube_EditCommand provides a convenient way to edit or create
    a NanotubeGroup object     
    """
    cmd              =  greenmsg("Build Nanotube: ")
    sponsor_keyword  =  'Nanotube'
    prefix           =  'NanotubeGroup' # used for gensym
    cmdname          = "Build Nanotube"
    commandName       = 'BUILD_NANOTUBE'
    featurename       = 'Build_Nanotube'

    GraphicsMode_class = BuildNanotube_GraphicsMode

    command_should_resume_prevMode = False
    command_has_its_own_gui = True
    command_can_be_suspended = True

    # Generators for DNA, nanotubes and graphene have their MT name 
    # generated (in GeneratorBaseClass) from the prefix.
    create_name_from_prefix  =  True 

    #The following class constant is used in creating dynamic menu items (using self.makeMenus)
    #if this flag is not defined, the menu doesn't get created
    #or use of self.graphicsMode in self.makeMenus throws errors. 
    #See also other examples of its use in older Commands such as 
    #BuildAtoms_Command (earlier depositmode) 
    call_makeMenus_for_each_event = True    

    def __init__(self, commandSequencer, struct = None):
        """
        Constructor for BuildNanotube_EditCommand
        """

        EditCommand.__init__(self, commandSequencer)
        self.struct = struct


    def init_gui(self):
        """
        Do changes to the GUI while entering this command. This includes opening 
        the property manager, updating the command toolbar , connecting widget 
        slots (if any) etc. Note: The slot connection in property manager and 
        command toolbar is handled in those classes. 

        Called once each time the command is entered; should be called only 
        by code in modes.py

        @see: L{self.restore_gui}
        """
        EditCommand.init_gui(self)    

        if self.flyoutToolbar is None:
            self.flyoutToolbar = NanotubeFlyout(self.win, self.propMgr)

        self.flyoutToolbar.activateFlyoutToolbar()

    def resume_gui(self):
        """
        Called when this command, that was suspended earlier, is being resumed. 
        The temporary command (which was entered by suspending this command)
        might have made some changes to the model which need to be reflected 
        while resuming command. 

        Example: A user enters BreakStrands_Command by suspending 
        BuildNanotube_EditCommand, then breaks a few strands, thereby creating new 
        strand chunks. Now when the user returns to the BuildNanotube_EditCommand, 
        the command's property manager needs to update the list of strands 
        because of the changes done while in BreakStrands_Command.  
        @see: Command.resume_gui
        @see: Command._enterMode where this method is called.
        """
        #NOTE: Doing command toolbar updates in this method doesn't alwayswork.
        #consider this situation : You are in a) BuildNanotube_EditCommand, then you 
        #b) enter CntDuplex_EditCommand(i.e. Cnt line) and from this temporary 
        #command, you directly c) enter BreakStrands_Command 
        #-- During b to c, 1) it first exits (b) , 2) resumes (a) 
        #and then 3)enters (c)
        #This method is called during operation #2 and any changes to flyout 
        #toolbar are reset during #3  --- Ninad 2008-01-14
        if self.propMgr:
            self.propMgr.updateListWidgets()        

        if self.flyoutToolbar:
            self.flyoutToolbar.resetStateOfActions()


    def restore_gui(self):
        """
        Do changes to the GUI while exiting this command. This includes closing 
        this mode's property manager, updating the command toolbar ,
        Note: The slot connection/disconnection in property manager and 
        command toolbar is handled in those classes.
        @see: L{self.init_gui}
        """
        EditCommand.restore_gui(self)
        if self.flyoutToolbar:
            self.flyoutToolbar.deActivateFlyoutToolbar()

    def StateDone(self):   
        """
        @see: Command.StateDone 
        """
        return None

    def StateCancel(self):     
        """
        @see Command.StateCancel
        """
        return None

    def runCommand(self):
        """
        Overrides EditCommand.runCommand
        """
        self.struct = None     
        self.existingStructForEditing = False
        self.propMgr.updateListWidgets()

    def keep_empty_group(self, group):
        """
        Returns True if the empty group should not be automatically deleted. 
        otherwise returns False. The default implementation always returns 
        False. Subclasses should override this method if it needs to keep the
        empty group for some reasons. Note that this method will only get called
        when a group has a class constant autdelete_when_empty set to True. 
        (and as of 2008-03-06, it is proposed that cnt_updater calls this method
        when needed. 
        @see: Command.keep_empty_group() which is overridden here. 
        """

        bool_keep = EditCommand.keep_empty_group(self, group)

        if not bool_keep:     
            if group is self.struct:
                bool_keep = True

        return bool_keep

    def create_and_or_show_PM_if_wanted(self, showPropMgr = True):
        """
        Create the property manager object if one doesn't already exist 
        and then show the propMgr if wanted by the user. 
        @param showPropMgr: If True, show the property manager 
        @type showPropMgr: boolean
        """
        EditCommand.create_and_or_show_PM_if_wanted(
            self,
            showPropMgr = showPropMgr)

        self.propMgr.updateMessage("Use appropriate command in the command "\
                                   "toolbar to create or modify a CNT Object"\
                                   "<br>"                                   
                               )

    def createStructure(self, showPropMgr = True):
        """
        Overrides superclass method. It doesn't do anything for this type
        of editcommand
        """

        self.preview_or_finalize_structure(previewing = True)


    def editStructure(self, struct = None):
        """
        Overrides EditCommand.editStructure method. Provides a way to edit an 
        existing structure. This implements a topLevel command that the client
        can execute to edit an existing object(i.e. self.struct) that it wants.

        Example: If its a plane edit controller, this method will be used to 
                edit an object of class Plane. 

        This method also creates a propMgr objects if it doesn't exist and 
        shows this property manager 

        @see: L{self.createStructure} (another top level command that 
              facilitates creation of a model object created by this 
              editCommand
        @see: L{Plane.edit} and L{Plane_EditCommand._createPropMgrObject} 
        """

        if struct is not None:
            #Should we always unpick the structure while editing it? 
            #Makes sense for editing a Cnt. If this is problematic, the 
            #following should be done in the subclasses that need this.
            if hasattr(struct, 'picked') and struct.picked:
                struct.unpick()

        EditCommand.editStructure(self, struct) 


    def _getStructureType(self):
        """
        Returns the type of the structure this editCommand supports. 
        This is used in isinstance test. 
        @see: EditCommand._getStructureType() 
        """
        return self.win.assy.NanotubeGroup


    def _createPropMgrObject(self):
        """
        Creates a property manager  object (that defines UI things) for this 
        editCommand. 
        """
        assert not self.propMgr        
        propMgr = self.win.createBuildNanotubePropMgr_if_needed(self)
        return propMgr


    def _createStructure(self):
        """
        creates and returns the structure (in this case a L{Group} object that 
        contains the CNT axis chunks. 
        @return : group containing that contains the CNT axis chunks.
        @rtype: L{Group}  
        @note: This needs to return a CNT object once that model is implemented        
        """

        # self.name needed for done message
        if self.create_name_from_prefix:
            # create a new name
            name = self.name = gensym(self.prefix, self.win.assy) # (in _build_struct)
            self._gensym_data_for_reusing_name = (self.prefix, name)
        else:
            # use externally created name
            self._gensym_data_for_reusing_name = None
                # (can't reuse name in this case -- not sure what prefix it was
                #  made with)
            name = self.name


        # Create the model tree group node. 
        # Make sure that the 'topnode'  of this part is a Group (under which the
        # DNa group will be placed), if the topnode is not a group, make it a
        # a 'Group' (applicable to Clipboard parts).See part.py
        # --Part.ensure_toplevel_group method. This is an important line
        # and it fixes bug 2585
        self.win.assy.part.ensure_toplevel_group()

        cntGroup = NanotubeGroup(self.name, 
                                 self.win.assy,
                                 self.win.assy.part.topnode,
                                 editCommand = self)
        try:

            self.win.assy.place_new_geometry(cntGroup)

            return cntGroup

        except (PluginBug, UserError):
            # Why do we need UserError here? Mark 2007-08-28
            cntGroup.kill()
            raise PluginBug("Internal error while trying to create CNT.")


    def _gatherParameters(self):
        """
        Return the parameters needed to build this structure

        @return: A list of all NanotubeSegments present withing the self.struct 
                 (which is a cnt group) or None if self.structure doesn't exist
        @rtype:  tuple
        """       

        #Passing the segmentList as a parameter is not implemented
        ##if self.struct:
            ##segmentList = []
            ##for segment in self.struct.members:
                ##if isinstance(segment, NanotubeSegment):
                    ##segmentList.append(segment)

            ##if segmentList:
                ##return (segmentList)

        return None               


    def _modifyStructure(self, params):
        """
        Modify the structure based on the parameters specified. 
        Overrides EditCommand._modifystructure. This method removes the old 
        structure and creates a new one using self._createStructure. This 
        was needed for the structures like this (Cnt, Nanotube etc) . .
        See more comments in the method.
        """    
        assert self.struct
        # parameters have changed, update existing structure
        self._revertNumber()

        # self.name needed for done message
        if self.create_name_from_prefix:
            # create a new name
            name = self.name = gensym(self.prefix, self.win.assy) # (in _build_struct)
            self._gensym_data_for_reusing_name = (self.prefix, name)
        else:
            # use externally created name
            self._gensym_data_for_reusing_name = None
                # (can't reuse name in this case -- not sure what prefix it was
                #  made with)
            name = self.name

        #@NOTE: Unlike editcommands such as Plane_EditCommand, this 
        #editCommand actually removes the structure and creates a new one 
        #when its modified. We don't yet know if the CNT object model 
        # will solve this problem. (i.e. reusing the object and just modifying
        #its attributes.  Till that time, we'll continue to use 
        #what the old GeneratorBaseClass use to do ..i.e. remove the item and 
        # create a new one  -- Ninad 2007-10-24
        self._removeStructure()

        self.previousParams = params        

        self.struct = self._createStructure()            
        return 

    def _finalizeStructure(self):
        """
        Overrides EditCommand._finalizeStructure. 
        This method also makes sure that the NanotubeGroup is not empty ..if its 
        empty it deletes it. 
        @see: cnt_model.NanotubeGroup.isEmpty
        @see: EditCommand.preview_or_finalize_structure
        """     
        if self.struct is not None:
            if self.struct.isEmpty():
                #Don't keep empty NanotubeGroup Fixes bug 2603. 
                self._removeStructure()
                self.win.win_update()
            else:
                EditCommand._finalizeStructure(self) 

        if self.struct is not None:
            #Make sure that he NanotubeGroup in the Model Tree is in collapsed state
            #after finalizing the structure.
            #DON'T DO self.struct.open = False in the above conditional
            #because the EditCommand._finalizeStructure may have assigned
            #'None' for 'self.struct'!
            self.struct.open = False


    def makeMenus(self): 
        """
        Create context menu for this command. (Build Nanotube mode)
        @see: chunk.make_glpane_context_menu_items
        @see: NanotubeSegment_EditCommand.makeMenus
        """
        if not hasattr(self, 'graphicsMode'):
            return

        selobj = self.glpane.selobj

        if selobj is None:
            self._makeEditContextMenus()
            return

        self.Menu_spec = []

        highlightedChunk = None
        if isinstance(selobj, Chunk):
            highlightedChunk = selobj
        if isinstance(selobj, Atom):
            highlightedChunk = selobj.molecule
        elif isinstance(selobj, Bond):
            chunk1 = selobj.atom1.molecule
            chunk2 = selobj.atom2.molecule
            if chunk1 is chunk2 and chunk1 is not None:
                highlightedChunk = chunk1

        if highlightedChunk is not None:
            highlightedChunk.make_glpane_context_menu_items(self.Menu_spec,
                                                            command = self)
            return
