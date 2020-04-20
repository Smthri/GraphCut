import numpy as np
from skimage.io import imread, imsave
import sys
from front import *
from back import *
import tkinter as tk

def process_func():
    print('works')
    pass

if __name__ == '__main__':
    if (len(sys.argv) < 4):
        print('Usage: python main.py <input_image> <output_image> <num_classes>')
        sys.exit(0)

    cutter = Cutter(sys.argv[1], sys.argv[2], as_gray=False)
    root = tk.Tk()
    app = Application(master=root, input_image = sys.argv[1], processor = cutter, num_classes=int(sys.argv[3]))
    app.mainloop()
