using System.Collections.Generic;
using Obstacles;
using Unity.Collections;
using Unity.Netcode;
using UnityEngine;

namespace SlipSkid.CustomContent;

// Plays an obstacle's TriggeredMotion on every machine. The car's owner detects the touch, plays it at
// once, and sends a named message (no NGO code generation needed); the host relays it to the others.
internal static class TriggerBus
{
    private const string MessageName = "SlipSkid.CustomContent.Trigger";
    private const string PosesMessageName = "SlipSkid.CustomContent.Poses";
    private static CustomMessagingManager _registeredWith;

    // Called every frame: (re)registers the handlers whenever a new network session starts.
    internal static void Update()
    {
        var nm = NetworkManager.Singleton;
        var messaging = nm && nm.IsListening ? nm.CustomMessagingManager : null;
        if (messaging == null || messaging == _registeredWith)
            return;
        messaging.RegisterNamedMessageHandler(MessageName, Guard.Handler("TriggerBus", OnMessage));
        messaging.RegisterNamedMessageHandler(PosesMessageName, Guard.Handler("TriggerBus", OnPosesMessage));
        _registeredWith = messaging;
    }

    // Host only: where a Crumble's pieces landed, so every client locks the same layout.
    internal static void SendPoses(Crumble crumble, List<(Vector3, Quaternion)> poses)
    {
        var nm = NetworkManager.Singleton;
        var obstacle = crumble.Obstacle;
        if (!nm || !nm.IsListening || !nm.IsServer || !obstacle || !obstacle.NetworkObject)
            return;
        var targets = OthersExcept(nm, nm.LocalClientId);
        if (targets.Count == 0)
            return;
        int index = System.Array.IndexOf(obstacle.GetComponentsInChildren<Crumble>(true), crumble);
        var writer = new FastBufferWriter(32 + poses.Count * 28, Allocator.Temp);
        try
        {
            writer.WriteValueSafe(obstacle.NetworkObject.NetworkObjectId);
            writer.WriteValueSafe(index);
            writer.WriteValueSafe(poses.Count);
            foreach (var (position, rotation) in poses)
            {
                writer.WriteValueSafe(position.x); writer.WriteValueSafe(position.y); writer.WriteValueSafe(position.z);
                writer.WriteValueSafe(rotation.x); writer.WriteValueSafe(rotation.y); writer.WriteValueSafe(rotation.z);
                writer.WriteValueSafe(rotation.w);
            }
            nm.CustomMessagingManager.SendNamedMessage(PosesMessageName, targets, writer, NetworkDelivery.ReliableFragmentedSequenced);
        }
        finally
        {
            writer.Dispose();
        }
    }

    private static void OnPosesMessage(ulong sender, FastBufferReader reader)
    {
        reader.ReadValueSafe(out ulong id);
        reader.ReadValueSafe(out int index);
        reader.ReadValueSafe(out int count);
        var poses = new List<(Vector3, Quaternion)>(count);
        for (int i = 0; i < count; i++)
        {
            reader.ReadValueSafe(out float px); reader.ReadValueSafe(out float py); reader.ReadValueSafe(out float pz);
            reader.ReadValueSafe(out float rx); reader.ReadValueSafe(out float ry); reader.ReadValueSafe(out float rz);
            reader.ReadValueSafe(out float rw);
            poses.Add((new Vector3(px, py, pz), new Quaternion(rx, ry, rz, rw)));
        }
        if (!NetworkManager.Singleton.SpawnManager.SpawnedObjects.TryGetValue(id, out var networkObject))
            return;
        var crumbles = networkObject.GetComponentsInChildren<Crumble>(true);
        if (index >= 0 && index < crumbles.Length)
            crumbles[index].ApplyPoses(poses);
    }

    // `direction` (world space) is passed to Crumble so every machine knocks things over the same way.
    internal static void Fire(Obstacle obstacle, int channel, Vector3 direction = default)
    {
        Play(obstacle, channel, direction);
        var nm = NetworkManager.Singleton;
        if (!nm || !nm.IsListening || !obstacle.NetworkObject)
            return;
        ulong id = obstacle.NetworkObject.NetworkObjectId;
        if (nm.IsServer)
            Send(id, channel, direction, OthersExcept(nm, nm.LocalClientId));
        else
            Send(id, channel, direction, new List<ulong> { NetworkManager.ServerClientId });
    }

    private static void OnMessage(ulong sender, FastBufferReader reader)
    {
        reader.ReadValueSafe(out ulong id);
        reader.ReadValueSafe(out int channel);
        reader.ReadValueSafe(out float x);
        reader.ReadValueSafe(out float y);
        reader.ReadValueSafe(out float z);
        var direction = new Vector3(x, y, z);
        var nm = NetworkManager.Singleton;
        if (!nm.SpawnManager.SpawnedObjects.TryGetValue(id, out var networkObject))
            return;
        var obstacle = networkObject.GetComponent<Obstacle>();
        if (!obstacle)
            return;
        Play(obstacle, channel, direction);
        if (nm.IsServer)
            Send(id, channel, direction, OthersExcept(nm, sender));
    }

    private static void Play(Obstacle obstacle, int channel, Vector3 direction)
    {
        foreach (var motion in obstacle.GetComponentsInChildren<TriggeredMotion>(true))
        {
            if (motion.channel == channel)
                motion.Trigger();
        }
        foreach (var crumble in obstacle.GetComponentsInChildren<Crumble>(true))
        {
            if (crumble.channel == channel)
                crumble.Knock(direction);
        }
        foreach (var effect in obstacle.GetComponentsInChildren<BurstEffect>(true))
        {
            if (effect.channel == channel)
                effect.Play(direction);
        }
    }

    private static List<ulong> OthersExcept(NetworkManager nm, ulong skip)
    {
        var targets = new List<ulong>();
        foreach (ulong client in nm.ConnectedClientsIds)
        {
            if (client != skip && client != nm.LocalClientId)
                targets.Add(client);
        }
        return targets;
    }

    private static void Send(ulong id, int channel, Vector3 direction, List<ulong> targets)
    {
        if (targets.Count == 0)
            return;
        var writer = new FastBufferWriter(32, Allocator.Temp);
        try
        {
            writer.WriteValueSafe(id);
            writer.WriteValueSafe(channel);
            writer.WriteValueSafe(direction.x);
            writer.WriteValueSafe(direction.y);
            writer.WriteValueSafe(direction.z);
            NetworkManager.Singleton.CustomMessagingManager.SendNamedMessage(MessageName, targets, writer, NetworkDelivery.Reliable);
        }
        finally
        {
            writer.Dispose();
        }
    }
}

// Trigger that fires a TriggerBus channel when the owner's car touches it (a pressure plate).
internal sealed class TriggerPlate : MonoBehaviour
{
    public int channel;
    public float cooldown = 2f;

    private Obstacle _obstacle;
    private float _last = -100f;

    private void Start() => _obstacle = GetComponentInParent<Obstacle>();

    private void OnTriggerEnter(Collider other)
    {
        if (!_obstacle || !CarLookup.IsPlaced(_obstacle) || Time.time - _last < cooldown)
            return;
        if (!CarLookup.TryGetOwnedCar(other, out _, out _))
            return;
        _last = Time.time;
        TriggerBus.Fire(_obstacle, channel);
    }
}
