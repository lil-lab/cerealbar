using System.Collections;
using System.Collections.Generic;
using System;
using UnityEngine.Networking;
using UnityEngine.UI;
using UnityEngine;
using System.IO;
using System.Runtime.InteropServices;

#pragma warning disable 0219 // Use of variable 'info' in SockSend does not avoid 0219.
#pragma warning disable 0414 // Use of selfCommunication does not avoid 0414.
/// <summary>
/// Main control for connecting main webgl unity to client javascript,
/// to send information to the server
/// </summary>
public class WebSocketManager : MonoBehaviour
{
      // Web Socket Library imports.
    [DllImport("__Internal")]
    private static extern void Init();
    [DllImport("__Internal")]
    private static extern void SockSend(string route, string msg);

    private InformationGetter infoGetter;
    private TimeKeeper timeKeeper;
    private ScoreKeeper scoreKeeper;
    private ExternalActionHandler theirHandler;
    private SelfCommunication selfCommunication;
    // private ExternalActionHandler myHandler; Commented because of 0414 unused warning.
    public GameObject lobbyScreen;
    public string character;

    public delegate void OnStartGamePlayHandler();
    public static event OnStartGamePlayHandler OnStartGamePlayEvent;

    public bool applicationHasFocus = true;

    void OnEnable()
    {
        infoGetter = FindObjectOfType<InformationGetter>();
        timeKeeper = FindObjectOfType<TimeKeeper>();
        scoreKeeper = FindObjectOfType<ScoreKeeper>();
        selfCommunication = FindObjectOfType<SelfCommunication>();

        PropPlacement.OnMapCompleteEvent += GetExternalHandlers;
        PropPlacement.OnMapCompleteEvent += Test;
        PropPlacement.OnReadyToStartGamePlayEvent += ReadyToStartGamePlay;
        TurnController.GameOverEvent += SendFinalInfo;
        TurnController.GameOverQuitEvent += SendFinalInfo;

        #if UNITY_WEBGL && !UNITY_EDITOR
        Init();
        #endif
    }

    void Test()
    {
        foreach(var item in infoGetter.GetEyesightObjs("Agent"))
        {
            Debug.Log(item);
        }
    }

    void OnDisable()
    {
        PropPlacement.OnMapCompleteEvent -= GetExternalHandlers;
        PropPlacement.OnMapCompleteEvent -= Test;
        PropPlacement.OnReadyToStartGamePlayEvent -= ReadyToStartGamePlay;
        TurnController.GameOverEvent -= SendFinalInfo;
        TurnController.GameOverQuitEvent -= SendFinalInfo;
    }

    /* Sends a websocket message over route @route containing json information
    {"data", @data}. */
    public void SendString(string route, string data)
    {
        Dictionary<string, string> strData = new Dictionary<string, string>()
        {
            {"data", data},
        };
        Send(route, strData, null);
    }

    public void SendLog(string logMessage)
    {
        SendString("debug", logMessage);
    }

    /* Sends a websocket message over route "init" containing json information
    about initial map conditions @ tag is "Human" or "Agent" depending on
    which character was chosen. */
    public void SendMap(string tag)
    {
        if(Replay.replaying || TutorialGuide.tutorialMode) { return; }
        var info = infoGetter.GetMapInfo();
        #if UNITY_WEBGL
        if(!TutorialGuide.tutorialMode) { SockSend("init", info); }
        #endif
    }

    /* Sends a websocket message over route @route containing a json version
    of the data in @stringVals and @intVals. */
    public string Send(string route, Dictionary<string, string> stringVals, Dictionary<string, int> intVals)
    {
        if(Replay.replaying || TutorialGuide.tutorialMode) { return null; }
        string[] p = new string[2];
        p[0] = route;
        p[1] = "{\"time\": \"" + timeKeeper.gameTime + "\",";
        if (stringVals != null)
        {
            foreach (KeyValuePair<string, string> item in stringVals) {
                p[1] += "\"" + item.Key + "\":\"" + item.Value + "\",";
            }
        }
        if (intVals != null)
        {
            foreach (KeyValuePair<string, int> item in intVals) {
                p[1] += "\"" + item.Key + "\":" + item.Value + ",";
            }
        }
        p[1] = p[1].Substring(0, p[1].Length - 1);
        p[1] += "}";

        #if UNITY_WEBGL
        SockSend(p[0], p[1]);
        return "WEBGL";
        #endif

        #if UNITY_STANDALONE
        return "STANDALONE";
        #endif
    }

	public void GetExternalHandlers()
    {
        var them = GameObject.FindGameObjectWithTag(character=="Human"?"Agent":"Human");
        if (them)
            theirHandler = them.GetComponent<ExternalActionHandler>();

        /* var me = GameObject.FindGameObjectWithTag(character);
        if (me)
            myHandler = me.GetComponent<ExternalActionHandler>();
        */
    }

    public void SendFinalInfo()
    {
        if(!Replay.replaying)
        {
            Dictionary<string, int> intData = new Dictionary<string, int>()
            {
                {"score", scoreKeeper.score}
            };
            Send("gameOver", null, intData);
        }
    }

    public void ExternalMovement(string action)
    {
        switch (action)
        {
            case "RR":
                theirHandler.AddExternalAction(ActionInformation.AgentState.Turning, 1);
                break;
            case "RL":
                theirHandler.AddExternalAction(ActionInformation.AgentState.Turning, -1);
                break;
            case "MF":
                theirHandler.AddExternalAction(ActionInformation.AgentState.Walking, 1);
                break;
            case "MB":
                theirHandler.AddExternalAction(ActionInformation.AgentState.Walking, -1);
                break;
        }
    }

    public void ReadyToStartGamePlay()
    {
        var now = System.DateTime.Now;

        if(!Replay.replaying && !TutorialGuide.tutorialMode) { Send("readyToStartGamePlay", null, null); }
    }

    public void StartGamePlay()
    {
      var now = System.DateTime.Now;
      OnStartGamePlayEvent();
      if(!Replay.replaying) { lobbyScreen.SetActive(false); }
    }

    void OnApplicationFocus(bool f)
    {
        applicationHasFocus = f;
        SendString("changedFocus", f ? "true" : "false");
    }
}
