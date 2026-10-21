using System.IO;
using UnityEngine;

namespace SlipSkid.CustomContent;

// Loads card art from PNG files shipped next to the plugin DLL.
internal static class ThumbnailLoader
{
    private static readonly string PluginFolder = Path.GetDirectoryName(typeof(Plugin).Assembly.Location);

    internal static Texture2D Load(string fileName)
    {
        string path = Path.Combine(PluginFolder, fileName);
        if (!File.Exists(path))
        {
            Plugin.Log.LogWarning($"Thumbnail: {fileName} not found next to the plugin, keeping the carrier's art");
            return null;
        }

        var texture = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        if (!texture.LoadImage(File.ReadAllBytes(path)))
        {
            Plugin.Log.LogWarning($"Thumbnail: {fileName} isn't a valid PNG/JPG, keeping the carrier's art");
            Object.Destroy(texture);
            return null;
        }
        texture.name = Path.GetFileNameWithoutExtension(fileName);
        texture.hideFlags = HideFlags.DontUnloadUnusedAsset;
        Plugin.Log.LogInfo($"Thumbnail: loaded {fileName} ({texture.width}x{texture.height})");
        return texture;
    }
}
