using System.Collections;
using System.Collections.Generic;
using Unity.Jobs.LowLevel.Unsafe;
using UnityEngine;
using UnityEngine.SceneManagement;

public class StrategyMap_CamCtrl : MonoBehaviour
{
    private Camera cam;


    // Start is called before the first frame update
    void Start()
    {
        cam = GetComponent<Camera>();
    }

    // Update is called once per frame
    void Update()
    {
        if (cam == null)
        {
            return;
        }

        if (Input.GetMouseButton(1))  // 右クリック時
        {
            // 設定ファイル値取得
            float camMoveSensitive = (float)StaticParameters.settingParameters["gameplay"]["camMoveSensitive"];

            // move camera
            float moveX = Input.GetAxis("Mouse X") * camMoveSensitive;
            float moveY = Input.GetAxis("Mouse Y") * camMoveSensitive;
            cam.transform.localPosition -= new Vector3(moveX, moveY, 0.0f);
        }

        // 設定ファイル値取得
        float camZoomSensitive = (float)StaticParameters.settingParameters["gameplay"]["camZoomSensitive"];
        int camZoomReverse = (int)StaticParameters.settingParameters["gameplay"]["camZoomReverse"];
        // zoom camera
        float moveZ = Input.GetAxis("Mouse ScrollWheel") * camZoomSensitive;
        moveZ = moveZ * camZoomReverse;
        //cam.transform.position += cam.transform.forward * moveZ;
        // ホイールが動いている場合のみ
        if(moveZ != 0){
            //Logger.DebugLog("wheel move moveZ:" + moveZ );
            if(cam.orthographicSize > StaticParameters.minCamOrthographicSize && cam.orthographicSize < StaticParameters.maxCamOrthographicSize){
                cam.orthographicSize += moveZ;
                /*Logger.DebugLog("cam.orthographicSize > " + StaticParameters.minCamOrthographicSize + 
                                " && cam.orthographicSize < " + StaticParameters.maxCamOrthographicSize + 
                                "   cam.orthographicSize:" + cam.orthographicSize + " moveZ:" + moveZ );*/
            } else if (cam.orthographicSize <= StaticParameters.minCamOrthographicSize && moveZ > 0) {
                cam.orthographicSize += moveZ;
                /*Logger.DebugLog("cam.orthographicSize <= " + StaticParameters.minCamOrthographicSize + 
                                " && moveZ > 0   cam.orthographicSize:" + cam.orthographicSize + " moveZ:" + moveZ );*/
            } else if (cam.orthographicSize >= StaticParameters.maxCamOrthographicSize && moveZ < 0) {
                cam.orthographicSize += moveZ;
                /*Logger.DebugLog("cam.orthographicSize >= " + StaticParameters.maxCamOrthographicSize + 
                                " && moveZ < 0   cam.orthographicSize:" + cam.orthographicSize + " moveZ:" + moveZ );*/
            } else if (cam.orthographicSize <= StaticParameters.minCamOrthographicSize && moveZ < 0) {
                cam.orthographicSize = StaticParameters.minCamOrthographicSize;
                /*Logger.DebugLog("cam.orthographicSize <= " + StaticParameters.minCamOrthographicSize + 
                                " && moveZ < 0   cam.orthographicSize:" + cam.orthographicSize + " moveZ:" + moveZ );*/
            } else if (cam.orthographicSize >= StaticParameters.maxCamOrthographicSize && moveZ > 0) {
                cam.orthographicSize = StaticParameters.maxCamOrthographicSize;
                /*Logger.DebugLog("cam.orthographicSize >= " + StaticParameters.maxCamOrthographicSize + 
                                " && moveZ > 0   cam.orthographicSize:" + cam.orthographicSize + " moveZ:" + moveZ );*/
            } else {
                //Logger.DebugLog("else nothing to do   cam.orthographicSize:" + cam.orthographicSize + " moveZ:" + moveZ );
            }
        }
    }

}
