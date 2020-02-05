using System.Collections;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.IO;
using System;
using UnityEngine;
using UnityEngine.UI;

public class StartUIControl : BasicUIControl
{
    [DllImport("__Internal")]
    private static extern string PlayersMatched(string ID);

    public HexGrid hexGrid;
    public GameObject controlCenter;
    public GameObject background;
    private WebSocketManager webSocketManager;

    public Button lobbyButton;
    public Button leaderQualBtn;
    public Button followerQualBtn;
    public Button UIDButton;
    public Button startButton;
    public Button standaloneStartButton;
    public Button optionsButton;
    public Text status;
    public Text lobbyStatus;
    public Text lobbyInfo;
    public Text startButtonText;

    public GameObject characterPanel;
    public Text characterText;

    public GameObject promptText;
    private AudioSource audioSource;
    private Image backgroundImage;

    private bool startClicked = false;
    private bool lookingForPartner = false;
    public bool gameStarted;
    private readonly Color darkBlue = new Color32(33,140,253,255);
    private readonly Color lightBlue = new Color32(81,197,255,255);
    public string character;

    public static string qid;

    void Awake()
    {
        backgroundImage = background.GetComponent<Image>();
        backgroundImage.material.SetColor("_Color", darkBlue);
        backgroundImage.material.SetColor("_Color2", lightBlue);
        audioSource = GetComponent<AudioSource>();
        Time.timeScale = 1;
        lobbyButton.interactable = false;
        leaderQualBtn.interactable = false;
        followerQualBtn.interactable = false;
    }

    void OnEnable()
    {
        gameStarted = false;
        webSocketManager = FindObjectOfType<WebSocketManager>();
        PropPlacement.OnMapCompleteEvent += DeactivateStart;

        #if UNITY_WEBGL
        standaloneStartButton.gameObject.SetActive(false);
        #endif

        #if UNITY_STANDALONE
        startButton.gameObject.SetActive(false);
        status.gameObject.SetActive(false);
        #endif
    }

    void OnDisable()
    {
        PropPlacement.OnMapCompleteEvent -= DeactivateStart;
    }

    public void JoinLobby()
    {
        if (!startClicked)
        {
            startClicked = true;
            lobbyButton.interactable = false;
            lookingForPartner = true;
            StartCoroutine(FindingPartner());
        }
    }

    private IEnumerator FindingPartner()
    {
        while(lookingForPartner)
        {
            if(lookingForPartner){ lobbyStatus.text = "<b>Finding a partner.</b>"; }
            yield return new WaitForSeconds(1);
            if(lookingForPartner){ lobbyStatus.text = "<b>Finding a partner..</b>"; }
            yield return new WaitForSeconds(1);
            if(lookingForPartner){ lobbyStatus.text = "<b>Finding a partner...</b>"; }
            yield return new WaitForSeconds(1);
        }
        yield break;
    }

    public void LobbyReady()
    {
        if (!webSocketManager.applicationHasFocus)
        {
            audioSource.Play();
        }

        if (character == "Human") { 
            characterPanel.GetComponent<Image>().color = new Color32(244,220,98,255);

            characterText.text = "You are the <b>Leader</b>.\n\nYour job is to collaborate with your "
                            + "partner by <b>planning card sets</b>, <b>giving your partner commands</b>, "
                            + "and selecting cards.";
        } else {
            characterPanel.GetComponent<Image>().color = new Color32(225,119,215,255);
            characterText.text = "You are the <b>Follower</b>.\n\nYour job is to collaborate with your "
                            + "partner by <b>following commands</b> exactly as they are described.";
        }
        characterPanel.SetActive(true);
        optionsButton.interactable = false;
        optionsButton.gameObject.SetActive(false);
        promptText.gameObject.SetActive(false);

        lookingForPartner = false;
        lobbyStatus.text = "<b>Partner Found!</b>";
        startButtonText.text = "<b>Ready to Start Game!</b>";
        startButton.interactable = true;
        lobbyInfo.text = "<i>The game will begin when both players press 'Ready'!</i>";
    }

    public void ReadyPressed()
    {
        startButton.interactable = false;
        lobbyStatus.text = "<b>Starting game...</b>";
    }

    public void StartGame()
    {
        gameStarted = true;
        characterPanel.SetActive(false);
        characterText.text = "";
    }

    private void DeactivateStart()
    {
        var setup = controlCenter.GetComponent<CommandCenterSetup>();
        controlCenter.SetActive(true);
        setup.SetUp(character);
        webSocketManager.SendMap(character);
    }

    public void ResetStart()
    {
        backgroundImage = background.GetComponent<Image>();
        backgroundImage.material.SetColor("_Color", darkBlue);
        backgroundImage.material.SetColor("_Color2", lightBlue);
        startClicked = false;
        UIDButton.interactable = true;
        UIDButton.gameObject.SetActive(true);
        lobbyButton.interactable = false;
        characterPanel.SetActive(false);
        characterText.text = "";
        status.text = "<b><i>Status</i>: Ready to start another game!</b>";
        gameStarted = false;
    }

    public void AlreadyConnected()
    {
        status.text = "<b><i>Status</i>: You are already connected to the game! Check other tabs or browsers for the game. Once you've existed any other tabs, reload this page to re-join.</b>";

        // Don't allow them to put in a passcode if they are connecting via mturk.
        UIDButton.interactable = false;
        UIDButton.gameObject.SetActive(false);
    }

    public void AssignmentIDUsed()
    {
        status.text = "<b><i>Status</i>: You already used this assignment ID. Please accept another HIT if you want to play another game.</b>";

        // Don't allow them to put in a passcode if they are connecting via mturk.
        UIDButton.interactable = false;
        UIDButton.gameObject.SetActive(false);
        leaderQualBtn.interactable = true;
        leaderQualBtn.gameObject.SetActive(true);
        followerQualBtn.interactable = true;
        followerQualBtn.gameObject.SetActive(true);
    }

    public void ValidateGameAccess(string s)
    {
        if(s.Equals("Game"))
        {
            status.text = "<b><i>Status</i>: Successfully connected with your Worker ID! Ready to play game!</b>";
            UIDButton.interactable = false;
            UIDButton.gameObject.SetActive(false);
            lobbyButton.interactable = true;
            lobbyButton.gameObject.SetActive(true);
            leaderQualBtn.interactable = true;
            leaderQualBtn.gameObject.SetActive(true);
            followerQualBtn.interactable = true;
            followerQualBtn.gameObject.SetActive(true);
        } else if (s.Equals("Invalid")) {
            status.text = "<b><i>Status</i>: We couldn't find your worker ID. Did you make sure to click the link provided in the HIT? <i>Passcode is only for debugging, not for workers.</i></b>";
        } else {
            string[] components = s.Split('+');
            string workerId = components[1];
            status.text = "<b><i>Status</i>: Successfully connected to the Tutorials with worker ID " + workerId + ".</b>";
            UIDButton.interactable = false;
            UIDButton.gameObject.SetActive(false);
            leaderQualBtn.interactable = true;
            leaderQualBtn.gameObject.SetActive(true);
            followerQualBtn.interactable = true;
            followerQualBtn.gameObject.SetActive(true);
        }
    }

    public void PartnerLeftBeforeStart()
    {
      status.text = "<b><i>Status</i>: Partner quit after matching, try finding a new partner.</b>";
      lookingForPartner = false;
      startClicked = false;
      lobbyButton.interactable = true;
      startButtonText.text = "<b>Waiting to Start Game!</b>";
      startButton.interactable = false;
      lobbyInfo.text = "";
      characterPanel.SetActive(false);
      characterText.text = "";
    }

    public void PartnerLeftAfterStart()
    {
      lookingForPartner = false;
      startButton.gameObject.SetActive(false);
      lobbyStatus.text = "Partner quit after loading.";
      lobbyInfo.text = "Reload page to find a new partner.";
    }

    public void TimeOut()
    {
        lookingForPartner = false;
        startButton.gameObject.SetActive(false);
        lobbyStatus.text = "<b>Lobby Timed Out</b>";
        lobbyInfo.text = "<i>There aren't any other players around. Feel free to submit the HIT, and please return any other HITs you have from this batch.</i>";
    }
}
