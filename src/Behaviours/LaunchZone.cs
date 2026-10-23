using System.Collections;
using System.Collections.Generic;
using Obstacles;
using Player;
using UnityEngine;

namespace SlipSkid.CustomContent;

// Trigger that throws the owner's car along `localVelocity` (this transform's space, so it turns with
// the obstacle), optionally after a delay. Unlike BounceZone it needs no solid contact.
internal sealed class LaunchZone : MonoBehaviour
{
    public Vector3 localVelocity = new(0f, 20f, 0f);
    public bool setVelocity = true;
    public float delay;
    public float cooldown = 1f;
    public int channel = -1;   // TriggerBus channel to fire when it launches (e.g. the toast popping)

    private Obstacle _obstacle;
    private readonly Dictionary<SphereCarController, float> _lastLaunch = new();

    private bool _singleUse;

    private void Start()
    {
        _obstacle = GetComponentInParent<Obstacle>();
        _singleUse = BurstEffect.ConsumesOn(_obstacle, channel);
    }

    private void OnTriggerEnter(Collider other)
    {
        if (!CarLookup.IsPlaced(_obstacle) || !CarLookup.TryGetOwnedCar(other, out _, out var car))
            return;
        if (_singleUse && !CarLookup.IsRacing())
            return;
        if (_lastLaunch.TryGetValue(car, out float last) && Time.time - last < cooldown)
            return;
        _lastLaunch[car] = Time.time;
        if (delay > 0.01f)
            StartCoroutine(LaunchLater(car));
        else
            Launch(car);
    }

    private IEnumerator LaunchLater(SphereCarController car)
    {
        yield return new WaitForSeconds(delay);
        if (car)
            Launch(car);
    }

    private void Launch(SphereCarController car)
    {
        var body = car.sphereRigidbody;
        Vector3 velocity = transform.TransformDirection(localVelocity);
        if (setVelocity)
            body.velocity = velocity;
        else
            body.AddForce(velocity, ForceMode.VelocityChange);
        if (channel >= 0 && _obstacle)
            TriggerBus.Fire(_obstacle, channel);
    }
}
