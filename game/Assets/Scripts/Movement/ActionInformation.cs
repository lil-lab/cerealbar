using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ActionInformation : MonoBehaviour
{
    /* Note:
    - Characters can move while it is their turn AND they have >0 moves
    left in that turn.
    - Characters can take all other actions (turning, giving instructions) as
    long as it is their turn, even if they have no moves left in that turn
    */
    public bool canMove; // true when character can move forward and backward
    public bool canAct; // true when character can do anything
    public bool turnBased;
    protected bool started = false;

    public void SetTurnBased(bool t)
    {
      turnBased = t;
      if (t)
      {
        if (myCharacter == "Human")
        {
          canMove=true;
          canAct=true;
        }
        else if (myCharacter == "Agent")
        {
          canMove=false;
          canAct=false;
        }
      }
      else
      {
        canMove=true;
        canAct=true;
      }
      #if SIMULATING
      canMove=false;
      canAct=false;
      #endif

      if (Replay.replaying)
      {
        canMove=false;
        canAct=false;
      }
    }

    protected WebSocketManager webSocketManager;
    protected TurnController turnController;
    protected InstructionControl instructionControl;

    public string myCharacter;
    public string mainCharacter;

    [Tooltip("Set this in the Awake() deriving off of ActionInformation")]
    public TimeKeeper timeKeeper;
    public DataCollection dataCollection;
    public AgentState agentState = AgentState.Stationary;
    public HexGrid hexgrid;
    public PropPlacement propPlacement;

    #region Walk Info
    [SerializeField]
    internal float walkSpeed;
    internal readonly float m_interpolation = 20;
    [SerializeField]
    internal float walkAmount = 30;
    internal int walkVal = 1; //handles direction

    #endregion

    #region Turning Vars
    [SerializeField]
    internal float rotateMoveSpeed;
    [SerializeField]
    internal float rotateAmount = 30;
    [SerializeField]
    internal int rotVal = 1; //handles direction of rotation
    #endregion

    internal float deltaV = 0; // normally used to check if we have walked the specified amount and will stop the movement

    #region AnimatorThings
    [SerializeField]
    internal Animator animator;
    [SerializeField]
    internal Rigidbody rigidBody;
    internal float animRotSpeed = 0.5f;
    #endregion
    public enum AgentState { Walking, Turning, Stationary };
    public struct AgentAction
    {
        public AgentState agentState;
        public int direction;
        public int repeatX;
    }

    /// <summary>
    /// Function to create and return a new AgentAction with all of the parameters
    /// </summary>
    /// <param name="agentState"></param>
    /// <param name="dir"></param>
    /// <param name="repeatX"></param>
    /// <returns></returns>
    public AgentAction GenAgentAction(AgentState agentState, int dir, int repeatX)
    {
        var AA = new AgentAction();
        AA.agentState = agentState;
        AA.direction = dir;
        AA.repeatX = repeatX;
        return AA;
    }

    /// <summary>
    /// Changes the animator flags for different agentStates
    /// Animator Updater needs to be called in Update for every new movement/walking script that derives off.
    /// Handles Stationary, Turning and walking animations
    /// </summary>
    internal void AnimatorUpdater()
    {
        if (agentState == AgentState.Stationary)
        {
            animator.SetBool("Grounded", true);
            animator.SetFloat("MoveSpeed", 0);
        }
        else if (agentState == AgentState.Turning)
        {
            animator.SetFloat("MoveSpeed", animRotSpeed);
        }
        else if (agentState == AgentState.Walking)
        {
            animator.SetFloat("MoveSpeed", walkSpeed);
        }
    }

    /// <summary>
    /// Use this to subscribe an empty function to the DPAD ONClick event
    /// if there is no event subscribed to it for a certain type of movement an error will
    /// pop up unless something is subscribed to it
    /// </summary>
    /// <param name="a"></param>
    /// <param name="d"></param>
    internal void EmptySubscription(AgentState a, int d)
    {
        return;
    }

    public virtual void AddAction(AgentState agentstate, int dir) { }

    /// <summary>
    /// Checks if the neighboring cell of specified index can be moved to
    /// Locations that cannot be moved to, have props on them (tree, lamp post, etc) or are hills/water
    /// Cards do not count as props and thoselocations can be moved to.
    /// </summary>
    /// <param name="dir">neighborIndex that you want to check</param>
    /// <returns></returns>
    public bool CanMove(HexCell nextLocation, int dir)
    {
        if (!hexgrid.isPastEdge(nextLocation) &&
            (nextLocation.landType == LandType.Grass || nextLocation.landType == LandType.Path))
        {
            if (!propPlacement.propLocs.Contains(nextLocation) ||
                propPlacement.walkableLocs.Contains(nextLocation))
            {
                return true;
            }
            return false;
        }
        return false;
    }

    public virtual void Update() { }
    public virtual void FixedUpdate() { }

    protected IEnumerator BackgroundUpdate()
    {
        while (true)
        {
            if (!webSocketManager.applicationHasFocus)
            {
                Update();
                FixedUpdate();
            }
            yield return null;
        }
    }

    protected void StartGamePlay()
    {
      started = true;
      //StartCoroutine("BackgroundUpdate");
    }

    protected void StopGamePlay()
    {
      started = false;
      //StopCoroutine("BackgroundUpdate");
    }
}
