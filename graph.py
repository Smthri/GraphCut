import numpy as np
import math

class graph:
    def __init__(self, image):
        self.image = image
        self.flow_graph = np.zeros(shape = (3), dtype = np.float32)
