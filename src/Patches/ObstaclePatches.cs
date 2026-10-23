using System;
using HarmonyLib;
using Obstacles;
using Obstacles.ObstacleAffixes;
using Player;
using UnityEngine;

namespace SlipSkid.CustomContent;

[HarmonyPatch(typeof(ObstacleDescription), nameof(ObstacleDescription.Spawn),
    new[] { typeof(PlayerData), typeof(Vector3), typeof(Quaternion), typeof(Vector3), typeof(bool), typeof(int) })]
internal static class SpawnMarkerPatch
{
    // Host only (spawning is server-side). The affixIndex NetworkVariable is set before
    // SpawnWithOwnership, so the marker reaches clients in the spawn payload.
    private static void Prefix(ObstacleDescription __instance, ref int affixIndex)
    {
        try
        {
            int slot = CardRegistry.SlotOf(__instance);
            if (slot < 0)
                return;
            // A scatter passes its own (marked) affixIndex on to its pieces: keep only the real affix.
            if (SpawnMarker.TryDecode(affixIndex, out _, out int carriedAffix))
                affixIndex = carriedAffix;
            affixIndex = SpawnMarker.Encode(slot, affixIndex, ToiletPairing.PairKeyForSpawn(CardRegistry.Get(slot)));
        }
        catch (Exception e)
        {
            Guard.Report("SpawnMarker", e);
        }
    }
}

[HarmonyPatch(typeof(Obstacle), nameof(Obstacle.OnNetworkSpawn))]
internal static class VisualSwapPatch
{
    // Every machine. NetworkVariables are already synced here, and Obstacle.Init (called later in
    // OnNetworkSpawn) caches colliders and renderers, so swapping now makes the game use ours.
    private static void Prefix(Obstacle __instance)
    {
        int slot, pair;
        try
        {
            if (!CardRegistry.TryReadMarker(__instance, out slot, out _, out pair) || __instance.GetComponent<CustomObstacleTag>())
                return;
        }
        catch (Exception e)
        {
            Guard.Report("VisualSwap", e);
            return;
        }
        var entry = CardRegistry.Get(slot);

        try
        {
            var carrier = entry.KeepCarrier ? VisualSwap.ReadCarrier(__instance) : VisualSwap.StripCarrier(__instance);
            entry.Build(__instance, carrier);
            var tag = __instance.gameObject.AddComponent<CustomObstacleTag>();
            tag.Slot = slot;
            tag.Pair = pair;
            Plugin.Log.LogInfo($"VisualSwap: {entry.Id} built on {__instance.name}");
        }
        catch (Exception e)
        {
            Plugin.Log.LogError($"VisualSwap: {entry.Id} failed: {e}");
        }
    }
}

[HarmonyPatch(typeof(Obstacle), "ApplyAffix")]
internal static class AffixPatch
{
    // Every machine. The vanilla method ignores our negative marker, so apply the packed affix ourselves.
    private static bool Prefix(Obstacle __instance) => Guard.Prefix("Affix", () =>
    {
        if (!CardRegistry.TryReadMarker(__instance, out _, out int affixIndex, out _))
            return true;
        if (affixIndex > 0)
        {
            var affix = ObstacleAffixManager.GetAffixByIndex(affixIndex);
            if (affix && affix.IsValid && affix.callbacks)
            {
                affix.callbacks.Apply(__instance);
                Plugin.Log.LogInfo($"Affix: applied {affix.name} to {__instance.name}");
            }
        }
        return false;
    });
}
