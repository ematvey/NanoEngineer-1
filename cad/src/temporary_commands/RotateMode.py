# Copyright 2005-2007 Nanorex, Inc.  See LICENSE file for details. 
"""
Rotate mode functionality.

@author:    Mark Sims
@version:   $Id: RotateMode.py 12433 2008-04-09 22:53:02Z russfish $
@copyright: 2005-2007 Nanorex, Inc.  See LICENSE file for details.
@license:   GPL
"""

from temporary_commands.TemporaryCommand import TemporaryCommand_Overdrawing

### from utilities.debug import doProfile   ###
### clicked = False                         ###

# == GraphicsMode part

class RotateMode_GM( TemporaryCommand_Overdrawing.GraphicsMode_class ):
    """
    Custom GraphicsMode for use as a component of RotateMode.
    """
    def leftDown(self, event):
        ### global clicked                  ###
        ### clicked = True                  ###
        self.glpane.SaveMouse(event)
        self.glpane.trackball.start(self.glpane.MousePos[0],
                                    self.glpane.MousePos[1])
        self.picking = False
        return
        
    def leftDrag(self, event):
        ### global clicked                  ###
        ### if clicked:                     ###
        ###     doProfile(True)             ###
        ###     clicked = False             ###

        self.glpane.SaveMouse(event)
        q = self.glpane.trackball.update(self.glpane.MousePos[0],
                                         self.glpane.MousePos[1])
        self.glpane.quat += q 
        self.glpane.gl_update()
        self.picking = False
        return
        
    def update_cursor_for_no_MB(self): # Fixes bug 1638. Mark 3/12/2006
        """
        Update the cursor for 'Rotate' mode.
        """
        self.glpane.setCursor(self.win.RotateViewCursor)
        return

    pass

# == Command part

class RotateMode(TemporaryCommand_Overdrawing): # TODO: rename to RotateTool or RotateCommand or TemporaryCommand_Rotate or ...
    """
    Encapsulates the Rotate Tool functionality.
    """
    
    # class constants
    commandName = 'ROTATE'
    default_mode_status_text = "Tool: Rotate"
    featurename = "Rotate Tool"

    GraphicsMode_class = RotateMode_GM

    def init_gui(self):
        # Toggle on the Rotate Tool icon
        self.win.rotateToolAction.setChecked(1)
    
    def restore_gui(self):
        # Toggle off the Rotate Tool icon
        self.win.rotateToolAction.setChecked(0)

    pass

# end
