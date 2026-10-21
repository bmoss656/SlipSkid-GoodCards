using Obstacles;
using UnityEngine;

namespace SlipSkid.CustomContent;

// What we keep from the carrier before stripping it, so our parts look and collide like vanilla ones.
internal sealed class CarrierParts
{
    public Material Material;
    public int SolidLayer;
    public int TriggerLayer;
    public Vector3 PrefabScale = Vector3.one;
}

// Added to swapped obstacles so the swap never runs twice on one object.
internal sealed class CustomObstacleTag : MonoBehaviour
{
    public int Slot;
}

internal static class VisualSwap
{
    // Removes the carrier's look, collision and behaviour without touching any GameObject or
    // NetworkBehaviour, since NGO tracks those. Uses DestroyImmediate because Obstacle.Init caches
    // GetComponentsInChildren straight after, and a deferred Destroy would leave dead entries.
    internal static CarrierParts StripCarrier(Obstacle obstacle)
    {
        var parts = ReadCarrier(obstacle);
        var root = obstacle.gameObject;

        DestroyAll<KillZone>(root);
        DestroyAll<BounceZone>(root);
        DestroyAll<Zone>(root);
        DestroyAll<AccelerationZone>(root);
        DestroyAll<SlowDownZone>(root);
        DestroyAll<ZoneWithMinSpeed>(root);
        DestroyAll<Obstacles.Ray>(root);
        DestroyAll<Collider>(root);

        // Emptying the meshes hides the carrier even if the game re-enables its renderers later.
        // (The stripped build has no LODGroup or SkinnedMeshRenderer.sharedMesh; static carriers don't use them.)
        foreach (var filter in root.GetComponentsInChildren<MeshFilter>(true))
            filter.sharedMesh = null;

        return parts;
    }

    // What we reuse from the carrier (material, physics layers, prefab scale), without changing it.
    internal static CarrierParts ReadCarrier(Obstacle obstacle)
    {
        var root = obstacle.gameObject;
        var parts = new CarrierParts
        {
            SolidLayer = root.layer,
            TriggerLayer = root.layer,
        };
        if (obstacle.description && obstacle.description.prefab)
            parts.PrefabScale = obstacle.description.prefab.transform.localScale;

        foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
        {
            if (!parts.Material && renderer.sharedMaterial)
                parts.Material = renderer.sharedMaterial;
        }

        bool foundSolid = false, foundTrigger = false;
        foreach (var collider in root.GetComponentsInChildren<Collider>(true))
        {
            if (collider.isTrigger && !foundTrigger)
            {
                parts.TriggerLayer = collider.gameObject.layer;
                foundTrigger = true;
            }
            else if (!collider.isTrigger && !foundSolid)
            {
                parts.SolidLayer = collider.gameObject.layer;
                foundSolid = true;
            }
        }
        return parts;
    }

    private static void DestroyAll<T>(GameObject root) where T : Component
    {
        foreach (var component in root.GetComponentsInChildren<T>(true))
            Object.DestroyImmediate(component);
    }

    // Converts a world-size scale into a local scale under the obstacle's root.
    internal static Vector3 ToLocal(Vector3 worldSize, CarrierParts carrier) =>
        new(worldSize.x / carrier.PrefabScale.x, worldSize.y / carrier.PrefabScale.y, worldSize.z / carrier.PrefabScale.z);
}
