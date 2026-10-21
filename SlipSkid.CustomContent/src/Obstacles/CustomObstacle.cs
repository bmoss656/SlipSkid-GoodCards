using System;
using System.Linq;
using BepInEx.Configuration;
using Obstacles;
using Unity.Netcode;
using UnityEngine;

namespace SlipSkid.CustomContent;

internal enum CardRarity
{
    Off,
    Common,
    Uncommon,
    Rare,
    UltraRare,
    Legendary,
    Unique,
}

// A placeable obstacle that rides on a vanilla "carrier" card: the host spawns the carrier's
// network prefab, and every machine swaps its visuals and colliders for ours on spawn.
internal abstract class CustomObstacle
{
    // Stable name used in config, logs and Debug.ForceCard. Never change it once released.
    public abstract string Id { get; }

    // Stable ObstacleDescription id, identical on every machine. Never change it once released.
    public abstract Guid Guid { get; }

    protected abstract CardRarity DefaultRarity { get; }

    // Card text. TextMeshPro rich text works, e.g. <color=#2F7BFF>Bounces</color>.
    public abstract string DisplayName { get; }
    public abstract string Description { get; }

    // Card art: a PNG next to the plugin DLL (copied there from assets/ by the build).
    public virtual string ThumbnailFile => $"{Id}.png";

    // Full-art ("epic") card: this PNG fills the whole card, styled like the vanilla full-art cards.
    public virtual string FullArtFile => null;

    // Placing this obstacle hands its owner the partner obstacle to place next (the Toilet's Sewer Exit).
    public virtual string PartnerId => null;

    // Only ever spawned as another card's partner: registered (so indices match) but never drafted.
    public virtual bool IsPartnerOnly => false;

    // Default for the Carrier config: a specific vanilla card to borrow (asset name), or null to auto-pick.
    public virtual string DefaultCarrier => null;

    // Keep the carrier's own look and logic instead of stripping it (scatters, surface swaps).
    public virtual bool KeepCarrier => false;

    internal ConfigEntry<CardRarity> Rarity { get; private set; }
    internal ConfigEntry<string> Carrier { get; private set; }

    protected string Section => $"Card.{Id}";

    internal virtual void BindConfig(ConfigFile config)
    {
        Rarity = config.Bind(Section, "Rarity", DefaultRarity,
            "How often the card is offered. Off keeps it registered but never rolled. Must match for every player.");
        Carrier = config.Bind(Section, "Carrier", DefaultCarrier ?? "",
            "Asset name of the vanilla card to borrow (see the Catalog lines in the log). Empty picks one automatically.");
    }

    // Every vanilla prefab carries one extra NetworkBehaviour (likely ChangeOwnerByDistance). That's fine:
    // stripping never removes GameObjects or NetworkBehaviours. These two run logic on the parts we strip.
    private static readonly Type[] UnsafeNetworkParts = { typeof(ScorePointZone), typeof(SpeedCamera) };

    // Default carrier: a plain static prop with a solid collider and no networked logic we'd break.
    internal virtual bool IsCarrierCandidate(ObstacleDescription d)
    {
        if (d.type != ObstacleType.Prop || d.bodyBodyType != ObstacleBodyType.Static || !d.prefab)
            return false;
        if (d.prefab.GetType() != typeof(Obstacle))
            return false;
        var root = d.prefab.gameObject;
        if (root.GetComponentsInChildren<NetworkBehaviour>(true).Any(n => UnsafeNetworkParts.Contains(n.GetType())))
            return false;
        if (root.GetComponentsInChildren<NetworkAnimatedTransformation>(true).Length > 0)
            return false;
        return root.GetComponentsInChildren<Collider>(true).Any(c => !c.isTrigger);
    }

    // Runs on every machine during Obstacle.OnNetworkSpawn, after the carrier has been stripped
    // and before the game caches the obstacle's colliders and renderers.
    internal abstract void Build(Obstacle obstacle, CarrierParts carrier);
}
