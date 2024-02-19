# TiledStory
Development tools for editing and creating custom levels for Disney's Toy Story (Super Nintendo/Sega Genesis)

![Screenshot of the first level of Toy Story in Tiled](https://i.imgur.com/gOryVqy.jpg)

# About
The goal of this repo is to provide development tools so that people can create their own levels for Toy Story.

Initially, a dedicated level editor was considered, but then the map editor Tiled was discovered. The focus of this project then changed to surround importing/exporting to/from Tiled.

Currently, only the SNES version of Toy Story is supported. A Genesis version of this tool set is considered but will not be made until the SNES tool set is complete.

# How it works
With the help of an emulator (such as BSNES-Plus), a save state can be made after all the assets have been loaded into RAM. Most of the assets in the game are compressed and need to be uncompressed and loaded into RAM before a level can be played. A save state therefor contains the full data of the level, which can then be exported to a level editor. A python script reads data from the save state and then creates a Tiled map file. This file can then be opened in Tiled and should contain the full level. Most of what the Python script is doing is converting and formatting data to the correct format.

Toy Story uses tiles to represent levels. Tiles are 32x32 pixels in size and there can be a total of 8192 tiles per level. Each tile is 1 byte in size which means that there can be a total of 256 different tiles in a level, with tile index 0 being an empty tile, and tile 254 and 255 being bonus stars spinning in different directions.

The script also handles creatures. Creatures are any moving object, obstacle, enemy or other interactable entity. These are stored in 48 bytes per creature, and there can be a total of 48 creatures at a time in one level.

# Requirements 
- BSNES-Plus-v05 - Most SNES emulators with save state support should work if you know how to enter your own offset and file size of state, but this is the emulator that the scripts have been setup with.
- Python 3.12.1 - This is the version that I've been using but older versions of python 3 may work as well.
- Tiled Map Editor - I've been using 1.10.2, which is the latest version as of writing.
- Unheadered SNES ROM of Toy Story, US-version.

# Setup
At the moment, this is how I set up my workflow.
The process is divided into two scripts:

- state2level.py: Imports save state data and outputs Tiled CSV level data
- level2state.py: Does the opposite, import Tiled CSV level data and outputs into a save state

Here's how the scripts can be integrated with Tiled:
1. Create some custom commands inside of Tiled (File->Commands->Edit Commands...).
2. \<new command> should appear in the list. Click it and rename it to create and name a new command.
   - Let's start with "Import from Save State". The fields can be filled out like this:
   - Executable: Link to the python runtime. (Example: C:/Python3/python.exe) (Note: If installed, simply just type **python** here.)
   - Arguments: **FILE.PY STATE.BST MAPFILE.TMX PATH/TO/MAP** (Example: **state2level.py "C:/Program Files/BSNES-Plus-v05/states/Toy Story (U) [!]-1.bst" %mapfile %mappath**)
   - Working Directory: Path to the folder where the python scripts are located, but this can be specified in the first argument instead.
   - Shortcut: Optional key command
   Make sure to also enable "Show output in Console view" as it provides some useful data about the level and potential warnings.
   Note that %mapfile and %mappath are variables that Tiled will automatically fill out from the level that you are working on, so there's no need to change these unless you're running the script outside of Tiled.
4. Repeat most of step 2, but this time, create a new command for exporting and call it "Export to Save State". Fill it out the same way except for these arguments: **level2state.py %mapfile STATE.BST %mappath**
5. Create a new map file (File->New->New Map...). Just click OK when a new box appears, the script will fill out the dimensions for us.
6. Use the command feature to import the level data (File->Commands->Import from Save State).
7. In order to actually see anything, a tileset is required. The script specifies the tileset to be the name of the level in-game and the path is specified to be inside a folder called Tilesets, relative to where the map is.
   - For example: From the first level, file test.tmx is saved to C:/Tiled/Maps/test.tmx.
   - Tileset will be loaded from C:/Tiled/Maps/Tilesets/0 - That Old Army Game.tmx
   - You can grab the sample tileset and tilesheet from the Tilesets folder in this repo.

# Workflow
Given that everything is up and running, this is how you would get started:
1. Load the ROM in BSNES, fast-forward to the Etch-n-Sketch screen. Wait a few seconds while holding fast-forward.
   - The game has fairly long loading times, and from first seeing the Etch-n-Sketch loading screen, it will take a few seconds before the game has uncompressed the level tile data.
   - To make sure everything is loaded, use the fast-forward feature in the emulator and wait a few seconds before you make a save state. The game has loaded all relevant data into RAM if the screen fades out at the press of a button.
2. Make a save state on slot 1 and 2, given that the path is linked to save state 1.
3. In Tiled: Import from Save State.
4. Customize level and save it in Tiled.
5. Now use Export to Save State.
   - The data is exported to the same state that you read from, so the process can be continuous. If you want to clear the level, simply load state 2 and save it into state 1.
6. Load save state 1. Press any button to progress from the Etch-n-Sketch screen. You should now see the changes that you've made once the level has loaded.

### Notes
   - You can both save and load while already inside a level, but it's much more instable. All creature objects will also be in a different position. If the save state is loaded from the loading screen, none of the creatures have moved.
   - The main function of the scripts is to import/export to/from save states, but ROM files are now supported (see more below).
   - Tilesets are not included, because they would contain game assets. You can technically edit the level without a tileset but it would obviously be difficult to see what you're doing.

## More notes on tilesets
I painstakingly made my own tilesets by taking screen shot dumps from the Tile viewer in the emulator. Because I can't share these, the best method would probably be to create a tool so that the user can rip these themselves.

Here's some information on how they have to be setup:
  - Tilesets are 16x16 tiles in size, or 512x512 pixels. Each tile in the game is 32x32 pixels in size.
  - The game uses different layers for tiles: one for the front view and one for the parallax view. Parallax tiles are trickier to work with because you have to view the from a certain offset in game to see them.
  - Although each tile is stored in a single byte (0-255), Tiled handles the tileset a bit different. The first tile in the grid has to be tile 1, and the last will be 256. 256 is an invalid tile so just draw anything you want there.
  - Tiles 254 and 255 will always be stars, spinning counter-clockwise and clockwise respectively. The only exception I've seen is during the boss fights. Stars are also instantly updated if you manually edit tiles in an emulator.
  - Tile 0 is an empty tile.

## ROM import/export
With the help of [RNC ProPack compression tools](https://github.com/lab313ru/rnc_propack_source), it is now possible to read and write the level data directly from ROM. 
  - Replace the __savestate__ command line with a ROM file for both scripts, and then add a new command line depending on if you're exporting (**--exportmode 1**)) or importing (**--importmode 1**). By default these two modes are off (0).
  - Add a command line that links to the RNC ProPack runtimes with **--rnc**, pointing to the .exe file of the compressor.

## Tileset importer
Automatically importing a tileset graphics sheet from a save state can now be done with the help of the script called *readtileset.py*. 
This script requires the opencv2 module for Python. It can be installed with pip using: 
```
python -m pip install opencv-python
```
A few notes on the script so far:
  - Graphics data is being read directly from the VRAM dump in the save state. Because of this, tiles that reside within a part of the level which has not been loaded will be shown incorrectly. To combat this, the user can make a few save states in the same level at various points, create a sheet from each save state then combine them inside a graphics editor to get the complete tileset.
  - Although the graphics are read directly from VRAM, which means only currently loaded assets will be displayed correctly, some levels have every single tile with the correct color data stored in memory. Specifically, at address 0x18000, all front-facing tiles are stored for at least the first level and "Revenge of the Toys". 
  - Tilesets are saved as *.png* in a folder called *Tilesets*. Where this folder is created depends on what is parsed in the command line. Use ***%mappath*** to store the folder in the same directory as the map itself.
  - Importing from ROM is not yet supported with this script.
