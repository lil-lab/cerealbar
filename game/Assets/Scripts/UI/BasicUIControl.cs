using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class BasicUIControl : MonoBehaviour {


    public void OnOff()
    {
        if (gameObject.activeInHierarchy)
            gameObject.SetActive(false);
        else
            gameObject.SetActive(true);
    }

    public void OnOff(GameObject screen)
    {
        if (screen.activeInHierarchy)
            screen.SetActive(false);
        else
            screen.SetActive(true);
    }
}
