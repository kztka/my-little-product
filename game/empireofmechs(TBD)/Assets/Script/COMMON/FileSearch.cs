using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// ファイル検索共通処理クラス
/// </summary>
public static class FileSearch
{
    // 指定されたディレクトリからextentionで指定された拡張子(json等)を持つファイルのパスリストを取得する
    public static List<string> searchByExtention(string dirPath, string extention)
    {
        Logger.DebugLog("searchByExtention start dirPath:" + dirPath + " extention:" + extention);
        string[] files = System.IO.Directory.GetFiles(dirPath, "*" + extention );
        List<string> returnFiles = new List<string>();
        // GetFilesの絞り込みのみではそれ以降の拡張子があるファイルも引っかかる可能性がある為完全一致チェックを実施
        foreach (string name in files)
        {
            string ext = System.IO.Path.GetExtension(name).ToLower();
            if (0 == extention.CompareTo(ext))
            {
                returnFiles.Add(name);
            }
        }

        Logger.DebugLog("searchByExtention end returnFiles:" + string.Join(", ", returnFiles.ToArray()) );
        return returnFiles;
    }
}
