#This script extracts data from a SNES Toy Story save state (SNES RAM) and exports it into the .tmx file supported by Tiled
#Command line example: state2level.py "C:/Program Files/BSNES-Plus-v05/states/TS2-1.bst" %mapfile %mappath

import re               #We need regex to help us search through the csv format of Tiled's map structure
import os               #Used for some file read/write features
import sys              #Used for some file read/write features
import argparse         #Used to parse arguments so that this script can be used with Tiled's command feature

#Argument parser function
parser = argparse.ArgumentParser(
                    prog='State2Level',
                    description='Toy Story SNES Level Exporter - Read a BSNES-Plus or other SNES emulator save state and export the level data to Tiled.',
                    epilog='Usage: state2level INPUT OUTPUT MAPPATH TILESET')

parser.add_argument('statefile')                     #The path to the save state has to be provided in full inside the command string
parser.add_argument('levelfile')                     #Tiled supports parsing the filename that it is currently editing into this script, %mapfile
parser.add_argument('levelpath')                     #This is sent directly from a Tiled variable called %mappath
parser.add_argument('--tileset',required=False)      #Optional: Tileset used for the level file. Not technically required, but the user definitely will want one

args = parser.parse_args()
print("Save state file:", args.statefile,"\nLevel file:",args.levelfile,args.tileset)

fileName = args.statefile                           #Save state to read the level data from
levelFile = args.levelfile                          #Tiled level file, the data read from the save state will be exported here
tiledPath = args.levelpath                          #Path to the map file, as parsed from Tiled

file = open(fileName,"r+b")                         #Points to the RAM dump or save state we want to load from in binary write mode
stateSize = 289885                                  #Exact size of a BSNES save state, a fail safe just in case an invalid file was chosen

#Offsets will be defined here. They are all defined as stateOffset+value because then this script can be adjusted for different emulator save state formats
#RAM dump will have offset 0x0, while a BSNES-plus save state has an offset of 0x21C to get to the same address
stateOffset = int("21C", 16)                        #Offset from 0 off save states, when used with a BSNES RAM dump this should be just 0
objectOffset = stateOffset+int("A00", 16)           #By using stateOffset as reference, we can define the values as they show up in RAM on an emulator
levelOffset = stateOffset+int("4B20", 16)           #First tile in any level
levelIndex = stateOffset+int("1A", 16)              #Level index

createNew = True                                    #If true, this script creates a whole new .tmx file instead of editing an existing one. Edit mode might be less stable

creatureAmt = 0                                     #Total amount of valid creatures found inside the level
creatureFull = []                                   #Creature attribute table
creatureFullByte = []                               #Creature attribute table (8-bit mode)

#INCOMPLETE: Objects can be created in Tiled with an included sprite. Then they can be added to this table in succession
creatureSets = ["Woody.tsx",
                None,
                None,
                None,
                None,
                "Train.tsx",
                None,
                "Plane.tsx",
                None,
                "Planespin.tsx",
                None,
                "Helicopter.tsx",
                None,
                "Hangsun.tsx",
                None,
                "Balloon.tsx",
                None,
                "Ball.tsx",
                None,
                None,
                None,
                "Hamm.tsx"
]

creatureSets.extend([None]*50)                      #Allocates the table so that creatures with a high ID can be included from the get go
creatureSets[33] = "Rocky.tsx"                      #This would be an example of such a case
creatureSets[27] = "Robot.tsx"
creatureSets[71] = "MrPotato.tsx"
creatureSets[41] = "Lamp.tsx"

#This function looks for a specific filename in path
def findFile(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)

#This list holds the specific width for each level. 'None' is there because it's Really Inside, which doesn't even use 2D tiles
lWidth = [
    256,
    256,
    512,
    32,
    64,
    256,
    1024,
    32,
    512,
    32,
    None,
    64,
    512,
    256,
    1024,
    32,
    512
]

#This list stores the name of all the levels, exclamation points are removed (such as from "The Claw!"), useful when writing to a new file 
lName = [
    "That Old Army Game",
    "Red Alert",
    "Ego Check",
    "Nightmare Buzz",
    "A Buzz Clip",
    "Revenge Of The Toys",
    "Run, Rex, Run",
    "Buzz Battle",
    "Food And Drink",
    "Inside The Claw Machine",
    "Really Inside The Claw Machine",
    "The Claw",
    "Sid's Workbench",
    "Battle Of The Mutant Toys",
    "Roller Bob",
    "Light My Fire",
    "Rocket Man"
]

#A creature is an obstacle, enemy or interactable object in the game. An object has the following known attributes (48 bytes in total per object)
creatureDict = {
    "01. X-pos":            0,
    "02. Y-pos":            0,
    "03. X-start":          0,  
    "04. Y-start":          0, 
    "05. Render X-start":   0,
    "06. Render Y-start":   0,
    "07. Render X-end":     0,
    "08. Render Y-end":     0,
    "09. Palette":          0,
    "10. Animation Frame":  0,
    "11. Animation Speed":  0,
    "12. Creature index":   0,
    "13. X-end":            0,
    "14. Y-end":            0,
    "15. UNKNOWN A":        0,
    "16. UNKNOWN B":        0,
    "17. Hitbox X-offset":  0,
    "18. Hitbox Y-offset":  0,
    "19. Hitbox X-size":    0,
    "20. Hitbox Y-size":    0,
    "21. UNKNOWN C":        0,
    "22. Cooldown":         0,
    "23. UNKNOWN D":        0,
    "24. UNKNOWN E":        0
}

#This is a meta table that helps us keep track of the order in which the variables appear
#It's very important that they are put back in this order, as this is the order they appear in RAM
creatureEntry = [
    "01. X-pos",
    "02. Y-pos",
    "03. X-start",  
    "04. Y-start", 
    "05. Render X-start",
    "06. Render Y-start",
    "07. Render X-end",
    "08. Render Y-end",
    "09. Palette",
    "10. Animation Frame",
    "11. Animation Speed",
    "12. Creature index",
    "13. X-end",
    "14. Y-end",
    "15. UNKNOWN A",
    "16. UNKNOWN B",
    "17. Hitbox X-offset",
    "18. Hitbox Y-offset",
    "19. Hitbox X-size",
    "20. Hitbox Y-size",
    "21. UNKNOWN C",
    "22. Cooldown",
    "23. UNKNOWN D",
    "24. UNKNOWN E"
]

#This table is similar to the previous one, but here the 16-bit entries are split into 8-bit HI-byte+LO-byte segments
#Most attributes are stored handled as 16-bit but in some cases, only a single byte is used. This table also helps with some of the math
creatureEntryByte = [
    "01. X-pos LO",
    "02. X-pos HI",
    "03. Y-pos LO",
    "04. Y-pos HI",
    "05. X-start LO",
    "06. X-start HI",  
    "07. Y-start LO", 
    "08. Y-start HI",
    "09. Render X-start LO",
    "10. Render X-start HI",
    "11. Render Y-start LO",
    "12. Render Y-start HI",
    "13. Render X-end LO",
    "14. Render X-end HI",
    "15. Render Y-end LO",
    "16. Render Y-end HI",
    "17. Palette LO",
    "18. Palette HI",
    "19. Animation Frame LO",
    "20. Animation Frame HI",
    "21. Animation Speed LO",
    "22. Animation Speed HI",
    "23. Creature index LO",
    "24. Creature index HI",
    "25. X-end LO",
    "26. X-end HI",
    "27. Y-end LO",
    "28. Y-end HI",
    "29. UNKNOWN A LO",
    "30. UNKNOWN A HI",
    "31. UNKNOWN B LO",
    "32. UNKNOWN B HI",
    "33. Hitbox X-offset LO",
    "34. Hitbox X-offset HI",
    "35. Hitbox Y-offset LO",
    "36. Hitbox Y-offset HI",
    "37. Hitbox X-size LO",
    "38. Hitbox X-size HI",
    "39. Hitbox Y-size LO",
    "40. Hitbox Y-size HI",
    "41. UNKNOWN C LO",
    "42. UNKNOWN C HI",
    "43. Cooldown LO",
    "44. Cooldown HI",
    "45. UNKNOWN D LO",
    "46. UNKNOWN D HI",
    "47. UNKNOWN E LO",
    "48. UNKNOWN E HI"
]

def readMap():
    levelSize = int("2000", 16)                 #Size of the level in hex (should be 8192 or 0x2000, which is full size)
    columnSize = 64                             #Size of the columns used for formatting the output file
    insertAmt = levelSize/columnSize            #Defines how many times newlines have to be inserted into the list
    file.seek(levelOffset, 0)                   #Seek to offset where the level tiles are located before data is read
    number=list(file.read(levelSize))           #Read the entire level from RAM, specified from offset
    starAmt = 0                                 #Keeps track of the total amount of stars, may be helpful when trying to reach 50
    i = 0
    while i < len(number):
        if (int(number[i]) == 254) or (int(number[i]) == 255):
            starAmt += 1
        i += 1

    #The list is a straight string from number to number, there has to be a colon between each number which is done here
    i = 1
    while i < len(number):                      #insertAmt is being cast into integer just in case the divison becomes a decimal number
        number.insert(i, ",")                   #Newline has to be inserted, otherwise the output will have one giant row
        i += 2                                  #Inserted every other line
        
    #Newline has to be inserted, otherwise the output will have one giant row
    insertAmt = int(len(number))/columnSize    #Previous loop changed the size of the list, so this reevaluates it
    insertAmt = int(insertAmt)
    i = 1
    while i < int(insertAmt):                   #insertAmt is being cast into integer just in case the divison becomes a decimal number
        number.insert(columnSize*i, "\n")       #Using columnSize as a variable so it can be adjusted easier
        i += 1
    print(levelSize, "bytes read starting at offset", hex(objectOffset),"\nTotal stars:",starAmt)  #Tells us how much was read at said offset
    return number

#Because there are 48 bytes per creature and there are 48 creatures, we can do a nested loop that reads 48 bytes and then increments z
#z will then be used as the creature number (0 = first creature, 1 = second creature, etc)
def readCreatures(ByteMode):
    global creatureFull
    global creatureAmt
    global creatureFullByte
    readAll = False             #If false, the function only loads as many creatures that exist in the level. If true, it loads the full raster
    reformatValues = True       #If true, all read values will be properly converted from unsigned to signed integers
    calcus = 0
    if readAll == True:         
        creatureAmt = 48        #We already know that if all creatures are being read, the amount is going to be 48
    i = 0
    x = 0
    z = 0
    while z < 48:               #We're making a two-dimensional loop here, first we're looking to load 48 creatures
        while i < 48:           #Then, we're going to load 48 values from each creature (or 24 16-bit values)
            file.seek(objectOffset+(z*48)+i, 0)                   #Seek to offset where the the objects are loaded
            enemy=list(file.read(2))                        #Read two bytes at a time (we want to store 16-bits into a single integer)
            calcus = enemy[0] + (256 * enemy[1])            #Low byte + (256 * high byte), when a value reaches 256, high is +1 and low wraps to 0
            if ((i == 0) and (calcus == 0)) and readAll == False:   
                file.seek(objectOffset+(z*48)+2, 0)               #This is hard-coded to go through all 48 possible creatures, controlled by readAll 
                enemy=list(file.read(2))                    #Read two bytes
                calcus = enemy[0] + (256 * enemy[1])        #Read as low byte + (256 * high byte), little endian to integer conversion
                if calcus == 0:                             #All valid creatures have a X-pos beyond 0, so if 0 is read, we know there are no more
                    creatureAmt = z                         #At this point, the amount of creatures are known
                    z = 48                                  #We're setting this to 48 in order to get out of the loop
                    break
            creatureDict[creatureEntry[x]] = calcus
            creatureFull.append(calcus)
            i += 2
            x += 1
        i = 0
        while i < 48:                                       #This is a terrible solution, but for now, another loop after the first one is added in tandem
            file.seek(objectOffset+(z*48)+i, 0)                   #This solution is here because we want some values as 8-bit instead of 16-bit
            enemy2=list(file.read(1))                       #I didn't want to tamper with the original function
            enemyVal = int(enemy2[0])
            creatureFullByte.append(enemyVal)
            i += 1
        i = 0
        z += 1
        x = 0
    if reformatValues == True:
        i = 0
        y = 0
        while i < creatureAmt:
            while y < 24:
                if creatureFull[y+(24*i)] > 32768:                     #Max value of a signed 16-bit integer, if value is bigger, we know we need to convert it
                    creatureFull[y+(24*i)] = 65536 - creatureFull[y+(24*i)]   #All values will be negative with this offset, (FFFF = -1), so this formula should solve it
                    creatureFull[y+(24*i)] = creatureFull[y+(24*i)] * -1      #The remainder is then inverted to actually turn it into a negative value
                y += 1
            i += 1
            y = 0
    if ByteMode == True:
        return creatureFullByte
    else:
        return creatureFull

#This is a test or debug function that just dumps creature variables into a text file in the same folder as this script
def writeOutput():
    filename = 'output_obj.txt'
    outfile = open(filename, 'w')
    i = 0
    z = 0
    string = ""
    string2 = ""
    while z < creatureAmt:
        string2 = "#Creature number: " + str(z) + "\n"
        outfile.writelines(string2)
        while i < 24:
            string = "  " + creatureEntry[i] + " - " + str(creatureFull[i+(z*24)]) + "\n"
            outfile.writelines(string)
            i += 1
        z += 1
        i = 0
    outfile.close()

def editFile():
    x = 0
    y = 0
    z = 0
    
    readLevel = open(levelFile, 'r').readlines()    #We're reading the entire file
    writeLevel = open(levelFile,'w')                #We need to read it again as a new instance but with write enabled

    #This list is injected into the map file with the relevant variables
    list = ["<object id=\"{0}\" gid=\"{1}\" name=\"Creature {2}\" type=\"Creature\" x=\"{3}\" y=\"{4}\">", 
            " <properties>",
            "  <property name=\"{0}\" type=\"int\" value=\"{1}\"/>",
            " </properties>",
            "</object>", "\n"]

    
    for line in readLevel:                      #This function is here because we need to find the highest ID used in the map file
        if (str(" id=") in line) and (str("<object ") not in line):
            line = line.strip()                 #Strip blank spaces to make things a bit more tidy
            line1 = line
            testus = re.findall(r'\d+',line1)   #Searches for IDs in map file
            testus = int(testus[0])             #It returns a string so we need to cast it 
            if int(testus) > x:                 #Here we iterate through all IDs in the file and we want to save the highest
                x = testus                      #Save this value so we know the current highest ID we can use in the map
    for line in readLevel:                      #Read the map file line by line in a loop
        if str("<objectgroup") in line:         #After the objectgroup line, we can pass just about every variable that the creature requires
            writeLevel.write(line)
            while z < creatureAmt:              #We don't need to iterate beyond the amount of actual creatures in the level
                for item in list:
                    if y == 2:
                        while y < 24:
                            new_line = "\n %s" %(item.format(creatureEntry[y],creatureFull[y+(z*24)]))
                            writeLevel.write(new_line)
                            y += 1
                    else:
                        new_line = "\n %s" %(item.format(x+1,258+(creatureFull[11+(z*24)]),z,creatureFull[0+(z*24)],creatureFull[1+(z*24)]))   
                        writeLevel.write(new_line)
                    y += 1
                x += 1
                y = 0
                z += 1
        elif (str("<object ") in line) or (str("propert") in line) or (str("</object>") in line) or (str("<point/>") in line):
            #print("Object already exists, ignoring...")
            pass
        else:
            writeLevel.write(line)
        
    writeLevel.close()

def makeFile():
    outfile = open(levelFile, 'w')
    w = lWidth[lIndex[0]]
    h = int(8192 / w)                       #Levels can be 8192 bytes max, level width is stored in a table so we can divide max size with that width to get the height
    print("Level dimensions:",w,"x",h,"tiles")
    
    #This is the formatting of Tiled's map files, this may change though with later versions of Tiled. If so, this list has to be adjusted accordingly
    formatList = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
        "<map version=\"1.10\" tiledversion=\"1.10.2\" orientation=\"orthogonal\" renderorder=\"right-down\" width=\"{0}\" height=\"{1}\" tilewidth=\"32\" tileheight=\"32\" infinite=\"0\" nextlayerid=\"{2}\" nextobjectid=\"{3}\">\n",
        "<tileset firstgid=\"{0}\" source=\"{1}\"/>\n",
        "<layer id=\"{0}\" name=\"{1}\" width=\"{2}\" height=\"{3}\" offsetx=\"{4}\" offsety=\"{5}\">\n",
        "<data encoding=\"csv\">\n",
        "\n</data>\n",
        "</layer>\n",
        "<objectgroup id=\"{0}\" name=\"{1}{2}\" visible=\"{3}\" index=\"{4}\">\n",
        "<object id=\"{0}\" gid=\"{1}\" name=\"{2}\" class=\"{3}\" x=\"{4}\" y=\"{5}\" width=\"{6}\" height=\"{7}\" visible=\"{8}\"/>\n",
        "</objectgroup>\n",
        "</map>\n"
    ]
    
    fullMap = readMap()                                     #Read the map raster
    fullCreatures = readCreatures(False)                    #Read in 16-bit mode (useful for all coordinate variables)
    fullCreaturesByte = readCreatures(True)                 #Read in 8-bit mode (required for some variables as the 16-bit mode read can end up combining two unrelated values)
    print("Number of creatures loaded:",creatureAmt)        #This tells us how many creatures are actually put into the level
    mapSetup = []
    
    file.seek(stateOffset+int("1730", 16), 0)               #If available, Woody's coordinates can be read from the save state
    mapSetup = list(file.read(6))
    woodyX = mapSetup[0] + (mapSetup[1]*256)
    woodyY = mapSetup[4] + (mapSetup[5]*256)
    
    file.seek(stateOffset+int("15A", 16), 0)                #Read the defined border size from RAM
    mapSetup = list(file.read(8))
    
    #Game stores border as variables X-start and X-end. By taking X-end and subtracting it with X-start, the width can be calculated
    #This is required because Tiled only has a startin X and Y position for a region, and then uses a width offset from those positions
    borderX = mapSetup[0] + (mapSetup[1]*256)
    borderY = mapSetup[4] + (mapSetup[5]*256)
    borderW = (mapSetup[2] + (mapSetup[3]*256)) - borderX
    borderH = (mapSetup[6] + (mapSetup[7]*256)) + borderY
    x = 0
    for i in formatList:
        if x == 1:
            reformat = "\n %s" %(i.format(w,h,0,0))
            outfile.write(reformat)
        elif x == 2:
            if args.tileset == None:                                                 #If no tileset was specified, then choose this placeholder
                levelID = str(lIndex[0])
                levelTitle = str(lName[lIndex[0]])
                tileSet   = levelID+" - "+levelTitle+".tsx"                          #The placeholder is simply named after the id and title of the level
                reformat = "\n %s" %(i.format(1,tiledPath+"/Tilesets/"+tileSet))
            else:
                tileSet = args.tileset
                reformat = "\n %s" %(i.format(1,tiledPath+"/Tilesets/"+tileSet))
            outfile.write(reformat)
            a = 0
            while a < 72:
                if findFile(creatureSets[a], tiledPath+"/Tilesets"+"/Creatures"):
                    reformat = "\n %s" %(i.format(257+a,tiledPath+"/Tilesets"+"/Creatures/"+creatureSets[a]))
                    outfile.write(reformat)
                else:
                    #This part is used to print a placeholder icon for the creatures that don't yet have one
                    #reformat = "\n %s" %(i.format(257+a,tiledPath+"/Tilesets"+"/Creatures/"+"Placeholder.tsx"))    #Placeholder balloon if tilesets do not exist
                    #outfile.write(reformat)
                    pass
                a += 1
        elif x == 3:
            reformat = "\n %s" %(i.format(0,"Tiles",w,h,0,0))
            outfile.write(reformat)
        elif x == 4:
            outfile.write(i)
            for i in fullMap:
                outfile.write(str(i))
        elif x == 7:
            reformat = "\n %s" %(i.format(0,"Level","",1,0))
            outfile.write(reformat)
        elif x == 8:
            if woodyX + woodyY == 0:                
                pass                                       #Ignore placing Woody as an object if his position is zero
            else:
                reformat = "\n %s" %(i.format(0,257,"Woody","Level",woodyX,woodyY,41,85,1))
                outfile.write(reformat)
            if borderW + borderH == 0:
                pass
            else:
                reformat = "\n %s" %(i.format(0,0,"Level Border","Level",borderX,borderY,borderW,borderH,0))
                outfile.write(reformat)
            outfile.write(formatList[9])
            y = 0
            z = 0
            while y < creatureAmt:
                reformat = "\n %s" %(formatList[7].format(0,"Creature ",y,1,14))
                outfile.write(reformat)
                
                outfile.write("<properties>\n")
                
                b = 16
                while b < 48:
                    if (b == 24) or (b == 25) or (b == 26) or (b == 27) or (b == 32) or (b == 33) or (b == 34) or (b == 35) or (b == 36) or (b == 37) or (b == 38) or (b == 39):
                        pass        #Ignore these values because they are already dealt with earlier
                    else:
                        reformat = "\n %s" %("<property name=\"{0}\" type=\"{1}\" value=\"{2}\"/>".format(creatureEntryByte[b],"int",fullCreaturesByte[(y*48)+b]))
                        outfile.write(reformat)
                    b += 1
                b = 0
                
                outfile.write("\n</properties>")

                #Some math has to be done because the game stores most of the object coordinate data as points for X and Y, and then calculates a region based on that
                #For instance, the game stores render region X-start and X-end as separate values, subtracting X-end with X-start gets us the width of the region
                #Tiled only stores the region with a starting X and Y position, and then uses a specified width to get the end point
                patrolX = fullCreatures[(y*24)+12] - fullCreatures[(y*24)+2]
                patrolY = fullCreatures[(y*24)+13] - fullCreatures[(y*24)+3]
                renderX = fullCreatures[(y*24)+6] - fullCreatures[(y*24)+4]
                renderY = fullCreatures[(y*24)+7] - fullCreatures[(y*24)+5]
                
                hitboxX = fullCreatures[(y*24)+0] - fullCreatures[(y*24)+16]
                hitboxY = fullCreatures[(y*24)+1] + fullCreatures[(y*24)+17]
                    
                reformat = "\n %s" %(i.format(0,258+creatureFull[(y*24)+11],"01 - Position","Creature",creatureFull[(y*24)+0],creatureFull[(y*24)+1],None,None,0))
                outfile.write(reformat)
                reformat = "\n %s" %(i.format(0,0,"02 - Patrolling zone","Creature",fullCreatures[(y*24)+2],fullCreatures[(y*24)+3],patrolX,patrolY,0))
                outfile.write(reformat)
                reformat = "\n %s" %(i.format(0,0,"03 - Render zone","Creature",fullCreatures[(y*24)+4],fullCreatures[(y*24)+5],renderX,renderY,0))
                outfile.write(reformat)
                reformat = "\n %s" %(i.format(0,0,"04 - Hitbox size","Creature",hitboxX,hitboxY,fullCreatures[(y*24)+18],fullCreatures[(y*24)+19],1))
                outfile.write(reformat)

                y += 1
                outfile.write(formatList[9])
        elif x == 9:
            pass                #This is already written in the big loop
        else:
            outfile.write(i)
        x += 1
    outfile.close()    

if os.path.getsize(fileName) != stateSize:              #Fail safe so that we're not reading junk from the wrong file
    print("ERROR: Save state has the wrong file size. Has the correct file been chosen?")
    sys.exit()

file.seek(levelIndex, 0)                                #Read the level index to figure out what level is being handled
lIndex=list(file.read(1))                               #The name of the level is not stored in RAM, so a table is used to print it here
print("Level loaded from state:",lIndex[0],"-",lName[lIndex[0]])                       #Level number index + level name printed

if createNew == True:    
    makeFile()                                          #Create a new .tmx file for Tiled to handle
else:
    editFile()                                          #Edit an existing Tiled map file to add the creatures and map tiles in there
file.close()                                            #Finally the save state/RAM dump is closed