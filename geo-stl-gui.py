# By: Jim Town
# james.ross.town@gmail.com
#

#begin pyinstaller error prevention
import scipy.special._ufuncs_cxx
#end pyinstaller error prevention

#my imports
from numpy2stl import numpy2stl # my own numpy2stl edits
from loadOpenTopoData import loadAsciiDataTxt,loadAsciiData,loadXYZdata
from netcdf import loadNetCDF #netCDF loader

#dependencies
from scipy.ndimage import gaussian_filter, zoom
from PIL import Image
import tkinter as Tkinter #for compatibility
import numpy as np
from tkinter.filedialog import askopenfilename
import sys
import math
from platform import system

from tkinter.ttk import Separator
#import tkMessageBox
import struct

# geomapapp -> find map -> grid dialog -> black to white -> no sun -> preferences -> turn off axis -> save as .png
verbose=False#True #instead of printing to window print to console
BGCOLOR='#E5EDF3' #'#E0EEEE'
minImageScale=1  #minimum image size divided by (ie 2 means half)
maxDimension=300 #much larger than this and the time it takes to compile is too long, the file is too big, and the model is much larger than a printer can print
###
border=7 #gets rid of black lat and long lines in the .png default=6
maskValue=0 # heights at or below this value will be cut off in island mode
###
bottom=True #true prints a bottom
minThickHeight=1 #constant base of 1mm
maxWidth=10000#140 #10000, #afinia website says it can print a 5.5" cube 140mm
maxDepth=10000#140 #10000, #10000mm=10m user can shrink it with their printer software
maxHeight=10000#140 #10000, #
fileTypes=['png','tif','iff','asc','xyz','grd','.nc','txt']



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
                if int(self.outputBox.index('1.end')[2:])>120: #compare isn't working for some reason, so I did it myself
                    self.outputBox.delete(1.0,Tkinter.END)
                    self.outputBox.insert(Tkinter.END,str+' ')
                #self.outputBox.see(Tkinter.END)
                root.update()

    class NullDevice():
        #A class for redirecting stdout nowhere
        def write(self, s):
            pass

    def resizeArray(self, heightArray): #Bilinear Interpolation
        #faster than mine
        return zoom(heightArray,(float(1)/float(self.imageScale)),order=1)#spline of interpolation 1=bilinear, 3=bicubic
##        newArray=np.zeros((self.height/self.imageScale,self.width/self.imageScale),float)
##        rows,columns=newArray.shape
##        #print heightArray.shape
##        #print newArray.shape
##        for y in range(rows):
##            for x in range(columns):
##                subSum=0
##                for i in range(self.imageScale):
##                    for j in range(self.imageScale):
##                        subSum+=heightArray[self.imageScale*y+i][self.imageScale*x+j]
##                newArray[y][x]=subSum/float(self.imageScale**2)
##        return newArray

    def convertLatAndLong (self,lat1,lat2,long1,long2):
        rEarth = 6378.137 #in km
        lat1=lat1*math.pi/180
        lat2=lat2*math.pi/180
        dLat = lat1-lat2
        dLong = (long1-long2)*math.pi/180
        a = math.sin(dLat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dLong/2)**2
        c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = rEarth*c
        return d*1000 #meters

    def findWidthLength(self,point1,point2):
        width=self.convertLatAndLong   (point1[0],point2[0],point1[1],point1[1])#(41.2,40.34,248.35,248.35)
        length=self.convertLatAndLong  (point1[0],point1[0],point1[1],point2[1])#(41.2,41.2,248.35,246.54)
        #diagonal=convertLatAndLong(point1[0],point2[0],point1[1],point2[1])#(41.2,40.34,248.35,246.54)
        return width, length#, diagonal

    def loadAsciiDataTxt (self): #opentopo ascii file .txt, x and y are meters
        self.actualLength,self.actualWidth,heightArray=loadAsciiDataTxt(self.fileLocation,
                                                                       self.lowGot,self.override.get())
        self.height,self.width= heightArray.shape
        return heightArray
    
    def loadAsciiData (self): #opentopo ascii file depracated?
        self.actualLength,self.actualWidth,heightArray=loadAsciiData(self.fileLocation,
                                                           self.lowGot,self.override.get())
        self.height,self.width= heightArray.shape
        return heightArray
    
    def loadXYZdata (self): #ascii file, x and y are lat and long
        self.actualLength,self.actualWidth,heightArray=loadXYZdata(self.fileLocation)
        #print yDiff, currentXdiff
        self.height,self.width= heightArray.shape
        return heightArray

    def loadNetCdfData (self):
        originalStdout = sys.stdout  # keep a reference to STDOUT
        sys.stdout = self.NullDevice()  # redirect the real STDOUT
        longList, latList, dimList, heightDiffList, heightList=loadNetCDF(self.fileLocation)
        sys.stdout = originalStdout  # turn STDOUT back on
        heightArray=np.array(heightList)
        heightArray.resize(dimList[1],dimList[0])
        self.actualWidth,self.actualLength=self.findWidthLength((latList[0],longList[0]),(latList[1],longList[1]))
        self.height,self.width= heightArray.shape
        return heightArray

    def loadTifData(self,img):
        tifFile = open(self.fileLocation, "rb")
        fileStr=tifFile.read()
        tifFile.close()
        rowsPerStrip=img.getexif().tags[278][0] #tag 278 is the list of Rows per strip
        #print 'rowsPerStrip', rowsPerStrip
        #print (self.height, self.width)
        imageArray=np.zeros((self.height,self.width),float)
        y=0
        x=0
        for offset in img.getexif().tags[273]: #tag 273 is the list of strip offsets
            #print offset,x,y
            if y+1<self.height:
                for word in range(offset,self.width*4*rowsPerStrip+offset,4):
                    imageArray[y][x]=struct.unpack('>f', fileStr[word:word+4])[0]
                    if x+1<self.width:
                        x+=1
                    else:
                        x=0
                        y+=1
        return imageArray
    
    def findK (self,x): # k is how far off the scale is due to being further away from the equator (probably)
        rEarth=6378.137 #in km
        k0=.9996 #from wikipedia, default value for k0
        k=k0*math.cosh(x/(k0*rEarth))
        return k

    def prepareTifImage(self):
        originalStdout = sys.stdout  # keep a reference to STDOUT
        sys.stdout = self.NullDevice()  # redirect the real STDOUT
        Image.DEBUG=True
        img = Image.open(self.fileLocation)
        tags=img.getexif()
        sys.stdout = originalStdout  # turn STDOUT back on
        self.width,self.height=img.size
        try:
            img.getpixel((0,0))
        except ValueError: #if it is a geotiff we need to load data manually
            #print 'Load manually'
            imageArray=self.loadTifData(img)
        else:
            imageArray = np.asarray(img)
            try:
                imageArray=imageArray.astype(np.float32)
            except MemoryError:
                memoryError=True
            else:
                memoryError=False
            self.wayTooBigFactor=1
            while imageArray.ndim==0 or memoryError:
                self.wayTooBigFactor+=.1 #try to maintain the highest resolution possible
                tempImg=img.resize((int(self.width/self.wayTooBigFactor),int(self.height/self.wayTooBigFactor)),Image.BILINEAR)
                imageArray=np.asarray(tempImg)
                #print self.wayTooBigFactor,imageArray.shape, self.width/self.wayTooBigFactor
                try:
                    imageArray=imageArray.astype(np.float32)
                except MemoryError:
                    memoryError=True
                else:
                    memoryError=False
            self.width,self.height=int(self.width/self.wayTooBigFactor),int(self.height/self.wayTooBigFactor)
            if tags.get(258,0)==(8,8,8): #258 is bits per sample 32 means data, 8,8,8 means color
                imageArray=imageArray[:,:,0] + imageArray[:,:,1] + imageArray[:,:,2]
        if self.override.get():
            defaultHeight=self.lowGot
        else:
            defaultHeight=np.nanmin(imageArray)
        #print img.tag.tags[33922]
        tiePt=tags.get(33922,None)
        if tiePt is not None:
            tiePt=tiePt[4]
        else:
            tiePt=1.
        k=self.findK(tiePt/1000.0) #model tiepoint tag (x,y,z,i,j,k) where x,y is the origin of the image file and i,j is where it is on the earth, possibly, you never can tell with bees
        scales=tags.get(33550,(1,1,1))
        self.scale=tuple(scaleFactor/k for scaleFactor in scales) #scale tag tuple (xScale,yScale,0) (zScale is for 3D geotiffs)
        output=''
        print (tags)
        #print(imageArray.max(), imageArray.min(),imageArray.shape,imageArray[0,0])
        if np.isnan(imageArray).any():
            imageArray[np.isnan(imageArray)]=defaultHeight
            output='Missing data points... '
        try:
            maskValue=float(tags[42113])
        except KeyError: #key doesn't exist, checking for ridiculous points
            if self.override.get():
                imageArray[imageArray<self.lowGot]=defaultHeight
            if imageArray.max()>(defaultHeight+10000):
                imageArray[imageArray>(defaultHeight+10000)]=defaultHeight
                output='Missing data points... '
            if imageArray.min()<(defaultHeight-10000):
                imageArray[imageArray<(defaultHeight-10000)]=defaultHeight
                output='Missing data points... '
        else: #mask value exists
            if imageArray.min()==maskValue:#mask value 
                imageArray[imageArray==maskValue]=defaultHeight
                output='Missing data points... '
        self.outputBox.insert(Tkinter.END,output)
        if len(imageArray.shape)>2:
            return imageArray[:,:,0]
        else:
            return imageArray
    
    def preparePngImage(self):
        #resize image and crop border
        img = Image.open(self.fileLocation)
        self.width,self.height=img.size
        imgCrop=img.crop((border,border,self.width-border,self.height-border))
        #array of tuples (red, green, blue, alpha) alpha is opacity
        imageArray = np.asarray(imgCrop)
        #print(imageArray.shape)
        imageArray=imageArray.astype(float)
        # take tuple of color values and turn them into one height value
        if len(imageArray.shape)==3:
            return (imageArray[:,:,0] + imageArray[:,:,1] + imageArray[:,:,2])
        else:
            return (imageArray)

    def adjustHeights (self,heightArray):
        self.imageScale=max(self.imageScale,(math.ceil((max(self.width, self.height))/(self.maxDimGot*self.piecesGot))))
        if np.isnan(heightArray).any(): #get rid of all NANs
            if self.override.get():
                defaultValue=self.lowGot
            else:
                try:
                    defaultValue=heightArray.nanmin()
                except: #no good values at all
                    print('Data file is all NAN try a different file.')
            heightArray[np.isnan(heightArray)]=defaultValue
            print('Missing data points... ')
        if self.imageScale>1:
            print('Resizing array...')
            heightArray=self.resizeArray(heightArray)
        if self.gauss.get():
            print('Applying Gaussian Filter...')
            heightArray = gaussian_filter(heightArray, 1)  # smoothing, bigger number= smoother
        self.heightDiffColors=heightArray.max()-heightArray.min()
        if self.fileType!='png':
            areaM=self.actualLength*self.actualWidth #area in meters
            sqrtAreaMM=(self.height*self.width)**.5 #area of output in mm
            self.scaleFactor=self.vertExagGot*(sqrtAreaMM/(areaM**.5))/self.imageScale
            self.area.delete(0,Tkinter.END)
            self.area.insert(0, str(areaM/1000000))
            self.high.delete(0,Tkinter.END)
            self.high.insert(0, str(heightArray.max()))
            self.low.delete(0,Tkinter.END)
            self.low.insert(0, str(heightArray.min()))
        else:
            if self.reverse.get(): #it is a png file and they want the colors reversed
                print('Reversing Colors...')
                heightArray=heightArray.max()-heightArray
            heightDiffMeters=self.highGot-self.lowGot
            #pixels translate to millimeters 
            sqrtAreaMM=(self.height*self.width)**.5
            #user entered area in square kilometers converted to meters
            sqrtAreaM=(self.areaGot*1000000)**.5
            #adjusts the height of the model based on the difference in heights
            self.scaleFactor=self.vertExagGot*(sqrtAreaMM/sqrtAreaM)*heightDiffMeters/(self.heightDiffColors*self.imageScale)

        heightArray*=self.scaleFactor
        return heightArray

    def splitFiles(self,fileName,heightArray):
        #scaleFactor*=self.imageScale #since we aren't scaling, we don't need to divide the height by the scale
        width,height=heightArray.shape
        splitWidth=width/self.piecesGot
        splitHeight=height/self.piecesGot
        for xNumber in range(self.piecesGot):
            for yNumber in range(self.piecesGot):
                #print xNumber, yNumber, self.imageScale, splitHeight, splitWidth
                tempArray=heightArray[yNumber*splitHeight:(yNumber+1)*splitHeight,xNumber*splitWidth:(xNumber+1)*splitWidth]
                #tempArray[tempArray.shape[0]-1][tempArray.shape[1]-1]=heightArray.min() #dirty way of getting it to work with original stl_tools 
                numpy2stl (tempArray,
                           fileName+str(xNumber*2+yNumber)+".stl",
                           scale=self.scaleFactor, #maximum height?
                           mask_val=-1., # 1. cuts off bottom to make islands, -1. cuts off nothing
                           max_width=maxWidth,
                           max_depth=maxDepth,
                           max_height=maxHeight,
                           min_thickness=minThickHeight, #helps reduce waste at bottom #changed to a constant
                           solid=bottom,#) #True means it will make a bottom
                           Amin=heightArray.min())
                self.outputBox.delete(1.0,Tkinter.END)
                self.outputBox.insert(Tkinter.END, 'Completed file '+str(xNumber*2+yNumber+1)+' of '+str(self.piecesGot**2)+'. ')
                root.update()

    def pickFile(self):
        self.fileLocation=askopenfilename()
        self.outputBox.delete(1.0,Tkinter.END)
        self.outputBox.insert(Tkinter.END, self.fileLocation)
        self.fileType=self.fileLocation[-3:].lower()

    def main(self):
        self.outputBox.delete(1.0,Tkinter.END)
        try:
            self.areaGot=float(self.area.get())
            self.vertExagGot=float(self.vertExag.get())
            self.piecesGot=int(self.pieces.get())
            self.highGot=float(self.high.get())
            self.lowGot=float(self.low.get())
            self.maxDimGot=int(self.maxDimension.get())
        except ValueError:
            output="At least one of your inputs is not a valid number."
            self.outputBox.insert(Tkinter.END,output)
            return
        else:
            output=None
            if self.highGot<=self.lowGot and not self.override.get():
                output='High Point must be greater than Low Point.'
            elif self.areaGot<=0:#not self.fileLocation:
                output='Please enter a valid area.'# must be greater than 0 square kilometers.
            elif self.vertExagGot<=0:
                output='Please enter a valid Verical Exaggeration.'
            elif self.piecesGot<=0:
                output='Please enter a valid number of pieces.'
            elif not self.fileLocation or self.fileType not in fileTypes:
                output='Please choose a valid file '+str(fileTypes)+'.'
            if output:
                self.outputBox.insert(Tkinter.END,output)
                return
        self.outputBox.insert(Tkinter.END,'Working... This may take a while.')
        root.update()
        #start redirecting stdout:
        if not verbose: sys.stdout = self.StdoutRedirector(self.outputBox)
        for i in range(-1,-len(self.fileLocation),-1):
            if self.fileLocation[i]=='.':
                fileEnd=i
                break
        fileName=self.fileLocation[0:fileEnd]
        if self.fileType == 'png':
            heightArray=self.preparePngImage()
            heightArray=self.adjustHeights(heightArray)
            self.areaOutput=self.area.get()
            self.highOutput=self.high.get()
            self.lowOutput=self.low.get()
        elif self.fileType in ['tif','iff']:
            heightArray=self.prepareTifImage()
            self.actualLength=self.wayTooBigFactor*self.height*self.scale[0]# read from tif file
            self.actualWidth=self.wayTooBigFactor*self.width*self.scale[1]# read from tif file
            heightArray=self.adjustHeights(heightArray)
            #print (sqrtAreaMM/areaM**.5), self.imageScale, 1/self.scale[0]
        elif self.fileType=='asc':
            heightArray=self.loadAsciiData()
            heightArray=self.adjustHeights(heightArray)
        elif self.fileType=='xyz':
            heightArray=self.loadXYZdata()
            heightArray=self.adjustHeights(heightArray)
        elif self.fileType in ['grd','.nc']:
            heightArray=self.loadNetCdfData()
            heightArray=self.adjustHeights(heightArray)
            #print heightArray.max(), heightArray.min()
        elif self.fileType=='txt':
            heightArray=self.loadAsciiDataTxt()
            heightArray=self.adjustHeights(heightArray)
        root.update()
        #set minimum thickness
        totalHeight=self.scaleFactor*self.heightDiffColors
        #minThickPct=minThickHeight/totalHeight
        if self.piecesGot>1:
            print('Splitting files...')
            self.splitFiles(fileName,heightArray)
        else:
            #np.save("test.npy",heightArray)#for debugging
            numpy2stl (heightArray, fileName+".stl",
                       mask_val=maskValue, #values at or below this are treated as "ocean" to be cut
                       isIsland=self.island.get(),#cuts off bottom to make islands
                       min_thickness=minThickHeight, #helps reduce waste at bottom?
                       )
        self.outputBox.delete(1.0,Tkinter.END)
        self.outputBox.insert(Tkinter.END,'Program is finished.')
        #stop redirecting stdout:
        if not verbose: sys.stdout = sys.__stdout__

    def makeSlider(self, caption, default, width=None, **options):
        Tkinter.Label(self.frame, text=caption, bg=BGCOLOR).grid(row=self.row, column=self.column, columnspan=2, sticky='w')
        slider = Tkinter.Scale(self.frame, **options)
        slider.grid(row=self.row+1, column=self.column, columnspan=2)
        self.column+=2
        slider.set(default)
        return slider

    def intInput(self, caption, width=None, defaultValue='1',**options): #for area
        Tkinter.Label(self.frame, text=caption, bg=BGCOLOR).grid(row=self.row,
                                                                 column=self.column, sticky='w')
        entry = Tkinter.Entry(self.frame, **options)
        entry.grid(row=self.row, column=self.column+1, columnspan=1, sticky='ew')
        self.column+=2
        entry.insert(Tkinter.END,defaultValue)
        return entry

    def makeButton(self, **options):
        button = Tkinter.Button(self.frame, **options)
        button.grid(row=self.row, column=self.column)#, rowspan=2)
        self.column+=1
        return button

    def makeCheckBox(self, caption, defaultOn):
        var = Tkinter.BooleanVar()
        checkBox = Tkinter.Checkbutton(self.frame, text=caption, variable=var, 
                                       bg=BGCOLOR, onvalue=True, offvalue=False)
        if defaultOn:
            checkBox.select()
        checkBox.grid(row=self.row, column=self.column, sticky='w')
        self.column+=1
        return var
    
    def makeInfoBox(self, text):
        textBox = Tkinter.Text(self.frame, bg=BGCOLOR, height= 1, fg='black', font=("Helvetica", 10),
                               relief=Tkinter.FLAT, yscrollcommand='TRUE', width=50)#fg='black', relief=Tkinter.SUNKEN, 
        textBox.grid(row=self.row, column=self.column, columnspan=3, sticky='ew')
        self.column+=3
        offset=5#25 #for centering purposes
        textBox.insert(Tkinter.END,offset*' '+text)
        return textBox
    
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
        instructionLabel = Tkinter.Label(self.frame, image=theImage, bd=-2)
        instructionLabel.photo=theImage
        instructionLabel.grid(**options)

    def __init__(self, master=None):
        frame=Tkinter.Frame.__init__(self, master)
        if root.winfo_screenheight()<1060:
            root.bind('<Configure>', self.shrinkWindow)
            self.makeScrollBar()
        else:
            self.frame=frame
        self.fileLocation = None
        self.width=0
        self.height=0
        self.fileType='png'
        self.grid()
        self.imageScale=minImageScale #image size divided by (ie 2 means half): default is 1
        # first row
        self.column=1
        self.row=3
        self.low =self.intInput("Lowest Point (m):",bg=BGCOLOR, width=10, defaultValue='0')
        self.high=self.intInput("Highest Point (m):",bg=BGCOLOR,width=10, defaultValue='100')
        Separator(self.frame, orient=Tkinter.VERTICAL).grid(row=self.row, column=self.column, rowspan=3, sticky='ns')
        self.column+=1
        self.vertExag=self.intInput("Vertical Exaggeration:", bg=BGCOLOR, width=50)
        self.fileButton=self.makeButton(text="Choose File", width=10,command=self.pickFile)
        # second row
        self.row+=1 #next row
        self.column=1
        self.area = self.intInput("Enter Area (sq km):",bg=BGCOLOR,width=50)
        self.reverse=self.makeCheckBox("Reverse Colors", False)#reverse colors checkbox
        self.override=self.makeCheckBox("Manual Override", False)#manual override Lowest Point
        self.column+=1 #for separator
        self.pieces=self.intInput("Split the file into n by n pieces:", bg=BGCOLOR, width=50)
        self.startButton=self.makeButton(text="Start", width=10,command=self.main)
        # third row
        self.row+=1
        self.column=1
        self.PNGinfo=self.makeInfoBox('Input all values for PNG files or default lowest point for manual override.')
        self.island=self.makeCheckBox("Island Mode", False)#treat like an island

        self.column+=1#for separator
        self.maxDimension=self.intInput("Maximum dimension (mm):", bg=BGCOLOR, width=50, defaultValue=str(maxDimension))
        self.gauss=self.makeCheckBox("Gaussian Filter", True)#gauss checkbox
        # fourth row
        self.row+=1
        self.column=1
        Separator(self.frame, orient=Tkinter.HORIZONTAL).grid(row=self.row, column=self.column, columnspan=4, sticky='ew')
        # fifth row
        self.row+=1
        self.column=1
        self.outputBox = Tkinter.Text(self.frame, bg=BGCOLOR, height= 1, fg='black', font=("Helvetica", 10), relief=Tkinter.FLAT, yscrollcommand='TRUE')#fg='black', relief=Tkinter.SUNKEN, 
        self.outputBox.grid(row=self.row, column=self.column, columnspan=8, sticky='ew')
        self.row+=1
        self.column=1
        # sixth row
        self.insertImage('logo_pro',row=self.row,column=self.column,columnspan=10)
        #self.insertImage('instructions',row=7,column=1,rowspan=10,columnspan=10)


root = Tkinter.Tk()
root.title("Geo to *.stl: Professional Edition")
if system()=='Windows':
    root.wm_iconbitmap('images\geo-stl.ico')
root.configure(background=BGCOLOR)
#winHeight=min(1060,root.winfo_screenheight()-100)
root.geometry('900x330+10+10')
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
