using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Cached hex to hex cell movement for SIMULATING the game
/// </summary>
public class SimulatedControl : ActionInformation
{
    public bool isMoving = false;
    public HexCell currentLocation;
    public int directionIndex = 0;
    private bool gotCard;
    // private int hexRot = 60;
    // private DataCollection dc;

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
        gotCard = false;
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
      WebSocketManager.OnStartGamePlayEvent += StartGamePlay;
      Restarter.OnRestartEvent -= StopGamePlay;
    }

    //void Start()
    //{
    //    dc = FindObjectOfType<DataCollection>();
    //}

    public override void Update()
    {
      ExternalInputUpdate();
    }

    #endregion

    public void EnqueueExternalAction(ActionInformation.AgentState state, int dir)
    {
      var externalAction = new AgentAction();
      externalAction.agentState = state;
      externalAction.direction = dir;
      externalActionsQ.Enqueue(externalAction);
    }

    public void ExternalInputUpdate()
    {
      if (externalActionsQ.Count > 0 && !isMoving)
      {
        var action = externalActionsQ.Dequeue();
        DoAction(action.agentState, action.direction);
      }
    }

    public string DoAction(ActionInformation.AgentState state, int dir)
    {
	
		MainControl mainControl = FindObjectOfType<MainControl>();
		
		
        if (!timeKeeper.isPaused && !isMoving)
        {

            if (state == AgentState.Turning && dir == 1)
            {
                RotateTo(1);
            }
            else if (state == AgentState.Turning && dir == -1)
            {
                RotateTo(-1);
            }
            else if (state == AgentState.Walking && dir == 1)
            {
				
                MoveTo(directionIndex % 6, 1, tag);
            }
            else if (state == AgentState.Walking && dir == -1)
            {
                var oppositeDir = (int)HexDirectionExtensions.Opposite((HexDirection)(directionIndex % 6));
                MoveTo(oppositeDir, -1, tag);
            }
            if (gotCard)
            {
				
				gotCard = false;
                return "got card";
            }
			
        }
		 //MainControl mainControl = FindObjectOfType<MainControl>();
		

        return "";
    }


    #region MovementSetters
    /// <summary>
    /// Sets the neighborIndex as the next goal location, and the direction you need to walk to get to it
    /// Sets all the flags and also hanndles data collection
    /// </summary>
    /// <param name="neighborIndex"></param>
    /// <param name="dir"></param>
    private void MoveTo(int neighborIndex, int dir, string tag)
    {
		int myFlag=0;
        var nextLocation = currentLocation.GetNeighbor((HexDirection)((neighborIndex + 6) % 6));
		//**************************************
		PropPlacement propPlacement = FindObjectOfType<PropPlacement>();
		for (int i = 0; i < propPlacement.cards.Length; i++)
        {
		  if (!propPlacement.cards[i].activeSelf) {
			  if (propPlacement.cards[i].transform.position == nextLocation.transform.position){
				  myFlag=1;
			  }
			  
		  }
        }
		MainControl mainControl = FindObjectOfType<MainControl>();
		if (myFlag==1){
			
			mainControl.updating_cards=true;	
		}
		
		
        if (CanMove(nextLocation, dir) && turnController.CanMove(currentLocation.landType))
        {
            transform.position = nextLocation.transform.position;
            currentLocation = nextLocation;
        }
    }

    /// <summary>
    /// changes all the flags for a rotation and documents it
    /// </summary>
    /// <param name="direction"></param>
    private void RotateTo(int dir)
    {
        if(CanMove(currentLocation,dir) && turnController.CanMove(currentLocation.landType))
        {
          directionIndex += dir;
          var angle = (((directionIndex % 6) + 1) * 60) - 30;
          transform.eulerAngles = new Vector3(0, angle, 0);
        }
    }
    #endregion

    void OnTriggerEnter(Collider other)
    {

        if (other.tag == "Card")
        {
            gotCard = true;
        }
    }

}
