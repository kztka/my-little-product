using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using SqlKata.Execution;

public class Loading_GameLoad : MonoBehaviour
{
    [SerializeField] private Slider slider;
    [SerializeField] private TMP_Text loadingText;

    // Start is called before the first frame update
    void Start()
    {
        slider.value = 0;
        // DB接続
        loadingText.text = "create DB connection...";
        QueryFactory factory = DbAccessController.createDbConnection();
        Logger.DebugLog("DB接続完了");

        slider.value = 0.1f;
        // 設定ファイルの読み込み
        loadingText.text = "SettingFile Loading...";
        SettingFileController.loadSettingFile();
        Logger.DebugLog("設定ファイルの読み込み完了");

        slider.value = 0.2f;
        // ゲームファイルのDB書き込み
        loadingText.text = "GameFile Loading...";
        ConvertJSONToDB.importJSONToDB(factory);
        Logger.DebugLog("ゲームファイルのDB書き込み完了");

        // テーブル作成
        //Logger.DebugLog("テーブル作成：" + s_tableName);
        // scenesテーブルからidカラムのデータを取得する。
        //foreach (System.Object obj in factory.Query(s_tableName).Select(s_columnName).Get<System.Object>())
        //{
            // テーブルからデータを取得できているか確認
        //    Logger.DebugLog(obj.ToString());
        //}

        //100% 次画面遷移
        slider.value = 1;
        SceneManager.LoadScene("Title");
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}
