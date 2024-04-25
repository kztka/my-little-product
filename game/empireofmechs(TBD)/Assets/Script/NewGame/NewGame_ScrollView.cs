using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;
using SqlKata.Execution;
using UnityEngine.UI;


public class NewGame_ScrollView : MonoBehaviour
{
    public string selectedGameName = "";

    // Start is called before the first frame update
    void Start()
    {
        // DBからゲームリストを取得しスクロールビューに表示
        // DBアクセス取得
        QueryFactory factory = DbAccessController.getDbConnection();
        Logger.DebugLog("get QueryFactory");

        // ゲーム名を表示
        foreach(var dbGameData in factory.Query(nameof(Game))
                                         .Get<Game>()){
            Logger.DebugLog("dbGameData-> " + dbGameData.ToStringReflection());
            // 作成したTextをviewport/contentに配置
            GameObject TMPObject = new GameObject("TMPText_" + dbGameData.gamename);
            TMPObject.AddComponent<TextMeshProUGUI>();
            TextMeshProUGUI gameNameText = TMPObject.GetComponent<TextMeshProUGUI>();
            gameNameText.text = dbGameData.gamename;

            GameObject content = transform.Find("Viewport/Content").gameObject;
            TMPObject.transform.SetParent(content.transform);
            Vector3 scale = TMPObject.transform.localScale;
            scale.Set(1,1,1);
            TMPObject.transform.localScale = scale;

            TMPObject.AddComponent<Button>();
            Button buttonInTMP = TMPObject.GetComponent<Button>();
            ColorBlock tmpColors = buttonInTMP.colors;  // button.colors配下は直接変更できないので一旦テンポラリ変数に入れる
            tmpColors.pressedColor = new Color (0, 0, 0, 255);
            buttonInTMP.colors = tmpColors;

            // クリック時のゲーム選択スクリプトを設定
            TMPObject.AddComponent<NewGame_SelectGame>();
            NewGame_SelectGame selectGameScript = TMPObject.GetComponent<NewGame_SelectGame>();
            buttonInTMP.onClick.AddListener(()=>selectGameScript.clickButton(dbGameData.gamename));
        
            Logger.DebugLog("Object TMPText_" + dbGameData.gamename + " created." );
        }
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}
