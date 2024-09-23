import numpy as np        # For numerical operations
from opensimplex import OpenSimplex  # For noise generation
from pyqtgraph.Qt import QtCore  # For visualizing the data
import pyqtgraph.opengl as gl  # For handling GUI functionality
from PyQt5.QtWidgets import QApplication
import struct
import pyaudio 
import sys


class Terrain(object):  # flying terrain mesh animation
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = gl.GLViewWidget()
        self.window.setGeometry(0, 110, 1920, 1080)
        self.window.show()
        self.window.setWindowTitle('Music Visualizer')
        self.window.setCameraPosition(distance=60, elevation=20)

        grid = gl.GLGridItem()
        grid.scale(2, 2, 2)
        self.window.addItem(grid)

        self.nstep = 1.3
        self.ypoints = np.arange(-20, 20 + self.nstep, self.nstep)
        self.xpoints = np.arange(-20, 20 + self.nstep, self.nstep)
        self.nfaces = len(self.ypoints)  # The number of faces is equal to our number of vertices/y-columns
  

        self.RATE = 44100
        self.CHUNK = len(self.xpoints) * len(self.ypoints)

        self.pyaudio = pyaudio.PyAudio()
        self.stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.RATE,
            input=True,
            output=True,
            frames_per_buffer=self.CHUNK,
        )

        # Perlin Noise Object
        self.noise = OpenSimplex(seed=int(np.random.normal(1)))
        self.offset = 0
        
        # Create the vertices array to use to initiate the gl mesh item
        verts, faces, colors = self.mesh()

        self.mesh1 = gl.GLMeshItem(
            faces=faces,
            vertexes=verts,
            faceColors=colors,
            drawEdges=True,
            smooth=False,
        )
        self.mesh1.setGLOptions('additive')
        self.window.addItem(self.mesh1)

    def mesh(self, offset=0, height=3.5, wf_data=None):
        if wf_data is not None:
            wf_data = struct.unpack(str(2 * self.CHUNK) + 'B', wf_data)
            wf_data = np.array(wf_data, dtype='b')[::2] + 128
            wf_data = np.array(wf_data, dtype='int32') - 128
            wf_data = wf_data * 0.04
            wf_data = wf_data.reshape((len(self.xpoints), len(self.ypoints)))
        else:
            wf_data = np.array([1] * 1024)
            wf_data = wf_data.reshape((len(self.xpoints), len(self.ypoints)))

        faces = []
        colors = []
        verts = np.array([
            [
                x, y, wf_data[n][m] * self.noise.noise2(x=n / 5.5 + offset, y=m / 5.2 +  offset)
            ] for n, x in enumerate(self.xpoints) for m, y in enumerate(self.ypoints)
        ], dtype=np.float32)

        for m in range(self.nfaces - 1):
            yoff = m * self.nfaces
            for n in range(self.nfaces - 1):
                faces.append([n + yoff, yoff + n + self.nfaces, yoff + n + self.nfaces + 1])
                faces.append([n + yoff, yoff + n + 1, yoff + n + self.nfaces + 1])

                colors.append([n / self.nfaces, 1 - n / self.nfaces, m / self.nfaces, 0.7])
                colors.append([n / self.nfaces, 1 - n / self.nfaces, m / self.nfaces, 0.8])

        faces = np.array(faces, dtype=np.uint32)
        colors = np.array(colors, dtype=np.float32)

        return verts, faces, colors

    def update(self):
        """
        Update the mesh and shift the noise each time
        """
        try:
            if self.stream.is_active():
                wf_data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                verts, faces, colors = self.mesh(offset=self.offset, wf_data=wf_data)
                self.mesh1.setMeshData(vertexes=verts, faces=faces, faceColors=colors)
        except OSError as e:
            print(f"Error reading stream: {e}")
        
    def start(self): 
        if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
            QApplication.instance().exec_()

    def animation(self,frametime=10):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(frametime)
        self.start()


if __name__ == "__main__":
    t = Terrain()
    t.animation()
