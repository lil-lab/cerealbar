This whole folder is used for creating the map including the bodies of water/hills, prop location and card generation. 

### BorderGen.cs

The invisible border that is generated to keep the player from falling off. 

### PropPlacement.cs

Handles the placement of EVERYTHING, including players and cards. Props are randomly selected from the [ScriptableObjects](https://github.com/clic-lab/cereal-bar/tree/master/Assets/Scripts/Scriptable_Objects/Objects)
Each type of prop (trees/ larger structures/ path objects) has a scriptable object that is basically used as a database of objects to place. In the future if you want to expand on the objects that get placed, create prefabs with the same properties/scripts attached as the type of object you wish to add and just drop them into the array within the scriptable object.


### HexMap scripts

This probably will not need to be touched. In the future if the group wants to make smaller maps, all the main map generation variables are public and can be changed via editor, or easily modified to be changed by script. 
Note that if the map size shrinks, you will also have to reduce the size of the ponds/hills/path splits, and the number of props placed for the obvious reason of not crashing the program while generating.

