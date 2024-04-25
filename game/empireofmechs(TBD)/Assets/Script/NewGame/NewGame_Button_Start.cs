using System.Collections;
using System.Collections.Generic;
using Unity.Jobs.LowLevel.Unsafe;
using UnityEngine;
using UnityEngine.SceneManagement;

public class NewGame_Button_Start : MonoBehaviour
{
    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    // clickButton is called when player clicked return button
    public void clickButton()
    {
        Logger.DebugLog("Button_Start onclick start");
        // 選択したゲーム名をScroll Viewから取得
        NewGame_ScrollView scrollViewScript = GameObject.Find("GameSelectScrollView").GetComponent<NewGame_ScrollView>();
        string gamename = scrollViewScript.selectedGameName;
        if( "" == gamename ){
            // 選択されていない場合は何も起こらない
            Logger.DebugLog("Button_Start onclick end no selected game gamename:" + gamename);
        } else {
            // 選択されている場合は該当ゲーム名をスタティック変数に格納して戦略マップ画面へ
            Logger.DebugLog("Button_Start onclick end selected game gamename:" + gamename);
            StaticParameters.playingData.gamename = gamename;
            StaticParameters.playingData.currentTurn = 1;  // 現在ターン数を設定
            Logger.DebugLog("StaticParameters.playingData:" + StaticParameters.playingData.ToStringReflection());
            SceneManager.LoadScene("StrategyMap");
        }
    }
}
