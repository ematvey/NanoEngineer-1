# Copyright 2007 Nanorex, Inc.  See LICENSE file for details. 
"""
test_connectWithState.py -- test the connectWithState features.
Also serves as scratch code for their improvement.
 
$Id: test_connectWithState.py 12879 2008-05-21 16:22:55Z russfish $

History:

070830 bruce split this out of test_commands.py
"""

from prototype.test_connectWithState_constants import CYLINDER_HEIGHT_PREFS_KEY, CYLINDER_HEIGHT_DEFAULT_VALUE
from prototype.test_connectWithState_constants import cylinder_round_caps
##from test_connectWithState_constants import CYLINDER_VERTICAL_DEFAULT_VALUE
from prototype.test_connectWithState_constants import CYLINDER_WIDTH_DEFAULT_VALUE
    ### better to define here... ### REVISE

    ### REVISE: the default value should come from the stateref, when using the State macro,
    # so it can be defined only in this file and not needed via globals by the PM

# REVISE: the following should just be the stateref's get_value and set_value methods.
# And -- to be realistic, we should find some setting that is more sensible to store in prefs,
# and make a prefs stateref for that setting rather than for what ought to be a model
# object attribute.

def cylinder_height():
    import foundation.env as env
    return env.prefs.get( CYLINDER_HEIGHT_PREFS_KEY, CYLINDER_HEIGHT_DEFAULT_VALUE)

def set_cylinder_height(val):
    import foundation.env as env
    env.prefs[CYLINDER_HEIGHT_PREFS_KEY] = val

# REVISE: for prefs state, what is defined in what file?
# can we make the PM code not even know whether specific state is defined in prefs or in the mode or in a node?
# (i don't yet know how, esp for state in a node where the choice of nodes depends on other state,
#  but it's a good goal -- do we need to get the stateref itself from the command in a standard way? ### REVIEW)

# RELATED ISSUE: are staterefs useful when we don't have a UI to connect widgets to them? guess: yes.

# RELATED: can there be an object with modifiable attrs which refers to prefs values?
# If there was, the attr names would come from where? (the table in preferences.py i guess)
# Or, always define them in your own objs as needed using a State-like macro??


# === PM class

from prototype.test_connectWithState_PM import test_connectWithState_PM


# === GraphicsMode and Command classes

from prototype.test_commands import ExampleCommand

from geometry.VQT import V
from geometry.VQT import cross

from utilities.constants import pink, white
# TODO: import the following from somewhere
DX = V(1,0,0)
DY = V(0,1,0)
ORIGIN = V(0,0,0)
from graphics.drawing.CS_draw_primitives import drawcylinder
from graphics.drawing.CS_draw_primitives import drawsphere
from exprs.ExprsMeta import ExprsMeta
from exprs.instance_helpers import IorE_guest_mixin
from exprs.attr_decl_macros import Instance, State
from exprs.__Symbols__ import _self
from exprs.Exprs import call_Expr ## , tuple_Expr ### TODO: USE tuple_Expr
from exprs.Center import Center

from exprs.Rect import Rect # used to make our drag handle appearance

from exprs.DraggableHandle import DraggableHandle_AlongLine
from exprs.If_expr import If_expr

from widgets.prefs_widgets import ObjAttr_StateRef

class State_preMixin( IorE_guest_mixin):
    # TODO: refile (alongside IorE_guest_mixin ? in its own file?), once cleaned up & bugfixed --
    # note, as of 080128 or so, this is used in real code
    """
    Use this as the *first* superclass (thus the _preMixin in the name)
    in order to permit use of the State macro in the class assignments
    which set up instance variable defaults in a given class.
    The glpane must be passed as the first argument to __init__.
    """
    # the following are needed for now in order to use the State macro,
    # along with the IorE_guest_mixin superclass; this may be cleaned up:
    __metaclass__ = ExprsMeta
    _e_is_instance = True ### REVIEW: can the superclass define this, since to work as a noninstance you need a special subclass?
    _e_has_args = True # not needed -- only purpose is to remove "w/o a" from repr(self)

    def __init__(self, glpane, *args, **kws):
        
        #Following flag , if True, enables some debug prints in console
        debug_init = False 
        if debug_init:
            print "State_preMixin.__init__", glpane, args, kws
        IorE_guest_mixin.__init__(self, glpane)

        # REVIEW: should callers do the following, not us?
        if debug_init:
            print " State_preMixin.__init__ will call", super(State_preMixin, self).__init__
                ## <bound method test_connectWithState.__init__ of <test_connectWithState#4789(i w/o a)>>

            # note: the following debug output suggests that this would cause
            # infinite recursion, but something prevents it from happening at all
            # (it seems likely that no call at all is happening, but this is not yet
            #  fully tested -- maybe something different is called from what's printed)
            #
            ##debug fyi: starting DnaSegment_EditCommand.__init__
            ##State_preMixin.__init__ <GLPane 0> () {}
            ## State_preMixin.__init__ will call <bound method DnaSegment_EditCommand.__init__ of <DnaSegment_EditCommand#6986(i)>>
            ## State_preMixin.__init__ returned from calling <bound method DnaSegment_EditCommand.__init__ of <DnaSegment_EditCommand#6987(i)>>
            ##debug fyi: inside DnaSegment_EditCommand.__init__, returned from State_preMixin.__init__
            
        super(State_preMixin, self).__init__(glpane, *args, **kws)
            # this is not calling ExampleCommand.__init__ as I hoped it would. I don't know why. ###BUG
            # (but is it calling anything? i forget. clarify!)
        if debug_init:
            print " State_preMixin.__init__ returned from calling", super(State_preMixin, self).__init__
    pass


class _test_connectWithState_GM(ExampleCommand.GraphicsMode_class):
    """
    Custom GraphicsMode for test_connectWithState.
    """
    
    # bruce 071022 split this out, leaving all attrs in self.command
    # [REVIEW -- do some attrs (and therefore some or all of the
    #  exprs overhead) belong here? Guess: yes.]
    
    def Draw(self):

        # TODO: also super draw, for model, axes, etc?
        
        color = self.command.cylinderColor
        length = cylinder_height()
##        if self.command.cylinderVertical:
##            direction = DY
##        else:
##            direction = DX
        direction = self.command.direction
        end1 = ORIGIN - direction * length/2.0
        end2 = ORIGIN + direction * length/2.0
        radius = self.command.cylinderWidth / 2.0
        capped = True
        drawcylinder(color, end1, end2, radius, capped)

        if cylinder_round_caps():
            detailLevel = 2
            drawsphere( color, end1, radius, detailLevel)
            drawsphere( color, end2, radius, detailLevel)

        if self.command.widthHandleEnabled:
            self.command.widthHandle.draw()

        super(_test_connectWithState_GM, self).Draw() # added this, bruce 071022
        return
    pass


class test_connectWithState(State_preMixin, ExampleCommand):

    # class constants needed by mode API for example commands
    commandName = 'test_connectWithState-commandName'
    default_mode_status_text = "test_connectWithState"
    featurename = "Prototype: Test connectWithState"
    PM_class = test_connectWithState_PM

    # tracked state -- this initializes specially defined instance variables
    # which will track all their uses and changes so that connectWithState
    # works for them:
    cylinderVertical = State(bool, False)
    cylinderWidth = State(float, CYLINDER_WIDTH_DEFAULT_VALUE)
        # TODO: soon this will be the only use of this constant, so it can be inlined
    cylinderColor = State('color-stub', pink) # type should be Color (nim), but type is not yet used
    
        # note: you can add _e_debug = True to one or more of these State definitions
        # to see debug prints about some accesses to this state.

    GraphicsMode_class = _test_connectWithState_GM
    
    # init methods
    
    def __init__(self, glpane):
        # I don't know why this method is needed. ##### REVIEW (super semantics), FIX or clean up
        super(test_connectWithState, self).__init__(glpane) # State_preMixin.__init__
        ExampleCommand.__init__(self, glpane) # (especially this part)
        return

##    def __init__(self, glpane):
##        super(test_connectWithState, self).__init__(glpane)
####            # that only calls some mode's init method,
####            # so (for now) call this separately:
####        IorE_guest_mixin.__init__(self, glpane)
##        return

    # exprs-based formulae (and some compute methods)
    direction = If_expr( cylinderVertical, DY, DX )
    def _C_width_direction(self):
        """
        compute self.width_direction
        """
        # Note: to do this with a formula expr instead
        # would require cross_Expr to be defined,
        # and glpane.lineOfSight to be tracked.
        return cross( self.direction, self.env.glpane.lineOfSight )
    width_direction = _self.width_direction # so it can be used in formulae below

    # stub for handle test code [070912]
    
    widthHandleEnabled = True # stub
    ## widthHandle = Instance(Rect()) # stub
    h_offset = 0.5 + 0.2 # get it from handle? nah (not good if that changes with time); just make it fit.
        # or we could decide that handles ought to have useful fixed bounding boxes...
##    widthHandle = Instance(Translate(Center(Rect(0.5)),
##                                     width_direction * (cylinderWidth / 2.0 + h_offset) )) #stub
    widthHandle = Instance( DraggableHandle_AlongLine(
        appearance = Center(Rect(0.5, 0.5, white)),
        ### REVIEW:
        # Can't we just replace the following with something based on the formula for the position,
        #   width_direction * (cylinderWidth / 2.0 + h_offset)
        # ?
        # As it is, I have to manually solve that formula for origin and direction to pass in,
        # i.e. rewrite it as
        #   position = origin + direction * cylinderWidth
        ## height_ref = cylinderWidth, ###WRONG
##        height_ref = ObjAttr_StateRef( _self, 'cylinderWidth'),
##            ## AssertionError: ObjAttr_StateRef fallback is nim -- needed for S._self
        height_ref = call_Expr( ObjAttr_StateRef, _self, 'cylinderWidth'), # guess at workaround; #e we need a more principled way!
            ### REVIEW: efficient enough? (guess: overhead only happens once, so yes)
            # could we say instead something like: height_ref = Variable(cylinderWidth) ?? Or VariableRef? Or StateRef_to ?
        origin = width_direction * h_offset, # note: also includes cylinder center, but that's hardcoded at ORIGIN
        direction = width_direction / 2.0,
        sbar_text = "cylinder width", ### TODO: make it a formula, include printed value of width?
        range = (0.1, 10),
            ### TODO: DraggableHandle_AlongLine should take values from the stateref if this option is not provided;
            # meanwhile, we ought to pass a consistent value!
    ))
        # Note: the Instance is required; but I'm not sure if it would be
        # if we were using a fuller exprs superclass or init code. [bruce 070912]

    def cmd_Bigger(self):
        self.cylinderWidth += 0.5
        set_cylinder_height( cylinder_height() + 0.5)
        # TODO: enforce maxima
        return

    def cmd_Smaller(self):
        self.cylinderWidth -= 0.5
        set_cylinder_height( cylinder_height() - 0.5)
        # enforce minima (###BUG: not the same ones as declared in the PM)
        ### REVISE: min & max should be declared in State macro and (optionally) enforced by it
        if self.cylinderWidth < 0.1:
            self.cylinderWidth = 0.1
        if cylinder_height() < 0.1:
            set_cylinder_height(0.1)
        return
    
    pass

# end
