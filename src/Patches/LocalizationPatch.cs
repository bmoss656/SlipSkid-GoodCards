using System;
using HarmonyLib;
using UnityEngine.Localization;

namespace SlipSkid.CustomContent;

// Every card label (draft, collection, rules menu, stats) reads LocalizedString.GetLocalizedString(),
// mostly through UI.TextProcessor.Process, so answering here covers them all.
[HarmonyPatch(typeof(LocalizedString), nameof(LocalizedString.GetLocalizedString), new Type[0])]
internal static class LocalizationPatch
{
    // Only answers for our own cards' LocalizedString objects (matched by reference); everything else,
    // including other mods' cards, goes through untouched.
    private static bool Prefix(LocalizedString __instance, ref string __result)
    {
        try
        {
            if (!CardText.TryGet(__instance, out string text))
                return true;
            if (CardConfig.VerboseLog.Value)
                CardText.LogVanillaOnce();
            __result = text;
            return false;
        }
        catch (Exception e)
        {
            Guard.Report("CardText", e);
            return true;
        }
    }
}
