using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Linq;
using System;

public class SetGame : MonoBehaviour
{

    public PropPlacement propPlacement;
    public string character; 
    public bool reset;  // Whether the game is operating under a "reset" state, where new cards should not be added to the board.

    private WebSocketManager webSocketManager;
    private CardGenerator cardGenerator;
    private HexGrid hexgrid;
    private TurnController turnController;
    private ScoreKeeper scorekeeper;
    private InformationGetter infoGetter;

    public delegate void OnCardActivationHandler(GameObject card);
    public static event OnCardActivationHandler OnCardActivateEvent;
    public delegate void OnCardDeactivationHandler(GameObject card);
    public static event OnCardDeactivationHandler OnCardDeactivateEvent;

    public delegate void OnNoSetsHandler();
    public static event OnNoSetsHandler OnNoSetsEvent;

    public List<GameObject> activeCards = new List<GameObject>();
    private List<GameObject> cardsToRemove = new List<GameObject>(); 


    public static void InvokeCardActivation(GameObject card)
    {
        OnCardActivateEvent(card);
    }

    public static void InvokeCardDeactivation(GameObject card)
    {
        OnCardDeactivateEvent(card);
    }

    public static void InvokeNoSetsEvent()
    {
        OnNoSetsEvent();
    }

    void OnEnable()
    {
        OnCardActivateEvent += AddCard;
        OnCardDeactivateEvent += RemoveCard;
        webSocketManager = FindObjectOfType<WebSocketManager>();
        cardGenerator = FindObjectOfType<CardGenerator>();
        hexgrid = FindObjectOfType<HexGrid>();
        turnController = FindObjectOfType<TurnController>();
        scorekeeper = GetComponent<ScoreKeeper>();
        infoGetter = FindObjectOfType<InformationGetter>();
        reset = false;
    }

    void OnDisable()
    {
        OnCardActivateEvent -= AddCard;
        OnCardDeactivateEvent -= RemoveCard;
    }

    public void ForceCardActivation(GameObject card) {
        activeCards.Add(card);
        var outline = card.GetComponent<cakeslice.Outline>();
        outline.eraseRenderer = false;
        outline.color = 0;
    }

    public void ForceCardDeactivation(GameObject card) {
        activeCards.Remove(card);
        var outline = card.GetComponent<cakeslice.Outline>();
        outline.eraseRenderer = true;
    }

    /// <summary>
    /// adds newly selected card to active cards list and if 3 checks if selection is a set
    /// </summary>
    /// <param name="card"></param>
    private void AddCard(GameObject card)
    {
        webSocketManager.SendLog("selected " + CardProperties.Stringify(card));
        if (!cardsToRemove.Contains(card) && card.activeSelf && !activeCards.Contains(card)) {
            webSocketManager.SendLog("not about to remove card from board, so will add it to active cards");
            activeCards.Add(card);
        
            StartCoroutine("CheckSet");
            
            Dictionary<string, string> strData = new Dictionary<string, string>()
            {
                {"card", CardProperties.Stringify(card)},
                {"result", "ACTIVATED"}
            };
            webSocketManager.Send("result", strData, null);
        } else {
            webSocketManager.SendLog("about to remove card from board, not adding to active cards");
        }
    }

    private void RemoveCard(GameObject card)
    {
        webSocketManager.SendLog("deselected " + CardProperties.Stringify(card));
        if (!cardsToRemove.Contains(card) && card.activeSelf && activeCards.Contains(card)) {
            webSocketManager.SendLog("not about to remove card from board, so will remove it from active cards");
            activeCards.Remove(card);
            StartCoroutine("CheckSet");
            
            Dictionary<string, string> strData = new Dictionary<string, string>()
            {
                {"card", CardProperties.Stringify(card)},
                {"result", "DEACTIVATED"}
            };

            webSocketManager.Send("result", strData, null);
        } else {
            webSocketManager.SendLog("about to remove card from board; not removing from active cards");
        }
    }

    /// <summary>
    /// Checks if the current active cards are a set
    /// If they are removes them and updates score'
    /// if not it removes them from the active set forcing player to start over selection
    /// </summary>
    /// <returns></returns>
    public IEnumerator CheckSet()
    {
		yield return null;
        var materialHashSet = new HashSet<Material>();
        var countHashSet = new HashSet<int>();
        var shapeHashSet = new HashSet<GameObject>();

        foreach (var card in activeCards)
        {
            var cardProperties = card.GetComponent<CardProperties>();
            materialHashSet.Add(cardProperties.color);
            countHashSet.Add(cardProperties.count);
            shapeHashSet.Add(cardProperties.shape);
        }

        //if all 3 card components are different score
        if (activeCards.Count == 3 &&
            materialHashSet.Count == 3 &&
            countHashSet.Count == 3 &&
            shapeHashSet.Count == 3)
        {
            // IMMEDIATELY need to remove cards from the active set.
            webSocketManager.SendLog("found a valid set, including:");
            cardsToRemove = new List<GameObject>(); 
            for (int i = 0; i < 3; i++)
            {
                cardsToRemove.Add(activeCards[i]);
                webSocketManager.SendLog("active card: " + CardProperties.Stringify(activeCards[i]));
            }

            // Clearing this now means that no moveement will modify the set of
            // active cards while the set is processing
            activeCards.Clear();

            ChangeCardColors(1, cardsToRemove);
            webSocketManager.SendLog("successfully changed the card colors");

            #if !SIMULATING
            yield return new WaitForSeconds(.25f);
            #endif
            #if SIMULATING
            yield return null;
            #endif

            for (int i = 0; i < 3; i++)
            {
                cardsToRemove[i].SetActive(false);
                webSocketManager.SendLog("successfully marked card " + CardProperties.Stringify(cardsToRemove[i]) + " as inactive");
            }
            cardsToRemove.Clear();
            webSocketManager.SendLog("emptied list of cards to remove");
			yield return null;

            #if !SIMULATING
            yield return new WaitForSeconds(.25f);
            #endif
            scorekeeper.ScoredSet();
            turnController.AddMovesOnSet(scorekeeper.score);
            webSocketManager.SendLog("added a set and extra turns");
            AddMoreCards();
            webSocketManager.SendLog("added new cards");

            #if !SIMULATING
            List<string> cardStringArray = new List<string>();
            for (int i = 0; i < propPlacement.cards.Length; i++) {
                cardStringArray.Add(CardProperties.Stringify(propPlacement.cards[i]));
            }

            string cardsString = String.Join(", ", cardStringArray.ToArray());

            Dictionary<string, string> strData = new Dictionary<string, string>()
            {
              {"formed", "YES"},
              {"score", (scorekeeper.score).ToString()},
              {"cards", cardsString}
            };

            webSocketManager.Send("set", strData, null);
            #endif
        }
        else if (activeCards.Count >= 3 ||
                  (materialHashSet.Count < activeCards.Count ||
                      countHashSet.Count < activeCards.Count ||
                      shapeHashSet.Count < activeCards.Count) )
        {
          ChangeCardColors(2, activeCards);
        }
        else
        {
          ChangeCardColors(0, activeCards);
        }
		
        // I believe this is only relevant if you are simulating

        #if !SIMULATING
        yield return null;
        #endif
        #if SIMULATING
		MainControl mainControl = FindObjectOfType<MainControl>();
		yield return null;
		mainControl.updating_cards=false;
        #endif

        yield break;
    }

    public void AddMoreCards()
    {
      List<int> newCards = new List<int>();

      // 3 cards in a set.
      List<GameObject> cardsToDelete = new List<GameObject>();
      for (int i = 0; i < propPlacement.cards.Length; i++)
      {
          if (!propPlacement.cards[i].activeSelf)
          {
            cardsToDelete.Add(propPlacement.cards[i]);
            webSocketManager.SendLog("marking card " + CardProperties.Stringify(propPlacement.cards[i]) + " to delete");

            // If not in a reset state, generate a card to put in this spot instead.
            if (!reset) {
                propPlacement.cards[i] = cardGenerator.GenCard();
                newCards.Add(i);
            } else {
                propPlacement.cards[i] = null;
            }
          }
      }

      if (!reset) {
          while (!SetsExist(propPlacement.cards))
          {
              foreach (int i in newCards)
              {
                  Destroy(propPlacement.cards[i]);
                  propPlacement.cards[i] = cardGenerator.GenCard();
              }
          }
          foreach (int i in newCards)
          {
              var rndGoodCell = hexgrid.GetRandomGrassOrPathCell();
              while (propPlacement.propLocs.Contains(rndGoodCell))
              {
                  rndGoodCell = hexgrid.GetRandomGrassOrPathCell();
              }

              propPlacement.cards[i].transform.position = rndGoodCell.transform.position;
              propPlacement.propLocs.Add(rndGoodCell);
              propPlacement.walkableLocs.Add(rndGoodCell);

          }
      }
      
      // Then you delete the cards.
      foreach (var card in cardsToDelete) {
        if (card != null) {
            webSocketManager.SendLog("about to destroy card " + CardProperties.Stringify(card)); 
            Destroy(card);
         }
      }

      cardsToDelete.Clear();
      webSocketManager.SendLog("successfully destroyed all previous cards");

      Debug.Log("Reset: " + reset);
      Debug.Log("Cards:");
      for (int i = 0; i < propPlacement.cards.Length; i++) {
        Debug.Log(propPlacement.cards[i]);
      }
    }

    /// <summary>
    /// Checks if sets exist from the bunch on the map
    /// </summary>
    /// <param name="currentCards"></param>
    /// <returns></returns>
    public bool SetsExist(GameObject[] currentCards)
    {

        List<GameObject> one = new List<GameObject>();
        List<GameObject> two = new List<GameObject>();
        List<GameObject> three = new List<GameObject>();
        foreach (var card in currentCards)
        {
            try
            {
                var properties = card.GetComponent<CardProperties>();
                switch (properties.count)
                {
                  case 1:
                        one.Add(card);
                        break;
                  case 2:
                        two.Add(card);
                        break;
                  case 3:
                        three.Add(card);
                        break;
                  default:
                        Debug.Log("something wrong when detecting sets");
                        break;
                }
            }
            catch (MissingReferenceException)
            {
              Debug.Log("MissingReferenceException in SetsExist on card", card);
            }
            catch (NullReferenceException)
            {
              Debug.Log("NullReferenceException in SetsExist on card ", card);
            }
        }

        foreach (var card1 in one)
        {
          var props1 = card1.GetComponent<CardProperties>();

          foreach (var card2 in two)
          {
            var props2 = card2.GetComponent<CardProperties>();

            foreach (var card3 in three)
            {
              var props3 = card3.GetComponent<CardProperties>();

              if (props1.shape != props2.shape &&
                  props1.shape != props3.shape &&
                  props2.shape != props3.shape &&

                  props1.color != props2.color &&
                  props1.color != props3.color &&
                  props2.color != props3.color )
                  {
                    return true;
                  }
            }
          }
        }
        return false;
    }

    /// <summary>
    /// Check OutlineEffectScript for colorIndex indicating what color
    /// </summary>
    /// <param name="colorIndex"></param>
    public void ChangeCardColors(int colorIndex, List<GameObject> cards)
    {
        // Don't render cards as red if you are the agent.
        if (character == "Agent" && colorIndex == 2) {
            return;
        }

        foreach (var card in cards)
        {
            var outline = card.GetComponent<cakeslice.Outline>();
            outline.eraseRenderer = false;
            outline.color = colorIndex;
        }
    }
}
