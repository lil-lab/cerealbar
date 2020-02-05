using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class QueuedControl : ActionInformation
{
    public bool isExecuting = false;
    private Queue<AgentAction> actionsQ = new Queue<AgentAction>();

    private List<AgentAction> actionsRecord = new List<AgentAction>();
    public delegate void OnFinishedActionHandler(string tag);
    public static event OnFinishedActionHandler OnFinishedActionEvent;

    public static void InvokeActionFinished(string tag)
    {
        OnFinishedActionEvent(tag);
    }

    #region Unity Event functions
    void Awake()
    {
        timeKeeper = FindObjectOfType<TimeKeeper>();
        dataCollection = GetComponent<DataCollection>();
        animator = GetComponent<Animator>();
        rigidBody = GetComponent<Rigidbody>();
    }
    void OnEnable()
    {

        OnFinishedActionEvent += ExecuteQueuedAction;

        ConditionalBools.OnGBoolMetEvent += StopClearAll;

    }

    void OnDisable()
    {
        OnFinishedActionEvent -= ExecuteQueuedAction;

        ConditionalBools.OnGBoolMetEvent -= StopClearAll;

    }


    void OnCollisionEnter()
    {
        StopClearAll();
    }

    public override void Update()
    {
        AnimatorUpdater();
        //InputUpdater();
    }

    public override void FixedUpdate()
    {
        RotateUpdate();
        WalkUpdate();
    }
    #endregion

/*    //TODO remove- this is for testing unless we want to keep key pressing
    private void InputUpdater()
    {
        if (!timeKeeper.isPaused && tag != "Agent")
        {
            if (Input.GetKeyDown(KeyCode.RightArrow))
            {
                AddAction(AgentState.Turning, 1);
            }
            else if (Input.GetKeyDown(KeyCode.LeftArrow))
            {
                AddAction(AgentState.Turning, -1);
            }
            else if (Input.GetKeyDown(KeyCode.UpArrow))
            {
                AddAction(AgentState.Walking, 1);
            }
            else if (Input.GetKeyDown(KeyCode.DownArrow))
            {
                AddAction(AgentState.Walking, -1);
            }

        }
    }
*/
    #region Action Handling
    /// <summary>
    /// Adds action to queue with state, direction and also creates a new keymovement for datacollection
    /// if there are no actions executing at the moment, calls the execute the queued action(s)
    /// </summary>
    /// <param name="state">walking/turning</param>
    /// <param name="dir">depending on the state being set:forward = 1, back = -1, right = 1, left = -1 </param>
    public override void AddAction(AgentState state, int dir)
    {
        var moveAction = new AgentAction();
        moveAction.agentState = state;
        moveAction.direction = dir;
        actionsQ.Enqueue(moveAction);
        if (actionsQ.Count <= 1)
        {
            ExecuteQueuedAction( this.tag);
        }
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
                SetRotate(action.direction);
            }
            else if (action.agentState == AgentState.Walking)
            {
                SetWalk(action.direction);
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

    // TODO possibly: only allow sets when you are waiting instruction - disregard/hold everything else
    /// <summary>
    /// On a rotate call, sets the rotate value for increasing or decreasing angle,
    /// resets delta and sets agents state to turning
    /// </summary>
    /// <param name="turnDir"></param>
    private void SetRotate(int turnDir)
    {
        rotVal = turnDir;
        deltaV = 0;
        agentState = AgentState.Turning;

    }

    /// <summary>
    /// On a walk call, sets the walk value to back or forward
    /// Resets delta and sets state to walking
    /// </summary>
    /// <param name="walk"></param>
    private void SetWalk(int walk)
    {
        walkVal = walk;
        //if (walk < 0)
        //    transform.Rotate(new Vector3(0, 180, 0));
        agentState = AgentState.Walking;
        deltaV = 0;
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
            if (deltaV >= rotateAmount)
            {
                isExecuting = false;
                agentState = AgentState.Stationary;
                InvokeActionFinished(this.tag);
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
            var move = transform.forward * m_interpolation * Time.deltaTime * walkVal;
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
                InvokeActionFinished(this.tag);
            }
        }
    }

    #endregion



}
