using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SqlKata.Execution;
using System.IO;
using System;
using Newtonsoft.Json.Linq;
using Unity.VisualScripting;
using System.Linq;

/// <summary>
/// JSON-DB間データ変換処理クラス
/// </summary>
public static class ConvertJSONToDB
{
    public static void importJSONToDB(QueryFactory factory)
    {
        Logger.DebugLog("importJSONToDB start");

        // マッピングデータJSONファイルリスト取得
        List<string> mapJsonFiles = FileSearch.searchByExtention(StaticParameters.mappingDataDir, ".json" );

        // マッピングデータファイル毎に処理実施
        foreach( string mapJsonFile in mapJsonFiles){
            Logger.DebugLog("mapJsonFile:" + mapJsonFile);
            string mapFileText = "";
            using(var reader = new StreamReader(mapJsonFile)){
                mapFileText = reader.ReadToEnd();
            }
            JObject mapJson = JObject.Parse(mapFileText);

            JObject mappingData = (JObject)mapJson["mapping"];
            Logger.DebugLog("mappingData:");
            Logger.DebugLog(mappingData.ToString());

            if(null != mapJson["jsonDirPath"]){
                string importDataDir = (string)mapJson["jsonDirPath"];
                Logger.DebugLog(importDataDir);

                // DBへの投入データJSONファイルリスト取得
                List<string> importJsonFiles = FileSearch.searchByExtention(importDataDir, ".json" );
                bool createFlg = false;
                // 投入データファイル毎に処理実施
                if(importJsonFiles.Count > 0){
                    Logger.DebugLog("importJsonFile exist, importJsonFiles.Count:" + importJsonFiles.Count);
                    foreach( string importJsonFile in importJsonFiles){
                        Logger.DebugLog("importJsonFile:" + importJsonFile);
                        string importFileText = "";
                        using(var reader = new StreamReader(importJsonFile)){
                            importFileText = reader.ReadToEnd();
                        }
                        JObject importJson = JObject.Parse(importFileText);

                        Logger.DebugLog("importJson:");
                        Logger.DebugLog(importJson.ToString());
                        // DB投入用情報作成
                        JObject dbStatementCre = new JObject(); // DBcreate投入文面用辞書型リスト
                        JObject dbStatementIns = new JObject(); // DBinsert投入文面用辞書型リスト

                        dbStatementCre = createCreStatement(mappingData, importJson, dbStatementCre, 1);
                        Logger.DebugLog("dbStatementCre:");
                        Logger.DebugLog(dbStatementCre.ToString());
                        dbStatementIns = createInsStatement(importJson, dbStatementCre, dbStatementIns);
                        Logger.DebugLog("dbStatementIns:");
                        Logger.DebugLog(dbStatementIns.ToString());

                        // DB投入実施
                        // createはDBマッピングデータごとに初回のみ実施
                        if(!createFlg){
                            Logger.DebugLog("queryCreateTable execute createFlg: " + createFlg);
                            queryCreateTable(dbStatementCre, factory);
                            createFlg = true;
                            Logger.DebugLog("queryCreateTable executed createFlg: " + createFlg);
                        }
                        queryInsertFromStatementJson(dbStatementIns, factory);
                        Logger.DebugLog("queryInsertFromStatementJson executed");
                    }
                } else {
                    Logger.DebugLog("importJsonFile not exist, importJsonFiles.Count:" + importJsonFiles.Count);
                    // 投入jsonデータが無い場合はテーブル作成のみ実施
                    Logger.DebugLog("jsonDirPath not found, create only execute");
                    // DB投入用情報作成
                    JObject dbStatementCre = new JObject(); // DBcreate投入文面用辞書型リスト
                    dbStatementCre = createCreStatement(mappingData, dbStatementCre);
                    Logger.DebugLog("dbStatementCre:");
                    Logger.DebugLog(dbStatementCre.ToString());
                    // DB投入実施
                    queryCreateTable(dbStatementCre, factory);
                    Logger.DebugLog("queryCreateTable executed");
                }
            } else {
                // 投入jsonデータが無い場合はテーブル作成のみ実施
                Logger.DebugLog("jsonDirPath not found, create only execute");
                // DB投入用情報作成
                JObject dbStatementCre = new JObject(); // DBcreate投入文面用辞書型リスト
                dbStatementCre = createCreStatement(mappingData, dbStatementCre);
                Logger.DebugLog("dbStatementCre:");
                Logger.DebugLog(dbStatementCre.ToString());
                // DB投入実施
                queryCreateTable(dbStatementCre, factory);
                Logger.DebugLog("queryCreateTable executed");
            }
        }

        Logger.DebugLog("importJSONToDB end");
    }

    // create table用データからcreate table文面を作成して投入する
    private static void queryCreateTable(JObject dbStatementCre, QueryFactory factory)
    {
        Logger.DebugLog("queryCreateTable START");
        foreach (var creTableElement in dbStatementCre){
            // テーブル毎のcreate table文面作成
            Logger.DebugLog("creTableElement.Key: " + creTableElement.Key);
            string createStatement = "create table " + creTableElement.Key + "(";
            Logger.DebugLog("[table]createStatement: " + createStatement);

            // PRIMARY KEY/UNIQUE用リスト作成
            List<string> primaryColumns = new List<string>();
            List<string> uniqueColumns = new List<string>();

            // 各カラム分の文面追記
            foreach (var creColumnElement in (JObject)creTableElement.Value){
                Logger.DebugLog("creColumnElement.Key: " + creColumnElement.Key);
                // RESERVED_insertCountは無視
                if( "RESERVED_insertCount" == creColumnElement.Key ){
                    Logger.DebugLog("RESERVED_insertCount is ignored");
                    continue;
                }
                string columnType = (string)creColumnElement.Value["columnType"];
                JArray columnOptions = (JArray)creColumnElement.Value["columnOption"];
                createStatement += creColumnElement.Key + " " + columnType;
                Logger.DebugLog("[column]createStatement: " + createStatement);
                // カラムオプションの追記
                foreach(string columnOptionElement in columnOptions){
                    // 複合PRIMARY KEY/UNIQUEの考慮。PRIMARY KEY/UNIQUEは別で分けておき最後に記述
                    if( "primary key" == columnOptionElement.ToLower()){
                        primaryColumns.Add(creColumnElement.Key);
                        Logger.DebugLog("[columnOption primary]primaryColumns: " + string.Join(", ", primaryColumns.ToArray()));
                    } else if ( "unique" == columnOptionElement.ToLower()){
                        uniqueColumns.Add(creColumnElement.Key);
                        Logger.DebugLog("[columnOption unique]uniqueColumns: " + string.Join(", ", uniqueColumns.ToArray()));
                    } else {
                        createStatement += " " + columnOptionElement;
                        Logger.DebugLog("[columnOption not primary]createStatement: " + createStatement);
                    }
                }
                createStatement += ",";
                Logger.DebugLog("[comma]createStatement: " + createStatement);
            }

            // PRIMARY KEYの記述
            if ( 0 != primaryColumns.Count) {
                Logger.DebugLog("[columnOption primary exist]primaryColumns.Count: " + primaryColumns.Count);
                createStatement += "primary key(";
                foreach(string primaryColumn in primaryColumns){
                    createStatement += primaryColumn + ",";
                    Logger.DebugLog("[columnOption primary exist]createStatement: " + createStatement);
                }
                createStatement = createStatement.RemoveEnd(1);
                createStatement += "),";
            }

            // UNIQUEの記述
            if ( 0 != uniqueColumns.Count) {
                Logger.DebugLog("[columnOption unique exist]uniqueColumns.Count: " + uniqueColumns.Count);
                createStatement += "unique(";
                foreach(string uniqueColumn in uniqueColumns){
                    createStatement += uniqueColumn + ",";
                    Logger.DebugLog("[columnOption unique exist]createStatement: " + createStatement);
                }
                createStatement = createStatement.RemoveEnd(1);
                createStatement += "),";
            }
            
            createStatement = createStatement.RemoveEnd(1);
            createStatement += ");";
            Logger.DebugLog("[end]createStatement: " + createStatement);

            // DB投入実施
            factory.Statement(createStatement);
            Logger.DebugLog("execute: " + createStatement);
        }
        Logger.DebugLog("queryCreateTable END");
    }

    // insert用データからinsert文面を作成して投入する
    private static void queryInsertFromStatementJson(JObject dbStatementIns, QueryFactory factory)
    {
        Logger.DebugLog("queryInsertFromStatementJson START");
        foreach (var insTableElement in dbStatementIns){
            // テーブル毎のinsert文面作成
            Logger.DebugLog("insTableElement.Key: " + insTableElement.Key);

            // 各Statement分の文面追記
            foreach (var insStatementElement in (JObject)insTableElement.Value){
                Logger.DebugLog("insStatementElement.Key: " + insStatementElement.Key);
                string insertStatement = "insert into " + insTableElement.Key + "(";
                Logger.DebugLog("[table]insertStatement: " + insertStatement);
                // 各カラム分の文面追記
                string colomnNameTemp = "";
                string colomnValueTemp = "";
                foreach (var insColumnElement in (JObject)insStatementElement.Value){
                    colomnNameTemp += insColumnElement.Key + ",";
                    // columnTypeによってvalueの型変換実施
                    if( "text" == ((string)insColumnElement.Value["columnType"]).ToLower()){
                        colomnValueTemp += "'" + (string)insColumnElement.Value["value"] + "',";
                        Logger.DebugLog("[text route] columnType: " + (string)insColumnElement.Value["columnType"] + " colomnValueTemp: " + colomnValueTemp);
                    } else if ( "integer" == ((string)insColumnElement.Value["columnType"]).ToLower() ){
                        colomnValueTemp += (int)insColumnElement.Value["value"] + ",";
                        Logger.DebugLog("[integer route] columnType: " + (string)insColumnElement.Value["columnType"] + " colomnValueTemp: " + colomnValueTemp);
                    } else if ( "real" == ((string)insColumnElement.Value["columnType"]).ToLower() ){
                        colomnValueTemp += (float)insColumnElement.Value["value"] + ",";
                        Logger.DebugLog("[real route] columnType: " + (string)insColumnElement.Value["columnType"] + " colomnValueTemp: " + colomnValueTemp);
                    } else if ( "json" == ((string)insColumnElement.Value["columnType"]).ToLower() ){
                        colomnValueTemp += "'" + (string)insColumnElement.Value["value"] + "',";
                        Logger.DebugLog("[json route] columnType: " + (string)insColumnElement.Value["columnType"] + " colomnValueTemp: " + colomnValueTemp);
                    } else if ( "null" == ((string)insColumnElement.Value["columnType"]).ToLower() ){
                        colomnValueTemp += "null,";
                        Logger.DebugLog("[null route] columnType: " + (string)insColumnElement.Value["columnType"] + " colomnValueTemp: " + colomnValueTemp);
                    } else if ( "blob" == ((string)insColumnElement.Value["columnType"]).ToLower() ){
                        colomnValueTemp += insColumnElement.Value["value"] + "',";
                        Logger.DebugLog("[blob route] columnType: " + (string)insColumnElement.Value["columnType"] + " colomnValueTemp: " + colomnValueTemp);
                    } else {
                        colomnValueTemp += "'" + (string)insColumnElement.Value["value"] + "',";
                        Logger.DebugLog("[else route] columnType: " + (string)insColumnElement.Value["columnType"] + " colomnValueTemp: " + colomnValueTemp);
                    }
                }
                colomnNameTemp = colomnNameTemp.RemoveEnd(1);
                colomnValueTemp = colomnValueTemp.RemoveEnd(1);
                Logger.DebugLog("[name]colomnNameTemp: " + colomnNameTemp);
                Logger.DebugLog("[value]colomnValueTemp: " + colomnValueTemp);
                insertStatement += colomnNameTemp + ") values(" + colomnValueTemp + ");";
                Logger.DebugLog("[end]insertStatement: " + insertStatement);
                // DB投入実施
                factory.Statement(insertStatement);
                Logger.DebugLog("execute: " + insertStatement);
            }
        }
        Logger.DebugLog("queryInsertFromStatementJson END");
    }


    // 投入データとマッピングデータを再帰的に分析する事でDB create table用データを生成する
    private static JObject createCreStatement(JObject mappingData, JObject importJson, JObject dbStatementCre, int insertCount)
    {
        Logger.DebugLog("createCreStatement START");
        // 各データについて末端まで解析しマッピングデータと照らし合わせてDB投入情報作成を実施
        foreach (var importJsonElement in importJson){
            Logger.DebugLog("importJsonElement.Key:" + importJsonElement.Key);
            Logger.DebugLog("insertCount:" + insertCount);

            // 該当エレメントのキーがマッピングデータに存在するかチェック
            if(null != mappingData[importJsonElement.Key]){
                Logger.DebugLog("mappingData Found");
                // 該当マッピングデータがarrayであるかどうか確認
                if(mappingData[importJsonElement.Key] is JArray){
                    // arrayである場合は投入用データを取得する。
                    Logger.DebugLog("mappingData is Array");
                    foreach(var mappingDataElement in mappingData[importJsonElement.Key]){
                        // テーブル情報を取得してDB投入用SQL文面作成を実施。JObjectに入れていく。
                        dbStatementCre = mergeCreStatementParts(dbStatementCre, mappingDataElement, importJsonElement.Value, insertCount);
                    }

                } else {
                    // arrayでない場合は次の階層へ
                    Logger.DebugLog("mappingData Not Array");
                    // 投入データの該当階層がarrayの場合はループする
                    if(importJsonElement.Value.Type is JTokenType.Array){
                        Logger.DebugLog("importJson is Array");
                        insertCount = 1;
                        foreach(JObject importJsonArrayElement in importJsonElement.Value){
                            dbStatementCre = createCreStatement((JObject)mappingData[importJsonElement.Key], importJsonArrayElement, dbStatementCre, insertCount);
                            insertCount++;
                        }
                    } else {
                        Logger.DebugLog("importJson Not Array");
                        insertCount = 1;
                        dbStatementCre = createCreStatement((JObject)mappingData[importJsonElement.Key], (JObject)importJsonElement.Value, dbStatementCre, insertCount);
                    }
                }

            } else {
                // マッピングデータに無い投入データのJSONエレメントは無視する
                Logger.DebugLog("mappingData Not Found");
            }

        }

        Logger.DebugLog("createCreStatement END");
        return dbStatementCre;
    }


    // 投入データとマッピングデータを再帰的に分析する事でDB create table用データを生成する(insertデータなし版)
    private static JObject createCreStatement(JObject mappingData, JObject dbStatementCre)
    {
        Logger.DebugLog("createCreStatement not exist insertinfo START");
        // マッピングデータについて末端まで解析しDB投入情報作成を実施
        foreach(var mappingDataColumn in mappingData){
            Logger.DebugLog("mappingDataColumn.Key:" + mappingDataColumn.Key);
            // 該当マッピングデータがarrayであるかどうか確認
            if(mappingDataColumn.Value is JArray){
                // arrayである場合は投入用データを取得する。
                Logger.DebugLog("mappingData is Array");
                foreach(var mappingDataElement in mappingDataColumn.Value){
                    // テーブル情報を取得してDB投入用SQL文面作成を実施。JObjectに入れていく。
                    dbStatementCre = mergeCreStatementParts(dbStatementCre, mappingDataElement);
                }

            } else {
                // arrayでない場合は次の階層へ
                Logger.DebugLog("mappingData Not Array");
                dbStatementCre = createCreStatement((JObject)mappingDataColumn.Value, dbStatementCre);
            }
        }

        Logger.DebugLog("createCreStatement not exist insertinfo END");
        return dbStatementCre;
    }

    // 個々のcreateデータをマージする
    private static JObject mergeCreStatementParts(JObject dbStatementCre, JToken mappingDataElement, JToken importJsonElement, int insertCount)
    {
        Logger.DebugLog("mergeCreStatementParts START");
        // create文面情報作成。
        // イメージ："テーブル名":{"カラム名":{"カラム型":"aaa", "カラムオプション":["bbb","ccc"], "Insert対象データパス情報":{"Statement_X":"投入JSONの対象データまでのパス"}}}
        string tableName = (string)mappingDataElement["tableName"];
        string columnName = (string)mappingDataElement["columnName"];
        string columnType = (string)mappingDataElement["columnType"];
        JArray columnOptions = (JArray)mappingDataElement["columnOption"];

        JObject columnTemp = new JObject();
        JObject columnTypeTemp = new JObject();
        JObject origPathTempArray = new JObject();
        JObject insertCountTemp = new JObject();
        JObject origPathTemp = new JObject();
        JObject columnOptionTemp = new JObject();

        columnTypeTemp.Add("columnType", columnType);
        Logger.DebugLog("columnTypeTemp-> " + columnTypeTemp.ToString());
        columnOptionTemp.Add("columnOption", columnOptions);
        Logger.DebugLog("columnOptionTemp-> " + columnOptionTemp.ToString());
        origPathTempArray.Add("Statement_" + insertCount, importJsonElement.Path);
        origPathTemp.Add("origPathInfo", origPathTempArray);
        Logger.DebugLog("origPathTemp-> " + origPathTemp.ToString());
        columnTypeTemp.Merge(origPathTemp);
        columnTypeTemp.Merge(columnOptionTemp);
        Logger.DebugLog("columnTypeTemp-> " + columnTypeTemp.ToString());
        columnTemp.Add(columnName, columnTypeTemp);
        Logger.DebugLog("columnTemp-> " + columnTemp.ToString());
        insertCountTemp.Add("RESERVED_insertCount", insertCount);
        Logger.DebugLog("insertCountTemp-> " + insertCountTemp.ToString());
        // 既に該当テーブル名が無い場合は新規追加。ある場合はマージ
        if(dbStatementCre.ContainsKey(tableName)){
            Logger.DebugLog("dbStatementCre " + tableName + " is already exist");
            // creの場合既に該当カラム名のデータがある場合はスキップ(投入データのパス情報のみマージ)
            if(((JObject)dbStatementCre[tableName]).ContainsKey(columnName)){
                Logger.DebugLog("dbStatementCre " + columnName + " is already exist, skip (merge path info only)");
                ((JObject)dbStatementCre[tableName][columnName]).Merge(origPathTemp);
                ((JObject)dbStatementCre[tableName]).Merge(insertCountTemp);
            } else {
                Logger.DebugLog("dbStatementCre " + columnName + " is already exist, merge");
                ((JObject)dbStatementCre[tableName]).Merge(columnTemp);
                ((JObject)dbStatementCre[tableName]).Merge(insertCountTemp);
            }
        } else {
            Logger.DebugLog("dbStatementCre " + tableName + " is not exist, add");
            dbStatementCre.Add(tableName, columnTemp);
            ((JObject)dbStatementCre[tableName]).Merge(insertCountTemp);
        }
        Logger.DebugLog("create table-> " + dbStatementCre.ToString());
        Logger.DebugLog("mergeCreStatementParts END");
        return dbStatementCre;
    }


    // 個々のcreateデータをマージする(insert情報無し版)
    private static JObject mergeCreStatementParts(JObject dbStatementCre, JToken mappingDataElement)
    {
        Logger.DebugLog("mergeCreStatementParts not exist insertinfo START");
        // create文面情報作成。
        // イメージ："テーブル名":{"カラム名":{"カラム型":"aaa", "カラムオプション":["bbb","ccc"]}}
        string tableName = (string)mappingDataElement["tableName"];
        string columnName = (string)mappingDataElement["columnName"];
        string columnType = (string)mappingDataElement["columnType"];
        JArray columnOptions = (JArray)mappingDataElement["columnOption"];

        JObject columnTemp = new JObject();
        JObject columnTypeTemp = new JObject();
        JObject columnOptionTemp = new JObject();

        columnTypeTemp.Add("columnType", columnType);
        Logger.DebugLog("columnTypeTemp-> " + columnTypeTemp.ToString());
        columnOptionTemp.Add("columnOption", columnOptions);
        Logger.DebugLog("columnOptionTemp-> " + columnOptionTemp.ToString());
        columnTypeTemp.Merge(columnOptionTemp);
        Logger.DebugLog("columnTypeTemp-> " + columnTypeTemp.ToString());
        columnTemp.Add(columnName, columnTypeTemp);
        Logger.DebugLog("columnTemp-> " + columnTemp.ToString());
        // 既に該当テーブル名が無い場合は新規追加。ある場合はマージ
        if(dbStatementCre.ContainsKey(tableName)){
            Logger.DebugLog("dbStatementCre " + tableName + " is already exist");
            // creの場合既に該当カラム名のデータがある場合はスキップ(投入データのパス情報のみマージ)
            if(((JObject)dbStatementCre[tableName]).ContainsKey(columnName)){
                Logger.DebugLog("dbStatementCre " + columnName + " is already exist, skip");
            } else {
                Logger.DebugLog("dbStatementCre " + columnName + " is already exist, merge");
                ((JObject)dbStatementCre[tableName]).Merge(columnTemp);
            }
        } else {
            Logger.DebugLog("dbStatementCre " + tableName + " is not exist, add");
            dbStatementCre.Add(tableName, columnTemp);
        }
        Logger.DebugLog("create table-> " + dbStatementCre.ToString());
        Logger.DebugLog("mergeCreStatementParts not exist insertinfo END");
        return dbStatementCre;
    }

    // 投入データとマッピングデータを再帰的に分析する事でDB insert用データを生成する
    private static JObject createInsStatement(JObject importJson, JObject dbStatementCre, JObject dbStatementIns)
    {
        Logger.DebugLog("createInsStatement START");
        // 各データについて末端まで解析しマッピングデータと照らし合わせてDB投入を実施
        foreach (var creElement in dbStatementCre){
            Logger.DebugLog("creElement.Key-> " + creElement.Key);

            // insert文面数分ループ
            int insertCount = (int)creElement.Value["RESERVED_insertCount"];
            Logger.DebugLog("insertCount-> " + insertCount);

            for( int i = 1; i < insertCount + 1; i++ ){
                Logger.DebugLog("i-> " + i);
                // カラム数分ループ
                foreach(var creElementColumn in (JObject)creElement.Value){
                    Logger.DebugLog("creElementColumn-> " + creElementColumn.ToString());

                    // RESERVED_insertCountは無視
                    if( "RESERVED_insertCount" == creElementColumn.Key ){
                        Logger.DebugLog("RESERVED_insertCount is ignored");
                        continue;
                    }

                    JObject origPathInfo = (JObject)creElementColumn.Value["origPathInfo"];
                    Logger.DebugLog("origPathInfo-> " + origPathInfo.ToString());

                    string statementKey = "Statement_" + i;
                    string origPathTemp = "";

                    // 該当カラムの投入データパスが存在するかチェック
                    if(null != origPathInfo[statementKey]){
                        Logger.DebugLog("origPathInfo Found");
                        origPathTemp = (string)origPathInfo[statementKey];
                    } else {
                        // 無い場合は1個目のデータを使用
                        Logger.DebugLog("origPathInfo Not Found");
                        origPathTemp = (string)origPathInfo["Statement_1"];
                    }
                    Logger.DebugLog("origPathTemp-> " + origPathTemp);

                    // insert文面情報作成。
                    // イメージ："テーブル名":{"Statement_X":{"カラム名":{"columnType":"aaa", "value":"値"},"カラム名":{"columnType":"aaa", "value":"値"},...}}
                    JObject valueTemp = new JObject();
                    JObject insDataTemp = new JObject();
                    JObject columnTypeTemp = new JObject();
                    JObject statementTemp = new JObject();
                    // ここまで来ている時点で現在のデータがJSONオブジェクト/配列以外であるためinsert文面情報を追加する。
                    valueTemp.Add("value", getJValueFromPath(importJson, origPathTemp));
                    Logger.DebugLog("valueTemp-> " + valueTemp.ToString());
                    columnTypeTemp.Add("columnType", (string)creElementColumn.Value["columnType"]);
                    Logger.DebugLog("columnTypeTemp-> " + columnTypeTemp.ToString());
                    valueTemp.Merge(columnTypeTemp);
                    insDataTemp.Add(creElementColumn.Key, valueTemp);
                    Logger.DebugLog("insDataTemp-> " + insDataTemp.ToString());
                    statementTemp.Add(statementKey, insDataTemp);
                    Logger.DebugLog("statementTemp-> " + statementTemp.ToString());
                    // 既に該当テーブル名が無い場合は新規追加。ある場合はマージ
                    if(dbStatementIns.ContainsKey(creElement.Key)){
                        Logger.DebugLog("dbStatementIns " + creElement.Key + " is already exist, merge");
                        ((JObject)dbStatementIns[creElement.Key]).Merge(statementTemp);
                    } else {
                        Logger.DebugLog("dbStatementIns " + creElement.Key + " is not exist, add");
                        dbStatementIns.Add(creElement.Key, statementTemp);
                    }
                    Logger.DebugLog("insert-> " + dbStatementIns.ToString());
                }
            }


        }

        Logger.DebugLog("createInsStatement END");
        return dbStatementIns;
    }

    // JObjectからtargetPathで指定されたパスにあるJTokenを取り出す
    // targetPath設定例："connections[0].destBaseName"
    private static JToken getJValueFromPath(JObject targetObj, string targetPath)
    {
        Logger.DebugLog("getJValueFromPath START");
        Logger.DebugLog("targetObj-> " + targetObj.ToString());
        Logger.DebugLog("targetPath-> " + targetPath);
        // パス情報を分割
        string[] splitedPaths = targetPath.Split('.');
        string firstPath = splitedPaths[0];
        Logger.DebugLog("firstPath-> " + firstPath);
        IEnumerable<string> nextPaths;
        string nextPath = "";
        if( splitedPaths.Length > 1 ){
            nextPaths = splitedPaths.Skip( 1 );
            foreach( string value in nextPaths ){
                nextPath += value;
            }
        }
        Logger.DebugLog("nextPath-> " + nextPath);

        // 直近のパス文面からarrayかどうか判定。arrayの場合はkeyとindexを分離
        char[] delimiter = {'[', ']'};
        string[] firstSplitedPaths = firstPath.Split(delimiter);
        JToken nextObj;
        if (firstSplitedPaths.Length > 1){
            // arrayの場合は分離したkeyとindexを指定
            nextObj = (JToken)targetObj[firstSplitedPaths[0]][int.Parse(firstSplitedPaths[1])];
        } else {
            // array以外の場合は直近のパス文面をそのまま指定
            nextObj = (JToken)targetObj[firstPath];
        }
        Logger.DebugLog("nextObj-> " + nextObj.ToString());

        // itemがツリー構造の枝/葉のどちらか判定
        if ((nextObj.Type == JTokenType.Object) || (nextObj.Type == JTokenType.Array)){
            // ObjectまたはArrayの場合は枝と判定
            Logger.DebugLog("nextObj is Object or Array, nextObj.Type-> " + nextObj.Type);
            // nextPathがある場合は次の階層へ。ない場合はそのままreturn
            if (nextPath != ""){
                Logger.DebugLog("nextPath exist");
                nextObj = getJValueFromPath((JObject)nextObj, nextPath);
            } else {
                Logger.DebugLog("nextPath not exist");
            }

        } else {
            // ObjectまたはArray以外の場合は葉と判定してreturn
            Logger.DebugLog("nextObj is not Object or Array, nextObj.Type-> " + nextObj.Type);
        }

        Logger.DebugLog("getJValueFromPath END");
        return nextObj;
    }

    internal class StrategyMap
    {
        public string mapname { get; set; }
    }
}
