using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System;
using UnityEngine;
using UnityEngine.UI;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using System.IO;
using UnityEngine.Networking;


public class TutorialGuide : MonoBehaviour {
    [DllImport("__Internal")]  
    private static extern string CompleteTutorial(bool isLeader);

    private GameObject msgBanner;
    private Text msg;
    private GameObject note;
    private GameObject panel;

    private GameObject endOfTutorialBanner;
    private Text endOfTutorialMsg;

	public InputField cmdPrompt;
    public InputField cmdHistory;
	public Button btn;
    public Button finishCommandButton;
    public InputField followerCmdHistory;

    public HexToHexControl leaderHexCtrl;
	public Text timeDisplay;
	public Text moveDisplay;
	public Text turnDisplay;

    private SetGame setGame;
    private ScoreKeeper scoreKeeper;
    private InstructionControl instrucCtrl;

    public static bool tutorialMode = false;
    public static string role;
    private int step = 1;
    private bool complete = true;
    private bool done = false;
    private bool findingSets = false;
    private const string dashes = "---------------------------------------------------------------";

    public Material card_black;
    public Material card_blue;

    private void Awake() {
    }

    void Start() {
    }


    void OnEnable()
    {
  		tutorialMode = true;
  		msgBanner = GameObject.Find("MsgBanner");
  		msg = msgBanner.transform.Find("Msg").gameObject.GetComponent<Text>();
  		note = msgBanner.transform.Find("Note").gameObject;
        panel = msgBanner.transform.Find("Panel").gameObject;

        GameObject gameManager = GameObject.Find("GameManager");
        setGame = gameManager.GetComponent<SetGame>();
  		scoreKeeper = gameManager.GetComponent<ScoreKeeper>();
  		GameObject instructions = GameObject.Find("Instructions");
  		instrucCtrl = instructions.GetComponent<InstructionControl>();
  		GameObject human = GameObject.FindGameObjectWithTag("Human");
  		leaderHexCtrl = human.GetComponent<HexToHexControl>();


  		if(role == "Human")
        {
            msg.text = "Welcome to the <b>Leader Tutorial</b>! Complete all steps to get started playing the game!";
        }
  		else if(role == "Agent")
        {
            msg.text = "Welcome to the <b>Follower Tutorial</b>! Complete all steps to get started playing the game!";
        }
    }

    void Update()
    {
        if(tutorialMode && (Input.GetKeyDown(KeyCode.RightShift) || Input.GetKeyDown(KeyCode.LeftShift)))
        {
            if ((role == "Agent" && !findingSets) || role == "Human") {
                MsgUpdate();
            }
            if (role == "Agent" && findingSets && done)
            {
                MsgUpdate();
            }
        } 
        if(!complete && !done)
        {
            CheckComplete(step);
        }
    	if(step == 1 || step == 2)
        {
    	    leaderHexCtrl.canMove = false;
    	}

        if (role == "Agent" && step >= 10) {
            if (!done)
            {
                note.SetActive(false);
                msg.text = "Are you sure you have followed the commands correctly? If yes, your score should be 1 now. If not, scroll the box to read the commands again and try to get a point.";
                findingSets = true;
                complete = false;
            } 
        }
    }

    void DisplayFollowerCommand(string s)
    {
        string followerHistory = followerCmdHistory.text;
        followerHistory = followerCmdHistory.text.Replace("--- [CURRENT]", "--- [DONE]");
        followerCmdHistory.text = followerHistory + "--- [CURRENT] " + s + " \n";
    }

    private void MsgUpdate()
    {
        if(!complete && !done)
        {
            if ((role == "Human" && findingSets) || role == "Agent") {
                msgBanner.SetActive(false);
            }
            if (role == "Agent" && findingSets) {
                msgBanner.SetActive(true);
            }
            return;
        }
        ResetStep();

        if(role == "Human")
        {
        	switch(step)
        	{
            	case 1:
                    note.SetActive(false);
                    msg.text = "You are playing as the <b>Leader</b> (<i>yellow arrow</i>). As the Leader, you can see the entire map! Toggle your map view by clicking the <b>'Camera'</b> button below.";
                    btn.onClick.AddListener(BtnTask);
    				break;
            	case 2:
                    note.SetActive(true);
                    msg.text = "At the bottom of the screen, there is the <b>Time Left</b> display. During the game, you are given <i>60 seconds</i> per turn as the leader.";
                    btn.onClick.RemoveListener(BtnTask);
                    timeDisplay.color = Color.green;
                    CompleteStep();
                    break;
		       case 3:
					msg.text = "Below the time, the game shows you the number of <b>moves</b> left in the turn, and the number of turns left before game over. <i>Use them wisely</i> in the game!";
					timeDisplay.color = Color.black;
					moveDisplay.color = Color.green;
					turnDisplay.color = Color.green;
					CompleteStep();
					break;
      			case 4:
                    note.SetActive(false);
  					msg.text = "Toggle the <b>'Camera'</b> button again to return to the original view!";
  					moveDisplay.color = Color.black;
  					turnDisplay.color = Color.black;
  					btn.onClick.AddListener(BtnTask);
  					break;
      			case 5:
  					msg.text = "The <i>purple arrow</i> is pointing to the <b>Follower</b>. You can send the follower commands in the <b>'Send Commands'</b> box and click <b>'SEND'</b> to send. Try it now!";
  					btn.onClick.RemoveListener(BtnTask);
  					cmdHistory.onValueChanged.AddListener(delegate {SubmitCmdComplete(); });
  					break;
      			case 6:
                    note.SetActive(true);
                    msg.text = "For now, the Follower won't do anything, but in the game, once you end your turn, the Follower will see your instruction and get a chance to move.";
  					cmdPrompt.DeactivateInputField();
  					CompleteStep();
  					break;
      			case 7:
                    note.SetActive(false);
                    msg.text = "To move the Leader, use the <b>arrow keys</b>! Walk to the <i>three black squares</i> card near the round yellow tree near the right edge and pick it up.";
  					btn.onClick.RemoveListener(BtnTask);
  					leaderHexCtrl.canMove = true;
  					TurnController.isFirstTurn = false;
  					break;
  				case 8:
  					msg.text = "Good job! The goal is to collect as many <b>sets of 3 cards</b> as possible before you run out of turns. Try picking up the <i>three blue stripes</i> card in the front.";
  					break;
  				case 9:
                    note.SetActive(true);
  					msg.text = "Looks like we picked up a bad set! Each card in a set must have a <b>different</b> shape, color, and number of items. If you violate this rule, the cards will turn <b>red</b>!";
                    CompleteStep();
  					break;
  				case 10:
                    note.SetActive(false);
  					msg.text = "To <b>deselect</b> a card, <i>walk off and onto the card again</i>. Try it now!";
  					break;
  				case 11:
                    note.SetActive(false);
  					msg.text = "Now try collecting your <b>first set</b> by going to the 1 orange circle card and the 2 green stripes card! Once complete, the cards will flash <b>green</b> then disappear.";
  					break;
  				case 12:
                    note.SetActive(true);
  					msg.text = "<b>Good work</b>! Each set will give you more <b>turns</b> to collect even more sets. The <b>higher your score</b>, the <b>more credits</b> you will receive at the end of the game.";
                    CompleteStep();
  					break;
  				case 13:
  					msg.text = "Complete <b>2 more sets</b> to finish the tutorial. <b>Hint</b>: Toggle the camera view to find hidden cards and objects! Good luck!";
                    findingSets = true;
  					break;
                case 14:
                    msg.text = "Great work! Please remember you would have limited moves and turns in the real game.";
                    CompleteStep();
                    break;
				default:
                    CompleteTutorial(true);
                    note.SetActive(false);
                    Image image = panel.transform.GetComponent<Image>();
                    image.color = new Color32(255, 137, 80, 255);
                    done = true;
                    msg.text = "Congrats! We recorded your completion of the Leader Tutorial to the database. Please go back to HIT page to continue.";
                  	break;
        	}
        }
        else
        {
        	switch(step)
        	{
        		case 1:
        			msg.text = "You are playing as the <b>Follower</b>. Your job is to do <b>only</b> what the leader commands you to in the <b>Command History</b> window.";
        			CompleteStep();
        			break;
				case 2:
        			msg.text = "As the Follower, you can <i>only</i> see what is in front of your character, not like the leader's overhead view.";
        			CompleteStep();
        			break;
				case 3:
        			msg.text = "The <b>time</b>, number of <b>moves</b>, and <b>turns</b> are at the bottom of the screen. You have <i>30 seconds</i> per turn as the follower.";
        			CompleteStep();
        			break;
        		case 4:
                    msg.text = "Every time you finish the most recent command, click 'FINISH COMMAND,' and you will see the next command that you should follow.";
                    CompleteStep();
                    break;
                case 5:
                    finishCommandButton.interactable = true;
                    msgBanner.SetActive(false);
                    DisplayFollowerCommand("Follow the road and go to the <b>one blue triangle</b> card in front of you.");
                    finishCommandButton.GetComponent<Button>().onClick.AddListener(FinishBtnTask);
                    break;
                case 6:
                    msgBanner.SetActive(false);
                    DisplayFollowerCommand("Make a right immediately and walk on the road along the lake. Turn left at the first crossing and you should see a <b>two red circles</b> card near the light. Go pick it up.");
                    break;
        		case 7:
                    msgBanner.SetActive(false);
                    DisplayFollowerCommand("Come back to the road and you should see the leader in front of you. Walk past the leader and pick up the <b>one orange circle</b> card near the tall tree and right next to the three blue stripes card.");
                    break;
        		case 8:
                    msgBanner.SetActive(false);
                    DisplayFollowerCommand("Oops! I messed up. Please deselect the one orange circles card by walking off and onto it again.");
                    break;
                case 9:
                    msgBanner.SetActive(false);
                    DisplayFollowerCommand("Now go back to the road and make a right. You should see a <b>three black squares</b> card between the round yellow tree and the light. Now pick it up.");
                    break;
        		case 10:
                    note.SetActive(true);
                    msg.text = "Good job on collecting the set! Please remember you will have <b>limited</b> moves during the game, so remember to <i>use them wisely</i>!";
                    CompleteStep();
        			break;
                case 11:
                    break;
                case 12:
                    note.SetActive(true);
                    msg.text = "Good job on collecting the set! Please remember you will have <b>limited</b> moves during the game, so remember to <i>use them wisely</i>!";
                    CompleteStep();
                    break;
        		default:
                    if (done) {
                        CompleteTutorial(false);
                        note.SetActive(false);
                        Image image = panel.transform.GetComponent<Image>();
                        image.color = new Color32(255, 137, 80, 255);
                        done = true;
                        finishCommandButton.GetComponent<Button>().onClick.RemoveListener(FinishBtnTask);
                        msg.text = "Congrats! We recorded your completion of the Follower Tutorial to the database. Please go back to HIT page to continue.";
                    }
                    break;
        	}
        }
    }

    private void CheckComplete(int step)
    {
    	if(role == "Human")
    	{
        	switch(step)
        	{
		        case 7:
                	try
                	{
                		if(!setGame.activeCards.Any()) { break; }
                		var cardProp = setGame.activeCards.FirstOrDefault().GetComponent<CardProperties>();

                		if(cardProp.color == card_black && cardProp.count == 3)
                		{
                    		CompleteStep();
                    		MsgUpdate();
                		}
                		break;
                	}
                	catch(InvalidOperationException exception) { Debug.Log(exception); break; }
				case 8:
					try
					{
						var cardProp = setGame.activeCards.Last().GetComponent<CardProperties>();
						if(cardProp.color == card_blue && cardProp.count == 3 && scoreKeeper.score == 0)
						{
							CompleteStep();
							MsgUpdate();
						}
						break;
					}
					catch(InvalidOperationException exception) { Debug.Log(exception); break; }
				case 10:
					if(setGame.activeCards.Count == 1)
					{
						CompleteStep();
						MsgUpdate();
					}
					break;
				case 11:
					if(scoreKeeper.score == 1)
					{
						CompleteStep();
						MsgUpdate();
					}
					break;
				case 13:
					if(scoreKeeper.score == 3)
					{
						CompleteStep();
						MsgUpdate();
                        done = true;
					}
					break;
				default:
                	break;
        	}
        }
        else
        {
            if (step >= 10) {
                if(scoreKeeper.score == 1)
                {
                    done = true;
                    CompleteStep();
                    MsgUpdate();
                }
            }
        }
    }

    private void ResetStep()
    {
        complete = false;
        msgBanner.SetActive(true);
    }

    private void CompleteStep()
    {
        complete = true;
        step++;
        msgBanner.SetActive(true);
    }

    private void SubmitCmdComplete()
	{
		if(step == 5)
		{
			CompleteStep();
			MsgUpdate();
			note.SetActive(true);
		}
	}

	private void BtnTask()
	{
		CompleteStep();
		MsgUpdate();
	}

    private void FinishBtnTask() {
        if (step == 9) {
            finishCommandButton.GetComponent<Button>().onClick.RemoveListener(FinishBtnTask);
        }
        CompleteStep();
        MsgUpdate();
    }
}
