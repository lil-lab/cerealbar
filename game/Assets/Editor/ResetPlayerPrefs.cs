 using UnityEditor;
using UnityEngine;

public class ResetPlayerPrefs : EditorWindow
{

    [MenuItem("Edit/Reset Playerprefs")]

    public static void DeletePlayerPrefs()
    {
        PlayerPrefs.DeleteAll();
    }

}
