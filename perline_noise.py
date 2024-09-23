"""
This creates a 3D mesh with perlin noise to simulate
a terrain. The mesh is animated by shifting the noise
to give a "fly-over" effect.

If you don't have pyOpenGL or opensimplex, then:

    - conda install -c anaconda pyopengl
    - pip install opensimplex
"""

import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import sys
from PyQt5.QtWidgets import QApplication
from opensimplex import OpenSimplex
import math


class Terrain(object):
    def __init__(self):
        """
        Initialize the graphics window and mesh
        """

        # setup the view window
        self.app = QApplication(sys.argv)
        self.w = gl.GLViewWidget()
        self.w.setGeometry(0, 110, 1920, 1080)
        self.w.show()
        self.w.setWindowTitle('Terrain')
        self.w.setCameraPosition(distance=30, elevation=8)

        # constants and arrays
        self.nsteps = 1
        self.ypoints = range(-20, 22, self.nsteps) 
        self.xpoints = range(-20, 22, self.nsteps)
        self.xrotate = 0
        self.yrotate = 0
        self.nfaces = len(self.ypoints)
        self.offset = 0
        self.theta = 0
        self.theta_x = 0 # 30 degrees
        self.theta_y = 0  # 45 degrees
        self.theta_z = 0

        # perlin noise object
        seed_value = 42
        self.tmp = OpenSimplex(seed=seed_value)

        # create the veritices array
        verts = np.array([
            [
                x, y, 1.5 * self.tmp.noise2(x=n / 5, y=m / 5)
            ] for n, x in enumerate(self.xpoints) for m, y in enumerate(self.ypoints)
        ], dtype=np.float32)

        rotated_verts = self.rotate_vertices(verts,self.theta_x,self.theta_y,self.theta_z)

        # create the faces and colors arrays
        faces = []
        colors = []
        for m in range(self.nfaces - 1):
            yoff = m * self.nfaces
            for n in range(self.nfaces - 1):
                faces.append([n + yoff, yoff + n + self.nfaces, yoff + n + self.nfaces + 1])
                faces.append([n + yoff, yoff + n + 1, yoff + n + self.nfaces + 1])
                colors.append([0, 0, 0, 0])
                colors.append([0, 0, 0, 0])

        faces = np.array(faces)
        colors = np.array(colors)

        # create the mesh item
        self.m1 = gl.GLMeshItem(
            vertexes=rotated_verts,
            faces=faces, faceColors=colors,
            smooth=False, drawEdges=True,
        )
        self.m1.setGLOptions('additive')
        self.w.addItem(self.m1)

    # Assuming 'theta' is the angle of rotation and 'axis' is the axis of rotation

    def rotation_matrix_3d(self, theta_x, theta_y, theta_z):
        """Create a combined 3D rotation matrix for rotation around X, Y, and Z axes."""
        
        # Rotation matrix around the X-axis
        R_x = np.array([
            [1, 0, 0],
            [0, np.cos(theta_x), -np.sin(theta_x)],
            [0, np.sin(theta_x), np.cos(theta_x)]
        ])
        
        # Rotation matrix around the Y-axis
        R_y = np.array([
            [np.cos(theta_y), 0, np.sin(theta_y)],
            [0, 1, 0],
            [-np.sin(theta_y), 0, np.cos(theta_y)]
        ])
        
        # Rotation matrix around the Z-axis
        R_z = np.array([
            [np.cos(theta_z), -np.sin(theta_z), 0],
            [np.sin(theta_z), np.cos(theta_z), 0],
            [0, 0, 1]
        ])
        
        # Combine the rotations: R_total = R_z * R_y * R_x
        R_total = np.dot(np.dot(R_z, R_y), R_x)
        
        return R_total

    def rotate_vertices(self, vertices, theta_x, theta_y, theta_z):
        """Apply the 3D rotation to a set of vertices."""
        rotation_matrix = self.rotation_matrix_3d(theta_x, theta_y, theta_z)
        rotated_vertices = np.dot(vertices, rotation_matrix.T)
        return rotated_vertices

    def update(self):
        """
        Update the mesh and shift the noise each time
        """
        self.theta_x -= np.pi / 60  # 30 degrees
        self.theta_y += np.pi / 40  # 45 degrees
        self.theta_z -= np.pi / 30 
        
        verts = np.array([
            [
                x, y, 2.5 * self.tmp.noise2(x=n / 5 + self.offset, y=m / 5 + self.offset)
            ] for n, x in enumerate(self.xpoints) for m, y in enumerate(self.ypoints)
        ], dtype=np.float32)

        rotated_verts = self.rotate_vertices(verts,self.theta_x,self.theta_y,self.theta_z)

        faces = []
        colors = []
        for m in range(self.nfaces - 1):
            yoff = m * self.nfaces
            for n in range(self.nfaces - 1):
                faces.append([n + yoff, yoff + n + self.nfaces, yoff + n + self.nfaces + 1])
                faces.append([n + yoff, yoff + n + 1, yoff + n + self.nfaces + 1])
                colors.append([n / self.nfaces, 1 - n / self.nfaces, m / self.nfaces, 0.7])
                colors.append([n / self.nfaces, 1 - n / self.nfaces, m / self.nfaces, 0.8])

        faces = np.array(faces, dtype=np.uint32)
        colors = np.array(colors, dtype=np.float32)

        self.m1.setMeshData(
            vertexes=rotated_verts, faces=faces, faceColors=colors
        )
        
        # Debugging prints

        self.offset -= 0.18
    def start(self):
        """
        get the graphics window open and setup
        """
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
           QApplication.instance().exec_()

    def animation(self):
        """
        calls the update method to run in a loop
        """
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(10)
        self.start()
        self.update()


if __name__ == '__main__':
    t = Terrain()
    t.animation()