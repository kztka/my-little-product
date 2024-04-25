using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using System.IO;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json;

/// <summary>
/// 全体設定ファイル(settings.json)制御クラス
/// </summary>
public static class SettingFileController
{
    // DB名

    public static void loadSettingFile()
    {
        Logger.DebugLog("loadSettingFile START");
        string settingFilePath = copySettingFile();
        Logger.DebugLog("settingFilePath: " + settingFilePath);

        string settingFileText = "";
        using(var reader = new StreamReader(settingFilePath)){
            settingFileText = reader.ReadToEnd();
        }
        JObject settingJson = JObject.Parse(settingFileText);
        StaticParameters.settingParameters = settingJson;
        Logger.DebugLog(StaticParameters.settingParameters.ToString());
        Logger.DebugLog("loadSettingFile END");
    }

    public static void saveSettingFile(JObject settingJsonToSave)
    {
        Logger.DebugLog("saveSettingFile START");
        string json = JsonConvert.SerializeObject(settingJsonToSave, Formatting.Indented);
        Logger.DebugLog("saveSettings-> " + json);
        string targetPath = Path.Combine(Application.persistentDataPath, StaticParameters.settingFileName);
        Logger.DebugLog("settingFilePath: " + targetPath);
        File.WriteAllText(targetPath, json);
        Logger.DebugLog("saveSettingFile END");
    }

    public static JObject getSettingParameters()
    {
        return StaticParameters.settingParameters;
    }

    /// <summary>
    /// ユーザ固有フォルダに設定ファイルがあるか確認しあればそのパスを返す。
    /// 無ければ工場出荷時フォルダの設定ファイルをユーザ固有フォルダにコピーする
    /// 工場出荷時フォルダにも無ければFileNotFoundExceptionをthrowする
    /// </summary>
    static string copySettingFile()
    {
        Logger.DebugLog("copySettingFile START");
        string targetPath = Path.Combine(Application.persistentDataPath, StaticParameters.settingFileName);
        if (File.Exists(targetPath)){
            Logger.DebugLog(targetPath + "に設定ファイル有り");
        } else {
            Logger.DebugLog(targetPath + "に設定ファイル無し");
            string sourcePath = Path.Combine(Application.streamingAssetsPath, StaticParameters.settingFileName);
            if (File.Exists(sourcePath)){
                Logger.DebugLog(sourcePath + "から工場出荷時設定ファイルをコピー");
                File.Copy(sourcePath, targetPath);
            } else {
                Logger.DebugLog(sourcePath + "に工場出荷時設定ファイル無しの為Exception発生");
                throw new FileNotFoundException(sourcePath);
            }
        }
        Logger.DebugLog("copySettingFile END");
        return targetPath;
    }

}
