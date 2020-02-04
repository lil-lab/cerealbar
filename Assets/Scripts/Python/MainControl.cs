using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using System.IO;
using UnityEngine.SceneManagement;

/// <summary>
/// Main control for connecting main unity thread to the socket thread
/// Handles ALL the things that the server wants done in client, that means all the scripts that handle anything will probably be referenced in here eventually
/// </summary>
public class MainControl : MonoBehaviour
{

	public bool updating_cards = false;
	public Queue<string> myCommands = new Queue<string>();
    private SocketStarter socketStarter;
    private InformationGetter infoGetter;
    private CommandCommunication commandCommunication;
    //private HexGrid hexgrid;
    private bool isProcessingInstruction = false;
	
    private bool waitingForActionCompletion = false;
    private byte[] pic;

    private ExternalActionHandler humanHandler;
    private ExternalActionHandler agentHandler;
    private TurnController turnController;
    private Startup startup;
    private PropPlacement propPlacement;

    void OnEnable()
    {
        infoGetter = FindObjectOfType<InformationGetter>();
       // hexgrid = FindObjectOfType<HexGrid>();
        turnController = FindObjectOfType<TurnController>();
        commandCommunication = FindObjectOfType<CommandCommunication>();
        propPlacement = FindObjectOfType<PropPlacement>();
        startup = FindObjectOfType<Startup>();

        InformationGetter.OnImageTakenEvent += GetSendImage;
        PropPlacement.OnMapCompleteEvent += SendMapCompleteMsg;
        PropPlacement.OnMapCompleteEvent += GetHandlers;

        HexQueuedCntrl.OnFinishedHexActionEvent += SendAgentInfo;
        QueuedControl.OnFinishedActionEvent += SendAgentInfo;
    }

    void OnDisable()
    {
        InformationGetter.OnImageTakenEvent -= GetSendImage;
        PropPlacement.OnMapCompleteEvent -= SendMapCompleteMsg;
        PropPlacement.OnMapCompleteEvent -= GetHandlers;

        HexQueuedCntrl.OnFinishedHexActionEvent -= SendAgentInfo;
        QueuedControl.OnFinishedActionEvent -= SendAgentInfo;
    }

    void Start()
    {
        try
        {
            socketStarter = FindObjectOfType<SocketStarter>();
        }
        catch
        {
            this.enabled = false;
        }
    }

    /// <summary>
    /// ** Called in Update **
    ///  This is how we bring the messages from socket back to the main thread to execute any other functions
    ///  checks if we are executing anything and if there are any requests to fulfill
    /// </summary>
    private void CheckRequests()
    {
		
		if (socketStarter.rcvdRequests.Count > 0 ){
			string msg = socketStarter.rcvdRequests.Dequeue();
			myCommands.Enqueue(msg);
			string tmp_msg = msg.Trim();

		if (tmp_msg =="agent" || tmp_msg == "human" || tmp_msg=="start"  || tmp_msg=="grammer" || tmp_msg=="state" || tmp_msg=="goaldist" || tmp_msg=="trajdist" || tmp_msg=="obsdist" || tmp_msg=="avoiddist"){
                msg = socketStarter.rcvdRequests.Dequeue();
				myCommands.Enqueue(msg);
			
			}
			
		}
		
		
        if (!isProcessingInstruction && myCommands.Count > 0 && !updating_cards)
        {
            isProcessingInstruction = true;
			
            StartCoroutine(ProcessMsgRequest(myCommands.Dequeue()));
			
        }
    }

    /// <summary>
    /// Processes the request in queue
    /// start, seed
    /// restart,seed
    ///
    /// start information: See GetMapInfo in InformationGetter Script to view all the types and information sent
    /// <bodytocontrol>,<move>
    /// status human
    /// status agent
    ///
    /// image overhead: sends a byte array of the image taken from the overhead camera
    /// image human: sends a byte array of the image taken for the human camera
    /// image agent: sends a byte array of the image taken for the agent camera
    /// </summary>
    /// <param name="msg"></param>
    private IEnumerator ProcessMsgRequest(string msg)
    {
        msg = msg.Trim();
        //TODO make it wait until the processing flag is false
        Debug.Log("Message: " + msg);

        switch (msg)
        {
			case "grammer":
			
				InstructionControl instructionControl = FindObjectOfType<InstructionControl>();
                var command = myCommands.Dequeue();

                instructionControl.DisplayInstruction(command);
				yield return null;
			
				socketStarter.CerealSendMsg("123");
                break;

            case "state":
                var stateJson = myCommands.Dequeue();

                var setState = startup.SetState(stateJson);

                if (!setState) {
                    socketStarter.CerealSendMsg("Failed - game not started");
                }
				socketStarter.CerealSendMsg("");
                break;

            case "goaldist":
                var goalJson = myCommands.Dequeue();
                propPlacement.SetGoalDist(goalJson);
                socketStarter.CerealSendMsg("");
                break;
            case "trajdist":
                var trajJson = myCommands.Dequeue();
                propPlacement.SetTrajectoryDist(trajJson);
                socketStarter.CerealSendMsg("");
                break;
            case "obsdist":
                var obsJson = myCommands.Dequeue();
                propPlacement.SetObstacleDist(obsJson);
                socketStarter.CerealSendMsg("");
                break;
            case "avoiddist":
                var avoidJson = myCommands.Dequeue();
                propPlacement.SetAvoidDist(avoidJson);
                socketStarter.CerealSendMsg("");
                break;

            case "newcards":
                var cardsJson = myCommands.Dequeue();
                propPlacement.AddCards(JsonUtility.FromJson<CardLists>(cardsJson));
                socketStarter.CerealSendMsg("");

                break;
			
            case "start":
                // dequeue get seed number;
				
				var splitM = myCommands.Dequeue().Split(',');			
                // splitM is in the format "seed/numcards"
                var seed = 0;

                var parsed = int.TryParse( splitM[0].Trim(), out seed);

                var numCards = 0;
                var numCardsParsed = int.TryParse(splitM[1].Trim(), out numCards);

                // Now get the number of cards
                if(!parsed || !numCardsParsed)
                {
                    socketStarter.CerealSendMsg("Failed - expected integer for map seed start");
                }
                else
                {
                    var result = startup.StandaloneStartWithSeed(seed, numCards);

                    if (result)
                    {
                    }
                    else
                    {
                        socketStarter.CerealSendMsg("Failed - game already started");
                    }
                    //send start information - need to wait for the proplacement event
                }
                //set the map seed
                // UI start map

                break;
            case "restart":
               
				
					//Resources.UnloadUnusedAssets();
					string sss =SceneManager.GetActiveScene().name ; 
					SceneManager.LoadScene("Game");
				
					
			
             
                break;
            case "info":
                yield return null;
				
				
                var info = infoGetter.GetStateDelta();
                socketStarter.CerealSendMsg(info);
                break;
			case "score":
					ScoreKeeper scoreKeeper = FindObjectOfType<ScoreKeeper>();
					int tmpScore = scoreKeeper.score;
					socketStarter.CerealSendMsg(tmpScore.ToString());
					
                break;
            case "finishcommand":
                if (commandCommunication == null) {
                    commandCommunication = FindObjectOfType<CommandCommunication>();
                }
                commandCommunication.ReplayFinishCommand();
                socketStarter.CerealSendMsg("");
                break;
            case "turn":
                turnController.GiveTurn("Switched From Python");
                socketStarter.CerealSendMsg("");
                break;
            case "agent":
                Debug.Log("Agent is moving");
				splitM = myCommands.Dequeue().Split(',');
			
               
                var movement = splitM[0].Trim();
                var ret = MovementHandler(agentHandler, movement);
				
                info = infoGetter.GetStateDelta();
                socketStarter.CerealSendMsg(info);
                break;
            case "human":
                Debug.Log("Human is moving");
			
				
				splitM = myCommands.Dequeue().Split(',');
                movement = splitM[0].Trim();
                ret = MovementHandler(humanHandler, movement);
				
                info = infoGetter.GetStateDelta();
                socketStarter.CerealSendMsg(info);
                break;

            case "image overhead":
                pic = infoGetter.GetScreenShotImageView("overhead");

                socketStarter.CerealSendMsg(pic);
                break;
            case "image human":
                waitingForActionCompletion = true;
                StartCoroutine(infoGetter.GetPOVImg("human"));
                break;
            case "image agent":
                waitingForActionCompletion = true;
                StartCoroutine(infoGetter.GetPOVImg("agent"));
                break;

            case "status agent":
		
                socketStarter.CerealSendMsg(infoGetter.GetAgentMoveInfo("Agent"));
                break;

            case "status human":
			
                socketStarter.CerealSendMsg(infoGetter.GetAgentMoveInfo("Human"));
                break;

            case "quit":
            case "exit":
                socketStarter.CloseConnection();
                Application.Quit();
                break;

            default:
                socketStarter.CerealSendMsg("");
                break;
        }
        yield return null;
        isProcessingInstruction = false;
		yield return null;
        yield break;
    }
	

IEnumerator UnLoadYourAsyncScene(string sss)
    {
		
       
		
        //AsyncOperation asyncLoad = SceneManager.UnloadSceneAsync(sss);
AsyncOperation asyncLoad = SceneManager.LoadSceneAsync(sss);
        // Wait until the asynchronous scene fully loads
        while (!asyncLoad.isDone)
        {
            yield return null;
        }
		
		
		//SceneManager.LoadSceneAsync(sss);
		
    }


    private void GetHandlers()
    {
        var ag = GameObject.FindGameObjectWithTag("Agent");
        if(ag)
            agentHandler = ag.GetComponent<ExternalActionHandler>();

        var hum = GameObject.FindGameObjectWithTag("Human");
        if (hum)
            humanHandler = hum.GetComponent<ExternalActionHandler>();

    }

    private string MovementHandler(ExternalActionHandler actionHandler, string action)
    {
        string ret = "";
        switch (action)
        {
            case "RR":
                ret = actionHandler.AddAction(ActionInformation.AgentState.Turning, 1);
                break;
            case "RL":
                ret = actionHandler.AddAction(ActionInformation.AgentState.Turning, -1);
                break;
            case "MF":
                ret = actionHandler.AddAction(ActionInformation.AgentState.Walking, 1);
                break;
            case "MB":
                ret = actionHandler.AddAction(ActionInformation.AgentState.Walking, -1);
                break;

            //Note that "stop" currently only works for queued movements
            case "stop":
                agentHandler.StopClearAll();
                break;
        }
        return ret;
    }

    #region SocketMessages
    //Don't need to set waiting flags bc the movements are queued?
    private void SendAgentInfo(string tag)
    {

        socketStarter.CerealSendMsg(infoGetter.GetAgentMoveInfo(tag));
        //maybe add flags to indicate which agent is done?
    }

    private void GetSendImage()
    {
        pic = infoGetter.tempPic;
        infoGetter.tempPic = null;
        socketStarter.CerealSendMsg(pic);
        waitingForActionCompletion = false;
        isProcessingInstruction = false;
    }

    public void SendMapCompleteMsg()
    {
        var starterInfo = infoGetter.GetMapInfo();
        socketStarter.CerealSendMsg(starterInfo);
        isProcessingInstruction = false;
        waitingForActionCompletion = false;
    }
    #endregion

    // Update is called once per frame
    void Update ()
    {
        CheckRequests();
	  }
}
