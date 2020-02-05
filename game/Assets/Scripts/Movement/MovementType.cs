using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

[RequireComponent(typeof(QueuedControl), typeof(ContinuousControl), typeof(HexToHexControl))]
public class MovementType : MonoBehaviour
{
    public enum ControlType { DiscreteQueued, Continuous, HexToHex, HexQueued, Discrete, TurnBased, Simulated, Replay };
    //public enum ControlType { HexToHex, Simulated };
    public ControlType controlType;
    public bool turnBased;
    public string myCharacter;

    private QueuedControl discreteQueued;
    private ContinuousControl continousControl;
    private HexToHexControl hexesControl;
    private DiscreteMovement discreteControl;
    private HexQueuedCntrl hexQueuedControl;
    private TurnBasedControl turnControl;
    private SimulatedControl simulatedControl;
    private ReplayControl replayControl;

    void Awake()
    {
        discreteQueued = GetComponent<QueuedControl>();
        continousControl = GetComponent<ContinuousControl>();
        hexesControl = GetComponent<HexToHexControl>();
        discreteControl = GetComponent<DiscreteMovement>();
        hexQueuedControl = GetComponent<HexQueuedCntrl>();
        turnControl = GetComponent<TurnBasedControl>();
        simulatedControl = GetComponent<SimulatedControl>();
        replayControl = GetComponent<ReplayControl>();
    }

    public void SetControl(string mainCharacter)
    {

        #if SIMULATING
        controlType = ControlType.Simulated;
        #endif

        if (Replay.replaying)
        {
          controlType = ControlType.Replay;
        }

        DeactivateAllMovements();

        hexesControl.mainCharacter = mainCharacter;
        hexQueuedControl.mainCharacter = mainCharacter;
        turnControl.mainCharacter = mainCharacter;

        switch (controlType)
        {
            case ControlType.DiscreteQueued:
                discreteQueued.enabled = true;
                discreteQueued.myCharacter = myCharacter;
                discreteQueued.SetTurnBased(turnBased);
                break;
            case ControlType.Continuous:
                continousControl.enabled = true;
                continousControl.myCharacter = myCharacter;
                continousControl.SetTurnBased(turnBased);
                break;
            case ControlType.HexToHex:
                hexesControl.enabled = true;
                hexesControl.myCharacter = myCharacter;
                hexesControl.SetTurnBased(turnBased);
                break;
            case ControlType.HexQueued:
                hexQueuedControl.enabled = true;
                hexQueuedControl.myCharacter = myCharacter;
                hexQueuedControl.SetTurnBased(turnBased);
                break;
            case ControlType.Discrete:
                discreteControl.enabled = true;
                discreteControl.SetTurnBased(turnBased);
                discreteControl.myCharacter = myCharacter;
                break;
            case ControlType.TurnBased:
                turnControl.enabled = true;
                turnControl.SetTurnBased(turnBased);
                turnControl.myCharacter = myCharacter;
                break;
            case ControlType.Simulated:
                simulatedControl.enabled = true;
                simulatedControl.SetTurnBased(turnBased);
                simulatedControl.myCharacter = myCharacter;
                break;
            case ControlType.Replay:
                replayControl.enabled = true;
                replayControl.SetTurnBased(false);
                replayControl.myCharacter = myCharacter;
                break;
            default:
                break;
        }
    }

    public void ActivateHexToHex()
    {
        hexesControl.enabled = true;
    }

    private void DeactivateAllMovements()
    {
        discreteQueued.enabled = false;
        discreteControl.enabled = false;
        continousControl.enabled = false;
        hexesControl.enabled = false;
        hexQueuedControl.enabled = false;
        turnControl.enabled = false;
        simulatedControl.enabled = false;
        replayControl.enabled = false;
    }



}
