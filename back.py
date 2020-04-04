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

    def __init__(self, input_image, output_image, scale_shape=None, as_gray=True, mode='simple'):
        if not scale_shape is None:
            self.image = np.array(resize(skimage.img_as_float(imread(input_image, as_gray=as_gray)), scale_shape))
        else:
            self.image = np.array(skimage.img_as_float(imread(input_image, as_gray=as_gray)))
        self.output_image = output_image
        self.hist = np.zeros((2, 3, 256), dtype=np.uint32)
        self.D = np.max(self.image) - np.min(self.image)
        self.M = np.max(self.image)
        self.pixel_list = [set(), set()]

        self.w = self.simple
        self.tw = self.term_simple


    def update_data(self, obj, x, y, r, g, b):
        self.pixel_list[obj].add((y, x)) #TODO: check pixel coordinates
        self.hist[obj, 0, r] += 1
        self.hist[obj, 1, g] += 1
        self.hist[obj, 2, b] += 1

    def simple(self, p, q, image):
        '''
        Calculates weight between pixels p and q.
        p, q - tuple(line, column) - coordinates of pixels
        '''
        return self.D - np.max(np.abs(image[p] - image[q]))

    def term_simple(self, p, image, s=True):
        if not s:
            return self.M - np.max(np.abs(self.B - image[p]))
        return self.M - np.max(np.abs(self.O - image[p]))

    def clearhist(self):
        self.hist *= 0
        self.pixel_list[0].clear()
        self.pixel_list[1].clear()

    def __call__(self, bbox):

        '''
        Method where the maxflow is computed and the image is segmented.
        
        bbox - tuple(x, y, w, h) - region of the image to segment
        '''

        if np.max(self.hist[0]) == 0 or np.max(self.hist[1]) == 0:
            print('No data offered, quitting.')
            return
        x, y, w, h = bbox
        image = self.image[y:y+h, x:x+w]
        
        self.O = np.mean([image[i, j] for i, j in self.pixel_list[1]])
        self.B = np.mean([image[i, j] for i, j in self.pixel_list[0]])
        self.M = np.max(image)
        self.D = self.M - np.min(image)

        g = GraphFloat()
        nodeids = g.add_grid_nodes((h, w))
        print('Constructing graph....')
        
        for i in tqdm(range(h)):
            for j in range(w):

                if i < h - 1:
                    weight = self.w((i, j), (i + 1, j), image)
                    g.add_edge(nodeids[i, j], nodeids[i + 1, j], weight, weight)

                if j < w - 1:
                    weight = self.w((i, j), (i, j + 1), image)
                    g.add_edge(nodeids[i, j], nodeids[i, j + 1], weight, weight)

                if (i, j) in self.pixel_list[1]:
                    g.add_tedge(nodeids[i, j], float('inf'), 0)
                elif (i, j) in self.pixel_list[0]:
                    g.add_tedge(nodeids[i, j], 0, float('inf'))
                else:
                    g.add_tedge(nodeids[i, j], self.tw((i, j), image), self.tw((i, j), image, s=False))

        print('Graph constructed. Starting maxflow calculation....')
        flow = g.maxflow()
        print('Maxflow calculated. Performing segmentation...')

        mask = np.zeros(image.shape, dtype=np.float32)
        boolarray = g.get_grid_segments(nodeids)
        mask[boolarray] = 1.
        print('Mask constructed.')
        imsave(self.output_image, 1 - mask) #TODO: check with API/code why positions are inverted
        print('Done.')

