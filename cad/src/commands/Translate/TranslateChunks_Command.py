# Copyright 2008 Nanorex, Inc.  See LICENSE file for details. 
"""
TranslateChunks_Command.py

@author: Ninad
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details.
@version: $Id: TranslateChunks_Command.py 14380 2008-09-30 17:30:40Z ninadsathaye $

History:

NOTE:
As of 2008-01-25, this command is not yet used, however its graphics mode class
(TranslateChunks_GraphicsMode) is used as an alternative graphics mode in 
Move_Command.
"""
from commands.Move.Move_Command import Move_Command
from commands.Translate.TranslateChunks_GraphicsMode import TranslateChunks_GraphicsMode

_superclass = Move_Command
class TranslateChunks_Command(Move_Command):
    """
    Translate Chunks command
    """
       
    commandName = 'TRANSLATE_CHUNKS'
    featurename = "Translate Chunks"
    from utilities.constants import CL_EDIT_GENERIC
    command_level = CL_EDIT_GENERIC
    
    command_should_resume_prevMode = True 
    command_has_its_own_PM = False    
    GraphicsMode_class = TranslateChunks_GraphicsMode
        
    
    def connect_or_disconnect_signals(self, isConnect):
        """
        Connect or disconnect widget signals sent to their slot methods.
        @param isConnect: If True the widget will send the signals to the slot 
                          method. 
        @type  isConnect: boolean
        As of 2008-01-25, this method does nothing.
        """
        pass
        
    
    
