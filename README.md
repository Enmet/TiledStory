# TiledStory
Development tools for editing and creating custom levels for Disney's Toy Story (Super Nintendo/Sega Genesis)

# About
The goal of this repo is to provide development tools so that people can create their own levels for Toy Story.

Initially, a dedicated level editor was considered, but then the map editor Tiled was discovered. The focus of this project then changed to surround importing/exporting to/from Tiled.

Currently, only the SNES version of Toy Story is supported. A Genesis version of this tool set is considered but will not be made until the SNES tool set is complete.

# How it works
With the help of an emulator (such as BSNES-Plus), a save state can be made after all the assets have been loaded into RAM. Most of the assets in the game are compressed and need to be uncompressed and loaded into RAM before a level can be played. A save state therefor contains the full data of the level, which can then be exported to a level editor. A python script reads data from the save state and then creates a Tiled map file. This file can then be opened in Tiled and should contain the full level. Most of what the Python script is doing is converting and formatting data to the correct format.

Toy Story uses tiles to represent levels. Tiles are 32x32 pixels in size and there can be a total of 8192 tiles per level. Each tile is 1 byte in size which means that there can be a total of 256 different tiles in a level, with tile index 0 being an empty tile, and tile 254 and 255 being bonus stars spinning in different directions.

The script also handles creatures. Creatures are any moving object, obstacle, enemy or other interactable entity. These are stored in 48 bytes per creature, and there can be a total of 48 creatures at a time in one level.

# Requirements 
-BSNES-Plus-v05 - Most SNES emulators with save state support should work if you know how to enter your own offset and file size of state, but this is the emulator that the scripts have been setup with.
-Python 3.12.1 - This is the version that I've been using but older versions of python 3 may work as well.
-Tiled Map Editor - I've been using 1.10.2, which is the latest version as of writing.
-Unheadered SNES ROM of Toy Story, US-version.

# Setup
At the moment, this is how I set up my workflow.
The process is divided into two scripts:
*state2level.py: This script imports save state data and outputs Tiled CSV level data
*level2state.py: This script does the opposite; importing Tiled CSV level data and writes the data into a save state

Here's how the scripts can be integrated with Tiled:
1. Create some custom commands inside of Tiled (File->Commands->Edit Commands...).
2. \<new command> should appear in the list. Click it and rename it to create and name a new command.
   -Let's start with "Import from Save State". The fields can be filled out like this:
   -Executable: Link to the python runtime. (Example: C:/Python3/python.exe)
   -Arguments: FILE.PY STATE.BST MAPFILE.TMX PATH/TO/MAP (Example: state2level.py "C:/Program Files/BSNES-Plus-v05/states/Toy Story (U) [!]-1.bst" %mapfile %mappath)
   -Working Directory: Path to the folder where the python scripts are located, but this can be specified in the first argument instead.
   -Shortcut: Optional key command
   Make sure to also enable "Show output in Console view" as it provides some useful data about the level and potential warnings.
   Note that %mapfile and %mappath are variables that Tiled will automatically fill out from the level that you are working on, so there's no need to change these unless you're running the script outside of Tiled.
4. Repeat step 2, this time, create a new command for exporting and call it "Export to Save State". Fill it out the same way except for these arguments: level2state.py %mapfile STATE.BST %mappath
5. Create a new map file (File->New->New Map...). Just click OK when a new box appears, the script will fill out the dimensions for us.
6. Use the command feature to import the level data (File->Commands->Import from Save State). 

# Workflow
