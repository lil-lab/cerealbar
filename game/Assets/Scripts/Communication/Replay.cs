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
public class Replay : MonoBehaviour {

    // private TimeKeeper tk;
    // private HexGrid hexgrid;
    // private ScoreKeeper score;
    // private InformationGetter infoGetter;
    private WebSocketManager webSocketManager;
    public Startup starterControl;
    public InstructionControl instrControl;

    // private GameObject start;
    public InputField databaseField;
    public InputField gameIDField;
    public Slider slider;
    public GameObject dataPanel;
    public Text pausePlayText;
    private ExternalActionHandler agentHandler;
    private ExternalActionHandler humanHandler;
    private ExternalActionHandler handler;

    public static bool replaying = false;
    public static bool running = false;
    private bool simPaused = false;
    public static List<string[]> instrList;
    public static List<string[]> moveList;
    //public static IOrderedEnumerable<string[]> moveList;
    public static int mLi = 0;

    private IEnumerator InvokeReplayGame;

    void OnEnable()
    {
        // tk = FindObjectOfType<TimeKeeper>();
        // hexgrid = FindObjectOfType<HexGrid>();
        // score = FindObjectOfType<ScoreKeeper>();
        // infoGetter = FindObjectOfType<InformationGetter>();
        webSocketManager = FindObjectOfType<WebSocketManager>();
        // start = GameObject.Find("Start");

        PropPlacement.OnMapCompleteEvent += GetHandlers;
    }

    void OnDisable()
    {
        PropPlacement.OnMapCompleteEvent -= GetHandlers;
        if(replaying) { PropPlacement.OnMapCompleteEvent -= ExecuteReplay; }
    }

    // Queries a given database for data simulation.
    public void QueryGameData()
    {
        string dbFile = databaseField.text;
        string gameId = gameIDField.text;
        Dictionary<string, string> gameData = new Dictionary<string, string>()
        {
            {"database", dbFile},
            {"gameID", gameId}
        };
        webSocketManager.Send("queryData", gameData, null);
    }


    // Start data simulation.
    private void StartReplay(string seed)
    {
        replaying = true;
        starterControl.SetSeed(seed);
        starterControl.SetCharacter("Human");
        dataPanel.SetActive(true);
    }

    // Reads in list of instructions for data simulation and stores it in instructionList.
    private void ReplayInstructions(string instructions)
    {
        instrList = new List<string[]>();
    	string[] buf = instructions.Split('|');
    	for(int i = 0; i < buf.Length; i += 1)
    		instrList.Add(buf[i].Split(','));
    }

    // Initialize list of moves to replay.
    private void ReplayMoves(string moves)
    {
        // List<string[]> bufList = new List<string[]>();

        string[] buf = moves.Split('|');
        moveList = new List<String[]>();
        for(int i = 0; i < buf.Length; i += 1)
            moveList.Add(buf[i].Split(','));

        PropPlacement.OnMapCompleteEvent += ExecuteReplay;
        starterControl.StartGame();
        webSocketManager.StartGamePlay();
        // start.GetComponent<Renderer>().enabled = false;
    }

    // Simulation function.
    // Originally called from the Replay() function and had constant intervals, but these were removed.
    private void ExecuteReplay()
    {
        InvokeReplayGame = ReplayGame();
        StartCoroutine(InvokeReplayGame);
    }

    private IEnumerator ReplayGame()
    {
        yield return new WaitForSeconds(5);
        int lastTurn;
        int.TryParse(moveList[moveList.Count-1][4], out lastTurn);
        string character = "";

        // Each iteration queues all the movements for that turn, then dequeues
        // one at a time so that watching a replay you see the moves one turn
        // at a time.
        for (int turn = 0; turn <= lastTurn; turn++)
        {
            foreach (string[] move in moveList)
            {
              if (move[4] == turn.ToString())
              {
                Tuple<string, string> moveArg = Tuple.Create(move[1], move[2]);
                character = move[1];
                QueueMovement(moveArg);

                // Check if any instructions exist to display.
                if(instrList.Any() && Int32.Parse(instrList[0][0]) == -1)
                {
                    instrControl.DisplayInstruction(instrList[0][1]);
              		instrList.RemoveAt(0);
                }
                while(instrList.Any() && instrList[0][0] == move[0])
                {
                    instrControl.DisplayInstruction(instrList[0][1]);
              		instrList.RemoveAt(0);
                }
              }
            }
            DequeueMovements(character);
            yield return new WaitWhile(() => running == true); // Waits while movements are dequeueing.
            yield return new WaitForSeconds(3);
        }
        instrControl.DisplayInstruction("*********** REPLAY: END OF GAME ***********");
        yield break;
    }

    /*  Outdated replay function. Runs by constant time intervals.
        // Calculate initial time.
    	int prevTime;
        if(!Int32.TryParse(bufList[0][3], out prevTime))
            yield return null;

        // Iterate through list of moves by moveId.
        foreach(var move in bufList.OrderBy(move => move[0], new SemiNumericComparer()))
        {
        	// Displays instructions if move ID matches.
        	while(instructionList.Any() && instructionList.First()[0] == move[0])
        	{
        		instrControl.DisplayInstruction(instructionList.First()[1]);
        		instructionList.RemoveAt(0);
        	}

        	int newTime;
        	if(!Int32.TryParse(move[3], out newTime))
        		continue;
            int elapsed = newTime - prevTime;
            prevTime = newTime;

            Tuple<string, string, int> moveArg = Tuple.Create(move[1], move[2], elapsed);
            CallMovement(moveArg);
        }
        humanHandler.DoExternalActions();
        agentHandler.DoExternalActions();
    }
    */

    // Calls the correct movement on the given agent.
    private void QueueMovement(Tuple<string, string> moveArg)
    {

    	if(moveArg.Item1 == "Human") { handler = humanHandler; }
    	else if(moveArg.Item1 == "Agent") { handler = agentHandler; }
    	else return;

        switch(moveArg.Item2)
        {
        	case "RR":
        		handler.AddExternalAction(ActionInformation.AgentState.Turning, 1);
        		break;
        	case "RL":
        		handler.AddExternalAction(ActionInformation.AgentState.Turning, -1);
        		break;
        	case "MF":
        		handler.AddExternalAction(ActionInformation.AgentState.Walking, 1);
        		break;
        	case "MB":
        		handler.AddExternalAction(ActionInformation.AgentState.Walking, -1);
        		break;
        	default:
        		break;
        }
    }

    private void DequeueMovements(string character)
    {
      if(character == "Human")      { handler = humanHandler; }
      else if(character == "Agent") { handler = agentHandler; }
      else                          { return; }
      handler.DoExternalActions();
    }

    // Used to order the move list by move ID.
    public class SemiNumericComparer: IComparer<string>
    {
    	public int Compare(string s1, string s2)
    	{
    		int x, y;
    		bool res1 = Int32.TryParse(s1, out x);
    		bool res2 = Int32.TryParse(s2, out y);

    		if(res1)
    		{
    			if(res2)
    			{
    				if (x > y) return 1;
    				else if (x < y) return -1;
    				else return 0;
    			}
    			else return -1;
    		}
    		else if(res2) return 1;
    		else return string.Compare(s1, s2, true);
    	}
    }

    private void GetHandlers()
    {
        if(replaying) {
            var ag = GameObject.FindGameObjectWithTag("Agent");
            if(ag)
                agentHandler = ag.GetComponent<ExternalActionHandler>();

            var hum = GameObject.FindGameObjectWithTag("Human");
            if (hum)
                humanHandler = hum.GetComponent<ExternalActionHandler>();
        }
    }

    public void PausePlay()
    {
        if(simPaused)
        {
            simPaused = false;
            pausePlayText.text = "Pause";
        }
        else
        {
            simPaused = true;
            pausePlayText.text = "Play";
        }
    }

    public void UpdateSlider()
    {
        if(simPaused)
        {
            Debug.Log("Changed value!");
        }
        else { Debug.Log("Do not adjust slider until you have paused the replay!"); }
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

    private string Show(string[] a)
    {
      string ret ="[";
      foreach (string s in a)
      {
        ret += a + ",";
      }
      return ret + "]";
    }

    public void TestReplay()
    {
        replaying = true;
        starterControl.SetSeed(0.ToString());
        starterControl.SetCharacter("Human");
        dataPanel.SetActive(true);
        instrList = new List<string[]>();
        instrList.Add(new string[] {"1", "Hello"});
        instrList.Add(new string[] {"3", "Test"});
        moveList = new List<string[]>();
        moveList.Add(new string[] {"1", "Human", "RR", "0", "1"});
        moveList.Add(new string[] {"2", "Human", "MF", "0", "1"});
        moveList.Add(new string[] {"3", "Agent", "MB", "0", "2"});
        moveList.Add(new string[] {"4", "Agent", "RL", "0", "2"});

        PropPlacement.OnMapCompleteEvent += ExecuteReplay;
        starterControl.StartGame();
        webSocketManager.StartGamePlay();
        //start.GetComponent<Renderer>().enabled = false;
    }
}
