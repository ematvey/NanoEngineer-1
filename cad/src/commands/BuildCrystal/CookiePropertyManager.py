# Copyright 2004-2007 Nanorex, Inc.  See LICENSE file for details. 
"""
$Id: CookiePropertyManager.py 11749 2008-03-02 23:46:06Z ericmessick $
"""

from commands.BuildCrystal.Ui_CookiePropertyManager import Ui_CookiePropertyManager

class CookiePropertyManager(Ui_CookiePropertyManager):
    def __init__(self, parentMode):
        Ui_CookiePropertyManager.__init__(self, parentMode)
        self.updateMessage()           
    
    def ok_btn_clicked(self):
        """
        Calls MainWindow.toolsDone to exit the current mode. 
        @attention: this method needs to be renamed. (this should be done in 
        PM_Dialog)
        """
        self.w.toolsDone()
    
    def cancel_btn_clicked(self):
        """
        Calls MainWindow.toolsDone to exit the current mode. 
        @attention: this method needs to be renamed. (this should be done in 
        PM_Dialog)
        """
        self.w.toolsCancel()
    
    def updateMessage(self):
        """
        """
        msg = "Draw the Crystal geometry selecting the desired shape from the \
        flyout toolbar at the top."
        self.MessageGroupBox.insertHtmlMessage(msg)
        
