using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

/// <summary>
/// Applied to each button on the DPAD,
/// Identifies which button does what functionality and applies respective types of movement functions/flags
/// </summary>
public class HoldRelease : MonoBehaviour, IPointerDownHandler, IPointerUpHandler
{
    public enum DPADInput { Up, Down, Left, Right };
    public DPADInput dpadButton = DPADInput.Up;
    public ContinuousControl continuousControl;

    void Start()
    {
        continuousControl = FindObjectOfType<ContinuousControl>();
        if (!continuousControl.isActiveAndEnabled)
        {
            this.enabled = false; //need this for if the movement type is not Continuous Control
        }
    }

    /// <summary>
    /// Checks if pointer is down on this element and calls the movement setting functions in the Continuous Control script 
    /// </summary>
    /// <param name="eventData"></param>
    public void OnPointerDown(PointerEventData eventData)
    {
        if (!continuousControl.timeKeeper.isPaused)
        {
            if (!continuousControl.keyDown)
            {
                switch (dpadButton)
                {
                    case DPADInput.Up:
                        continuousControl.SetKeyDown("forward");
                        break;
                    case DPADInput.Down:
                        continuousControl.SetKeyDown("back");
                        break;
                    case DPADInput.Left:
                        continuousControl.SetKeyDown("left");
                        break;
                    case DPADInput.Right:
                        continuousControl.SetKeyDown("right");
                        break;
                    default:
                        break;
                }
            }
        }
    }

    /// <summary>
    /// When pointer is released on this element- calls finish movement to set all the flags to stop movement that was set
    /// </summary>
    /// <param name="eventData"></param>
    public void OnPointerUp(PointerEventData eventData)
    {
        if (!continuousControl.timeKeeper.isPaused)
        {
            switch (dpadButton)
            {
                case DPADInput.Up:
                    continuousControl.FinishMovement("forward");
                    break;
                case DPADInput.Down:
                    continuousControl.FinishMovement("back");
                    break;
                case DPADInput.Left:
                    continuousControl.FinishMovement("left");
                    break;
                case DPADInput.Right:
                    continuousControl.FinishMovement("right");
                    break;
                default:
                    break;
            }
        }
    }
}
