using System.Collections.Generic;
using Obstacles;
using Player;
using UnityEngine;

namespace SlipSkid.CustomContent;

// The Speed Bump: harmless at low speed; crossing it at `minSpeed` or faster launches the car (keeps
// `keep` of its ground speed, plus `up` straight up). Owner only; `channel` flashes the speed camera.
internal sealed class SpeedBumpZone : MonoBehaviour
{
    public float minSpeed = 20f;
    public float up = 22f;
    public float keep = 0.9f;
    public float cooldown = 1f;
    public int channel = -1;

    private Obstacle _obstacle;
    private readonly Dictionary<SphereCarController, float> _last = new();

    private void Start() => _obstacle = GetComponentInParent<Obstacle>();

    private void OnTriggerEnter(Collider other)
    {
        if (!CarLookup.IsPlaced(_obstacle) || !CarLookup.TryGetOwnedCar(other, out _, out var car))
            return;
        if (_last.TryGetValue(car, out float last) && Time.time - last < cooldown)
            return;
        var body = car.sphereRigidbody;
        Vector3 ground = Vector3.ProjectOnPlane(body.velocity, Vector3.up);
        if (ground.magnitude < minSpeed)
            return;
        _last[car] = Time.time;
        body.velocity = ground * keep + Vector3.up * up;
        if (channel >= 0 && _obstacle)
            TriggerBus.Fire(_obstacle, channel);
    }
}
