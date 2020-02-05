using System.Collections;
using System.Collections.Generic;
using UnityEngine;


[System.Serializable]
public class StateDelta  {
    [System.Serializable]
    public class AgentInfo
    {
        public int[] pos;
        public int rot;
    }

    [System.Serializable]
    public class CardInfo
    {
        public int[] pos;
        public int count;
        public string color;
        public string shape;
        public bool sel;
    }

    public AgentInfo lead;
    public AgentInfo follow;
    public CardInfo[] cards;
}
