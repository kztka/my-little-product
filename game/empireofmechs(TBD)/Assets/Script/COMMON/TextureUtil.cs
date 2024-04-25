using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using StbImageSharp;

public static class TextureUtil
{
    public static Texture2D ReadTexture(string path, long width, long height){
        byte[] readBinary = File.ReadAllBytes(path);
        Texture2D texture = new Texture2D((int)width, (int)height);
        texture.LoadImage(readBinary);
        texture.filterMode = FilterMode.Point;
        return texture;
    }

    public static Texture2D ReadTexture(string path){
        byte[] readBinary = File.ReadAllBytes(path);
        ImageResult image = ImageResult.FromMemory(readBinary);
        Texture2D texture = new Texture2D(image.Width, image.Height);
        texture.LoadImage(readBinary);
        texture.filterMode = FilterMode.Point;
        return texture;
    }
}
