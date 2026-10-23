using Game;
using Obstacles;
using UnityEngine;
using World;

namespace SlipSkid.CustomContent;

// The car's gravity is the sum of every GravityShape (SphereCarController asks GravityShapesManager each
// physics step, and jumps use it too). This shape adds an upward pull inside its box, cancelling `factor`
// of the map's GravityShapeInfinitePlane (40 m/s^2). Same on every machine, no networking needed.
internal sealed class LowGravityShape : GravityShape
{
    public BoxCollider area;
    public float factor = 0.7f;
    public float planeGravity = 40f;

    private Obstacle _obstacle;

    private void Start() => _obstacle = GetComponentInParent<Obstacle>();

    public override Vector3 GetGravityAtPoint(Vector3 position)
    {
        if (!area || !CarLookup.IsPlaced(_obstacle) || !area.bounds.Contains(position))
            return Vector3.zero;
        return Vector3.up * planeGravity * factor;
    }
}

// Trigger that sends the owner's car back to its start position (the Teleport Grenade).
internal sealed class SpawnZone : MonoBehaviour
{
    public float cooldown = 1.5f;
    public int channel = -1;   // fired after the teleport, with where the car reappeared (for the effect)

    private Obstacle _obstacle;
    private float _last = -100f;

    private void Start() => _obstacle = GetComponentInParent<Obstacle>();

    private void OnTriggerEnter(Collider other)
    {
        if (!CarLookup.IsPlaced(_obstacle) || Time.time - _last < cooldown || !CarLookup.TryGetOwnedCar(other, out _, out var car))
            return;
        if (!car.player || !GameManager.instance || !CarLookup.IsRacing())
            return;
        _last = Time.time;
        GameManager.instance.PlacePlayerAtSpawn(car.player);
        Plugin.Log.LogInfo($"Teleport: sent {car.player.DisplayNameRaw} back to the start");
        if (channel >= 0 && _obstacle)
            TriggerBus.Fire(_obstacle, channel, car.sphereRigidbody.position);
    }
}
