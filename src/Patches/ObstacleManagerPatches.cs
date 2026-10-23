using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using Obstacles;
using Obstacles.ObstacleAffixes;

namespace SlipSkid.CustomContent;

[HarmonyPatch(typeof(ObstacleManager), "Awake")]
internal static class ObstacleManagerAwakePatch
{
    // Runs on every machine. Awake destroys duplicate managers, so only act on the real one.
    // First among the Awake postfixes: another mod's postfix throwing can't then skip ours. Where our cards
    // land relative to other mods' doesn't matter, because CatalogSync copies the host's order.
    [HarmonyPriority(Priority.First)]
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

// Host only. With dozens of extra cards in the catalog, plain rarity weights made nearly every draft card one
// of ours. Each draft slot first decides "Good Cards or not" with Draft.CustomCardChance, then the vanilla
// weighted roll runs on just that half of the catalog (so maxQuantity, contexts and history still apply).
[HarmonyPatch(typeof(ObstacleManager), nameof(ObstacleManager.GetRandomObstaclesDescriptions))]
internal static class DraftRollScope
{
    internal static bool Active;

    private static void Prefix() => Active = true;
    private static Exception Finalizer(Exception __exception)
    {
        Active = false;
        return __exception;
    }
}

[HarmonyPatch(typeof(ObstacleDescription), nameof(ObstacleDescription.GetRandomWeightedObstacleDescription))]
internal static class DraftOddsPatch
{
    private static void Prefix(ref ObstacleDescription[] descriptions, Dictionary<ObstacleDescription, int> selectionHistory,
        (int, ObstacleDescription)[] currentList, int currentCount)
    {
        try
        {
            descriptions = Narrow(descriptions, selectionHistory, currentList, currentCount);
        }
        catch (Exception e)
        {
            Guard.Report("DraftOdds", e);   // the roll goes ahead on whatever list it was given
        }
    }

    private static ObstacleDescription[] Narrow(ObstacleDescription[] descriptions, Dictionary<ObstacleDescription, int> selectionHistory,
        (int, ObstacleDescription)[] currentList, int currentCount)
    {
        if (!DraftRollScope.Active || descriptions == null || descriptions.Length == 0)
            return descriptions;
        // Cards some connected player doesn't have (see CatalogSync) are never offered.
        if (descriptions.Any(CatalogSync.IsExcluded))
        {
            var allowed = descriptions.Where(d => !CatalogSync.IsExcluded(d)).ToArray();
            if (allowed.Any(d => Weight(d, selectionHistory, currentList, currentCount) > 0))
                descriptions = allowed;
        }
        bool wantCustom = UnityEngine.Random.value < CardConfig.CustomCardChance.Value;
        var subset = descriptions.Where(d => d && CardRegistry.SlotOf(d) >= 0 == wantCustom).ToArray();
        // Nothing rollable on that side (e.g. a modifier-only draft has none of ours): leave the roll alone.
        if (subset.Length == 0 || !subset.Any(d => Weight(d, selectionHistory, currentList, currentCount) > 0))
            return descriptions;
        return subset;
    }

    // Same rules as the weight lambda in ObstacleDescription.GetRandomWeightedObstacleDescription.
    private static int Weight(ObstacleDescription d, Dictionary<ObstacleDescription, int> history,
        (int, ObstacleDescription)[] currentList, int currentCount)
    {
        if (!d.IsContextValid(currentList))
            return 0;
        if (d.maxQuantity < 0)
            return d.RarityWeight;
        if (d.maxQuantity == 0)
            return 0;
        int count = 0;
        if (currentList != null)
        {
            for (int i = 0; i < currentCount && i < currentList.Length; i++)
            {
                if (currentList[i].Item2 == d)
                    count++;
            }
        }
        if (history != null && history.TryGetValue(d, out int seen))
            count += seen;
        return count < d.maxQuantity ? d.RarityWeight : 0;
    }
}

[HarmonyPatch(typeof(ObstacleManager), nameof(ObstacleManager.GetRandomObstaclesDescriptions))]
internal static class ForceCardPatch
{
    // Host only: this roll feeds GenerateObstaclesToSelect, which writes the networked draft lists.
    private static void Postfix(bool modifierOnly,
        ((int, ObstacleDescription)[], (int, ObstacleAffixDescription)[]) __result) =>
        Guard.Run("Debug.ForceCard", () => Force(modifierOnly, __result));

    private static void Force(bool modifierOnly, ((int, ObstacleDescription)[], (int, ObstacleAffixDescription)[]) __result)
    {
        string id = CardConfig.ForceCard.Value;
        if (string.IsNullOrWhiteSpace(id) || modifierOnly || __result.Item1.Length == 0)
            return;
        if (id.Trim() == "*")
        {
            FillWithCustomCards(__result, CardRegistry.Entries.Where(e => e.IsDraftable).Select(e => e.Id).ToArray());
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
