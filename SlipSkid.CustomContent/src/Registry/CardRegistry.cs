using System;
using System.Linq;
using BepInEx.Configuration;
using Obstacles;
using UnityEngine;
using Utils;
using Object = UnityEngine.Object;

namespace SlipSkid.CustomContent;

internal static class CardRegistry
{
    // APPEND-ONLY. A card's position here is its slot, which travels over the network inside
    // the spawn marker, and its catalog index follows this order. Never reorder or remove.
    internal static readonly CustomObstacle[] Entries =
    {
        new BumperPillar(),
        new DataObstacle("JengaTower", "9853880f-a011-48d1-8b38-62e5f2ddcbc8"),
        new DataObstacle("BookStack", "314c5b58-1e69-4aaf-8ebc-2634ce8bf6e3"),
        new DataObstacle("Baguette", "d8a6a063-356d-43db-960e-5b963c4f405b"),
        new DataObstacle("RubberDuck", "f6c94350-1a16-4014-ab6b-90e88f9cdc2b"),
        new DataObstacle("DominoLine", "6d8e8286-9859-49d3-940f-3b14daf2501c"),
        new DataObstacle("Sponge", "b5af8a6b-09fd-4981-83be-4c5bdfe6e58e"),
        new DataObstacle("TinCanPyramid", "8c5903a6-b322-4516-8452-c892dadd0237"),
        new DataObstacle("Mattress", "94cd60b7-8434-4f06-b306-3d91f8b9e4c1"),
        new DataObstacle("WhoopeeCushion", "7c5b4e20-e012-4b9e-9764-4aa688695be3"),
        new DataObstacle("HotSaucePuddle", "5dd0ef9a-2167-481a-9170-a505929b9053"),
        new DataObstacle("Skateboard", "2e359e20-bb9a-440f-882f-0ba6721142c5"),
        new DataObstacle("LegoBrick", "2ce887f1-33e2-4664-a62b-3e1bc82c50b8"),
        new DataObstacle("Blender", "8546b197-ad4a-474b-8e6f-9e2615489ee5"),
        new DataObstacle("CheeseGrater", "85fd7abf-565e-46bc-a50a-d4b844366c0d"),
        new DataObstacle("LavaLamp", "2493ddf5-74ce-4979-856d-132013c39213"),
        new DataObstacle("Hairbrush", "e0438278-709c-4342-b2bc-3fc0d3a8f1b3"),
        new DataObstacle("RevolvingDoor", "424ae098-7460-42b1-9579-993650de4574"),
        new DataObstacle("MiniGolfWindmill", "a171e1b4-5d97-4184-9ef4-e14fe8658bb7"),
        new DataObstacle("Metronome", "294ae1b6-24cc-434e-ac06-edb4306f042a"),
        new DataObstacle("WhackAMole", "3a9f2919-1829-434f-bf18-4cb7042ac04c"),
        new DataObstacle("JackInTheBox", "21d3e9a3-33bd-4ada-b23d-09ab8d32f128"),
        new DataObstacle("Turntable", "d2e6d433-5df6-43ba-8a19-94a7ea42e1e6"),
        new DataObstacle("Toaster", "c911804a-ac64-4e0e-bee9-d0a0dab793ae"),
        new DataObstacle("Slingshot", "f5db2031-d3f3-4156-b537-ae66bac4af63"),
        new DataObstacle("ShakenSoda", "bf30a812-8da6-4588-b900-a53c473e9822"),
        new DataObstacle("Mousetrap", "0253ebe1-f3bc-4b29-8373-8600f7c765e8"),
        new DataObstacle("GardenRake", "65a2e27c-d094-4cee-b85f-7b9719559d9d"),
        new DataObstacle("PizzaCutter", "0c1ab705-cee0-43d5-9a5d-d71135b65ac2"),
        new DataObstacle("MagnifyingGlass", "21877700-5faf-403b-8845-4a9456a73325"),
        new DataObstacle("Toilet", "595a4393-902e-4a8e-b597-f104c2a01812"),
        new DataObstacle("SewerExit", "6b146b54-38ff-466b-bddf-3b4ff5d11071"),   // the Toilet's partner, never drafted
        new TestArena(),   // F6 debug platform, never drafted
        new DataObstacle("LongRamp", "8100eea0-9a6a-4238-8889-19b167bc0adc"),
        new DataObstacle("LongRoad", "f3ce1038-7403-4d29-95ed-2094fd82cf2f"),
        new DataObstacle("CurvedRoad", "ad93f9b0-97e6-4f2c-acb3-ed700de1250e"),
        new DataObstacle("LowGravityZone", "35519524-6c8b-406b-ac0b-e606cf330315"),
        new DataObstacle("Drawbridge", "d0b4021a-4620-48bf-b4fd-ffcf272949e3"),
        new DataObstacle("ShockMine", "b208a31a-bad1-464b-a4be-5bd069e66af6"),
        new DataObstacle("TeleportGrenade", "e368c8b9-4faf-41d3-bd3a-df0ffc349883"),
        new DataObstacle("ShockMinefield", "26a70780-46d5-4966-a6ba-0b1f30a9da07"),    // scatters ShockMine (LandMineScatter carrier)
        new DataObstacle("GrenadeShower", "821cc5d4-2da6-4c21-a753-6f0349423121"),     // scatters TeleportGrenade
        new DataObstacle("ReverseRoad", "e1776ea2-0f52-4fec-ab11-56b9c9342b5d"),       // surface swap to the Reverse surface
    };

    // One clone per slot, built once and reused for every ObstacleManager instance.
    private static ObstacleDescription[] _descriptions;

    internal static void BindConfig(ConfigFile config)
    {
        foreach (var entry in Entries)
            entry.BindConfig(config);
    }

    internal static CustomObstacle Get(int slot) =>
        slot >= 0 && slot < Entries.Length ? Entries[slot] : null;

    internal static int SlotOf(ObstacleDescription description)
    {
        if (_descriptions == null || !description)
            return -1;
        return Array.IndexOf(_descriptions, description);
    }

    internal static ObstacleDescription DescriptionOf(string id)
    {
        if (_descriptions == null)
            return null;
        int slot = Array.FindIndex(Entries, e => string.Equals(e.Id, id, StringComparison.OrdinalIgnoreCase));
        return slot >= 0 ? _descriptions[slot] : null;
    }

    internal static void Register(ObstacleManager manager)
    {
        if (_descriptions == null)
            _descriptions = Entries.Select(e => CreateDescription(e, manager.allowedObstacleDescriptions)).ToArray();

        var catalog = manager.allowedObstacleDescriptions.ToList();
        for (int slot = 0; slot < Entries.Length; slot++)
        {
            var description = _descriptions[slot];
            if (!description || catalog.Contains(description))
                continue;
            catalog.Add(description);
            Plugin.Log.LogInfo($"CustomCards: {Entries[slot].Id} at index {catalog.Count - 1} " +
                               $"(carrier {description.prefab.name}, rarity {Entries[slot].Rarity.Value})");
        }
        manager.allowedObstacleDescriptions = catalog.ToArray();
    }

    private static ObstacleDescription CreateDescription(CustomObstacle entry, ObstacleDescription[] catalog)
    {
        var carrier = FindCarrier(entry, catalog);
        if (!carrier)
        {
            Plugin.Log.LogError($"CustomCards: no carrier found for {entry.Id}; it will not be registered. " +
                                "Every player must see this same error, or the draft will desync.");
            return null;
        }

        var clone = Object.Instantiate(carrier);
        clone.name = $"CustomContent_{entry.Id}";
        clone.hideFlags = HideFlags.DontUnloadUnusedAsset;
        clone.id = new SerializableGuid(entry.Guid);
        if (entry.Rarity.Value == CardRarity.Off || entry.IsPartnerOnly)
            clone.maxQuantity = 0;
        else
            clone.rarity = (ObstacleDescription.ObstacleRarity)(entry.Rarity.Value - 1);
        if (!string.IsNullOrEmpty(entry.FullArtFile))
            ApplyFullArt(clone, entry, catalog);

        // Instantiate deep-copies serialized classes, so these are the clone's own LocalizedStrings.
        if (ReferenceEquals(clone.displayName, carrier.displayName) || ReferenceEquals(clone.description, carrier.description))
            Plugin.Log.LogWarning($"CustomCards: {entry.Id} shares LocalizedStrings with its carrier; its text would leak onto the carrier");
        else
        {
            CardText.Register(clone.displayName, entry.DisplayName);
            CardText.Register(clone.description, entry.Description);
        }

        var thumbnail = ThumbnailLoader.Load(entry.ThumbnailFile);
        if (thumbnail)
            clone.thumbnail = thumbnail;
        return clone;
    }

    // ObstacleSelectionElement.SetStyle: isFullArt hides the border, icons and stars, and
    // overrideBackGroundMaterialTexture (a Sprite) replaces the thumbnail with art covering the card.
    // The shiny material and name font come from a vanilla full-art card.
    private static void ApplyFullArt(ObstacleDescription clone, CustomObstacle entry, ObstacleDescription[] catalog)
    {
        var template = catalog.FirstOrDefault(d => d && d.isFullArt && d.overrideBackGroundMaterial);
        var texture = ThumbnailLoader.Load(entry.FullArtFile);
        if (!template || !texture)
        {
            Plugin.Log.LogWarning($"CustomCards: {entry.Id} full art unavailable (template {(bool)template}, art {(bool)texture})");
            return;
        }
        var sprite = Sprite.Create(texture, new Rect(0, 0, texture.width, texture.height), new Vector2(0.5f, 0.5f), 100f);
        sprite.name = $"{entry.Id}_FullArt";
        sprite.hideFlags = HideFlags.DontUnloadUnusedAsset;
        clone.isFullArt = true;
        clone.overrideBackGroundMaterial = template.overrideBackGroundMaterial;
        clone.overrideBackGroundMaterialTexture = sprite;
        clone.overrideBackGroundMaterialNormalMap = null;
        clone.overrideNameFontMaterial = template.overrideNameFontMaterial;
        clone.overrideShineColor = template.overrideShineColor;
        clone.shineColor = template.shineColor;
        Plugin.Log.LogInfo($"CustomCards: {entry.Id} uses full art (style from {template.name})");
    }

    private static ObstacleDescription FindCarrier(CustomObstacle entry, ObstacleDescription[] catalog)
    {
        string wanted = entry.Carrier.Value;
        if (!string.IsNullOrWhiteSpace(wanted))
        {
            var named = catalog.FirstOrDefault(d => d && d.name == wanted);
            if (named)
                return named;
            Plugin.Log.LogWarning($"CustomCards: carrier '{wanted}' for {entry.Id} not found, picking one automatically");
        }
        // Catalog order is the same on every machine, so the first match is too.
        return catalog.FirstOrDefault(d => d && entry.IsCarrierCandidate(d));
    }
}
