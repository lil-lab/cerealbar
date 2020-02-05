using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Stores the properties for each card.
/// </summary>
public class CardProperties:MonoBehaviour
{
    /// Each card has a material (color), a count, and a shape.
    public Material color;
    public int count;
    public GameObject shape;

    /// <summary>
    /// Converts a card GameObject into a string representation (count +
    /// color + shape).
    /// </summary>
    public static string Stringify(GameObject card)
    {
      var c = card.GetComponent<CardProperties>();
      return c.count.ToString() + " " + c.color.ToString().Split(' ')[0] 
             + " " + c.shape.ToString().Split(' ')[0] + " " + c.transform.position.ToString("f3");
    }

}
