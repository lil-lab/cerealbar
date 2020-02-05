using System.Collections;
using System.Collections.Generic;
using System;
using UnityEngine.Networking;
using UnityEngine.UI;
using UnityEngine;
using System.IO;
using System.Runtime.InteropServices;


#pragma warning disable 0414
/// <summary>
/// Main control for two player functions when running the game as a standalone
/// build.
/// </summary>
public class SelfCommunication : MonoBehaviour
{
    private TurnController turnController;

    void OnEnable()
    {
      turnController = FindObjectOfType<TurnController>();
    }

    void OnDisable()
    {

    }
}
