## CardGenerator.cs

Attached to the `MapManager` in the scene. Cards are created using the
`shapesDB` and `matsDB` which provide the shapes and colors that appear on the
set cards.

Cards are generated so that there is always at least 1 set in the 9 cards that
appear on the map. 9 cards does not guaranteed 3 sets as in the actual set game, 
you are not guaranteed all 9 cards match up.

`GenerateCards()` returns all the cards created to `PropPlacement.cs` which
handles putting the cards in available locations around the map.


## CardProperties.cs

This script is attached to the card prefabs. On card generation the properties
are grabbed and filled out. Shouldn't need to be touched.
