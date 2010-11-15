# Copyright 2004-2008 Nanorex, Inc.  See LICENSE file for details. 
"""
setup_draw.py - The function to allocate and compile our standard display lists
into the current GL context, and initialize the globals that hold their opengl
names.

@version: $Id: setup_draw.py 13207 2008-06-19 18:07:40Z russfish $
@copyright: 2004-2008 Nanorex, Inc.  See LICENSE file for details. 

History:

Originated by Josh as drawer.py .

Various developers extended it since then.

Brad G. added ColorSorter features.

At some point Bruce partly cleaned up the use of display lists.

071030 bruce split some functions and globals into draw_grid_lines.py
and removed some obsolete functions.

080210 russ Split the single display-list into two second-level lists (with and
without color) and a set of per-color sublists so selection and hover-highlight
can over-ride Chunk base colors.  ColorSortedDisplayList is now a class in the
parent's displist attr to keep track of all that stuff.

080311 piotr Added a "drawpolycone_multicolor" function for drawing polycone
tubes with per-vertex colors (necessary for DNA display style)

080313 russ Added triangle-strip icosa-sphere constructor, "getSphereTriStrips".

080420 piotr Solved highlighting and selection problems for multi-colored
objects (e.g. rainbow colored DNA structures).

080519 russ pulled the globals into a drawing_globals module and broke drawer.py
into 10 smaller chunks: glprefs.py setup_draw.py shape_vertices.py
ColorSorter.py CS_workers.py CS_ShapeList.py CS_draw_primitives.py drawers.py
gl_lighting.py gl_buffers.py
"""

# the imports from math vs. Numeric are as discovered in existing code
# as of 2007/06/25.  It's not clear why acos is coming from math...
from Numeric import sin, cos, pi

from OpenGL.GL import GL_ARRAY_BUFFER_ARB
from OpenGL.GL import glBegin
from OpenGL.GL import GL_COMPILE
from OpenGL.GL import glDisable
from OpenGL.GL import GL_ELEMENT_ARRAY_BUFFER_ARB
from OpenGL.GL import glEnable
from OpenGL.GL import glEnd
from OpenGL.GL import glEndList
from OpenGL.GL import GL_EXTENSIONS
from OpenGL.GL import glGenLists
from OpenGL.GL import glGetString
from OpenGL.GL import GL_LINE_LOOP
from OpenGL.GL import GL_LINES
from OpenGL.GL import GL_LINE_SMOOTH
from OpenGL.GL import GL_LINE_STRIP
from OpenGL.GL import glNewList
from OpenGL.GL import glNormal3fv
from OpenGL.GL import GL_POLYGON
from OpenGL.GL import GL_QUADS
from OpenGL.GL import GL_QUAD_STRIP
from OpenGL.GL import GL_STATIC_DRAW
from OpenGL.GL import GL_TRIANGLES
from OpenGL.GL import GL_TRIANGLE_STRIP
from OpenGL.GL import GL_UNSIGNED_BYTE
from OpenGL.GL import GL_UNSIGNED_SHORT
from OpenGL.GL import glVertex
from OpenGL.GL import glVertex3f
from OpenGL.GL import glVertex3fv

from geometry.VQT import norm, vlen, V, Q, A

from utilities.debug_prefs import Choice

import graphics.drawing.drawing_globals as drawing_globals
from graphics.drawing.gl_buffers import GLBufferObject
from graphics.drawing.shape_vertices import getSphereTriStrips
from graphics.drawing.shape_vertices import getSphereTriangles
from graphics.drawing.shape_vertices import indexVerts

import numpy

numSphereSizes = 3

def setup_drawer():
    """
    Set up the usual constant display lists in the current OpenGL context.

    WARNING: THIS IS ONLY CORRECT IF ONLY ONE GL CONTEXT CONTAINS DISPLAY LISTS
    -- or more precisely, only the GL context this has last been called in (or
    one which shares its display lists) will work properly with the routines in
    drawer.py, since the allocated display list names are stored in globals set
    by this function, but in general those names might differ if this was called
    in different GL contexts.
    """
    #bruce 060613 added docstring, cleaned up display list name allocation
    # bruce 071030 renamed from setup to setup_drawer

    spherelistbase = glGenLists(numSphereSizes)
    sphereList = []
    for i in range(numSphereSizes):
        sphereList += [spherelistbase+i]
        glNewList(sphereList[i], GL_COMPILE)
        glBegin(GL_TRIANGLE_STRIP) # GL_LINE_LOOP to see edges.
        stripVerts = getSphereTriStrips(i)
        for vertNorm in stripVerts:
            glNormal3fv(vertNorm)
            glVertex3fv(vertNorm)
            continue
        glEnd()
        glEndList()
        continue
    drawing_globals.sphereList = sphereList

    # Sphere triangle-strip vertices for each level of detail.
    # (Cache and re-use the work of making them.)
    # Can use in converter-wrappered calls like glVertexPointerfv,
    # but the python arrays are re-copied to C each time.
    sphereArrays = []
    for i in range(numSphereSizes):
        sphereArrays += [getSphereTriStrips(i)]
        continue
    drawing_globals.sphereArrays = sphereArrays

    # Sphere glDrawArrays triangle-strip vertices for C calls.
    # (Cache and re-use the work of converting a C version.)
    # Used in thinly-wrappered calls like glVertexPointer.
    sphereCArrays = []
    for i in range(numSphereSizes):
        CArray = numpy.array(sphereArrays[i], dtype=numpy.float32)
        sphereCArrays += [CArray]
        continue
    drawing_globals.sphereCArrays = sphereCArrays

    # Sphere indexed vertices.
    # (Cache and re-use the work of making the indexes.)
    # Can use in converter-wrappered calls like glDrawElementsui,
    # but the python arrays are re-copied to C each time.
    sphereElements = []             # Pairs of lists (index, verts) .
    for i in range(numSphereSizes):
        sphereElements += [indexVerts(sphereArrays[i], .0001)]
        continue
    drawing_globals.sphereElements = sphereElements

    # Sphere glDrawElements index and vertex arrays for C calls.
    sphereCIndexTypes = []          # numpy index unsigned types.
    sphereGLIndexTypes = []         # GL index types for drawElements.
    sphereCElements = []            # Pairs of numpy arrays (Cindex, Cverts) .
    for i in range(numSphereSizes):
        (index, verts) = sphereElements[i]
        if len(index) < 256:
            Ctype = numpy.uint8
            GLtype = GL_UNSIGNED_BYTE
        else:
            Ctype = numpy.uint16
            GLtype = GL_UNSIGNED_SHORT
            pass
        sphereCIndexTypes += [Ctype]
        sphereGLIndexTypes += [GLtype]
        sphereCIndex = numpy.array(index, dtype=Ctype)
        sphereCVerts = numpy.array(verts, dtype=numpy.float32)
        sphereCElements += [(sphereCIndex, sphereCVerts)]
        continue
    drawing_globals.sphereCIndexTypes = sphereCIndexTypes
    drawing_globals.sphereGLIndexTypes = sphereGLIndexTypes
    drawing_globals.sphereCElements = sphereCElements

    if glGetString(GL_EXTENSIONS).find("GL_ARB_vertex_buffer_object") >= 0:

        # A GLBufferObject version for glDrawArrays.
        sphereArrayVBOs = []
        for i in range(numSphereSizes):
            vbo = GLBufferObject(GL_ARRAY_BUFFER_ARB,
                                 sphereCArrays[i], GL_STATIC_DRAW)
            sphereArrayVBOs += [vbo]
            continue
        drawing_globals.sphereArrayVBOs = sphereArrayVBOs

        # A GLBufferObject version for glDrawElements indexed verts.
        sphereElementVBOs = []              # Pairs of (IBO, VBO)
        for i in range(numSphereSizes):
            ibo = GLBufferObject(GL_ELEMENT_ARRAY_BUFFER_ARB,
                                 sphereCElements[i][0], GL_STATIC_DRAW)
            vbo = GLBufferObject(GL_ARRAY_BUFFER_ARB,
                                 sphereCElements[i][1], GL_STATIC_DRAW)
            sphereElementVBOs += [(ibo, vbo)]
            continue
        drawing_globals.sphereElementVBOs = sphereElementVBOs

        ibo.unbind()
        vbo.unbind()
        pass

    #bruce 060415
    drawing_globals.wiresphere1list = wiresphere1list = glGenLists(1)
    glNewList(wiresphere1list, GL_COMPILE)
    didlines = {} # don't draw each triangle edge more than once

    def shoulddoline(v1,v2):
        # make sure not list (unhashable) or Numeric array (bug in __eq__)
        v1 = tuple(v1)
        v2 = tuple(v2)
        if (v1,v2) not in didlines:
            didlines[(v1,v2)] = didlines[(v2,v1)] = None
            return True
        return False
    def doline(v1,v2):
        if shoulddoline(v1,v2):
            glVertex3fv(v1)
            glVertex3fv(v2)
        return
    glBegin(GL_LINES)
    ocdec = getSphereTriangles(1)
    for tri in ocdec:
        #e Could probably optim this more, e.g. using a vertex array or VBO or
        #  maybe GL_LINE_STRIP.
        doline(tri[0], tri[1])
        doline(tri[1], tri[2])
        doline(tri[2], tri[0])
    glEnd()
    glEndList()

    drawing_globals.CylList = CylList = glGenLists(1)
    glNewList(CylList, GL_COMPILE)
    glBegin(GL_TRIANGLE_STRIP)
    for (vtop, ntop, vbot, nbot) in drawing_globals.cylinderEdges:
        glNormal3fv(nbot)
        glVertex3fv(vbot)
        glNormal3fv(ntop)
        glVertex3fv(vtop)
    glEnd()
    glEndList()

    drawing_globals.CapList = CapList = glGenLists(1)
    glNewList(CapList, GL_COMPILE)
    glNormal3fv(drawing_globals.cap0n)
    glBegin(GL_POLYGON)
    for p in drawing_globals.drum0:
        glVertex3fv(p)
    glEnd()
    glNormal3fv(drawing_globals.cap1n)
    glBegin(GL_POLYGON)
    #bruce 060609 fix "ragged edge" bug in this endcap: drum1 -> drum2
    for p in drawing_globals.drum2:
        glVertex3fv(p)
    glEnd()
    glEndList()

    drawing_globals.diamondGridList = diamondGridList = glGenLists(1)
    glNewList(diamondGridList, GL_COMPILE)
    glBegin(GL_LINES)
    for p in drawing_globals.digrid:
        glVertex(p[0])
        glVertex(p[1])
    glEnd()
    glEndList()

    drawing_globals.lonsGridList = lonsGridList = glGenLists(1)
    glNewList(lonsGridList, GL_COMPILE)
    glBegin(GL_LINES)
    for p in drawing_globals.lonsEdges:
        glVertex(p[0])
        glVertex(p[1])
    glEnd()
    glEndList()

    drawing_globals.CubeList = CubeList = glGenLists(1)
    glNewList(CubeList, GL_COMPILE)
    glBegin(GL_QUAD_STRIP)
    # note: CubeList has only 4 faces of the cube; only suitable for use in
    # wireframes; see also solidCubeList [bruce 051215 comment reporting
    # grantham 20051213 observation]
    glVertex((-1,-1,-1))
    glVertex(( 1,-1,-1))
    glVertex((-1, 1,-1))
    glVertex(( 1, 1,-1))
    glVertex((-1, 1, 1))
    glVertex(( 1, 1, 1))
    glVertex((-1,-1, 1))
    glVertex(( 1,-1, 1))
    glVertex((-1,-1,-1))
    glVertex(( 1,-1,-1))
    glEnd()
    glEndList()

    drawing_globals.solidCubeList = solidCubeList = glGenLists(1)
    glNewList(solidCubeList, GL_COMPILE)
    glBegin(GL_QUADS)
    for i in xrange(len(drawing_globals.cubeIndices)):
        avenormals = V(0,0,0) #bruce 060302 fixed normals for flat shading 
        for j in xrange(4) :    
            nTuple = tuple(
                drawing_globals.cubeNormals[drawing_globals.cubeIndices[i][j]])
            avenormals += A(nTuple)
        avenormals = norm(avenormals)
        for j in xrange(4) :    
            vTuple = tuple(
                drawing_globals.cubeVertices[drawing_globals.cubeIndices[i][j]])
            #bruce 060302 made size compatible with glut.glutSolidCube(1.0)
            vTuple = A(vTuple) * 0.5
            glNormal3fv(avenormals)
            glVertex3fv(vTuple)
    glEnd()
    glEndList()                

    drawing_globals.rotSignList = rotSignList = glGenLists(1)
    glNewList(rotSignList, GL_COMPILE)
    glBegin(GL_LINE_STRIP)
    for ii in xrange(len(drawing_globals.rotS0n)):
        glVertex3fv(tuple(drawing_globals.rotS0n[ii]))
    glEnd()
    glBegin(GL_LINE_STRIP)
    for ii in xrange(len(drawing_globals.rotS1n)):
        glVertex3fv(tuple(drawing_globals.rotS1n[ii]))
    glEnd()
    glBegin(GL_TRIANGLES)
    for v in drawing_globals.arrow0Vertices + drawing_globals.arrow1Vertices:
        glVertex3f(v[0], v[1], v[2])
    glEnd()
    glEndList()

    drawing_globals.linearArrowList = linearArrowList = glGenLists(1)
    glNewList(linearArrowList, GL_COMPILE)
    glBegin(GL_TRIANGLES)
    for v in drawing_globals.linearArrowVertices:
        glVertex3f(v[0], v[1], v[2])
    glEnd()
    glEndList()

    drawing_globals.linearLineList = linearLineList = glGenLists(1)
    glNewList(linearLineList, GL_COMPILE)
    glEnable(GL_LINE_SMOOTH)
    glBegin(GL_LINES)
    glVertex3f(0.0, 0.0, -drawing_globals.halfHeight)
    glVertex3f(0.0, 0.0, drawing_globals.halfHeight)
    glEnd()
    glDisable(GL_LINE_SMOOTH)
    glEndList()

    drawing_globals.circleList = circleList = glGenLists(1)
    glNewList(circleList, GL_COMPILE)
    glBegin(GL_LINE_LOOP)
    for ii in range(60):
        x = cos(ii*2.0*pi/60)
        y = sin(ii*2.0*pi/60)
        glVertex3f(x, y, 0.0)
    glEnd()    
    glEndList()

    # piotr 080405
    drawing_globals.filledCircleList = filledCircleList = glGenLists(1)
    glNewList(filledCircleList, GL_COMPILE)
    glBegin(GL_POLYGON)
    for ii in range(60):
        x = cos(ii*2.0*pi/60)
        y = sin(ii*2.0*pi/60)
        glVertex3f(x, y, 0.0)
    glEnd()    
    glEndList()

    drawing_globals.lineCubeList = lineCubeList = glGenLists(1)
    glNewList(lineCubeList, GL_COMPILE)
    glBegin(GL_LINES)
    cvIndices = [0,1, 2,3, 4,5, 6,7, 0,3, 1,2, 5,6, 4,7, 0,4, 1,5, 2,6, 3,7]
    for i in cvIndices:
        glVertex3fv(tuple(drawing_globals.cubeVertices[i]))
    glEnd()    
    glEndList()

    # Debug Preferences
    from utilities.debug_prefs import debug_pref, Choice_boolean_True
    from utilities.debug_prefs import Choice_boolean_False
    choices = [Choice_boolean_False, Choice_boolean_True]

    # 20060314 grantham
    initial_choice = choices[drawing_globals.allow_color_sorting_default]
    drawing_globals.allow_color_sorting_pref = debug_pref(
        "Use Color Sorting?", initial_choice,
        prefs_key = drawing_globals.allow_color_sorting_prefs_key)
        #bruce 060323 removed non_debug = True for A7 release, changed default
        #value to False (far above), and changed its prefs_key so developers
        #start with the new default value.
    #russ 080225: Added.
    initial_choice = choices[drawing_globals.use_color_sorted_dls_default]
    drawing_globals.use_color_sorted_dls_pref = debug_pref(
        "Use Color-sorted Display Lists?", initial_choice,
        prefs_key = drawing_globals.use_color_sorted_dls_prefs_key)
    #russ 080225: Added.
    initial_choice = choices[drawing_globals.use_color_sorted_vbos_default]
    drawing_globals.use_color_sorted_vbos_pref = debug_pref(
        "Use Color-sorted Vertex Buffer Objects?", initial_choice,
        prefs_key = drawing_globals.use_color_sorted_vbos_prefs_key)

    #russ 080403: Added drawing variant selection
    variants = [
        "0. OpenGL 1.0 - glBegin/glEnd tri-strips vertex-by-vertex.",
        "1. OpenGL 1.1 - glDrawArrays from CPU RAM.",
        "2. OpenGL 1.1 - glDrawElements indexed arrays from CPU RAM.",
        "3. OpenGL 1.5 - glDrawArrays from graphics RAM VBO.",
        "4. OpenGL 1.5 - glDrawElements, verts in VBO, index in CPU.",
        "5. OpenGL 1.5 - VBO/IBO buffered glDrawElements."]
    drawing_globals.use_drawing_variant = debug_pref(
        "GLPane: drawing method",
        Choice(names = variants, values = range(len(variants)),
               defaultValue = drawing_globals.use_drawing_variant_default),
        prefs_key = drawing_globals.use_drawing_variant_prefs_key)

    # temporarily always print this, while default setting might be in flux,
    # and to avoid confusion if the two necessary prefs are set differently
    # [bruce 080305]
    if (drawing_globals.allow_color_sorting_pref and
        drawing_globals.use_color_sorted_dls_pref):
        print "\nnote: this session WILL use color sorted display lists"
    else:
        print "\nnote: this session will NOT use color sorted display lists"
    if (drawing_globals.allow_color_sorting_pref and
        drawing_globals.use_color_sorted_vbos_pref):
        print "note: this session WILL use", \
              "color sorted Vertex Buffer Objects\n"
    else:
        print "note: this session will NOT use", \
              "color sorted Vertex Buffer Objects\n"

    # 20060313 grantham Added use_c_renderer debug pref, can
    # take out when C renderer used by default.
    if drawing_globals.quux_module_import_succeeded:
        initial_choice = choices[drawing_globals.use_c_renderer_default]
        drawing_globals.use_c_renderer = (
            debug_pref("Use native C renderer?",
                       initial_choice,
                       prefs_key = drawing_globals.use_c_renderer_prefs_key))
            #bruce 060323 removed non_debug = True for A7 release, and changed
            # its prefs_key so developers start over with the default value.

    #initTexture('C:\\Huaicai\\atom\\temp\\newSample.png', 128,128)
    return # from setup_drawer
