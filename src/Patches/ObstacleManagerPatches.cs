using System;
using System.Linq;
using HarmonyLib;
using Obstacles;
using Obstacles.ObstacleAffixes;

namespace SlipSkid.CustomContent;

[HarmonyPatch(typeof(ObstacleManager), "Awake")]
internal static class ObstacleManagerAwakePatch
{
    // Runs on every machine. Awake destroys duplicate managers, so only act on the real one.
    private static void Postfix(ObstacleManager __instance)
    {
        if (ObstacleManager.instance != __instance)
            return;
        try
        {
            if (CardConfig.VerboseLog.Value)
                CatalogDump.Log(__instance);
            MaterialLibrary.Collect(__instance.allowedObstacleDescriptions);
            CardRegistry.Register(__instance);
        }
        catch (Exception e)
        {
            Plugin.Log.LogError($"CustomCards: registration failed: {e}");
        }
    }
}

[HarmonyPatch(typeof(ObstacleManager), nameof(ObstacleManager.GetRandomObstaclesDescriptions))]
internal static class ForceCardPatch
{
    // Host only: this roll feeds GenerateObstaclesToSelect, which writes the networked draft lists.
    private static void Postfix(bool modifierOnly,
        ((int, ObstacleDescription)[], (int, ObstacleAffixDescription)[]) __result)
    {
        string id = CardConfig.ForceCard.Value;
        if (string.IsNullOrWhiteSpace(id) || modifierOnly || __result.Item1.Length == 0)
            return;
        if (id.Trim() == "*")
        {
            FillWithCustomCards(__result, CardRegistry.Entries.Where(e => !e.IsPartnerOnly).Select(e => e.Id).ToArray());
            return;
        }
        if (id.Contains(","))
        {
            FillWithCustomCards(__result, id.Split(',').Select(s => s.Trim()).Where(s => s.Length > 0).ToArray());
            return;
        }

        var description = CardRegistry.DescriptionOf(id);
        int index = description ? ObstacleManager.GetIndexFromDescription(description) : -1;
        if (index < 0)
        {
            Plugin.Log.LogWarning($"Debug.ForceCard: '{id}' isn't a registered custom card");
            return;
        }

        int affix = Math.Max(0, CardConfig.ForceAffixIndex.Value);
        __result.Item1[0] = (index, description);
        __result.Item2[0] = (affix, ObstacleAffixManager.GetAffixByIndex(affix));
        Plugin.Log.LogInfo($"Debug.ForceCard: slot 0 is {id} (index {index}, affix {affix})");
    }

    // ForceCard = * (every custom card) or a comma-separated list of ids: every draft slot gets one of
    // them, continuing round to round until all have shown.
    private static int _next;

    private static void FillWithCustomCards(((int, ObstacleDescription)[], (int, ObstacleAffixDescription)[]) result, string[] ids)
    {
        int count = ids.Length;
        if (count == 0)
            return;
        for (int slot = 0; slot < result.Item1.Length; slot++)
        {
            for (int tries = 0; tries < count; tries++)
            {
                var description = CardRegistry.DescriptionOf(ids[_next++ % count]);
                int index = description ? ObstacleManager.GetIndexFromDescription(description) : -1;
                if (index < 0)
                    continue;
                result.Item1[slot] = (index, description);
                result.Item2[slot] = (0, ObstacleAffixManager.GetAffixByIndex(0));
                break;
            }
        }
        Plugin.Log.LogInfo($"Debug.ForceCard: filled {result.Item1.Length} slots with custom cards");
    }
}
