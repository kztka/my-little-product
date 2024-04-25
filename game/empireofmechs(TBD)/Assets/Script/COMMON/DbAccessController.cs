using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Microsoft.Data.Sqlite;
using SqlKata.Execution;
using SqlKata.Compilers;
using UnityEngine.Networking;

/// <summary>
/// SQLite3のDBアクセス制御クラス
/// </summary>
public static class DbAccessController
{
    // DB名

    public static QueryFactory createDbConnection()
    {
        if( null != StaticParameters.queryFactory ){
            Logger.DebugLog("DB接続存在済みの為return");
            return StaticParameters.queryFactory;
        }

        DeleteDB();
        CloneDB();

        SqliteConnectionStringBuilder builder = new SqliteConnectionStringBuilder
        {
            DataSource = System.IO.Path.Combine(GetPlatFormDataPath(), StaticParameters.s_dbName)
        };

        SQLitePCL.Batteries_V2.Init();

        Logger.DebugLog("接続確認");

        SqliteConnection dbConnection = new SqliteConnection(builder.ConnectionString);

        // SQLiteのバージョン出力
        Logger.DebugLog("バージョン情報：" + dbConnection.ServerVersion);

        SqliteCompiler compiler = new SqliteCompiler();
        StaticParameters.queryFactory = new QueryFactory(dbConnection, compiler);

        return StaticParameters.queryFactory;
    }

    public static void closeDbConnection()
    {
        Logger.DebugLog("DB connection close実施");
        StaticParameters.queryFactory.Connection.Close();
    }

    public static QueryFactory getDbConnection()
    {
        return StaticParameters.queryFactory;
    }

    static string GetPlatFormDataPath()
    {
        return Application.persistentDataPath;
    }

    static void CloneDB()
    {
        string targetPath = System.IO.Path.Combine(GetPlatFormDataPath(), StaticParameters.s_dbName);
        if (System.IO.File.Exists(targetPath)){
            Logger.DebugLog(targetPath + "にDB有り");
            return;
        }
        string sourcePath = System.IO.Path.Combine(Application.streamingAssetsPath, StaticParameters.s_dbName);
        if (!System.IO.File.Exists(sourcePath)){
            Logger.DebugLog(sourcePath + "にDB無しのため新規作成");
            SqliteConnectionStringBuilder builder = new SqliteConnectionStringBuilder
            {
                DataSource = sourcePath
            };
            using (SqliteConnection connection = new SqliteConnection(builder.ConnectionString))
            {
                connection.Open();
                connection.Close();
            }
        }
        System.IO.File.Copy(sourcePath, targetPath);
    }

    static void DeleteDB()
    {
        string targetPath = System.IO.Path.Combine(GetPlatFormDataPath(), StaticParameters.s_dbName);
        if (System.IO.File.Exists(targetPath)){
            Logger.DebugLog(targetPath + "にDB有りの為削除");
            System.IO.File.Delete(targetPath);
        }
        string sourcePath = System.IO.Path.Combine(Application.streamingAssetsPath, StaticParameters.s_dbName);
        if (System.IO.File.Exists(sourcePath)){
            Logger.DebugLog(sourcePath + "にDB有りの為削除");
            System.IO.File.Delete(sourcePath);
        }
    }
}
