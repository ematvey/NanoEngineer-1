# Copyright 2008 Nanorex, Inc.  See LICENSE file for details.
"""

@author: Ninad
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details.
@version:$Id$

History:

TODO: 2008-04-20
- Created a support a NFR to rotate about a point just before FNANO 2008
conference. This may be revised further.
-- Need documentation
"""

from temporary_commands.LineMode import LineMode
from temporary_commands.LineMode import LineMode_GM
import foundation.env as env
from utilities.prefs_constants import atomHighlightColor_prefs_key
from model.chem import Atom # for isinstance check as of 2008-04-17

from geometry.VQT import cross, norm, Q
from Numeric import dot



_superclass_for_GM = LineMode_GM

class RotateAboutPoint_GraphicsMode(LineMode_GM):

    pivotAtom = None

    def Enter_GraphicsMode(self):
        #TODO: use this more widely,  than calling grapicsMode.resetVariables
        #in command.restore_GUI. Need changes in superclasses etc
        #-- Ninad 2008-04-17
        self.resetVariables() # For safety

    def resetVariables(self):
        _superclass_for_GM.resetVariables(self)
        self.pivotAtom = None


    def leftDown(self, event):
        """
        Event handler for LMB press event.
        """
        #The endPoint1 and self.endPoint2 are the mouse points at the 'water'
        #surface. Soon, support will be added so that these are actually points
        #on a user specified reference plane. Also, once any temporary mode
        # begins supporting highlighting, we can also add feature to use
        # coordinates of a highlighted object (e.g. atom center) as endpoints
        # of the line
        farQ_junk, self.endPoint1 = self.dragstart_using_GL_DEPTH( event)

        if self._snapOn and self.endPoint2 is not None:
            # This fixes a bug. Example: Suppose the dna line is snapped to a
            # constraint during the bare motion and the second point is clicked
            # when this happens, the second clicked point is the new
            #'self.endPoint1'  which needs to be snapped like we did for
            # self.endPoint2 in the bareMotion. Setting self._snapOn to False
            # ensures that the cursor is set to the simple Pencil cursor after
            # the click  -- Ninad 2007-12-04
            self.endPoint1 = self.snapLineEndPoint()
            self._snapOn = False


        if isinstance(self.glpane.selobj, Atom):
            self.pivotAtom = self.glpane.selobj
            #note that using selobj as self.endPoint1 is NIY.

        self.command.mouseClickPoints.append(self.endPoint1)
        return

    def leftUp(self, event):
        """
        Event handler for Left Mouse button left-up event
        """
        if  self.command.mouseClickLimit is None:
            if len(self.command.mouseClickPoints) == 2:
                self.endPoint2 = None
                self.command.rotateAboutPoint()
                self.command.restore_gui()
                self.glpane.gl_update()
            return


        assert len(self.command.mouseClickPoints) <= self.command.mouseClickLimit

        if len(self.command.mouseClickPoints) == self.command.mouseClickLimit:
            self.endPoint2 = None
            self._snapOn = False
            self._standardAxisVectorForDrawingSnapReference = None
            self.glpane.gl_update()
            self.command.rotateAboutPoint()
            self.command.Done(exit_using_done_or_cancel_button = False)
            return


    def _getAtomHighlightColor(self, selobj):
        return env.prefs[atomHighlightColor_prefs_key]

    def update_cursor_for_no_MB(self):
        """
        Update the cursor for this mode.
        """
        if self._snapOn:
            if self._snapType == 'HORIZONTAL':
                self.glpane.setCursor(self.win.rotateAboutPointHorizontalSnapCursor)
            elif self._snapType == 'VERTICAL':
                self.glpane.setCursor(self.win.rotateAboutPointVerticalSnapCursor)
        else:
            self.glpane.setCursor(self.win.rotateAboutPointCursor)


class RotateAboutPoint_Command(LineMode):

    GraphicsMode_class = RotateAboutPoint_GraphicsMode

    commandName = 'RotateAboutPoint'
    default_mode_status_text = ""
    featurename = "Rotate About Point"
        # (I don't know if this featurename is ever user-visible;
        #  if it is, it's probably wrong -- consider overriding
        #  self.get_featurename() to return the value from the
        #  prior command, if this is used as a temporary command.
        #  The default implementation returns this constant
        #  or (if it's not overridden in subclasses) something
        #  derived from it. [bruce 071227])

    def rotateAboutPoint(self):
        """
        Rotates the selected entities along the specified vector, about the
        specified pivot point (pivot point it the starting point of the
        drawn vector.
        """
        startPoint = self.mouseClickPoints[0]
        endPoint = self.mouseClickPoints[1]
        pivotAtom = self.graphicsMode.pivotAtom
        #initial assignment of reference_vec. The selected movables will be
        #rotated by the angle between this vector and the lineVector
        reference_vec = self.glpane.right
        if isinstance(pivotAtom, Atom) and not pivotAtom.molecule.isNullChunk():
            mol = pivotAtom.molecule
            reference_vec, node_junk = mol.getAxis_of_self_or_eligible_parent_node(
                atomAtVectorOrigin = pivotAtom)
            del node_junk
        else:
            reference_vec = self.glpane.right

        lineVector = endPoint - startPoint

        quat1 = Q(lineVector, reference_vec)

        #DEBUG Disabled temporarily . will not be used
        ##if dot(lineVector, reference_vec) < 0:
            ##theta = math.pi - quat1.angle
        ##else:
            ##theta = quat1.angle

        #TEST_DEBUG-- Works fine
        theta = quat1.angle

        rot_axis = cross(lineVector, reference_vec)

        if dot(lineVector, reference_vec) < 0:
            rot_axis = - rot_axis

        cross_prod_1 = norm(cross(reference_vec, rot_axis))
        cross_prod_2 = norm(cross(lineVector, rot_axis))

        if dot(cross_prod_1, cross_prod_2) < 0:
            quat2 = Q(rot_axis,  theta)
        else:
            quat2 = Q(rot_axis,  - theta)


        movables = self.graphicsMode.getMovablesForLeftDragging()
        self.assy.rotateSpecifiedMovables(
            quat2,
            movables = movables,
            commonCenter = startPoint)

        self.glpane.gl_update()


    def restore_gui(self):
        """
        Restore the GUI
        """

        prevMode = self.commandSequencer.prevMode
        #Clean this up -- acceptParamsFromTemporaryMode is only needed for the
        #unchecking the 'RotateAboutPoint checkbox in the previous mode
        #(ie in the Mov Property Manager. )

        if hasattr(prevMode, 'acceptParamsFromTemporaryMode'):
            params = ()
            prevMode.acceptParamsFromTemporaryMode(
                self.commandName,
                params)
            #clear the list
            self.mouseClickPoints = []

        self.graphicsMode.resetVariables()
        return
