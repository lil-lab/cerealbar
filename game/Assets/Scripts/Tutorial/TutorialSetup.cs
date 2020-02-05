using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class TutorialSetup : MonoBehaviour
{
	public GameObject tutorial;
	private TurnController turnController;
	private TimeKeeper timeKeeper;
    private PropPlacement PropPlacement;

	void Awake()
  {
			Startup.OnTutorialStartEvent += Noobify;
			turnController = GetComponent<TurnController>();
			timeKeeper = GetComponent<TimeKeeper>();
	}

	void OnDisable()
  {
			Startup.OnTutorialStartEvent -= Noobify;
	}

	private void Noobify()
    {
		timeKeeper.humansSecondsPerTurn = 9999;
		timeKeeper.agentsSecondsPerTurn = 9999;
		turnController.initialTurns = 2000;
        turnController.leadersMovesPerTurn = 999;
        turnController.followersMovesPerTurn = 999;
		tutorial.SetActive(true);
	}
}
