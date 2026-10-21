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
