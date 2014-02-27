from scipy.ndimage import gaussian_filter
from stl_tools import numpy2stl
import Image
import Tkinter
from numpy import asarray
from tkFileDialog import askopenfilename
import sys

# geomapapp -> find map -> grid dialog -> black to white -> no sun -> preferences -> turn off axis -> save as .png

imageScale=1  #minimum image size divided by (ie 2 means half)
maxDimension=400 #much larger than this and the time it takes to compile is too long, the file is too big, and the model is much larger than a printer can print
border=6 #gets rid of black lat and long lines in the .png
bottom=True #true prints a bottom
minThickPct=.03
maxWidth=10000#140 #10000, #afinia website says it can print a 5.5" cube 140mm
maxDepth=10000#140 #10000, #10000mm=10m user can shrink it with their printer software
maxHeight=10000#140 #10000, #



class Application(Tkinter.Frame):

    class IORedirector(object):
        #A general class for redirecting I/O to this text widget.
        def __init__(self,outputBox):
            self.outputBox = outputBox

    class StdoutRedirector(IORedirector):
        #A class for redirecting stdout to this text widget.
        def write(self,str):
            if not str.isspace():
                self.outputBox.insert(Tkinter.END,str+' ')#,False)
                root.update()

    def prepareImage(self):
        #resize image and crop border
        img = Image.open(self.fileLocation)
        self.width,self.height=img.size
        self.imageScale=max(self.imageScale,((max(self.width, self.height))/maxDimension))
        print self.imageScale
##        if self.fileType=='png':
##            self.imageScale=1
##        elif self.fileType=='tif' or self.fileType=='iff': #DEM Tiffs seem to be really really big
##            self.imageScale=8
        imgCrop=img.crop((border,border,self.width-border,self.height-border))
        imgSmall = imgCrop.resize((self.width/self.imageScale,self.height/self.imageScale), Image.ANTIALIAS)
        #other options: ANTIALIAS, NEAREST, BILINEAR, BICUBIC
        for i in range(-1,-len(self.fileLocation),-1):
            if self.fileLocation[i]=='.':
                fileEnd=i
                break
        fileName=self.fileLocation[0:fileEnd]
        return fileName,imgSmall

    def makeHeights (self,img):
        #array of tuples (red, green, blue, alpha) alpha is opacity
        imageArray = asarray(img)
        imageArray=imageArray.astype(float)
        if self.fileType=='png':
            # take tuple of color values and turn them into one height value
            heightArray  = imageArray[:,:,0] + imageArray[:,:,1] + imageArray[:,:,2]
            heightArray = gaussian_filter(heightArray, 1)  # smoothing, bigger number= smoother
        elif self.fileType=='tif' or self.fileType=='iff': #for super users, DEM Tiffs work
            heightArray=imageArray
        return heightArray
        
    def pickFile(self):
        self.fileLocation=askopenfilename(filetypes=[("PNG","*.png")])
        self.outputBox.delete(1.0,Tkinter.END)
        self.outputBox.insert(Tkinter.END, self.fileLocation)
        self.fileType=self.fileLocation[-3:].lower()

    def main(self):
        while self.high.get()<=self.low.get() or not self.fileLocation:
            self.outputBox.delete(1.0,Tkinter.END)
            if self.high.get()<=self.low.get():
                output='High Point must be greater than Low Point.'
            else:
                output='Please choose a file.'
            self.outputBox.insert(Tkinter.END,output)
            return
        self.outputBox.delete(1.0,Tkinter.END)
        self.outputBox.insert(Tkinter.END,'Working... ')#This may take a while.')
        root.update()
        #start redirecting stdout:
        sys.stdout = self.StdoutRedirector(self.outputBox)
        fileName,imgSmall=self.prepareImage()
        heightArray=self.makeHeights(imgSmall)
        heightDiffMeters=self.high.get()-self.low.get()
        heightDiffColors=heightArray.max()-heightArray.min()
        #pixels translate to millimeters 
        sqrtAreaMM=(self.height*self.width)**.5
        #user entered area in square kilometers converted to meters
        sqrtAreaM=(self.area.get()*1000000)**.5
        #adjusts the height of the model based on the difference in heights
        scaleFactor=self.vertExag.get()*(sqrtAreaMM/sqrtAreaM)*heightDiffMeters/(heightDiffColors*self.imageScale)
            
        numpy2stl (heightArray, fileName+".stl",
                   scale=scaleFactor, #maximum height?
                   #mask_val=1, #cuts of bottom to make islands
                   max_width=maxWidth,
                   max_depth=maxDepth,
                   max_height=maxHeight,
                   min_thickness_percent=minThickPct, #helps reduce waste at bottom
                   solid=bottom) #True means it will make a bottom
        self.outputBox.delete(1.0,Tkinter.END)
        self.outputBox.insert(Tkinter.END,'Program is finished.')
        # To stop redirecting stdout:
        sys.stdout = sys.__stdout__
        

    def makeSlider(self, caption, default, width=None, **options):
        Tkinter.Label(root, text=caption, bg='#E0EEEE').grid(row=3, column=self.column, columnspan=2, sticky='w')
        slider = Tkinter.Scale(root, **options)
        slider.grid(row=4, column=self.column, columnspan=2)
        self.column+=2
        slider.set(default)
        return slider

    def areaSlider(self, caption, default, width=None, **options):
        Tkinter.Label(root, text=caption, bg='#E0EEEE').grid(row=5, column=0)
        slider = Tkinter.Scale(root, **options)
        slider.grid(row=5, column=1, columnspan=6)
        slider.set(default)
        return slider

    def makeButton(self, **options):
        button = Tkinter.Button(root, **options)
        button.grid(row=3, column=self.column, rowspan=2)
        self.column+=1
        return button                                 

    def __init__(self, master=None):
        Tkinter.Frame.__init__(self, master)
        self.fileLocation = None
        self.width=0
        self.height=0
        self.fileType='png'
        self.grid()
        self.imageScale=imageScale #image size divided by (ie 2 means half): default is 1
        self.column=0
        self.high=self.makeSlider("Highest Point (m)", 100, from_=0, to=10000, length=200, bg='#E0EEEE', resolution=10, orient=Tkinter.HORIZONTAL)
        self.low =self.makeSlider("Lowest Point (m)", 0, from_=0, to=10000, length=200, bg='#E0EEEE', resolution=10, orient=Tkinter.HORIZONTAL)
        self.area = self.areaSlider("Area (sq km)",50,from_=1, to=100000, length=600, bg='#E0EEEE', resolution=1, orient=Tkinter.HORIZONTAL) 
        self.vertExag=self.makeSlider("Vertical Exaggeration", 1, from_=.1, to=10, length=150, bg='#E0EEEE', resolution=.1, orient=Tkinter.HORIZONTAL)
        self.fileButton=self.makeButton(text="Choose File", width=15,command=self.pickFile)
        self.startButton=self.makeButton(text="Start", width=10,command=self.main)
        self.outputBox = Tkinter.Text(root, bg='#E0EEEE', height= 1, fg='black', font=("Helvetica", 10), relief=Tkinter.FLAT, yscrollcommand='TRUE')#fg='black', relief=Tkinter.SUNKEN, 
        self.outputBox.grid(row=6, column=0, columnspan=6)



root = Tkinter.Tk()
root.title("GeoMapApp to *.stl")
root.configure(background='#E0EEEE')
root.geometry('800x150+100+100')
app = Application(master=root)
app.mainloop()


#numpy2stl(heightArray, "filename.stl",
#          scale=0.05, maximum height
#          mask_val=5., not quite sure, seems to add holes
#          max_width=235., #width of your 3-D printer surface in mm
#          max_depth=140., #depth of your 3-D printer surface in mm
#          max_height=150.,#height of your 3-D printer surface in mm
#          min_thickness_percent = .005, helps reduce waste at bottom
#          solid=True) True means it will make a bottom
