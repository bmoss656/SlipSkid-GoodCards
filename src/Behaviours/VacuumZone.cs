using System.Collections;
using System.Collections.Generic;
using Obstacles;
using Player;
using UnityEngine;

namespace SlipSkid.CustomContent;

// The Vacuum: a suction trigger reaching from the road in front of the nozzle into the chamber inside it.
// `mouth` is the middle of that chamber. It works like a tractor beam: cars are dragged towards it at a set
// speed (pullSpeedFar at the edge of the field, rising to pullSpeed close in), never accelerated harder than
// `pull`, and much less while they're still outside and driving away, so they can escape. A car that gets
// all the way in (within catchDistance of the chamber's middle) is caught, rattles inside for a moment, then
// is fired back out of the mouth along `localVelocity`. Runs on the car owner's machine; `channel` plays the
// vacuum's shudder everywhere.
internal sealed class VacuumZone : MonoBehaviour
{
    public Vector3 mouth;                                    // this node's space
    public float pull = 22f;                                 // most the suction can accelerate a car, m/s²
    public float pullSpeedFar = 4f;                          // m/s towards the mouth at `reach`
    public float pullSpeed = 12f;                            // m/s towards the mouth right at it
    public float reach = 14f;                                // distance the pull speed ramps over
    public float catchDistance = 2.2f;
    public float escapeDistance = 2.4f;                      // closer than this to `mouth` there's no escape
    public float escapeFactor = 0.35f;                       // pull strength left for a car driving away
    public float holdTime = 0.9f;
    public Vector3 localVelocity = new(0f, 14f, -40f);       // this node's space
    public float cooldown = 2f;
    public int channel = -1;

    private Obstacle _obstacle;
    private SphereCarController _held;
    private readonly Dictionary<SphereCarController, float> _released = new();
    private readonly Dictionary<SphereCarController, float> _lastStep = new();

    private void Start() => _obstacle = GetComponentInParent<Obstacle>();

    private void OnTriggerStay(Collider other)
    {
        if (!CarLookup.IsPlaced(_obstacle) || !CarLookup.TryGetOwnedCar(other, out _, out var car) || car == _held)
            return;
        // Each of the car's colliders reports its own stay: pull once per physics step.
        if (_lastStep.TryGetValue(car, out float step) && step == Time.time)
            return;
        _lastStep[car] = Time.time;
        if (_released.TryGetValue(car, out float released) && Time.time - released < cooldown)
            return;

        var body = car.sphereRigidbody;
        Vector3 target = transform.TransformPoint(mouth);
        // Drag along the ground: the mouth sits low, and pulling down into the road would only add grip.
        Vector3 toMouth = Vector3.ProjectOnPlane(target - body.position, Vector3.up);
        float distance = toMouth.magnitude;
        if (distance < catchDistance)
        {
            StartCoroutine(Catch(car));
            return;
        }
        Vector3 direction = toMouth / distance;
        float closeness = Mathf.Clamp01(1f - distance / Mathf.Max(0.1f, reach));
        float wanted = Mathf.Lerp(pullSpeedFar, pullSpeed, closeness * closeness);
        // Only top the car up to the wanted approach speed; a car already heading in faster is left alone.
        float current = Vector3.Dot(body.velocity, direction);
        float shortfall = wanted - current;
        if (shortfall <= 0f)
            return;
        float cap = pull;
        // Still outside the nozzle and driving away: the suction only weakly holds on, so you can break free.
        // Once past `escapeDistance` (inside the mouth) there's no getting out.
        if (distance > escapeDistance && current < -0.5f)
            cap *= escapeFactor;
        float accel = Mathf.Min(cap, shortfall * 6f);
        body.AddForce(direction * accel, ForceMode.Acceleration);
    }

    private IEnumerator Catch(SphereCarController car)
    {
        _held = car;
        if (channel >= 0 && _obstacle)
            TriggerBus.Fire(_obstacle, channel);
        Vector3 launch = transform.TransformDirection(localVelocity);
        Vector3 facing = Vector3.ProjectOnPlane(launch, Vector3.up);
        if (facing.sqrMagnitude < 0.01f)
            facing = -transform.forward;
        facing.Normalize();
        Vector3 holdPoint = transform.TransformPoint(mouth) + Vector3.up * 0.8f;
        // Turned to face the way it's about to be fired out.
        car.Teleport(holdPoint, Quaternion.LookRotation(facing), facing, Vector3.zero, Vector3.zero);
        float end = Time.time + holdTime;
        while (car && Time.time < end)
        {
            // Rattling in the nozzle.
            var shake = new Vector3(Random.Range(-1f, 1f), Random.Range(-0.5f, 0.5f), Random.Range(-1f, 1f)) * 0.12f;
            car.sphereRigidbody.position = holdPoint + shake;
            car.sphereRigidbody.velocity = Vector3.zero;
            yield return new WaitForFixedUpdate();
        }
        if (car)
        {
            car.sphereRigidbody.velocity = launch;
            _released[car] = Time.time;
            if (car.player)
                Plugin.Log.LogInfo($"Vacuum: spat out {car.player.DisplayNameRaw}");
        }
        _held = null;
    }
}
