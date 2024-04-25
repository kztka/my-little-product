using UnityEngine;
public static class Logger
{
    /// <summary>
    /// 現在のClass名, Method名をログ出力します。
    /// 引数を付けた場合は、引数の中身を文字列として出力します。
    /// </summary>
    /// <param name="logMessage">ログ出力したい場合は文字列を指定</param>
    public static void DebugLog(string logMessage = "") {

        // 1つ前のフレームを取得
        System.Diagnostics.StackFrame objStackFrame = new System.Diagnostics.StackFrame(1);
 
        // 呼び出し元のメソッド名を取得する
        string methodName = objStackFrame.GetMethod().Name + "()";

        // 呼び出し元のクラス名を取得する
        string className = objStackFrame.GetMethod().ReflectedType.FullName;

        string msg = "";
        if (logMessage != "") {
            msg = logMessage;
        }

        Debug.Log("[" + className + "] [" + methodName + "] " + msg);
    }
}
