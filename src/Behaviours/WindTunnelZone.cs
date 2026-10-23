using System.Collections.Generic;
using Obstacles;
using Player;
using UnityEngine;

namespace SlipSkid.CustomContent;

// The Wind Tunnel: wind blows against `localDirection` (the way through, in this node's space). A car moving
// through at `passSpeed` or faster cuts straight through; anything slower is blown back out. Owner only.
internal sealed class WindTunnelZone : MonoBehaviour
{
    public Vector3 localDirection = Vector3.forward;
    public float wind = 45f;        // m/s² against the way through
    public float passSpeed = 30f;   // m/s along the way through

    private Obstacle _obstacle;
    private readonly Dictionary<SphereCarController, float> _lastStep = new();

    private void Start() => _obstacle = GetComponentInParent<Obstacle>();

    private void OnTriggerStay(Collider other)
    {
        if (!CarLookup.IsPlaced(_obstacle) || !CarLookup.TryGetOwnedCar(other, out _, out var car))
            return;
        // Each of the car's colliders reports its own stay: push once per physics step.
        if (_lastStep.TryGetValue(car, out float step) && step == Time.time)
            return;
        _lastStep[car] = Time.time;

        var body = car.sphereRigidbody;
        Vector3 through = transform.TransformDirection(localDirection).normalized;
        if (Vector3.Dot(body.velocity, through) >= passSpeed)
            return;
        body.AddForce(-through * wind, ForceMode.Acceleration);
    }
}
