//instructionControl
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class InstructionControl : MonoBehaviour
{
    private const string dashes = "---------------------------------------------------------------";

    //TODO: needs to make sure all the other parts work before removing this
    //commandHistory, scrollRect, history refers to the each respective gameObject or variable for leader
    //only the follower's will be specified: followerScrollRect, followerCommandHistory, followerHistory
    public InputField commandHistory;
    public ScrollRect scrollRect;

    public InputField commandPrompt;
    public InputField leaderCommandHistory;
    public Button submitButton;
    public ScrollRect leaderScrollRect;
    public WebSocketManager webSocketManager;
    public CommandCommunication commandCommunication;

    public ScrollRect followerScrollRect;
    public InputField followerCommandHistory;

    public bool hasNewInstruction = false;
    private string history, txt, followerHistory;
    public bool displayedHasNotSent = false;
    public GameObject notSentBanner;

    //the boolean variable checks if there are more commands coming from the leader

    private void Awake()
    {
    }

    void OnEnable()
    {
        webSocketManager = FindObjectOfType<WebSocketManager>();
        commandCommunication = FindObjectOfType<CommandCommunication>();
        //if(Replay.replaying) { commandHistory = GameObject.FindGameObjectWithTag("CommandHistoryData").GetComponent<InputField>(); }

        //TODO: need to adjust replay
        if (Replay.replaying)
        {
            leaderCommandHistory = GameObject.FindGameObjectWithTag("CommandHistoryData").GetComponent<InputField>();
        }

        Restarter.OnRestartEvent += ClearHistory;
    }

    void OnDisable()
    {
        Restarter.OnRestartEvent -= ClearHistory;
    }

    void Update()
    {   
        if (Input.GetKeyDown(KeyCode.Return) && commandPrompt.isFocused) { commandCommunication.SubmitCode(); }
    }

    public bool HasFocus()
    {
        return commandHistory.isFocused || (commandPrompt != null && commandPrompt.isFocused);
    }

    //Leader
    public void DisplayInstruction(string s)
    {
        commandCommunication.AddCommandToQueue(s);
        ShowCommands();
    }

    public void DisplayTurnGraphic() 
    {
        if (webSocketManager.character == "Human")
        {
            txt = commandHistory.text.Replace("<b>", "").Replace("</b>", "");
            commandHistory.text = txt;
            scrollRect.verticalNormalizedPosition = 0;
        }
        else
        {
            txt = followerCommandHistory.text.Replace("<b>", "").Replace("</b>", "");
            followerCommandHistory.text = txt;
            followerScrollRect.verticalNormalizedPosition = 0;
        }
    }

    //show commands from leader if there is any in instrBuffer
    public void ShowFollowerCommands() {
        txt = "";
        int currInstrIdx = CommandCommunication.currInstrIdx;
        List<string> currBuff = CommandCommunication.instrBuffer;

        // Only display the current one if there is a current one
        for (int i = 0; i <= currInstrIdx; i++)
        {
            if (i < currInstrIdx)
            {
                txt += "--- [DONE] " + currBuff[i] + "\n";
            }
            else if (currInstrIdx < currBuff.Count)
            {
                txt += "--- [CURRENT] " + currBuff[i] + "\n";
            }
        }
        // txt = txt + "<b>      " + dashes + dashes + "      </b>\n";

        followerCommandHistory.text = txt;
        followerScrollRect.verticalNormalizedPosition = 0;
        
        followerScrollRect.GetComponent<RectTransform>().ForceUpdateRectTransforms();
    }

    public void ShowLeaderCommands() {
        txt = "";
        int currInstrIdx = CommandCommunication.currInstrIdx;
        List<string> currBuff = CommandCommunication.instrBuffer;

        bool hasNotSent = false;

        for (int i = 0; i < currBuff.Count; i++) {
            if (i > currInstrIdx) {
                txt += "--- [NOT SENT] ";
                hasNotSent = true;
            } else if (i == currInstrIdx) {
                txt += "--- [CURRENT] ";
            } else {
                txt += "--- [DONE] ";
            }
            txt += currBuff[i] + "\n";
        }

        if (hasNotSent && !displayedHasNotSent) {
            notSentBanner.SetActive(true);
            displayedHasNotSent = true;
        }

        commandHistory.text = txt;
        scrollRect.verticalNormalizedPosition = 0;
        
        scrollRect.GetComponent<RectTransform>().ForceUpdateRectTransforms();

    }

    public void ShowCommands() {
        if (webSocketManager.character == "Human") {
            ShowLeaderCommands();
        } else {
            ShowFollowerCommands();
        }
    }

    public void TurnOff()
    {
        commandPrompt.interactable = false;
        submitButton.interactable = false;

    }

    public void TurnOn()
    {
        commandPrompt.interactable = true;
        submitButton.interactable = true;
    }

    public void FocusPrompt()
    {
        commandPrompt.Select();
        commandPrompt.ActivateInputField();
    }

    private void ClearHistory()
    {
        commandHistory.text = "";
        history = "";
        txt = "";
    }

}
