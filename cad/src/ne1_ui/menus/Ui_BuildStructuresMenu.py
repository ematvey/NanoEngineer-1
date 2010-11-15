# Copyright 2004-2007 Nanorex, Inc.  See LICENSE file for details. 
"""
$Id: Ui_BuildStructuresMenu.py 12416 2008-04-09 05:40:41Z marksims $
"""

from PyQt4 import QtGui
from utilities.debug_prefs import debug_pref, Choice_boolean_True

def setupUi(win):
    """
    Populates the "Build Structures" menu, a submenu of the "Tools" menu.

    @param win: NE1's main window object.
    @type  win: Ui_MainWindow
    """
    
    # Populate the "Build Structures" menu. 
    # Start with "Builders", then add single shot "Generators".
    win.buildStructuresMenu.addAction(win.toolsDepositAtomAction)
    win.buildStructuresMenu.addAction(win.buildDnaAction)
    
    #  New Nanotube Builder or old Nanotube Generator?
    if debug_pref("Use new 'Build > Nanotube' builder? (next session)", 
                      Choice_boolean_True, 
                      prefs_key = "A10 devel/Old Nanotube Generator"):
        win.buildStructuresMenu.addAction(win.buildNanotubeAction) 
    else:
        # Original "Build > Nanotube"
        win.buildStructuresMenu.addAction(win.nanotubeGeneratorAction)
        
    win.buildStructuresMenu.addAction(win.toolsCookieCutAction)
    
    win.buildStructuresMenu.addSeparator() # Generators after this separator.
    win.buildStructuresMenu.addAction(win.insertPeptideAction) # piotr 080304
    win.buildStructuresMenu.addAction(win.insertGrapheneAction)
    win.buildStructuresMenu.addAction(win.insertAtomAction)
    
    
def retranslateUi(win):
    """
    Sets text related attributes for the "Build Structures" submenu, 
    which is a submenu of the "Tools" menu.

    @param win: NE1's mainwindow object.
    @type  win: U{B{QMainWindow}<http://doc.trolltech.com/4/qmainwindow.html>}
    """
    win.buildStructuresMenu.setTitle(QtGui.QApplication.translate(
         "MainWindow", "Build Structures", 
         None, QtGui.QApplication.UnicodeUTF8))