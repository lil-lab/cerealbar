using System.Collections;
using System.Collections.Generic;
using UnityEngine;


[System.Serializable]
public class HexDist  {
    [System.Serializable]
    public class HexInfo
    {
        public int[] p;
        public float v;
    }

    public HexInfo[] hexInfo;
}
