import numpy as np
from numpy.linalg import norm
from skimage.io import imread, imsave
from skimage.transform import resize
from skimage.color import rgb2gray
import skimage
from maxflow import *
from tqdm import tqdm
import math
from skimage.feature.texture import *
from scipy.signal import convolve2d as cnv


class Cutter():

    '''
    Class that performs the GraphCut.
    hist[0] - histogram of background pixels
    hist[1] - histogram of object pixels

    pixel_list[0] - locations of background pixels
    pixel_list[1] - locations of object pixels
    '''

    def __init__(self, input_image, output_image, scale_shape=None, as_gray=True):
        if not scale_shape is None:
            self.image = np.array(resize(skimage.img_as_float(imread(input_image, as_gray=as_gray)), scale_shape))
        else:
            self.image = np.array(skimage.img_as_float(imread(input_image, as_gray=as_gray)))
            
        if self.image.ndim == 2:
            self.image = np.dstack((self.image, self.image, self.image))
            
        self.output_image = output_image
        self.hist = np.zeros((2, 3, 256), dtype=np.float64)
        self.D = np.max(self.image) - np.min(self.image)
        self.M = np.max(self.image)
        self.pixel_list = [set(), set()]
        self.mask = np.zeros(self.image.shape[:2], dtype=np.uint8)
        self.last_bbox = None

    def clear_mask(self):
        if self.last_bbox:
            x, y, w, h = self.last_bbox
            self.mask[y:y+h, x:x+w] = 0
        
    # Update processor data
    def update_data(self, obj, x, y, r, g, b):
        self.pixel_list[obj].add((y, x)) #TODO: check pixel coordinates
        self.hist[obj, 0, r] += 1
        self.hist[obj, 1, g] += 1
        self.hist[obj, 2, b] += 1

        
    # List of segmentation functions
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

    def probabilistic(self, p, q, image):
        sigma = 1.
        return math.exp(-(np.max(np.abs(image[p] - image[q])))**2 / (2*sigma**2))
                
    def term_probabilistic(self, p, image, s=True):
        if s:
            hist = self.hist[0]
        else:
            hist = self.hist[1]
            
        pr = 0.
        for d, i in enumerate(image[p]):
            pr += hist[d, int(i*255)]
        
        if pr == 0.:
            return float('inf')
        return max(-math.log(pr), 0.)
    
    
    # Clear processor data
    def clearhist(self):
        self.hist *= 0
        self.pixel_list[0].clear()
        self.pixel_list[1].clear()
        
    def texture(self, image):
        kernel = np.full((3, 3), 1/9)
        asmn = np.stack([cnv(image[:,:,i]**2, kernel, mode='same', boundary='symm') for i in range(3)], axis=2)
        mean = np.stack([cnv(image[:,:,i], kernel, mode='same', boundary='symm') for i in range(3)], axis=2)
        sd = np.stack([np.sqrt(cnv((image[:,:,i]-mean[:,:,i])**2, kernel**2, mode='same', boundary='symm')) for i in range(3)], axis=2)
        var = sd/(mean+0.001)
        skew = np.stack([cnv((image[:,:,i]-mean[:,:,i])**3, kernel, mode='same', boundary='symm') for i in range(3)], axis=2) / (sd+0.001)**3
        kurt = np.stack([cnv((image[:,:,i]-mean[:,:,i])**4, kernel, mode='same', boundary='symm') for i in range(3)], axis=2) / (sd+0.001)**4
        #ent = -np.stack([cnv(image[:,:,i]*np.log2(image[:,:,i]), kernel*9, mode='same', boundary='symm') for i in range(3)], axis=2)
        
        texture_vector = np.stack((asmn, mean, sd, var, skew, kurt), axis=2)
        """texture_vector -= np.min(texture_vector)
        m = np.max(texture_vector)
        print(m)
        if m > 0:
            texture_vector /= m"""
            
        return texture_vector
    
    
    # Perform segmentation
    def __call__(self, bbox, classnum=255, mode='simple', progress=None, use_textures=True):

        '''
        Method where the maxflow is computed and the image is segmented.
        
        bbox - tuple(x, y, w, h) - region of the image to segment
        mode - string - determines what functions to use for weights
        progress - tuple(ttk.Progressbar, root) - views to send progress information to
        '''

        # Check if we have necessary inputs
        if np.max(self.hist[0]) == 0 or np.max(self.hist[1]) == 0:
            print('No data offered, quitting.')
            return
        
        self.last_bbox = bbox
        x, y, w, h = bbox
        image = self.image[y:y+h, x:x+w]
        
        if use_textures:
            texture_vector = self.texture(image)
        else:
            texture_vector = np.zeros((h, w))
        
        # For passed mode set functions and data
        if mode == 'simple':
            self.w = self.simple
            self.tw = self.term_simple
            
            self.O = np.mean([image[i, j] for i, j in self.pixel_list[1]])
            self.B = np.mean([image[i, j] for i, j in self.pixel_list[0]])
        elif mode == 'probabilistic':
            self.w = self.probabilistic
            self.tw = self.term_probabilistic
            
            for d in [0, 1, 2]:
                self.hist[1, d] /= np.sum(self.hist[1, d])
                self.hist[0, d] /= np.sum(self.hist[0, d])

        g = GraphFloat()
        nodeids = g.add_grid_nodes((h, w))
        print('Constructing graph....')
        
        for i in tqdm(range(h)):
            
            if progress:
                progress[0]['value'] = int(i/h*100)
                progress[1].update_idletasks()
                
            for j in range(w):
                
                if i < h - 1:
                    weight = self.w((i, j), (i + 1, j), image) - np.clip(norm(texture_vector[i, j] - texture_vector[i+1, j]), 0, 1)
                    #print(weight)
                    g.add_edge(nodeids[i, j], nodeids[i + 1, j], weight, weight)

                if j < w - 1:
                    weight = self.w((i, j), (i, j + 1), image) - np.clip(norm(texture_vector[i, j] - texture_vector[i, j+1]), 0, 1)
                    #print(weight)
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

        mask = np.full((h, w), classnum, dtype=np.uint8)
        boolarray = g.get_grid_segments(nodeids)
        mask[boolarray] = 0
        
        print('Mask constructed.')
        self.mask[y:y+h, x:x+w] = np.clip(self.mask[y:y+h, x:x+w] + mask, 0, 255)
        imsave(self.output_image, self.mask[y:y+h, x:x+w]) # maxflow returns 1 if pixel is a background pixel
        print('Done.')

