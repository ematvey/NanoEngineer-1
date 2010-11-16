# Copyright 2008 Nanorex, Inc.  See LICENSE file for details. 
"""
This class provides the flyout toolbar for FuseChunks_Command. 

@author: Ninad
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details.
@version:$Id: Ui_FuseFlyout.py 13903 2008-08-11 22:07:15Z ninadsathaye $

History:
2008-08-11: Created during command stack refactoring project

TODO:
"""
from ne1_ui.toolbars.Ui_AbstractFlyout import Ui_AbstractFlyout
from PyQt4.Qt import QAction

class FuseFlyout(Ui_AbstractFlyout):
    def _action_in_controlArea_to_show_this_flyout(self):
        """
        Required action in the 'Control Area' as a reference for this 
        flyout toolbar. See superclass method for documentation and todo note.
        """
        return self.win.toolsFuseChunksAction
    
    def _getExitActionText(self):
        """
        Overrides superclass method. 
        @see: self._createActions()
        """
        return "Exit Fuse"
    
    def getFlyoutActionList(self):
        """
        Returns a tuple that contains mode spcific actionlists in the
        added in the flyout toolbar of the mode.
        CommandToolbar._createFlyoutToolBar method calls this
        @return: params: A tuple that contains 3 lists:
        (subControlAreaActionList, commandActionLists, allActionsList)
        """
        #'allActionsList' returns all actions in the flyout toolbar
        #including the subcontrolArea actions
        allActionsList = []

        #Action List for  subcontrol Area buttons.
        #In this mode, there is really no subcontrol area.
        #We will treat subcontrol area same as 'command area'
        #(subcontrol area buttons will have an empty list as their command area
        #list). We will set  the Comamnd Area palette background color to the
        #subcontrol area.        
       
        subControlAreaActionList =[]
        
        subControlAreaActionList.append(self.exitModeAction)

        allActionsList.extend(subControlAreaActionList)

        #Empty actionlist for the 'Command Area'
        commandActionLists = []

        #Append empty 'lists' in 'commandActionLists equal to the
        #number of actions in subControlArea
        for i in range(len(subControlAreaActionList)):
            lst = []
            commandActionLists.append(lst)

        params = (subControlAreaActionList, commandActionLists, allActionsList)

        return params


