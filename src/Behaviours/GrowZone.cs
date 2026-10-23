using System.Collections.Generic;
using HarmonyLib;
using Obstacles;
using Player;
using UnityEngine;

namespace SlipSkid.CustomContent;

// Makes any car that drives through it huge for a while, using the game's own CarModifier system
// (the one the Shrink Ray and surfaces use). Runs for every car on every machine, so everyone sees it.
internal sealed class GrowZone : MonoBehaviour
{
    public float duration = 8f;
    public float scale = 2.2f;

    private Obstacle _obstacle;
    private CarModifier _modifier;

    private void Start()
    {
        _obstacle = GetComponentInParent<Obstacle>();
        _modifier = ScriptableObject.CreateInstance<CarModifier>();
        _modifier.id = "CUSTOMCONTENT_MAGNIFIED";
        _modifier.durationSeconds = duration;
        _modifier.isUniquePerApplier = true;
        // ApplyModifiers resets the car every frame, then multiplies by curve(t) * scale; the curve eases
        // from roughly normal size up to full size and back.
        float rest = 1f / scale;
        var curve = new AnimationCurve(new Keyframe(0f, rest), new Keyframe(0.08f, 1f), new Keyframe(0.88f, 1f), new Keyframe(1f, rest));
        _modifier.scale = new CarModifier.ModifierValue<Vector3>(CarModifier.ModifierValueType.Multiplicative, curve, Vector3.one * scale);
    }

    private void OnTriggerEnter(Collider other)
    {
        if (!_modifier || !CarLookup.IsPlaced(_obstacle) || !CarLookup.TryGetAnyCar(other, out var car))
            return;
        _modifier.Register(car, this);
    }

    private void OnDestroy()
    {
        if (_modifier)
            Destroy(_modifier);
    }
}

// CarModifier scale grows every child of the car, physics sphere included, but the ground check
// (SphereCarController.Simulate) is a raycast of fixed length from the sphere's centre. A huge car's
// raycast no longer reaches the road, so it counts as airborne: no grip, no steering ("slippery").
// Simulate calls ApplyModifiers just before that raycast, so stretch the raycast with the car here.
// Shrinking (the vanilla Shrink Ray) is left alone.
// The change is relative (undo last frame's factor, apply this frame's), so permanent edits by other mods
// survive: MoreCards' Supersize multiplies floorRaycastDistance once for the same reason.
[HarmonyPatch(typeof(SphereCarController), nameof(SphereCarController.ApplyModifiers))]
internal static class GrowGroundCheckPatch
{
    private static readonly Dictionary<SphereCarController, float> Applied = new();

    // Runs every physics step for every car: plain try/catch, no closure allocation.
    private static void Postfix(SphereCarController __instance)
    {
        try
        {
            Stretch(__instance);
        }
        catch (System.Exception e)
        {
            Guard.Report("Grow", e);
        }
    }

    private static void Stretch(SphereCarController car)
    {
        // scaleModifier is the largest axis of this frame's modifier scale (0 when none is active).
        float factor = car.scaleModifier > 1f ? car.scaleModifier : 1f;
        float previous = Applied.TryGetValue(car, out float p) ? p : 1f;
        if (System.Math.Abs(factor - previous) < 0.0001f)
            return;
        car.floorRaycastDistance = car.floorRaycastDistance / previous * factor;
        if (factor == 1f)
            Applied.Remove(car);
        else
            Applied[car] = factor;
    }
}
