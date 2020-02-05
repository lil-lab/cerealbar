using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// turn based movement control
/// </summary>
public class TurnBasedControl : ActionInformation
{

    public bool isMoving = false;
    public HexCell currentLocation;
    public HexCell goalLocation;
    private int directionIndex = 0;
    private int hexRot = 60;

    private Queue<AgentAction> externalActionsQ = new Queue<AgentAction>();

    #region Unity Event Functions
    void Awake()
    {
        hexgrid = FindObjectOfType<HexGrid>();
        timeKeeper = FindObjectOfType<TimeKeeper>();
        propPlacement = FindObjectOfType<PropPlacement>();
        turnController = FindObjectOfType<TurnController>();

        animator = GetComponent<Animator>();
        rigidBody = GetComponent<Rigidbody>();
        dataCollection = GetComponent<DataCollection>();
    }

    void OnEnable()
    {
        webSocketManager = FindObjectOfType<WebSocketManager>();
        instructionControl = FindObjectOfType<InstructionControl>();

        WebSocketManager.OnStartGamePlayEvent += StartGamePlay;
        Restarter.OnRestartEvent += StopGamePlay;
    }

    void OnDisable()
    {
        WebSocketManager.OnStartGamePlayEvent -= StartGamePlay;
        Restarter.OnRestartEvent -= StopGamePlay;
    }

    public override void Update()
    {
      InputUpdate();
      ExternalInputUpdate();
      AnimatorUpdater();
    }

    public override void FixedUpdate()
    {
      RotateUpdate();
      WalkUpdate();
    }
    #endregion

    private void InputUpdate()
    {
      if (instructionControl.HasFocus())
      {
        return;
      }
      if ((mainCharacter==myCharacter || TutorialGuide.tutorialMode) && !timeKeeper.isPaused && !isMoving && canAct)
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

    public void ExternalInputUpdate()
    {
      if (externalActionsQ.Count > 0 && !isMoving)
      {
        var action = externalActionsQ.Dequeue();
        AddAction(action.agentState, action.direction);
      }
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
            isMoving = true;
            walkAmount = Vector3.Distance(goalLocation.transform.position, currentLocation.transform.position);
            var km = new DataCollection.KeyMovement();
            km.direction = goalLocation.coordinates.ToString();
            km.keyDownTime = timeKeeper.gameTime;
      }
    }

    /// <summary>
    /// changes all the flags for a rotation and documents it
    /// </summary>
    /// <param name="direction"></param>
    private void SetRotate(int dir, string tag)
    {
        if(CanMove(currentLocation,dir) && turnController.CanMove(LandType.Path))
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
            isMoving = true;
            deltaV = 0;
        }

    }

    #endregion

    #region movement Updaters
    /// <summary>
    /// Call in Update, similar to the other movement scripts, rotates agent at every frame to eventualy get to desired rotation
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
