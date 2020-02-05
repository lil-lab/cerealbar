using System.Collections;
using System.Collections.Generic;
using System;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Controls how turns switch between the two players.
/// A 'turn' is each time a single player has control over the game. A 'round'
/// is the number of leader+follower turns remaining.
/// </summary>
#pragma warning disable 0414  // Disable webSocketManager unused warning.
public class TurnController : MonoBehaviour
{
    /// CONTROL VARIABLES
    public int initialTurns;  // Initial number of turns overall.
    private int turnsLeft;  // Number of turns remaining in the game.

    public int followersMovesPerTurn;  // Number of moves per follower turn.
    public int leadersMovesPerTurn;  // Number of moves per leader turn.

    public bool myTurn;  // Whether it's the player's turn right now.
    private bool gameNotOver;  // Whether the game has finished.
    public static bool isFirstTurn = true;  // Whether it's the first turn.
    public string character;  // The player's character.

    private int movesRemaining;  // The number of moves remaining.
    private int prevMoveTime;  // The time that the previous move was taken.
    public int movesInThisCommand = 0;  // The number of moves that have been used
                                        // To follow this command (TODO: should be
                                        // moved to the command handling code)

    /// UI VARIABLES
    // Number of moves and turns remaining
    public Text moveDisplay;
    public Text totalTurnsDisplay;

    // Buttons for ending the turn and finishing commands
    public Button endTurnButton;
    public Button finishCommandButton;

    // Banners
    public GameObject skipTurnBanner;
    public GameObject finishCommandBanner;

    // Background color that indicates whether it is your turn
    public GameObject background;
    private Image backgroundImage;
    private readonly Color gamePink = new Color(0.80F, 0.66F, 0.65F, 1F);
    private readonly Color gameGreen = new Color(0.10F, 0.96F, 0F, 1F);

    /// OTHER SCRIPTS
    public CommandCommunication commandCommunication;
    private WebSocketManager webSocketManager;
    private InstructionControl instructionControl;
    private TimeKeeper timeKeeper;
    private CommandCenterSetup commandCenterSetup;

    /// ACTION HANDLERS
    public ExternalActionHandler myHandler;
    private ExternalActionHandler theirHandler;

    // Game-over handlers; two versions: one where the game finished normally,
    // the other where one partner quit.
    public delegate void GameOverHandler();
    public static event GameOverHandler GameOverEvent;

    public delegate void GameOverPartnerQuitHandler();
    public static event GameOverPartnerQuitHandler GameOverQuitEvent;

    #region Unity Event Functions
    void Awake()
    {
        timeKeeper = FindObjectOfType<TimeKeeper>();
    }

    void OnEnable()
    {
        webSocketManager = GetComponent<WebSocketManager>();

        backgroundImage = background.GetComponent<Image>();
        commandCenterSetup = FindObjectOfType<CommandCenterSetup>();

        CommandCenterSetup.OnMovementSetupEvent += SetUpTurns;
    }

    void OnDisable()
    {
      CommandCenterSetup.OnMovementSetupEvent -= SetUpTurns;
    }

    void Update()
    {
        if (turnsLeft <= 0 && gameNotOver) { InvokeGameOverEvent(false); }

        // Compute the time since the last move.
        if (character == "Agent" && myTurn && !finishCommandBanner.activeSelf) {
            DateTime now = System.DateTime.Now;
            int nowSec = now.Hour * 3600 + now.Minute * 60 + now.Second;
            int timeSinceLastMove = nowSec - prevMoveTime;

            // Make the finish command banner active if it's been 15s since
            // the last action.
            if (timeSinceLastMove > 15 && !TutorialGuide.tutorialMode) { 
                finishCommandBanner.SetActive(true);
            }
        }
        
        InputUpdate();
    }
    #endregion

    public void AddMovesOnSet(int score)
    {
      if (score == 1) {
        turnsLeft += 10;
      } else if (score == 2 || score == 3) { 
        turnsLeft += 8;
      } else if (score == 4 || score == 5) {
        turnsLeft += 6;
      } else if (score == 6 || score == 7) {
        turnsLeft += 4;
      } else if (score >= 8 && score <= 10) {
        turnsLeft += 2;
      }

      // If turns were added, update th e text and change the color to blue.
      if (score >= 1 && score <= 13) {
        totalTurnsDisplay.text = "Turns Left: " + (turnsLeft+1)/2;
        totalTurnsDisplay.color = Color.blue;
      }

      // Commented out because we are not using the kind of decay anymore.
//      if (extraTurnsLeft > 0)
//      {
//        turnsLeft += extraTurnsLeft;
//        extraTurnsLeft -= decaySpeed;
//        // (turnsLeft+1)/2 to show half the num turns left correctly w/ int division
//      }
    }

    public void SetPrevMoveTime() {
        DateTime now = System.DateTime.Now;
        prevMoveTime = now.Hour * 3600 + now.Minute * 60 + now.Second;
    }


    /*
      Configure UI elements for turns, get externalHandlers for characters,
    */
    public void SetUpTurns()
    {
        turnsLeft = initialTurns;
        //extraTurnsLeft = extraTurns;
        gameNotOver = true;
        instructionControl = FindObjectOfType<InstructionControl>();
        timeKeeper = FindObjectOfType<TimeKeeper>();


        var them = GameObject.FindGameObjectWithTag(character=="Human"?"Agent":"Human");
        if (them)
            theirHandler = them.GetComponent<ExternalActionHandler>();
        var me = GameObject.FindGameObjectWithTag(character);
        if (me)
            myHandler = me.GetComponent<ExternalActionHandler>();
        if (character=="Human")
        {
          movesRemaining = leadersMovesPerTurn;
          myTurn = true;
          moveDisplay.text = "Moves Left: "+leadersMovesPerTurn+" Moves Left in Turn";
          
          // Initially the end-turn button should be disabled so the leader must
          // put in a command during their turn.
          endTurnButton.interactable = false;
          #if UNITY_WEBGL
          if(!TutorialGuide.tutorialMode)
          {
          backgroundImage.material.SetColor("_Color", gameGreen);
          backgroundImage.material.SetColor("_Color2", gameGreen);
          }
          #endif
        }
        else //character=="Agent"
        {
          movesRemaining = followersMovesPerTurn;
          myTurn = false;
          moveDisplay.text = "Moves Left: Waiting for partner!";
          if(!TutorialGuide.tutorialMode)
          {
          backgroundImage.material.SetColor("_Color", gamePink);
          backgroundImage.material.SetColor("_Color2", gamePink);
          }
        }
        // (turnsLeft+1)/2 to show half the num turns left correctly w/ int division
        totalTurnsDisplay.text = "Turns Left: " + (turnsLeft+1)/2;
        if(TutorialGuide.tutorialMode) { theirHandler.GiveTurn(); GetTurn(); } // Fix movement for tutorial role.
    }

    #if UNITY_WEBGL
    // TODO: don't need to pass the land type here
    public void Movement(string movingCharacter, LandType landType)
    {

      if (movingCharacter == character || TutorialGuide.tutorialMode)
      {
        movesRemaining -= 1;

        // Display the finish command banner if they've moved more than 15 steps
        // in this command (1.5 turns)
        movesInThisCommand += 1;
        if (character == "Agent" && movesInThisCommand >= 15 && !TutorialGuide.tutorialMode) {
            finishCommandBanner.SetActive(true);
        }

        // Reset the time when the last move happened.
        SetPrevMoveTime();
        moveDisplay.text = "Moves Left: "+movesRemaining+" Moves Left in Turn";
        if (movesRemaining <= 0) { NoMoves(); }
      }
    }

    public void NoMoves()
    {
      myHandler.NoMoves();
    }
    #endif

    #if UNITY_STANDALONE
    public void Movement(string movingCharacter, LandType landType)
    {
      movesRemaining -= 1;
      moveDisplay.text = "Moves Left: "+movesRemaining+" Moves Left in Turn";
      if (movesRemaining <= 0) { NoMoves(movingCharacter); }
    }

    public void NoMoves(string movingCharacter)
    {
        if (movingCharacter == "Human") { myHandler.NoMoves(); }
        else { theirHandler.NoMoves(); }
    }
    #endif

    #if UNITY_WEBGL
    public void GiveTurn(string method)
    {
        if(!TutorialGuide.tutorialMode)
        {
            Dictionary<string, string> strData = new Dictionary<string, string>()
            {
                {"character", character},
                {"method", method}
            };
            webSocketManager.Send("yourTurn", strData, null);
            movesRemaining = character=="Human"?leadersMovesPerTurn : followersMovesPerTurn;
            moveDisplay.text = "Moves: Waiting for partner!";

            turnsLeft -= 1;
            totalTurnsDisplay.text = "Turns Left: " + (turnsLeft+1)/2; // Shows each player's usable turns
            totalTurnsDisplay.color = Color.black;

            if (character=="Human")
            {
                instructionControl.TurnOff();
                endTurnButton.interactable = false;
            } else {
                // Make the finish command button non-interactable.
                finishCommandButton.interactable = false;
            }


            myTurn=false;
            myHandler.GiveTurn();
            backgroundImage.material.SetColor("_Color", gamePink);
            backgroundImage.material.SetColor("_Color2", gamePink);
            timeKeeper.ResetTime(character=="Human"?"Agent":"Human");
            if(isFirstTurn) { isFirstTurn = false; }
        }
        else
        {
        	if(character == "Agent")
        	{
          		movesRemaining = followersMovesPerTurn;
          		timeKeeper.ResetTime("Agent");
        	}
        	else { timeKeeper.ResetTime("Human"); }
        }
    }
    #endif

    #if UNITY_STANDALONE
    public void GiveTurn(string method)
    {
        turnsLeft -= 1;
        // (turnsLeft+1)/2 to show half the num turns left correctly w/ int division
        totalTurnsDisplay.text = "Turns Left: " + (turnsLeft+1)/2;
        totalTurnsDisplay.color = Color.black;
        if (!commandCenterSetup)
          commandCenterSetup = FindObjectOfType<CommandCenterSetup>();
        if (turnsLeft%2 == 0) //just switched to human's turn
        {
          theirHandler.GiveTurn();
          myHandler.GetTurn();
          movesRemaining = leadersMovesPerTurn;
          instructionControl.TurnOn();
          backgroundImage.material.SetColor("_Color", gameGreen);
          backgroundImage.material.SetColor("_Color2", gameGreen);
          timeKeeper.ResetTime("Human");
          // commandCenterSetup.ToggleLeaderFollowerView("Human");
        }
        else { //just switched to agent's turn
          myHandler.GiveTurn();
          theirHandler.GetTurn();
          movesRemaining = followersMovesPerTurn;
          instructionControl.TurnOff();
          timeKeeper.ResetTime("Agent");
          backgroundImage.material.SetColor("_Color", gamePink);
          backgroundImage.material.SetColor("_Color2", gamePink);
          // commandCenterSetup.ToggleLeaderFollowerView("Agent");
          instructionControl.DisplayTurnGraphic();
        }
        moveDisplay.text = "Moves: "+movesRemaining+" Moves Left in Turn";
        if(isFirstTurn) { isFirstTurn = false; }
    }
    #endif

    public void GetTurn()
    {
      timeKeeper.ResetTime(character);

      // Reset the timer since the last move.
      SetPrevMoveTime();
      moveDisplay.text = "Moves: "+movesRemaining+" Moves Left in Turn";

      turnsLeft -= 1;
      // (turnsLeft+1)/2 to show half the num turns left correctly w/ int division
      totalTurnsDisplay.text = "Turns Left: " + (turnsLeft+1)/2;
      totalTurnsDisplay.color = Color.black;

      if (character=="Human") { 
          instructionControl.TurnOn();

          // Keep end turn buttoned disabled if the follower has followed all
          // commands.
          if (!commandCommunication.CompletedAllCommands()) {
              endTurnButton.interactable = true;
          }
      } else {
          if (commandCommunication.CompletedAllCommands() && !TutorialGuide.tutorialMode) {
              skipTurnBanner.SetActive(true);

              // Also give the turn up, and don't do the rest of the things.
              GiveTurn("No Commands to Follow");
              return;
          } else {
              skipTurnBanner.SetActive(false);

              // Don't allow the tutorial to finish the command immediately.
              if (!TutorialGuide.tutorialMode) {
                  finishCommandButton.interactable = true;
              }
          }
      }

      myTurn=true;
      myHandler.GetTurn();
      #if UNITY_WEBGL
      if(!TutorialGuide.tutorialMode)
      {
            backgroundImage.material.SetColor("_Color", gameGreen);
            backgroundImage.material.SetColor("_Color2", gameGreen);
      }
      #endif
      instructionControl.DisplayTurnGraphic();
    }

    public void InputUpdate()
    {
        #if !SIMULATING
        if (myTurn) {
            if (character == "Human" && Input.GetKeyDown(KeyCode.Tab)) {
                GiveTurn("Pressed Tab to End Turn");
            } else if (character == "Agent" && movesRemaining == 0) {
                GiveTurn("Ran Out of Moves");
            }
        }
        #endif
    }

    public void InvokeGameOverEvent(bool playerQuit)
    {
        # if !SIMULATING
        if (gameNotOver) {
            if (playerQuit) {
                GameOverQuitEvent();
            } else {
                GameOverEvent();
            }
            gameNotOver = false;
        }
        #endif
    }

    public bool CanMove(LandType landType)
    {
      // TODO: don't need to pass the land type here
	  #if SIMULATING
      return true;
	  #endif

	  #if !SIMULATING
      return movesRemaining - 1 >= 0;
	  #endif

    }
}
