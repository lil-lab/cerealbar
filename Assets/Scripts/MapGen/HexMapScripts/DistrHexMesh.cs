using System.Collections;
using System;
using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class DistrHexMesh : MonoBehaviour
{

    private Mesh hexMesh;
    private List<Vector3> vertices = new List<Vector3>();
    private List<int> triangles = new List<int>();
    private List<Color> colors = new List<Color>();

    void Awake()
    {
        hexMesh = GetComponent<MeshFilter>().mesh;
        hexMesh.name = "Hex Mesh";

    }

    void OnEnable()
    {
        Restarter.OnRestartEvent += ResetMeshes;
    }

    void OnDisable()
    {
        Restarter.OnRestartEvent -= ResetMeshes;
    }

    public void Triangulate(DistrHexCell[] cells)
    {
        hexMesh.Clear();
        vertices.Clear();
        triangles.Clear();
        colors.Clear();

        foreach (var cell in cells)
        {
            Triangulate(cell);
        }

        hexMesh.vertices = vertices.ToArray();
        hexMesh.triangles = triangles.ToArray();
        hexMesh.colors = colors.ToArray();
        hexMesh.RecalculateNormals();


    }

    public void Triangulate(DistrHexCell cell)
    {
        for (HexDirection d = HexDirection.NE; d <= HexDirection.NW; d++)
        {
            Triangulate(d, cell);
        }


    }

    private Vector3 Triangulate(HexDirection direction, DistrHexCell cell)
    {
        var center = cell.transform.localPosition;
        var vect1 = center + HexMetrics.GetFirstSolidCorner(direction);
        var vect2 = center + HexMetrics.GetSecondSolidCorner(direction);

        AddTriangle(center, vect1, vect2);
        AddTriangleColor(cell.color);

        if (direction <= HexDirection.SE)
        {
            TriangulateConnection(direction, cell, vect1, vect2);
        }
        return vect1;

    }

    private void TriangulateConnection(HexDirection direction, DistrHexCell cell, Vector3 v1, Vector3 v2)
    {
        var neighbor = cell.GetNeighbor(direction);
        if (neighbor == null)
        {
            return;
        }
        var bridge = HexMetrics.GetBridge(direction);
        var v3 = v1 + bridge;
        var v4 = v2 + bridge;
        ///v3.y = v4.y = neighbor.Elevation * HexMetrics.elevation;

        AddQuad(v1, v2, v3, v4);
        AddQuadColor(cell.color, neighbor.color);

        var nxtNeighbor = cell.GetNeighbor(direction.Next());
        if (direction <= HexDirection.E && nxtNeighbor != null)
        {
            Vector3 v5 = v2 + HexMetrics.GetBridge(direction.Next());
            // v5.y = nxtNeighbor.Elevation * HexMetrics.elevation;
            AddTriangle(v2, v4, v5);
            AddTriangleColor(cell.color, neighbor.color, nxtNeighbor.color);
        }


    }


    private void AddTriangle(Vector3 v1, Vector3 v2, Vector3 v3)
    {
        var vertexIndex = vertices.Count;
        vertices.Add(v1);
        vertices.Add(v2);
        vertices.Add(v3);

        triangles.Add(vertexIndex);
        triangles.Add(vertexIndex + 1);
        triangles.Add(vertexIndex + 2);

    }

    /// <summary>
    /// For when a triangle has the same color on all three corners/ will probably be only using this function
    /// </summary>
    /// <param name="color">Color for triangle</param>
    private void AddTriangleColor(Color color)
    {
        for (int i = 0; i < 3; i++)
            colors.Add(color);

    }
    private void AddTriangleColor(Color c1, Color c2, Color c3)
    {
        colors.Add(c1);
        colors.Add(c2);
        colors.Add(c3);

    }

    private void AddQuad(Vector3 v1, Vector3 v2, Vector3 v3, Vector3 v4)
    {
        var vertexIndex = vertices.Count;
        vertices.Add(v1);
        vertices.Add(v2);
        vertices.Add(v3);
        vertices.Add(v4);

        triangles.Add(vertexIndex);
        triangles.Add(vertexIndex + 2);
        triangles.Add(vertexIndex + 1);
        triangles.Add(vertexIndex + 1);
        triangles.Add(vertexIndex + 2);
        triangles.Add(vertexIndex + 3);
    }

    private void AddQuadColor(Color c1, Color c2)
    {
        colors.Add(c1); colors.Add(c1);
        colors.Add(c2); colors.Add(c2);
    }



    public void EditCell(DistrHexCell cell, Color color)
    {
        cell.color = color;
    }

    private void ResetMeshes()
    {
        hexMesh.Clear();
    }
}
