using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Screenshot : MonoBehaviour
{
    //might not need these 
    public Camera viewCamera;
    private string screenshotName;
    private byte[] tb;

    //For Testing
    //void LateUpdate()
    //{
    //    if (Input.GetKeyDown(KeyCode.P)){
    //        TakeCameraScreenShot();
    //    }
    //}




    /// <summary>
    /// THIS MAIN SCREENSHOT FUNCTION _ others are similar but more tests 
    /// </summary>
    /// <returns></returns>
    public byte[] GetScreenShotBA()
    {
       
        var screenshot = new Texture2D(viewCamera.targetTexture.width, viewCamera.targetTexture.height, TextureFormat.RGB24, false);
        viewCamera.Render();
        RenderTexture.active = viewCamera.targetTexture;
        screenshot.ReadPixels(new Rect(0, 0, viewCamera.targetTexture.width, viewCamera.targetTexture.height), 0, 0);
        var newTex = Instantiate(screenshot);
        TextureScale.Bilinear (newTex, screenshot.width*3, screenshot.height*3);
        RenderTexture.active = null;
        byte[] bytes = newTex.EncodeToPNG();
        return bytes;
    }

    // for screenshots taken on moving objects, coroutine is needed to wait for end of frame to take and send the image 
    public IEnumerator CaptureView(System.Action<byte[]> callbackImg)
    {
        yield return new WaitForEndOfFrame();
        var img = GetScreenShotBA();
        callbackImg(img);

        //return ImageConversion.EncodeToJPG(screenshot);
    }


    public byte[] ObservationToTexture()
    {
        Rect oldRec = viewCamera.rect;
        
        var width = viewCamera.targetTexture.width;
        var height = viewCamera.targetTexture.height;
        //viewCamera.rect = new Rect(0f, 0f, 1f, 1f);
        var depth = 60;
        var format =RenderTextureFormat.Default;
        var readWrite = RenderTextureReadWrite.Default;

        var tempRT =
            RenderTexture.GetTemporary(width, height, depth, format, readWrite);

        var tex = new Texture2D(width, height, TextureFormat.RGB24, false);

        var prevActiveRT = RenderTexture.active;
        var prevCameraRT = viewCamera.targetTexture;

        // render to offscreen texture (readonly from CPU side)
        RenderTexture.active = tempRT;
        viewCamera.targetTexture = tempRT;

        viewCamera.Render();

        tex.ReadPixels(new Rect(0, 0, tex.width, tex.height), 0, 0);
        tex.Apply();
        viewCamera.targetTexture = prevCameraRT;
        viewCamera.rect = oldRec;
        RenderTexture.active = prevActiveRT;
        RenderTexture.ReleaseTemporary(tempRT);
        byte[] bytes = tex.EncodeToPNG();

        return bytes;
    }

}
