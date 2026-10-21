using Obstacles;
using UnityEngine;
using Utils;

namespace SlipSkid.CustomContent;

// Enables the colliders under it only during a window of a repeating cycle, timed off the same network
// clock as the vanilla animators, so a geyser erupts at the same moment on every screen.
internal sealed class TimedActive : MonoBehaviour
{
    public float speed = 0.2f;   // cycles per second
    public float start;          // window start, 0..1 of the cycle
    public float end = 0.5f;     // window end

    private Obstacle _obstacle;
    private Collider[] _colliders = new Collider[0];

    private void Start()
    {
        _obstacle = GetComponentInParent<Obstacle>();
        _colliders = GetComponentsInChildren<Collider>(true);
    }

    private void LateUpdate()
    {
        double time = TimeUtils.LocalTimeSec * speed * NetworkAnimatedParameter.GlobalSpeedFactor;
        float phase = (float)(time - System.Math.Floor(time));
        bool live = phase >= start && phase < end && CarLookup.IsPlaced(_obstacle);
        foreach (var collider in _colliders)
        {
            if (collider)
                collider.enabled = live;
        }
    }
}

// The sliding mover vanilla lacks: same network-clock maths as NetworkAnimatedRotation, but moves localPosition.
internal sealed class NetworkAnimatedPosition : NetworkAnimatedTransformation
{
    public override void UpdateValues() => target.localPosition = new Vector3(x.value, y.value, z.value);

    public override void DoPreview()
    {
    }
}
