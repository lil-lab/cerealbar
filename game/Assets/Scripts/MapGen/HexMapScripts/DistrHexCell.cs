using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using System.Linq;


public class DistrHexCell : MonoBehaviour
{

    [SerializeField]
    DistrHexCell[] neighbors;
    public HexCoordinates coordinates;

    private float elevation;
    public Color color = Color.clear;
    // Each cell will have an accessible list of its neighbors

    public DistrHexCell GetNeighbor(HexDirection direction)
    {
        return neighbors[(int)direction];
    }

    public List<DistrHexCell> GetAllNeighborsList()
    {
        return neighbors.ToList();
        //return neighborsList;
    }

    public void SetNeighbor(HexDirection direction, DistrHexCell cell)
    {
        // 'direction' represents the direction in this cell to get to cell.

        neighbors[(int)direction] = cell;
        cell.neighbors[(int)direction.Opposite()] = this;
    }


}
