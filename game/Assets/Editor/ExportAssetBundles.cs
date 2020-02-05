using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;

public class ExportAssetBundles : MonoBehaviour {

    [MenuItem("Assets/Build AssetBundles")]
    static void BuildAllAssetBundles()
    {
        string assetBundleDirectory = "Assets/AssetBundles";
        BuildPipeline.BuildAssetBundles(assetBundleDirectory, BuildAssetBundleOptions.ChunkBasedCompression, BuildTarget.WebGL);
    }
}
