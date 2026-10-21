using Obstacles;
using UnityEngine;

namespace SlipSkid.CustomContent;

// A one-shot move played when its TriggerBus channel fires: rest -> active (inTime), hold, back to rest
// (outTime). Colliders under it can be "armed": enabled only while it's out, so a trap only hurts mid-snap.
internal sealed class TriggeredMotion : MonoBehaviour
{
    public enum Kind { Rotation, Position, Scale }

    public int channel;
    public Kind kind;
    public Vector3 rest;
    public Vector3 active;
    public float startDelay;
    public float inTime = 0.15f;
    public float holdTime = 1f;
    public float outTime = 0.8f;
    public float cooldown = 0.5f;
    public bool arm;

    private Obstacle _obstacle;
    private Collider[] _armed = new Collider[0];
    private float _triggeredAt = -1000f;

    private float Duration => startDelay + inTime + holdTime + outTime;

    private void Start()
    {
        _obstacle = GetComponentInParent<Obstacle>();
        if (arm)
            _armed = GetComponentsInChildren<Collider>(true);
        Apply(0f);
    }

    internal void Trigger()
    {
        if (Time.time - _triggeredAt < Duration + cooldown)
            return;
        _triggeredAt = Time.time;
    }

    private void Update()
    {
        float t = Time.time - _triggeredAt - startDelay;
        float amount = 0f;
        if (t >= 0f)
        {
            if (t < inTime) amount = Smooth(t / inTime);
            else if (t < inTime + holdTime) amount = 1f;
            else if (t < inTime + holdTime + outTime) amount = 1f - Smooth((t - inTime - holdTime) / outTime);
        }
        Apply(amount);
    }

    // The stripped build has no Mathf.SmoothStep.
    private static float Smooth(float t)
    {
        t = Mathf.Clamp01(t);
        return t * t * (3f - 2f * t);
    }

    // LateUpdate so the game's own collider toggling (placement) never leaves a trap armed at rest.
    private void LateUpdate()
    {
        if (!arm)
            return;
        float t = Time.time - _triggeredAt - startDelay;
        bool live = t >= 0f && t < inTime + holdTime && CarLookup.IsPlaced(_obstacle);
        foreach (var collider in _armed)
        {
            if (collider)
                collider.enabled = live;
        }
    }

    private void Apply(float amount)
    {
        Vector3 value = Vector3.LerpUnclamped(rest, active, amount);
        switch (kind)
        {
            case Kind.Rotation: transform.localRotation = Quaternion.Euler(value); break;
            case Kind.Position: transform.localPosition = value; break;
            case Kind.Scale: transform.localScale = value; break;
        }
    }
}
