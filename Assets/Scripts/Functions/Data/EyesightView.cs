using System.Collections;
using System.Collections.Generic;
using UnityEngine;

// Each player/agent gets on attached
public class EyesightView : MonoBehaviour
{

    public List<GameObject> objectsInEyesight = new List<GameObject>();

    void OnEnable()
    {
        var collider = gameObject.GetComponent<MeshCollider>();
        // enable and disable to rig the objects in sight to be included in the
        // eyesight list - when you instatiate an item the trigger won't detect
        // the items inside
        collider.enabled = false;
        collider.enabled = true;
    }

    void OnTriggerEnter(Collider other)
    {
        objectsInEyesight.Add(other.gameObject);

    }

    void OnTriggerExit(Collider other)
    {
        if (objectsInEyesight.Contains(other.gameObject))
            objectsInEyesight.Remove(other.gameObject);
    }
}
