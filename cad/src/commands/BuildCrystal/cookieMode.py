# Copyright 2004-2008 Nanorex, Inc.  See LICENSE file for details. 
"""
cookieMode.py -- cookie cutter mode, aka "Build Crystal"

@version: $Id: cookieMode.py 12962 2008-05-28 00:36:08Z russfish $
@copyright: 2004-2008 Nanorex, Inc.  See LICENSE file for details.

Note: Till Alpha8, this mode was called Cookie Cutter mode. In Alpha9 
it has been renamed to 'Build Crystal' mode. -- ninad 20070511
"""

import math # only for pi
from Numeric import size, dot, sqrt, floor

from OpenGL.GL import GL_COLOR_LOGIC_OP
from OpenGL.GL import GL_DEPTH_TEST
from OpenGL.GL import GL_XOR
from OpenGL.GL import glLogicOp
from OpenGL.GL import glTranslatef
from OpenGL.GL import glRotatef
from OpenGL.GL import GL_CLIP_PLANE1
from OpenGL.GL import glColor3fv
from OpenGL.GL import glDisable
from OpenGL.GL import glEnable
from OpenGL.GL import glFlush
from OpenGL.GL import glPushMatrix
from OpenGL.GL import GL_CLIP_PLANE0
from OpenGL.GL import glClipPlane
from OpenGL.GL import glPopMatrix

from PyQt4.Qt import Qt
from PyQt4.Qt import QCursor

import foundation.env as env
from geometry.VQT import V, Q, A, norm, vlen
from command_support.modes import basicMode
from commands.BuildCrystal.CookieCtrlPanel import CookieCtrlPanel
from utilities.Log import orangemsg
from utilities.Log import redmsg

from graphics.behaviors.shape import get_selCurve_color
from geometry.Slab import Slab
from commands.BuildCrystal.CookieShape import CookieShape

import graphics.drawing.drawing_globals as drawing_globals
from graphics.drawing.CS_draw_primitives import drawline
from graphics.drawing.drawers import drawCircle
from graphics.drawing.drawers import drawGrid
from graphics.drawing.drawers import drawLineLoop
from graphics.drawing.drawers import drawrectangle
from graphics.drawing.drawers import findCell
from model.chunk import Chunk
from model.chem import Atom

from utilities.constants import intRound
from utilities.constants import gensym
from utilities.constants import diTUBES
from utilities.constants import SELSHAPE_LASSO
from utilities.constants import START_NEW_SELECTION
from utilities.constants import white
from utilities.constants import ADD_TO_SELECTION
from utilities.constants import SUBTRACT_FROM_SELECTION
from utilities.constants import SELSHAPE_RECT

import foundation.changes as changes


class cookieMode(basicMode):
    """
    Build Crystal
    """
    # class constants
    backgroundColor = 0/255.0, 0/255.0, 0/255.0
    backgroundGradient = False # Mark 051029.
    gridColor = 222/255.0, 148/255.0, 0/255.0
    commandName = 'COOKIE'
    default_mode_status_text = "Mode: Build Crystal"
    featurename = "Build Crystal Mode"

    displayMode = diTUBES 
        # displayMode isn't used except for updating the 'Display Mode' combobox in the Preference dialog.
        # Cookie mode uses its own attr <cookieDisplayMode> to display Tubes (default) or Spheres.
    
    selCurve_List = []
        # <selCurve_List> contains a list of points used to draw the selection curve.  
        # The points lay in the plane parallel to the screen, just beyond the front clipping 
        # plane, so that they are always  inside the clipping volume.
        
    defaultSelShape = SELSHAPE_LASSO
        # <defaultSelShape> determines whether the current *default* selection curve is a rectangle 
        # or lasso.
    
    MAX_LATTICE_CELL = 25
    
    layerColors = ((0.0, 85.0/255.0, 127/255.0),
                           (85/255.0, 85/255.0, 0.0),
                           (85/255.0, 85/255.0, 127/255.0),
                            (170.0/255.0, 0.0, 127.0/255.0),
                           (170.0/255.0, 0.0,  1.0),
                           (1.0, 0.0, 127.0/255.0),
                           )
    
    LATTICE_TYPES = ['DIAMOND', 'LONSDALEITE', 'GRAPHITE']
    
    MAX_LAYERS = 6
    
    freeView = False
    drawingCookieSelCurve = False
        # <drawingCookieSelCurve> is used to let other methods know when
        # we are in the process of defining/drawing a selection curve, where:
        # True = in the process of defining selection curve
        # False = finished/not defining selection curve
                           
    # methods related to entering this mode
    def __init__(self, glpane):
        """The initial function is called only once for the whole program """
        basicMode.__init__(self, glpane)
        
        if not self.propMgr:
            self.propMgr = CookieCtrlPanel(self)
            changes.keep_forever(self.propMgr)            
    
    def Enter(self): 
        basicMode.Enter(self)
        
        # Save original GLPane background color and gradient, to be restored when exiting Cookie Cutter mode.
        self.glpane_backgroundColor = self.o.backgroundColor
        self.o.backgroundColor = self.backgroundColor
        
        self.glpane_backgroundGradient = self.o.backgroundGradient
        self.o.backgroundGradient = self.backgroundGradient
        
        self.oldPov = V(self.o.pov[0], self.o.pov[1], self.o.pov[2])
        self.setOrientSurf(self.o.snap2trackball())
        
        self.o.pov -= 3.5*self.o.out
        self.savedOrtho = self.o.ortho
        self.o.ortho = True
        self.cookieQuat = None

        ##Every time enters into this mode, we need to set this to False
        self.freeView = False
        self.propMgr.freeViewCheckBox.setChecked(self.freeView)
        
        self.gridShow = True
        self.propMgr.gridLineCheckBox.setChecked(self.gridShow)
        
        self.gridSnap = False
        self.propMgr.snapGridCheckBox.setChecked(self.gridSnap)
        
        self.showFullModel = self.propMgr.fullModelCheckBox.isChecked()
        self.cookieDisplayMode = str(self.propMgr.dispModeComboBox.currentText())
        self.latticeType = self.LATTICE_TYPES[self.propMgr.latticeCBox.currentIndex()]
        
        self.layers = [] ## Stores 'surface origin' for each layer
        self.layers += [V(self.o.pov[0], self.o.pov[1], self.o.pov[2])]
        self.currentLayer = 0
 
        self.drawingCookieSelCurve = False
            # <drawingCookieSelCurve> is used to let other methods know when
            # we are in the process of defining/drawing a selection curve, where:
            # True = in the process of defining selection curve
            # False = finished/not defining selection curve
        self.Rubber = False
            # Set to True in end_selection_curve() when doing a poly-rubber-band selection.
        self.lastDrawStored = []
       
        #Show the flyout toolbar
        
        #self.w.commandToolbar.updateCommandToolbar(self.propMgr.btn_list, entering =True)        
        
        self.selectionShape = self.propMgr.getSelectionShape()
        
    
    def init_gui(self):
        """GUI items need initialization every time."""
        self.propMgr.initGui()
        
        #This can't be done in the above call. During this time, 
        # the ctrlPanel can't find the cookieMode, the nullMode
        # is used instead. I don't know if that's good or not, but
        # generally speaking, I think the code structure for mode 
        # operations like enter/init/cancel, etc, are kind of confusing.
        # The code readability is also not very good. --Huaicai
        self.setThickness(self.propMgr.layerCellsSpinBox.value()) 

        # I don't know if this is better to do here or just before setThickness (or if it matters): ####@@@@
        # Disable Undo/Redo actions, and undo checkpoints, during this mode (they *must* be reenabled in restore_gui).
        # We do this last, so as not to do it if there are exceptions in the rest of the method,
        # since if it's done and never undone, Undo/Redo won't work for the rest of the session.
        # [bruce 060414; same thing done in some other modes]
        import foundation.undo_manager as undo_manager
        undo_manager.disable_undo_checkpoints('Build Crystal Mode')
        undo_manager.disable_UndoRedo('Build Crystal Mode', "in Build Crystal") # optimizing this for shortness in menu text
            # this makes Undo menu commands and tooltips look like "Undo (not permitted in Cookie Cutter)" (and similarly for Redo)
   
   
    def restore_gui(self):
        """Restore GUI items when exit every time. """

        # Reenable Undo/Redo actions, and undo checkpoints (disabled in init_gui);
        # do it first to protect it from exceptions in the rest of this method
        # (since if it never happens, Undo/Redo won't work for the rest of the session)
        # [bruce 060414; same thing done in some other modes]
        import foundation.undo_manager as undo_manager
        undo_manager.reenable_undo_checkpoints('Build Crystal Mode')
        undo_manager.reenable_UndoRedo('Build Crystal Mode')
        self.set_cmdname('Build Crystal') # this covers all changes while we were in the mode
            # (somewhat of a kluge, and whether this is the best place to do it is unknown;
            #  without this the cmdname is "Done")

        self.propMgr.restoreGui()
                
        if not self.savedOrtho:
            self.w.setViewPerspecAction.setChecked(True)
            
        #Restore GL states
        self.o.redrawGL = True
        glDisable(GL_COLOR_LOGIC_OP)
        glEnable(GL_DEPTH_TEST)
   
        # Restore default background color. Ask Bruce if I should create a subclass of Done and place it there. Mark 060815.
        self.o.backgroundColor = self.glpane_backgroundColor
        self.o.backgroundGradient = self.glpane_backgroundGradient
    
    def setFreeView(self, freeView):
        """Enables/disables 'free view' mode.
        When <freeView> is True, cookie-cutting is frozen.
        """
        self.freeView = freeView
        self.update_cursor_for_no_MB()
        
        if freeView: # Disable cookie cutting.
            #Save current pov before free view transformation
            self.cookiePov = V(self.o.pov[0], self.o.pov[1], self.o.pov[2])
            
            env.history.message(orangemsg(
                "'Free View' enabled. You can not create crystal shapes while Free View is enabled."))
            self.w.setViewOrthoAction.setEnabled(True)
            self.w.setViewPerspecAction.setEnabled(True)
            
            #Disable controls to change layer.
            self.propMgr.currentLayerComboBox.setEnabled(False)
            self.isAddLayerEnabled = self.propMgr.addLayerButton.isEnabled ()
            self.propMgr.addLayerButton.setEnabled(False)
            
            self.propMgr.enableViewChanges(True)
            
            if self.drawingCookieSelCurve: #Cancel any unfinished cookie drawing
                self._afterCookieSelection()
                env.history.message(redmsg(
                    "In free view mode,the unfinished crystal shape creation has been cancelled."))
            
        else: ## Restore cookie cutting mode
            self.w.setViewOrthoAction.setChecked(True)  
            self.w.setViewOrthoAction.setEnabled(False)
            self.w.setViewPerspecAction.setEnabled(False)
            
            #Restore controls to change layer/add layer
            self.propMgr.currentLayerComboBox.setEnabled(True)
            self.propMgr.addLayerButton.setEnabled(self.isAddLayerEnabled)
            
            self.propMgr.enableViewChanges(False)
            
            self.o.ortho = True
            if self.o.shape:
                self.o.quat = Q(self.cookieQuat)
                self.o.pov = V(self.cookiePov[0], self.cookiePov[1], self.cookiePov[2]) 
            self.setOrientSurf(self.o.snap2trackball())
    
      
    def showGridLine(self, show):
        self.gridShow = show
        self.o.gl_update()
        
    def setGridLineColor(self, c):
        """Set the grid Line color to c. c is an object of QColor """
        self.gridColor = c.red()/255.0, c.green()/255.0, c.blue()/255.0
        
    def changeDispMode(self, mode):
        """Change cookie display mode as <mode>, which can be 'Tubes'
            or 'Spheres'.
        """
        self.cookieDisplayMode = str(mode)
        if self.o.shape:
            self.o.shape.changeDisplayMode(self.cookieDisplayMode)
            self.o.gl_update()
            
    # methods related to exiting this mode [bruce 040922 made these
    # from old Done and Flush methods]

    def haveNontrivialState(self):
        return self.o.shape != None # note that this is stored in the glpane, but not in its assembly.

    def StateDone(self):
        if self.o.shape:
            #molmake(self.o.assy, self.o.shape) #bruce 050222 revised this call
            self.o.shape.buildChunk(self.o.assy)
        self.o.shape = None
        return None

    def StateCancel(self):
        self.o.shape = None
        # it's mostly a matter of taste whether to put this statement into StateCancel, restore_patches_by_*, or clear()...
        # it probably doesn't matter in effect, in this case. To be safe (e.g. in case of Abandon), I put it in more than one place.
        #
        # REVIEW: shouldn't we store shape in the Command object (self or self.command depending on which method we're in)
        # rather than in the glpane? Or, if it ought to be a temporary part of the model, in assy? [bruce 071012 comment]
        
        return None
        
    def restore_patches_by_Command(self):
        self.o.ortho = self.savedOrtho
        self.o.shape = None
        self.selCurve_List = []
        self.o.pov = V(self.oldPov[0], self.oldPov[1], self.oldPov[2])
    
    def Backup(self):
        if self.o.shape:
            self.o.shape.undo(self.currentLayer)
            # If no curves left, let users do what they can just like
            # when they first enter into cookie mode.
            if not self.o.shape.anyCurvesLeft():
                self.StartOver()
        self.o.gl_update()

    # mouse and key events

    def keyRelease(self,key):
        basicMode.keyRelease(self, key)
        if key == Qt.Key_Escape and self.drawingCookieSelCurve:
            self._cancelSelection()
        
    def update_cursor_for_no_MB(self):
        """
        Update the cursor for 'Cookie Cutter' mode.
        """
        if self.freeView:
            self.o.setCursor(QCursor(Qt.ArrowCursor))
            return
        if self.drawingCookieSelCurve:
            # In the middle of creating a selection curve.
            return
        if self.o.modkeys is None:
            self.o.setCursor(self.w.CookieCursor)
        elif self.o.modkeys == 'Shift':
            self.o.setCursor(self.w.CookieAddCursor)
        elif self.o.modkeys == 'Control':
            self.o.setCursor(self.w.CookieSubtractCursor)
        elif self.o.modkeys == 'Shift+Control':
            self.o.setCursor(self.w.CookieSubtractCursor)
        else:
            print "Error in update_cursor_for_no_MB(): Invalid modkey=", self.o.modkeys
        return
        
    # == LMB down-click (button press) methods
   
    def leftShiftDown(self, event):
        self.leftDown(event)

    def leftCntlDown(self, event):
        self.leftDown(event)
        
    def leftDown(self, event):
        self.select_2d_region(event)

    # == LMB drag methods

    def leftShiftDrag(self, event):
        self.leftDrag(event)
            
    def leftCntlDrag(self, event):
        self.leftDrag(event)
        
    def leftDrag(self, event):
        self.continue_selection_curve(event)

    # == LMB up-click (button release) methods

    def leftShiftUp(self, event):
        self.leftUp(event)

    def leftCntlUp(self, event):
        self.leftUp(event)
                
    def leftUp(self, event):
        self.end_selection_curve(event)
    
    # == LMB double click method

    def leftDouble(self, event):
        """End rubber selection """
        if self.freeView or not self.drawingCookieSelCurve:
            return
        
        if self.Rubber and not self.rubberWithoutMoving:
            self.defaultSelShape = SELSHAPE_LASSO
                # defaultSelShape needs to be set to SELSHAPE_LASSO here since it
                # may have been set to SELSHAPE_RECT in continue_selection_curve()
                # while creating a polygon-rubber-band selection.
            self._traditionalSelect()
        
    # == end of LMB event handlers.
        
    def select_2d_region(self, event): # Copied from selectMode(). mark 060320.
        '''Start 2D selection of a region.
        '''
        if self.o.modkeys is None:
            self.start_selection_curve(event, START_NEW_SELECTION)
        if self.o.modkeys == 'Shift':
            self.start_selection_curve(event, ADD_TO_SELECTION)
        if self.o.modkeys == 'Control':
            self.start_selection_curve(event, SUBTRACT_FROM_SELECTION)
        if self.o.modkeys == 'Shift+Control':
            self.start_selection_curve(event, SUBTRACT_FROM_SELECTION)
        return
            
    def start_selection_curve(self, event, sense):
        """Start a selection curve
        """
        
        if self.freeView: return
        if self.Rubber: return
        
        self.selSense = sense
            # <selSense> is the type of selection.
        self.selCurve_length = 0.0
            # <selCurve_length> is the current length (sum) of all the selection curve segments.
        
        self.drawingCookieSelCurve = True
            # <drawingCookieSelCurve> is used to let other methods know when
            # we are in the process of defining/drawing a selection curve, where:
            # True = in the process of defining selection curve
            # False = finished/not defining selection curve
            
        self.cookieQuat = Q(self.o.quat)
        
        ## Start color xor operations
        self.o.redrawGL = False
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_COLOR_LOGIC_OP)
        glLogicOp(GL_XOR)
        
        if not self.selectionShape in ['DEFAULT', 'LASSO']:
            # Drawing one of the other selection shapes (not polygon-rubber-band or lasso).
            return
        
        if self.selectionShape == 'LASSO':
            self.defaultSelShape = SELSHAPE_LASSO
        
        selCurve_pt, selCurve_AreaPt = self._getPoints(event)
            # _getPoints() returns a pair (tuple) of points (Numeric arrays of x,y,z)
            # that lie under the mouse pointer, just beyond the near clipping plane
            # <selCurve_pt> and in the plane of the center of view <selCurve_AreaPt>.
        self.selCurve_List = [selCurve_pt]
            # <selCurve_List> contains the list of points used to draw the selection curve.  The points lay in the 
            # plane parallel to the screen, just beyond the front clipping plane, so that they are always
            #  inside the clipping volume.
        self.o.selArea_List = [selCurve_AreaPt]
            # <selArea_List> contains the list of points that define the selection area.  The points lay in 
            # the plane parallel to the screen and pass through the center of the view.  The list
            # is used by pickrect() and pickline() to make the selection.
        self.selCurve_StartPt = self.selCurve_PrevPt = selCurve_pt
            # <selCurve_StartPt> is the first point of the selection curve.  It is used by 
            # continue_selection_curve() to compute the net distance between it and the current 
            # mouse position.
            # <selCurve_PrevPt> is the previous point of the selection curve.  It is used by 
            # continue_selection_curve() to compute the distance between the current mouse 
            # position and the previous one.
            # Both <selCurve_StartPt> and <selCurve_PrevPt> are used by 
            # basicMode.drawpick().
        
    def continue_selection_curve(self, event):
        """Add another segment to a selection curve for a lasso or polygon selection.
        """
        
        if self.freeView: return
        if not self.drawingCookieSelCurve: return
        if self.Rubber:
            # Doing a poly-rubber-band selection.  bareMotion() is updating the current rubber-band segment.
            return
        if not self.selectionShape in ['DEFAULT', 'LASSO']: return
        
        selCurve_pt, selCurve_AreaPt = self._getPoints(event)
            # The next point of the selection curve, where <selCurve_pt> is the point just beyond
            # the near clipping plane and <selCurve_AreaPt> is in the plane of the center of view.
        self.selCurve_List += [selCurve_pt]
        self.o.selArea_List += [selCurve_AreaPt]
        
        self.selCurve_length += vlen(selCurve_pt - self.selCurve_PrevPt)
            # add length of new line segment to <selCurve_length>.
            
        chord_length = vlen(selCurve_pt - self.selCurve_StartPt)
            # <chord_length> is the distance between the (first and last/current) endpoints of the 
            # selection curve.
        
        if self.selectionShape == 'DEFAULT':
            if self.selCurve_length < 2*chord_length:
            # Update the shape of the selection_curve.
            # The value of <defaultSelShape> can change back and forth between lasso and rectangle
            # as the user continues defining the selection curve.
                self.defaultSelShape = SELSHAPE_RECT
            else:
                self.defaultSelShape = SELSHAPE_LASSO
                
        self.selCurve_PrevPt = selCurve_pt
            
        env.history.statusbar_msg("Release left button to end selection; Press <Esc> key to cancel selection.")    
        self.draw_selection_curve()
        
    def end_selection_curve(self, event):
        """Close a selection curve and do the selection
        """
            
        if self.freeView or not self.drawingCookieSelCurve:
            return

        selCurve_pt, selCurve_AreaPt = self._getPoints(event)
 
        if self.selCurve_length/self.o.scale < 0.03:
            #Rect_corner/circular selection
            if not self.selectionShape in ['DEFAULT', 'LASSO']: 
                if not (self.selCurve_List and self.o.selArea_List): # The first click release
                    self.selCurve_List = [selCurve_pt]
                    self.selCurve_List += [selCurve_pt]
                    self.selCurve_List += [selCurve_pt]
                    self.o.selArea_List = [selCurve_AreaPt]
                    self.o.selArea_List += [selCurve_AreaPt]
                    if self.selectionShape == 'RECT_CORNER':    
                            self.defaultSelShape = SELSHAPE_RECT
                    #Disable view changes when begin curve drawing 
                    self.propMgr.enableViewChanges(False)
                else: #The end click release
                    self.o.selArea_List[-1] = selCurve_AreaPt
                    if self.defaultSelShape == SELSHAPE_RECT:
                        self._traditionalSelect() 
                    else:
                        self._centerBasedSelect()
            elif self.selectionShape == 'DEFAULT':  ##polygon-rubber-band/lasso selection
                self.selCurve_List += [selCurve_pt]
                self.o.selArea_List += [selCurve_AreaPt]
                if not self.Rubber:
                    # The first click of a polygon selection.
                    self.Rubber = True
                    self.rubberWithoutMoving = True
                    #Disable view changes when begin curve drawing        
                    self.propMgr.enableViewChanges(False)
            else: #This means single click/release without dragging for Lasso
                self.selCurve_List = []
                self.o.selArea_List = []
                self.drawingCookieSelCurve = False
        else: #Default(excluding rubber band)/Lasso selection
            self.selCurve_List += [selCurve_pt]
            self.o.selArea_List += [selCurve_AreaPt]
            self._traditionalSelect()    
    
    def _anyMiddleUp(self):
        if self.freeView: return
       
        if self.cookieQuat:
            self.o.quat = Q(self.cookieQuat)
            self.o.gl_update()
        else:
            self.setOrientSurf(self.o.snap2trackball())

    def middleDown(self, event):
        """Disable this method when in curve drawing"""
        if not self.drawingCookieSelCurve:
            basicMode.middleDown(self, event)
     
    def middleUp(self, event):
        """If self.cookieQuat: , which means: a shape 
        object has been created, so if you change the view,
        and thus self.o.quat, then the shape object will be wrong
        ---Huaicai 3/23/05 """
        if not self.drawingCookieSelCurve:
            basicMode.middleUp(self, event)
            self._anyMiddleUp()
           
    def middleShiftDown_ORIG(self, event):        
         """Disable this action when cutting cookie. """
         if self.freeView: basicMode.middleShiftDown(self, event)
    
    def middleCntlDown(self, event):
         """Disable this action when cutting cookie. """   
         if self.freeView: basicMode.middleCntlDown(self, event)

    def middleShiftUp_ORIG(self, event):        
         """Disable this action when cutting cookie. """   
         if self.freeView: basicMode.middleShiftUp(self, event)
    
    def middleCntlUp(self, event):        
         """Disable this action when cutting cookie. """   
         if self.freeView: basicMode.middleCntlUp(self, event)
    
    def Wheel(self, event):
        """When in curve drawing stage, disable the zooming. """
        if not self.drawingCookieSelCurve: 
            basicMode.Wheel(self, event)
        
    def bareMotion(self, event):
        if self.freeView or not self.drawingCookieSelCurve:
            return False # russ 080527        
        
        if self.Rubber or not self.selectionShape in ['DEFAULT', 'LASSO']: 
            if not self.selCurve_List: return
            p1, p2 = self._getPoints(event)
            try: 
                if self.Rubber:
                    self.pickLinePrev = self.selCurve_List[-1]
                else:
                    self.selCurve_List[-2] = self.selCurve_List[-1]
                self.selCurve_List[-1] = p1
            except:
                print self.selCurve_List
            if self.Rubber:
                self.rubberWithoutMoving = False
                env.history.statusbar_msg("Double click to end selection; Press <Esc> key to cancel selection.")
            else:
                env.history.statusbar_msg("Left click to end selection; Press <Esc> key to cancel selection.")
            self.draw_selection_curve()
            ######self.o.gl_update()
        return False # russ 080527        
   
    def _afterCookieSelection(self):
        """Restore some variable states after the each curve selection """
        if self.selCurve_List:
            self.draw_selection_curve(True)
            
            self.drawingCookieSelCurve = False
            self.Rubber = False
            self.defaultSelShape = SELSHAPE_LASSO
            self.selCurve_List = []
            self.o.selArea_List = []
            
            env.history.statusbar_msg("   ")
            # Restore the cursor when the selection is done.
            self.update_cursor_for_no_MB()
            
            #Restore GL states
            self.o.redrawGL = True
            glDisable(GL_COLOR_LOGIC_OP)
            glEnable(GL_DEPTH_TEST)
            self.o.gl_update()
     
     
    def _traditionalSelect(self):
        """The original curve selection"""
        
        # Close the selection curve and selection area.
        self.selCurve_List += [self.selCurve_List[0]]
        self.o.selArea_List += [self.o.selArea_List[0]]
        
        # bruce 041213 comment: shape might already exist, from prior drags
        if not self.o.shape:
            self.o.shape = CookieShape(self.o.right, self.o.up, self.o.lineOfSight, self.cookieDisplayMode, self.latticeType)
            self.propMgr.latticeCBox.setEnabled(False) 
            self.propMgr.enableViewChanges(False)
            
        # took out kill-all-previous-curves code -- Josh
        if self.defaultSelShape == SELSHAPE_RECT:
            self.o.shape.pickrect(self.o.selArea_List[0], self.o.selArea_List[-2], 
                    self.o.pov, self.selSense, self.currentLayer,
                                  Slab(-self.o.pov, self.o.out, self.thickness))
        else:
            self.o.shape.pickline(self.o.selArea_List, -self.o.pov, self.selSense,
                                  self.currentLayer, Slab(-self.o.pov, self.o.out, self.thickness))
        
        if self.currentLayer < (self.MAX_LAYERS - 1) and self.currentLayer == len(self.layers) - 1:
            self.propMgr.addLayerButton.setEnabled(True) 
        self._afterCookieSelection()
  
  
    def _centerBasedSelect(self):
        """Construct the right center based selection shape to generate the
         cookie. """
        if not self.o.shape:
                self.o.shape = CookieShape(self.o.right, self.o.up, self.o.lineOfSight, self.cookieDisplayMode, self.latticeType)
                self.propMgr.latticeCBox.setEnabled(False)
                self.propMgr.enableViewChanges(False)
                 
        p1 = self.o.selArea_List[1]
        p0 = self.o.selArea_List[0]
        pt = p1 - p0
        if self.selectionShape in ['RECTANGLE', 'DIAMOND']:
            hw = dot(self.o.right, pt)*self.o.right
            hh = dot(self.o.up, pt)*self.o.up
            if self.selectionShape == 'RECTANGLE':
                pt1 = p0 - hw + hh
                pt2 = p0 + hw - hh
                self.o.shape.pickrect(pt1, pt2, -self.o.pov,
                                  self.selSense, self.currentLayer,
                                  Slab(-self.o.pov, self.o.out,
                                            self.thickness))
            elif self.selectionShape == 'DIAMOND':
                pp = []
                pp += [p0 + hh]; pp += [p0 - hw]
                pp += [p0 - hh];  pp += [p0 + hw]; pp += [pp[0]]
                self.o.shape.pickline(pp, -self.o.pov, self.selSense,
                                  self.currentLayer, Slab(-self.o.pov, self.o.out, self.thickness))
  
        elif self.selectionShape in ['HEXAGON', 'TRIANGLE', 'SQUARE']:
            if self.selectionShape == 'HEXAGON': sides = 6
            elif self.selectionShape == 'TRIANGLE': sides = 3
            elif self.selectionShape == 'SQUARE': sides = 4
            
            hQ = Q(self.o.out, 2.0*math.pi/sides)
            pp = []
            pp += [p1]
            for ii in range(1, sides):
                pt = hQ.rot(pt)
                pp += [pt + p0]
            pp += [p1]
            self.o.shape.pickline(pp, -self.o.pov, self.selSense,
                                  self.currentLayer, Slab(-self.o.pov, self.o.out, self.thickness))
                                  
        elif self.selectionShape == 'CIRCLE':
            self.o.shape.pickCircle(self.o.selArea_List, -self.o.pov, self.selSense, self.currentLayer,
                                    Slab(-self.o.pov, self.o.out, self.thickness))
        
        if self.currentLayer < (self.MAX_LAYERS - 1) and self.currentLayer == len(self.layers) - 1:
                self.propMgr.addLayerButton.setEnabled(True)
        self._afterCookieSelection()                          
    
        
    def _centerRectDiamDraw(self, color, pts, sType, lastDraw):
        """Construct center based Rectange or Diamond to draw
            <Param> pts: (the center and a corner point)"""
        pt = pts[2] - pts[0]
        hw = dot(self.o.right, pt)*self.o.right
        hh = dot(self.o.up, pt)*self.o.up
        pp = []
        
        if sType == 'RECTANGLE':
            pp = [pts[0] - hw + hh]
            pp += [pts[0] - hw - hh]
            pp += [pts[0] + hw - hh]
            pp += [pts[0] + hw + hh]
        elif sType == 'DIAMOND':
            pp += [pts[0] + hh]; pp += [pts[0] - hw]
            pp += [pts[0] - hh];  pp += [pts[0] + hw]
        
        if not self.lastDrawStored:
            self.lastDrawStored += [pp]
            self.lastDrawStored += [pp]
         
        self.lastDrawStored[0] = self.lastDrawStored[1]
        self.lastDrawStored[1] = pp    
        
        if not lastDraw:
            drawLineLoop(color, self.lastDrawStored[0])
        else: self.lastDrawStored = []     
        drawLineLoop(color, pp)    
  
    
    def _centerEquiPolyDraw(self, color, sides, pts, lastDraw):
        """Construct a center based equilateral polygon to draw. 
        <Param> sides: the number of sides for the polygon
        <Param> pts: (the center and a corner point) """
        hQ = Q(self.o.out, 2.0*math.pi/sides)
        pt = pts[2] - pts[0]
        pp = []
        pp += [pts[2]]
        for ii in range(1, sides):
            pt = hQ.rot(pt)
            pp += [pt + pts[0]]
        
        if not self.lastDrawStored:
            self.lastDrawStored += [pp]
            self.lastDrawStored += [pp]
         
        self.lastDrawStored[0] = self.lastDrawStored[1]
        self.lastDrawStored[1] = pp    
        
        if not lastDraw:
            drawLineLoop(color, self.lastDrawStored[0])        
        else: self.lastDrawStored = []
        drawLineLoop(color, pp)        

   
    def _centerCircleDraw(self, color, pts, lastDraw):
        """Construct center based hexagon to draw 
        <Param> pts: (the center and a corner point)"""
        pt = pts[2] - pts[0]
        rad = vlen(pt)
        if not self.lastDrawStored:
            self.lastDrawStored += [rad]
            self.lastDrawStored += [rad]
         
        self.lastDrawStored[0] = self.lastDrawStored[1]
        self.lastDrawStored[1] = rad    
        
        if not lastDraw:
            drawCircle(color, pts[0], self.lastDrawStored[0], self.o.out)
        else:
            self.lastDrawStored = []
        
        drawCircle(color, pts[0], rad, self.o.out)

        
    def _getXorColor(self, color):
        """Get color for <color>.  When the color is XORed with background color, it will get <color>. 
        If background color is close to <color>, we'll use white color.
        """
        bg = self.backgroundColor
        diff = vlen(A(color)-A(bg))
        if diff < 0.5:
            return (1-bg[0], 1-bg[1], 1-bg[2])
        else:
            rgb = []
            for ii in range(3):
                f = int(color[ii]*255)
                b = int(bg[ii]*255)
                rgb += [(f ^ b)/255.0]
            
            return rgb    
 
    def draw_selection_curve(self, lastDraw = False):
        """Draw the selection curve."""
        color = get_selCurve_color(self.selSense, self.backgroundColor)
        color = self._getXorColor(color) 
            #& Needed since drawrectangle() in rectangle instance calls get_selCurve_color(), but can't supply bgcolor.
            #& This should be fixed.  Later.  mark 060212.
        
        if not self.selectionShape == 'DEFAULT':
            if self.selCurve_List:
                 if self.selectionShape == 'LASSO':
                     if not lastDraw:
                        for pp in zip(self.selCurve_List[:-2],self.selCurve_List[1:-1]): 
                            drawline(color, pp[0], pp[1])
                     for pp in zip(self.selCurve_List[:-1],self.selCurve_List[1:]):
                            drawline(color, pp[0], pp[1])
                 elif self.selectionShape == 'RECT_CORNER':
                     if not lastDraw:
                        drawrectangle(self.selCurve_List[0], self.selCurve_List[-2],
                                 self.o.up, self.o.right, color)
                     drawrectangle(self.selCurve_List[0], self.selCurve_List[-1],
                                 self.o.up, self.o.right, color)
                 else:
                    xor_white = self._getXorColor(white)
                    if not lastDraw:
                        drawline(xor_white, self.selCurve_List[0], self.selCurve_List[1], True)
                    drawline(xor_white, self.selCurve_List[0], self.selCurve_List[2], True)
                    if self.selectionShape in ['RECTANGLE', 'DIAMOND']:
                        self._centerRectDiamDraw(color, self.selCurve_List, self.selectionShape, lastDraw)
                    elif self.selectionShape == 'CIRCLE':
                        self._centerCircleDraw(color, self.selCurve_List, lastDraw)
                        ###A work around for bug 727
                        ######self._centerEquiPolyDraw(color, 60, self.selCurve_List, lastDraw)
                    elif self.selectionShape == 'HEXAGON':
                        self._centerEquiPolyDraw(color, 6, self.selCurve_List, lastDraw)
                    elif self.selectionShape == 'SQUARE':
                        self._centerEquiPolyDraw(color, 4, self.selCurve_List, lastDraw)
                    elif self.selectionShape == 'TRIANGLE':
                        self._centerEquiPolyDraw(color, 3, self.selCurve_List, lastDraw)   
        else: #Default selection shape
            if self.Rubber:
                if not lastDraw:
                    drawline(color, self.selCurve_List[-2], self.pickLinePrev)
                drawline(color, self.selCurve_List[-2], self.selCurve_List[-1])
            else:
                if not lastDraw:
                    for pp in zip(self.selCurve_List[:-2],self.selCurve_List[1:-1]): 
                        drawline(color, pp[0], pp[1])
                for pp in zip(self.selCurve_List[:-1],self.selCurve_List[1:]):
                    drawline(color,pp[0],pp[1])
                
                if self.defaultSelShape == SELSHAPE_RECT:  # Draw the rectangle window
                    if not lastDraw:
                        drawrectangle(self.selCurve_List[0], self.selCurve_List[-2],
                                     self.o.up, self.o.right, color)
                    drawrectangle(self.selCurve_List[0], self.selCurve_List[-1],
                                     self.o.up, self.o.right, color)
        
        glFlush()
        self.o.swapBuffers() #Update display         


    def Draw(self):
        basicMode.Draw(self)
        if self.gridShow:    
            self.griddraw()
        if self.selCurve_List: ## XOR color operation doesn't request paintGL() call.
            self.draw_selection_curve()
        if self.o.shape:
            self.o.shape.draw(self.o, self.layerColors)
        if self.showFullModel:
            self.o.assy.draw(self.o)
    
    
    def Draw_after_highlighting(self): 
        """Only draw those translucent parts of the whole model when we are requested to draw the whole model
        """
        if self.showFullModel:
            basicMode.Draw_after_highlighting(self)
        return

    
    def griddraw(self):
        """Assigned as griddraw for a diamond lattice grid that is fixed in
        space but cut out into a slab one nanometer thick parallel to the 
        screen (and is equivalent to what the cookie-cutter will cut).
        """
        # the grid is in modelspace but the clipping planes are in eyespace
        glPushMatrix()
        q = self.o.quat
        glTranslatef(-self.o.pov[0], -self.o.pov[1], -self.o.pov[2])
        glRotatef(- q.angle*180.0/math.pi, q.x, q.y, q.z)
        glClipPlane(GL_CLIP_PLANE0, (0.0, 0.0, 1.0, 6.0))
        glClipPlane(GL_CLIP_PLANE1, (0.0, 0.0, -1.0, 0.1))
        glEnable(GL_CLIP_PLANE0)
        glEnable(GL_CLIP_PLANE1)
        glPopMatrix()
        glColor3fv(self.gridColor)
        drawGrid(1.5*self.o.scale, -self.o.pov, self.latticeType)
        glDisable(GL_CLIP_PLANE0)
        glDisable(GL_CLIP_PLANE1)

   
    def makeMenus(self):
        self.Menu_spec = [
            ('Cancel', self.Cancel),
            ('Start Over', self.StartOver),
            ('Backup', self.Backup),
            ('Done', self.Done), # bruce 041217
            #None,
            #('Add New Layer', self.addLayer),
            # bruce 041103 removed Copy, per Ninad email;
            # Josh says he might implement it for Alpha;
            # if/when he does, he can uncomment the following two lines.
            ## None,
            ## ('Copy', self.copy),
         ]

    def copy(self):
        print 'NYI'

    def addLayer(self):
        """Add a new layer: the new layer will always be at the end"""
        if self.o.shape:
            lastLayerId = len(self.layers) - 1
            pov = self.layers[lastLayerId]
            pov = V(pov[0], pov[1], pov[2])
            pov -= self.o.shape.pushdown(lastLayerId)
            
            ## Make sure pushdown() doesn't return V(0,0,0)
            self.layers += [pov]
            size = len(self.layers)
           
            # Change the new layer as the current layer
            self.change2Layer(size-1)
            
            return size


    def change2Layer(self, layerIndex):
        """Change current layer to layer <layerIndex>"""
        if layerIndex == self.currentLayer: return
        
        assert layerIndex in range(len(self.layers))
        
        pov = self.layers[layerIndex]
        self.currentLayer = layerIndex
        self.o.pov = V(pov[0], pov[1], pov[2])
        
        maxCells = self._findMaxNoLattCell(self.currentLayer)
        self.propMgr.layerCellsSpinBox.setMaximum(maxCells)
       
        ##Cancel any selection if any.
        if self.drawingCookieSelCurve:
            env.history.message(redmsg("Layer changed during crystal shape creation, shape creation cancelled"))
            self._cancelSelection()
       
        self.o.gl_update()
      
        
    def _findMaxNoLattCell(self, curLay):
        """Find the possible max no of lattice cells for this layer """
        if curLay == len(self.layers) - 1:
            return self.MAX_LATTICE_CELL
        else:
            depth = vlen(self.layers[curLay+1] - self.layers[curLay])
            num = int(
                depth/(drawing_globals.DiGridSp*sqrt(self.whichsurf+1)) + 0.5)
            return num

    def setOrientSurf(self, num):
        """Set the current view orientation surface to <num>, which
        can be one of values(0, 1, 2) representing 100, 110, 111 surface respectively. """
        
        self.whichsurf = num
        self.setThickness(self.propMgr.layerCellsSpinBox.value())
        button = self.propMgr.orientButtonGroup.button(self.whichsurf)
        button.setChecked(True)     
        #self.w.statusBar().dispbarLabel.setText(button.toolTip()) #@ unnecessary. --Mark 2008-03-15

    def setThickness(self, num):
        self.thickness = num*drawing_globals.DiGridSp*sqrt(self.whichsurf+1)
        s = "%3.3f Angstroms" % (self.thickness)
        self.propMgr.layerThicknessLineEdit.setText(s)
   
    def toggleFullModel(self, showFullModel):
        """Turn on/off full model """
        self.showFullModel = showFullModel
        self.o.gl_update()
    
    def _cancelSelection(self):
        """Cancel selection before it's finished """
        self._afterCookieSelection()
        if not self.o.shape:
            self.propMgr.enableViewChanges(True)
        
    
    def changeLatticeType(self, lType):
        """Change lattice type as 'lType'. """
        self.latticeType = self.LATTICE_TYPES[lType]
        self.o.gl_update()
    
    def changeSelectionShape(self, newShape):
        if newShape != self.selectionShape:
            #Cancel current selection if any. Otherwise, it may cause
            #bugs like 587
            if self.selCurve_List: ##
                env.history.message(redmsg("Current crystal shape creation cancelled as a different shape profile is selected. "))
                self._cancelSelection()
            self.selectionShape = newShape
    
    def _project2Plane(self, pt):
        """Project a 3d point <pt> into the plane parallel to screen and through "pov". 
            Return the projected point. """
        op = -self.o.pov
        np = self.o.lineOfSight
        
        v1 = op - pt
        v2 = dot(v1, np)*np
        
        vr = pt + v2
        return vr
 
    def _snap100Grid(self, cellOrig, bLen, p2):
        """Snap point <p2> to its nearest 100 surface grid point"""
        orig3d = self._project2Plane(cellOrig)
        out = self.o.out
        sqrt2 = 1.41421356/2
        if abs(out[2]) > 0.5:
            rt0 = V(1, 0, 0)
            up0 = V(0,1, 0)
            right = V(sqrt2, -sqrt2, 0.0)
            up = V(sqrt2, sqrt2, 0.0)
        elif abs(out[0]) > 0.5:
            rt0 = V(0, 1, 0)
            up0 = V(0, 0, 1)
            right = V(0.0, sqrt2, -sqrt2)
            up = V(0.0, sqrt2, sqrt2)
        elif abs(out[1]) > 0.5:
            rt0 = V(0, 0, 1)
            up0 = V(1, 0, 0)
            right = V(-sqrt2, 0.0, sqrt2)
            up = V(sqrt2, 0.0, sqrt2)    
       
        pt1 = p2 - orig3d
        pt = V(dot(rt0, pt1), dot(up0, pt1))
        pt -= V(2*bLen, 2*bLen)
            
        pt1 = V(sqrt2*pt[0]-sqrt2*pt[1], sqrt2*pt[0]+sqrt2*pt[1])
      
        dx = pt1[0]/(2*sqrt2*bLen)
        dy = pt1[1]/(2*sqrt2*bLen)
        if dx > 0: dx += 0.5
        else: dx -= 0.5
        ii = int(dx)
        if dy > 0: dy += 0.5
        else: dy -= 0.5
        jj = int(dy)
            
        nxy = orig3d + 4*sqrt2*bLen*up + ii*2*sqrt2*bLen*right + jj*2*sqrt2*bLen*up
        
        return nxy
 
 
    def _snap110Grid(self, offset, p2):
        """Snap point <p2> to its nearest 110 surface grid point"""
        uLen = 0.87757241
        DELTA = 0.0005

        if abs(self.o.out[1]) < DELTA: #Looking between X-Z
                if self.o.out[2]*self.o.out[0] < 0:
                    vType = 0  
                    right = V(1, 0, 1)
                    up = V(0, 1, 0)
                    rt = V(1, 0, 0)
                else: 
                    vType = 2  
                    if self.o.out[2] < 0:
                        right = V(-1, 0, 1)
                        up = V(0, 1, 0)
                        rt = V(0, 0, 1)
                    else: 
                        right = V(1, 0, -1)
                        up = V(0, 1, 0)
                        rt = V(1, 0, 0)
        elif abs(self.o.out[0]) < DELTA: # Looking between Y-Z
            if self.o.out[1] * self.o.out[2] < 0:  
                vType = 0
                right = V(0, 1, 1)
                up = V(1, 0, 0)
                rt = V(0, 0, 1)
            else:
                vType = 2
                if self.o.out[2] > 0: 
                    right = V(0, -1, 1)
                    up = V(1, 0, 0)
                    rt = V(0, 0, 1)
                else:
                    right = V(0, 1, -1)
                    up = V(1, 0, 0)
                    rt = V(0, 1, 0)
        elif abs(self.o.out[2]) < DELTA: # Looking between X-Y
            if self.o.out[0] * self.o.out[1] < 0:
                vType = 0
                right = V(1, 1, 0)
                up = V(0, 0, 1)
                rt = (1, 0, 0)
            else:
                vType = 2
                if self.o.out[0] < 0:        
                    right = V(1, -1 , 0)
                    up = V(0, 0, 1)
                    rt = (1, 0, 0)
                else:
                    right = V(-1, 1, 0)
                    up = V(0, 0, 1)
                    rt = V(0, 1, 0)
        else: ##Sth wrong
            raise ValueError, self.out
        
        orig3d = self._project2Plane(offset)
        p2 -= orig3d
        pt = V(dot(rt, p2), dot(up, p2))
        
        if vType == 0:  ## projected orig-point is at the corner
            if pt[1] < uLen:
                uv1 = [[0,0], [1,1], [2, 0], [3, 1], [4, 0]]
                ij = self._findSnap4Corners(uv1, uLen, pt)
            elif pt[1] < 2*uLen:
                if pt[0] < 2*uLen:
                    if pt[1] < 1.5*uLen: ij = [1, 1]
                    else: ij = [1, 2]
                else:
                    if pt[1] < 1.5*uLen: ij = [3, 1]
                    else: ij = [3, 2]
            elif pt[1] < 3*uLen:
                uv1 = [[0,3], [1,2], [2,3], [3, 2], [4, 3]]
                ij = self._findSnap4Corners(uv1, uLen, pt)
            else:
                if pt[1] < 3.5*uLen: j = 3
                else: j = 4
                if pt[0] < uLen: i = 0
                elif pt[0] < 3*uLen: i = 2
                else: i = 4
                ij = [i, j]
        
        elif vType == 2: ## projected orig-point is in the middle
             if pt[1] < uLen:
                 if pt[1] < 0.5*uLen: j = 0
                 else: j = 1
                 if pt[0] < -1*uLen: i = -2
                 elif pt[0] < uLen: i = 0
                 else: i = 2
                 ij = [i, j]
             elif pt[1] < 2*uLen:
                 uv1 = [[-2, 1], [-1, 2], [0, 1], [1, 2], [2, 1]]
                 ij = self._findSnap4Corners(uv1, uLen, pt)
             elif pt[1] < 3*uLen:
                 if pt[1] < 2.5*uLen: j = 2
                 else: j = 3
                 if pt[0] < 0: i = -1
                 else: i = 1
                 ij = [i, j]
             else:
                 uv1 = [[-2, 4], [-1, 3], [0, 4], [1, 3], [2, 4]]
                 ij = self._findSnap4Corners(uv1, uLen, pt)
        
        nxy = orig3d + ij[0]*uLen*right + ij[1]*uLen*up
        return nxy
    
    
    def _getNCartP2d(self, ax1, ay1, pt):
        """Axis <ax> and <ay> is not perpendicular, so we project pt to axis
        <ax> or <ay> by parallel to <ay> or <ax>. The returned 2d coordinates are not cartesian coordinates """
        
        ax = norm(ax1)
        ay = norm(ay1)
        try:
            lx = (ay[1]*pt[0] - ay[0]*pt[1])/(ax[0]*ay[1] - ay[0]*ax[1])
            ly = (ax[1]*pt[0] - ax[0]*pt[1])/(ax[1]*ay[0] - ax[0]*ay[1])
        except ZeroDivisionError:
            print " In _getNCartP2d() of cookieMode.py, divide-by-zero detected."
            return None
        
        return V(lx, ly)
        
    
    def _snap111Grid(self, offset, p2):
        """Snap point <p2> to its nearest 111 surface grid point"""
        DELTA = 0.00005
        uLen = 0.58504827
        
        sqrt6 = sqrt(6)
        orig3d = self._project2Plane(V(0, 0,0))
        p2 -= orig3d
        
        if (self.o.out[0] > 0 and self.o.out[1] > 0 and self.o.out[2] > 0) or \
                (self.o.out[0] < 0 and self.o.out[1] < 0 and self.o.out[2] < 0):
            axy =[V(1, 1, -2), V(-1, 2, -1),  V(-2, 1, 1), V(-1, -1, 2), V(1, -2, 1), V(2, -1, -1), V(1, 1, -2)]
        elif (self.o.out[0] < 0 and self.o.out[1] < 0 and self.o.out[2] > 0) or \
                (self.o.out[0] > 0 and self.o.out[1] > 0 and self.o.out[2] < 0):
            axy =[V(1, -2, -1), V(2, -1, 1),  V(1, 1, 2), V(-1, 2, 1), V(-2, 1, -1), V(-1, -1, -2), V(1, -2, -1)]
        elif (self.o.out[0] < 0 and self.o.out[1] > 0 and self.o.out[2] > 0) or \
                (self.o.out[0] > 0 and self.o.out[1] < 0 and self.o.out[2] < 0):
            axy =[V(2, 1, 1), V(1, 2, -1),  V(-1, 1, -2), V(-2, -1, -1), V(-1, -2, 1), V(1, -1, 2), V(2, 1, 1)]
        elif (self.o.out[0] > 0 and self.o.out[1] < 0 and self.o.out[2] > 0) or \
                (self.o.out[0] < 0 and self.o.out[1] > 0 and self.o.out[2] < 0):
            axy =[V(-1, -2, -1), V(1, -1, -2),  V(2, 1, -1), V(1, 2, 1), V(-1, 1, 2), V(-2, -1, 1), V(-1, -2, -1)]
        
        vlen_p2 = vlen(p2)
        if vlen_p2 < DELTA:
            ax = axy[0]
            ay = axy[1]
        else:
            for ii in range(size(axy) -1):
                cos_theta = dot(axy[ii], p2)/(vlen(axy[ii])*vlen_p2)
                ## the 2 vectors has an angle > 60 degrees 
                if cos_theta < 0.5: continue
                cos_theta = dot(axy[ii+1], p2)/(vlen(axy[ii+1])*vlen_p2)
                if cos_theta > 0.5:  
                    ax = axy[ii]
                    ay = axy[ii+1]
                    break
       
        p2d = self._getNCartP2d(ax, ay, p2)
        
        i = intRound(p2d[0]/uLen/sqrt6)
        j = intRound(p2d[1]/uLen/sqrt6)
        
        nxy = orig3d + i*uLen*ax + j*uLen*ay 
        
        return nxy
        
    
    def _findSnap4Corners(self, uv1, uLen, pt, vLen = None):
        """Compute  distance from point <pt> to corners and select the nearest corner."""
        if not vLen: vLen = uLen
        hd = 0.5*sqrt(uLen*uLen + vLen*vLen)
        
        ix = int(floor(pt[0]/uLen)) - uv1[0][0]
        if ix == -1: ix = 0
        elif ix == (len(uv1) - 1): ix = len(uv1) - 2
        elif ix < -1 or ix >= len(uv1): raise ValueError, (uv1, pt, uLen, ix)
        
        dist = vlen(V(uv1[ix][0]*uLen, uv1[ix][1]*vLen) - pt)
        if dist < hd:
            return uv1[ix]
        else: return uv1[ix+1]

    
    def _getPoints(self, event):
        """This method is used to get the points in near clipping plane and pov plane which are in line 
        with the mouse clicking point on the screen plane. Adjust these 2 points if self.snapGrid == True.
        <event> is the mouse event.
        Return a tuple of those 2 points.
        """
        p1, p2 = self.o.mousepoints(event, 0.01)
        # For each curve, the following value is constant, so it could be
        # optimized by saving it to the curve object.
        vlen_p1p2 = vlen(p1 - p2) 
        
        if not self.gridSnap: 
            return p1, p2
        else: # Snap selection point to grid point
             cellOrig, uLen = findCell(p2, self.latticeType)
             
             if self.whichsurf == 0: p2 = self._snap100Grid(cellOrig, uLen, p2)
             elif self.whichsurf == 1: p2 = self._snap110Grid(cellOrig, p2)
             else: p2 = self._snap111Grid(cellOrig, p2)
             
             return p2 + vlen_p1p2*self.o.out, p2
  
    pass # end of class cookieMode

# == helper functions

def hashAtomPos(pos):
        return int(dot(V(1000000, 1000,1),floor(pos*1.2)))

# make a new Chunk using a cookie-cut shape

# [bruce 050222 changed this from an assembly method to a cookieMode function
#  (since it's about cookies made from diamond, like this file),
#  and moved it from assembly.py to cookieMode.py, but changed nothing else
#  except renaming self->assy and adding some comments.]

def molmake(assy,shap):
    assy.changed() # The file and the part are now out of sync.
        #bruce 050222 comment: this is not needed, since it's done by addmol
    shap.combineLayers()    
    if not shap.curves: return
    #@@@ ninad20070511 : Is the followinf ever used?? I found another code
    # which eventually decided the chunk name after Crystal creation. 
    # it is in shape.py -> buildChunk method
    mol = Chunk(assy, gensym("Crystal", assy))
    ndx={}
    hashAtomPos #bruce 050222 comment: this line is probably a harmless typo, should be removed
    bbhi, bblo = shap.bbox.data
    # Widen the grid enough to get bonds that cross the box
    allCells = drawing_globals.genDiam(bblo-1.6, bbhi+1.6, shap.latticeType)
    for cell in allCells:
        for pp in cell:
            pp0 = pp1 = None
            if shap.isin(pp[0]):
                pp0h = hashAtomPos(pp[0])
                if pp0h not in ndx:
                    pp0 = Atom("C", pp[0], mol)
                    ndx[pp0h] = pp0
                else: pp0 = ndx[pp0h]
            if shap.isin(pp[1]):
                pp1h = hashAtomPos(pp[1])
                if pp1h not in ndx:
                    pp1 = Atom("C", pp[1], mol)
                    ndx[pp1h] = pp1
                else: pp1 = ndx[pp1h]
            if pp0 and pp1: mol.bond(pp0, pp1)
            elif pp0:
                x = Atom("X", (pp[0] + pp[1]) / 2.0, mol)
                mol.bond(pp0, x)
            elif pp1:
                x = Atom("X", (pp[0] + pp[1]) / 2.0, mol)
                mol.bond(pp1, x)
   
    #Added by huaicai to fixed some bugs for the 0 atoms Chunk 09/30/04
    # [bruce 050222 comment: I think Huaicai added the condition, not the body,
    #  i.e. before that it was effectively "if 1".]
    if len(mol.atoms) > 0:
        #bruce 050222 comment: much of this is not needed, since mol.pick() does it.
        # Note: this method is similar to one in shape.py.
        assy.addmol(mol)
        assy.unpickall_in_GLPane() # was unpickparts; not sure _in_GLPane is best (or that this is needed at all) [bruce 060721]
        mol.pick()
        assy.mt.mt_update()

    return # from molmake

# end
