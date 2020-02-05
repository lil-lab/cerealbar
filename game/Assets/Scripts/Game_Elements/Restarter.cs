using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Restarter : MonoBehaviour {
    public delegate void OnRestartHandler();
    public static event OnRestartHandler OnRestartEvent;

    public static void InvokeRestart()
    {
        OnRestartEvent();
    }

}
