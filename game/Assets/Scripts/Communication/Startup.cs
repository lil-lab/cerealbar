using System.Collections;
using System.Collections.Generic;
using System;
using System.Runtime.InteropServices;
using System.Linq;
using UnityEngine.Networking;
using UnityEngine.UI;
using UnityEngine;

/// <summary>
/// Control for handeling the startup procedure
/// </summary>
public class Startup : MonoBehaviour
{
    [DllImport("__Internal")]
    private static extern string QueryPasscode();

    private HexGrid hexGrid;
    private PropPlacement propPlacement;
    private StartUIControl startUIControl;
    private SetUpUIControl setUpUIControl;
    private TurnController turnController;
    private CardGenerator cardGenerator;
    private SetGame setGame;
    private WebSocketManager webSocketManager;


    private string character;
    private int seed;

    private DateTime timeOutDeadline;
    private TimeSpan timeOutTime = new TimeSpan(0,5,0); // 5 minutes
    private DateTime nextCheckIn;
    private TimeSpan checkInLength = new TimeSpan(0,1,0); // 1 minute
    private bool waiting;

    public delegate void OnTutorialStartHandler();
    public static event OnTutorialStartHandler OnTutorialStartEvent;

    public static Startup StartupInstance {get; private set;}

    void Awake()
    {
        StartupInstance = this;
    }

    void OnEnable()
    {
      hexGrid =          FindObjectOfType<HexGrid>();
      propPlacement =    FindObjectOfType<PropPlacement>();
      startUIControl =   FindObjectOfType<StartUIControl>();
      setUpUIControl =   FindObjectOfType<SetUpUIControl>();
      turnController =   FindObjectOfType<TurnController>();
      cardGenerator =   FindObjectOfType<CardGenerator>();
      webSocketManager = FindObjectOfType<WebSocketManager>();
      setGame = FindObjectOfType<SetGame>();
    }

    public void QueryPasscodeUnity()
    {
        if(!Application.isEditor)
        {
          QueryPasscode();
        }
    }

    public void JoinLobby()
    {
      webSocketManager.Send("joinLobby", null, null);
      startUIControl.JoinLobby();
      timeOutDeadline = System.DateTime.Now.Add(timeOutTime);
      nextCheckIn = System.DateTime.Now.Add(checkInLength);
      waiting = true;
      StartCoroutine(RunTimer());
    }

    public void LobbyReady()
    {
      startUIControl.LobbyReady();
    }

    public void ReadyPressed()
    {
      webSocketManager.Send("readyPressed", null, null);
      startUIControl.ReadyPressed();
    }

    public void SetSeed(string s)
    {
        int x = 0;
        Int32.TryParse(s, out x);
        seed = x;
    }

    public void SetCharacter(string ch)
    {
        character = ch;
        webSocketManager.character = ch;
        turnController.character = ch;
        startUIControl.character = ch;
        setGame.character = ch;
    }

    public void SetNumCards(int numCards)
    {
        cardGenerator.numCards = numCards;
    }

    public void StartGame()
    {
        waiting = false;
        hexGrid.UpdateSeed(seed);
        hexGrid.CreateTestGrid();
        startUIControl.StartGame();
    }

    public void StartRecording()
    {
        //VideoCaptureCtrl.instance.StartCapture();
    }

    public void StopRecording()
    {
        //VideoCaptureCtrl.instance.StopCapture();
    }

    public void StandaloneStart()
    {
      // Generate seed.
      string _seed = new System.Random().Next(100000000).ToString();

      // Initialize game.
      SetSeed(_seed);
      SetCharacter("Human");
      StartGame();
      webSocketManager.StartGamePlay();
    }

    public bool StandaloneStartWithSeed(int seed, int numCards)
    {
      if (startUIControl.gameStarted)
      {
        return false;
      }
      else
      {
        SetSeed(seed.ToString());
        SetCharacter("Human");
        SetNumCards(numCards);
        StartGame();
        webSocketManager.StartGamePlay();
        return true;
      }
    }

    public bool SetState(string jsonState) {
      if (!startUIControl.gameStarted)
      {
        return false;
      }
      else
      {
        // Parse the JSON
        StateDelta stateDelta = JsonUtility.FromJson<StateDelta>(jsonState);

        SetSeed(seed.ToString());
        SetCharacter("Human");
        setGame.reset = true;
        SetNumCards(stateDelta.cards.Length);
        propPlacement.PlaceCardsWithState(stateDelta.cards, stateDelta.lead, stateDelta.follow);
        propPlacement.PlacePlayersWithState(stateDelta.lead, stateDelta.follow);
        return true;
      }
    }

    public void TutorialStart(string character)
    {
        startUIControl.leaderQualBtn.interactable = false;
        startUIControl.followerQualBtn.interactable = false;
        startUIControl.lobbyButton.interactable = false;
        startUIControl.optionsButton.interactable = false;
        startUIControl.optionsButton.gameObject.SetActive(false);
        startUIControl.promptText.gameObject.SetActive(false);
        SetSeed(0.ToString());
        SetCharacter(character);
        TutorialGuide.role = character;
        propPlacement.numStructures = 8;
        propPlacement.numTrees = 29;
        propPlacement.numPathObjects = 29;
        OnTutorialStartEvent();
        StartGame();
        webSocketManager.StartGamePlay();
    }

    private IEnumerator RunTimer()
    {
        while (waiting)
        {
            yield return new WaitForSeconds(1f);
            CheckTimeOut();
        }
        yield break;
    }

    private void CheckTimeOut()
    {
      if (timeOutDeadline < System.DateTime.Now)
      {
        waiting = false;
      }
    }

    public void Reset()
    {
      startUIControl.TimeOut();
      waiting = false;
    }
}
