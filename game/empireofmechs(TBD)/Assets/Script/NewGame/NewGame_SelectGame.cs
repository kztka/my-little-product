using System.Collections;
using System.Collections.Generic;
using Unity.Jobs.LowLevel.Unsafe;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class NewGame_SelectGame : MonoBehaviour
{
    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    // clickButton is called when player clicked button
    public void clickButton(string gamename)
    {
        Logger.DebugLog("GameSelect onclick gamename: " + gamename);
        // 選択したゲーム名をScroll ViewのScriptに設定
        NewGame_ScrollView scrollViewScript = GameObject.Find("GameSelectScrollView").GetComponent<NewGame_ScrollView>();
        scrollViewScript.selectedGameName = gamename;

        // ボタンの色を選択以外は元に戻し選択したものは色を変更する
        // 親オブジェクトを取得し配下オブジェクトの色を全て元に戻す
        for (int i = 0; i < transform.parent.childCount; i++){
            GameObject childObject = transform.parent.GetChild(i).gameObject;
            Button buttonInTMPother = childObject.GetComponent<Button>();
            ColorBlock tmpColorsOther = buttonInTMPother.colors;
            tmpColorsOther.selectedColor = new Color (245, 245, 245, 255);
            buttonInTMPother.colors = tmpColorsOther;
        }

        // 選択ボタンの色を変更
        Button buttonInTMP = transform.GetComponent<Button>();
        ColorBlock tmpColors = buttonInTMP.colors;
        tmpColors.selectedColor = new Color (0, 0, 0, 255);
        buttonInTMP.colors = tmpColors;
        
        Logger.DebugLog("selectedGameName: " + scrollViewScript.selectedGameName);
    }
}
