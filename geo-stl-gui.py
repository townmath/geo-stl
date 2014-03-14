from scipy.ndimage import gaussian_filter
from stl_tools import numpy2stl
import Image
import Tkinter
from numpy import asarray
from tkFileDialog import askopenfilename
import sys

# geomapapp -> find map -> grid dialog -> black to white -> no sun -> preferences -> turn off axis -> save as .png

BGCOLOR='#E5EDF3' #'#E0EEEE'
minImageScale=1  #minimum image size divided by (ie 2 means half)
maxDimension=400 #much larger than this and the time it takes to compile is too long, the file is too big, and the model is much larger than a printer can print
border=6 #gets rid of black lat and long lines in the .png default=6
bottom=True #true prints a bottom
minThickPct=.03 #percent of total height to put at bottom
maxWidth=10000#140 #10000, #afinia website says it can print a 5.5" cube 140mm
maxDepth=10000#140 #10000, #10000mm=10m user can shrink it with their printer software
maxHeight=10000#140 #10000, #
fileTypes=['png','tif','iff']



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
        self.outputBox.delete(1.0,Tkinter.END)
        try:
            area=float(self.area.get())
        except ValueError:
            output=self.area.get()+' is not a number, try again.'
            self.outputBox.insert(Tkinter.END,output)
            return
        else:
            while self.high.get()<=self.low.get() or area<=0 or not self.fileLocation or self.fileType not in fileTypes:# or area>=100000:
                if self.high.get()<=self.low.get():
                    output='High Point must be greater than Low Point.'
                elif area<=0:#not self.fileLocation:
                    output='Please enter a valid area.'# between 0 and 100,000 square kilometers.'
                else:
                    output='Please choose a .png file.'
                self.outputBox.insert(Tkinter.END,output)
                return
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
        sqrtAreaM=(float(self.area.get())*1000000)**.5
        #adjusts the height of the model based on the difference in heights
        scaleFactor=self.vertExag.get()*(sqrtAreaMM/sqrtAreaM)*heightDiffMeters/(heightDiffColors*self.imageScale)
            
        numpy2stl (heightArray, fileName+".stl",
                   scale=scaleFactor, #maximum height?
                   #mask_val=1, #cuts off bottom to make islands
                   max_width=maxWidth,
                   max_depth=maxDepth,
                   max_height=maxHeight,
                   min_thickness_percent=minThickPct, #helps reduce waste at bottom
                   solid=bottom) #True means it will make a bottom
        self.outputBox.delete(1.0,Tkinter.END)
        self.outputBox.insert(Tkinter.END,'Program is finished.')
        #stop redirecting stdout:
        sys.stdout = sys.__stdout__

    def makeSlider(self, caption, default, width=None, **options):
        Tkinter.Label(self.frame, text=caption, bg=BGCOLOR).grid(row=3, column=self.column, columnspan=2, sticky='w')
        slider = Tkinter.Scale(self.frame, **options)
        slider.grid(row=4, column=self.column, columnspan=2)
        self.column+=2
        slider.set(default)
        return slider

    def intInput(self, caption, width=None, **options):
        Tkinter.Label(self.frame, text=caption, bg=BGCOLOR).grid(row=5, column=1, sticky='e')
        entry = Tkinter.Entry(self.frame, **options)
        entry.grid(row=5, column=2, columnspan=3, sticky='ew')
        entry.insert(Tkinter.END,'1')
        return entry

    def makeButton(self, **options):
        button = Tkinter.Button(self.frame, **options)
        button.grid(row=3, column=self.column, rowspan=2)
        self.column+=1
        return button
    
    def makeScrollBar(self):
        winHeight=min(1060,root.winfo_screenheight()-500)
        scrollbar = Tkinter.Scrollbar(self, orient="vertical")
        scrollbar.pack(side='right',fill='y', expand=False)
        self.canvas= Tkinter.Canvas(self,bd=0, #width=935, height=winHeight,
                               borderwidth=0, background=BGCOLOR,
                               highlightthickness=0,
                               yscrollcommand=scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.canvas.yview)

        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        self.frame = Tkinter.Frame(self.canvas, background=BGCOLOR)
        newWindow = self.canvas.create_window(0,0,window=self.frame,anchor='nw')

        def configureFrame(event):
            size=(self.frame.winfo_reqwidth(), self.frame.winfo_reqheight())
            self.canvas.config(scrollregion="0 0 %s %s" % size)
            if self.frame.winfo_reqwidth() != self.canvas.winfo_width():
                self.canvas.config(width=self.frame.winfo_reqwidth())
        self.frame.bind('<Configure>', configureFrame)
        
        def configureCanvas(event):
            if self.frame.winfo_reqwidth() != self.canvas.winfo_width():
                self.canvas.config(width=self.frame.winfo_width())
        self.canvas.bind('<Configure>', configureCanvas)
        self.pack()

    def shrinkWindow(self, event): #when the window shrinks the scrollbar/canvas shrinks with it
        if root.winfo_height()!=self.canvas.winfo_height():
            self.canvas.config(height=root.winfo_height())        
    
    def insertImage(self,filename,**options):
        theImage=Tkinter.PhotoImage(file="images/"+filename+".gif")
        instructionLabel = Tkinter.Label(self.frame, image=theImage)
        instructionLabel.photo=theImage
        instructionLabel.grid(**options)

    def __init__(self, master=None):
        frame=Tkinter.Frame.__init__(self, master)
        root.bind('<Configure>', self.shrinkWindow)
        self.makeScrollBar()
        self.fileLocation = None
        self.width=0
        self.height=0
        self.fileType='png'
        self.grid()
        self.imageScale=minImageScale #image size divided by (ie 2 means half): default is 1
        self.column=1
        self.insertImage('logo',row=0,column=0,rowspan=10)
        self.high=self.makeSlider("Highest Point (m)", 100, from_=0, to=10000, length=200, bg=BGCOLOR, resolution=10, orient=Tkinter.HORIZONTAL)
        self.low =self.makeSlider("Lowest Point (m)", 0, from_=0, to=10000, length=200, bg=BGCOLOR, resolution=10, orient=Tkinter.HORIZONTAL)
        self.area = self.intInput("Enter Area (sq km):",bg=BGCOLOR,width=50)
#        self.area = self.areaSlider("Area (sq km)",50,from_=1, to=100000, length=600, bg=BGCOLOR, resolution=1, orient=Tkinter.HORIZONTAL) 
        self.vertExag=self.makeSlider("Vertical Exaggeration", 1, from_=.1, to=10, length=150, bg=BGCOLOR, resolution=.1, orient=Tkinter.HORIZONTAL)
        self.fileButton=self.makeButton(text="Choose File", width=15,command=self.pickFile)
        self.startButton=self.makeButton(text="Start", width=10,command=self.main)
        self.outputBox = Tkinter.Text(self.frame, bg=BGCOLOR, height= 1, fg='black', font=("Helvetica", 10), relief=Tkinter.FLAT, yscrollcommand='TRUE')#fg='black', relief=Tkinter.SUNKEN, 
        self.outputBox.grid(row=6, column=1, columnspan=8, sticky='ew')
        self.insertImage('instructions',row=7,column=1,rowspan=10,columnspan=10)


root = Tkinter.Tk()
root.title("GeoMapApp to *.stl")
root.configure(background=BGCOLOR)
winHeight=min(1060,root.winfo_screenheight()-100)
root.geometry('950x'+str(winHeight)+'+10+10')
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
