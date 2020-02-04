using System.Collections;
using System.Collections.Generic;
using System;
using UnityEngine;
using UnityEngine.UI;

public class SetUpUIControl : BasicUIControl
{
    public GameObject startUI;
    public GameObject commandCenter;
    public GameObject lobby;
    public GameObject controls;
    public GameObject endScreen;
    public GameObject quitEndScreen;
    public GameObject options;

    void OnEnable()
    {
      SetUI();
    }

    public void SetUI()
    {
      startUI.SetActive(true);
      lobby.SetActive(false);
      commandCenter.SetActive(false);
      controls.SetActive(false);
      endScreen.SetActive(false);
      quitEndScreen.SetActive(false);
      options.SetActive(false);
    }

}
