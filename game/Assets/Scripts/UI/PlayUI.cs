using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;

/// <summary>
/// Script to be attached to main play screen gameobject
/// Handles PL command screen call
///     -opening the end screen
///     -DPAD movement for queued input
/// </summary>
public class PlayUI : BasicUIControl
{
    public GameObject endScreen;
    public GameObject quitEndScreen;
    public GameObject instructionsScreen;
    public GameObject optionsScreen;
    public GameObject lobbyScreen;
    public Text infoDisplay;
    private TimeKeeper tk;

    void OnEnable() // might move this to Command Communication
    {
        tk = FindObjectOfType<TimeKeeper>();
        TurnController.GameOverEvent += OpenEndScreen;
        TurnController.GameOverQuitEvent += OpenPartnerQuitScreen;
        SetGame.OnCardActivateEvent += ShowCardActivated;
        SetGame.OnCardDeactivateEvent += ShowCardDeactivated;
    }

    void OnDisable()
    {
        TurnController.GameOverEvent -= OpenEndScreen;
        TurnController.GameOverQuitEvent -= OpenPartnerQuitScreen;
        SetGame.OnCardActivateEvent -= ShowCardActivated;
        SetGame.OnCardDeactivateEvent -= ShowCardDeactivated;
    }

    public void OpenPartnerQuitScreen()
    {
        quitEndScreen.SetActive(true);
        tk.Pause();
        gameObject.SetActive(false);
    }

    public void OpenEndScreen()
    {
        endScreen.SetActive(true);
        tk.Pause();
        gameObject.SetActive(false);
    }

    public void ShowCardActivated(GameObject card)
    {
      var str = "Result: activated "+Stringify(card);
      infoDisplay.text = str;
    }

    public void ShowCardDeactivated(GameObject card)
    {
      var str = "Result: deactivated "+Stringify(card);
      infoDisplay.text = str;
    }

    private string Stringify(GameObject card)
    {
      var props = card.GetComponent<CardProperties>();
      return ""+props.count+" "+(""+props.color).Split(' ')[0]+" "+(""+props.shape).Split(' ')[0];
    }

    public void ShowInstructions()
    {
        instructionsScreen.SetActive(true);
    }

    public void HideInstructions()
    {
        instructionsScreen.SetActive(false);
    }

    public void ShowOptions()
    {
        optionsScreen.SetActive(true);
    }

    public void HideOptions()
    {
        optionsScreen.SetActive(false);
    }

    public void ShowLobby()
    {
        lobbyScreen.SetActive(true);
    }
}
