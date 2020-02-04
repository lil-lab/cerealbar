## This folder holds the various kinds of data that is collected/transmitted

### DataCollection.cs

Basic play data collection. Human moving models (see `KeyMovement` struct), tab presses, textinputs, feedback, etc. To get all this infrmation `GetSubmitData` will compile it and make an external call called `EndOfGameData` that a web application will have to catch. This can be modified if the information is not intended to be caught from the web app. 

### EyesightVision.cs

Record of the current objects in the "eyesight scope" of each player. This is pulled by infogetter for the information that is sent over python

### InformationGetter.cs

This is the most important script that handles the information collection for the python/socket stuff. 
All the information needed to be sent is collected and accessible here 
Note that all vector3's are sent as strings in order to concat the amount of digits that get sent over the socket (Vect3's are composed of floats). 


### Screenshot.cs

Handles getting the screenshots of the agent/human/overhead view. Agent and Human run as coroutines because you have to wait for the end of the frame to grab a screenshot. 
