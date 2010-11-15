# Copyright 2007 Nanorex, Inc.  See LICENSE file for details. 
"""
@author:    Urmi
@version:   $Id: 
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details.
"""

import foundation.changes as changes
from commands.SelectChunks.SelectChunks_GraphicsMode import SelectChunks_GraphicsMode
from command_support.EditCommand import EditCommand
from utilities.constants import red
from protein.commands.ProteinDisplayStyle.ProteinDisplayStyle_PropertyManager import ProteinDisplayStyle_PropertyManager

# == GraphicsMode part

_superclass_for_GM = SelectChunks_GraphicsMode

class ProteinDisplayStyle_GraphicsMode(SelectChunks_GraphicsMode ):
    """
    Graphics mode for (Protein) Display Style command. 
    """
    pass
    
# == Command part


class ProteinDisplayStyle_Command(EditCommand): 
    """
    
    """
    # class constants
    
    commandName = 'EDIT_PROTEIN_DISPLAY_STYLE'
    default_mode_status_text = ""
    featurename = "Protein Display Style"
         
    hover_highlighting_enabled = True
    GraphicsMode_class = ProteinDisplayStyle_GraphicsMode
   
    
    command_can_be_suspended = False
    command_should_resume_prevMode = True 
    command_has_its_own_gui = True
    
    flyoutToolbar = None

    def init_gui(self):
        """
        Initialize GUI for this mode 
        """
        previousCommand = self.commandSequencer.prevMode 
        if previousCommand.commandName == 'BUILD_PROTEIN':
            try:
                self.flyoutToolbar = previousCommand.flyoutToolbar
                self.flyoutToolbar.displayProteinStyleAction.setChecked(True)
            except AttributeError:
                self.flyoutToolbar = None
            if self.flyoutToolbar:
                if not self.flyoutToolbar.displayProteinStyleAction.isChecked():
                    self.flyoutToolbar.displayProteinStyleAction.setChecked(True)         
            
                
        if self.propMgr is None:
            self.propMgr = ProteinDisplayStyle_PropertyManager(self)
            #@bug BUG: following is a workaround for bug 2494.
            #This bug is mitigated as propMgr object no longer gets recreated
            #for modes -- niand 2007-08-29
            changes.keep_forever(self.propMgr)  
            
        self.propMgr.show()
            
        
    def restore_gui(self):
        """
        Restore the GUI 
        """
        EditCommand.restore_gui(self)
        if self.flyoutToolbar:
            self.flyoutToolbar.displayProteinStyleAction.setChecked(False)    
        
    
   
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