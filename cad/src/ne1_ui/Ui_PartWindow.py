# Copyright 2004-2008 Nanorex, Inc.  See LICENSE file for details.
"""
Ui_PartWindow.py provides the part window class.

@version: $Id: Ui_PartWindow.py 13243 2008-06-27 00:26:24Z marksims $
@copyright: 2004-2008 Nanorex, Inc.  See LICENSE file for details.

To Do:
- Reorder widget and layout creation so that the code is easier to follow
and understand. Also will make it more obvious were to insert future widgets
and layouts post Rattlesnake.
- Add "Right Area" frame (pwRightArea) containing the glpane.
- More attr renaming.
- Review/refine layouts one last time.
- Remove any unused methods I missed.
- Fix window title(s) when MDI is enabled (after Rattlesnake release)

History:

Mark 2007-06-27: PartWindow and GridPosition classes moved here from MWSemantics.py.
Mark 2008-01-05: Implemented the new U{B{NE1 Part Window Framework (SDI)}
<http://www.nanoengineer-1.net/mediawiki/index.php?title=NE1_Main_Window_Framework>}
which includes moving the history widget to the new reportDockWidget, renaming
key attrs and widgets (i.e. pwLeftArea and pwBottomArea)
"""

import os

from PyQt4.Qt import Qt, QWidget, QFrame, QVBoxLayout, QSplitter
from PyQt4.Qt import QTabWidget, QScrollArea, QSizePolicy
from graphics.widgets.GLPane import GLPane
from PM.PM_Constants import PM_DEFAULT_WIDTH, PM_MAXIMUM_WIDTH, PM_MINIMUM_WIDTH
from utilities.icon_utilities import geticon
from modelTree.ModelTree import modelTree
from utilities.qt4transition import qt4warnDestruction
from utilities import debug_flags
import foundation.env as env
from utilities.debug import print_compact_traceback

from utilities.prefs_constants import captionFullPath_prefs_key

class _pwProjectTabWidget(QTabWidget):
    """
    A helper class for the Project Tab Widget (a QTabWidget).
    It was created to help fix bug 2522.

    @note: [bruce 070829] to fix bug 2522 I need to intercept removeTab(),
    so I made this subclass. It needs to know the GLPane, which is set using
    KLUGE_setGLPane().

    @see: U{B{Bug 2522}
    <https://mirror2.cvsdude.com/bugz/polosims_svn/show_bug.cgi?id=2540>}
    """
    #bruce 070829 made this subclass re bug 2522
    def KLUGE_setGLPane(self, glpane):
        self._glpane = glpane
        return
    def removeTab(self, index):
        res = QTabWidget.removeTab(self, index)
            # note: AFAIK, res is always None
        if index != -1: # -1 happens!
            glpane = self._glpane
            glpane.gl_update_confcorner() # fix bug 2522 (try 2)
        return res
    pass

class Ui_PartWindow(QWidget):
    """
    The Ui_PartWindow class provides a Part Window UI object composed of three
    primary areas:

    - The "left area" contains the Project TabWidget which contains
    the Model Tree and Property Manager (tabs). Other tabs (widgets)
    can be introduced when needed.

    - The "right area" contains the 3D Graphics Area (i.e. glpane) displaying
    the current part.

    - The "bottom area" lives below the left and right areas, spanning
    the full width of the part window. It can be used whenever a landscape
    layout is needed (i.e. the Sequence Editor). Typically, this area is
    not used.

    A "part window" splitter lives between the left and right areas that
    allow the user to resize the shared area occupied by them. There is no
    splitter between the top and bottom areas.

    This class supports and is limited to a B{Single Document Interface (SDI)}.
    In time, NE1 will migrate to and support a Multiple Document Interface (MDI)
    that will allow multiple project documents (i.e. parts, assemblies,
    simulations, text files, graphs, tables, etc. documents) to be available
    within the common workspace of the NE1 main window.

    @see: U{B{NE1 Main Window Framework}
    <http://www.nanoengineer-1.net/mediawiki/index.php?title=NE1_Main_Window_Framework>}
    """
    widgets = [] # For debugging purposes.

    def __init__(self, assy, parent):
        """
        Constructor for the part window.

        @param assy: The assembly (part)
        @type  assy: Assembly

        @param parent: The parent widget.
        @type  parent: U{B{QMainWindow}
                       <http://doc.trolltech.com/4/qmainwindow.html>}
        """
        QWidget.__init__(self, parent)
        self.parent = parent
        self.assy = assy
            # note: to support MDI, self.assy would probably need to be a
            # different assembly for each PartWindow.
            # [bruce 080216 comment]
        self.setWindowIcon(geticon("ui/border/Part.png"))
        self.updateWindowTitle()

        # Used in expanding or collapsing the Model Tree/ PM area
        self._previous_pwLeftAreaWidth = PM_DEFAULT_WIDTH

        # The main layout for the part window is a VBoxLayout <pwVBoxLayout>.
        self.pwVBoxLayout = QVBoxLayout(self)
        pwVBoxLayout = self.pwVBoxLayout
        pwVBoxLayout.setMargin(0)
        pwVBoxLayout.setSpacing(0)

        # ################################################################
        # <pwSplitter> is the horizontal splitter b/w the
        # pwProjectTabWidget and the glpane.
        self.pwSplitter = QSplitter(Qt.Horizontal)
        pwSplitter = self.pwSplitter
        pwSplitter.setObjectName("pwSplitter")
        pwSplitter.setHandleWidth(3) # 3 pixels wide.
        pwVBoxLayout.addWidget(pwSplitter)

        # ##################################################################
        # <pwLeftArea> is the container holding the pwProjectTabWidget.
        # Note: Making pwLeftArea (and pwRightArea and pwBottomArea) QFrame
        # widgets has the benefit of making it easy to draw a border around
        # each area. One purpose of this would be to help developers understand
        # (visually) how the part window is laid out. I intend to add a debug
        # pref to draw part window area borders and add "What's This" text to
        # them. Mark 2008-01-05.
        self.pwLeftArea = QFrame()
        pwLeftArea = self.pwLeftArea
        pwLeftArea.setObjectName("pwLeftArea")
        pwLeftArea.setMinimumWidth(PM_MINIMUM_WIDTH)
        pwLeftArea.setMaximumWidth(PM_MAXIMUM_WIDTH)
        pwLeftArea.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy(QSizePolicy.Fixed),
                        QSizePolicy.Policy(QSizePolicy.Expanding)))

        # Setting the frame style like this is nice since it clearly
        # defines the splitter at the top-left corner.
        pwLeftArea.setFrameStyle( QFrame.Panel | QFrame.Sunken )

        # This layout will contain splitter (above) and the pwBottomArea.
        leftChannelVBoxLayout = QVBoxLayout(pwLeftArea)
        leftChannelVBoxLayout.setMargin(0)
        leftChannelVBoxLayout.setSpacing(0)

        pwSplitter.addWidget(pwLeftArea)

        # Makes it so pwLeftArea is not collapsible.
        pwSplitter.setCollapsible (0, False)

        # ##################################################################
        # <pwProjectTabWidget> is a QTabWidget that contains the MT and PM
        # widgets. It lives in the "left area" of the part window.
        self.pwProjectTabWidget = _pwProjectTabWidget()
           # _pwProjectTabWidget subclasses QTabWidget
           # Note [bruce 070829]: to fix bug 2522 I need to intercept
           # self.pwProjectTabWidget.removeTab, so I made it a subclass of
           # QTabWidget. It needs to know the GLPane, but that's not created
           # yet, so we set it later using KLUGE_setGLPane (below).
           # Note: No parent supplied. Could this be the source of the
           # minor vsplitter resizing problem I was trying to resolve a few
           # months ago?  Try supplying a parent later. Mark 2008-01-01
        self.pwProjectTabWidget.setObjectName("pwProjectTabWidget")
        self.pwProjectTabWidget.setCurrentIndex(0)
        self.pwProjectTabWidget.setAutoFillBackground(True)

        # Create the model tree "tab" widget. It will contain the MT GUI widget.
        # Set the tab icon, too.
        self.modelTreeTab = QWidget()
        self.modelTreeTab.setObjectName("modelTreeTab")
        self.pwProjectTabWidget.addTab(
            self.modelTreeTab,
            geticon("ui/modeltree/Model_Tree.png"),
            "")

        modelTreeTabLayout = QVBoxLayout(self.modelTreeTab)
        modelTreeTabLayout.setMargin(0)
        modelTreeTabLayout.setSpacing(0)

        # Create the model tree (GUI) and add it to the tab layout.
        self.modelTree = modelTree(self.modelTreeTab, parent)
        self.modelTree.modelTreeGui.setObjectName("modelTreeGui")
        modelTreeTabLayout.addWidget(self.modelTree.modelTreeGui)

        # Create the property manager "tab" widget. It will contain the PropMgr
        # scroll area, which will contain the property manager and all its
        # widgets.
        self.propertyManagerTab = QWidget()
        self.propertyManagerTab.setObjectName("propertyManagerTab")

        self.propertyManagerScrollArea = QScrollArea(self.pwProjectTabWidget)
        self.propertyManagerScrollArea.setObjectName("propertyManagerScrollArea")
        self.propertyManagerScrollArea.setWidget(self.propertyManagerTab)
        self.propertyManagerScrollArea.setWidgetResizable(True)
        # Eureka!
        # setWidgetResizable(True) will resize the Property Manager (and its
        # contents) correctly when the scrollbar appears/disappears.
        # It even accounts correctly for collapsed/expanded groupboxes!
        # Mark 2007-05-29

        # Add the property manager scroll area as a "tabbed" widget.
        # Set the tab icon, too.
        self.pwProjectTabWidget.addTab(
            self.propertyManagerScrollArea,
            geticon("ui/modeltree/Property_Manager.png"),
            "")

        # Finally, add the "pwProjectTabWidget" to the left channel layout.
        leftChannelVBoxLayout.addWidget(self.pwProjectTabWidget)

        # Create the glpane and make it a child of the part splitter.
        self.glpane = GLPane(assy, self, 'glpane name', parent)
            # note: our owner (MWsemantics) assumes
            # there is just this one GLPane for assy, and stores it
            # into assy as assy.o and assy.glpane. [bruce 080216 comment]
        self.pwProjectTabWidget.KLUGE_setGLPane(self.glpane)
            # help fix bug 2522 [bruce 070829]
        qt4warnDestruction(self.glpane, 'GLPane of PartWindow')
        pwSplitter.addWidget(self.glpane)

        # ##################################################################
        # <pwBottomArea> is a container at the bottom of the part window
        # spanning its entire width. It is intended to be used as an extra
        # area for use by Property Managers (or anything else) that needs
        # a landscape oriented layout.
        # An example is the Sequence Editor, which is part of the
        # Strand Properties PM.
        self.pwBottomArea = QFrame()
            # IMHO, self is not a good parent. Mark 2008-01-04.
        pwBottomArea = self.pwBottomArea
        pwBottomArea.setObjectName("pwBottomArea")
        pwBottomArea.setMaximumHeight(50)
        pwBottomArea.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy(QSizePolicy.Expanding),
                        QSizePolicy.Policy(QSizePolicy.Fixed)))

        # Add a frame border to see what it looks like.
        pwBottomArea.setFrameStyle( QFrame.Panel | QFrame.Sunken )

        self.pwVBoxLayout.addWidget(pwBottomArea)

        # Hide the bottom frame for now. Later this might be used for the
        # sequence editor.
        pwBottomArea.hide()

    def updateWindowTitle(self, changed = False):
        #by mark; bruce 050810 revised this in several ways, fixed bug 785
        """
        Update the window title (caption) at the top of the part window.
        Example:  "partname.mmp"

        This implements the standard way most applications indicate that a
        document has unsaved changes. On Mac OS X the close button will have
        a modified look; on other platforms the window title will have
        an '*' (asterisk).

        @note: We'll want to experiment with this to make sure it

        @param changed: If True, the document has unsaved changes.
        @type  changed: boolean

        @see: U{B{windowTitle}<http://doc.trolltech.com/4/qwidget.html#windowTitle-prop>},
              U{B{windowModified}<http://doc.trolltech.com/4/qwidget.html#windowModified-prop>}
        """
        caption_fullpath = env.prefs[captionFullPath_prefs_key]

        try:
            # self.assy.filename is always an empty string, even after a
            # file has been opened with a complete name. Need to ask Bruce
            # about this problem, resulting in a bug (i.e. the window title
            # is always "Untitled". Mark 2008-01-02.
            junk, basename = os.path.split(self.assy.filename)
            assert basename
                # it's normal for this to fail, when there is no file yet

            if caption_fullpath:
                partname = os.path.normpath(self.assy.filename)
                    #fixed bug 453-1 ninad060721
            else:
                partname = basename

        except:
            partname = 'Untitled'

        # If you're wondering about the "[*]" placeholder below, see:
        # http://doc.trolltech.com/4/qwidget.html#windowModified-prop
        self.setWindowTitle(self.trUtf8(partname + '[*]'))
        self.setWindowModified(changed)
        return

    def collapseLeftArea(self):
        """
        Collapse the left area.
        """
        self._previous_pwLeftAreaWidth = self.pwLeftArea.width()
        self.pwLeftArea.setFixedWidth(0)
        self.pwSplitter.setMaximumWidth(self.pwLeftArea.width())

    def expandLeftArea(self):
        """
        Expand the left area.

        @see: L{MWsemantics._showFullScreenCommonCode()} for an example
        showing how it is used.
        """
        if self._previous_pwLeftAreaWidth == 0:
            self._previous_pwLeftAreaWidth = PM_DEFAULT_WIDTH
        self.pwLeftArea.setMaximumWidth(
            self._previous_pwLeftAreaWidth)
        self.pwSplitter.setMaximumWidth(self.pwLeftArea.width())

    def updatePropertyManagerTab(self, tab): #Ninad 061207
        "Update the Properties Manager tab with 'tab' "

        self.parent.glpane.gl_update_confcorner()
            #bruce 070627, since PM affects confcorner appearance

        if self.propertyManagerScrollArea.widget():
            # The following is necessary to get rid of those C object
            # deleted errors (and the resulting bugs)
            lastwidgetobject = self.propertyManagerScrollArea.takeWidget()
            if lastwidgetobject:
                # bruce 071018 revised this code; see my comment on same
                # code in PM_Dialog
                try:
                    lastwidgetobject.update_props_if_needed_before_closing
                except AttributeError:
                    if 1 or debug_flags.atom_debug:
                        msg1 = "Last PropMgr %r doesn't have method" % lastwidgetobject
                        msg2 =" update_props_if_needed_before_closing. That's"
                        msg3 = " OK (for now, only implemented for Plane PM). "
                        msg4 = "Ignoring Exception: "
                        print_compact_traceback(msg1 + msg2 + msg3 + msg4)
                else:
                    lastwidgetobject.update_props_if_needed_before_closing()

            lastwidgetobject.hide()
            # @ ninad 061212 perhaps hiding the widget is not needed

        self.pwProjectTabWidget.removeTab(
            self.pwProjectTabWidget.indexOf(self.propertyManagerScrollArea))

        # Set the PropertyManager tab scroll area to the appropriate widget.
        self.propertyManagerScrollArea.setWidget(tab)

        self.pwProjectTabWidget.addTab(
            self.propertyManagerScrollArea,
            geticon("ui/modeltree/Property_Manager.png"),
            "")

        self.pwProjectTabWidget.setCurrentIndex(
            self.pwProjectTabWidget.indexOf(self.propertyManagerScrollArea))

    def KLUGE_current_PropertyManager(self):
        #bruce 070627; revised 070829 as part of fixing bug 2523
        """
        Return the current Property Manager widget (whether or not its tab is
        chosen, but only if it has a tab), or None if there is not one.

        @warning: This method's existence (not only its implementation)
        is a kluge, since the right way to access that would be by asking
        the "command sequencer";
        but that's not yet implemented, so this is the best we can do for now.
        Also, it would be better to get the top command and talk to it, not
        its PM (a QWidget). Also, whatever calls this will be making
        assumptions about that PM which are really only the command's business.
        So in short, every call of this is in need of cleanup once we have a
        working "command sequencer". (That's true of many things related to
        PMs, not only this method.)

        @warning: The return values are (presumably) widgets, but they can
        also be mode objects and generator objects, due to excessive use of
        multiple inheritance in the current PM code. So be careful what you
        do with them -- they might have lots of extra methods/attrs,
        and setting your own attrs in them might mess things up.
        """
        res = self.propertyManagerScrollArea.widget()
        if not hasattr(res, 'done_btn'):
            # not sure what widget this is otherwise, but it is a widget
            # (not None) for the default mode, at least on startup, so just
            # return None in this case
            return None
        # Sometimes this PM remains present from a prior command, even when
        # there is no longer a tab for the PM. As part of fixing bug 2523
        # we have to avoid returning it in that case. How we do that is a kluge,
        # but hopefully this entire kluge function can be dispensed with soon.
        # This change also fixes bug 2522 on the Mac (but not on Windows --
        # for that, we needed to intercept removeTab in separate code above).
        index = self.pwProjectTabWidget.indexOf(
            self.propertyManagerScrollArea)
        if index == -1:
            return None
        # Due to bugs in other code, sometimes the PM tab is left in place,
        # though the PM itself is hidden. To avoid finding the PM in that case,
        # also check whether it's hidden. This will fix the CC part of a new bug
        # just reported by Keith in email (when hitting Ok in DNA Gen).
        if res.isHidden(): # probably a QWidget method [bruce 080205 comment]
            return None
        return res

    def dismiss(self):
        self.parent.removePartWindow(self)
    
    def setSplitterPosition(self, leftAreaWidth = PM_DEFAULT_WIDTH): 
        """
        Set the position of the splitter between the left area and graphics area
        so that the starting width of the model tree/property manager is 
        I{leftAreaWdith} pixels wide.
        """
        # This code fixes bug 2424. Mark 2007-06-27.
        #
        # Bug 2424 was difficult to fix for many reasons:
        #
        # - QSplitter.sizes() does not return valid values until the main window
        #   is displayed. Specifically, the value of the second index (the glpane
        #   width) is always zero until the main window is displayed. I suspect 
        #   that the initial size of the glpane (in its constructor) is not set
        #   (or set to 0) and may be contributing to the confusion. This is only
        #   a theory.
        #
        # - QSplitter.setSizes() only works if width1 (the PropMgr width) and
        #   width2 (the glpane width) equal a "magic combined width". See 
        #   more about this in the Method description below.
        #
        # - Qt's QSplitter.moveSplitter() function doesn't work.
        #   
        # Method for bug fix:
        #
        # Get the widths of the left area and the glpane using QSplitter.sizes().
        # These (2) widths add up and equal a total width. You can only
        # feed QSplitter.setSizes() two values that add up to the total width
        # or it will do nothing.
    
        pw = self
        w1, w2 = pw.pwSplitter.sizes()
        total_combined_width = w1 + w2
        new_glpane_width = total_combined_width - leftAreaWidth
        pw.pwSplitter.setSizes([leftAreaWidth, new_glpane_width])
        return
