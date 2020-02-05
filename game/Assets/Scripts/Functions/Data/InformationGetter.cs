using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;

/// <summary>
/// This script will be called from SocketStarter
/// All the information needed to be sent is collected and accessible here
/// Note that all vector3's are sent as strings in order to concat the amount of digits that get sent over the socket
/// </summary>
public class InformationGetter : MonoBehaviour
{
    public PropPlacement propPlacement;
    public HexGrid hexGrid;
    private InitialInformation initialInfo;
    public Screenshot overheadScreenshot;
    public Texture screenshotTx;

    public GameObject[] agents;

    private GameObject human;
    public Screenshot humanScreenshot;
    private EyesightView humanScope;
    public MovementType humanMoveType;

    private GameObject agent;
    public Screenshot agentScreenshot;
    private EyesightView agentScope;
    public MovementType agentMoveType;

    public byte[] tempPic;

    #region image Event
    public delegate void OnImageHandler();
    public static event OnImageHandler OnImageTakenEvent;

    public static void InvokeImageTaken()
    {
        OnImageTakenEvent();
    }
    #endregion

    #region Unity Event Functions
    void Awake()
    {
        if (!propPlacement)
            propPlacement = FindObjectOfType<PropPlacement>();
        if (!hexGrid)
            hexGrid = FindObjectOfType<HexGrid>();
    }

    void OnEnable()
    {
        PropPlacement.OnMapCompleteEvent += GetScreenshotScripts;
        PropPlacement.OnMapCompleteEvent += GetAgents;
    }

    void OnDisable()
    {
        PropPlacement.OnMapCompleteEvent -= GetScreenshotScripts;
        PropPlacement.OnMapCompleteEvent -= GetAgents;
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Space))
        {
            // var l = GetEyesightObjs("Human");
        }
    }

    #endregion

    #region Initial Getters
    private void GetScreenshotScripts()
    {

        var human = GameObject.FindGameObjectWithTag("Human");
        if (human)
            humanScreenshot = human.GetComponent<Screenshot>();

        var a = GameObject.FindGameObjectWithTag("Agent");
        if (a)
            agentScreenshot = a.GetComponent<Screenshot>();

    }

    private void GetAgents()
    {
        var moveScripts = FindObjectsOfType<MovementType>();
        agents = new GameObject[moveScripts.Length];
        for (int i = 0; i < agents.Length; i++)
        {
            agents[i] = moveScripts[i].gameObject;
            if (agents[i].tag == "Human")
            {
                human = agents[i];
                humanScope = human.GetComponentInChildren<EyesightView>();
                humanMoveType = human.GetComponent<MovementType>();
            }
            else if (agents[i].tag == "Agent")
            {
                agent = agents[i];
                agentScope = agent.GetComponentInChildren<EyesightView>();
                agentMoveType = agent.GetComponent<MovementType>();
            }
        }
    }
    #endregion

    public string GetAgentMoveInfo(string agentTag)
    {
        var agentInfo = new AgentInformation();
        agentInfo.agentName = agentTag;
        var agentGO = Array.Find(agents, x => x.tag == agentTag);

        agentInfo.agPosV3 = agentGO.transform.position.ToString("f3");
        agentInfo.agRotV3 = agentGO.transform.eulerAngles.ToString("f3");
        agentInfo.currentCardInfo = GetCardInformation();
        agentInfo.eyesightInfo = GetEyesightObjs(agentTag);

        return JsonUtility.ToJson(agentInfo);
    }

    public AgentInformation.EyesightInfo[] GetEyesightObjs(string agent)
    {
        var tempSightList = new List<AgentInformation.EyesightInfo>();
        EyesightView playerScope;
        if (agent == "Human")
        {
          playerScope = humanScope;
        }
        else //agent == "Agent"
        {
          playerScope = agentScope;
        }
        foreach (var thing in playerScope.objectsInEyesight)
        {
            if (thing != null){
                var eyesight = new AgentInformation.EyesightInfo();
                var hexCell = thing.GetComponent<HexCell>();
                if (hexCell != null)
                {
                  eyesight.prop = hexCell.landType + " cell";
                }
                else
                {
                  eyesight.prop = thing.name;
                }
                eyesight.propPosV3 = thing.transform.position.ToString("f3");
                eyesight.propRotV3 = thing.transform.eulerAngles.ToString("f3");

                tempSightList.Add(eyesight);
            }
        }
        return tempSightList.ToArray();
    }



    private InitialInformation.PropPlacementInfo[] GetPropPlacementInformation()
    {
        var propsList = new List<InitialInformation.PropPlacementInfo>();
        for (int i = 0; i < propPlacement.props.Count; i++)
        {
            var currentProp = new InitialInformation.PropPlacementInfo();

            currentProp.pName = propPlacement.props[i].name;

            currentProp.posV3 = propPlacement.props[i].transform.position.ToString("f3");
            currentProp.rotV3 = propPlacement.props[i].transform.rotation.eulerAngles.ToString("f3");

            propsList.Add(currentProp);
        }
        return propsList.ToArray();
    }

    public InitialInformation.CardInfo[] GetCardInformation()
    {
        var cardList = new List<InitialInformation.CardInfo>();
        for (int i = 0; i < propPlacement.cards.Length; i++)
        {
            var currentCardInfo = new InitialInformation.CardInfo();
            var cardproperties = propPlacement.cards[i].GetComponent<CardProperties>();
            currentCardInfo.posV3 = cardproperties.transform.position.ToString("f3");
            currentCardInfo.num = cardproperties.count;
            currentCardInfo.color = cardproperties.color.ToString();
            currentCardInfo.shape = cardproperties.shape.ToString();

            var outline = propPlacement.cards[i].GetComponent<cakeslice.Outline>();
            currentCardInfo.notSelected = outline.eraseRenderer;

            cardList.Add(currentCardInfo);
        }

        return cardList.ToArray();
    }

    /// <summary>
    /// Gets the starting map information
    /// This includes:
    /// HexGrid information: real coordiantes, grid coordinates, landtyoe
    /// PropPlacement: Prop name, real coordinates, real rotation
    /// Card Information: real coordinates, number, color, shape, active state
    /// </summary>
    /// <returns></returns>
    public string GetMapInfo()
    {
        var initialInfo = new InitialInformation();
        initialInfo.seed = hexGrid.GetMapSeed();
        initialInfo.hexCellInfo = GetGridInformation();
        initialInfo.propPlacementInfo = GetPropPlacementInformation();
        initialInfo.cardInfo = GetCardInformation();
        return JsonUtility.ToJson(initialInfo);
    }

    public string GetStateDelta()
    {
        // Just return the location/rotation of the players and the cards information
        List<string> cardStringArray = new List<string>();
        for (int i = 0; i < propPlacement.cards.Length; i++) {
            if (propPlacement.cards[i] != null) {
                var outline = propPlacement.cards[i].GetComponent<cakeslice.Outline>();
                bool notSelected = outline.eraseRenderer;
                string selectionInfo = notSelected ? "unselected" : "selected";

                cardStringArray.Add("\"" + selectionInfo + " " + CardProperties.Stringify(propPlacement.cards[i]) + "\"");
            }
        }

        var cardString = String.Join(", ", cardStringArray.ToArray());
        
        var leaderPosV3 = propPlacement.props[propPlacement.props.Count-2].transform.position.ToString("f3");
        var leaderRotV3 = propPlacement.props[propPlacement.props.Count-2].transform.rotation.eulerAngles.ToString("f3");
        var followerPosV3 = propPlacement.props[propPlacement.props.Count-1].transform.position.ToString("f3");
        var followerRotV3 = propPlacement.props[propPlacement.props.Count-1].transform.rotation.eulerAngles.ToString("f3");

        string finalString = "";
        finalString += "{\"leader\": {\"position\": \"" + leaderPosV3 + "\", \"rotation\": \"" + leaderRotV3 + "\"},";
        finalString += "\"follower\": {\"position\": \"" + followerPosV3 + "\", \"rotation\": \"" + followerRotV3 + "\"},";
        finalString += "\"cards\": [" + cardString + "]}";

        return finalString;
    }


    private InitialInformation.HexCellInfo[] GetGridInformation()
    {
        var hexCellInfoList = new List<InitialInformation.HexCellInfo>();
        for (int i = 0; i < hexGrid.hexCells.Length; i++)
        {
            var cellInfo = new InitialInformation.HexCellInfo();
            cellInfo.posV3 = hexGrid.hexCells[i].transform.position.ToString("f3");
            cellInfo.hexX = hexGrid.hexCells[i].coordinates.X;
            cellInfo.hexZ = hexGrid.hexCells[i].coordinates.Z;
            cellInfo.lType = hexGrid.hexCells[i].landType.ToString();
            hexCellInfoList.Add(cellInfo);
        }
        return hexCellInfoList.ToArray();
    }
    #region Images

    /// <summary>
    /// strings "agent", "human","overhead"
    /// </summary>
    /// <param name="view"></param>
    /// <returns>byte array of the image </returns>
    public byte[] GetScreenShotImageView(string view)
    {
        var screenshot = new byte[1];
        if (view == "agent")
            screenshot = agentScreenshot.GetScreenShotBA();
        else if (view == "human")
            screenshot = humanScreenshot.GetScreenShotBA();
        else if (view == "overhead")
            screenshot = overheadScreenshot.GetScreenShotBA();
        return screenshot;

    }

    public IEnumerator GetPOVImg(string view)
    {
        yield return new WaitForEndOfFrame();
        tempPic = GetScreenShotImageView(view);
        InvokeImageTaken();
    }
    #endregion

}
