using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class CommandCenterSetup : MonoBehaviour
{
    public GameObject startScreen;
    public GameObject lobbyScreen;
    public Text characterDisplay;
    public Text myTurnDisplay;
    public Text totalTurnsDisplay;
    public Text controlsInfoDisplay;
    public Text timeLeftDisplay;
    public Button endTurnButton;
    public ScrollRect commandHistoryRect;

    List<GameObject> humanOnlyObjects;
    public GameObject miniAgentView;
    public Text agentViewDisplayLabel;
    public Button submitButton;
    public InputField commandField;
    public ScrollRect leaderScrollRect;

    List<GameObject> agentOnlyObjects;
    public Button finishCommandButton;
    public GameObject finishCommandBanner;
    public ScrollRect followerScrollRect;

    public GameObject mainScreen;
    public RenderTexture agent_pov_forAgent;
    public RenderTexture agent_pov_forHuman;
    public RenderTexture angled_main_view;
    public RenderTexture overhead_main_view;
    public Button toggleMainViewButton;
    private bool isDisplayAngled;
    private RawImage mainRawImage;
    private bool isDisplayingHuman; //true if main screen is human view, false if agent view

    public delegate void OnMovementSetupHandler();
    public static event OnMovementSetupHandler OnMovementSetupEvent;

    void Awake()
    {
        humanOnlyObjects = new List<GameObject>();
        humanOnlyObjects.Add(miniAgentView);
        humanOnlyObjects.Add(submitButton.gameObject);
        humanOnlyObjects.Add(commandField.gameObject);
        humanOnlyObjects.Add(agentViewDisplayLabel.gameObject);
        humanOnlyObjects.Add(toggleMainViewButton.gameObject);
        humanOnlyObjects.Add(leaderScrollRect.gameObject);

        agentOnlyObjects = new List<GameObject>();
        agentOnlyObjects.Add(finishCommandButton.gameObject);
        agentOnlyObjects.Add(followerScrollRect.gameObject);
    }

    public void SetUp(string character) {
        var movementTypes = FindObjectsOfType<MovementType>();
        for (int i = movementTypes.Length-1; i>=0; i--)
        {
          movementTypes[i].SetControl(character);
        }
        commandField.text = "";
        mainRawImage = mainScreen.GetComponent<RawImage>();
        if (character=="Agent")
        {
          characterDisplay.text = "Follower";
          foreach(GameObject o in agentOnlyObjects) { 
            o.SetActive(true);
          }
          foreach (GameObject o in humanOnlyObjects) { 
            o.SetActive(false);
          }
          commandField.readOnly = true;
          endTurnButton.gameObject.SetActive(false);
          //commandHistoryRect.GetComponent<RectTransform>().sizeDelta = new Vector2(1040, 263);
          // var ag = GameObject.FindGameObjectWithTag("Agent"); Commented out because of 0414 disuse warning
          mainRawImage.texture = agent_pov_forAgent;
          isDisplayingHuman = false;
          controlsInfoDisplay.text+= "<b>Follower Only</b>:\n\t- When you run out of moves, your turn ends automatically";

          finishCommandButton.interactable = false;
          finishCommandBanner.SetActive(false);
        }
        else
        {
          characterDisplay.text = "Leader";
          foreach (GameObject o in humanOnlyObjects) { 
            o.SetActive(true);
          }
          foreach(GameObject o in agentOnlyObjects) {
            o.SetActive(false);
          }
          commandField.readOnly = false;
          endTurnButton.interactable = true;
          commandField.placeholder.GetComponent<Text>().text = "Send Command...";
          endTurnButton.gameObject.SetActive(true);
          mainRawImage.texture = angled_main_view;
          isDisplayingHuman = true;
          //commandHistoryRect.GetComponent<RectTransform>().sizeDelta = new Vector2(530, 215);
          isDisplayAngled = true;
          controlsInfoDisplay.text+= "<b>Leader Only</b>:\n\t- <i>Submit Command:</i> ENTER\n\t- <i>Toggle Camera:</i> 'Camera' Button";
        }
        #if SIMULATING
        endTurnButton.gameObject.SetActive(false);
        totalTurnsDisplay.gameObject.SetActive(false);
        myTurnDisplay.gameObject.SetActive(false);
        timeLeftDisplay.gameObject.SetActive(false);
        #endif
        OnMovementSetupEvent();
    }

    #if UNITY_WEBGL
    public void ToggleMainView()
    {
      if (isDisplayAngled) { mainRawImage.texture = overhead_main_view; }
      else { mainRawImage.texture = angled_main_view;}
      isDisplayAngled = !isDisplayAngled;
    }
    #endif

    #if UNITY_STANDALONE
    public void ToggleMainView()
    {
        if (isDisplayingHuman)
        {
            if (isDisplayAngled)
            {
              mainRawImage.texture = overhead_main_view;
              isDisplayAngled = false;
            }
            else
            {
              mainRawImage.texture = agent_pov_forAgent;
              isDisplayingHuman = false;
            }
        }
        else
        {
            mainRawImage.texture = angled_main_view;
            isDisplayingHuman = true;
            isDisplayAngled = true;
        }
    }
    #endif

    public void ToggleLeaderFollowerView(string character)
    {
      if (character=="Agent")
      {
        mainRawImage.texture = agent_pov_forAgent;
        characterDisplay.text = "Follower";
      }
      else
      {
        if (isDisplayAngled)
        {
          mainRawImage.texture = angled_main_view;
        }
        else
        {
          mainRawImage.texture = overhead_main_view;
        }
        characterDisplay.text = "Leader";
      }
      isDisplayingHuman = !isDisplayingHuman;
    }
}
