using System;
using Obstacles;
using UnityEngine;
using Object = UnityEngine.Object;

namespace SlipSkid.CustomContent;

// A huge flat platform for testing obstacles (F6), spawned high above the current map. It's a hidden
// card, so it travels over the network like any obstacle and every player sees the same arena.
internal sealed class TestArena : CustomObstacle
{
    public const float Size = 160f;
    public const float Height = 250f;

    public override string Id => "TestArena";
    public override Guid Guid { get; } = new("3f0e7b52-6a1d-4c8e-9f3b-8d2a51c7e604");
    protected override CardRarity DefaultRarity => CardRarity.Off;
    public override string DisplayName => "The Test Arena";
    public override string Description => "Debug only.";
    public override bool IsPartnerOnly => true;

    internal override void Build(Obstacle obstacle, CarrierParts carrier)
    {
        var floorMaterial = MaterialLibrary.Resolve("toon:#C9CDD6", carrier.Material);
        var lineMaterial = MaterialLibrary.Resolve("toon:#7D8494", carrier.Material);

        // Top surface at the obstacle's origin, so the arena sits exactly where it was spawned.
        var floor = GameObject.CreatePrimitive(PrimitiveType.Cube);
        floor.name = "CustomContent_ArenaFloor";
        floor.layer = carrier.SolidLayer;
        floor.transform.SetParent(obstacle.transform, false);
        floor.transform.localPosition = VisualSwap.ToLocal(new Vector3(0f, -1f, 0f), carrier);
        floor.transform.localScale = VisualSwap.ToLocal(new Vector3(Size, 2f, Size), carrier);
        floor.GetComponent<MeshRenderer>().sharedMaterial = floorMaterial;

        // A 10 m grid, visual only, to judge distances and sizes.
        for (int i = 0; i <= Size / 10f; i++)
        {
            float offset = -Size / 2f + i * 10f;
            Line(obstacle, carrier, lineMaterial, new Vector3(offset, 0.02f, 0f), new Vector3(0.3f, 0.04f, Size));
            Line(obstacle, carrier, lineMaterial, new Vector3(0f, 0.02f, offset), new Vector3(Size, 0.04f, 0.3f));
        }
        obstacle.pointsToCheckForbiddenZones = new[] { Vector3.zero };
    }

    private static void Line(Obstacle obstacle, CarrierParts carrier, Material material, Vector3 position, Vector3 size)
    {
        var line = GameObject.CreatePrimitive(PrimitiveType.Cube);
        line.name = "CustomContent_ArenaLine";
        Object.DestroyImmediate(line.GetComponent<Collider>());
        line.transform.SetParent(obstacle.transform, false);
        line.transform.localPosition = VisualSwap.ToLocal(position, carrier);
        line.transform.localScale = VisualSwap.ToLocal(size, carrier);
        line.GetComponent<MeshRenderer>().sharedMaterial = material;
    }
}
