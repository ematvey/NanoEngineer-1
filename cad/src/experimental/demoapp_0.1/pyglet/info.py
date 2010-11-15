# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

'''Get environment information useful for debugging.

Intended usage is to create a file for bug reports, e.g.::

    python -m pyglet.info > info.txt

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: info.py 13191 2008-06-17 21:46:54Z brucesmith $'

_first_heading = True
def _heading(heading):
    global _first_heading
    if not _first_heading:
        print
    else:
        _first_heading = False
    print heading
    print '-' * 78

def dump_python():
    '''Dump Python version and environment to stdout.'''
    import os
    import sys
    print 'sys.version:', sys.version
    print 'sys.platform:', sys.platform
    print 'os.getcwd():', os.getcwd()
    for key, value in os.environ.items():
        if key.startswith('PYGLET_'):
            print "os.environ['%s']: %s" % (key, value)

def dump_pyglet():
    '''Dump pyglet version and options.'''
    import pyglet
    print 'pyglet.version:', pyglet.version
    print 'pyglet.__file__:', pyglet.__file__
    for key, value in pyglet.options.items():
        print "pyglet.options['%s'] = %r" % (key, value)

def dump_window():
    '''Dump display, windowm, screen and default config info.'''
    import pyglet.window
    platform = pyglet.window.get_platform()
    print 'platform:', repr(platform)
    display = platform.get_default_display()
    print 'display:', repr(display)
    screens = display.get_screens()
    for i, screen in enumerate(screens):
        print 'screens[%d]: %r' % (i, screen)
    window = pyglet.window.Window(visible=False)
    for key, value in window.config.get_gl_attributes():
        print "config['%s'] = %r" % (key, value)
    print 'context:', repr(window.context)
    window.close()

def dump_gl():
    '''Dump GL info.'''
    from pyglet.gl import gl_info
    print 'gl_info.get_version():',  gl_info.get_version()
    print 'gl_info.get_vendor():',  gl_info.get_vendor()
    print 'gl_info.get_renderer():',  gl_info.get_renderer()
    print 'gl_info.get_extensions():'
    extensions = list(gl_info.get_extensions())
    extensions.sort()
    for name in extensions:
        print '  ', name

def dump_glu():
    '''Dump GLU info.'''
    from pyglet.gl import glu_info
    print 'glu_info.get_version():',  glu_info.get_version()
    print 'glu_info.get_extensions():'
    extensions = list(glu_info.get_extensions())
    extensions.sort()
    for name in extensions:
        print '  ', name

def dump_glx():
    '''Dump GLX info.'''
    try:
        from pyglet.gl import glx_info
    except:
        print 'GLX not available.'
        return
    import pyglet
    window = pyglet.window.Window(visible=False)
    print 'context.is_direct():', window.context.is_direct()
    window.close()

    if not glx_info.have_version(1, 1):
        print 'Version: < 1.1'
    else:
        print 'glx_info.get_server_vendor():', glx_info.get_server_vendor()
        print 'glx_info.get_server_version():', glx_info.get_server_version()
        print 'glx_info.get_server_extensions():'
        for name in glx_info.get_server_extensions():
            print '  ', name
        print 'glx_info.get_client_vendor():', glx_info.get_client_vendor()
        print 'glx_info.get_client_version():', glx_info.get_client_version()
        print 'glx_info.get_client_extensions():'
        for name in glx_info.get_client_extensions():
            print '  ', name
        print 'glx_info.get_extensions():'
        for name in glx_info.get_extensions():
            print '  ', name

def dump_media():
    '''Dump pyglet.media info.'''
    import pyglet.media
    print 'driver:', pyglet.media.driver.__name__

def dump_avbin():
    '''Dump AVbin info.'''
    try:
        import pyglet.media.avbin
        print 'Library:', pyglet.media.avbin.av
        print 'AVbin version:', pyglet.media.avbin.av.avbin_get_version()
        print 'FFmpeg revision:', \
            pyglet.media.avbin.av.avbin_get_ffmpeg_revision()
    except:
        print 'AVbin not available.'

def dump_al():
    '''Dump OpenAL info.'''
    try:
        from pyglet.media.drivers import openal
        print 'Library:', openal.al._lib
        print 'Version:', openal.get_version()
        print 'Extensions:'
        for extension in openal.get_extensions():
            print '  ', extension
    except:
        print 'OpenAL not available.'

def _try_dump(heading, func):
    _heading(heading)
    try:
        func()
    except:
        import traceback
        traceback.print_exc()

def dump():
    '''Dump all information to stdout.'''
    _try_dump('Python', dump_python)
    _try_dump('pyglet', dump_pyglet)
    _try_dump('pyglet.window', dump_window)
    _try_dump('pyglet.gl.gl_info', dump_gl)
    _try_dump('pyglet.gl.glu_info', dump_glu)
    _try_dump('pyglet.gl.glx_info', dump_glx)
    _try_dump('pyglet.media', dump_media)
    _try_dump('pyglet.media.avbin', dump_avbin)
    _try_dump('pyglet.media.drivers.openal', dump_al)

if __name__ == '__main__':
    dump()
