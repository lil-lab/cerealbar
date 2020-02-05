## Scripts for the python communication

### ExternalActionHandler.cs (attached to each agent)

This script handles the movement calls that are sent from the socket . Depending on the movement type for the specified agent, adds the action for the agent to do.
You can add actions to the cached and queued movements. For `Stop`,cached is not supported. To send over multiple actions in one go you can do `agent,MF,agent,MF...` or just tweak the script in `MainControl` to do a loop checking for commands.

### MainControl.cs

This is where the processing for the python commands is.

`ProcessMsgRequest()` handles:

- `start, <seednumber>`
- `restart, <seednumber> `
- `start information`
- `agent, <moveaction>` // to send multiples you can do ``agent, <moveaction>,agent, <moveaction>,agent, <moveaction>...`` OR you can change the code to just loop until a non action word is found.
-  `human, <moveaction>` //^
- image <overhead/human/agent>
- status <agent/human>
- `<quit/exit>`


### Socketstarter.cs

If the game is started and no connection is found, the script disables and the game continues for whatever other purpose it is being used for.
