using UnityEngine;

[CreateAssetMenu()]
/// <summary>
/// Stores a list of materials to choose from.
/// </summary>
public class MaterialsDB: ScriptableObject
{
    // The list of materials.
    public Material[] materials;

    /// <summary>
    /// Chooses a random material from the materials list, and returns it.
    /// </summary>
    public Material GetRandomMaterial()
    {
        return materials[UnityEngine.Random.Range(0, materials.Length)];
    }

    public Material GetMaterial(string name)
    {
        int index = -1;
        if (name == "blue") {
            index = 0;
        } else if (name == "green") {
            index = 1;
        } else if (name == "pink") {
            index = 2;
        } else if (name == "red") {
            index = 3;
        } else if (name == "yellow") { 
            index = 4;
        } else if (name == "black") {
            index = 5;
        } else if (name == "orange") {
            index = 6;
        } else {
            Debug.Log("Could not identify color: " + name);
        }

        return materials[index];
    }
}
