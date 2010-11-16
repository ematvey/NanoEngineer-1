# Copyright 2008 Nanorex, Inc.  See LICENSE file for details. 
"""
@author:    Piotr
@version:   $Id: EditResidues_Command.py 14380 2008-09-30 17:30:40Z ninadsathaye $
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details.
"""

import foundation.changes as changes
from commands.SelectChunks.SelectChunks_GraphicsMode import SelectChunks_GraphicsMode
from command_support.EditCommand import EditCommand
from utilities.constants import red
from protein.commands.EditResidues.EditResidues_PropertyManager import EditResidues_PropertyManager
from utilities.GlobalPreferences import MODEL_AND_SIMULATE_PROTEINS
# == GraphicsMode part

_superclass_for_GM = SelectChunks_GraphicsMode

class EditResidues_GraphicsMode(SelectChunks_GraphicsMode ):
    """
    Graphics mode for Edit Residues command. 
    """
    pass
    
# == Command part


class EditResidues_Command(EditCommand): 
    """
    
    """    
    # class constants
    GraphicsMode_class = EditResidues_GraphicsMode
    
    PM_class = EditResidues_PropertyManager
        
    commandName = 'EDIT_RESIDUES'
    featurename = "Edit Residues"
    from utilities.constants import CL_SUBCOMMAND
    command_level = CL_SUBCOMMAND
    command_parent = 'BUILD_PROTEIN'
    if MODEL_AND_SIMULATE_PROTEINS:
        command_parent = 'MODEL_AND_SIMULATE_PROTEIN'

    command_should_resume_prevMode = True 
    command_has_its_own_PM = True
    
    flyoutToolbar = None
    
    def _getFlyoutToolBarActionAndParentCommand(self):
        """
        See superclass for documentation.
        @see: self.command_update_flyout()
        """
        flyoutActionToCheck = 'editResiduesAction'
        if MODEL_AND_SIMULATE_PROTEINS:
            parentCommandName = 'MODEL_AND_SIMULATE_PROTEIN'    
        else:
            parentCommandName = None
            
        return flyoutActionToCheck, parentCommandName
     
        
    def keep_empty_group(self, group):
        """
        Returns True if the empty group should not be automatically deleted. 
        otherwise returns False. The default implementation always returns 
        False. Subclasses should override this method if it needs to keep the
        empty group for some reasons. Note that this method will only get called
        when a group has a class constant autdelete_when_empty set to True. 
        (and as of 2008-03-06, it is proposed that dna_updater calls this method
        when needed. 
        @see: Command.keep_empty_group() which is overridden here. 
        """
        
        bool_keep = EditCommand.keep_empty_group(self, group)
        
        return bool_keep
    
