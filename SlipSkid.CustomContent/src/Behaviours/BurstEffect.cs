using System.Collections;
using System.Collections.Generic;
using Obstacles;
using Unity.Netcode;
using UnityEngine;

namespace SlipSkid.CustomContent;

// Plays a one-off visual when its TriggerBus channel fires (so every machine sees it), and optionally
// uses the obstacle up: it vanishes at once everywhere and the host despawns it a moment later.
// The visual is a standalone object, so it keeps playing after the obstacle is gone.
internal sealed class BurstEffect : MonoBehaviour
{
    public enum Kind { Shock, Teleport }

    public int channel;
    public Kind kind;
    public bool consume;

    private Obstacle _obstacle;
    private bool _used;

    private void Start() => _obstacle = GetComponentInParent<Obstacle>();

    // `target` is extra position data from the trigger (the Teleport Grenade sends where the car reappeared).
    internal void Play(Vector3 target)
    {
        if (_used)
            return;
        Vector3 origin = transform.position;
        if (kind == Kind.Shock)
            EffectBurst.Shock(origin);
        else
        {
            EffectBurst.Implode(origin);
            if (target.sqrMagnitude > 0.01f)
                EffectBurst.Appear(target);
        }
        if (consume)
            UseUp();
    }

    private void UseUp()
    {
        _used = true;
        if (!_obstacle)
            return;
        foreach (var renderer in _obstacle.GetComponentsInChildren<Renderer>(true))
            renderer.enabled = false;
        foreach (var collider in _obstacle.GetComponentsInChildren<Collider>(true))
            collider.enabled = false;
        if (NetworkManager.Singleton && NetworkManager.Singleton.IsServer)
            _obstacle.StartCoroutine(DespawnSoon(_obstacle));
    }

    private static IEnumerator DespawnSoon(Obstacle obstacle)
    {
        yield return new WaitForSeconds(0.2f);
        ObstacleManager.Delete(obstacle);
    }
}

// Procedural effect animation built from primitives with glowing materials; destroys itself when done.
internal sealed class EffectBurst : MonoBehaviour
{
    private sealed class Part
    {
        public Transform transform;
        public System.Func<float, Vector3> scale;   // scale over normalised time
        public float spin;
    }

    private readonly List<Part> _parts = new();
    private readonly List<Transform> _bolts = new();
    private float _born, _life, _nextFlicker;
    private System.Random _rnd;

    internal static void Shock(Vector3 position)
    {
        var fx = Create("CustomContent_ShockFx", position, 0.55f);
        var cyan = MaterialLibrary.Resolve("glow:#4FD3FF", null);
        var white = MaterialLibrary.Resolve("glow:#E8FBFF", null);
        // Flash, then a ground shockwave and crackling bolts.
        fx.Add(PrimitiveType.Sphere, white, Vector3.up * 0.6f, t => Vector3.one * (t < 0.3f ? Mathf.Lerp(0.4f, 5f, t / 0.3f) : Mathf.Lerp(5f, 0f, (t - 0.3f) / 0.7f)));
        fx.Add(PrimitiveType.Cylinder, cyan, Vector3.up * 0.15f, t => new Vector3(Mathf.Lerp(1f, 12f, t), Mathf.Lerp(0.15f, 0.01f, t), Mathf.Lerp(1f, 12f, t)));
        fx.Add(PrimitiveType.Cylinder, cyan, Vector3.up * 3f, t => new Vector3(Mathf.Lerp(1.2f, 0f, t), Mathf.Lerp(3f, 6f, t), Mathf.Lerp(1.2f, 0f, t)));
        for (int i = 0; i < 8; i++)
            fx._bolts.Add(fx.Add(PrimitiveType.Cube, i % 2 == 0 ? cyan : white, Vector3.up * 0.8f, t => new Vector3(0.12f, 0.12f, 3.5f * (1f - t))).transform);
    }

    internal static void Implode(Vector3 position)
    {
        var fx = Create("CustomContent_TeleportFx", position, 0.6f);
        var purple = MaterialLibrary.Resolve("glow:#A64DFF", null);
        var pink = MaterialLibrary.Resolve("glow:#F0B8FF", null);
        fx.Add(PrimitiveType.Sphere, pink, Vector3.up * 0.8f, t => Vector3.one * Mathf.Lerp(3.2f, 0f, t * t));
        for (int i = 0; i < 3; i++)
        {
            float delay = i * 0.12f;
            var ring = fx.Add(PrimitiveType.Cylinder, purple, Vector3.up * (0.4f + i * 0.6f),
                t => { float k = Mathf.Clamp01((t - delay) / (1f - delay)); return new Vector3(Mathf.Lerp(5f, 0f, k), 0.04f, Mathf.Lerp(5f, 0f, k)); });
            ring.spin = 540f * (i % 2 == 0 ? 1f : -1f);
        }
    }

    internal static void Appear(Vector3 position)
    {
        var fx = Create("CustomContent_AppearFx", position, 0.7f);
        var purple = MaterialLibrary.Resolve("glow:#A64DFF", null);
        var pink = MaterialLibrary.Resolve("glow:#F0B8FF", null);
        fx.Add(PrimitiveType.Cylinder, purple, Vector3.up * 4f, t => new Vector3(Mathf.Lerp(2.4f, 0f, t), t < 0.2f ? Mathf.Lerp(0f, 4f, t / 0.2f) : 4f, Mathf.Lerp(2.4f, 0f, t)));
        fx.Add(PrimitiveType.Sphere, pink, Vector3.up * 1f, t => Vector3.one * (t < 0.25f ? Mathf.Lerp(0f, 3.5f, t / 0.25f) : Mathf.Lerp(3.5f, 0f, (t - 0.25f) / 0.75f)));
    }

    private static EffectBurst Create(string name, Vector3 position, float life)
    {
        var go = new GameObject(name);
        go.transform.position = position;
        var fx = go.AddComponent<EffectBurst>();
        fx._born = Time.time;
        fx._life = life;
        fx._rnd = new System.Random(name.GetHashCode() ^ (int)(position.x * 31f + position.z * 17f));
        return fx;
    }

    private Part Add(PrimitiveType type, Material material, Vector3 offset, System.Func<float, Vector3> scale)
    {
        var part = GameObject.CreatePrimitive(type);
        Destroy(part.GetComponent<Collider>());
        part.transform.SetParent(transform, false);
        part.transform.localPosition = offset;
        if (material)
            part.GetComponent<MeshRenderer>().sharedMaterial = material;
        var entry = new Part { transform = part.transform, scale = scale };
        _parts.Add(entry);
        entry.transform.localScale = scale(0f);
        return entry;
    }

    private void Update()
    {
        float t = (Time.time - _born) / _life;
        if (t >= 1f)
        {
            Destroy(gameObject);
            return;
        }
        foreach (var part in _parts)
        {
            part.transform.localScale = part.scale(t);
            if (part.spin != 0f)
                part.transform.Rotate(Vector3.up, part.spin * Time.deltaTime, Space.Self);
        }
        // Lightning crackle: each bolt jumps to a new random direction every few frames.
        if (_bolts.Count > 0 && Time.time >= _nextFlicker)
        {
            _nextFlicker = Time.time + 0.045f;
            foreach (var bolt in _bolts)
            {
                var dir = new Vector3((float)_rnd.NextDouble() - 0.5f, (float)_rnd.NextDouble() * 0.6f, (float)_rnd.NextDouble() - 0.5f).normalized;
                bolt.localRotation = Quaternion.LookRotation(dir);
                bolt.localPosition = Vector3.up * 0.8f + dir * 1.6f * (1f - t);
            }
        }
    }
}
