using System.Collections;
using System.Collections.Generic;
using System;
using UnityEngine.Networking;
using UnityEngine.UI;
using UnityEngine;

/// <summary>
/// Control for handeling event where client's partner disconnects from the game.
/// </summary>
public class Disconnects : MonoBehaviour
{

    public GameObject lobby;
    private StartUIControl startUIControl;
    private SetUpUIControl setUpUIControl;
    private PlayUI playUI;
    private InstructionControl instructionControl;
    private TurnController turnController;

    void OnEnable()
    {
      startUIControl = FindObjectOfType<StartUIControl>();
      setUpUIControl = FindObjectOfType<SetUpUIControl>();
      instructionControl = FindObjectOfType<InstructionControl>();
      playUI = FindObjectOfType<PlayUI>();
      turnController = FindObjectOfType<TurnController>();
    }

    void PartnerLeft()
    {
      if (lobby.activeSelf)
      {
        if (!startUIControl.gameStarted)
        {
          setUpUIControl.SetUI();
          startUIControl.PartnerLeftBeforeStart();
        }
        else
        {
          startUIControl.PartnerLeftAfterStart();
        }
      }
      else
      {
        turnController.InvokeGameOverEvent(true);
      }
    }

}
