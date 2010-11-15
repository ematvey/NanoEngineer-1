# Copyright 2007 Nanorex, Inc.  See LICENSE file for details. 
"""
Ui_ProteinSequenceEditor.py

@author: Urmi
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details.
@version:$Id$

History:
Urmi copied this from Ui_DnaSequenceEditor.py and modified it to suit the 
requirements of a protein sequence editor
"""

from PyQt4.Qt import QToolButton
from PyQt4.Qt import QPalette
from PyQt4.Qt import QTextOption
from PyQt4.Qt import QLabel
from PyQt4.Qt import QAction, QMenu
from PyQt4.Qt import Qt, QColor
from PM.PM_Colors import pmGrpBoxColor
from PM.PM_Colors    import getPalette
from PM.PM_Colors    import sequenceEditStrandMateBaseColor

from PM.PM_DockWidget import PM_DockWidget
from PM.PM_WidgetRow  import PM_WidgetRow
from PM.PM_ToolButton import PM_ToolButton
from PM.PM_ComboBox   import PM_ComboBox
from PM.PM_TextEdit   import PM_TextEdit
from PM.PM_LineEdit   import PM_LineEdit
from PM.PM_PushButton import PM_PushButton

from utilities.icon_utilities import geticon, getpixmap

_superclass = PM_DockWidget
class Ui_ProteinSequenceEditor(PM_DockWidget):
    """
    The Ui_DnaSequenceEditor class defines UI elements for the Sequence Editor
    object. The sequence editor is usually visible while in DNA edit mode.
    It is a DockWidget that is doced at the bottom of the MainWindow
    """
    _title         =  "Sequence Editor"
    _groupBoxCount = 0
    _lastGroupBox = None

    def __init__(self, win):
        """
        Constructor for the Ui_DnaSequenceEditor 
        @param win: The parentWidget (MainWindow) for the sequence editor 
        """
        
        self.win = win
        # Should parentWidget for a docwidget always be win? 
        #Not necessary but most likely it will be the case.        
        parentWidget = win 
        
        _superclass.__init__(self, parentWidget, title = self._title)
        
        #A flag used to restore the state of the Reports dock widget 
        #(which can be accessed through View  >  Reports) see self.show() and
        #self.closeEvent() for more details. 
        self._reportsDockWidget_closed_in_show_method = False
        self.setFixedHeight(90)

    def show(self):
        """
        Shows the sequence editor. While doing this, it also closes the reports
        dock widget (if visible) the state of the reports dockwidget will be
        restored when the sequence editor is closed. 
        @see:self.closeEvent()
        """
        self._reportsDockWidget_closed_in_show_method = False
        
        if self.win.viewFullScreenAction.isChecked() or \
           self.win.viewSemiFullScreenAction.isChecked():
            pass
        else:
            if self.win.reportsDockWidget.isVisible():
                self.win.reportsDockWidget.close()
                self._reportsDockWidget_closed_in_show_method = True

        _superclass.show(self)  
        
    def closeEvent(self, event):
        """
        Overrides close event. Makes sure that the visible state of the reports
        widgetis restored when the sequence editor is closed. 
        @see: self.show()
        """
        _superclass.closeEvent(self, event)
       
        if self.win.viewFullScreenAction.isChecked() or \
           self.win.viewSemiFullScreenAction.isChecked():
            pass
        else:
            if self._reportsDockWidget_closed_in_show_method:
                self.win.viewReportsAction.setChecked(True) 
                self._reportsDockWidget_closed_in_show_method = False

    def _loadWidgets(self):
        """
        Overrides PM.PM_DockWidget._loadWidgets. Loads the widget in this
        dockwidget.
        """
        self._loadMenuWidgets()
        self._loadTextEditWidget()


    def _loadMenuWidgets(self):
        """
        Load the various menu widgets (e.g. Open, save sequence options, 
        Find and replace widgets etc. 
        """
        #Note: Find and replace widgets might be moved to their own class.

        self.loadSequenceButton = PM_ToolButton(
            self,
            iconPath = "ui/actions/Properties Manager/Open.png")  

        self.saveSequenceButton = PM_ToolButton(
            self, 
            iconPath = "ui/actions/Properties Manager/Save_Strand_Sequence.png") 

        self.loadSequenceButton.setAutoRaise(True)
        self.saveSequenceButton.setAutoRaise(True)

        
        #Find and replace widgets --
        self.findLineEdit = \
            PM_LineEdit( self, 
                         label        = "",
                         spanWidth    = False)
        self.findLineEdit.setMaximumWidth(60)


        self.replaceLineEdit = \
            PM_LineEdit( self, 
                         label        = "",
                         spanWidth    = False)
        self.replaceLineEdit.setMaximumWidth(60)

        self.findOptionsToolButton = PM_ToolButton(self)
        self.findOptionsToolButton.setMaximumWidth(12)
        self.findOptionsToolButton.setAutoRaise(True)

        self.findOptionsToolButton.setPopupMode(QToolButton.MenuButtonPopup)

        self._setFindOptionsToolButtonMenu()

        self.findNextToolButton = PM_ToolButton(
            self,
            iconPath = "ui/actions/Properties Manager/Find_Next.png")
        self.findNextToolButton.setAutoRaise(True)

        self.findPreviousToolButton = PM_ToolButton(
            self,
            iconPath = "ui/actions/Properties Manager/Find_Previous.png")
        self.findPreviousToolButton.setAutoRaise(True)

        self.replacePushButton = PM_PushButton(self, text = "Replace")

        self.warningSign = QLabel(self)
        self.warningSign.setPixmap(
            getpixmap('ui/actions/Properties Manager/Warning.png'))
        self.warningSign.hide()

        self.phraseNotFoundLabel = QLabel(self)
        self.phraseNotFoundLabel.setText("Sequence Not Found")
        self.phraseNotFoundLabel.hide()

        

        #Widgets to include in the widget row. 
        widgetList = [('PM_ToolButton', self.loadSequenceButton, 0),
                      ('PM_ToolButton', self.saveSequenceButton, 1),
                      ('QLabel', "     Find:", 4),
                      ('PM_LineEdit', self.findLineEdit, 5),
                      ('PM_ToolButton', self.findOptionsToolButton, 6),
                      ('PM_ToolButton', self.findPreviousToolButton, 7),
                      ('PM_ToolButton', self.findNextToolButton, 8), 
                      ('QLabel', "     Replace:", 9),
                      ('PM_TextEdit', self.replaceLineEdit, 10), 
                      ('PM_PushButton', self.replacePushButton, 11),
                      ('PM_Label', self.warningSign, 12),
                      ('PM_Label', self.phraseNotFoundLabel, 13),
                      ('QSpacerItem', 5, 5, 14) ]

        widgetRow = PM_WidgetRow(self,
                                 title     = '',
                                 widgetList = widgetList,
                                 label = "",
                                 spanWidth = True )
        
        

    def _loadTextEditWidget(self):
        """
        Load the SequenceTexteditWidgets.         
        """        
        self.aaRulerTextEdit = \
            PM_TextEdit( self, 
                         label = "", 
                         spanWidth = False,
                         permit_enter_keystroke = False) 
        
        palette = getPalette(None, 
                             QPalette.Base, 
                             pmGrpBoxColor)
        self.aaRulerTextEdit.setPalette(palette)     
        self.aaRulerTextEdit.setWordWrapMode( QTextOption.WrapAnywhere )
        self.aaRulerTextEdit.setFixedHeight(20)
        self.aaRulerTextEdit.setReadOnly(True)
        
        self.sequenceTextEdit = \
            PM_TextEdit( self, 
                         label = " Sequence: ", 
                         spanWidth = False,
                         permit_enter_keystroke = False) 
        
        
        self.sequenceTextEdit.setCursorWidth(2)
        self.sequenceTextEdit.setWordWrapMode( QTextOption.WrapAnywhere )
        self.sequenceTextEdit.setFixedHeight(20)
        
        self.secStrucTextEdit = \
            PM_TextEdit( self, 
                         label = " Secondary structure: ", 
                         spanWidth = False,
                         permit_enter_keystroke = False) 
        
        palette = getPalette(None, 
                             QPalette.Base, 
                             sequenceEditStrandMateBaseColor)
        self.secStrucTextEdit.setPalette(palette)     
        self.secStrucTextEdit.setWordWrapMode( QTextOption.WrapAnywhere )
        self.secStrucTextEdit.setFixedHeight(20)
        self.secStrucTextEdit.setReadOnly(True)

        #Important to make sure that the horizontal and vertical scrollbars 
        #for these text edits are never displayed. 
        
        self.sequenceTextEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sequenceTextEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.secStrucTextEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.secStrucTextEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.aaRulerTextEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.aaRulerTextEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def _getFindLineEditStyleSheet(self):
        """
        Return the style sheet for the findLineEdit. This sets the following 
        properties only:
         - background-color

        This style is set whenever the searchStrig can't be found (sets
        a light red color background to the lineedit when this happens)   

        @return: The line edit style sheet.
        @rtype:  str

        """
        styleSheet = \
                   "QLineEdit {\
                   background-color: rgb(255, 102, 102)\
                   }"
        #Not used:
        #  background-color: rgb(217, 255, 216)\       

        return styleSheet

    def _setFindOptionsToolButtonMenu(self):
        """
        Sets the menu for the findOptionstoolbutton that appears a small 
        menu button next to the findLineEdit.
        """
        self.findOptionsMenu = QMenu(self.findOptionsToolButton)

        self.caseSensitiveFindAction = QAction(self.findOptionsToolButton)
        self.caseSensitiveFindAction.setText('Match Case')
        self.caseSensitiveFindAction.setCheckable(True)
        self.caseSensitiveFindAction.setChecked(False)

        self.findOptionsMenu.addAction(self.caseSensitiveFindAction)
        self.findOptionsMenu.addSeparator()

        self.findOptionsToolButton.setMenu(self.findOptionsMenu)

    def _addToolTipText(self):
        """
            What's Tool Tip text for widgets in this Property Manager.  
            """ 
        pass

    def _addWhatsThisText(self):
        """
            What's This text for widgets in this Property Manager.  

            """
        pass
    