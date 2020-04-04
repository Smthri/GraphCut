import numpy as np
from skimage.io import imread, imsave
from skimage.transform import resize
import skimage
from maxflow import *
from tqdm import tqdm


class Cutter():

    '''
    Class that performs the GraphCut.
    hist[0] - histogram of background pixels
    hist[1] - histogram of object pixels

    pixel_list[0] - locations of background pixels
    pixel_list[1] - locations of object pixels
    '''

    def __init__(self, input_image, output_image, scale_shape = None, mode='simple'):
        if not scale_shape is None:
            self.image = np.array(resize(skimage.img_as_float(imread(input_image, as_gray=True)), scale_shape))
        else:
            self.image = np.array(skimage.img_as_float(imread(input_image, as_gray=True)))
        self.output_image = output_image
        self.hist = np.zeros((2, 3, 256), dtype=np.uint32)
        self.D = np.max(self.image) - np.min(self.image)
        self.M = np.max(self.image)
        self.pixel_list = [set(), set()]

        self.w = self.simple


    def update_data(self, obj, x, y, r, g, b):
        self.pixel_list[obj].add((y, x)) #TODO: check pixel coordinates
        self.hist[obj, 0, r] += 1
        self.hist[obj, 1, g] += 1
        self.hist[obj, 2, b] += 1

    def simple(self, p, q):
        '''
        Calculates weight between pixels p and q.
        p, q - tuple(line, column) - coordinates of pixels
        '''
        return self.D - np.abs(self.image[p] - self.image[q])

    def term_simple(self, p, s=True):
        if not s:
            return self.M - np.abs(self.B - self.image[p])
        return self.M - np.abs(self.O - self.image[p])

    def clearhist(self):
        self.hist = np.zeros((2, 3, 256), dtype=np.uint32)
        self.pixel_list[0].clear()
        self.pixel_list[1].clear()

    def __call__(self):

        '''
        Method where the maxflow is computed and the image is segmented.
        '''

        if np.max(self.hist[0]) == 0 or np.max(self.hist[1]) == 0:
            print('No data offered, quitting.')
            return

        self.O = np.mean([self.image[i, j] for i, j in self.pixel_list[1]])
        self.B = np.mean([self.image[i, j] for i, j in self.pixel_list[0]])

        g = GraphFloat()
        nodeids = g.add_grid_nodes(self.image.shape)
        print('Constructing graph....')
        h, w = self.image.shape
        for i in tqdm(range(h)):
            for j in range(w):

                if i < h - 1:
                    weight = self.w((i, j), (i + 1, j))
                    g.add_edge(nodeids[i, j], nodeids[i + 1, j], weight, weight)

                if j < w - 1:
                    weight = self.w((i, j), (i, j + 1))
                    g.add_edge(nodeids[i, j], nodeids[i, j + 1], weight, weight)

                if (i, j) in self.pixel_list[1]:
                    g.add_tedge(nodeids[i, j], h*(w-1) + w*(h-1), 0)
                elif (i, j) in self.pixel_list[0]:
                    g.add_tedge(nodeids[i, j], 0, h*(w-1) + w*(h-1))
                else:
                    g.add_tedge(nodeids[i, j], self.term_simple((i, j)), self.term_simple((i, j), s=False))

        print('Graph constructed. Starting maxflow calculation....')
        flow = g.maxflow()
        print('Maxflow calculated. Performing segmentation...')

        mask = np.zeros(self.image.shape, dtype=np.float32)
        boolarray = g.get_grid_segments(nodeids)
        mask[boolarray] = 1.
        print('Mask constructed.')
        imsave(self.output_image, 1 - mask) #TODO: check with API/code why positions are inverted
        print('Done.')

