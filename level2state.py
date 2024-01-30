#This script reads data from a Tiled map file and exports the level and object data to a SNES Toy Story save state
#Command line example: level2state.py %mapfile "C:/Program Files/BSNES-Plus-v05/states/TS2-1.bst" %mappath

import re               #We need regex to help us search through the csv format of Tiled's map structure
import os               #Used for some file read/write features
import sys              #Used for some file read/write features
import argparse         #Used to parse arguments so that this script can be used with Tiled's command feature

#Argument parser function
parser = argparse.ArgumentParser(
                    prog='Level2State',
                    description='Toy Story SNES Level Importer - Read a Tiled map and export it into a BSNES save state.',
                    epilog='Usage: level2state INPUT OUTPUT MAPPATH')
                    

parser.add_argument('levelfile')                     #Tiled supports parsing the filename that it is currently editing into this script, %mapfile
parser.add_argument('statefile')                     #The path to the save state has to be provided in full inside the command string
parser.add_argument('levelpath')                     #This is sent directly from a Tiled variable called %mappath

args = parser.parse_args()
print("Save state file:", args.statefile,"\nLevel file:",args.levelfile,args.levelpath)

fileName = args.statefile                           #Save state to read the level data from
levelFile = args.levelfile                          #Tiled level file, the data read from the save state will be exported here
tiledPath = args.levelpath                          #Path to the map file, as parsed from Tiled

file = open(fileName,"r+b")                         #Open the RAM export or save state from BSNES-plus, defined in fileName
ramSize = int("FFFFFF", 16)                         #Size of SNES RAM
stateSize = 289885                                  #Exact size of a BSNES save state, a fail safe just in case an invalid file was chosen

stateOffset = int("21C", 16)                        #Offset from 0 off save states, BSNES savestates has some data before the actual RAM so zero offset is at 21C
objectOffset = stateOffset+int("A00", 16)           #Starting location in RAM where objects are stored
levelOffset = stateOffset+int("4B20", 16)           #Starting location in RAM where level tiles are stored

tempArray = [None] * 2304                           #Temporary array fit to full object size just to avoid running into index-out-of-range problems

if os.path.getsize(fileName) != stateSize:
    print("ERROR: Save state has the wrong file size. Has the correct file been chosen?")
    sys.exit()

#This function converts 16-bit signed and unsigned integers into 16-bit signed integers stored in little endian (least significant byte first) 
def intToByte(x):
    y = 0                               #Y will be used as the high byte, and it will be calculated from the integer passed into the function
    z = x
    if z < 0:                           
        z = 65536 + z                   #This converts the unsigned integer into a signed integer
    if x > 65535:                       #Sanity check: We're only dealing with 16-bit integers
        print("ERROR: Value is not a 16-bit value")
        return
    elif (x < 256) and (x >= 0):        #If x is up to 255, it will fit in a single byte (low byte), but it also has to be a positive number
        #print("Integer to byte conversion: Value returned with a high byte of 0",x)
        y = 0
    else:
        while z > 255:                  #This essentially divides the number in a safe way and puts the remainder as low byte
            z -= 256
            y += 1
        #print("Integer to byte conversion: LOW byte:",z,"HIGH byte:",y)
    if y > 255:                         #Debug: this probably is not an issue anymore
        y = 255
        print("WARNING! 1 byte has exceeded 255 in value and is therefor not valid. Something is wrong with the math.")
    return z, y                         #Returns low and high byte

#Level data segment, first loop finds the line start and line end point, then the file is read again to load the actual data
with open(levelFile, "r",encoding="utf-8") as f:
    lines = f.readlines()
    for index, line in enumerate(lines):
        if "<data encoding=" in line:                   #Find the start of the level data segment
            mStart = index + 1
            #print("".join(lines[max(0, index+1):index + 5])) 
        if "</data>" in line:                           #Find the end of the level data segment
            mEnd = index 
with open(levelFile, "r",encoding="utf-8") as f:
    lines = str(f.readlines()[mStart:mEnd])             #Read lines between start and end of level data segment as string
    lines = lines.split(",")                            #Splits the string into a list so that every number is its own entry

starAmt = 0
blankAmt = 0
firstTile = 0
lastTile = 0
firstMatch = False
tileIndex = 0
newList = []
for ind in lines:                                       #There's still junk such as newline characters and spaces inside the list that has to be removed
    und = re.sub('[^0-9]', '', ind)                     #Using regex to clear everything but numbers
    if und == "":                                       #There may still be empty entries, so we ignore those
        pass
    else:
        newList.append(int(und))                        #Add the valid numbers into our new list
for ind in newList:    
    if (ind == 254) or (ind == 255):                    #Stars can either be id 254 or id 255 depending on their orientation
        starAmt += 1                                    #Calculates how many stars are located inside the map
    elif (ind == 0):
        blankAmt += 1                                   #Calculates how many blank tiles there are
    if (ind == 0) and (firstMatch == False):
        pass                                            #Do nothing if only zeroes have been found so far
    elif (ind > 0) and (firstMatch == False):           #Looks for the first tile that isn't empty space and considers it the beginning
        firstMatch = True                               #After this point we don't need to look for the first matched value anymore
        firstTile = tileIndex
    elif (ind > 0) and (firstMatch == True):            #Keep updating the last tile variable as long as the tile ID is larger than 0
        lastTile = tileIndex                            #This way, we found out where exactly the last tile is and can use that to calculate effective level size 
    tileIndex += 1                                      #This is just here to keep track of where we are in the loop
tileIndex = 0
#Diagnostics, useful data about the level
print("Stars found:",starAmt,"- Blank tiles:",blankAmt,"- Non-empty tiles:",(len(newList)-blankAmt),"- Consecutive level size:",(lastTile-firstTile),"- Of which are blanks:",(lastTile-firstTile)-(len(newList)-blankAmt))
print("First tile number:",firstTile,"- Located at:",hex(int("0x4B20",16) + firstTile),"- Value:",newList[firstTile])
print("Last tile number:",lastTile,"- Located at:",hex(int("0x4B20",16) + lastTile),"- Value:",newList[lastTile])

#This is where the level file is being read
readLevel = open(levelFile, 'r',encoding="utf-8").readlines()
x = 0
y = 0
creatureIndex = 0
for line in readLevel:                                          #This function is here because we need to find the highest ID used in the map file
    if str("<data encoding") in line:
        pass
    if str("<objectgroup") in line:
        testus2 = re.findall('name="Creature ([^"]*)"',line)    #Only bother to set the creature index if the object in question is a creature
        if testus2:
            creatureIndex = int(float(testus2[0]))              #Multiple casting has to be done to get around the document format
        else:
            pass
    if str("<object id=") in line:                              #Clues are stored in the name inside Tile
        if (re.findall("01 - Position",line)):
            testus = re.findall('x="([^"]*)"',line)
            xPos = int(float(testus[0]))
            testus = re.findall('y="([^"]*)"',line)
            yPos = int(float(testus[0]))
            lowByte,highByte = intToByte(xPos)
            tempArray[0+((creatureIndex)*48)] = lowByte
            tempArray[1+((creatureIndex)*48)] = highByte
            lowByte,highByte = intToByte(yPos)
            tempArray[2+((creatureIndex)*48)] = lowByte
            tempArray[3+((creatureIndex)*48)] = highByte
        elif (re.findall("02 - Patrolling zone",line)):
            testus = re.findall('x="([^"]*)"',line)
            xPatrol = int(float(testus[0]))
            testus = re.findall('y="([^"]*)"',line)
            yPatrol = int(float(testus[0]))
            testus = re.findall('width="([^"]*)"',line)
            if testus:                                          #If width or height is 0, Tiled will remove the line from the map file. So if regex doesn't find the line, we know it's 0
                wPatrol = xPatrol + int(float(testus[0]))
            else:
                wPatrol = 0
            testus = re.findall('height="([^"]*)"',line)
            if testus:
                hPatrol = yPatrol + int(float(testus[0]))
            else:
                hPatrol = 0
            lowByte,highByte = intToByte(xPatrol)
            tempArray[4+((creatureIndex)*48)] = lowByte
            tempArray[5+((creatureIndex)*48)] = highByte
            lowByte,highByte = intToByte(yPatrol)
            tempArray[6+((creatureIndex)*48)] = lowByte
            tempArray[7+((creatureIndex)*48)] = highByte
            lowByte,highByte = intToByte(wPatrol)
            tempArray[24+((creatureIndex)*48)] = lowByte
            tempArray[25+((creatureIndex)*48)] = highByte
            lowByte,highByte = intToByte(hPatrol)
            tempArray[26+((creatureIndex)*48)] = lowByte
            tempArray[27+((creatureIndex)*48)] = highByte
        elif (re.findall("03 - Render zone",line)):
            testus = re.findall('x="([^"]*)"',line)
            xRender = int(float(testus[0]))
            testus = re.findall('y="([^"]*)"',line)
            yRender = int(float(testus[0]))
            testus = re.findall('width="([^"]*)"',line)
            if testus:
                wRender = int(float(testus[0]))
            else:
                wRender = 0
            testus = re.findall('height="([^"]*)"',line)
            if testus:
                hRender = int(float(testus[0]))
            else:
                hRender = 0
            lowByte,highByte = intToByte(xRender)
            tempArray[8+((creatureIndex)*48)] = lowByte
            tempArray[9+((creatureIndex)*48)] = highByte
            lowByte,highByte = intToByte(yRender)
            tempArray[10+((creatureIndex)*48)] = lowByte
            tempArray[11+((creatureIndex)*48)] = highByte
            lowByte,highByte = intToByte(xRender + wRender)
            tempArray[12+((creatureIndex)*48)] = lowByte
            tempArray[13+((creatureIndex)*48)] = highByte

            lowByte,highByte = intToByte(yRender + hRender)
            tempArray[14+((creatureIndex)*48)] = lowByte
            tempArray[15+((creatureIndex)*48)] = highByte
        elif (re.findall("04 - Hitbox size",line)):
            testus = re.findall('x="([^"]*)"',line)
            xHitbox = int(float(testus[0]))
            testus = re.findall('y="([^"]*)"',line)
            yHitbox = int(float(testus[0]))
            testus = re.findall('width="([^"]*)"',line)
            if testus:
                wHitbox = int(float(testus[0]))
            else:
                wHitbox = 0
            testus = re.findall('height="([^"]*)"',line)
            if testus:
                hHitbox = int(float(testus[0]))
            else:
                hHitbox = 0
            resetOffsetX = xPos - xHitbox                       #The game doesn't read the hitbox variables the same way as Tiled, so here they're converted
            resetOffsetY = yPos + (yHitbox*-1)                  #Game reads it as offset from X-pos, while Tiled needs the hitbox to have it's own separate position
            resetOffsetY = resetOffsetY * -1
            lowByte,highByte = intToByte(resetOffsetX)
            tempArray[32+((creatureIndex)*48)] = lowByte
            tempArray[33+((creatureIndex)*48)] = highByte
            lowByte,highByte = intToByte(resetOffsetY)
            tempArray[34+((creatureIndex)*48)] = lowByte
            tempArray[35+((creatureIndex)*48)] = highByte
            lowByte,highByte = intToByte(wHitbox)
            tempArray[36+((creatureIndex)*48)] = lowByte
            tempArray[37+((creatureIndex)*48)] = highByte
            lowByte,highByte = intToByte(hHitbox)
            tempArray[38+((creatureIndex)*48)] = lowByte
            tempArray[39+((creatureIndex)*48)] = highByte
        y += 2
    if str("<property name=") in line:
        testus3 = re.findall('name="([^"]*).',line)
        findIndex = re.search(r'(-?[\d]+)',testus3[0])
        findIndex = int(float(findIndex[0])) - 1                #This simply extracts that index number to figure out exactly where to put it back in RAM
        
        testus2 = re.findall('value="([^"]*)"',line)
        if testus2:
            tempArray[findIndex+((creatureIndex)*48)] = int(float(testus2[0]))
        else:
            pass                                                #If no valid value was found, just ignore it. This is a sanity check and may not be required 
    y += 1
x += 1
i = 0
creatureDouble = []
forceRead = True
while i < len(tempArray):
    if (tempArray[i] == None) and (forceRead == False):         #We definitely don't want to load the final byte array with "None"
        break                                                   #Break out of the loop on the first instance of "None", at this point we know there are no more creatures to load
    elif (tempArray[i] == None) and (forceRead == True):        #Force reading here means that the next creature instance was empty, but it will still continue with the loop
        creatureDouble.append(0)
    else:
        creatureDouble.append(int(tempArray[i]))
    i += 1
print("Creature amount:",creatureIndex,"\nWriting into file:",fileName,"\nFrom map file:",levelFile)
arrayCreatures=bytearray(creatureDouble)
arrayLevel=bytearray(newList)

file.seek(objectOffset, 0)                                      #Seek to offset where the objects are located before data is written to
file.write(arrayCreatures)
file.seek(levelOffset, 0)                                       #Seek to offset where the level tiles are located before data is written to
file.write(arrayLevel)
file.close()