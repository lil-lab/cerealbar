using System.Collections;
using System.Collections.Generic;
using UnityEngine;


[System.Serializable]
public class InitialInformation  {
    [System.Serializable]
    public class HexCellInfo
    {
        public string posV3;
        public int hexX;
        public int hexZ;
        public string lType;
    }

    [System.Serializable]
    public class PropPlacementInfo
    {
        public string pName;
        public string posV3;
        public string rotV3;
    }

    [System.Serializable]
    public class CardInfo
    {
        public string posV3;
        public int num;
        public string color;
        public string shape;
        public bool notSelected;
    }


    public int seed;
    public HexCellInfo[] hexCellInfo;
    public PropPlacementInfo[] propPlacementInfo;
    public CardInfo[] cardInfo;
}
