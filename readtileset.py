#Tileset ripper for SNES Toy Story by Enmet
#This script reads the full tilemap from the VRAM section of a BSNES-plus save state and exports it into a PNG
#Intended to be used for SNES Toy Story but could potentially be used for other games as well if the tilemap address is adjusted accordingly

import cv2
import numpy as np
import argparse
import subprocess

parser = argparse.ArgumentParser(
                    prog='Readtileset',
                    description='Toy Story SNES Tileset Exporter - Read a BSNES-Plus or other SNES emulator save state and export the tilemap to Tiled.',
                    epilog='Usage: readtileset INPUT TILESET IMPORTMODE RNC')

parser.add_argument('statefile', 
                    metavar='S',
                    help='BSNES save state file to read from (.bst). ROM file if in mode 1')                     
parser.add_argument('tileset', 
                    metavar='T',
                    help='Saves the tileset at the user specified location')
parser.add_argument('--importmode', 
                    metavar='M',
                    help='Import mode (0-1). 0 if importing from a save state, 1 if importing directly from ROM',
                    required=False,
                    default='0')
parser.add_argument('--rnc', 
                    metavar='R',
                    help='Path to RNC compression runtimes. Required if using export mode 1',
                    required=False,
                    default=None)   

args = parser.parse_args()
print("Save state file:", args.statefile,"\nTile set:",args.tileset)

fileName = args.statefile                           #Save state to read the level data from
tilesetPath = args.tileset
file = open(fileName,"r+b")                         #Points to the RAM dump or save state we want to load from in binary write mode

stateOffset = int("21C", 16)                        #Offset from 0 off save states, when used with a BSNES RAM dump this should be just 0
tilemapOffset = stateOffset+int("2B20", 16)         #Starting tile in the tilemap
vramOffset = stateOffset+int("18000", 16)           #VRAM starting address in save state
cgramOffset = stateOffset+int("40220", 16)

exampleTileID = vramOffset+int("1A0", 16)           #Locates the specific tile inside VRAM

def swapEndian(tableCopy):                          #Converts little endian to big endian, and big endian to little endian by swapping bytes in list
    x = 0
    tablePaste = []
    for i in tableCopy:
        if x % 2 != 0:  #If x is an odd number
            tablePaste.append(tableCopy[x])
            tablePaste.append(tableCopy[x-1])
        else:
            pass
        x += 1
    return(tablePaste)

def splitPlane(planeByte):                          #This function splits the bit planes by converting the int to a binary number and put it as a list
    planeList = []
    x = 0
    bitID = 128                                     #Start with the highest byte and shift downwards
    while x < 8: 
        bitResult = planeByte & bitID               #AND the current bit with the value
        bitID = bitID >> 1                          #Shift one bit downwards per iteration
        if bitResult > 0:                           #If there is a match, it means that a 1 was found
            planeList.append(1)
        else:
            planeList.append(0)
        x += 1
    return planeList

def printValues(table):                             #Useful for debugging, outputs values read in the tilemap table
    x = 0
    y = 0
    while x < 32:
        print("Hex:",format(table[x], '02x'),"\tBinary:",format(table[x], '08b'),"\tDecimal:",table[x])
        x += 1
        y += 1
        if y == 8:
            print("\n")
            y = 0

def compositePlanes(row,tilepart):                              #Puts together 8x8 tiles, each pixel is stored in 4 bits per pixel mode
    x = 0                                                       #Effectively this means that each 8-pixel row is stored in 4 bytes
    y = 0                                                       #However, each pixel is stored in 4 different bit planes and then they are composited together
    newPlane = []                                               #Therefor, this function composites the 4 different bit planes
    while x < 8:
        newPlane.append(0)
        x += 1
    x = 0
    bitPlane = []
    planeMult = 1  
    while x < 4:
        if x > 1:
            bitPlane = splitPlane(tilepart[x+14+(row*2)])
        else:
            bitPlane = splitPlane(tilepart[x+(row*2)])
        while y < 8:
            newPlane[y] = newPlane[y] + (bitPlane[y] * planeMult)
            y += 1
        x += 1
        planeMult = planeMult << 1
        y = 0
    return newPlane

def drawTilePart(tilepart):                                     
    partTile = []                                               
    z = 0                                                       
    while z < 8:
        line = compositePlanes(z,tilepart)
        partTile.append(line)
        z += 1
    return partTile

def splitColorByte(Byte):                                       #SNES reads colors from a pallette stored in CGRAM, which in turn is BGR555
    colTest = Byte                                              #5 bits for each color (0-31), with the highest bit being unused
    colB = (colTest & 31744) >> 10                              #To sort out these colors, the bits that we want can be shifted out
    colG = (colTest & 992) >> 5
    colR = (colTest & 31)
    return colB, colG, colR

def byteToIntList(wordList):
    byteList = []
    for i in range(0,len(wordList),2): #:
        byteList.append((wordList[i+1])+(256*wordList[i]))
    return byteList

def drawFullTile(tileIndex):
    colorTable = []
    currentTile = tileIndex * 32                                #Each full tile consists of 32 bytes
    file.seek(tilemapOffset+currentTile, 0)
    fullTile = []
    fullTile = list(file.read(32))
    fullTile = swapEndian(fullTile)
    file.seek(cgramOffset, 0)
    colTable = list(file.read(8*32))                            #Read all possible pallettes from color graphics RAM
    colTable = swapEndian(colTable)
    colTableByte = byteToIntList(colTable)                      #Put the two big endian bytes together to make the math a bit easier to keep track of
    x = 0
    y = 0
    z = 0
    tileAdr = 0
    partTileRow = []
    while x < 16:
        tileAdr = fullTile[(x*2)+1]+(fullTile[x*2]*256)         #Need to read 10 bits from both of these bytes, so combine them first
        tilePal = tileAdr & 7168                                #AND with 3 bits to get pallette
        vMirror = tileAdr & 32768                               #Vertical mirroring flag
        hMirror = tileAdr & 16384                               #Horizontal mirroring flag
        tilePri = tileAdr & 8192                                #Priority flag
        tilePal = tilePal >> 10                                 #Shift bits down as we don't want the padding
        tileAdr = tileAdr & 1023                                #AND only with the first 10 bytes
        file.seek(vramOffset+(tileAdr*32), 0)                   #From tilemap, find tile segment in VRAM
        numberLE = list(file.read(32))                          #Read the full tile
        numberBE = swapEndian(numberLE)                         #Swap from little to big endian
        partTile = drawTilePart(numberBE)                       #The key function that triggers the chain of reading pixel data all the way down
        for i in partTile:
            for m in i:    
                if m == 0:                                      #Set transparent tiles to a very specific number so that the sheet can be chroma-keyed
                    B,G,R = 1,1,1                               #For SNES, color 0 is always transparent, and from the color space conversion a "real"    
                else:                                           #color can never be 1, the darkest pixel is 8, therefor, chroma key can safely be set to 1
                    B,G,R = splitColorByte(colTableByte[m+(tilePal*16)])
                    B = int((B * 255) / 31)                     #Convert from color space BGR555 to BGR888
                    G = int((G * 255) / 31)
                    R = int((R * 255) / 31)
                colorTable.append((B,G,R))                      #BGR can be converted to RGB here if needed by changing the append order
        x += 1  
    x = 0
    y = 0
    z = 0
    a = 0
    #From partTileRow: A full tile is read, but the data is in the wrong format because it's read from VRAM in 8x8 segments
    #Because of this, the result of partTileRow will be a giant column that is 8 pixels wide, 256 pixels tall, totalling 32 pieces of 8x8 tiles in one dimension
    #Most of the relevant image/picture functions require a 2D-array to define the horizontal and vertical size of the constructed tile
    #The following nested loop in the x-axis reads one 8-pixel row per 8x8 tile, for four consecutive tiles, and places the rows in order of 4, so we get 8x4=32
    #This is done 8 times (y-axis) which produces the first part of the tile which becomes 32x8
    #This is then done 4 times in total to properly read off the column of 32 segments of 8x8 tiles.
    tempRow = []
    colorTable2 = []
    while z < 4:
        while y < 8:
            while x < 4:
                while a < 8:
                    tempRow.append(colorTable[(z*256)+(y*8)+(64*x)+a])
                    a += 1
                colorTable2 = colorTable2 + tempRow
                tempRow.clear()
                x += 1
                a = 0
            y += 1
            x = 0
        z += 1
        y = 0
    return colorTable2
    
def drawTileset():   
    colTable = []
    t = 1
    x = 0
    y = 0
    z = 0
    r = 0
    tempRow = []
    tempRow2 = []
    while z < 16:
        while t < 17:
            colTable = colTable + drawFullTile(t+(16*z))
            t += 1
        while y < 32:
            while x < 16:
                while r < 32:
                    tempRow.append(colTable[r+(x*1024)+(y*32)])
                    r += 1
                x += 1
                r = 0
            y += 1
            x = 0
        z += 1
        t = 1
        y = 0
        tempRow2 = tempRow2 + tempRow
        tempRow.clear()
        colTable.clear()
    
    colTable2 = np.asarray(tempRow2,dtype='uint8')
    colTable2 = colTable2.reshape(32*z,512,3)
    cv2.imwrite(tilesetPath, colTable2)

    #cv2.imshow("image",colTable2)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()

drawTileset()

file.close()