using System.Collections;
using System;
using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class HexMesh : MonoBehaviour
{

    private Mesh hexMesh;
    public MeshCollider hexMeshCollider;
    private List<Vector3> vertices = new List<Vector3>();
    private List<int> triangles = new List<int>();
    public List<Color> colors = new List<Color>();

    // [SerializeField]
    // private Color grassColor = Color.green;
    [SerializeField]
    private Color waterColor = Color.blue;
    [SerializeField]
    private Color hillColor = Color.white;
    public Color pathColor = Color.yellow;

    public GameObject outlines;

    void Awake()
    {
        hexMesh = GetComponent<MeshFilter>().mesh;
        hexMeshCollider = GetComponentInChildren<MeshCollider>();
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

    public void Triangulate(HexCell[] cells)
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
        GenerateCollider();
        hexMesh.RecalculateNormals();


    }

    public void Triangulate(HexCell cell)
    {
        for (HexDirection d = HexDirection.NE; d <= HexDirection.NW; d++)
        {
            Triangulate(d, cell);
        }


    }

    private Vector3 Triangulate(HexDirection direction, HexCell cell)
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

    private void TriangulateConnection(HexDirection direction, HexCell cell, Vector3 v1, Vector3 v2)
    {
        var neighbor = cell.GetNeighbor(direction);
        if (neighbor == null)
        {
            return;
        }
        var bridge = HexMetrics.GetBridge(direction);
        var v3 = v1 + bridge;
        var v4 = v2 + bridge;
        v3.y = v4.y = neighbor.Elevation * HexMetrics.elevation;

        AddQuad(v1, v2, v3, v4);
        AddQuadColor(cell.color, neighbor.color);

        var nxtNeighbor = cell.GetNeighbor(direction.Next());
        if (direction <= HexDirection.E && nxtNeighbor != null)
        {
            Vector3 v5 = v2 + HexMetrics.GetBridge(direction.Next());
            v5.y = nxtNeighbor.Elevation * HexMetrics.elevation;
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



    public void EditCell(HexCell cell, float newElev)
    {
        cell.Elevation = newElev;

        if (newElev < -.2f)
        {
            cell.color = waterColor;
            cell.originalColor = waterColor;
            cell.landType = LandType.Water;
        }
        else if (newElev > 0f)
        {
            cell.color = hillColor;
            cell.originalColor = hillColor;
            cell.landType = LandType.Hill;
        }
        else
        {
            cell.color = pathColor;
            cell.originalColor = pathColor;
            cell.landType = LandType.Path;
        }


    }

    public void GenerateCollider()
    {
        var meshFilter = hexMeshCollider.gameObject.GetComponent<MeshFilter>();

        meshFilter.mesh = Instantiate(hexMesh);
        var meshVertices = (Vector3[])meshFilter.mesh.vertices.Clone();
        for (int i = 0; i < meshVertices.Length; i++)
        {
            if (meshVertices[i].y < 0)
            {
                meshVertices[i] += new Vector3(0, 50f, 0);

            }
            else if (meshVertices[i].y > 5)
            {
                meshVertices[i] += new Vector3(0, 50f, 0);
            }
        }
        meshFilter.mesh.vertices = meshVertices;
        meshFilter.mesh.RecalculateNormals();
        hexMeshCollider.sharedMesh = meshFilter.mesh;

    }

    private void ResetMeshes()
    {
        hexMesh.Clear();
        hexMeshCollider.sharedMesh = null;
    }
}
