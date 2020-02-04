using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System;

/// <summary>
/// Main place for map generation
/// </summary>
public class DistrHexGrid : MonoBehaviour
{
    private int whereAmI = 0;

    [Tooltip("Just the DistrHexCell Prefab")]
    public DistrHexCell hexCell;
    private int xWidth = 25;
    private int zHeight = 25;
    private int mooCounter = 0;

    public Text hexCellLabel;
    public Canvas gridUICanvas;

    private DistrHexMesh hexMesh;

    private GameObject parentCell;
    // public static System.Random rnd;

    [HideInInspector]
    public DistrHexCell[] hexCells;

    void Awake()
    {
        SetParentCell();
        hexMesh = GetComponentInChildren<DistrHexMesh>();
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
        hexCells = new DistrHexCell[zHeight * xWidth];
        for (int z = 0, i = 0; z < zHeight; z++)
        {
            for (int x = 0; x < xWidth; x++)
            {
                CreateCell(x, z, i++);
            }
        }
    }

    public bool isEdge(DistrHexCell hexCell)
    {
        var x = hexCell.coordinates.X;
        var z = hexCell.coordinates.Z;

        if (x == 0 || z == 0 || x == xWidth-1 || z == zHeight-1)
            return true;
        return false;
    }

    public bool isPastEdge(DistrHexCell hexCell)
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

    #region CellGen

    private void CreateCell(int x, int z, int i)
    {
        // Z is indexed starting from below.
        var xPosition = (x + z * .5f - z / 2) * HexMetrics.innerRadius * 2f;
        var zPosition = z * HexMetrics.outerRadius * 1.5f;
        var position = new Vector3(xPosition, 0, zPosition);

        var cell = Instantiate(hexCell, position, Quaternion.identity);

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

    public DistrHexCell GetCell(int hexX, int hexZ)
    {
        var arrIndex = hexX + hexZ * xWidth;
        return hexCells[arrIndex];
    }


    public void RefreshCells()
    {
        hexMesh.Triangulate(hexCells);

    }

    #endregion

    private void Clear()
    {
        hexCells = new DistrHexCell[zHeight * xWidth];
    }


}
