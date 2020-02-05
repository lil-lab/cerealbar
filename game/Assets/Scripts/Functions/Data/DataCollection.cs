using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Data Collection Handles Getting all of the EndOfGameData information
/// </summary>
#pragma warning disable 0618 // Obsolete call to ExternalCall()
public class DataCollection : MonoBehaviour {

    private TimeKeeper tk;
    private HexGrid hexgrid;
    private ScoreKeeper score;
    private InformationGetter infoGetter;
    public Startup starterControl;
    public InstructionControl instrControl;
    // private WebSocketManager webSocketManager;

    public InputField databaseField;
    public InputField gameIDField;
    public Slider slider;
    private ExternalActionHandler handler;
    public GameObject dataPanel;
    public Text pausePlayText;
    // private ExternalActionHandler agentHandler;
    // private ExternalActionHandler humanHandler;

    // public static bool simulating = false;
    // private bool simPaused = false;
    public static List<string[]> inList;
    public static IOrderedEnumerable<string[]> moveList;
    public static int mLi = 0;

    public struct KeyMovement
    {
        public string direction;
        public float keyDownTime;
        public float keyUpTime;
    }

    //textinputs added to list by time,input,time,input...
    public List<EndOfGameData.Log> textInputs = new List<EndOfGameData.Log>();
    public List<EndOfGameData.FeedBack> feedbacks = new List<EndOfGameData.FeedBack>();

    //human actions time, action(MF,MB...),time, action...
    public List<EndOfGameData.Log> humanActions = new List<EndOfGameData.Log>();

    void OnEnable()
    {
        tk = FindObjectOfType<TimeKeeper>();
        hexgrid = FindObjectOfType<HexGrid>();
        score = FindObjectOfType<ScoreKeeper>();
        infoGetter = FindObjectOfType<InformationGetter>();
        // webSocketManager = FindObjectOfType<WebSocketManager>();
        starterControl = FindObjectOfType<Startup>();

        SetGame.OnNoSetsEvent += GetSubmitData;
        CommandCommunication.OnFeedbackEvent += LogFeedback;
        Restarter.OnRestartEvent += ClearAll;
        // PropPlacement.OnMapCompleteEvent += GetHandlers;
    }

    void OnDisable()
    {
        SetGame.OnNoSetsEvent -= GetSubmitData;
        CommandCommunication.OnFeedbackEvent -= LogFeedback;
        Restarter.OnRestartEvent -= ClearAll;
        // PropPlacement.OnMapCompleteEvent -= GetHandlers;
    }

    /// <summary>
    /// See EndOfGameData class. At the end of a play, this information is compiled
    /// and an external call for the web browser is made.
    /// </summary>
    private void GetSubmitData()
    {
        var eogData = new EndOfGameData();
        eogData.seed = hexgrid.seed;
        eogData.timeTaken = tk.gameTime;
        eogData.gameScore = score.score;
        eogData.agentControlType = infoGetter.agentMoveType.controlType;
        eogData.humanControlType = infoGetter.humanMoveType.controlType;

        eogData.humanActions = humanActions.ToArray();
        eogData.agentInstructions = textInputs.ToArray();

        eogData.agentFeedback = feedbacks.ToArray();
        Application.ExternalCall("EndOfGameData", JsonUtility.ToJson(eogData));
    }

    /*private void GetHandlers()
    {
        if(simulating) {
            var ag = GameObject.FindGameObjectWithTag("Agent");
            if(ag)
                agentHandler = ag.GetComponent<ExternalActionHandler>();

            var hum = GameObject.FindGameObjectWithTag("Human");
            if (hum)
                humanHandler = hum.GetComponent<ExternalActionHandler>();
        }
    }*/

    // Log record
    private void LogFeedback(bool good)
    {
        var f = new EndOfGameData.FeedBack();
        f.good = good;
        f.timeCalled = tk.gameTime;
        feedbacks.Add(f);
    }

    private string GetStringDirection(ActionInformation.AgentState agentState, int dir)
    {
        var directionStr = "forward";
        if (agentState == ActionInformation.AgentState.Walking)
        {
            if (dir == -1)
                directionStr = "MB";
            else
                directionStr = "MF";
        }
        else if (agentState == ActionInformation.AgentState.Turning)
        {
            if(dir == -1)
                directionStr = "RL";
            else
                directionStr = "RR";
        }
        return directionStr;
    }

    private void ClearAll()
    {
        textInputs.Clear();
        humanActions.Clear();
        feedbacks.Clear();
    }

}
