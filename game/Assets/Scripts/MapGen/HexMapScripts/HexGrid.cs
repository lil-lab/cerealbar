using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System;

/// <summary>
/// Main place for map generation
/// </summary>
public class HexGrid : MonoBehaviour
{
    public int seed;
    private int whereAmI = 0;

    [Tooltip("Just the HexCell Prefab")]
    public HexCell hexCell;
    private int xWidth = 25;
    private int zHeight = 25;
    private int mooCounter = 0;

    public Text hexCellLabel;
    public Canvas gridUICanvas;

    private HexMesh hexMesh;

    public int ponds;
    public int hills;
    public int pondSize;
    public int hillSize;
    public int maxPathSplits;
    private int paths = 1;

    private GameObject parentCell;
    // public static System.Random rnd;

    [HideInInspector]
    public HexCell[] hexCells;

    #region paths things
    private int numPathSplits = 0;
    private Stack<bool> pathsInProgress = new Stack<bool>();
    private int rerouteCount = 0;

    //When paths are finished invoke the pathsfinished event to trigger the placement of objects around the map
    public delegate void OnPathsFinishedHandler();
    public static event OnPathsFinishedHandler OnPathsFinishedEvent;


    public static void InvokePathsFinished()
    {
        OnPathsFinishedEvent();
    }
    #endregion

    void Awake()
    {
        SetParentCell();
        hexMesh = GetComponentInChildren<HexMesh>();
        // rnd = new System.Random();
        UnityEngine.Random.InitState(seed);
    }

    void Start()
    {
    }

    private void SetParentCell()
    {
        parentCell = new GameObject("Cells");
        parentCell.transform.parent = this.transform;
    }

    /// <summary>
    /// This sets the foundation for the map, not the actual cell pieces yet
    /// </summary>
    public void CreateGrid()
    {
        //hexMesh.Triangulate(hexCells);
        hexCells = new HexCell[zHeight * xWidth];
        for (int z = 0, i = 0; z < zHeight; z++)
        {
            for (int x = 0; x < xWidth; x++)
            {
                CreateCell(x, z, i++);
            }
        }
    }

    /// <summary>
    /// This creates the whole map (visually)
    /// </summary>
    public void CreateTestGrid()
    {
        CreateGrid();

        for (int i = 0; i < ponds; i++)
            CreateDepression(LandType.Water, pondSize, -1f);
        for (int h = 0; h < hills; h++)
            CreateDepression(LandType.Hill, hillSize, 4f);
        for (int p = 0; p < paths; p++){
            HexCell startEdgeCell = GetStartingEdgeCell();
            if (startEdgeCell == null) {break;} //##############
            StartAPathAt(startEdgeCell);
        }

        DrawOutlines();
    }


    #region Depressions

    /// <summary>
    /// raise/lower the cell height
    /// </summary>
    /// <param name="landType">water/hill, really only these two that would need the blob depression </param>
    /// <param name="typeSize">amount of cells you want the land block to be</param>
    /// <param name="depressionScale">inceasing or decreasing </param>
    private void CreateDepression(LandType landType, int typeSize, float depressionScale)
    {
        var currentNeighbors = new List<HexCell>();
        var potentialAccepts = new List<HexCell>();
        var acceptedCells = new List<HexCell>();


        acceptedCells.Add(GetRandomGrassCell());
        for (int l = 0; l < typeSize - 1; l++)
        {
            var currentHex = acceptedCells[UnityEngine.Random.Range(0, acceptedCells.Count)];

            currentNeighbors = currentHex.GetAllNeighborsList();
            foreach (var neighbor in currentNeighbors)
            {
                try
                {
                    if (acceptedCells.Contains(neighbor))
                        continue;
                    var count = GetSimilarNeighbors(acceptedCells, currentHex, neighbor);
                    for (int i = 0; i < count; i++)
                    {
                        potentialAccepts.Add(neighbor);
                    }
                }
                catch (NullReferenceException exception)
                {
                    Debug.Log("CreateDepression():" + exception.ToString());
                }
            }

            if (potentialAccepts.Count != 0)
            {
                var accepted = potentialAccepts[UnityEngine.Random.Range(0, potentialAccepts.Count)];

                acceptedCells.Add(accepted);
                potentialAccepts.Clear();
            }
        }
        SetDepression(acceptedCells, depressionScale);
    }

    /// <summary>
    /// Set the mesh with the list of cells to the depression level wanted.
    /// HexMesh script will edit the landtype valus based on the depression scale
    /// Note that any 0f depression casts are assumed to be paths and not grass as the entire grid is first initialized with grass
    /// </summary>
    /// <param name="hexcellsList"></param>
    /// <param name="depressionScale"></param>
    private void SetDepression(IList<HexCell> hexcellsList, float depressionScale)
    {
        foreach (var cell in hexcellsList)
        {
            try
            {
                var cIndex = Array.FindIndex(hexCells, element => element.coordinates.ToString() == cell.coordinates.ToString());
                hexMesh.EditCell(hexCells[cIndex], depressionScale);
            }
            catch (ArgumentNullException)
            {
                Debug.Log("Hex cells not found!");
            }
        }
        RefreshCells();

    }


    private int GetSimilarNeighbors(List<HexCell> acceptedCells, HexCell currentCell, HexCell neighborCell)
    {
        var neighborsNeighbors = neighborCell.GetAllNeighborsList();
        var intersection = acceptedCells.Intersect(neighborsNeighbors).ToList();

        if (intersection.Count > 1)
            return 2;
        return 1;
    }


    #endregion

    #region Random Cell Getters
    public HexCell GetRandomGrassCell()
    {
        var arrIndex = UnityEngine.Random.Range(0, xWidth * zHeight);
        var foundCell = false;
        while (!foundCell)
        {
            var cell = hexCells[arrIndex];
            if (cell.landType == LandType.Grass && !isEdge(cell))
                foundCell = true;
            else
                arrIndex = UnityEngine.Random.Range(0, xWidth * zHeight);
        }
        return hexCells[arrIndex];
    }

    public HexCell GetRandomGrassOrPathCell()
    {
        var arrIndex = UnityEngine.Random.Range(0, xWidth * zHeight);
        var foundCell = false;
        while (!foundCell)
        {
            var cell = hexCells[arrIndex];
            if (cell.landType == LandType.Grass || cell.landType == LandType.Path)
            {
                if (!isEdge(cell))
                    foundCell = true;
                else
                    arrIndex = UnityEngine.Random.Range(0, xWidth * zHeight);
            }
            else
                arrIndex = UnityEngine.Random.Range(0, xWidth * zHeight);
        }

        return hexCells[arrIndex];
    }

    public HexCell GetRandomPathCell()
    {
        var arrIndex = UnityEngine.Random.Range(0, xWidth * zHeight);
        var foundCell = false;
        int counter = 0;

        while (!foundCell)
        {
            var cell = hexCells[arrIndex];
            if (cell.landType == LandType.Path)
            {
                if (!isEdge(cell))
                    foundCell = true;
                else
                    arrIndex = UnityEngine.Random.Range(0, xWidth * zHeight);
            }
            else
                arrIndex = UnityEngine.Random.Range(0, xWidth * zHeight);
        }

        return hexCells[arrIndex];
    }

    #endregion
    #region PathGen


    /// <summary>
    /// Takes in the cell it is supposed to start from. this way you can start a path from anywhere
    /// Possible future TODO - add checks to make sure the starting cell is on grass/path
    /// </summary>
    /// <param name="startingCell"></param>
    private void StartAPathAt(HexCell startingCell)
    {


        var startingNeighbors = startingCell.GetAllNeighborsList();
        var possibleDirs = new List<int>();
        rerouteCount = 0;
        numPathSplits = 0;
        var goodStart = false;
        int counter = 0;

        while (!goodStart)
        {
            counter++;
            if (counter == 10 * startingNeighbors.Count) {
            break;
            }    //#############

            for (int i = 0; i < startingNeighbors.Count; i++)
            {
                try
                {
                    if (startingNeighbors[i].landType == LandType.Grass
                        && startingNeighbors[i].landType != LandType.Path
                        && !isEdge(startingNeighbors[i]))
                    {
                        possibleDirs.Add(i);
                    }
                }
                catch (NullReferenceException)
                {

                }
            }
            if (possibleDirs.Count != 0)
            {
                goodStart = true;

            }
            else
            {
                startingCell = GetStartingEdgeCell();
                if (startingCell == null){ continue;}   //########
                startingNeighbors = startingCell.GetAllNeighborsList();
            }
        }

        var directionIndex = possibleDirs[UnityEngine.Random.Range(0, possibleDirs.Count)];

        StartCoroutine(CreatePathinDir(startingCell, directionIndex));


        StopCoroutine("CreatePathinDir");
    }



    /// <summary>
    /// Coroutine used to recursively make path.
    /// Starts with passed in direction and when split chances occur calls a new CreatePathinDir in the directions to split
    /// Sets each portion of the path at each call
    /// </summary>
    /// <param name="startCell"></param>
    /// <param name="directionIndex"></param>
    /// <returns></returns>
    private IEnumerator CreatePathinDir(HexCell startCell, int directionIndex)
    {
        //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "push - ");

        //whereAmI++;
        //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", whereAmI.ToString());
        //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "\n");
        pathsInProgress.Push(true);
        //yield return new WaitForSeconds(.5f); //just for debugging purposes
        var goodDir = true;
        var currentNeighbors = startCell.GetAllNeighborsList();
        var current = currentNeighbors[directionIndex];
        var pathCells = new List<HexCell>() { startCell, currentNeighbors[directionIndex] };

        if (rerouteCount >= 7)
        {
            HexCell s = GetStartingEdgeCell();
            if (s != null){         //######
                StartAPathAt(s);
            }
            //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "stop1 \n");

            pathsInProgress.Pop();
            //whereAmI-- ;
            yield break;                ///#########
            //StopCoroutine("CreatePathinDir");     ###########
        }

        if (numPathSplits >= maxPathSplits)
        {

            //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "numPathSplits >= maxPathSplits \n");

            if (!isEdge(startCell))
            {
                SimplePathinDir(current, directionIndex);
            }

             //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "pop1 - ");

            //whereAmI--;
            //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", whereAmI.ToString());
            //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "\n");


            pathsInProgress.Pop();
            yield break;
        }

        if (isEdge(current) && numPathSplits < 2 )
        {
            HexCell s = GetStartingEdgeCell();
            if (s != null){
                StartAPathAt(s);
            }

           //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "pop3 - ");

           //whereAmI--;
           //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", whereAmI.ToString());
           //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "\n");
           pathsInProgress.Pop();
           yield break;
            //StopCoroutine("CreatePathinDir");

        }

        numPathSplits += 1;
        while (goodDir)
        {
            //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "gooddir ");
            //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt",  mooCounter.ToString());
            //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", " , \n ");




            mooCounter ++;
            if (mooCounter == 2000){
                 InvokePathsFinished();
                 break;
             }

            currentNeighbors = current.GetAllNeighborsList();
            var nextCell = currentNeighbors[directionIndex];

            if (nextCell == null)
            {
                break;
            }
            else if (nextCell.landType != LandType.Grass && nextCell.landType != LandType.Path)
            {
                if (CanChangeDir(currentNeighbors, (HexDirection)directionIndex))
                {

                    directionIndex = GetNewDir(currentNeighbors, (HexDirection)directionIndex);
                    rerouteCount += 1;

                    yield return CreatePathinDir(current, directionIndex);
                    break;
                 }
                else {
                    //!!System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "else1  \n");
                }
                break;
            }
            // check if nextCell is grass, then check if its an edge , if not grass, have to change the direction
            else if (isEdge(nextCell))
            {
                pathCells.Add(nextCell);
                if (CanChangeDir(nextCell.GetAllNeighborsList(), (HexDirection)directionIndex) && numPathSplits < maxPathSplits)
                {
                    rerouteCount += 1;
                    directionIndex = GetNewDir(nextCell.GetAllNeighborsList(), (HexDirection)directionIndex);

                    yield return CreatePathinDir(nextCell, directionIndex);
                }
                else{
                     //!!System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "is edge but can't charge direction  \n");
                }

                break;
            }
            else if (ifSplit(pathCells.Count))
            {
                var splitIndices = GetPathSplit(current, (HexDirection)directionIndex);
                foreach (var index in splitIndices)
                {
                    yield return CreatePathinDir(current, index);
                }
                //goodDir = false;
                break;

            }
            else
            {
                pathCells.Add(nextCell);
                current = nextCell;
            }
        }

        // kind of messy final clean
        for (int p = 0; p < pathCells.Count; p++)
        {
            if (pathCells[p].landType == LandType.Hill || pathCells[p].landType == LandType.Water)
            {
                pathCells.Remove(pathCells[p]);
            }
        }

        SetDepression(pathCells, 0f);

         //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "pop2 -  ");


        //whereAmI--;
        //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", whereAmI.ToString());
        //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "\n");

        pathsInProgress.Pop();

        if (pathsInProgress.Count == 0)
        {
            InvokePathsFinished();
        }
        else {
            //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "did not finish paths \n ");
            //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", pathsInProgress.Count.ToString());
            //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "\n ");
        }


    }

    /// <summary>
    /// Creates a path straight to an edge or nongrass type in the direction indicated from the current cell
    /// Used to finish up the paths when max splits have been reached
    /// </summary>
    /// <param name="currentCell"></param>
    /// <param name="directionIndex"></param>
    private void SimplePathinDir(HexCell currentCell, int directionIndex)
    {
        var currentNeighbors = currentCell.GetAllNeighborsList();
        var next = currentCell;
        var pathCells = new List<HexCell> { currentCell };

        var keepPathGoing = true;
        while (keepPathGoing)
        {
            //System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "keeppathgoing \n ");

            next = currentNeighbors[directionIndex];
            if (next == null){
                   break;
            }

            try
            {
                if (isEdge(next) && next.landType != LandType.Grass)
                {
                    break;
                }

                else if (isEdge(next) && next.landType == LandType.Grass)
                {
                    pathCells.Add(next);
                    break;

                }

                else if (next.landType != LandType.Grass){
                    break;
                 }
            }
            catch (NullReferenceException) {
                 System.IO.File.AppendAllText(@"/Users/cerealbar/Downloads/cereal-bar-master 12 2/debug.txt", "caattch \n ");

             }

            pathCells.Add(next);
            currentNeighbors = next.GetAllNeighborsList();
        }
        SetDepression(pathCells, 0f);
    }



    // <summary>
    // Intended purpose: new paths preferably start on edges
    // Only using foundEdge for seed 0 because it freezes the map for certain seeds.
    // </summary>
    // <returns>a random edge hexcell</returns>
    private HexCell GetStartingEdgeCell()
    {
        int count = 0;
        var randomCell = UnityEngine.Random.Range(1, hexCells.Length - 1);
        var startingCell = hexCells[randomCell];

        var foundEdge = false;
        while(!foundEdge)
        {
            count++;
            if (count == 10*hexCells.Length){return null;}
            randomCell = UnityEngine.Random.Range(1, hexCells.Length - 1);
            startingCell = hexCells[randomCell];

            if (startingCell.landType == LandType.Grass && isEdge(startingCell))
                foundEdge = true;
        }
        return startingCell;
    }

    public bool isEdge(HexCell hexCell)
    {
        var x = hexCell.coordinates.X;
        var z = hexCell.coordinates.Z;

        if (x == 0 || z == 0 || x == xWidth-1 || z == zHeight-1)
            return true;
        return false;
    }

    public bool isPastEdge(HexCell hexCell)
    {
        if (hexCell == null) {
          return true;
        }
        var x = hexCell.coordinates.X;
        var z = hexCell.coordinates.Z;

        if (x < 0 || z < 0 || x >= xWidth || z >= zHeight)
            return true;
        return false;
    }

    private bool ifSplit(int currentPathSize)
    {
        if (currentPathSize < 4)
            return false;
        var changeProb = 19;
        var percent = UnityEngine.Random.Range(0, 100);
        if (percent <= changeProb)
            return true;
        return false;
    }

    /// <summary>
    /// NOT IN USE
    /// Rolls the chance of the path needing to split//
    /// </summary>
    /// <returns></returns>
    private bool ifSplit()
    {
        var changeProb = 19;
        var percent = UnityEngine.Random.Range(0, 100);
        if (percent <= changeProb)
            return true;
        return false;
    }

    /// <summary>
    /// Returns the two directions that the path should split in when a split is called.
    /// If only one direction is possible, only returns one.
    /// </summary>
    /// <param name="currentCell"></param>
    /// <param name="direction">current hexdirection that the path is going </param>
    /// <returns>List on (int)Hexdirections to go in</returns>
    private List<int> GetPathSplit(HexCell currentCell, HexDirection direction)
    {
        var neighbors = currentCell.GetAllNeighborsList();
        var goodHexDirs = new List<HexDirection> { direction, direction.Next(), direction.Previous() };
        var splitOptionIndices = new List<int>();
        var splitableCellsNeighbors = new HexCell[]
                {
                    neighbors[(int)direction],
                    neighbors[(int)goodHexDirs[1]],
                    neighbors[(int)goodHexDirs[2]]
                };
        foreach (var neighbor in splitableCellsNeighbors)
        {
            try
            {
                if (neighbor.landType != LandType.Grass || isEdge(neighbor))
                {
                    goodHexDirs.Remove((HexDirection)neighbors.IndexOf(neighbor));
                }
            }
            catch (NullReferenceException) { }
        }
        var splitDir = goodHexDirs[UnityEngine.Random.Range(0, goodHexDirs.Count)];
        splitOptionIndices.Add((int)splitDir);

        goodHexDirs.Remove(splitDir);

        if (goodHexDirs.Count > 0)
        {
            //do the second path
            splitDir = goodHexDirs[UnityEngine.Random.Range(0, goodHexDirs.Count)];
            splitOptionIndices.Add((int)splitDir);

        }
        return splitOptionIndices;
    }

    /// <summary>
    /// Checks if a direction change is possible at the passed location. Used to check before calling changedir
    /// </summary>
    /// <param name="currentNeighbors"></param>
    /// <param name="currentDirection"></param>
    /// <returns></returns>
    private bool CanChangeDir(List<HexCell> currentNeighbors, HexDirection currentDirection)
    {
        var viableNeighborsIndices = new List<int>();
        for (int i = 0; i < currentNeighbors.Count; i++)
        {
            try
            {
                if ((currentNeighbors[i].landType == LandType.Grass) && i != (int)currentDirection && i != (int)HexDirectionExtensions.Opposite(currentDirection))
                {
                    viableNeighborsIndices.Add(i);
                }
            }
            catch (NullReferenceException) { }
        }
        if (viableNeighborsIndices.Count == 0)
            return false;
        return true;
    }

    /// <summary>
    /// Only call this after checking CanChangeDir, this function will not return the current dir if it is the only one left
    /// </summary>
    /// <param name="currentNeighbors"></param>
    /// <param name="currentDirection"></param>
    /// <returns></returns>
    private int GetNewDir(List<HexCell> currentNeighbors, HexDirection currentDirection)
    {
        var viableNeighborsIndices = new List<int>();
        for (int i = 0; i < currentNeighbors.Count; i++)
        {
            try
            {
                if (currentNeighbors[i].landType == LandType.Grass  && i != (int)currentDirection)
                {
                    viableNeighborsIndices.Add(i);
                }
            }
            catch (NullReferenceException) { }
        }

        var favoredDirections = new HexDirection[] { currentDirection.Next(), currentDirection.Previous() };

        foreach (var hexDir in favoredDirections)
        {
            if (viableNeighborsIndices.Contains((int)hexDir))
            {
                return (int)hexDir;
            }
        }

        return viableNeighborsIndices[UnityEngine.Random.Range(0, viableNeighborsIndices.Count)];
    }


    #endregion

    #region CellGen

    private void CreateCell(int x, int z, int i)
    {
        // Z is indexed starting from below.
        var xPosition = (x + z * .5f - z / 2) * HexMetrics.innerRadius * 2f;
        var zPosition = z * HexMetrics.outerRadius * 1.5f;
        var position = new Vector3(xPosition, 0, zPosition);

        var cell = Instantiate(hexCell, position, Quaternion.identity);
        var collider = cell.gameObject.AddComponent(typeof(BoxCollider)) as BoxCollider;
        // Box collider is not ideal, but placeholder until we can get an actual hexagon prefab?
        collider.size = new Vector3(20.0f, 5.0f, 20.0f);
        collider.isTrigger = true;

        cell.transform.parent = parentCell.transform;
        hexCells[i] = cell;
        cell.coordinates = HexCoordinates.FromOffsetCoords(x, z);

        if (x > 0)
        {
            cell.SetNeighbor(HexDirection.W, hexCells[i - 1]);
        }
        if (z > 0)
        {
            if (z % 2 == 0) //even
            {

                cell.SetNeighbor(HexDirection.SE, hexCells[i - xWidth]);
                if (x > 0)
                    cell.SetNeighbor(HexDirection.SW, hexCells[i - xWidth - 1]);
            }
            else
            {
                cell.SetNeighbor(HexDirection.SW, hexCells[i - xWidth]);
                if (x < xWidth - 1)
                    cell.SetNeighbor(HexDirection.SE, hexCells[i - xWidth + 1]);
            }
        }
        var label = Instantiate(hexCellLabel);
        label.rectTransform.SetParent(gridUICanvas.transform, false);
        label.rectTransform.anchoredPosition = new Vector2(xPosition, zPosition);
        label.text = x + "," + z; //hex grid coordinates, not global
    }

    private void DrawOutlines()
    {
        Vector3 smudge = new Vector3(0F,0.2F,0F); //so lines dont get rendered under hexes
        float alpha = 1.0f;
        Gradient gradient = new Gradient();
        gradient.SetKeys(
           new GradientColorKey[] { new GradientColorKey(Color.green, 0.0f), new GradientColorKey(Color.red, 1.0f) },
           new GradientAlphaKey[] { new GradientAlphaKey(alpha, 0.0f), new GradientAlphaKey(alpha, 1.0f) }
           );
        foreach (HexCell cell in hexCells)
        {
            if (Math.Abs(cell.Elevation) <= 0.2)
            {
                GameObject lineObj = new GameObject("outline-"+cell.ToString());
                lineObj.layer = 10;//OnlyAgentView
                lineObj.transform.parent = cell.transform;
                LineRenderer renderer = lineObj.AddComponent(typeof(LineRenderer)) as LineRenderer;
                int numPoints = 4;
                if (isEdge(cell))
                {
                  numPoints = 6;
                  renderer.loop = true;
                }
                else
                {
                  renderer.loop = false;
                }
                Vector3[] positions = new Vector3[numPoints];
                for (HexDirection dir = HexDirection.NE; (int)dir < numPoints; dir++)
                {
                  var center = cell.transform.localPosition;
                  positions[(int)dir] = center + HexMetrics.GetFirstSolidCorner(dir)/0.75f + smudge;
                }
                renderer.startWidth = 0.25F;
                renderer.endWidth = 0.25F;
                renderer.material.color = Color.white;
                renderer.numCornerVertices = numPoints;
                renderer.positionCount = numPoints;
                renderer.SetPositions(positions);
            }
        }
    }


    public HexCell GetCell(int hexX, int hexZ)
    {
        var arrIndex = hexX + hexZ * xWidth;
        return hexCells[arrIndex];
    }


    public void RefreshCells()
    {
        hexMesh.Triangulate(hexCells);

    }

    #endregion

    public void UpdateSeed(int seed)
    {
        this.seed = seed;
        UnityEngine.Random.InitState(seed);
    }

    public int GetMapSeed()
    {
        return this.seed;
    }

    private void Clear()
    {
        hexCells = new HexCell[zHeight * xWidth];
    }


}
