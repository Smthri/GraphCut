import tkinter as tk
from PIL import Image, ImageTk
import numpy as np

class Application(tk.Frame):
    def __init__(self, master=None, w=600, h=600):
        super().__init__(master=master, width=w, height=h)
        self.width = w
        self.height = h
        self.master = master
        self.pack()
        self.points_recorded = []
        self.hist = np.zeros(shape=(2, 3, 256), dtype=np.uint32)
        self.inputmode = {'obj': 1, 'color': 'blue'}
        self.create_widgets()

    def mousepos(self, event):
        if event.x < 0 or event.x >= self.width or event.y < 0 or event.y >= self.height:
            self.clearpoints(event)
            return

        self.points_recorded += [event.x, event.y]

        r, g, b = self.pil_image.convert('RGB').getpixel((event.x, event.y))
        #print(f'I see pixel at ({event.x}, {event.y}) with RGB ({r}, {g}, {b})')
        self.hist[self.inputmode['obj'], 0, r] += 1
        self.hist[self.inputmode['obj'], 1, g] += 1
        self.hist[self.inputmode['obj'], 2, b] += 1

        if len(self.points_recorded) > 4:
            self.points_recorded = self.points_recorded[2:]
        if len(self.points_recorded) == 2:
            self.points_recorded += self.points_recorded

        self.canvas.create_line(self.points_recorded, fill=self.inputmode['color'])

    def clearpoints(self, event):
        self.points_recorded = []

    def cleardrawings(self):
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, image = self.render, anchor=tk.NW)

    def load_image(self, image_path):
        self.pil_image = Image.open(image_path).resize((self.width, self.height))
        self.render = ImageTk.PhotoImage(self.pil_image)

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

    def create_widgets(self):
        f = tk.Frame(self)
        f.pack(side='left')
        self.load_image('geo_dataset/Cpy-Sh33.jpg')
        self.label = tk.Label(f, image=self.render)
        #self.label.image = self.render
        self.label.pack(side='left')

        uf = tk.Frame(self)
        uf.pack(side='right')
        self.canvas = tk.Canvas(uf, width=self.width, height=self.height)
        self.canvas.create_image(0, 0, image=self.render, anchor=tk.NW)
        self.canvas.bind('<B1-Motion>', self.mousepos)
        self.canvas.bind('<ButtonRelease-1>', self.clearpoints)
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH)
       
        '''
        self.hi_there = tk.Button(self)
        self.hi_there['text'] = 'Hello World!\nClick me'
        self.hi_there['command'] = self.say_hi
        self.hi_there.pack(side = 'bottom')
        '''
        self.switch = tk.Button(self, text='Object', fg='blue', command=self.switch)
        self.switch.pack(side='top')

        self.quit = tk.Button(self, text='QUIT', fg='red', command=self.master.destroy)
        self.quit.pack(side='top')

        self.clear = tk.Button(self, text='Clear', command=self.cleardrawings)
        self.clear.pack(side='top')
'''
root = tk.Tk()
app = Application(master=root)
app.mainloop()
'''
