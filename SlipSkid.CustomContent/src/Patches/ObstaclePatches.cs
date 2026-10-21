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
        int slot = CardRegistry.SlotOf(__instance);
        if (slot < 0)
            return;
        affixIndex = SpawnMarker.Encode(slot, affixIndex);
    }
}

[HarmonyPatch(typeof(Obstacle), nameof(Obstacle.OnNetworkSpawn))]
internal static class VisualSwapPatch
{
    // Every machine. NetworkVariables are already synced here, and Obstacle.Init (called later in
    // OnNetworkSpawn) caches colliders and renderers, so swapping now makes the game use ours.
    private static void Prefix(Obstacle __instance)
    {
        if (!SpawnMarker.TryDecode(__instance.affixIndex.Value, out int slot, out _))
            return;
        if (__instance.GetComponent<CustomObstacleTag>())
            return;

        var entry = CardRegistry.Get(slot);
        if (entry == null)
        {
            Plugin.Log.LogWarning($"VisualSwap: unknown custom slot {slot}. Does everyone have the same mod version?");
            return;
        }

        try
        {
            var carrier = entry.KeepCarrier ? VisualSwap.ReadCarrier(__instance) : VisualSwap.StripCarrier(__instance);
            entry.Build(__instance, carrier);
            __instance.gameObject.AddComponent<CustomObstacleTag>().Slot = slot;
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
    private static bool Prefix(Obstacle __instance)
    {
        if (!SpawnMarker.TryDecode(__instance.affixIndex.Value, out _, out int affixIndex))
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
    }
}
