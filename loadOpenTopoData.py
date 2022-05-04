# By: Jim Town
# james.ross.town@gmail.com
#

import numpy as np
import math

def convertLatAndLong (lat1,lat2,long1,long2):
    rEarth = 6378.137 #in km
    lat1=lat1*math.pi/180
    lat2=lat2*math.pi/180
    dLat = lat1-lat2
    dLong = (long1-long2)*math.pi/180
    a = math.sin(dLat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dLong/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = rEarth*c
    return d*1000 #meters

def makeHeights(xs,ys,zs):
    uniqueXs=np.unique(xs)
    uniqueYs=np.unique(ys)
    #print(len(uniqueXs),uniqueXs[-1]-uniqueXs[0])
    #print(len(uniqueYs),uniqueYs[-1]-uniqueYs[0])
    width=uniqueXs[-1]-uniqueXs[0]+1
    height=uniqueYs[-1]-uniqueYs[0]+1
    actualLength=height#x and y are in meters
    actualWidth=width
    baseX=uniqueXs[-1]#[0]
    baseY=uniqueYs[-1]#[0]
    heightArray=np.zeros((height,width),dtype=float)
    for k,z in enumerate(zs):
        j=baseX-xs[k]#-baseX
        i=baseY-ys[k]#-baseY
        heightArray[i,j]=z
    #for i in range(1,self.height-1):#fillin zeros? gauss works better
    #    for j in range(1,self.width-1):
    #        if heightArray[i,j]==0 and min(heightArray[i+1,j],heightArray[i,j+1],heightArray[i-1,j],heightArray[i,j-1])>0:
    #            heightArray[i,j]=(heightArray[i+1,j]+heightArray[i,j+1]+heightArray[i-1,j]+heightArray[i,j-1])/4
    #print(self.width, self.height)
    return actualLength,actualWidth,heightArray
    
def loadXYZdataTab (fileLocation): #geomapapp ascii file
    dataFile = open(fileLocation,'r')
    lineCnt=0
    rowList=[]
    heightList=[]
    while True:
        nextLine = dataFile.readline()
        nextLine=nextLine.replace(',',' ')
        if not nextLine:
            break
        else:
            tabCnt=0
            nextNumber=''
        for char in nextLine:
            if char.isspace():
                if tabCnt==0: #tabCnt=0 is the x value
                    if lineCnt==0:
                        beginningX=float(nextNumber)
                    elif beginningX!=float(nextNumber):
                        xDiff=beginningX-float(nextNumber)
                elif tabCnt==1: #tabCnt=1 is the y value
                    if lineCnt==0:
                        beginningY=currentY=float(nextNumber)
                    elif currentY != float(nextNumber):
                        currentY = float(nextNumber)
                        heightList.append(rowList[:])
                        currentXdiff=xDiff
                        rowList[:]=[]
                elif tabCnt==2: #z is the last number
                    rowList.append(float(nextNumber))  
                tabCnt+=1
                nextNumber=''
            else:
                nextNumber+=char
        lineCnt+=1
    #print nextNumber
    #print rowList
    #rowList.append(float(nextNumber))
    heightList.append(rowList[:])
    yDiff=currentY-beginningY
    #print yDiff, currentXdiff
    actualLength=convertLatAndLong(currentY,beginningY,beginningX,beginningX)
    actualWidth=convertLatAndLong(beginningY,beginningY,beginningX,beginningX+currentXdiff)
    heightArray=np.array(heightList)
    dataFile.close()
    return actualLength,actualWidth,heightArray

def loadXYZdataComma (fileLocation,lastGoodValue=0,override=False): #ascii file .xyz
    #test files from https://pubs.usgs.gov/of/2004/1221/dataxyz.html
    dataFile = open(fileLocation,'r')
    #print("test")
    lineCnt=0
    xs=[]
    ys=[]
    zs=[]
    last=""
    separator=','
    while True:
        nextLine = dataFile.readline()
        if not nextLine:
            break
        if lineCnt==0:
            if separator not in nextLine:#if it isn't a comma, it is a tab
                separator='\t'
            first=nextLine.strip().split(separator)
        else:
            values=nextLine.strip().split(separator)
            last=values
            xVal=abs(float(values[0]))*10000
            yVal=abs(float(values[1]))*10000
            xs.append(int(xVal))
            ys.append(int(yVal))
            try:
                height=float(values[2])
                zs.append(height)
                if not override: #if manual override then all missing data points should be  self.lowGot
                    lastGoodValue=height
            except:
                zs.append(lastGoodValue)
                print('Missing data points... ')
        lineCnt+=1

    beginningX,beginningY=float(first[0]),float(first[1])
    endingX,endingY=float(last[0]),float(last[1])
    actualLength=convertLatAndLong(endingY,beginningY,beginningX,beginningX)
    actualWidth=convertLatAndLong(beginningY,beginningY,beginningX,endingX)

    #print(actualLength,actualWidth)
    dataFile.close()
    _,_,heightArray=makeHeights(xs,ys,zs)
    return actualLength,actualWidth,heightArray

def loadXYZdata(fileLocation):
    dataFile = open(fileLocation,'r')
    nextLine = dataFile.readline()
    dataFile.close()
    #if ',' in nextLine:
    return loadXYZdataComma(fileLocation)
    #else:
    #    return loadXYZdataTab(fileLocation)
    
def loadAsciiData (fileLocation,lastGoodValue,override): #opentopo ascii file...depracated?
    dataFile = open(fileLocation,'r')
    lineCnt=0
    nextNumber=''
    output=''
    while True:
        nextLine = dataFile.readline()
        if not nextLine:
            break
        else:
            spaceCnt=0
        if lineCnt==0:
            width=int(nextLine[5:])
        elif lineCnt==1:
            height=int(nextLine[5:])
            heightArray=np.zeros((height,width),float)
            print(str(height*width/1000000))
        elif lineCnt==2:
            xCorner=float(nextLine[9:])
        elif lineCnt==3:
            yCorner=float(nextLine[9:])
        elif lineCnt==4: #maybe means each pixel is cellSize meters?
            cellSize=float(nextLine[8:])
        elif lineCnt==5: # filter out these values and replace with lastGoodValue
            noData=nextLine[13:]
        else:
            for char in nextLine:
                if char==' ':
                    if spaceCnt!=0:
                        if nextNumber[:5]==noData[:5]:
                            heightArray[lineCnt-6][spaceCnt-1]=lastGoodValue
                            print('Missing data points... ')
                        else:
                            heightArray[lineCnt-6][spaceCnt-1]=float(nextNumber)
                            if not override: #if manual override then all missing data points should be  self.lowGot
                                lastGoodValue=float(nextNumber)
                    spaceCnt+=1
                    nextNumber=''
                else:
                    nextNumber+=char
            if nextNumber[:5]==noData[:5]:
                heightArray[lineCnt-6][spaceCnt-1]=lastGoodValue
            else:
                heightArray[lineCnt-6][spaceCnt-1]=float(nextNumber)
                #print nextNumber
        lineCnt+=1
    #print self.width, self.height
    actualWidth=self.width*cellSize
    actualLength=self.height*cellSize
    dataFile.close()
    return actualLength,actualWidth,heightArray

def loadAsciiDataTxt (fileLocation,lastGoodValue,override): #opentopo ascii file .txt
    dataFile = open(fileLocation,'r')
    #print("test")
    lineCnt=0
    xs=[]
    ys=[]
    zs=[]
    while True:
        nextLine = dataFile.readline()
        if not nextLine:
            break
        else:
            spaceCnt=0
        if lineCnt==0:
            categories=nextLine
            #print(categories)
        else:
            values=nextLine.strip().split(',')
            xs.append(int(math.floor(float(values[0]))))
            xs.append(int(math.ceil(float(values[0]))))
            ys.append(int(math.floor(float(values[1]))))
            ys.append(int(math.ceil(float(values[1]))))
            try:
                height=float(values[2])
                zs.append(height)
                zs.append(height)#
                if not override: #if manual override then all missing data points should be  self.lowGot
                    lastGoodValue=height
            except:
                zs.append(lastGoodValue)
                print('Missing data points... ')
        lineCnt+=1
    
    dataFile.close()
    return makeHeights(xs,ys,zs)

if __name__=="__main__":
    loadXYZdata("delreymos.xyz")
