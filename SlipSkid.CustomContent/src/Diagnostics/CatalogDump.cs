using System.Linq;
using Obstacles;
using Unity.Netcode;
using UnityEngine;

namespace SlipSkid.CustomContent;

// Logs every card in the catalog, so we can pick carriers and see how vanilla obstacles are built.
internal static class CatalogDump
{
    internal static void Log(ObstacleManager manager)
    {
        var catalog = manager.allowedObstacleDescriptions;
        int hidden = manager.hiddenObstacleDescriptions?.Length ?? 0;
        Plugin.Log.LogInfo($"Catalog: {catalog.Length} cards, {hidden} hidden");
        for (int i = 0; i < catalog.Length; i++)
            Plugin.Log.LogInfo($"Catalog[{i}] {Describe(catalog[i])}");
        LogMaterials(catalog);
        LogZones(catalog);
    }

    // The tuning of vanilla zones, so our obstacles can match how hard vanilla ones bounce or push.
    private static void LogZones(ObstacleDescription[] catalog)
    {
        foreach (var d in catalog.Where(d => d && d.prefab))
        {
            var root = d.prefab.gameObject;
            foreach (var b in root.GetComponentsInChildren<BounceZone>(true))
                Plugin.Log.LogInfo($"Zone: {d.name} Bounce factor={b.bounceFactor} collisionNormal={b.useCollisionNormal} customNormal={b.useCustomNormal}:{b.customNormal} customVelocity={b.useCustomVelocity}:{b.customBounceVelocity} counterNegative={b.counterNegativeVelocity}");
            foreach (var a in root.GetComponentsInChildren<AccelerationZone>(true))
                Plugin.Log.LogInfo($"Zone: {d.name} Accel acceleration={a.acceleration} setVelocity={a.setVelocityOnEnter}:{a.velocityOnEnter}");
            foreach (var s in root.GetComponentsInChildren<SlowDownZone>(true))
                Plugin.Log.LogInfo($"Zone: {d.name} Slow factor={s.slowDownFactor} stop={s.stopCompletelyOnEnter}");
            foreach (var k in root.GetComponentsInChildren<KillZone>(true))
                Plugin.Log.LogInfo($"Zone: {d.name} Kill aligned={k.alignedVelocityToKill} axis={k.alignedVelocityNormalType}");
        }
    }

    // Size of the prefab's meshes in its root space, so our obstacles can match vanilla scale.
    private static string MeshSize(GameObject root)
    {
        bool any = false;
        var bounds = new Bounds();
        foreach (var filter in root.GetComponentsInChildren<MeshFilter>(true))
        {
            if (!filter.sharedMesh)
                continue;
            var b = filter.sharedMesh.bounds;
            for (int i = 0; i < 8; i++)
            {
                var corner = new Vector3(i % 2 == 0 ? b.min.x : b.max.x, (i / 2) % 2 == 0 ? b.min.y : b.max.y, i / 4 == 0 ? b.min.z : b.max.z);
                var p = root.transform.InverseTransformPoint(filter.transform.TransformPoint(corner));
                if (!any) { bounds = new Bounds(p, Vector3.zero); any = true; }
                else bounds.Encapsulate(p);
            }
        }
        return any ? $"({bounds.size.x:0.0}x{bounds.size.y:0.0}x{bounds.size.z:0.0} minY={bounds.min.y:0.0})" : "none";
    }

    // Shader names and properties of a few plain props, so we know how to colour our own parts.
    private static void LogMaterials(ObstacleDescription[] catalog)
    {
        var seenShaders = new System.Collections.Generic.HashSet<string>();
        foreach (var d in catalog.Where(d => d && d.prefab && d.type == ObstacleType.Prop).Take(30))
        {
            foreach (var renderer in d.prefab.GetComponentsInChildren<MeshRenderer>(true))
            {
                foreach (var material in renderer.sharedMaterials)
                {
                    if (!material || !material.shader)
                        continue;
                    var shader = material.shader;
                    Plugin.Log.LogInfo($"Material: {d.name}/{renderer.name} {material.name} shader={shader.name}");
                    if (!seenShaders.Add(shader.name))
                        continue;
                    var props = new System.Collections.Generic.List<string>();
                    for (int i = 0; i < shader.GetPropertyCount(); i++)
                        props.Add(shader.GetPropertyName(i));
                    Plugin.Log.LogInfo($"Shader: {shader.name} props=[{string.Join(",", props)}]");
                }
            }
        }
    }

    private static string Describe(ObstacleDescription d)
    {
        if (!d)
            return "null";
        string head = $"{d.name} type={d.type} body={d.bodyBodyType} move={d.movementType} rot={d.rotationType} " +
                      $"rarity={d.rarity} maxQty={d.maxQuantity} affixes={d.allowedAffixes?.Length ?? 0} " +
                      $"thumb={(d.thumbnail ? $"{d.thumbnail.width}x{d.thumbnail.height}" : "none")} fullArt={d.isFullArt}";
        if (!d.prefab)
            return head + " prefab=null";

        var root = d.prefab.gameObject;
        var colliders = root.GetComponentsInChildren<Collider>(true);
        int triggers = colliders.Count(c => c.isTrigger);
        string layers = string.Join(",", colliders.Select(c => LayerMask.LayerToName(c.gameObject.layer)).Distinct());
        int renderers = root.GetComponentsInChildren<MeshRenderer>(true).Length;
        string netParts = string.Join(",", root.GetComponentsInChildren<NetworkBehaviour>(true)
            .Where(n => n != d.prefab)
            .Select(n => n.transform == root.transform ? n.GetType().Name : $"{n.GetType().Name}@{n.name}"));
        string parts = string.Join(",", root.GetComponentsInChildren<MonoBehaviour>(true)
            .Where(m => m && m != d.prefab && m.GetType().Namespace == "Obstacles")
            .GroupBy(m => m.GetType().Name)
            .Select(g => g.Count() > 1 ? $"{g.Key}x{g.Count()}" : g.Key));

        return $"{head} prefab={d.prefab.name} class={d.prefab.GetType().Name} scale={d.prefab.transform.localScale} size={MeshSize(root)} " +
               $"colliders={colliders.Length - triggers}+{triggers}trig layers=[{layers}] renderers={renderers} " +
               $"net=[{netParts}] parts=[{parts}]";
    }
}
