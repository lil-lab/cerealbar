using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// QUEUED Hex to hex cell movement
/// </summary>
public class HexQueuedCntrl : ActionInformation
{
    public HexCell currentLocation;
    public HexCell goalLocation;
    private int directionIndex = 0;
    private int hexRot = 60;
    // private DataCollection dc;
    public bool isExecuting = false;
    private Queue<AgentAction> actionsQ = new Queue<AgentAction>();

    private List<AgentAction> actionsRecord = new List<AgentAction>();
    public delegate void OnFinishedActionHandler(string tag);
    public static event OnFinishedActionHandler OnFinishedHexActionEvent;

    public static void InvokeHexActFinished(string tag)
    {
        OnFinishedHexActionEvent(tag);
    }

    #region Unity Event functions
    void Awake()
    {
        timeKeeper = FindObjectOfType<TimeKeeper>();
        dataCollection = GetComponent<DataCollection>();
        animator = GetComponent<Animator>();
        rigidBody = GetComponent<Rigidbody>();

        hexgrid = FindObjectOfType<HexGrid>();
        propPlacement = FindObjectOfType<PropPlacement>();
        turnController = FindObjectOfType<TurnController>();

    }
    void OnEnable()
    {
        webSocketManager = FindObjectOfType<WebSocketManager>();
        instructionControl = FindObjectOfType<InstructionControl>();

        OnFinishedHexActionEvent += ExecuteQueuedAction;
        ConditionalBools.OnGBoolMetEvent += StopClearAll;

        // WebSocketManager.OnStartGamePlayEvent += StartGamePlay;
        Restarter.OnRestartEvent += StopGamePlay;

    }

    void OnDisable()
    {
        OnFinishedHexActionEvent -= ExecuteQueuedAction;
        ConditionalBools.OnGBoolMetEvent -= StopClearAll;

        // WebSocketManager.OnStartGamePlayEvent -= StartGamePlay;
        Restarter.OnRestartEvent -= StopGamePlay;
    }


    void OnCollisionEnter()
    {
        StopClearAll();
    }

    //void Start()
    //{
    //    dc = FindObjectOfType<DataCollection>();
    //}

    public override void Update()
    {
      if ( !started )
        return;
      AnimatorUpdater();
      InputUpdater();
    }

    public override void FixedUpdate()
    {
      RotateUpdate();
      WalkUpdate();
    }
    #endregion

    //TODO remove- this is for testing unless we want to keep key pressing
    private void InputUpdater()
    {
      if (instructionControl.HasFocus())
      {
        return;
      }
      /*if (Input.GetKeyDown(KeyCode.Space))
      {
      }*/
      if (mainCharacter==myCharacter && !timeKeeper.isPaused && canAct)
      {
          if(canMove && Input.GetKeyDown(KeyCode.RightArrow))
          {
              AddAction(AgentState.Turning, 1);
          }
          else if(canMove && Input.GetKeyDown(KeyCode.LeftArrow))
          {
              AddAction(AgentState.Turning, -1);
          }
          else if(canMove && Input.GetKeyDown(KeyCode.UpArrow))
          {
              AddAction(AgentState.Walking, 1);
          }
          else if(canMove && Input.GetKeyDown(KeyCode.DownArrow))
          {
              AddAction(AgentState.Walking, -1);
          }
      }
    }
    #region Action Handling

    public override void AddAction(AgentState state, int dir)
    {
        var moveAction = new AgentAction();
        moveAction.agentState = state;
        moveAction.direction = dir;
        actionsQ.Enqueue(moveAction);
        if (actionsQ.Count <= 1)
        {
            ExecuteQueuedAction(this.tag);
        }
    }

    public void AddExternalAction(AgentState state, int dir)
    {
      AddAction(state,dir);
    }
    /// <summary>
    /// Can only be called when we are not executing actions
    /// If not executing, takes action from actionqueue and calls for corresponding movemnt
    /// </summary>
    public void ExecuteQueuedAction(string tag)
    {
        if (actionsQ.Count != 0 && !isExecuting)
        {
            isExecuting = true;
            var action = actionsQ.Dequeue();
            actionsRecord.Add(action);
            if (action.agentState == AgentState.Turning)
            {
                SetRotate(action.direction, tag);
            }
            else if (action.agentState == AgentState.Walking)
            {
                if (action.direction == 1)
                    SetMoveTo(directionIndex % 6, 1, tag);
                else
                {
                    var oppositeDir = (int)HexDirectionExtensions.Opposite((HexDirection)(directionIndex % 6));
                    SetMoveTo(oppositeDir, -1, tag);
                }
            }
        }
    }

    /// <summary>
    /// Called in OnCollisionEnter
    /// In the event of hitting something and player cannot continue set course of action
    /// Stops all movement, and resets the action queue for movemnt to be started anew from point of collision
    /// </summary>
    public void StopClearAll()
    {
        agentState = AgentState.Stationary;
        actionsQ.Clear();
        if (timeKeeper)
        {
            var keyMovement = new DataCollection.KeyMovement();
            keyMovement.direction = "stop";
            keyMovement.keyDownTime = timeKeeper.gameTime;
        }
        isExecuting = false;
    }
    #endregion
    #region direction setters

    /// <summary>
    /// changes all the flags for a rotation and documents it
    /// </summary>
    /// <param name="direction"></param>
    private void SetRotate(int dir, string tag)
    {
        if(CanMove(currentLocation, dir) && turnController.CanMove(LandType.Path))
        {
            Dictionary<string, string> strData = new Dictionary<string, string>()
            {
                {"character", tag},
                {"type", "R" + (dir==1 ? "R":"L")},
                {"position","same"}
            };
            webSocketManager.Send("movement", strData, null);
            if (turnBased) { turnController.Movement(myCharacter, LandType.Path); }

            directionIndex += dir;
            rotVal = dir;
            agentState = AgentState.Turning;
            deltaV = 0;
        }
        else
        {
            isExecuting = false;
            OnCollisionEnter();
        }
    }

    /// <summary>
    /// Sets the neighborIndex as the next goal location, and the direction you need to walk to get to it
    /// Sets all the flags and also hanndles data collection
    /// </summary>
    /// <param name="neighborIndex"></param>
    /// <param name="dir"></param>
    private void SetMoveTo(int neighborIndex, int dir, string tag)
    {
        // have to check the prop placements/card placements here
        var nextLocation = currentLocation.GetNeighbor((HexDirection)((neighborIndex + 6) % 6));

        if (CanMove(nextLocation, dir) && turnController.CanMove(nextLocation.landType))
        {
            Dictionary<string, string> strData = new Dictionary<string, string>()
            {
                {"character", tag},
                {"type", "M" + (dir==1 ? "F":"B")},
                {"position",nextLocation.coordinates.ToString()}
            };
            webSocketManager.Send("movement", strData, null);
            if (turnBased) { turnController.Movement(myCharacter, nextLocation.landType); }

            goalLocation = nextLocation;
            deltaV = 0;
            walkVal = dir;
            agentState = AgentState.Walking;
            walkAmount = Vector3.Distance(goalLocation.transform.position, currentLocation.transform.position);
            var km = new DataCollection.KeyMovement();
            km.direction = goalLocation.coordinates.ToString();
            km.keyDownTime = timeKeeper.gameTime;
        }
        else
        {
            isExecuting = false;
            OnCollisionEnter();
        }
    }
    #endregion

    #region movement updaters
    /// <summary>
    /// Called in Update, rotates using update loop until degrees rotation is achieved
    /// </summary>
    private void RotateUpdate()
    {
        if (agentState == AgentState.Turning)
        {
            var r = rotateMoveSpeed * Time.deltaTime;
            deltaV += r;
            transform.Rotate(0, r * rotVal, 0);
            if (deltaV >= hexRot)
            {
                var angle = (((directionIndex % 6) + 1) * 60) - 30;
                transform.eulerAngles = new Vector3(0, angle, 0);
                isExecuting = false;
                agentState = AgentState.Stationary;
                InvokeHexActFinished(this.tag);
            }

        }
    }

    /// <summary>
    /// Called in Update loop - moves player using update loop until walkamount is achieved
    /// </summary>
    private void WalkUpdate()
    {
        if (agentState == AgentState.Walking)
        {
            var move = walkSpeed * transform.forward * m_interpolation * Time.deltaTime * walkVal;
            transform.position += move;
            deltaV += Vector3.Magnitude(move);
            if (transform.position.y > .75)
            {
                StopClearAll();
                transform.position = new Vector3(transform.position.x, 0, transform.position.z);
            }
            else if (deltaV >= walkAmount)
            {
                isExecuting = false;
                agentState = AgentState.Stationary;
                currentLocation = goalLocation;
                transform.position = goalLocation.transform.position;
                InvokeHexActFinished(this.tag);

            }
        }
    }
    #endregion

}
