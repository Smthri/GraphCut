import numpy as np
from skimage.io import imread, imsave
import sys

if __name__ == '__main__':
    if (len(sys.argv) < 3):
        print('Usage: python main.py <input_image> <output_image>')
        sys.exit(0)

    #TODO
