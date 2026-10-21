using System.Collections;
using System.Collections.Generic;
using Game;
using Game.Levels;
using HarmonyLib;
using Obstacles;
using Player;
using UnityEngine;

namespace SlipSkid.CustomContent;

// Drive into the bowl, get flushed out of this toilet's Sewer Exit. Runs on the car owner's machine;
// the teleport reaches everyone through the car's ClientNetworkTransform.
internal sealed class ToiletZone : MonoBehaviour
{
    public float delay = 0.35f;
    public float exitSpeed = 25f;
    public int channel = -1;   // TriggerBus channel played on flush (the water swirl)

    private Obstacle _obstacle;
    private readonly HashSet<SphereCarController> _flushing = new();

    private void Start() => _obstacle = GetComponentInParent<Obstacle>();

    private void OnTriggerEnter(Collider other)
    {
        if (!_obstacle || !CarLookup.IsPlaced(_obstacle) || !CarLookup.TryGetOwnedCar(other, out _, out var car))
            return;
        if (_flushing.Add(car))
            StartCoroutine(Flush(car));
    }

    private IEnumerator Flush(SphereCarController car)
    {
        if (channel >= 0)
            TriggerBus.Fire(_obstacle, channel);
        yield return new WaitForSeconds(delay);
        _flushing.Remove(car);
        if (!car || !car.player)
            yield break;

        var exit = ToiletPairing.FindExit(_obstacle);
        if (exit)
        {
            Vector3 forward = Vector3.ProjectOnPlane(exit.transform.forward, Vector3.up).normalized;
            if (forward.sqrMagnitude < 0.01f)
                forward = Vector3.forward;
            Vector3 position = exit.transform.position + Vector3.up * 2.5f + forward * 3.5f;
            car.Teleport(position, Quaternion.LookRotation(forward), forward, forward * exitSpeed, Vector3.zero);
            Plugin.Log.LogInfo($"Toilet: flushed {car.player.DisplayNameRaw} to {exit.name}");
        }
        else
        {
            FlushToCheckpoint(car);
        }
    }

    // No exit (it was deleted): back to the last checkpoint this player passed, or the start.
    private static void FlushToCheckpoint(SphereCarController car)
    {
        var player = car.player;
        var level = LevelManager.instance ? LevelManager.instance.levelDefinition : null;
        int best = -1;
        ulong bestTime = 0;
        if (level && player.passedCheckPoints != null)
        {
            for (int i = 0; i < player.passedCheckPoints.Count && i < level.checkpoints.Count; i++)
            {
                if (player.passedCheckPoints[i] > bestTime)
                {
                    bestTime = player.passedCheckPoints[i];
                    best = i;
                }
            }
        }
        if (best >= 0 && level.checkpoints[best])
        {
            var gate = level.checkpoints[best].transform;
            car.Teleport(gate.position + Vector3.up * 2f, gate.rotation, gate.forward, Vector3.zero, Vector3.zero);
        }
        else if (GameManager.instance)
        {
            GameManager.instance.PlacePlayerAtSpawn(player);
        }
    }
}

// Placing a Toilet hands its owner a Sewer Exit to place next, in the same placement phase.
internal static class ToiletPairing
{
    private static readonly AccessTools.FieldRef<GameManager, bool> TimerHandled =
        AccessTools.FieldRefAccess<GameManager, bool>("_hasHandledObstaclePlacementTimer");

    // Owner side: players whose flag we cleared and who are waiting for their exit to arrive.
    private static readonly HashSet<PlayerData> AwaitingExit = new();

    internal static bool IsToilet(Obstacle obstacle, out CustomObstacle entry)
    {
        entry = null;
        var tag = obstacle ? obstacle.GetComponent<CustomObstacleTag>() : null;
        if (!tag)
            return false;
        entry = CardRegistry.Get(tag.Slot);
        return entry != null && !string.IsNullOrEmpty(entry.PartnerId);
    }

    internal static bool IsExit(Obstacle obstacle)
    {
        var tag = obstacle ? obstacle.GetComponent<CustomObstacleTag>() : null;
        return tag && CardRegistry.Get(tag.Slot) is { IsPartnerOnly: true };
    }

    // Placing mid-phase (before the timer ran out) means the player still has time to place the exit.
    private static bool CanHandOver() =>
        GameManager.instance && GameManager.instance.networkVariables.state.Value == GameManager.GameState.PlacingObstacles
        && !TimerHandled(GameManager.instance);

    // Every machine, when any obstacle lands. Only the host spawns.
    internal static void OnPlaced(Obstacle toilet, bool inScene)
    {
        if (!toilet.IsServer || !IsToilet(toilet, out var entry) || FindExit(toilet))
            return;
        var exitDescription = CardRegistry.DescriptionOf(entry.PartnerId);
        var player = toilet.playerInfos;
        if (!exitDescription || !player)
            return;

        var forward = Vector3.ProjectOnPlane(toilet.transform.forward, Vector3.up).normalized;
        if (forward.sqrMagnitude < 0.01f)
            forward = Vector3.forward;
        if (!inScene && CanHandOver())
        {
            // Into the player's hands, like a freshly drafted obstacle (they move and place it).
            exitDescription.Spawn(player, toilet.transform.position + Vector3.up * 3f + forward * 8f, Quaternion.identity);
            Plugin.Log.LogInfo($"Toilet: handed {player.DisplayNameRaw} a Sewer Exit to place");
        }
        else
        {
            // No time left (timer, F7, scripted spawns): drop the exit already placed a little way ahead.
            Vector3 position = toilet.transform.position + forward * 18f;
            if (Physics.Raycast(position + Vector3.up * 50f, Vector3.down, out var hit, 200f))
                position = hit.point;
            exitDescription.Spawn(player, position, Quaternion.LookRotation(forward), Vector3.one, inScene: true);
            Plugin.Log.LogInfo($"Toilet: dropped a placed Sewer Exit for {player.DisplayNameRaw}");
        }
    }

    // Owner side, right after PlayerData.PlaceObstacle marked the player as done: keep them placing.
    internal static void OnPlayerPlaced(PlayerData player, Obstacle obstacle, bool inScene)
    {
        if (inScene || !player.IsOwner || !IsToilet(obstacle, out _) || !CanHandOver())
            return;
        player.placedObstacle.Value = false;
        AwaitingExit.Add(player);
    }

    // Owner side, when an exit spawns. If it arrived already placed (the host ran out of time), the player is done.
    internal static void OnExitSpawned(Obstacle exit)
    {
        var player = exit.playerInfos;
        if (!IsExit(exit) || !player || !player.IsOwner || !AwaitingExit.Remove(player))
            return;
        if (exit.state == Obstacle.ObstacleState.Placed)
            player.placedObstacle.Value = true;
    }

    // Same answer on every machine: the exit spawned for the same player straight after this toilet.
    internal static Obstacle FindExit(Obstacle toilet)
    {
        if (!toilet || !toilet.NetworkObject)
            return null;
        ulong toiletId = toilet.NetworkObject.NetworkObjectId;
        Obstacle best = null;
        ulong bestId = ulong.MaxValue;
        foreach (var obstacle in ObstacleManager.AllObstacles)
        {
            if (!obstacle || !obstacle.NetworkObject || !IsExit(obstacle))
                continue;
            ulong id = obstacle.NetworkObject.NetworkObjectId;
            if (id > toiletId && id < bestId && obstacle.playerInfosIndex.Value == toilet.playerInfosIndex.Value)
            {
                best = obstacle;
                bestId = id;
            }
        }
        return best;
    }
}

// Postfix: playerInfos and the synced state are only filled in during OnNetworkSpawn.
[HarmonyPatch(typeof(Obstacle), nameof(Obstacle.OnNetworkSpawn))]
internal static class ExitSpawnedPatch
{
    private static void Postfix(Obstacle __instance) => ToiletPairing.OnExitSpawned(__instance);
}

[HarmonyPatch(typeof(Obstacle), nameof(Obstacle.OnPlace))]
internal static class ToiletPlacedPatch
{
    private static void Postfix(Obstacle __instance, bool inScene) => ToiletPairing.OnPlaced(__instance, inScene);
}

[HarmonyPatch(typeof(PlayerData), nameof(PlayerData.PlaceObstacle))]
internal static class ToiletPlayerPlacedPatch
{
    private static void Postfix(PlayerData __instance, Obstacle obstacle, bool inScene) =>
        ToiletPairing.OnPlayerPlaced(__instance, obstacle, inScene);
}
