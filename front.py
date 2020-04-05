import tkinter as tk
import tkinter.ttk as ttk
from PIL import Image, ImageTk
import numpy as np

class Application(tk.Frame):
    def __init__(self, input_image, processor, master=None):
        self.load_image(input_image, resize=False)
        w, h = self.pil_image.size[:2]
        super(Application, self).__init__(master=master, width=w, height=h)
        
        self.width = min(800, w)
        self.height = min(800, h)
        self.image_path = input_image
        self.master = master
        self.pack()
        self.points_recorded = []
        self.inputmode = {'obj': 1, 'color': 'blue'}
        self.processor = processor
        self.mode = 'simple'
        self.create_widgets()

        
    # Update processor data and draw lines
    def mousepos(self, event):
        if event.x < 0 or event.x >= self.width or event.y < 0 or event.y >= self.height:
            self.clearpoints(event)
            return

        l = self.hbar.get()[0]
        u = self.vbar.get()[0]
        
        x = int(np.around(event.x + l*self.pil_image.size[0]))
        y = int(np.around(event.y + u*self.pil_image.size[1]))
        self.points_recorded += [x, y]

        r, g, b = self.pil_image.convert('RGB').getpixel((x, y))
        self.processor.update_data(self.inputmode['obj'], event.x, event.y, r, g, b)

        if len(self.points_recorded) > 4:
            self.points_recorded = self.points_recorded[2:]
        if len(self.points_recorded) == 2:
            self.points_recorded += self.points_recorded

        self.canvas.create_line(self.points_recorded, fill=self.inputmode['color'])

        
    # Clear recorded points from buffer
    def clearpoints(self, event):
        self.points_recorded = []

        
    # Clear processor data and scribbles
    def cleardrawings(self):
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, image = self.render, anchor=tk.NW)
        self.processor.clearhist()

        
    # Load image data
    def load_image(self, image_path, resize=True):
        if resize:
            self.pil_image = Image.open(image_path).resize((self.width, self.height))
        else:
            self.pil_image = Image.open(image_path)
        self.render = ImageTk.PhotoImage(self.pil_image)

        
    # Switch between object and background selection
    def switch(self):
        self.inputmode['obj'] = 1 - self.inputmode['obj']

        if self.inputmode['obj'] == 1:
            self.inputmode['color'] = 'blue'
            self.switch['text'] = 'Object'
            self.switch['fg'] = 'blue'
        else:
            self.inputmode['color'] = 'red'
            self.switch['text'] = 'Background'
            self.switch['fg'] = 'red'

            
    # Switch chosen segmentation options
    def change_mode(self):
        if self.modebutton['text'] == 'Simple':
            self.modebutton['text'] = 'Expon'
            self.mode='probabilistic'
        else:
            self.modebutton['text'] = 'Simple'
            self.mode='simple'
            
            
    # Perform segmentation and ouput result
    def segment(self):
        x = int(np.around(self.hbar.get()[0] * self.pil_image.size[0]))
        y = int(np.around(self.vbar.get()[0] * self.pil_image.size[1]))
        
        self.processor((x, y, self.width, self.height), self.mode, (self.progressbar, self))
        
        pil_image = Image.open(self.processor.output_image).resize((self.width, self.height))
        rendered = ImageTk.PhotoImage(pil_image)
        self.label.configure(image=rendered)
        self.label.image=rendered
           
            
    # Set up the layout
    def create_widgets(self):
        '''
        Result frame initialization with resize
        '''
        f = tk.Frame(self)
        f.pack(side='left')
        pil_image = Image.open(self.image_path).resize((self.width, self.height))
        render = ImageTk.PhotoImage(pil_image)
        self.label = tk.Label(f, image=render)
        self.label.image=render
        self.label.pack(side='left')

        '''
        Canvas initialization
        '''
        uf = tk.Frame(self)
        uf.pack(side='right')
        self.canvas = tk.Canvas(uf, width=self.width, height=self.height, scrollregion=(0, 0, self.pil_image.size[0], self.pil_image.size[1]))
        self.hbar = tk.Scrollbar(uf, orient=tk.HORIZONTAL)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.hbar.config(command=self.canvas.xview)
        self.vbar = tk.Scrollbar(uf, orient=tk.VERTICAL)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.vbar.config(command=self.canvas.yview)
        self.canvas.create_image(0, 0, image=self.render, anchor=tk.NW)
        self.canvas.bind('<B1-Motion>', self.mousepos)
        self.canvas.bind('<ButtonRelease-1>', self.clearpoints)
        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.canvas.pack(side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)   
    
        '''
        Button initialization
        '''
        self.switch = tk.Button(self, text='Object', fg='blue', command=self.switch)
        self.switch.pack(side='top')

        self.quit = tk.Button(self, text='QUIT', fg='red', command=self.master.destroy)
        self.quit.pack(side='top')

        self.clear = tk.Button(self, text='Clear', command=self.cleardrawings)
        self.clear.pack(side='top')
        
        self.modebutton = tk.Button(self, text='Simple', command=self.change_mode)
        self.modebutton.pack(side='top')

        self.process_button = tk.Button(self, text='Segment', command=self.segment)
        self.process_button.pack(side='top')
        
        '''
        Progressbar initialization
        '''
        self.progressbar = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progressbar.pack(side='top')
