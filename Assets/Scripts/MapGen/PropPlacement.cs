using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using System.Linq;

public class PropPlacement : MonoBehaviour
{
    private HexGrid hexgrid;
    [Tooltip("Check in the ScriptableObjects Folder or create a new ObjectDB and fill it with your own items ")]
    public ObjectDB StructuresDB;
    public ObjectDB TreesDB;
    public ObjectDB PathObjectsDB;
    public GameObject[] players;
    public GameObject human;
    public GameObject agent;
    public int numStructures;
    public int numTrees;
    public int numPathObjects;

    private float[] structureRotations = { 30f, 90f, 150f, 210f, 270f, 330f };

    public HashSet<HexCell> propLocs = new HashSet<HexCell>();
    public HashSet<HexCell> walkableLocs = new HashSet<HexCell>();

    public GameObject[] cards;
    private CardGenerator cardGenerator;
    private SetGame setGame;

    private GameObject pG;
    [HideInInspector]
    public List<GameObject> props = new List<GameObject>();
    private List<HexCell> preferredCells = new List<HexCell>();

    private int placementsTodo =  5; //number of placement events subscribed to OnPathsFinishedEvent #########
    public delegate void OnMapCompleteHandler();
    public static event OnMapCompleteHandler OnMapCompleteEvent;


    public delegate void OnImReadyToStartGamePlayHandler();
    public static event OnImReadyToStartGamePlayHandler OnReadyToStartGamePlayEvent;


    public static void InvokeMapCompleted()
    {
        OnMapCompleteEvent();
        OnReadyToStartGamePlayEvent();
    }

    void Awake()
    {
        pG = new GameObject("Props");
        hexgrid = GetComponent<HexGrid>();
        cardGenerator = GetComponent<CardGenerator>();
        setGame = FindObjectOfType<SetGame>();
        if (StructuresDB == null)
        {
            Debug.LogErrorFormat("Missing LargeStructures ObjectDB ScriptableObject");
        }
        if (TreesDB == null)
        {
            Debug.LogErrorFormat("Missing trees objectDB scriptableobject");
        }
        if (PathObjectsDB == null)
        {
            Debug.LogErrorFormat("Missing trees pathobjectsdb scriptableobject");
        }

    }

    void OnEnable()
    {
        props.Clear();
        // subscribing placement functions to the event when all the paths are finished generating
        HexGrid.OnPathsFinishedEvent += PlaceTrees;
        HexGrid.OnPathsFinishedEvent += PlaceStructures;
        HexGrid.OnPathsFinishedEvent += PlacePathObjects;
        HexGrid.OnPathsFinishedEvent += PlaceCards;
        HexGrid.OnPathsFinishedEvent += PlacePlayers;

        Restarter.OnRestartEvent += ClearCards;
        Restarter.OnRestartEvent += ClearProps;
        Restarter.OnRestartEvent += ResetPlacementNum;
    }

    void OnDisable()
    {
        HexGrid.OnPathsFinishedEvent -= PlaceTrees;
        HexGrid.OnPathsFinishedEvent -= PlaceStructures;
        HexGrid.OnPathsFinishedEvent -= PlacePathObjects;
        HexGrid.OnPathsFinishedEvent -= PlaceCards;
        HexGrid.OnPathsFinishedEvent -= PlacePlayers;

        Restarter.OnRestartEvent -= ClearCards;
        Restarter.OnRestartEvent -= ClearProps;
        Restarter.OnRestartEvent -= ResetPlacementNum;

    }

    #region PopulatingPreferredLocations

    /// <summary>
    /// sets all grasscells to just have all possible grass locations
    /// </summary>
    private void RepopulateWithAllGrass()
    {
        preferredCells.Clear();
        preferredCells = hexgrid.hexCells.Where(hexcell => hexcell.landType == LandType.Grass).ToList();

    }


    /// <summary>
    /// sets all grasscells to just have all possible grass locations
    /// </summary>
    private void RepopWPathCells()
    {
        preferredCells.Clear();
        preferredCells = hexgrid.hexCells.Where(hexcell => hexcell.landType == LandType.Path).ToList();
    }

    /// <summary>
    /// Large structures have a slightly more complicated population preference
    /// They prefer paths and water, but can still be placed in other locations
    /// </summary>
    private void RepopulateGrassWithStructurePreferences()
    {
        preferredCells.Clear();
        preferredCells = hexgrid.hexCells.Where(hexcell => hexcell.landType == LandType.Grass).ToList();
        var favorLocs = hexgrid.hexCells.Where(hexcell => hexcell.landType == LandType.Path).ToList();
        favorLocs.AddRange(hexgrid.hexCells.Where(hexcell => hexcell.landType == LandType.Water).ToList());

        for (int i = 0; i < favorLocs.Count; i++)
        {
            var tier1PathNeighbors = favorLocs[i].GetAllGrassNeighbors();
            foreach (var n in tier1PathNeighbors) // we can go one hexcell away from paths to give it a more natural placement
            {
                var tier2n = n.GetAllGrassNeighbors();
                preferredCells.AddRange(tier2n);
            }
            preferredCells.AddRange(tier1PathNeighbors);
        }

    }
    #endregion

    #region PlacementOfObjects

    /// <summary>
    /// Place trees with the preference that trees spawn near other trees to make small "groves"
    /// </summary>
    private void PlaceTrees()
    {
        RepopulateWithAllGrass();
        for (int i = 0; i < numTrees; i++)
        {
            var rndCell = GetRndCellFromPreferred();
            propLocs.Add(rndCell);
            var neighbors = rndCell.GetAllGrassNeighbors();
            if (neighbors != null)
                preferredCells.AddRange(rndCell.GetAllGrassNeighbors());
            preferredCells.RemoveAll(tc => tc == rndCell);
            var prop = Instantiate(TreesDB.GetRandomPrefab(), rndCell.transform.position, Quaternion.identity);
            var collider = prop.AddComponent(typeof(MeshCollider)) as MeshCollider;
            collider.convex = true;
            collider.isTrigger = true;
            props.Add(prop);
            prop.transform.parent = pG.transform ;
        }
        OnePlacementComplete();
    }
    /// <summary>
    /// Objects from the large structures db will be placed in the specified locations
    /// </summary>
    private void PlaceStructures()
    {
        RepopulateGrassWithStructurePreferences();
        for (int i = 0; i < numStructures; i++)
        {
            var rndCell = GetRndCellFromPreferred();
            propLocs.Add(rndCell);
            var neighbors = rndCell.GetAllGrassNeighbors();
            if (neighbors != null)
            {
                foreach (var n in neighbors) //remove surrounding neighbors as acceptable locations because we do not want to crowd the houses
                {
                    preferredCells.RemoveAll(x => x == n);
                }
            }

            preferredCells.RemoveAll(cell => cell == rndCell);
            var prop = Instantiate(StructuresDB.GetRandomPrefab(), rndCell.transform.position, Quaternion.Euler(0,structureRotations[UnityEngine.Random.Range(0, structureRotations.Count())],0));
            // var collider = prop.AddComponent(typeof(BoxCollider)) as BoxCollider;
            var collider = prop.AddComponent(typeof(MeshCollider)) as MeshCollider;
            collider.convex = true;
            collider.isTrigger = true;
            props.Add(prop);
            prop.transform.parent = pG.transform;
        }
        OnePlacementComplete();
    }

    /// <summary>
    /// Objects from pathobjects db will be randombly placed along paths
    /// </summary>
    private void PlacePathObjects()
    {
        preferredCells.Clear();
        var favorLocs = hexgrid.hexCells.Where(hexcell => hexcell.landType == LandType.Path).ToList();

        for (int i = 0; i < favorLocs.Count; i++)
        {
            var tier1PathNeighbors = favorLocs[i].GetAllGrassNeighbors();
            preferredCells.AddRange(tier1PathNeighbors);
        }

        for (int i = 0; i < numPathObjects; i++)
        {
            var rndCell = GetRndCellFromPreferred();
            if (rndCell == null) { break ;}
            propLocs.Add(rndCell);
            preferredCells.RemoveAll(cell => cell == rndCell);
            var prop = Instantiate(PathObjectsDB.GetRandomPrefab(), rndCell.transform.position, Quaternion.identity);
            // var collider = prop.AddComponent(typeof(BoxCollider)) as BoxCollider;
            var collider = prop.AddComponent(typeof(MeshCollider)) as MeshCollider;
            collider.convex = true;
            collider.isTrigger = true;
            props.Add(prop);
            prop.transform.parent = pG.transform;
        }
        OnePlacementComplete();
    }

    /// <summary>
    /// Does not utilize any preferences - just places card anywhere on the map that is grass or path a
    /// and does not have another prop on it
    /// </summary>
    private void PlaceCards()
    {
        cards = cardGenerator.GenerateCards();
        for (int i = 0; i < cards.Length; ++i) {
            var rndGoodCell = hexgrid.GetRandomGrassOrPathCell();
            while (propLocs.Contains(rndGoodCell))
            {
                rndGoodCell = hexgrid.GetRandomGrassOrPathCell();
            }

            cards[i].transform.position = rndGoodCell.transform.position;
            propLocs.Add(rndGoodCell);
            walkableLocs.Add(rndGoodCell);

        }

        OnePlacementComplete();
    }

    private void MakeCardsTransparent() {
        for (int i = 0; i < cards.Length; ++i) {
            cards[i].GetComponent<Renderer>().material.color = new Color(1.0f, 1.0f, 1.0f, 0.5f);
        }
    }

    public void SetGoalDist(string hexDistStr) {
        // Convrt from JSON
        HexDist hexDist = JsonUtility.FromJson<HexDist>(hexDistStr);

        // First, reset the distribution's value to zero.
        for (int x = 0; x < 25; x ++)
        {
            for (int y = 0; y < 25; y ++)
            {
                HexCell hexCell = hexgrid.GetCell(x, y);
                hexCell.SetGoalDist(0.0f);
            }
        }

        // Then iterate through the sent cells and set the non-zero ones.
        for (int i = 0; i < hexDist.hexInfo.Length; i ++)
        {
            // Set the values for this hex.
            HexDist.HexInfo thisHex = hexDist.hexInfo[i];

            int[] position = thisHex.p;
            HexCell hexCell = hexgrid.GetCell(position[0], position[1]);
            hexCell.SetGoalDist(thisHex.v);
        }

        // Re-triangulate to reset the card colors
        // TODO: is this necessary?
        hexgrid.RefreshCells();
        MakeCardsTransparent();
    }

    public void SetTrajectoryDist(string hexDistStr) {
        // Convrt from JSON
        HexDist hexDist = JsonUtility.FromJson<HexDist>(hexDistStr);

        // First, reset the distribution's value to zero.
        for (int x = 0; x < 25; x ++)
        {
            for (int y = 0; y < 25; y ++)
            {
                HexCell hexCell = hexgrid.GetCell(x, y);
                hexCell.SetTrajectoryDist(0.0f);
            }
        }

        // Then iterate through the sent cells and set the non-zero ones.
        for (int i = 0; i < hexDist.hexInfo.Length; i ++)
        {
            // Set the values for this hex.
            HexDist.HexInfo thisHex = hexDist.hexInfo[i];

            int[] position = thisHex.p;
            HexCell hexCell = hexgrid.GetCell(position[0], position[1]);
            hexCell.SetTrajectoryDist(thisHex.v);
        }

        // Re-triangulate to reset the card colors
        // TODO: is this necessary?
        hexgrid.RefreshCells();
        MakeCardsTransparent();
    }

    public void SetObstacleDist(string hexDistStr) {
        // Convrt from JSON
        HexDist hexDist = JsonUtility.FromJson<HexDist>(hexDistStr);

        // First, reset the distribution's value to zero.
        for (int x = 0; x < 25; x ++)
        {
            for (int y = 0; y < 25; y ++)
            {
                HexCell hexCell = hexgrid.GetCell(x, y);
                hexCell.SetObstacleDist(0.0f);
            }
        }

        // Then iterate through the sent cells and set the non-zero ones.
        for (int i = 0; i < hexDist.hexInfo.Length; i ++)
        {
            // Set the values for this hex.
            HexDist.HexInfo thisHex = hexDist.hexInfo[i];

            int[] position = thisHex.p;
            HexCell hexCell = hexgrid.GetCell(position[0], position[1]);
            hexCell.SetObstacleDist(thisHex.v);
        }

        // Re-triangulate to reset the card colors
        // TODO: is this necessary?
        hexgrid.RefreshCells();
        MakeCardsTransparent();
    }

    public void SetAvoidDist(string hexDistStr) {
        // Convrt from JSON
        HexDist hexDist = JsonUtility.FromJson<HexDist>(hexDistStr);

        // First, reset the distribution's value to zero.
        for (int x = 0; x < 25; x ++)
        {
            for (int y = 0; y < 25; y ++)
            {
                HexCell hexCell = hexgrid.GetCell(x, y);
                hexCell.SetAvoidDist(0.0f);
            }
        }

        // Then iterate through the sent cells and set the non-zero ones.
        for (int i = 0; i < hexDist.hexInfo.Length; i ++)
        {
            // Set the values for this hex.
            HexDist.HexInfo thisHex = hexDist.hexInfo[i];

            int[] position = thisHex.p;
            HexCell hexCell = hexgrid.GetCell(position[0], position[1]);
            hexCell.SetAvoidDist(thisHex.v);
        }

        // Re-triangulate to reset the card colors
        // TODO: is this necessary?
        hexgrid.RefreshCells();
        MakeCardsTransparent();
    }

    public void AddCards(CardLists newCards) {
        int newCardIndex = 0;
        for (int i = 0; i < cards.Length; i ++)
        {
            if (cards[i] == null) {
                string cardColor = newCards.cards[newCardIndex].color;
                string cardShape = newCards.cards[newCardIndex].shape;
                int cardCount = newCards.cards[newCardIndex].count;
                int[] cardPosition = newCards.cards[newCardIndex].pos;
                bool cardSelection = newCards.cards[newCardIndex].sel;
                
                cards[i] = cardGenerator.GenCardWithProperties(cardColor, cardShape, cardCount, cardPosition[0], cardPosition[1], cardSelection);

                newCardIndex += 1;
            }
        }
    }

    public void PlaceCardsWithState(StateDelta.CardInfo[] newCards, StateDelta.AgentInfo lead, StateDelta.AgentInfo follow) {
        // Clear all cards
        setGame = FindObjectOfType<SetGame>();
        setGame.activeCards.Clear();
        ClearCards();
        for (int i = 0; i < cards.Length; i ++)
        {
            string cardColor = newCards[i].color;
            string cardShape = newCards[i].shape;
            int cardCount = newCards[i].count;
            int[] cardPosition = newCards[i].pos;
            bool cardSelection = newCards[i].sel;
            bool agentOnTop = false;

            // Reverse the card selection if the agent is on top, because the agent
            // will later collide with the object.
            if (newCards[i].pos[0] == lead.pos[0] && newCards[i].pos[1] == lead.pos[1]) {
                agentOnTop = true;
            } else if (newCards[i].pos[0] == follow.pos[0] && newCards[i].pos[1] == follow.pos[1]) {
                agentOnTop = true;
            }
            if (agentOnTop) {
                cardSelection = !cardSelection;
            }
            

            cards[i] = cardGenerator.GenCardWithProperties(cardColor, cardShape, cardCount, cardPosition[0], cardPosition[1], cardSelection);

            // If the card was not unselected, then add it to the set of selected cards
            if (cardSelection) {
                setGame.ForceCardActivation(cards[i]);
            } else {
                setGame.ForceCardDeactivation(cards[i]);
            }

        }
    }

    /// <summary>
    /// Add agents to the players array in the editor
    /// However many agents there are, they will be placed after whole map is set on an open location at 60 degrees
    /// </summary>
    private void PlacePlayers()
    {
        RepopWPathCells();
        var rndPathcell = hexgrid.GetRandomPathCell();
        for (int i=0; i < players.Count(); i++)
        {
            while (propLocs.Contains(rndPathcell))
                rndPathcell = hexgrid.GetRandomPathCell();
            var player = Instantiate(players[i], rndPathcell.transform.position, Quaternion.identity);
            player.transform.Rotate(new Vector3(0, 30, 0));
            propLocs.Add(rndPathcell);
            walkableLocs.Add(rndPathcell);
            props.Add(player);
            player.GetComponent<HexToHexControl>().currentLocation = rndPathcell;
            player.GetComponent<HexQueuedCntrl>().currentLocation = rndPathcell;
            player.GetComponent<TurnBasedControl>().currentLocation = rndPathcell;
            player.GetComponent<SimulatedControl>().currentLocation = rndPathcell;
            player.GetComponent<ReplayControl>().currentLocation = rndPathcell;
        }
        human.GetComponent<HexToHexControl>().currentLocation = props[props.Count - 2].GetComponent<HexToHexControl>().currentLocation;
        human.GetComponent<HexQueuedCntrl>().currentLocation = props[props.Count - 2].GetComponent<HexQueuedCntrl>().currentLocation;
        human.GetComponent<SimulatedControl>().currentLocation = props[props.Count - 2].GetComponent<SimulatedControl>().currentLocation;
        human.GetComponent<ReplayControl>().currentLocation = props[props.Count - 2].GetComponent<ReplayControl>().currentLocation;

        agent.GetComponent<HexToHexControl>().currentLocation = props[props.Count - 1].GetComponent<HexToHexControl>().currentLocation;
        agent.GetComponent<HexQueuedCntrl>().currentLocation = props[props.Count - 1].GetComponent<HexQueuedCntrl>().currentLocation;
        agent.GetComponent<SimulatedControl>().currentLocation = props[props.Count - 1].GetComponent<SimulatedControl>().currentLocation;
        agent.GetComponent<ReplayControl>().currentLocation = props[props.Count - 1].GetComponent<ReplayControl>().currentLocation;
        OnePlacementComplete();
    }

    public void PlacePlayersWithState(StateDelta.AgentInfo leaderInfo, StateDelta.AgentInfo followerInfo) {
        // Destroy the previous leader and follower
        HexCell leaderCell = hexgrid.GetCell(leaderInfo.pos[0], leaderInfo.pos[1]);

        props[props.Count - 2].transform.position = leaderCell.transform.localPosition;
        props[props.Count - 2].transform.eulerAngles = new Vector3(0, leaderInfo.rot, 0);
        props[props.Count - 2].GetComponent<HexToHexControl>().currentLocation = leaderCell;
        props[props.Count - 2].GetComponent<HexQueuedCntrl>().currentLocation = leaderCell;
        props[props.Count - 2].GetComponent<TurnBasedControl>().currentLocation = leaderCell;
        props[props.Count - 2].GetComponent<SimulatedControl>().currentLocation = leaderCell;
        props[props.Count - 2].GetComponent<ReplayControl>().currentLocation = leaderCell;
        int leaderDirection = (leaderInfo.rot - 30) / 60;

        props[props.Count - 2].GetComponent<SimulatedControl>().directionIndex = leaderDirection;

        // Set the follower
        HexCell followerCell = hexgrid.GetCell(followerInfo.pos[0], followerInfo.pos[1]);

        int followerDirection = (followerInfo.rot - 30) / 60;

        props[props.Count - 1].GetComponent<SimulatedControl>().directionIndex = followerDirection;

        props[props.Count - 1].transform.position = followerCell.transform.localPosition;
        props[props.Count - 1].transform.eulerAngles = new Vector3(0, followerInfo.rot, 0);
        props[props.Count - 1].GetComponent<SimulatedControl>().currentLocation = followerCell;
        
        // Set their prop info
        human.GetComponent<HexToHexControl>().currentLocation = props[props.Count - 2].GetComponent<HexToHexControl>().currentLocation;
        human.GetComponent<HexQueuedCntrl>().currentLocation = props[props.Count - 2].GetComponent<HexQueuedCntrl>().currentLocation;
        human.GetComponent<SimulatedControl>().currentLocation = props[props.Count - 2].GetComponent<SimulatedControl>().currentLocation;
        human.GetComponent<ReplayControl>().currentLocation = props[props.Count - 2].GetComponent<ReplayControl>().currentLocation;

        human.GetComponent<SimulatedControl>().directionIndex = props[props.Count - 2].GetComponent<SimulatedControl>().directionIndex;

        // Set their prop info
        agent.GetComponent<HexToHexControl>().currentLocation = props[props.Count - 1].GetComponent<HexToHexControl>().currentLocation;
        agent.GetComponent<HexQueuedCntrl>().currentLocation = props[props.Count - 1].GetComponent<HexQueuedCntrl>().currentLocation;
        agent.GetComponent<SimulatedControl>().currentLocation = props[props.Count - 1].GetComponent<SimulatedControl>().currentLocation;
        agent.GetComponent<ReplayControl>().currentLocation = props[props.Count - 1].GetComponent<ReplayControl>().currentLocation;
        agent.GetComponent<SimulatedControl>().directionIndex = props[props.Count - 1].GetComponent<SimulatedControl>().directionIndex;
    }

    /// <summary>
    /// Every time a placement is completed subtract 1 from number of placements
    /// There should be five map procedures
    /// 1. placing trees
    /// 2. placing structures
    /// 3. placing path objects
    /// 4. placing cards
    /// 5. placing player/agents
    /// when the total number of placements is met, invokes map completion event which wil probably switch to let the player start game
    /// </summary>
    private void OnePlacementComplete()
    {
        placementsTodo -= 1;
        if (placementsTodo == 0)
            InvokeMapCompleted();
    }
    #endregion

    /// <summary>
    /// Assuming you have already populated the allGrassCells list with the locations you favor
    /// this just returns a random hexcel from all the cells that you want
    /// </summary>
    /// <returns>random hexcell from the list of grasscells you want</returns>
    private HexCell GetRndCellFromPreferred()
    {
        int counter = 0;
        var arrIndex = UnityEngine.Random.Range(0, preferredCells.Count);
        var foundCell = false;
        while (!foundCell)
        {
            counter +=1;
            if (counter == 10 * preferredCells.Count) {return null ;} // this was added to fix the seeds that did not build
            var cell = preferredCells[arrIndex];
            if (propLocs.Contains(cell) || hexgrid.isEdge(cell))
                arrIndex = UnityEngine.Random.Range(0, preferredCells.Count);
            else foundCell = true;

        }
        return preferredCells[arrIndex];
    }

    /// <summary>
    /// Dummy method used for quick visualization of dumping objects randomly
    /// </summary>
    /// <param name="objectDB"></param>
    /// <param name="amount"></param>
    private void SimplePlacement(ObjectDB objectDB, int amount)
    {
        for (int i = 0; i < amount; i++)
        {
            var rndGrassCell = hexgrid.GetRandomGrassCell();
            while (propLocs.Contains(rndGrassCell))
            {
                rndGrassCell = hexgrid.GetRandomGrassCell();
            }
            var prop = Instantiate(objectDB.GetRandomPrefab(), rndGrassCell.transform.position, Quaternion.identity);
            props.Add(prop);
            propLocs.Add(rndGrassCell);
            prop.transform.parent = pG.transform;
        }
    }



    #region ClearingFunctions
    /// <summary>
    /// Clear cards from the map.
    /// </summary>
    private void ClearCards()
    {
        for (int i = 0; i < cards.Length; i++)
        {
            Destroy(cards[i]);
        }
    }

    /// <summary>
    /// Clears all props from the map - will probably be used for map restarts
    /// </summary>
    private void ClearProps()
    {
        propLocs.Clear();
        walkableLocs.Clear();
        for (int i = 0; i < props.Count; i++)
        {
            Destroy(props[i]);
        }
        props.Clear();
    }

    private void ResetPlacementNum()
    {
        placementsTodo = 5;     // #############
    }

    #endregion


}
