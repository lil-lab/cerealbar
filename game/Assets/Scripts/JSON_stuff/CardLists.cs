using System.Collections;
using System.Collections.Generic;
using UnityEngine;


[System.Serializable]
public class CardLists {
    [System.Serializable]
    public class CardInfo
    {
        public int[] pos;
        public int count;
        public string color;
        public string shape;
        public bool sel;
    }

    public CardInfo[] cards;
}
