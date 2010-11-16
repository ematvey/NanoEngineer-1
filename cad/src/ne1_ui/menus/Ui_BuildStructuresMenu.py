# Copyright 2004-2007 Nanorex, Inc.  See LICENSE file for details. 
"""
$Id: Ui_BuildStructuresMenu.py 14019 2008-08-22 19:16:12Z ninadsathaye $
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
    
    win.buildStructuresMenu.addAction(win.buildNanotubeAction) 
    win.buildStructuresMenu.addAction(win.buildCrystalAction)
    
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