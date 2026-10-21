using System.Collections.Generic;
using System.Runtime.CompilerServices;
using Obstacles;
using UI;
using UnityEngine.Localization;

namespace SlipSkid.CustomContent;

// Our cards' text. Each clone has its own LocalizedString objects (copies of the carrier's), and the
// GetLocalizedString patch returns our string for exactly those objects. Anything that bypasses the
// patch still falls back to the carrier's text rather than an error.
internal static class CardText
{
    private static readonly Dictionary<LocalizedString, string> Texts = new(new ReferenceComparer());
    private static bool _loggedVanilla;
    private static bool _inLog;

    internal static void Register(LocalizedString key, string text)
    {
        if (key != null)
            Texts[key] = text;
    }

    internal static bool TryGet(LocalizedString key, out string text) => Texts.TryGetValue(key, out text);

    // Logs the game's text tags and a few raw vanilla descriptions, so new cards can reuse their styling.
    internal static void LogVanillaOnce()
    {
        if (_loggedVanilla || _inLog || !ObstacleManager.instance)
            return;
        _loggedVanilla = true;
        _inLog = true;
        try
        {
            foreach (var tag in CustomTmpTags.tagToOpenValue)
                Plugin.Log.LogInfo($"TextTag: <{tag.Key}> opens as <{tag.Value}>");
            foreach (var d in ObstacleManager.instance.allowedObstacleDescriptions)
            {
                if (d && d.description != null && !Texts.ContainsKey(d.description))
                    Plugin.Log.LogInfo($"CardText: {d.name} = \"{d.displayName?.GetLocalizedString()}\" / \"{d.description.GetLocalizedString()}\"");
            }
        }
        finally
        {
            _inLog = false;
        }
    }

    private sealed class ReferenceComparer : IEqualityComparer<LocalizedString>
    {
        public bool Equals(LocalizedString a, LocalizedString b) => ReferenceEquals(a, b);
        public int GetHashCode(LocalizedString s) => RuntimeHelpers.GetHashCode(s);
    }
}
