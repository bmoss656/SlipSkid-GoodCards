using System;
using BepInEx.Configuration;
using Obstacles;
using UnityEngine;

namespace SlipSkid.CustomContent;

// A solid square pillar that bounces cars away. Built from a Unity primitive until we have a real model.
internal sealed class BumperPillar : CustomObstacle
{
    public override string Id => "BumperPillar";
    public override Guid Guid { get; } = new("6f1c2a5e-3b7d-4c1e-9a8f-2d5b7e0c4a11");
    protected override CardRarity DefaultRarity => CardRarity.Uncommon;
    public override string DisplayName => "The Bumper";
    public override string Description => "A solid pillar that <color=#2F7BFF>bounces</color> any vehicle that hits it.";

    private ConfigEntry<float> _width;
    private ConfigEntry<float> _height;
    private ConfigEntry<float> _bounceFactor;

    internal override void BindConfig(ConfigFile config)
    {
        base.BindConfig(config);
        _width = config.Bind(Section, "Width", 3f, "Pillar width in metres. Must match for every player.");
        _height = config.Bind(Section, "Height", 3f, "Pillar height in metres. Must match for every player.");
        _bounceFactor = config.Bind(Section, "BounceFactor", 1.0f,
            "Push strength: 1 throws cars away at 18 m/s. Must match for every player.");
    }

    internal override void Build(Obstacle obstacle, CarrierParts carrier)
    {
        float width = _width.Value;
        float height = _height.Value;

        // A cube, because its BoxCollider matches the mesh exactly and needs no stripped members
        // (the stripped build has no MeshCollider.sharedMesh). Assumes the carrier's pivot sits on the ground.
        var pillar = GameObject.CreatePrimitive(PrimitiveType.Cube);
        pillar.name = "CustomContent_BumperPillar";
        pillar.layer = carrier.SolidLayer;
        pillar.transform.SetParent(obstacle.transform, false);
        pillar.transform.localPosition = VisualSwap.ToLocal(new Vector3(0f, height / 2f, 0f), carrier);
        pillar.transform.localScale = VisualSwap.ToLocal(new Vector3(width, height, width), carrier);

        if (carrier.Material)
            pillar.GetComponent<MeshRenderer>().sharedMaterial = carrier.Material;

        // A fixed-speed push: a reflecting BounceZone sees the car already stopped by the contact.
        var push = pillar.AddComponent<PushZone>();
        push.speed = 18f * _bounceFactor.Value;
        push.up = 4f;

        // Placement checks these root-local points against forbidden zones: centre plus the four corners.
        float half = width / 2f;
        obstacle.pointsToCheckForbiddenZones = new[]
        {
            Vector3.zero,
            VisualSwap.ToLocal(new Vector3(half, 0f, half), carrier),
            VisualSwap.ToLocal(new Vector3(-half, 0f, half), carrier),
            VisualSwap.ToLocal(new Vector3(half, 0f, -half), carrier),
            VisualSwap.ToLocal(new Vector3(-half, 0f, -half), carrier),
        };
    }
}
