using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using System;
using System.Text.RegularExpressions;
using System.Text;
using System.Linq;

/// <summary>
/// This script handles everything on the PlayUI screen, including the onscreen dpad, the pos/neg buttons and the code input stuff
/// </summary>
public class CommandCommunication : MonoBehaviour
{
    public enum InputType { LanguageInput,PLInput};
    public InputType inputType = InputType.LanguageInput;

    //screen color changers for PL when input cant be processed
    [SerializeField]
    public Color warningRed;

    private string[] whileCons = { "Near", "NotNear", "NotAtEdge", "AtEdge" };

    private Dictionary<string, GameObject> clickedItems = new Dictionary<string, GameObject>();
    public HexToHexControl hexMoveControl;
    public QueuedControl queuedControl;

    public InputField inputField;
    public InputField commandHistory;
    private string inputText;

    private bool isExecutingWhile = false;
    public ConditionalBools agentCBS;
    public string Tag;

    #region PL Regexes

    private string patternFor = @"for[(]([0-9]+)[)]";
    private Regex r_For;

    private string patternEndFor = @"endfor";
    private Regex r_EndFor;

    private string patternWhile = @"while[(]([a-zA-Z '_ 0-9()]+)[)]";
    private Regex r_While;

    private string patternEndWhile = @"endwhile";
    private Regex r_EndWhile;
    #endregion

    #region Custom Events for UI

    public delegate void OnFeedbackHandler(bool good);
    public static event OnFeedbackHandler OnFeedbackEvent;
    private WebSocketManager webSocketManager;
    private InstructionControl instructionControl;
    private TurnController turnController;

    private static string lowerCase = "abcdefghijklmnopqrstuvwxyz";
    private static string upperCase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    private static string nums = "1234567890";
    private static string otherChars = ",.?/;:'()*&^#@!~-_=+ ";
    private static string safeCharacters = lowerCase+upperCase+nums+otherChars;

    public static int currInstrIdx;
    public static List<string> instrBuffer;

    public static CommandCommunication CommandCommunicationInstance { get; private set; }

    public static void InvokeFeedback(bool good)
    {
        OnFeedbackEvent(good);
    }
    #endregion

    #region Unity Event Functions
    void OnEnable()
    {
        GrabMoveScripts();
        agentCBS = FindObjectOfType<ConditionalBools>();
        webSocketManager = FindObjectOfType<WebSocketManager>();
        instructionControl = FindObjectOfType<InstructionControl>();
        turnController = FindObjectOfType<TurnController>();
        ConditionalBools.OnGBoolMetEvent += codeboolMet;

        //initialize the list objects to store commands and set currInstrIdx to 0
        instrBuffer = new List<string>();
        currInstrIdx = 0;
    }

    void OnDisable()
    {
        ConditionalBools.OnGBoolMetEvent -= codeboolMet;
    }

    void Start()
    {
        r_For = new Regex(patternFor);
        r_EndFor = new Regex(patternEndFor);
        r_While = new Regex(patternWhile);
        r_EndWhile = new Regex(patternEndWhile);
    }

    /*void Update()
    {
        ClickCheck();
    }*/

    void LateUpdate()
    {

    }
    #endregion

    #region FeedBack

    public void PositiveFeedback()
    {
        InvokeFeedback(true);
    }

    public void NegativeFeedback()
    {
        InvokeFeedback(false);
    }

    public bool CompletedAllCommands()
    {
        return currInstrIdx >= instrBuffer.Count;
    }

    #endregion
    private void GrabMoveScripts()
    {
        var hexScripts = FindObjectsOfType<HexToHexControl>();
        foreach (var hscript in hexScripts)
        {
            if (hscript.gameObject.tag == "Agent")
            {
                hexMoveControl = hscript;
                hexMoveControl.tag = "Agent";
                break;
            }
        }

        var queuedControls = FindObjectsOfType<QueuedControl>();
        foreach (var qscript in queuedControls)
        {
            if (qscript.tag == "Agent")
            {
                queuedControl = qscript;
                queuedControl.tag = "Agent";
                break;
            }
        }
    }

    /// <summary>
    /// Called in Update- if in command input mode, and user clicks on an object
    /// that object is grabbed and a unique name of it is added to the inputfield as well as
    /// to the dictionary "clicked items" with a reference to the GO.
    /// </summary>
    //TODO Clear on restart
    private void ClickCheck()
    {
        if (Input.GetMouseButtonDown(0))
        {
            RaycastHit hit;
            var ray = Camera.main.ScreenPointToRay(Input.mousePosition);
            if (Physics.Raycast(ray, out hit))
            {
                if (hit.transform.tag == "PlaceableObject" || hit.transform.tag == "Card")
                {
                    var goName = CleanGOName(hit.transform.name) + clickedItems.Count;
                    var keyAdded = false;
                    while (!keyAdded)
                    {
                        if (clickedItems.ContainsKey(goName))
                        {
                            goName = CleanGOName(hit.transform.name) + (clickedItems.Count + 1);
                        }
                        else
                        {
                            clickedItems.Add(goName, hit.transform.gameObject);
                            inputField.text += "'" + goName + "'";
                            keyAdded = true;

                        }
                    }

                }
            }
        }
    }

    private string CleanGOName(string goName)
    {
        var gname = goName;
        try
        {
            var firstbracketIndex = goName.IndexOf("(");
            gname = goName.Substring(0, firstbracketIndex);
        }
        catch (ArgumentOutOfRangeException)
        {

        }
        return gname;
    }

    public bool IsInputFieldValid(string s) {
        s = Regex.Replace(s, @"\s+", "");
        bool containsLetter = Regex.IsMatch(s, @"^[a-zA-Z]");
        bool containsNumber = Regex.IsMatch(s, @"\d");

        return containsLetter || containsNumber ? true : false;
    }

    #region PL stuff

    /// <summary>
    /// Functions (* means complete)
    /// for * endfor
    /// while -endwhile
    /// WalkForward *
    /// WalkBackward*
    /// RotateRight*
    /// RotateLeft*
    /// Clear*
    /// near - todo
    /// notnear -todo
    /// edge -todo
    /// notEdge -todo
    /// </summary>
    public void SubmitCode()
    {
        if(inputField.text == "\n" || inputField.text == "") // Check for empty commands.
        {
            inputField.text = "";
            return;
        } else if (!IsInputFieldValid(inputField.text)) {
            return;
        }
        if (turnController.instructionCostMove && !turnController.HasMoves())
        {
            inputField.text = "";
            return;
        }

        if (inputType == InputType.PLInput)
        {
            inputText = inputField.text;
            var pv = ProcessCommandInput(inputText);
            if (pv > 0)
            {
                //get pv code
                queuedControl.StopClearAll();
                StartCoroutine(RedTintScreen());
                // change screen to red for 2 seconds?
            }
        }
        // language input
        else
        {
            inputText = CommandCommunication.Filter(inputField.text);

            Dictionary<string, string> strData = new Dictionary<string, string>()
            {
                {"content", inputText}
            };
            webSocketManager.Send("instruction", strData, null);
            
            if (turnController.instructionCostMove)
                turnController.Movement("Human", LandType.Path);
        }

        inputField.text = "";
        turnController.endTurnButton.interactable = true;
        AddCommandToQueue(inputText);
    }

    public void AddCommandToQueue(string inputText)
    {
        instrBuffer.Add(inputText);

        // Now the end-turn button should be available to the leader.
        
        instructionControl.ShowCommands();

        // Turn off the not-sent banner if it has already been put up.
        if (instructionControl.displayedHasNotSent) {
            instructionControl.notSentBanner.SetActive(false);
        }
    }

    public void FinishCommand()
    {
        // Ignore finish-command keypresses if in tutorial mode.
        if (!TutorialGuide.tutorialMode) {
            // Only to be called by the follower.
            currInstrIdx += 1;
            instructionControl.ShowCommands();
            // End turn when there is no more instruction

            // Set the finish command banner as inactive because the person has followed
            // our instructions. Also reset the previous move time, and the number of
            // moves in the current command.
            turnController.finishCommandBanner.SetActive(false);
            turnController.SetPrevMoveTime();
            turnController.movesInThisCommand = 0;

            Dictionary<string, string> strData = new Dictionary<string, string>()
            {
                {"content", currInstrIdx.ToString()}
            };
            webSocketManager.Send("finishedCommand", strData, null);

            if (currInstrIdx >= instrBuffer.Count) {
                TurnController turnController = FindObjectOfType<TurnController>();
                turnController.GiveTurn("Finished All Commands");
            }
        }
    }

    public void ReplayFinishCommand()
    {
        currInstrIdx += 1;
        instructionControl.ShowCommands();
    }

    public void ReceiveFinishCommand(string finishedIndex)
    {
        // Only to be called by the leader.
        currInstrIdx += 1;
        instructionControl.ShowCommands();
    }

    public void StoreCommand(string s)
    {
        instrBuffer.Add(s);
        instructionControl.ShowCommands();
    }

    public static string Filter(string s)
    {

      StringBuilder ret = new StringBuilder();
      foreach (char c in s)
      {
        if (safeCharacters.Contains(c))
        {
          ret.Append(c);
        }
      }

      ret = ret.Replace("\\","\\\\");
      ret = ret.Replace("\"", "\\\"");
      return ret.ToString();
    }


    private int ProcessCommandInput(string fieldInput)
    {
        var instructions = fieldInput.Split('\n');
        var loopInstructions = new StringBuilder();
        var inFerLoop = false; //spelt wrong to indicate its players for loops
        var readingWhilerLoop = false;
        var loopCount = 0;
        var numFors = 0;

        for (int i = 0; i < instructions.Length; i++)
        {
            //DONE: PROCESSING FOR LOOP
            if (inFerLoop && !r_For.IsMatch(instructions[i]) && !r_While.IsMatch(instructions[i])) // need to check if not a match - if it is a match ,we got back to the for/while checks
            {
                //maybe split this into another function
                if (r_EndFor.IsMatch(instructions[i])) // if the next instruction is a endfor - subtract the number of fors
                {
                    numFors -= 1;
                    if (numFors == 0)
                    {
                        for (int l = 0; l < loopCount; l++)
                            ProcessCommandInput(loopInstructions.ToString()); // need to wait for this to be finished
                        inFerLoop = false;
                    }
                }
                else
                {
                    loopInstructions.Append(instructions[i]);
                    loopInstructions.Append('\n');
                }
            }
            //TODO: PROCESSING WHILE LOOP
            else if (readingWhilerLoop ) //maybe need to include a for in there {
            {
                if (r_EndWhile.IsMatch(instructions[i]))
                {
                    while (isExecutingWhile) // conditionalbools script will invoke an event when
                    {
                        var ps = ProcessCommandInput(loopInstructions.ToString());
                        if (ps > 0)
                        {
                            queuedControl.StopClearAll();
                            return ps;
                        }
                    }
                    // break off to start new process of while and then come back later to resume code
                    readingWhilerLoop = false;
                }
                else if (r_While.IsMatch(instructions[i]) || r_For.IsMatch(instructions[i]))
                {
                    // theres another while or a for loop in here - no bueno
                    return 4;
                }
                else
                {
                    loopInstructions.Append(instructions[i]);
                    loopInstructions.Append('\n');
                    //TODO - add instructions for while loop
                    // should the while loop be singular
                    // cannot do while loop in for loop

                }
            }
            //DONE: DETECT + PROCESS FOR LOOP
            if (r_For.IsMatch(instructions[i]))
            {
                var match = r_For.Match(fieldInput);
                loopCount = int.Parse(match.Groups[1].Value);
                inFerLoop = true;
                numFors += 1;
                //-look for the closest closing for in the following lines
            }
            //TODO: DETECT + PROCESS WHILE LOOP
            else if (r_While.IsMatch(instructions[i]))
            {
                if (r_While.IsMatch(instructions[i]))
                {
                    var match = r_While.Match(fieldInput);
                    var conditional = match.Groups[1].Value;
                    var svGood = SetWhileContents(conditional);
                    if (svGood == false)
                    {
                        return 3;
                        // kill while loop - stop reading - not readable do not load
                    }
                    else
                        readingWhilerLoop = true; // only make reading the while true if conditional exists


                }
            }
            //DONE: PLAIN INSTRUCTION
            else if (!inFerLoop && !readingWhilerLoop)
            {
                var eS =  EnqueueAction(instructions[i]);
                if (eS == false)
                {
                    return 2;
                }
            }

        }
        if (inFerLoop || readingWhilerLoop)
            return 1; // means we ran through the code and never found a closing for loop or while
        return 0;
    }

    //TODO  change to int to expand on error codes
    private bool SetWhileContents(string contents)
    {
        var okCondition = false;
        try
        {
            var condition =contents.Substring(0, contents.IndexOf('('));
             if (!whileCons.Contains(condition))
            {
                return false;
            }

            var clickedObjName = contents.Split('(', ')')[1].Replace("'","");
            if (clickedObjName == "")
            {
                //if there is nothing there - it is a near - so setCV with jsut the condition/bool to be met
                agentCBS.SetCB((ConditionalBools.GameBools)Array.IndexOf(whileCons, condition));

            }
            // There are two possibilites -1. isEdge or is Near

            // only isNear will need the object
            //todo check obj - if these two are not met no bueno -
            if (!clickedItems.ContainsKey(clickedObjName))
            {
                return false;
            }
            else
            {
                var clickedObj = clickedItems[clickedObjName];
                agentCBS.SetCB((ConditionalBools.GameBools)Array.IndexOf(whileCons, condition), clickedObj);

            }
        }
        catch
        {
            okCondition = false;
        }
        return okCondition;
    }

    private bool ConditionCheck(string condition)
    {
        if(whileCons.Contains(condition))
            return true;
        return false;
    }

    private bool ConditionGOCheck(string goName)
    {
        if (clickedItems.ContainsKey(goName))
            return true;
        return false;
    }

    private bool EnqueueAction(string instruction)
    {
        var enqueueSuccess = true;

        switch (instruction)
        {
            case "WalkForward":
                queuedControl.AddAction(ActionInformation.AgentState.Walking, 1);
                break;
            case "WalkBackward":
                queuedControl.AddAction(ActionInformation.AgentState.Walking, -1);
                break;
            case "RotateLeft":
                queuedControl.AddAction(ActionInformation.AgentState.Turning, -1);
                break;
            case "RotateRight":
                queuedControl.AddAction(ActionInformation.AgentState.Turning, 1);
                break;
            case "Clear":
                queuedControl.StopClearAll();
                break;
            default:
                enqueueSuccess = false;
                break;
        }
        return enqueueSuccess;
    }

    private void codeboolMet()
    {
        isExecutingWhile = false;
    }

    #endregion


    private IEnumerator RedTintScreen()
    {
        yield return new WaitForSecondsRealtime(1f);
    }

}
