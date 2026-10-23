using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using Obstacles;
using Unity.Collections;
using Unity.Netcode;
using UnityEngine;
using World;
using Object = UnityEngine.Object;

namespace SlipSkid.CustomContent;

// Keeps every machine's card and surface lists in the HOST's order, whatever other mods are installed.
// The game syncs draft cards by index into ObstacleManager.allowedObstacleDescriptions and surface swaps by
// index into SurfaceManager.surfaces. Card mods (us, EvenMoreCards, MoreCards...) all append to those lists,
// so the indices only line up when every player has the same mods, versions and settings, loaded in the same
// order. Instead of hoping for that:
// - The host sends its lists (by id and name) to each client when it connects and whenever its lists are
//   rebuilt (a new scene).
// - The client reorders its own lists to match. A card the host has but the client doesn't gets a placeholder
//   in its slot, so later indices still line up; cards only the client has go to the end, where the host never
//   rolls them.
// - The client tells the host which cards it's missing, and the host stops drafting those. A client that never
//   answers doesn't have Good Cards at all, so the host stops drafting Good Cards cards.
internal static class CatalogSync
{
    private const string CatalogMessage = "SlipSkid.GoodCards.Catalog";
    private const string RequestMessage = "SlipSkid.GoodCards.CatalogRequest";
    private const string ReplyMessage = "SlipSkid.GoodCards.CatalogReply";
    private const float AnswerTimeout = 15f;

    private sealed class ClientState
    {
        public float SentAt;
        public bool Answered;
        public bool WarnedNoMod;
        public HashSet<string> Missing = new();
    }

    private static CustomMessagingManager _registeredWith;

    // Host side.
    private static readonly Dictionary<ulong, ClientState> Clients = new();
    private static HashSet<string> _excluded = new();
    private static bool _excludeOurCards;

    // Client side.
    private static List<string> _hostCards;
    private static List<string> _hostSurfaces;
    private static float _connectedAt = -1f;
    private static bool _requested;
    private static readonly Dictionary<string, ObstacleDescription> Placeholders = new();

    internal static string Key(ObstacleDescription d) => d ? $"{d.id}/{d.name}" : "null";
    private static string Key(Surface s) => s ? s.name : "null";

    // Host only, during the draft roll: true for cards some connected player can't show or spawn.
    internal static bool IsExcluded(ObstacleDescription d) =>
        d && ((_excludeOurCards && CardRegistry.SlotOf(d) >= 0) || (_excluded.Count > 0 && _excluded.Contains(Key(d))));

    internal static void Update()
    {
        var nm = NetworkManager.Singleton;
        var messaging = nm && nm.IsListening ? nm.CustomMessagingManager : null;
        if (messaging == null)
        {
            if (_registeredWith != null)
                ResetSession();
            return;
        }
        if (messaging != _registeredWith)
        {
            ResetSession();
            messaging.RegisterNamedMessageHandler(CatalogMessage, Guard.Handler("CatalogSync", OnCatalog));
            messaging.RegisterNamedMessageHandler(RequestMessage, Guard.Handler("CatalogSync", OnRequest));
            messaging.RegisterNamedMessageHandler(ReplyMessage, Guard.Handler("CatalogSync", OnReply));
            _registeredWith = messaging;
        }

        if (nm.IsServer)
            UpdateHost(nm);
        else
            UpdateClient(nm);
    }

    private static void ResetSession()
    {
        _registeredWith = null;
        Clients.Clear();
        _excluded = new HashSet<string>();
        _excludeOurCards = false;
        _hostCards = null;
        _hostSurfaces = null;
        _connectedAt = -1f;
        _requested = false;
    }

    // ---------------------------------------------------------------- host

    private static void UpdateHost(NetworkManager nm)
    {
        foreach (ulong client in nm.ConnectedClientsIds)
        {
            if (client == nm.LocalClientId || Clients.ContainsKey(client))
                continue;
            Clients[client] = new ClientState();
            SendCatalog(client);
        }
        bool changed = false;
        foreach (ulong gone in Clients.Keys.Where(id => !nm.ConnectedClientsIds.Contains(id)).ToList())
        {
            Clients.Remove(gone);
            changed = true;
        }
        foreach (var pair in Clients)
        {
            var state = pair.Value;
            if (state.Answered || state.WarnedNoMod || Time.unscaledTime - state.SentAt < AnswerTimeout)
                continue;
            state.WarnedNoMod = true;
            changed = true;
            Plugin.Log.LogWarning($"CatalogSync: player {pair.Key} never answered, so they don't have Good Cards " +
                                  $"{Plugin.Version}. Good Cards cards won't be drafted while they're here.");
        }
        if (changed)
            RebuildExclusions();
    }

    private static void RebuildExclusions()
    {
        _excluded = new HashSet<string>(Clients.Values.SelectMany(c => c.Missing));
        _excludeOurCards = Clients.Values.Any(c => c.WarnedNoMod && !c.Answered);
    }

    // Host, after its ObstacleManager or SurfaceManager is (re)built: everyone gets the new lists.
    internal static void OnHostListsChanged()
    {
        var nm = NetworkManager.Singleton;
        if (!nm || !nm.IsListening || !nm.IsServer)
            return;
        foreach (ulong client in Clients.Keys.ToList())
            SendCatalog(client);
    }

    private static void SendCatalog(ulong client)
    {
        var cards = ObstacleManager.instance ? ObstacleManager.instance.allowedObstacleDescriptions : null;
        var surfaces = SurfaceManager.instance ? SurfaceManager.instance.surfaces : null;
        if (cards == null)
            return;
        if (Clients.TryGetValue(client, out var state))
            state.SentAt = Time.unscaledTime;

        var writer = new FastBufferWriter(4096, Allocator.Temp, 1 << 20);
        try
        {
            writer.WriteValueSafe(Plugin.Version);
            writer.WriteValueSafe(cards.Length);
            foreach (var d in cards)
                writer.WriteValueSafe(Key(d));
            int surfaceCount = surfaces?.Length ?? 0;
            writer.WriteValueSafe(surfaceCount);
            for (int i = 0; i < surfaceCount; i++)
                writer.WriteValueSafe(Key(surfaces[i]));
            NetworkManager.Singleton.CustomMessagingManager.SendNamedMessage(CatalogMessage, client, writer,
                NetworkDelivery.ReliableFragmentedSequenced);
        }
        finally
        {
            writer.Dispose();
        }
    }

    private static void OnRequest(ulong sender, FastBufferReader reader)
    {
        var nm = NetworkManager.Singleton;
        if (!nm.IsServer)
            return;
        if (!Clients.ContainsKey(sender))
            Clients[sender] = new ClientState();
        SendCatalog(sender);
    }

    private static void OnReply(ulong sender, FastBufferReader reader)
    {
        reader.ReadValueSafe(out string version);
        reader.ReadValueSafe(out int count);
        var missing = new HashSet<string>();
        for (int i = 0; i < count; i++)
        {
            reader.ReadValueSafe(out string key);
            missing.Add(key);
        }
        if (!Clients.TryGetValue(sender, out var state))
            Clients[sender] = state = new ClientState();
        state.Answered = true;
        state.Missing = missing;
        RebuildExclusions();
        if (version != Plugin.Version)
            Plugin.Log.LogWarning($"CatalogSync: player {sender} has Good Cards {version}, you have {Plugin.Version}. " +
                                  "Everyone should run the same version.");
        if (missing.Count > 0)
            Plugin.Log.LogWarning($"CatalogSync: player {sender} is missing {missing.Count} of your cards " +
                                  $"(other mods?), so they won't be drafted: {string.Join(", ", missing.Select(NameOf))}");
        else
            Plugin.Log.LogInfo($"CatalogSync: player {sender} has every card you have");
    }

    // ---------------------------------------------------------------- client

    private static void UpdateClient(NetworkManager nm)
    {
        if (!nm.IsConnectedClient)
            return;
        if (_connectedAt < 0f)
            _connectedAt = Time.unscaledTime;
        // The host pushes the lists when we connect; ask once in case that arrived before we were listening.
        if (_hostCards == null && !_requested && Time.unscaledTime - _connectedAt > 3f)
        {
            _requested = true;
            var writer = new FastBufferWriter(8, Allocator.Temp);
            try
            {
                nm.CustomMessagingManager.SendNamedMessage(RequestMessage, NetworkManager.ServerClientId, writer);
            }
            finally
            {
                writer.Dispose();
            }
        }
    }

    private static void OnCatalog(ulong sender, FastBufferReader reader)
    {
        reader.ReadValueSafe(out string version);
        reader.ReadValueSafe(out int cardCount);
        var cards = new List<string>(cardCount);
        for (int i = 0; i < cardCount; i++)
        {
            reader.ReadValueSafe(out string key);
            cards.Add(key);
        }
        reader.ReadValueSafe(out int surfaceCount);
        var surfaces = new List<string>(surfaceCount);
        for (int i = 0; i < surfaceCount; i++)
        {
            reader.ReadValueSafe(out string key);
            surfaces.Add(key);
        }
        _hostCards = cards;
        _hostSurfaces = surfaces;
        if (version != Plugin.Version)
            Plugin.Log.LogWarning($"CatalogSync: the host has Good Cards {version}, you have {Plugin.Version}. " +
                                  "Everyone should run the same version.");

        var missing = ApplyCards(ObstacleManager.instance);
        ApplySurfaces(SurfaceManager.instance);
        SendReply(missing);
    }

    private static void SendReply(List<string> missing)
    {
        var nm = NetworkManager.Singleton;
        if (!nm || !nm.IsListening || nm.IsServer)
            return;
        var writer = new FastBufferWriter(1024, Allocator.Temp, 1 << 20);
        try
        {
            writer.WriteValueSafe(Plugin.Version);
            writer.WriteValueSafe(missing.Count);
            foreach (var key in missing)
                writer.WriteValueSafe(key);
            nm.CustomMessagingManager.SendNamedMessage(ReplyMessage, NetworkManager.ServerClientId, writer,
                NetworkDelivery.ReliableFragmentedSequenced);
        }
        finally
        {
            writer.Dispose();
        }
    }

    // Client, after its own ObstacleManager or SurfaceManager is rebuilt: put the host's order back.
    internal static void OnClientListsChanged()
    {
        var nm = NetworkManager.Singleton;
        if (!nm || !nm.IsListening || nm.IsServer || _hostCards == null)
            return;
        var missing = ApplyCards(ObstacleManager.instance);
        ApplySurfaces(SurfaceManager.instance);
        SendReply(missing);
    }

    // Returns the host's cards this machine doesn't have.
    private static List<string> ApplyCards(ObstacleManager manager)
    {
        var missing = new List<string>();
        if (!manager || _hostCards == null || manager.allowedObstacleDescriptions == null)
            return missing;
        var local = manager.allowedObstacleDescriptions;
        var ordered = Reorder(local, _hostCards, Key, key =>
        {
            missing.Add(key);
            return Placeholder(key, local);
        }, out int extra);
        if (!ordered.SequenceEqual(local))
        {
            manager.allowedObstacleDescriptions = ordered.ToArray();
            Plugin.Log.LogInfo($"CatalogSync: card list put in the host's order ({_hostCards.Count} cards)");
        }
        if (missing.Count > 0)
            Plugin.Log.LogWarning($"CatalogSync: the host has {missing.Count} cards you don't (install the same card mods " +
                                  $"as the host): {string.Join(", ", missing.Select(NameOf))}");
        if (extra > 0)
            Plugin.Log.LogInfo($"CatalogSync: you have {extra} cards the host doesn't; they won't come up in this lobby");
        return missing;
    }

    private static void ApplySurfaces(SurfaceManager manager)
    {
        if (!manager || _hostSurfaces == null || manager.surfaces == null || _hostSurfaces.Count == 0)
            return;
        var local = manager.surfaces;
        int missingCount = 0;
        var ordered = Reorder(local, _hostSurfaces, Key, key =>
        {
            missingCount++;
            return manager.defaultSurface;   // a road the host swaps to a surface we lack shows as plain road
        }, out _);
        if (!ordered.SequenceEqual(local))
        {
            manager.surfaces = ordered.ToArray();
            Plugin.Log.LogInfo($"CatalogSync: surface list put in the host's order ({_hostSurfaces.Count} surfaces)");
        }
        if (missingCount > 0)
            Plugin.Log.LogWarning($"CatalogSync: the host has {missingCount} road surfaces you don't (other mods?)");
    }

    // The host's order; each host key takes the first unused local entry with that key.
    private static List<T> Reorder<T>(T[] local, List<string> hostKeys, System.Func<T, string> key,
        System.Func<string, T> missing, out int extra)
    {
        var used = new bool[local.Length];
        var result = new List<T>(Mathf.Max(local.Length, hostKeys.Count));
        foreach (var hostKey in hostKeys)
        {
            int found = -1;
            for (int i = 0; i < local.Length; i++)
            {
                if (!used[i] && key(local[i]) == hostKey)
                {
                    found = i;
                    break;
                }
            }
            if (found >= 0)
            {
                used[found] = true;
                result.Add(local[found]);
            }
            else
            {
                result.Add(missing(hostKey));
            }
        }
        extra = 0;
        for (int i = 0; i < local.Length; i++)
        {
            if (used[i])
                continue;
            result.Add(local[i]);
            extra++;
        }
        return result;
    }

    // Stands in for a card only the host has: never rolled here (only the host rolls anyway), and its text
    // says what's missing if it ever shows up on a draft.
    private static ObstacleDescription Placeholder(string key, ObstacleDescription[] local)
    {
        if (Placeholders.TryGetValue(key, out var existing) && existing)
            return existing;
        var template = local.FirstOrDefault(d => d && d.type == ObstacleType.Prop && d.maxQuantity != 0) ?? local.FirstOrDefault(d => d);
        if (!template)
            return null;
        var placeholder = Object.Instantiate(template);
        placeholder.name = $"GoodCards_Missing_{NameOf(key)}";
        placeholder.hideFlags = HideFlags.DontUnloadUnusedAsset;
        placeholder.maxQuantity = 0;
        CardText.Register(placeholder.displayName, "Missing card");
        CardText.Register(placeholder.description,
            $"The host has a card you don't (<color=#E0204A>{NameOf(key)}</color>). Install the same card mods as the host.");
        Placeholders[key] = placeholder;
        return placeholder;
    }

    private static string NameOf(string key)
    {
        int slash = key.IndexOf('/');
        return slash >= 0 ? key.Substring(slash + 1) : key;
    }
}

// Runs after every other mod's Awake postfix (they append their cards there), so the lists are final.
[HarmonyPatch(typeof(ObstacleManager), "Awake")]
internal static class CatalogSyncObstacleManagerPatch
{
    [HarmonyPriority(Priority.Last)]
    private static void Postfix(ObstacleManager __instance) => Guard.Run("CatalogSync", () =>
    {
        if (ObstacleManager.instance != __instance)
            return;
        CatalogSync.OnHostListsChanged();
        CatalogSync.OnClientListsChanged();
    });
}

[HarmonyPatch(typeof(SurfaceManager), "Awake")]
internal static class CatalogSyncSurfaceManagerPatch
{
    [HarmonyPriority(Priority.Last)]
    private static void Postfix(SurfaceManager __instance) => Guard.Run("CatalogSync", () =>
    {
        if (SurfaceManager.instance != __instance)
            return;
        CatalogSync.OnHostListsChanged();
        CatalogSync.OnClientListsChanged();
    });
}
