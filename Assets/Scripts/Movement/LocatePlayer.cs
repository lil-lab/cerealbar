using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class LocatePlayer : MonoBehaviour
{

    public GameObject locator;
    private Transform arrowImg;
    private bool isLocating;
    private Vector3 animationDistance = new Vector3(0f,8f,0f);
    private float animationSpeed = 3;
    private bool goingUp = true;
    private float deltaPos = 0;

    #if !SIMULATING
    void OnEnable()
    {
      isLocating = true;
      locator.SetActive(true);
      arrowImg = locator.gameObject.transform.GetChild(0).GetChild(0);
      arrowImg.Rotate(0, 25, 0);
    }
    #endif

    #if SIMULATING
    void OnEnable()
    {
      locator.SetActive(false);
      enabled = false;
    }
    #endif

    void OnDisable()
    {
      isLocating = false;
    }

    #if !SIMULATING
    void Update()
    {
      if (isLocating)
      {
        AnimateLocator();
        if(!TurnController.isFirstTurn) { locator.SetActive(false); }
      }
      // Old locator disabling function:
      /*if (Input.anyKey)
      {
        locator.SetActive(false);
        enabled = false;
      }*/
    }
    #endif

    private void AnimateLocator()
    {
      var move = animationSpeed * animationDistance * Time.deltaTime;
      if (goingUp)
      {
          locator.transform.position += move;
          deltaPos += Vector3.Magnitude(move);
          if (deltaPos >= animationDistance.y)
          {
              goingUp = false;
              deltaPos = 0;
          }
      }
      else // going down
      {
          locator.transform.position -= move;
          deltaPos += Vector3.Magnitude(move);
          if (deltaPos >= animationDistance.y)
          {
              goingUp = true;
              deltaPos = 0;
          }
      }
    }

}
