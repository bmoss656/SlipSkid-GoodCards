using System.Collections;
using System.Collections.Generic;
using CameraUtils;
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
            // The pipe's mouth is on the model's front (-forward, the side the card art shows).
            Vector3 forward = Vector3.ProjectOnPlane(-exit.transform.forward, Vector3.up).normalized;
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
// - Owner: placing the Toilet skips the vanilla "done" step (placedObstacle flag, the pointing hand and its
//   camera), because the hand takes over camera and controls and the exit could then never be placed.
// - Host: spawns the exit into that player's hands from the Toilet's OnPlace. Obstacle.OnNetworkSpawn binds
//   it to the owner like a freshly drafted obstacle, and the state machine re-enables placement controls.
// - Toilet and exit share a pair key packed into their spawn markers, so every machine pairs them the same way.
internal static class ToiletPairing
{
    private static readonly AccessTools.FieldRef<GameManager, bool> TimerHandled =
        AccessTools.FieldRefAccess<GameManager, bool>("_hasHandledObstaclePlacementTimer");

    // Seconds the owner waits for an exit before giving up and finishing their turn normally.
    private const float ExitWaitSeconds = 6f;

    // Owner side: players who placed a Toilet and are waiting for its exit to arrive, with when they started.
    private static readonly Dictionary<PlayerData, float> AwaitingExit = new();

    // Host side: next pair key, and the key the next partner spawn should carry.
    private static int _nextPair = new System.Random().Next(1, SpawnMarker.MaxPair);
    private static int _pendingPartnerPair;

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

    // Host, from the spawn-marker patch: a Toilet gets a fresh key, the exit spawned for it gets the same key.
    internal static int PairKeyForSpawn(CustomObstacle entry)
    {
        if (entry == null)
            return 0;
        if (!string.IsNullOrEmpty(entry.PartnerId))
        {
            int key = _nextPair;
            _nextPair = _nextPair % SpawnMarker.MaxPair + 1;
            return key;
        }
        if (entry.IsPartnerOnly)
        {
            int key = _pendingPartnerPair;
            _pendingPartnerPair = 0;
            return key;
        }
        return 0;
    }

    // Still time to place another obstacle this phase? With no placement timer the game marks the timer
    // "handled" straight away, so that flag only means "ran out" when a timer is set.
    private static bool CanHandOver()
    {
        var gm = GameManager.instance;
        if (!gm || !gm.networkVariables || gm.networkVariables.state.Value != GameManager.GameState.PlacingObstacles)
            return false;
        return gm.networkVariables.currentGameRules.Value.obstaclePlacementTimerSec == 0 || !TimerHandled(gm);
    }

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
        // The exit's mouth is its -forward: face it onward, the way cars were driving into the bowl.
        var exitRotation = Quaternion.LookRotation(-forward);
        _pendingPartnerPair = PairOf(toilet);
        try
        {
            if (!inScene && CanHandOver())
            {
                // Into the player's hands, like a freshly drafted obstacle (they move and place it).
                exitDescription.Spawn(player, toilet.transform.position + Vector3.up * 3f + forward * 10f, exitRotation);
                Plugin.Log.LogInfo($"Toilet: handed {player.DisplayNameRaw} a Sewer Exit to place");
            }
            else
            {
                // No time left (timer, F7, scripted spawns): drop the exit already placed a little way ahead.
                Vector3 position = toilet.transform.position + forward * 18f;
                if (Physics.Raycast(position + Vector3.up * 50f, Vector3.down, out var hit, 200f, ~0, QueryTriggerInteraction.Ignore))
                    position = hit.point;
                exitDescription.Spawn(player, position, exitRotation, Vector3.one, inScene: true);
                Plugin.Log.LogInfo($"Toilet: dropped a placed Sewer Exit for {player.DisplayNameRaw}");
            }
        }
        finally
        {
            _pendingPartnerPair = 0;
        }
    }

    // Owner side, in place of PlayerData.PlaceObstacle for a Toilet: release it without ending the turn.
    // Returns false when vanilla should run instead.
    internal static bool TryKeepPlacing(PlayerData player, Obstacle obstacle, bool inScene)
    {
        if (inScene || !player.IsOwner || !IsToilet(obstacle, out _) || !CanHandOver())
            return false;
        player.currentRoundSaveData.placedObstacle = obstacle.description;
        player.lastObstaclePosition.Value = obstacle.transform.position;
        player.isLastObstaclePositionSet.Value = true;
        player.UnBindFromObstacle();
        // UnBind switches to the driving controls; stay in placement controls until the exit is bound.
        if (player.inputs)
            player.inputs.SwitchCurrentActionMap("ObstaclePlacement");
        AwaitingExit[player] = Time.time;
        Plugin.Log.LogInfo($"Toilet: {player.DisplayNameRaw} placed a Toilet, waiting for its Sewer Exit");
        return true;
    }

    // Owner side, when an exit spawns for a player who is waiting for one.
    internal static void OnExitSpawned(Obstacle exit)
    {
        var player = exit.playerInfos;
        if (!IsExit(exit) || !player)
            return;
        // Other machines showed this player's pointing hand when the Toilet landed; they're still placing.
        if (!player.IsOwner && exit.state != Obstacle.ObstacleState.Placed && player.playerObstacleHandNetworking
            && player.playerObstacleHandNetworking.IsHandVisible)
            player.playerObstacleHandNetworking.Hide();
        if (!player.IsOwner || !AwaitingExit.Remove(player))
            return;
        if (exit.state == Obstacle.ObstacleState.Placed)
        {
            // The host ran out of time and dropped it already placed: this player is done.
            player.placedObstacle.Value = true;
        }
        else if (!CanHandOver())
        {
            // Our timer ran out while it was on its way: place it where it is.
            exit.ForcePlaceObstacle();
        }
        else if (player.currentObstacle == exit)
        {
            // The game only aims the placement camera when placement view first turns on, so it would stay on
            // the Toilet. This re-aims every local player's camera at their current obstacle (now the exit).
            CameraManager.EnableObstaclePlacementView();
            Plugin.Log.LogInfo($"Toilet: camera moved to {player.DisplayNameRaw}'s Sewer Exit");
        }
    }

    // Owner side, every frame: never leave a player stuck if the exit doesn't arrive.
    internal static void Update()
    {
        if (AwaitingExit.Count == 0)
            return;
        List<PlayerData> late = null;
        foreach (var waiting in AwaitingExit)
        {
            if (!waiting.Key || Time.time - waiting.Value > ExitWaitSeconds || !CanHandOver())
                (late ??= new List<PlayerData>()).Add(waiting.Key);
        }
        if (late == null)
            return;
        foreach (var player in late)
        {
            AwaitingExit.Remove(player);
            if (!player || !player.IsOwner || player.currentObstacle)
                continue;
            Plugin.Log.LogWarning($"Toilet: no Sewer Exit arrived for {player.DisplayNameRaw}; ending their turn");
            player.placedObstacle.Value = true;
        }
    }

    private static int PairOf(Obstacle obstacle)
    {
        var tag = obstacle ? obstacle.GetComponent<CustomObstacleTag>() : null;
        return tag ? tag.Pair : 0;
    }

    // Same answer on every machine: the exit carrying this toilet's pair key.
    internal static Obstacle FindExit(Obstacle toilet)
    {
        int pair = PairOf(toilet);
        if (pair == 0)
            return null;
        foreach (var obstacle in ObstacleManager.AllObstacles)
        {
            if (obstacle && IsExit(obstacle) && PairOf(obstacle) == pair)
                return obstacle;
        }
        return null;
    }
}

// Postfix: playerInfos and the synced state are only filled in during OnNetworkSpawn.
[HarmonyPatch(typeof(Obstacle), nameof(Obstacle.OnNetworkSpawn))]
internal static class ExitSpawnedPatch
{
    private static void Postfix(Obstacle __instance) => Guard.Run("Toilet", () => ToiletPairing.OnExitSpawned(__instance));
}

[HarmonyPatch(typeof(Obstacle), nameof(Obstacle.OnPlace))]
internal static class ToiletPlacedPatch
{
    private static void Postfix(Obstacle __instance, bool inScene) => Guard.Run("Toilet", () => ToiletPairing.OnPlaced(__instance, inScene));
}

[HarmonyPatch(typeof(PlayerData), nameof(PlayerData.PlaceObstacle))]
internal static class ToiletPlayerPlacedPatch
{
    private static bool Prefix(PlayerData __instance, Obstacle obstacle, bool inScene) =>
        Guard.Prefix("Toilet", () => !ToiletPairing.TryKeepPlacing(__instance, obstacle, inScene));
}
