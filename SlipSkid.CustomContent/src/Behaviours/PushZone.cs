using System.Collections.Generic;
using Obstacles;
using Player;
using UnityEngine;

namespace SlipSkid.CustomContent;

// Solid collider that throws the owner's car straight away from it at a fixed speed. Vanilla BounceZone
// reflects the car's velocity, but by OnCollisionEnter the contact has already stopped the car, so a
// factor-1 bounce barely moves it; vanilla's Egg gets around that with a fixed velocity, and so do we.
internal sealed class PushZone : MonoBehaviour
{
    public float speed = 18f;
    public float up = 5f;
    public float cooldown = 0.4f;

    private Obstacle _obstacle;
    private readonly Dictionary<SphereCarController, float> _last = new();

    private void Start() => _obstacle = GetComponentInParent<Obstacle>();

    private void OnCollisionEnter(Collision collision)
    {
        if (!CarLookup.IsPlaced(_obstacle) || !CarLookup.TryGetOwnedCar(collision.collider, out _, out var car))
            return;
        if (_last.TryGetValue(car, out float last) && Time.time - last < cooldown)
            return;
        _last[car] = Time.time;

        var body = car.sphereRigidbody;
        Vector3 away = Vector3.ProjectOnPlane(body.position - transform.position, Vector3.up);
        if (away.sqrMagnitude < 0.01f)
            away = -Vector3.ProjectOnPlane(body.velocity, Vector3.up);
        if (away.sqrMagnitude < 0.01f)
            away = transform.forward;
        body.velocity = away.normalized * speed + Vector3.up * up;
    }
}
