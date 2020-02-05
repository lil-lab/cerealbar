using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class QuitEndUI : BasicUIControl {

    public Text score;
    public ScoreKeeper sk;

    void OnEnable()
    {
        score.text = "<i><b>Your partner quit the game. \n\n You collected " + ((int)sk.score).ToString()+" sets.</b> \n\n Return to the HIT page to give feedback and submit,"+
                     " and reload the page to play again!</i>";
    }



    public void ClearMap()
    {
        Restarter.InvokeRestart();
        System.GC.Collect(); // Force garbage collection.
    }
}
