using System.Collections;
using System.Collections.Generic;
using Unity.Jobs.LowLevel.Unsafe;
using UnityEngine;
using UnityEngine.SceneManagement;
using System.IO;
using SqlKata.Execution;
using System.Linq;

public class StrategyMap_MapCreate : MonoBehaviour
{
    // Start is called before the first frame update
    void Start()
    {
        // DBアクセス取得
        QueryFactory factory = DbAccessController.getDbConnection();
        Logger.DebugLog("get QueryFactory");

        // プレイ中のゲーム名からマップセット取得
        if( "" == StaticParameters.playingData.gamename ){
            // 万が一選択されていない場合はタイトル画面に戻る
            Logger.DebugLog("playingGame is none StaticParameters.playingGameName:" + StaticParameters.playingData.gamename);
            SceneManager.LoadScene("Title");
        } else {
            Logger.DebugLog("playingGame is exist StaticParameters.playingGameName:" + StaticParameters.playingData.gamename);
            // マップセットの一番順序が上のマップを取得
            StrategyMapSetPerGame dbTopMapSetData = factory.Query(nameof(StrategyMapSetPerGame))
                                                           .WhereColumns(nameof(StrategyMapSetPerGame) + "." + nameof(StrategyMapSetPerGame.gamename), "=", StaticParameters.playingData.gamename)
                                                           .WhereColumns(nameof(StrategyMapSetPerGame) + "." + nameof(StrategyMapSetPerGame.maporder), "=", "0")
                                                           .Get<StrategyMapSetPerGame>()
                                                           .ElementAt(0);
            Logger.DebugLog("dbTopMapSetData-> " + dbTopMapSetData.ToStringReflection());

            // マップ背景画像表示
            StrategyMap dbMapData = factory.Query(nameof(StrategyMap))
                                            .WhereColumns(nameof(StrategyMap) + "." + nameof(StrategyMap.mapname), "=", dbTopMapSetData.mapname)
                                            .Get<StrategyMap>()
                                            .ElementAt(0);
            GameObject tmpBgObj = new GameObject("BG_" + dbTopMapSetData.mapname );
            tmpBgObj.AddComponent<SpriteRenderer>();
            SpriteRenderer tmpBgSr = tmpBgObj.GetComponent<SpriteRenderer>();
            // テクスチャ画像ファイル読み込み
            Texture2D bgTexture = TextureUtil.ReadTexture(dbMapData.bgImagePath);
            // Sprite設定  textureの中心が設定ファイルのx,ｙになるように調整(pivotを0.5fにすることで中心になる)
            Sprite createdbgSprite = Sprite.Create(bgTexture, new Rect(0, 0, bgTexture.width, bgTexture.height), new Vector2(0.5f, 0.5f), StaticParameters.pixelsPerUnit);
            tmpBgSr.sprite = createdbgSprite;
            tmpBgSr.sortingOrder = 0;
            // スケール調整
            tmpBgObj.transform.localScale = new Vector2(dbMapData.bgImageXScale, dbMapData.bgImageYScale);

            Logger.DebugLog("Object BG_" + dbTopMapSetData.mapname + " created." );

            // 基地描画
            foreach(var dbBaseData in factory.Query(nameof(StrategyBase))
                                            .WhereColumns(nameof(StrategyBase) + "." + nameof(StrategyBase.mapname), "=", dbTopMapSetData.mapname )
                                            .Get<StrategyBase>()){
                Logger.DebugLog("dbBaseData-> " + dbBaseData.ToStringReflection());
                // 基地描画
                GameObject tmpBaseObj = new GameObject("Base_" + dbBaseData.basename );
                tmpBaseObj.AddComponent<SpriteRenderer>();
                SpriteRenderer tmpSr = tmpBaseObj.GetComponent<SpriteRenderer>();
                // テクスチャ画像ファイル読み込み
                Texture2D texture = TextureUtil.ReadTexture(dbBaseData.texturePath);
                // Sprite設定  textureの中心が設定ファイルのx,ｙになるように調整(pivotを0.5fにすることで中心になる)
                Sprite createdSprite = Sprite.Create(texture, new Rect(0, 0, texture.width, texture.height), new Vector2(0.5f, 0.5f), StaticParameters.pixelsPerUnit);
                tmpSr.sprite = createdSprite;
                tmpSr.sortingOrder = 2;
                // 位置調整
                Vector2 tmpPosition = tmpBaseObj.transform.position;
                tmpPosition.x = dbBaseData.x;
                tmpPosition.y = dbBaseData.y;
                tmpBaseObj.transform.position = tmpPosition;
                // スケール調整
                tmpBaseObj.transform.localScale = new Vector2(dbBaseData.textureXScale, dbBaseData.textureYScale);

                Logger.DebugLog("Object Base_" + dbBaseData.basename + " created." );
            }

            // 基地間接続描画
            foreach(var dbConnectionData in factory.Query(nameof(StrategyConnection))
                                            .WhereColumns(nameof(StrategyConnection) + "." + nameof(StrategyConnection.mapname), "=", dbTopMapSetData.mapname )
                                            .Get<StrategyConnection>()){
                Logger.DebugLog("dbConnectionData-> " + dbConnectionData.ToStringReflection());
                // オブジェクト作成
                GameObject tmpConnectionObj = new GameObject("Connection_" + dbConnectionData.origBaseName + "-" + dbConnectionData.destBaseName );
                tmpConnectionObj.AddComponent<LineRenderer>();
                LineRenderer tmpLr = tmpConnectionObj.GetComponent<LineRenderer>();

                // 線の幅を設定
                tmpLr.startWidth = 0.1f;
                tmpLr.endWidth = 0.1f;

                // 頂点の数を設定
                tmpLr.positionCount = 2;

                // 各端点の基地座標情報を取得(各Mapにbasenameは一つしかない為情報をそのまま格納)
                StrategyBase dbOrigBaseData = factory.Query(nameof(StrategyBase))
                                            .WhereColumns(nameof(StrategyBase) + "." + nameof(StrategyBase.mapname), "=", dbTopMapSetData.mapname)
                                            .WhereColumns(nameof(StrategyBase) + "." + nameof(StrategyBase.basename), "=", dbConnectionData.origBaseName)
                                            .Get<StrategyBase>()
                                            .ElementAt(0);
                Logger.DebugLog("dbOrigBaseData-> " + dbOrigBaseData.ToStringReflection());

                StrategyBase dbDestBaseData = factory.Query(nameof(StrategyBase))
                                            .WhereColumns(nameof(StrategyBase) + "." + nameof(StrategyBase.mapname), "=", dbTopMapSetData.mapname)
                                            .WhereColumns(nameof(StrategyBase) + "." + nameof(StrategyBase.basename), "=", dbConnectionData.destBaseName)
                                            .Get<StrategyBase>()
                                            .ElementAt(0);
                Logger.DebugLog("dbDestBaseData-> " + dbDestBaseData.ToStringReflection());

                // 端点の位置を設定
                tmpLr.SetPosition(0, new Vector2(dbOrigBaseData.x, dbOrigBaseData.y));
                tmpLr.SetPosition(1, new Vector2(dbDestBaseData.x, dbDestBaseData.y));

                // レイヤー順序を設定
                tmpLr.sortingOrder = 1;

                // 画像マテリアルを設定
                tmpLr.material = new Material(Shader.Find("Sprites/Default"));

                Logger.DebugLog("Object Connection_" + dbConnectionData.origBaseName + "-" + dbConnectionData.destBaseName + " created." );
            }
        }
    }

    // Update is called once per frame
    void Update()
    {
    }
}
