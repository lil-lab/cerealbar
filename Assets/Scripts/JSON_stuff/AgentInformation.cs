using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Information for a specific agent at called point 
/// </summary>
[System.Serializable]
public class AgentInformation  {

    [System.Serializable]
    public struct EyesightInfo
    {
        public string prop;
        public string propPosV3;
        public string propRotV3; //euler
    }

    public string agentName;
    public string agPosV3;
    public string agRotV3;
    public EyesightInfo[] eyesightInfo;
    public InitialInformation.CardInfo[] currentCardInfo;

}
