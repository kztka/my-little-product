using System.Collections;
using System.Collections.Generic;
using Unity.Jobs.LowLevel.Unsafe;
using UnityEngine;
using UnityEngine.SceneManagement;
using TMPro;

public class StrategyMap_Button_TurnProgress : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI currentTurnText;

    // Start is called before the first frame update
    void Start()
    {
        Logger.DebugLog("StrategyMap_Button_TurnProgress Start start");
        // 格納されている値でテキストのターン数を更新
        currentTurnText.text = "Turn " + StaticParameters.playingData.currentTurn;
        Logger.DebugLog("StrategyMap_Button_TurnProgress Start end currentTurnText.text: " + currentTurnText.text);
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    // clickButton is called when player clicked return button
    public void clickButton()
    {
        Logger.DebugLog("StrategyMap_Button_TurnProgress onclick start");
        // 現在のターン数を更新
        StaticParameters.playingData.currentTurn++;
        // テキストのターン数を更新
        currentTurnText.text = "Turn " + StaticParameters.playingData.currentTurn;
        Logger.DebugLog("StrategyMap_Button_TurnProgress onclick end currentTurnText.text: " + currentTurnText.text);
    }
}
