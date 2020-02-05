using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[CreateAssetMenu()]
public class ObjectDB : ScriptableObject {
    public GameObject[] prefabs;

    public GameObject GetRandomPrefab()
    {
        return prefabs[UnityEngine.Random.Range(0, prefabs.Length)];
    }

    public GameObject GetPrefab(string name) {
        var index = -1;
        if (name == "cube") {
            index = 0;
        } else if (name == "diamond") {
            index = 1;
        } else if (name == "heart") {
            index = 2;
        } else if (name == "plus") {
            index = 3;
        } else if (name == "star") { 
            index = 4;
        } else if (name == "triangle") { 
            index = 5;
        } else if (name == "torus") { 
            index = 6;
        } else { 
            Debug.Log("Could not identify prefab name " + name);
        }

        return prefabs[index];
    }
}
