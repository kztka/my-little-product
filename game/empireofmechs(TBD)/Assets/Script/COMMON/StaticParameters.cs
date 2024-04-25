using Newtonsoft.Json.Linq;
using SqlKata.Execution;

/// <summary>
/// static変数管理クラス
/// </summary>
public static class StaticParameters{

    public static readonly string mappingDataDir = ".\\Assets\\Data\\mappingJSONToDB"; // マッピングデータディレクトリ名
    public static readonly string s_dbName = "mainDB.sqlite3";  // DB名
    public static QueryFactory queryFactory = null;  // SqlKataのQuery用オブジェクト
    public static PlayingData playingData = new PlayingData();  // プレイ中ゲーム情報(DBではない方が良いセーブ対象データはここに集約)
    public static readonly int pixelsPerUnit = 100;  // ゲーム全体のpixelsPerUnit値
    public static readonly float minCamOrthographicSize = 3; // 最大ズームインカメラサイズ
    public static float maxCamOrthographicSize = 25; // 最大ズームアウトカメラサイズ  ★TODO:最大ズームアウトサイズは解像度に基づいて自動算出する？
    public static readonly string settingFileName = "settings.json";  // 全体設定ファイル名
    public static JObject settingParameters = null;  // 全体設定ファイルパラメータ格納先

}
