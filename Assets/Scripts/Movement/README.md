## Types of Movement

### On human/agent each of these movement types are attached to the prefab with the `MovementType.cs` script being the script that sets the desired walking type to be active on runtime.
For the player, movement triggered from the onscreen UI arrow keys. Keyboard input is in each of the scripts for debugging purposes but is commented out. 


- Continuous : Hold keys to move
- Discrete : One key press prompts some pre-measured movement (parameters are seen in editor), "cached" movement in that multiple keypresses during movement does not do anything, need to wait for the movement to finish 
- Discrete Queued : Same as Discrete but multiple keypresses are saved and executed in order. If the key order results in object collision, the agent stops and the input is deleted 
- Hex to Hex : Player can only move to the neighboring 6 cells if they are empty. Cached
- Hex to Hex Queued : Hex to hex, but queued. 


