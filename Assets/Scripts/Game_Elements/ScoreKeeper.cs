using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class ScoreKeeper : MonoBehaviour
{

    public int score = 0;
    public Text scoreDisplay;

    void OnEnable()
    {
        score = 0;
        UpdateScore();
        Restarter.OnRestartEvent += ResetScore;
        Application.runInBackground = true;
    }

    void OnDisable()
    {
        Restarter.OnRestartEvent -= ResetScore;
    }
    public void ResetScore()
    {
      score = 0;
      UpdateScore();
    }

    public void ScoredSet()
    {
        score += 1;
        UpdateScore();
    }

    void UpdateScore() { scoreDisplay.text = score.ToString(); }
}
