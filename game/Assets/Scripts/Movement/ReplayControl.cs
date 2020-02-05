using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

/// <summary>
/// Cached hex to hex cell movement for replaying games
/// </summary>
public class ReplayControl : ActionInformation
{
    public bool isMoving = false;
    public HexCell currentLocation;
    public HexCell goalLocation;
    private int directionIndex = 0;
    private int hexRot = 60;
    // private DataCollection dc;

    // public delegate void MovingEvent(bool movingCheck);
    // public static event MovingEvent movingEvent;

    private Queue<AgentAction> externalActionsQ = new Queue<AgentAction>();

    // Note: every rot left to sub 1 and rot right to add 1
    // mod it by 6 to access the hexcell
    // can't move to edge pieces, cant move to proplocs

    #region Unity Event Functions
    void Awake()
    {
        hexgrid = FindObjectOfType<HexGrid>();
        timeKeeper = FindObjectOfType<TimeKeeper>();
        dataCollection = GetComponent<DataCollection>();
        propPlacement = FindObjectOfType<PropPlacement>();
        turnController = FindObjectOfType<TurnController>();
        animator = GetComponent<Animator>();
        rigidBody = GetComponent<Rigidbody>();
    }

    void OnEnable()
    {
        webSocketManager = FindObjectOfType<WebSocketManager>();
        instructionControl = FindObjectOfType<InstructionControl>();
        // WebSocketManager.OnStartGamePlayEvent += StartGamePlay;
        Restarter.OnRestartEvent += StopGamePlay;
    }

    void OnDisable()
    {
    	// WebSocketManager.OnStartGamePlayEvent -= StartGamePlay;
    	Restarter.OnRestartEvent -= StopGamePlay;
    }

    //void Start()
    //{
    //    dc = FindObjectOfType<DataCollection>();
    //}

    public override void Update()
    {
        AnimatorUpdater();
    }

    public override void FixedUpdate()
    {
        DoExternalActions();
        RotateUpdate();
        WalkUpdate();
    }
    #endregion

    public bool DoExternalActions()
    {
      if(externalActionsQ.Count > 0)
      {
        Replay.running = true;
        if (!isMoving)
        {
          var action = externalActionsQ.Dequeue();
          AddAction(action.agentState, action.direction);
        }
      }
      else { Replay.running = false; }
      return true;
    }

    public override void AddAction(ActionInformation.AgentState state, int dir)
    {
        if (!timeKeeper.isPaused && !isMoving)
        {
            if (state == AgentState.Turning && dir == 1)
            {
                SetRotate(1, tag);
            }
            else if (state == AgentState.Turning && dir == -1)
            {
                SetRotate(-1, tag);
            }
            else if (state == AgentState.Walking && dir == 1)
            {
                SetMoveTo(directionIndex % 6, 1, tag);
            }
            else if (state == AgentState.Walking && dir == -1)
            {
                var oppositeDir = (int)HexDirectionExtensions.Opposite((HexDirection)(directionIndex % 6));
                SetMoveTo(oppositeDir, -1, tag);
            }

        }

    }

    public void AddExternalAction(ActionInformation.AgentState state, int dir)
    {
      var externalAction = new AgentAction();
      externalAction.agentState = state;
      externalAction.direction = dir;
      externalActionsQ.Enqueue(externalAction);
    }

    #region MovementSetters
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

        if (CanMove(nextLocation, dir) && turnController.CanMove(currentLocation.landType))
        {
            goalLocation = nextLocation;
            deltaV = 0;
            walkVal = dir;
            agentState = AgentState.Walking;
            isMoving = true;
            walkAmount = Vector3.Distance(goalLocation.transform.position, currentLocation.transform.position);
        }
    }

    /// <summary>
    /// changes all the flags for a rotation and documents it
    /// </summary>
    /// <param name="direction"></param>
    private void SetRotate(int dir, string tag)
    {


        if(CanMove(currentLocation,dir) && turnController.CanMove(currentLocation.landType))
        {
            directionIndex += dir;
            rotVal = dir;
            agentState = AgentState.Turning;
            isMoving = true;
            deltaV = 0;
        }
    }

    #endregion

    #region movement Updaters
    /// <summary>
    /// Call in Update, similar to the other movement scripts, rotates agent at every frame to eventually get to desired rotation
    /// in this case the goal rotation is 60 degrees because there are 6 neighboring cells that the agent can turn to
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
                isMoving = false;
                agentState = AgentState.Stationary;
            }
        }
    }

    /// <summary>
    /// Call in Update()
    /// Sets all the flags and updates position, when deltaV is reached, agents location is adjusted to be exactly center
    /// </summary>
    private void WalkUpdate()
    {
        if (agentState == AgentState.Walking)
        {
            var move = walkSpeed * transform.forward * m_interpolation * Time.deltaTime * walkVal;
            transform.position += move;
            deltaV += Vector3.Magnitude(move);
            if (deltaV >= walkAmount)
            {
                agentState = AgentState.Stationary;
                currentLocation = goalLocation;
                transform.position = goalLocation.transform.position;
                // bc WalkUpdate is called at every frame deltaV does not necessairy == walkAmount (could exceed)
                // so to keep the agent consistently at the center of each hexCell, adjust the agents location to be at the center
                isMoving = false;
            }
        }
    }
    #endregion
}
