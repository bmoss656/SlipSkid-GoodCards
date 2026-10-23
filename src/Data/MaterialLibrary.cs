using System.Collections.Generic;
using System.Globalization;
using Obstacles;
using UnityEngine;

namespace SlipSkid.CustomContent;

// Vanilla materials by name, collected from the catalog's prefabs, plus coloured copies of the
// game's toon material. Reusing the game's shaders keeps our obstacles looking native and lets
// player colours, Golden and surface swaps work on them.
internal static class MaterialLibrary
{
    private const string ToonBase = "ToonWhite";
    private static readonly Dictionary<string, Material> Vanilla = new();
    private static readonly Dictionary<Color32, Material> Toon = new();

    internal static void Collect(ObstacleDescription[] catalog)
    {
        foreach (var d in catalog)
        {
            if (!d || !d.prefab)
                continue;
            foreach (var renderer in d.prefab.GetComponentsInChildren<MeshRenderer>(true))
            {
                foreach (var material in renderer.sharedMaterials)
                {
                    if (material && !Vanilla.ContainsKey(material.name))
                        Vanilla.Add(material.name, material);
                }
            }
        }
        Plugin.Log.LogInfo($"Materials: collected {Vanilla.Count} vanilla materials");
    }

    internal static Material Resolve(string spec, Material fallback)
    {
        if (string.IsNullOrEmpty(spec))
            return fallback;
        if (spec.StartsWith("toon:"))
            return GetToon(ParseHex(spec.Substring(5)), fallback);
        if (spec.StartsWith("glow:"))
            return GetGlow(ParseHex(spec.Substring(5)), fallback);
        string name = spec switch
        {
            "primary" => "PlayerPrimaryColor",
            "secondary" => "PlayerSecondaryColor",
            "pattern" => "PlayerColorsPattern",
            _ => spec.StartsWith("mat:") ? spec.Substring(4) : spec,
        };
        if (Vanilla.TryGetValue(name, out var material))
            return material;
        Plugin.Log.LogWarning($"Materials: no vanilla material '{name}', using the carrier's");
        return fallback;
    }

    private static Material GetToon(Color32 color, Material fallback)
    {
        if (Toon.TryGetValue(color, out var cached))
            return cached;
        if (!Vanilla.TryGetValue(ToonBase, out var source))
            return fallback;
        // Keep the vanilla name: Golden and surface swaps pick materials by name.
        var material = new Material(source) { name = source.name, hideFlags = HideFlags.DontUnloadUnusedAsset };
        material.SetColor("_Color", color);
        Toon.Add(color, material);
        return material;
    }

    // Flat, unlit colour for effects: a copy of the checkpoint outline (Universal Render Pipeline/Unlit).
    private const string GlowBase = "CheckPointOutline";
    private static readonly Dictionary<Color32, Material> Glow = new();

    private static Material GetGlow(Color32 color, Material fallback)
    {
        if (Glow.TryGetValue(color, out var cached))
            return cached;
        if (!Vanilla.TryGetValue(GlowBase, out var source))
            return GetToon(color, fallback);
        var material = new Material(source) { name = $"CustomContent_Glow", hideFlags = HideFlags.DontUnloadUnusedAsset };
        material.SetColor("_BaseColor", color);
        material.SetColor("_Color", color);
        Glow.Add(color, material);
        return material;
    }

    internal static Color32 ParseHex(string hex)
    {
        hex = hex.TrimStart('#');
        if (hex.Length < 6 || !uint.TryParse(hex.Substring(0, 6), NumberStyles.HexNumber, CultureInfo.InvariantCulture, out uint rgb))
            return new Color32(255, 0, 255, 255);
        return new Color32((byte)(rgb >> 16), (byte)(rgb >> 8), (byte)rgb, 255);
    }
}
