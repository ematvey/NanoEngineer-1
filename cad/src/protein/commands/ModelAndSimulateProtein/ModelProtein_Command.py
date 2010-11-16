# Copyright 2008 Nanorex, Inc.  See LICENSE file for details. 
"""

@author: Urmi
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details.
@version:$Id: ModelProtein_Command.py 14380 2008-09-30 17:30:40Z ninadsathaye $

"""
from utilities.debug import print_compact_stack, print_compact_traceback
from protein.commands.ModelAndSimulateProtein.ModelAndSimulateProtein_Command import ModelAndSimulateProtein_Command

_superclass = ModelAndSimulateProtein_Command
class ModelProtein_Command(ModelAndSimulateProtein_Command):
    """
    Class for modeling proteins
    """
    
    FlyoutToolbar_class = None
    
    featurename = 'Model and Simulate Protein Mode/Model Protein'
    commandName = 'MODEL_PROTEIN'
    
    command_should_resume_prevMode = True
    #Urmi 20080806: We may want it to have its own PM
    command_has_its_own_PM = False
    
    _currentActiveTool = 'MODEL_PROTEIN'
    from utilities.constants import CL_SUBCOMMAND

    #class constants for the NEW COMMAND API -- 2008-07-30
    command_level = CL_SUBCOMMAND
    command_parent = 'MODEL_AND_SIMULATE_PROTEIN'
    
    def command_entered(self):
        """
        Extends superclass method. 
        @see: baseCommand.command_entered() for documentation
        """
        _superclass.command_entered(self)
        msg = "Select a modeling tool to either modify an existing protein "\
                    "or create a new peptide chain."
        self.propMgr.updateMessage(msg)
