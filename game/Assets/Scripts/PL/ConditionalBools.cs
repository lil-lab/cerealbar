using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Note: I have no idea what to call this script 
/// or any of its variables 
/// </summary>
public class ConditionalBools : MonoBehaviour
{

    public enum GameBools { Near, NotNear, NotAtEdge, AtEdge };
    private GameBools? calledBool = null; // makes calledBool a nullable obj
    private GameObject clickedObj; // the one we want to be near
    private GameObject currentlyNearObj; // the one we are actually near

    public delegate void OnGBoolMetHandler();
    public static event OnGBoolMetHandler OnGBoolMetEvent;
    public List<GameObject> currentlyCollidingList = new List<GameObject>();

    public static void InvokeGBoolMet()
    {
        OnGBoolMetEvent(); //maybe subscribe queued control to this 
    }

    void OnTriggerEnter(Collider collision)
    {
        currentlyCollidingList.Add(collision.gameObject);
        // is BorderCommand a lie?
        currentlyNearObj = collision.gameObject;

        if(clickedObj != null && collision.gameObject == clickedObj)
        {
            //collided with referenced object - create some event 
            this.calledBool = null;
            clickedObj = null;
            InvokeGBoolMet();
        }
    }


    void OnTriggerExit(Collider collision)
    {
        currentlyCollidingList.Remove(collision.gameObject);

        currentlyNearObj = null;
    }

    /// <summary>
    /// CB could be edge conditional which we do not need so set the newobj
    /// </summary>
    /// <param name="calledBool"></param>
    /// <param name="clickedObj"></param>
    public void SetCB(GameBools calledBool, GameObject clickedObj)
    {
        this.calledBool = calledBool;
        this.clickedObj = clickedObj;
        // check if currently satisfied
        // if not near - check if near 
        // if near - check if not near then invoke 
    }
    /// <summary>
    /// More for the edge condition where we wil not need to set an obj
    /// </summary>
    /// <param name="calledConditional"></param>
    public void SetCB(GameBools calledConditional)
    {
        this.calledBool = calledConditional;
    }

    //TODO
    // Note, need to check if the current calledbool Gamebool is Near
    private bool IsNear()
    {
        if (currentlyNearObj != clickedObj && this.calledBool != null)
        {
            return false;
        }
        return true;
    }

    //TODO
    private bool IsNotNear()
    {
        if (currentlyNearObj == clickedObj) // now near
        {
            return false;
        }
        return true;
    }
}

