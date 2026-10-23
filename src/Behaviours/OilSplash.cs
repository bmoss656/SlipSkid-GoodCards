using System.Collections.Generic;
using Obstacles;
using Player;
using UnityEngine;

namespace SlipSkid.CustomContent;

// Oil droplets kicked up by any car driving through the Baby Oil slick: a steady spray behind the car while
// it moves, and a bigger crown splash when it hits the slick fast. Purely visual, so it runs for every car
// on every machine. A car that leaves for over a quarter second counts as new when it comes back.
// Speeds come from each car's movement between frames (a remote car's rigidbody doesn't
// carry its real velocity). Droplets are pooled primitives without colliders.
internal sealed class OilSplash : MonoBehaviour
{
    public float surfaceHeight = 0.06f;   // slick top above the obstacle's origin
    public Material oil;
    public Material shine;

    private const int PoolSize = 90;
    private const float Gravity = 26f;

    private sealed class Drop
    {
        public Transform transform;
        public Renderer renderer;
        public Vector3 velocity;
        public float size;
        public float born, life;
        public bool alive;
    }

    private sealed class Tracked
    {
        public Vector3 lastPosition;
        public float lastSeen;
        public bool splashed;   // the entry splash has played (or the car came in too slowly for one)
        public float emitDebt;
        public bool hasPosition;
    }

    private Obstacle _obstacle;
    private readonly List<Drop> _pool = new();
    private int _next;
    private readonly Dictionary<SphereCarController, Tracked> _cars = new();
    private readonly List<SphereCarController> _gone = new();

    private void Start() => _obstacle = GetComponentInParent<Obstacle>();

    // Droplets live at the scene root (the obstacle's own scale would distort them), so clean them up here.
    private void OnDestroy()
    {
        foreach (var drop in _pool)
        {
            if (drop.transform)
                Destroy(drop.transform.gameObject);
        }
    }

    private void OnTriggerStay(Collider other)
    {
        if (!CarLookup.IsPlaced(_obstacle) || !CarLookup.TryGetAnyCar(other, out var car) || !car.sphereRigidbody)
            return;
        if (!_cars.TryGetValue(car, out var tracked))
            _cars[car] = tracked = new Tracked();
        tracked.lastSeen = Time.time;
    }

    private void Update()
    {
        float now = Time.time;
        _gone.Clear();
        foreach (var pair in _cars)
        {
            var car = pair.Key;
            var tracked = pair.Value;
            if (!car || now - tracked.lastSeen > 0.25f)
            {
                _gone.Add(car);
                continue;
            }
            Vector3 position = car.sphereRigidbody.position;
            if (!tracked.hasPosition || Time.deltaTime <= 0f)
            {
                tracked.lastPosition = position;
                tracked.hasPosition = true;
                continue;
            }
            Vector3 velocity = (position - tracked.lastPosition) / Time.deltaTime;
            tracked.lastPosition = position;
            Vector3 ground = Vector3.ProjectOnPlane(velocity, Vector3.up);
            float speed = ground.magnitude;
            float slickY = (_obstacle ? _obstacle.transform.position.y : transform.position.y) + surfaceHeight;
            // Only while the car is actually down on the slick.
            if (position.y - slickY > car.SphereRadius + 0.9f)
                continue;
            Vector3 contact = new(position.x, slickY, position.z);
            if (!tracked.splashed)
            {
                tracked.splashed = true;
                if (speed > 10f)
                    Crown(contact, speed);
            }
            if (speed < 3f)
                continue;

            Vector3 back = speed > 0.01f ? -ground / speed : Vector3.zero;
            Vector3 side = Vector3.Cross(Vector3.up, back);
            // A steady spray off the back wheels, more the faster it goes.
            tracked.emitDebt += Mathf.Min(40f, speed * 1.4f) * Time.deltaTime;
            while (tracked.emitDebt >= 1f)
            {
                tracked.emitDebt -= 1f;
                float wheel = Random.value < 0.5f ? -1f : 1f;
                Vector3 from = contact + back * 1.1f + side * (wheel * Random.Range(0.6f, 1.0f));
                Vector3 v = back * (speed * Random.Range(0.15f, 0.35f)) + side * (wheel * Random.Range(0.5f, 2.5f))
                            + Vector3.up * Random.Range(2.5f, 4.5f + speed * 0.12f);
                Emit(from, v, Random.Range(0.12f, 0.26f), Random.Range(0.45f, 0.8f));
            }
        }
        foreach (var car in _gone)
            _cars.Remove(car);
        Animate(now);
    }

    // A ring of droplets thrown up and out around the impact point.
    private void Crown(Vector3 at, float speed)
    {
        int count = 18;
        float up = Mathf.Clamp(speed * 0.3f, 5f, 11f);
        for (int i = 0; i < count; i++)
        {
            float a = i * (float)(2 * System.Math.PI / count) + Random.Range(-0.15f, 0.15f);
            var outward = new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a));
            Emit(at + outward * 1.2f, outward * Random.Range(2.5f, 5f) + Vector3.up * Random.Range(up * 0.7f, up),
                Random.Range(0.18f, 0.38f), Random.Range(0.6f, 0.95f));
        }
    }

    private void Emit(Vector3 position, Vector3 velocity, float size, float life)
    {
        Drop drop;
        if (_pool.Count < PoolSize)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            Destroy(go.GetComponent<Collider>());
            go.name = "GoodCards_OilDrop";
            drop = new Drop { transform = go.transform, renderer = go.GetComponent<MeshRenderer>() };
            _pool.Add(drop);
        }
        else
        {
            drop = _pool[_next];
            _next = (_next + 1) % PoolSize;
        }
        // One in five catches the light.
        var material = Random.value < 0.2f && shine ? shine : oil;
        if (material)
            drop.renderer.sharedMaterial = material;
        drop.transform.position = position;
        drop.velocity = velocity;
        drop.size = size;
        drop.born = Time.time;
        drop.life = life;
        drop.alive = true;
        drop.transform.gameObject.SetActive(true);
    }

    private void Animate(float now)
    {
        float dt = Time.deltaTime;
        foreach (var drop in _pool)
        {
            if (!drop.alive)
                continue;
            float t = (now - drop.born) / drop.life;
            if (t >= 1f || !drop.transform)
            {
                drop.alive = false;
                if (drop.transform)
                    drop.transform.gameObject.SetActive(false);
                continue;
            }
            drop.velocity += Vector3.down * (Gravity * dt);
            drop.transform.position += drop.velocity * dt;
            // Stretched along its flight, shrinking away at the end.
            float s = drop.size * (t < 0.75f ? 1f : 1f - (t - 0.75f) / 0.25f);
            float stretch = 1f + Mathf.Min(1.5f, drop.velocity.magnitude * 0.06f);
            drop.transform.rotation = drop.velocity.sqrMagnitude > 0.01f ? Quaternion.LookRotation(drop.velocity) : Quaternion.identity;
            drop.transform.localScale = new Vector3(s, s, s * stretch);
        }
    }
}
