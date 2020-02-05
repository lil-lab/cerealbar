using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using System.Linq;

public class HexCell : MonoBehaviour
{

    [SerializeField]
    HexCell[] neighbors;
    public HexCoordinates coordinates;

    private float elevation;
    public Color color = Color.green;
    public LandType landType = LandType.Grass;
    // Each cell will have an accessible list of its neighbors

    // The following four items contain floats related to agent planning distributions.
    public float valueGoal = 0.0f;
    public float valueTrajectory = 0.0f;
    public float valueObstacle = 0.0f;
    public float valueAvoid = 0.0f;

    public Color originalColor = Color.green;

    private bool showingOriginal = false;
    private bool showingGoal = false;
    private bool showingTrajectory = false;
    private bool showingObstacle = false;
    private bool showingAvoid = false;

    public void ResetColor() {
        color = originalColor;
    }

    public Color layerColor(Color currentColor, Color layerColor, float tintAmount, bool grayscale) {
        if (grayscale) {
            // Add 0.25 to get it to be a lighter color than before
            float grayscale_value = 0.3f * currentColor.grayscale + 0.9f;
            currentColor = new Color(grayscale_value + 0.09f, grayscale_value / 1.2f - 0.05f, grayscale_value - 0.36f);
        }
        float newRed = currentColor.r + (layerColor.r - currentColor.r) * tintAmount; 
        float newGreen = currentColor.g + (layerColor.g - currentColor.g) * tintAmount; 
        float newBlue = currentColor.b + (layerColor.b - currentColor.b) * tintAmount;

        return new Color(newRed, newGreen, newBlue);
    }

    public void SetToGoalColor() {
        // Goals are green
        Color colorToAdd = Color.green;
        color = layerColor(originalColor, colorToAdd, valueGoal, true);
    }

    public void SetToTrajectoryColor() {
        // Trajectory is blue
        Color colorToAdd = new Color(0.79f, 0.27f, 0.87f);
        color = layerColor(originalColor, colorToAdd, valueTrajectory, true);
    }

    public void SetToObstacleColor() {
        // Obstacles are red
        Color colorToAdd = Color.red;
        color = layerColor(originalColor, colorToAdd, valueObstacle, true);
    }

    public void SetToAvoidColor() {
        // Avoid is yellow
        Color colorToAdd = Color.yellow;
        color = layerColor(originalColor, colorToAdd, valueAvoid, true);
    }

    public void SetToAllColors() {
        Color goalColor = Color.green;
        Color trajColor = Color.red;
        Color obsColor = Color.blue;
        Color avoidColor = Color.yellow;

        // Originally grayscale color.
        color = layerColor(originalColor, obsColor, valueObstacle, true);
        color = layerColor(color, avoidColor, valueAvoid, false);
        color = layerColor(color, trajColor, valueTrajectory, false);
        color = layerColor(color, goalColor, valueGoal, false);
    }

    public void SetGoalDist(float val) {
        valueGoal = val;
        if (showingGoal) {
            SetToGoalColor();
        }

        SetToAllColors();
    }

    public void SetTrajectoryDist(float val) {
        valueTrajectory = val;
        if (showingTrajectory) {
            SetToTrajectoryColor();
        }

        SetToAllColors();
    }

    public void SetObstacleDist(float val) {
        valueObstacle = val;
        if (showingObstacle) {
            SetToObstacleColor();
        }

        SetToAllColors();
    }

    public void SetAvoidDist(float val) {
        valueAvoid = val;
        if (showingAvoid) {
            SetToAvoidColor();
        }

        SetToAllColors();
    }


    public float Elevation
    {
        get{ return elevation; }
        set
        {
            elevation = value;
            var yHeight = HexMetrics.elevation * value;
            transform.localPosition = transform.localPosition + new Vector3(0, yHeight, 0);

        }
    }

    public HexCell GetNeighbor(HexDirection direction)
    {
        return neighbors[(int)direction];
    }

    public List<HexCell> GetAllNeighborsList()
    {
        return neighbors.ToList();
        //return neighborsList;
    }

    public List<HexCell> GetAllNeighborsNoWaterList()
    {
        var neighborsList = new List<HexCell>();
        foreach(var n in neighbors)
        {
            try
            {
                if (n.landType != LandType.Water)
                {
                    neighborsList.Add(n);
                }
            }
            catch(NullReferenceException)
            {

            }
        }
        return neighborsList;
    }

    /// <summary>
    /// NOTE
    /// </summary>
    /// <returns>NOTE= RETURNS NULL IN THE DIRECTIONS THAT DO NOT HAVE VIABLE NEIGHBORS</returns>
    public List<HexCell> GetAllGrassNeighbors()
    {
        var neighborsList = new List<HexCell>();
        foreach(var n in neighbors)
        {
            try
            {
                if (n.landType == LandType.Grass)
                {
                    neighborsList.Add(n);
                }

            }
            catch (NullReferenceException) { }
        }
        return neighborsList;
    }



    public void SetNeighbor(HexDirection direction, HexCell cell)
    {
        // 'direction' represents the direction in this cell to get to cell.
        neighbors[(int)direction] = cell;
        cell.neighbors[(int)direction.Opposite()] = this;
    }


}
