using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// This is what makes the bodies move when getting commands from python
/// each agent gets an ExternalActionHandler and adds the specified movement for that agent
/// </summary>
public class ExternalActionHandler : MonoBehaviour
{
    private MovementType mv;
    private DiscreteMovement discreteMovement;
    private HexQueuedCntrl hexQueuedMovement;
    private HexToHexControl hexhexControl;
    private QueuedControl disQueuedMovement;
    private TurnBasedControl turnControl;
    private SimulatedControl simulatedControl;
    private ReplayControl replayControl;

    // Have external be listening for events- depending on the string attached?

    void Awake()
    {
        mv = GetComponent<MovementType>();
        hexQueuedMovement = GetComponent<HexQueuedCntrl>();
        discreteMovement = GetComponent<DiscreteMovement>();
        hexhexControl = GetComponent<HexToHexControl>();
        disQueuedMovement = GetComponent<QueuedControl>();
        turnControl = GetComponent<TurnBasedControl>();
        simulatedControl = GetComponent<SimulatedControl>();
        replayControl = GetComponent<ReplayControl>();
    }

    //note - not doing the continuous one - highly likely not going to be using that
    public string AddAction(ActionInformation.AgentState state, int dir)
    {
        string ret = "";
        switch (mv.controlType)
        {
            case MovementType.ControlType.DiscreteQueued:
                disQueuedMovement.AddAction(state, dir);
                break;
            case MovementType.ControlType.Discrete:
                discreteMovement.AddAction(state, dir);
                break;

            case MovementType.ControlType.HexQueued:
                hexQueuedMovement.AddAction(state, dir);
                break;
            case MovementType.ControlType.HexToHex:
                hexhexControl.AddAction(state, dir);
                break;
            case MovementType.ControlType.TurnBased:
                turnControl.AddAction(state,dir);
                break;
            case MovementType.ControlType.Simulated:
                ret = simulatedControl.DoAction(state,dir);
                break;

        }
        return ret;
    }

    public void AddExternalAction(ActionInformation.AgentState state, int dir)
    {
      switch (mv.controlType)
      {
          case MovementType.ControlType.DiscreteQueued:
              break;
          case MovementType.ControlType.Discrete:
              break;

          case MovementType.ControlType.HexQueued:
              hexQueuedMovement.AddExternalAction(state, dir);
              break;
          case MovementType.ControlType.HexToHex:
              hexhexControl.AddExternalAction(state, dir);
              break;
          case MovementType.ControlType.TurnBased:
              turnControl.AddExternalAction(state,dir);
              break;
          case MovementType.ControlType.Simulated:
              simulatedControl.DoAction(state,dir);
              break;
          case MovementType.ControlType.Replay:
              replayControl.AddExternalAction(state,dir);
              break;

      }
    }

    public void DoExternalActions()
    {
      switch (mv.controlType)
      {
        case MovementType.ControlType.Replay:
          replayControl.DoExternalActions();
          break;
      }
    }

    public void StopClearAll()
    {
        switch (mv.controlType)
        {
            case MovementType.ControlType.DiscreteQueued:
                discreteMovement.StopClearAll();
                break;
            case MovementType.ControlType.HexQueued:
                hexQueuedMovement.StopClearAll();
                break;
            //TODO - HEXHEX
            //TODO DISCRETE
        }
    }

    public void GetTurn()
    {
      switch (mv.controlType)
      {
          case MovementType.ControlType.DiscreteQueued:
              disQueuedMovement.canMove = true;
              disQueuedMovement.canAct = true;
              break;
          case MovementType.ControlType.Discrete:
              discreteMovement.canMove = true;
              discreteMovement.canAct = true;
              break;
          case MovementType.ControlType.HexQueued:
              hexQueuedMovement.canMove = true;
              hexQueuedMovement.canAct = true;
              break;
          case MovementType.ControlType.HexToHex:
              hexhexControl.canMove = true;
              hexhexControl.canAct = true;
              break;
          case MovementType.ControlType.TurnBased:
              turnControl.canMove = true;
              turnControl.canAct = true;
              break;

      }
    }

    public void GiveTurn()
    {
      switch (mv.controlType)
      {
          case MovementType.ControlType.DiscreteQueued:
              disQueuedMovement.canMove = false;
              disQueuedMovement.canAct = false;
              break;
          case MovementType.ControlType.Discrete:
              discreteMovement.canMove = false;
              discreteMovement.canAct = false;
              break;
          case MovementType.ControlType.HexQueued:
              hexQueuedMovement.canMove = false;
              hexQueuedMovement.canAct = false;
              break;
          case MovementType.ControlType.HexToHex:
              hexhexControl.canMove = false;
              hexhexControl.canAct = false;
              break;
          case MovementType.ControlType.TurnBased:
              turnControl.canMove = false;
              turnControl.canAct = false;
              break;

      }
    }

    public void NoMoves()
    {
      switch (mv.controlType)
      {
          case MovementType.ControlType.DiscreteQueued:
              disQueuedMovement.canMove = false;
              break;
          case MovementType.ControlType.Discrete:
              discreteMovement.canMove = false;
              break;
          case MovementType.ControlType.HexQueued:
              hexQueuedMovement.canMove = false;
              hexQueuedMovement.StopClearAll();
              break;
          case MovementType.ControlType.HexToHex:
              hexhexControl.canMove = false;
              break;
          case MovementType.ControlType.TurnBased:
              turnControl.canMove = false;
              break;

      }
    }
}
