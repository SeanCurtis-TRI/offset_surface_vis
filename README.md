A simple utility for playing with offset surfaces and convex polytopes.

Installation
============

This is a python script with the following dependencies:
     - Python 2.7
     - numpy
     - scipy (0.19)
     - PyQt4
     - PyQt4-OpenGL

Help for satisfying dependencies
--------------------------------
sudo apt-get install python-qt4 python-qt4-gl
sudo apt-get install python-pip
sudo pip install numpy scipy
sudo pip install --upgrade numpy scipy

Running
=======

In the root of the repository, simply execute:

   `python offset_surface.py`

A window will appear.

Workflow
========

Camera manipulation
-------------------

The camera uses an "orbiting" model.
  Alt + Left Mouse Button   -- Orbit the camera around its current target
  Alt + Middle Mouse Button -- Move the camera *and* its target parallel with
                               the view plane.
  Alt + Right Mouse BUtton  -- Zoom in/out.  Move the camera closer and farther
                               from the target.

Manipulating the camera causes an icon to appear reflecting the nature of the
operation. These can be disabled, via the View menu (i.e., ``View ->
Show Camera Movement Widgets``).

Offset Surface Manipulation
---------------------------

First load an OBJ file through ``File -> Open Obj`` (or Ctrl+o). If successful,
a colored polyhedron should appear with the edges highlighted in white.

As you pass the mouse over the facets of the polyedron, a yellow line should
appear in the face under the mouse (centered on the face and point outward in
the face's normal direction). This indicates the "active" face.

_Changing offset_

By default, the offset surface has a distance of 0. This can be changed by
dragging on faces.

  - Left dragging in the visible normal direction of the active face will change
    that face's offset value. Moving away from the face increases the offset.
    Moving toward the polyhedron will decrease the offset (the value will not
    fall below zero.)
  - Holding shift while dragging will cause *all* faces to be offset the same
    amount.
