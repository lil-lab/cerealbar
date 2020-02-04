using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Agent movement is continous (moves when the key is held down, stops when key is released)
/// </summary>
public class ContinuousControl : ActionInformation
{
    private DataCollection.KeyMovement currentMovement;
    [HideInInspector]
    public bool keyDown = false;

    #region Unity event functions

    void OnEnable()
    {
    }

    void OnDisable()
    {
    }

    void Start()
    {
        timeKeeper = FindObjectOfType<TimeKeeper>();
        dataCollection = GetComponent<DataCollection>();
        animator = GetComponent<Animator>();
        rigidBody = GetComponent<Rigidbody>();
    }

    public override void Update()
    {
        AnimatorUpdater();
        InputLogger();
    }

    public override void FixedUpdate()
    {
        WalkUpdate();
        RotateUpdate();
    }
    #endregion

    /// <summary>
    /// Called in Update - checks for the keydowns and ups to set movement flags
    /// </summary>
    private void InputLogger()
    {
        if (!timeKeeper.isPaused && tag != "Agent")
        {
            if (!keyDown)
            {
                if (Input.GetKeyDown(KeyCode.RightArrow))
                {
                    SetKeyDown("right");
                }
                else if (Input.GetKeyDown(KeyCode.LeftArrow))
                {
                    SetKeyDown("left");
                }
                else if (Input.GetKeyDown(KeyCode.UpArrow))
                {
                    SetKeyDown("forward");
                }
                else if (Input.GetKeyDown(KeyCode.DownArrow))
                {
                    SetKeyDown("back");
                }
            }

            if (Input.GetKeyUp(KeyCode.RightArrow))
            {
                FinishMovement("right");
            }
            else if (Input.GetKeyUp(KeyCode.LeftArrow))
            {
                FinishMovement("left");
            }
            else if (Input.GetKeyUp(KeyCode.UpArrow))
            {
                FinishMovement("forward");
            }
            else if (Input.GetKeyUp(KeyCode.DownArrow))
            {
                FinishMovement("back");
            }
        }
    }

    /// <summary>
    /// Used for onscreen DPAD (see HoldRelease Script for UI). Like the inputlogger.
    /// starts a new log for datacollection
    /// </summary>
    /// <param name="dirkey">"right | left |forward| back"</param>
    public void SetKeyDown(string dirkey)
    {
        keyDown = true;
        currentMovement = new DataCollection.KeyMovement();
        currentMovement.keyDownTime = timeKeeper.gameTime - timeKeeper.initSec;
        currentMovement.direction = dirkey;
        if (dirkey == "right" || dirkey == "left")
        {
            if (dirkey == "right")
                rotVal = 1;
            else
                rotVal = -1;
            agentState = AgentState.Turning;
        }
        else
        {
            if (dirkey == "forward")
                walkVal = 1;
            else
                walkVal = -1;

            agentState = AgentState.Walking;
        }
    }

    /// <summary>
    /// For DPAD movement (See holdRelease script for UI).
    /// When UI button is released, changes agent flags, to stationary, any movement is done and update and adds a complete data collection entry
    /// </summary>
    /// <param name="dirkey"></param>
    public void FinishMovement(string dirkey)
    {
        if (dirkey != currentMovement.direction)
        {
            return;
        }
        keyDown = false;
        agentState = AgentState.Stationary;
        currentMovement.keyUpTime = timeKeeper.gameTime - timeKeeper.initSec;
    }
    #region movement Updaters
    /// <summary>
    /// Called in Update(). When agent state is set to Walking, does the maths for movement and updates position
    /// </summary>
    private void WalkUpdate()
    {
        if (agentState == AgentState.Walking)
        {
            var move = transform.forward * m_interpolation * Time.deltaTime * walkVal;
            transform.position += move;
            deltaV += Vector3.Magnitude(move);
        }
    }

    /// <summary>
    /// Called in Update(). When agent state is set to rotating, updates the agents rotation
    /// </summary>
    private void RotateUpdate()
    {
        if (agentState == AgentState.Turning)
        {
            var r = rotateMoveSpeed * Time.deltaTime;
            deltaV += r;
            transform.Rotate(0, r * rotVal, 0);
        }
    }
    #endregion
}
