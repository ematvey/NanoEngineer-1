# Copyright 2008 Nanorex, Inc.  See LICENSE file for details. 
"""
@author:    Mark
@version:   $Id: DnaDisplayStyle_Command.py 14380 2008-09-30 17:30:40Z ninadsathaye $
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details.
"""

import foundation.changes as changes
from commands.SelectChunks.SelectChunks_GraphicsMode import SelectChunks_GraphicsMode
from command_support.EditCommand import EditCommand
from utilities.constants import red
from dna.commands.DnaDisplayStyle.DnaDisplayStyle_PropertyManager import DnaDisplayStyle_PropertyManager

from graphics.drawing.drawDnaLabels import draw_dnaBaseNumberLabels

# == GraphicsMode part

_superclass_for_GM = SelectChunks_GraphicsMode

class DnaDisplayStyle_GraphicsMode( SelectChunks_GraphicsMode ):
    """
    Graphics mode for (DNA) Display Style command. 
    """
    def _drawLabels(self):
        """
        Overrides suoerclass method.
        @see: GraphicsMode._drawLabels()
        """
        _superclass_for_GM._drawLabels(self)
        draw_dnaBaseNumberLabels(self.glpane)
    
# == Command part


class DnaDisplayStyle_Command(EditCommand): 
    """
    
    """
     
    # class constants
    
    GraphicsMode_class = DnaDisplayStyle_GraphicsMode
    
    PM_class = DnaDisplayStyle_PropertyManager
    
    commandName = 'EDIT_DNA_DISPLAY_STYLE'
    featurename = "DNA Display Style"
    from utilities.constants import CL_GLOBAL_PROPERTIES
    command_level = CL_GLOBAL_PROPERTIES

    command_should_resume_prevMode = True 
    command_has_its_own_PM = True
    
    flyoutToolbar = None
    
    
    def _getFlyoutToolBarActionAndParentCommand(self):
        """
        See superclass for documentation.
        @see: self.command_update_flyout()
        """
        flyoutActionToCheck = 'editDnaDisplayStyleAction'
        parentCommandName = 'BUILD_DNA'      
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
        
        if not bool_keep:
            #Lets just not delete *ANY* DnaGroup while in DnaDisplayStyle_Command
            #Although DnaDisplayStyle command can only be accessed through
            #BuildDna_EditCommand, it could happen (due to a bug) that the 
            #previous command is not BuildDna_Editcommand. So bool_keep 
            #in that case will return False propmting dna updater to even delete
            #the empty DnaGroup (if it becomes empty for some reasons) of the 
            #BuildDna command. To avoid this ,this method will instruct 
            # to keep all instances of DnaGroup even when they might be empty.            
            if isinstance(group, self.assy.DnaGroup):
                bool_keep = True
            #Commented out code that shows what I was planning to implement 
            #earlier. 
            ##previousCommand = self.commandSequencer.prevMode # keep_empty_group: .struct
            ##if previousCommand.commandName == 'BUILD_DNA':
                ##if group is previousCommand.struct:
                    ##bool_keep = True                                
        
        return bool_keep
