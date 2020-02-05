using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[System.Serializable]
public class EndOfGameData  {

    //Trying to be generic to fit all the different types of movement 
    [System.Serializable]
    public class Log
    {
        public string log; //"mf, mb, rr, rl, stop,some instruction"
        public float timeCalled;
    }

    public class FeedBack
    {
        public bool good;
        public float timeCalled;
    }


    public int seed;
    public float timeTaken;
    public int gameScore;
    public MovementType.ControlType humanControlType;
    public MovementType.ControlType agentControlType;


    public Log[] humanActions;
    public Log[] agentInstructions; 

    public FeedBack[] agentFeedback;

}
