using System.Collections.Generic;
using Obstacles;
using UnityEngine;
using UnityEngine.Rendering;

namespace SlipSkid.CustomContent;

// Turns ObstacleData into GameObjects under the obstacle. Runs on every machine.
internal static class DataObstacleBuilder
{
    internal static void Build(string id, ObstacleData data, Obstacle obstacle, CarrierParts carrier)
    {
        // Built inactive and switched on at the end: AccelerationZone and the network animators read
        // their fields in Awake, so those must be set first.
        var container = new GameObject($"CustomContent_{id}");
        container.SetActive(false);
        container.layer = carrier.SolidLayer;
        container.transform.SetParent(obstacle.transform, false);
        container.transform.localScale = VisualSwap.ToLocal(Vector3.one, carrier);

        int triggerLayer = LayerMask.NameToLayer("Obstacle");
        if (triggerLayer < 0)
            triggerLayer = carrier.TriggerLayer;

        var contents = new Transform[data.nodes.Count];
        for (int i = 0; i < data.nodes.Count; i++)
        {
            var node = data.nodes[i];
            var go = new GameObject(node.name ?? $"Node{i}");
            go.layer = carrier.SolidLayer;
            var parent = node.parent >= 0 && node.parent < i ? contents[node.parent] : container.transform;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = ToVector(node.pos, Vector3.zero);
            go.transform.localRotation = ToQuaternion(node.rot);
            go.transform.localScale = ToVector(node.scale, Vector3.one);

            // Animated nodes get a pivot child: the animator sets its absolute local rotation/scale,
            // so everything that moves hangs under the pivot while the node keeps its rest transform.
            var content = go.transform;
            if (node.anim != null)
                content = AddAnimator(go, node.anim);
            if (node.motion != null)
                content = AddMotion(content.gameObject, node.motion);
            if (node.timed != null)
            {
                var timed = content.gameObject.AddComponent<TimedActive>();
                timed.speed = node.timed.speed;
                timed.start = node.timed.start;
                timed.end = node.timed.end;
            }
            if (node.effect != null)
            {
                var effect = content.gameObject.AddComponent<BurstEffect>();
                effect.channel = node.effect.channel;
                effect.kind = node.effect.kind == "teleport" ? BurstEffect.Kind.Teleport : BurstEffect.Kind.Shock;
                effect.consume = node.effect.consume;
            }
            if (node.crumble != null)
            {
                var crumble = content.gameObject.AddComponent<Crumble>();
                crumble.channel = node.crumble.channel;
                crumble.minSpeed = node.crumble.minSpeed;
                crumble.speed = node.crumble.speed;
                crumble.stagger = node.crumble.stagger;
                crumble.settleTime = node.crumble.settleTime;
            }
            contents[i] = content;

            if (node.mesh != null)
                AddMesh(content.gameObject, node.mesh, carrier.Material);
            if (node.collider != null)
            {
                var collider = AddCollider(content.gameObject, node.collider);
                content.gameObject.layer = node.collider.trigger ? triggerLayer : carrier.SolidLayer;
                if (node.zone != null)
                    AddZone(content.gameObject, collider, node.zone, obstacle);
            }
        }

        if (data.forbiddenPoints is { Length: > 0 })
        {
            var points = new Vector3[data.forbiddenPoints.Length];
            for (int i = 0; i < points.Length; i++)
                points[i] = VisualSwap.ToLocal(ToVector(data.forbiddenPoints[i], Vector3.zero), carrier);
            obstacle.pointsToCheckForbiddenZones = points;
        }

        container.SetActive(true);
    }

    private static Transform AddAnimator(GameObject node, AnimData anim)
    {
        // Inside the still-inactive container, so the animator's Awake waits until its fields are set.
        var pivot = new GameObject($"{node.name}_Pivot");
        pivot.layer = node.layer;
        pivot.transform.SetParent(node.transform, false);

        NetworkAnimatedTransformation animator = anim.type switch
        {
            "scale" => pivot.AddComponent<NetworkAnimatedScale>(),
            "position" => pivot.AddComponent<NetworkAnimatedPosition>(),
            _ => pivot.AddComponent<NetworkAnimatedRotation>(),
        };
        animator.target = pivot.transform;
        animator.min = ToVector(anim.min, Vector3.zero);
        animator.max = ToVector(anim.max, anim.type == "scale" ? Vector3.one : Vector3.zero);
        animator.speed = anim.speed;
        animator.easing = ToCurve(anim);
        animator.restingRotation = anim.type == "rotation" ? animator.min : Vector3.zero;
        animator.restingScale = anim.type == "scale" ? animator.min : Vector3.one;
        animator.previewStepsNumber = 0;
        return pivot.transform;
    }

    private static Transform AddMotion(GameObject node, MotionData data)
    {
        var pivot = new GameObject($"{node.name}_Motion");
        pivot.layer = node.layer;
        pivot.transform.SetParent(node.transform, false);
        var motion = pivot.AddComponent<TriggeredMotion>();
        motion.channel = data.channel;
        motion.kind = data.type switch
        {
            "position" => TriggeredMotion.Kind.Position,
            "scale" => TriggeredMotion.Kind.Scale,
            _ => TriggeredMotion.Kind.Rotation,
        };
        var fallback = motion.kind == TriggeredMotion.Kind.Scale ? Vector3.one : Vector3.zero;
        motion.rest = ToVector(data.rest, fallback);
        motion.active = ToVector(data.active, fallback);
        motion.startDelay = data.startDelay;
        motion.inTime = data.inTime;
        motion.holdTime = data.holdTime;
        motion.outTime = data.outTime;
        motion.cooldown = data.cooldown;
        motion.arm = data.arm;
        return pivot.transform;
    }

    private static AnimationCurve ToCurve(AnimData anim)
    {
        var keys = new List<Keyframe>();
        if (anim.curve is { Length: > 0 })
        {
            foreach (var k in anim.curve)
                keys.Add(k.Length >= 4 ? new Keyframe(k[0], k[1], k[2], k[3]) : new Keyframe(k[0], k[1]));
        }
        else
        {
            keys.Add(new Keyframe(0f, 0f, 1f, 1f));
            keys.Add(new Keyframe(1f, 1f, 1f, 1f));
        }
        var curve = new AnimationCurve(keys.ToArray());
        var wrap = anim.wrap == "pingpong" ? WrapMode.PingPong : WrapMode.Loop;
        curve.preWrapMode = wrap;
        curve.postWrapMode = wrap;
        return curve;
    }

    private static void AddMesh(GameObject go, MeshData data, Material fallback)
    {
        var mesh = new Mesh { name = go.name };
        int vertexCount = data.vertices.Length / 3;
        if (vertexCount > 65000)
            mesh.indexFormat = IndexFormat.UInt32;
        var vertices = new List<Vector3>(vertexCount);
        var normals = new List<Vector3>(vertexCount);
        for (int i = 0; i < vertexCount; i++)
        {
            vertices.Add(new Vector3(data.vertices[i * 3], data.vertices[i * 3 + 1], data.vertices[i * 3 + 2]));
            if (data.normals != null && data.normals.Length >= (i + 1) * 3)
                normals.Add(new Vector3(data.normals[i * 3], data.normals[i * 3 + 1], data.normals[i * 3 + 2]));
        }
        mesh.SetVertices(vertices);
        if (normals.Count == vertexCount)
            mesh.SetNormals(normals);

        mesh.subMeshCount = data.submeshes.Count;
        var materials = new Material[data.submeshes.Count];
        for (int s = 0; s < data.submeshes.Count; s++)
        {
            mesh.SetTriangles(new List<int>(data.submeshes[s].triangles), s);
            materials[s] = MaterialLibrary.Resolve(data.submeshes[s].material, fallback);
        }
        if (normals.Count != vertexCount)
            mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        go.AddComponent<MeshFilter>().sharedMesh = mesh;
        var renderer = go.AddComponent<MeshRenderer>();
        if (materials.Length == 1)
            renderer.sharedMaterial = materials[0];
        else
            renderer.materials = materials;   // the stripped build has no sharedMaterials setter
    }

    private static Collider AddCollider(GameObject go, ColliderData data)
    {
        Collider collider;
        if (data.type == "sphere")
        {
            var sphere = go.AddComponent<SphereCollider>();
            sphere.center = ToVector(data.center, Vector3.zero);
            sphere.radius = data.radius;
            collider = sphere;
        }
        else
        {
            var box = go.AddComponent<BoxCollider>();
            box.center = ToVector(data.center, Vector3.zero);
            box.size = ToVector(data.size, Vector3.one);
            collider = box;
        }
        collider.isTrigger = data.trigger;
        return collider;
    }

    private static void AddZone(GameObject go, Collider collider, ZoneData zone, Obstacle obstacle)
    {
        switch (zone.type)
        {
            case "kill":
                var kill = go.AddComponent<KillZone>();
                kill.parent = obstacle;
                if (zone.minSpeed > 0f)
                {
                    kill.alignedVelocityToKill = zone.minSpeed;
                    kill.alignedVelocityNormalType = zone.axis switch
                    {
                        "right" => KillZone.KillZoneNormalType.Right,
                        "forward" => KillZone.KillZoneNormalType.Forward,
                        _ => KillZone.KillZoneNormalType.Up,
                    };
                }
                break;
            case "bounce":
                var bounce = go.AddComponent<BounceZone>();
                bounce.bounceFactor = zone.factor;
                switch (zone.mode)
                {
                    case "collision":
                        bounce.useCollisionNormal = true;
                        break;
                    case "custom":
                        bounce.useCustomNormal = true;
                        bounce.customNormal = ToVector(zone.normal, Vector3.up).normalized;
                        bounce.counterNegativeVelocity = true;
                        break;
                    case "velocity":
                        bounce.useCustomNormal = true;
                        bounce.customNormal = ToVector(zone.velocity, Vector3.up).normalized;
                        bounce.useCustomVelocity = true;
                        bounce.customBounceVelocity = ToVector(zone.velocity, Vector3.up);
                        bounce.counterNegativeVelocity = true;
                        break;
                }
                break;
            case "accel":
                var accel = go.AddComponent<AccelerationZone>();
                accel.trigger = collider as BoxCollider;
                accel.acceleration = zone.acceleration;
                accel.velocityOnEnter = zone.velocityOnEnter;
                accel.setVelocityOnEnter = zone.setVelocity;
                if (!accel.trigger)
                    Plugin.Log.LogWarning($"DataObstacle: accel zone on {go.name} needs a box collider");
                break;
            case "slow":
                var slow = go.AddComponent<SlowDownZone>();
                slow.slowDownFactor = zone.slowFactor;
                slow.stopCompletelyOnEnter = zone.stop;
                break;
            case "push":
                var push = go.AddComponent<PushZone>();
                push.speed = zone.pushSpeed;
                push.up = zone.pushUp;
                break;
            case "launch":
                var launch = go.AddComponent<LaunchZone>();
                launch.localVelocity = ToVector(zone.velocity, new Vector3(0f, 20f, 0f));
                launch.setVelocity = zone.setVelocity;
                launch.delay = zone.delay;
                launch.cooldown = zone.cooldown;
                launch.channel = zone.channel;
                break;
            case "plate":
                var plate = go.AddComponent<TriggerPlate>();
                plate.channel = zone.channel;
                plate.cooldown = zone.cooldown;
                break;
            case "toilet":
                var toilet = go.AddComponent<ToiletZone>();
                toilet.delay = zone.delay;
                toilet.channel = zone.channel;
                break;
            case "gravity":
                var gravity = go.AddComponent<LowGravityShape>();
                gravity.area = collider as BoxCollider;
                gravity.factor = zone.gravityFactor;
                break;
            case "spawn":
                var spawn = go.AddComponent<SpawnZone>();
                spawn.cooldown = zone.cooldown;
                spawn.channel = zone.channel;
                break;
            case "slingshot":
                var sling = go.AddComponent<SlingshotZone>();
                sling.leftAnchor = ToVector(zone.anchorLeft, sling.leftAnchor);
                sling.rightAnchor = ToVector(zone.anchorRight, sling.rightAnchor);
                sling.halfWidth = zone.halfWidth;
                sling.maxStretch = zone.maxStretch;
                sling.spring = zone.spring;
                sling.launchBase = zone.launchBase;
                sling.launchPerMetre = zone.launchPerMetre;
                sling.launchUp = zone.launchUp;
                sling.rubberMaterial = MaterialLibrary.Resolve(zone.rubber, null);
                sling.pouchMaterial = MaterialLibrary.Resolve(zone.pouch, null);
                break;
            case "grow":
                var grow = go.AddComponent<GrowZone>();
                grow.scale = zone.growScale;
                grow.duration = zone.duration;
                break;
            default:
                Plugin.Log.LogWarning($"DataObstacle: unknown zone type '{zone.type}' on {go.name}");
                break;
        }
    }

    private static Vector3 ToVector(float[] v, Vector3 fallback) =>
        v is { Length: >= 3 } ? new Vector3(v[0], v[1], v[2]) : fallback;

    private static Quaternion ToQuaternion(float[] q) =>
        q is { Length: >= 4 } ? new Quaternion(q[0], q[1], q[2], q[3]) : Quaternion.identity;
}
