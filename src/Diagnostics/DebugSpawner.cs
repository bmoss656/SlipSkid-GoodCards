using Game;
using Obstacles;
using Unity.Netcode;
using UnityEngine;
using UnityEngine.InputSystem;

namespace SlipSkid.CustomContent;

// Test keys, in a match:
// F6: (host) spawns the Test Arena high above the map if there isn't one; then puts your car(s) on it.
//     Clients can press it too once the host has made the arena.
// F7: (host) spawns every custom obstacle, already placed, in a grid ahead of the first player's car.
//     Goes through ObstacleDescription.Spawn, so clients see them exactly like drafted ones.
internal static class DebugSpawner
{
    // 7 x 16 m keeps all 30 inside the arena when you start from its F6 spot.
    private const int Columns = 7;
    private const float Spacing = 16f;

    internal static void Update()
    {
        var keyboard = Keyboard.current;
        if (keyboard == null)
            return;
        if (keyboard.f6Key.wasPressedThisFrame)
            GoToArena();
        if (keyboard.f7Key.wasPressedThisFrame)
            SpawnAll();
    }

    private static void GoToArena()
    {
        var nm = NetworkManager.Singleton;
        if (!nm || !nm.IsListening)
            return;
        var arena = FindArena();
        if (!arena)
        {
            if (!nm.IsServer)
            {
                Plugin.Log.LogInfo("DebugSpawner: no Test Arena yet; the host has to press F6 first");
                return;
            }
            var player = FirstPlayerWithCar(ownedOnly: false);
            var description = CardRegistry.DescriptionOf("TestArena");
            if (!player || !description)
                return;
            Vector3 position = player.playerNetworking.carController.sphereRigidbody.position + Vector3.up * TestArena.Height;
            arena = description.Spawn(player, position, Quaternion.identity, Vector3.one, inScene: true);
            Plugin.Log.LogInfo($"DebugSpawner: spawned the Test Arena at {position}");
        }

        // Teleport every car this machine owns (split-screen players included), side by side.
        int index = 0;
        foreach (var player in GameManager.Players)
        {
            if (!player || !player.IsOwner || !player.playerNetworking || !player.playerNetworking.carController)
                continue;
            Vector3 position = arena.transform.position + Vector3.up * 2f + Vector3.right * (index++ * 6f) - Vector3.forward * 40f;
            player.playerNetworking.carController.Teleport(position, Quaternion.identity, Vector3.forward, Vector3.zero, Vector3.zero);
        }
    }

    private static void SpawnAll()
    {
        if (!NetworkManager.Singleton || !NetworkManager.Singleton.IsServer)
        {
            Plugin.Log.LogInfo("DebugSpawner: F7 only works for the host");
            return;
        }
        var player = FirstPlayerWithCar(ownedOnly: false);
        if (!player)
        {
            Plugin.Log.LogInfo("DebugSpawner: no car to spawn in front of");
            return;
        }

        var car = player.playerNetworking.carController;
        Vector3 origin = car.sphereRigidbody.position;
        Vector3 forward = Vector3.ProjectOnPlane(car.car.forward, Vector3.up).normalized;
        if (forward.sqrMagnitude < 0.01f)
            forward = Vector3.forward;
        Vector3 right = Vector3.Cross(Vector3.up, forward);
        var rotation = Quaternion.LookRotation(forward, Vector3.up);

        int spawned = 0;
        for (int slot = 0; slot < CardRegistry.Entries.Length; slot++)
        {
            // Partners arrive with their parent card (the Toilet drops its own Sewer Exit); retired cards are skipped.
            var description = !CardRegistry.Entries[slot].IsDraftable ? null : CardRegistry.DescriptionOf(CardRegistry.Entries[slot].Id);
            if (!description)
                continue;
            int row = spawned / Columns, column = spawned % Columns;
            Vector3 position = origin + forward * (25f + row * Spacing) + right * ((column - (Columns - 1) / 2f) * Spacing);
            if (Physics.Raycast(position + Vector3.up * 30f, Vector3.down, out var hit, 200f))
                position = hit.point;
            description.Spawn(player, position, rotation, Vector3.one, inScene: true);
            spawned++;
        }
        Plugin.Log.LogInfo($"DebugSpawner: spawned {spawned} custom obstacles");
    }

    private static Obstacle FindArena()
    {
        foreach (var obstacle in ObstacleManager.AllObstacles)
        {
            var tag = obstacle ? obstacle.GetComponent<CustomObstacleTag>() : null;
            if (tag && CardRegistry.Get(tag.Slot) is TestArena)
                return obstacle;
        }
        return null;
    }

    private static Player.PlayerData FirstPlayerWithCar(bool ownedOnly) =>
        GameManager.Players?.Find(p => p && (!ownedOnly || p.IsOwner) && p.playerNetworking && p.playerNetworking.carController);
}
