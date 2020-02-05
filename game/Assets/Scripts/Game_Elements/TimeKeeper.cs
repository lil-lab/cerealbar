using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

// Game Timer
public class TimeKeeper : MonoBehaviour
{
    private TurnController turnController;
    public Text timeDisplay;

    public bool gameIsActive = false;
    public bool isPaused = false;
    private float maxTime = 10800f; // 3 hr

    public int humansSecondsPerTurn; //set in unity editor
    public int agentsSecondsPerTurn;
    private int curentSecondsPerTurn;

    public int gameTime;
    public int initSec;
    public int nowSec;
    private DateTime initial;
    private DateTime now;
    private int turnTime;
    private int startThisTurnsTime;

    void OnEnable()
    {
        Application.runInBackground = true;
        turnController = FindObjectOfType<TurnController>();

        gameTime = -1;
        initSec = -1;
        nowSec = -1;
        turnTime = -1;
        startThisTurnsTime = -1;
        initial = new DateTime();
        now = initial;

        WebSocketManager.OnStartGamePlayEvent += StartGT;
        Restarter.OnRestartEvent += ClearTimeKeeper;
    }

    void OnDisable()
    {
        WebSocketManager.OnStartGamePlayEvent -= StartGT;
        Restarter.OnRestartEvent -= ClearTimeKeeper;
    }

    private void StartGT()
    {
        gameIsActive = true;
        initial = System.DateTime.Now;
        initSec = initial.Hour * 3600+ initial.Minute * 60 + initial.Second;
        startThisTurnsTime = initSec;
        curentSecondsPerTurn = humansSecondsPerTurn;
        turnTime = curentSecondsPerTurn;
        #if !SIMULATING
        StartCoroutine("RunTimer");
        #endif
    }

    private void ClearTimeKeeper()
    {
        gameIsActive = false;
        isPaused = false;
        gameTime = 0;
        #if !SIMULATING
        StopCoroutine("RunTimer");
        #endif
    }

    private IEnumerator RunTimer()
    {
        while (gameTime < maxTime)
        {
            yield return new WaitForSeconds(1f);
            UpdateTime();
        }
    }

    public void Pause()
    {
        isPaused = true;
        Time.timeScale = 0;
    }

    public void Resume()
    {
        isPaused = false;
        Time.timeScale = 1;
    }

    void UpdateTime()
    {
        now = System.DateTime.Now;
        nowSec = now.Hour * 3600 + now.Minute * 60 + now.Second;
        gameTime = nowSec - initSec;
        turnTime = curentSecondsPerTurn - (nowSec - startThisTurnsTime);
        turnTime = (turnTime < 0) ? 0 : turnTime;

        if (turnTime <= 0)
        {
          if (turnController.myTurn)
            turnController.GiveTurn("Ran Out of Time");
        }
        DisplayTime(turnTime);
    }

    public void ResetTime(string character)
    {
      if (character == "Human") { curentSecondsPerTurn = humansSecondsPerTurn; }
      else { curentSecondsPerTurn = agentsSecondsPerTurn; }
      turnTime = curentSecondsPerTurn;
      DisplayTime(turnTime);

      now = System.DateTime.Now;
      nowSec = now.Hour * 3600 + now.Minute * 60 + now.Second;
      startThisTurnsTime = nowSec;
    }

    public void DisplayTime(int time)
    {
        if (turnController.myTurn)
        {
            if(time <= 15) { timeDisplay.color = Color.red; }
            else if(!TutorialGuide.tutorialMode) { timeDisplay.color = Color.black; }
            timeDisplay.text = "Time Left: " + time;
        }
        else
        {
            timeDisplay.color = Color.black;
            timeDisplay.text = "Time Left in Partner's Turn: " + time;
        }
    }
}
