using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CardGenerator : MonoBehaviour {
    internal HexGrid hexgrid;

    public ObjectDB shapesDB;
    public MaterialsDB matsDB;
    public GameObject[] cardBases;

    public int numCards = 9;

    public SetGame setGame;

    void Awake()
    {
        hexgrid = GetComponent<HexGrid>();
    }

    /// <summary>
    /// Generates numCards of cards randomly
    /// Of the set of cards generated, run it through SetsExists checker and if no sets exist
    /// delete a card and replace it until at least one set exists
    /// </summary>
    /// <returns></returns>
    public GameObject[] GenerateCards()
    {
        var cards = new GameObject[numCards];
        for (int i = 0; i < numCards; i++)
        {
           cards[i]= GenCard();
        }
        while (!setGame.SetsExist(cards))
        {
            for (int i = 0; i < numCards; i++)
            {
                Destroy(cards[i]);
                cards[i] = GenCard();
            }
        }
        return cards;

    }

    /// <summary>
    /// Generates card, sets properties, rotates it some random amount, spawns at 0,0,0
    /// </summary>
    /// <returns>Card with randomly chosen material number and color</returns>
    public GameObject GenCard()
    {
        var mat = matsDB.GetRandomMaterial();
        var shape = shapesDB.GetRandomPrefab();

        var cardBase = cardBases[UnityEngine.Random.Range(0, cardBases.Length)];
        cardBase = Instantiate(cardBase);
        var gemLocs = cardBase.GetComponentsInChildren<Transform>();
        foreach (var loc in gemLocs)
        {
            if (loc.gameObject.tag == "Card")
                continue;
            var g = Instantiate(shape, loc.position, Quaternion.identity);

            if (shape.name == "Triangle") {
                g.transform.Rotate(new Vector3(180f, 0f, 0f));
            }

            try
            {
                g.GetComponent<Renderer>().material = mat;
            }
            catch
            {
                g.GetComponentInChildren<Renderer>().material = mat;
            }
            g.transform.parent = loc;
        }
        var properties= cardBase.GetComponent<CardProperties>();
        properties.count = gemLocs.Length- 1;
        properties.color = mat;
        properties.shape = shape;
        cardBase.transform.Rotate(new Vector3(0f, 150f, 0f));

        return cardBase;
    }

    public GameObject GenCardWithProperties(string colorS, string shapeS, int count, int xpos, int ypos, bool sel) {
        var mat = matsDB.GetMaterial(colorS);
        var shape = shapesDB.GetPrefab(shapeS);
        var cardBase = cardBases[count-1];
        cardBase = Instantiate(cardBase);
        var gemLocs = cardBase.GetComponentsInChildren<Transform>();
        foreach (var loc in gemLocs)
        {
            if (loc.gameObject.tag == "Card")
                continue;
            var g = Instantiate(shape, loc.position, Quaternion.identity);

            if (shape.name == "Triangle") {
                g.transform.Rotate(new Vector3(180f, 0f, 0f));
            }

            try
            {
                g.GetComponent<Renderer>().material = mat;
            }
            catch
            {
                g.GetComponentInChildren<Renderer>().material = mat;
            }
            g.transform.parent = loc;
        }

        var properties = cardBase.GetComponent<CardProperties>();
        properties.count = gemLocs.Length - 1;
        properties.color = mat;
        properties.shape = shape;
        cardBase.transform.Rotate(new Vector3(0f, 150f, 0f));

        // Gets the hex cell specified by the x/y coordinates, then sets the transform position to that cell's transform position
        cardBase.transform.position = hexgrid.GetCell(xpos, ypos).transform.localPosition;

        return cardBase;
    }
}
