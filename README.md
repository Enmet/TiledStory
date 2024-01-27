# TiledStory
Development tools for editing and creating custom levels for Disney's Toy Story (Super Nintendo/Sega Genesis)

# About
The goal of this repo is to provide development tools so that people can create their own levels for Toy Story.

Initially, a dedicated level editor was considered, but then the map editor Tiled was discovered. The focus of this project then changed to surround importing/exporting to/from Tiled.

Currently, only the SNES version of Toy Story is supported. A Genesis version of this tool set is considered but will not be made until the SNES tool set is complete.

# How it works
With the help of an emulator (such as BSNES-Plus), a save state can be made after all the assets have been loaded into RAM. Most of the assets in the game are compressed and need to be uncompressed and loaded into RAM before a level can be played. A save state therefor contains the full data of the level, which can then be exported to a level editor. A python script reads data from the save state and then creates a Tiled map file. This file can then be opened in Tiled and should contain the full level. Most of what the Python script is doing is converting and formatting data to the correct format.
