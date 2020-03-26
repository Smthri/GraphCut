import numpy as np
import math

class graph:
    def __init__(self, image):

        '''

        Class for processing the image through GraphCut.
        Image is RGB.
        Flow graph is a dictionary in which:
            Keys are tuple coordinates of a pixel or 's' or 't'.
            Values are tuple pairs of flow / reserve.
        '''
        self.image = image
        self.flow_graph = {}
