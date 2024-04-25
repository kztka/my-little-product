using System.Collections;
using System.Collections.Generic;
using Unity.Jobs.LowLevel.Unsafe;
using UnityEngine;
using UnityEngine.SceneManagement;

public class Title_Button_Settings : MonoBehaviour
{
    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    // clickButton is called when player clicked settings button
    public void clickButton()
    {
        SceneManager.LoadScene("Settings");
    }
}
