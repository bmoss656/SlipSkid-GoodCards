using System.Collections.Generic;
using Obstacles;
using Player;
using UnityEngine;

namespace SlipSkid.CustomContent;

// A rubber band across the gap between two prongs (this node's local X axis, at local z = 0).
// Drive through the band from either side, forwards or reversing: it catches the car and stretches with
// it, pulling back harder the further it goes. As soon as the car stops pushing on (stalls against the
// pull, or lets off), it's flung back out the side it came in, faster the further it was stretched.
// - The band is drawn on every machine from each car's synced position, so everyone sees the stretch.
// - The pull and the launch only run on the machine that owns the car, like every car effect.
internal sealed class SlingshotZone : MonoBehaviour
{
    public Vector3 leftAnchor = new(-2.2f, 0f, 0f);    // band ends, in this node's space
    public Vector3 rightAnchor = new(2.2f, 0f, 0f);
    public float halfWidth = 1.9f;      // only catches cars between the prongs
    public float maxStretch = 7f;       // metres
    public float spring = 9f;           // pull-back acceleration per metre of stretch
    public float damping = 1.5f;        // extra pull-back per m/s still pushing in
    public float launchBase = 14f;
    public float launchPerMetre = 5f;
    public float launchUp = 4f;
    public float cooldown = 1.2f;
    public Material rubberMaterial;
    public Material pouchMaterial;

    private sealed class Grab
    {
        public SphereCarController car;
        public Collider collider;
        public float sign;      // +1 travelling along local +Z, -1 along -Z
        public float stretch;
        public float maxStretch;
    }

    private Obstacle _obstacle;
    private readonly Dictionary<SphereCarController, float> _lastZ = new();
    private readonly Dictionary<SphereCarController, Grab> _grabs = new();
    private readonly Dictionary<SphereCarController, float> _cooldownUntil = new();
    private Transform _strandLeft, _strandRight, _pouch;
    private Vector3 _pouchLocal, _pouchVelocity;

    private Vector3 Rest => (leftAnchor + rightAnchor) * 0.5f;

    private void Start()
    {
        _obstacle = GetComponentInParent<Obstacle>();
        _strandLeft = MakePart("SlingStrandL", rubberMaterial);
        _strandRight = MakePart("SlingStrandR", rubberMaterial);
        _pouch = MakePart("SlingPouch", pouchMaterial);
        _pouch.localScale = new Vector3(1.0f, 1.1f, 0.45f);
        _pouchLocal = Rest;
        UpdateVisual();
    }

    private Transform MakePart(string partName, Material material)
    {
        var part = GameObject.CreatePrimitive(PrimitiveType.Cube);
        part.name = partName;
        Destroy(part.GetComponent<Collider>());
        part.layer = gameObject.layer;
        part.transform.SetParent(transform, false);
        if (material)
            part.GetComponent<MeshRenderer>().sharedMaterial = material;
        return part.transform;
    }

    // Every machine, every car: catch it when it crosses the band line between the prongs.
    private void OnTriggerStay(Collider other)
    {
        if (!CarLookup.IsPlaced(_obstacle) || !CarLookup.TryGetAnyCar(other, out var car) || _grabs.ContainsKey(car))
            return;
        Vector3 local = transform.InverseTransformPoint(other.bounds.center);
        bool hadLast = _lastZ.TryGetValue(car, out float lastZ);
        _lastZ[car] = local.z;
        if (!hadLast || Mathf.Abs(local.x) > halfWidth || Mathf.Sign(lastZ) == Mathf.Sign(local.z))
            return;
        if (_cooldownUntil.TryGetValue(car, out float until) && Time.time < until)
            return;
        _grabs[car] = new Grab { car = car, collider = other, sign = Mathf.Sign(local.z - lastZ) };
    }

    private void OnTriggerExit(Collider other)
    {
        if (!CarLookup.TryGetAnyCar(other, out var car))
            return;
        _lastZ.Remove(car);
        _grabs.Remove(car);
    }

    private void FixedUpdate()
    {
        List<SphereCarController> done = null;
        foreach (var grab in _grabs.Values)
        {
            if (!grab.car || !grab.collider)
            {
                (done ??= new()).Add(grab.car);
                continue;
            }
            Vector3 direction = transform.forward * grab.sign;
            Vector3 local = transform.InverseTransformPoint(grab.collider.bounds.center);
            grab.stretch = Vector3.Dot(grab.collider.bounds.center - transform.position, direction);
            grab.maxStretch = Mathf.Max(grab.maxStretch, grab.stretch);

            // Slipped out sideways, or backed out where it came from: let go without a launch.
            if (Mathf.Abs(local.x) > halfWidth + 1f || grab.stretch < -0.5f)
            {
                (done ??= new()).Add(grab.car);
                continue;
            }
            if (grab.car.player && grab.car.player.IsOwner && Pull(grab, direction))
                (done ??= new()).Add(grab.car);
        }
        if (done == null)
            return;
        foreach (var car in done)
        {
            _grabs.Remove(car);
            if (car)
                _cooldownUntil[car] = Time.time + cooldown;
        }
    }

    // Owner only. Returns true once the car has been flung.
    private bool Pull(Grab grab, Vector3 direction)
    {
        var body = grab.car.sphereRigidbody;
        float pushingIn = Vector3.Dot(body.velocity, direction);
        float stretch = Mathf.Max(0f, grab.stretch);
        body.AddForce(-direction * (spring * stretch + damping * Mathf.Max(0f, pushingIn)), ForceMode.Acceleration);
        if (stretch >= maxStretch && pushingIn > 0f)
            body.velocity -= direction * pushingIn;   // the band won't go any further

        // Stalled against the band, or let off: fire.
        if (grab.maxStretch > 0.8f && pushingIn <= 0.25f)
        {
            body.velocity = -direction * (launchBase + launchPerMetre * stretch) + Vector3.up * launchUp;
            return true;
        }
        return false;
    }

    private void Update() => UpdateVisual();

    private void UpdateVisual()
    {
        if (!_pouch)
            return;
        Grab pulling = null;
        foreach (var grab in _grabs.Values)
        {
            if (grab.car && grab.collider && (pulling == null || grab.stretch > pulling.stretch))
                pulling = grab;
        }
        if (pulling != null)
        {
            // The pouch rides on the car.
            Vector3 local = transform.InverseTransformPoint(pulling.collider.bounds.center);
            float stretch = Mathf.Clamp(pulling.stretch, 0f, maxStretch);
            _pouchLocal = new Vector3(Mathf.Clamp(local.x, -halfWidth, halfWidth), Rest.y, pulling.sign * stretch);
            _pouchVelocity = Vector3.zero;
        }
        else
        {
            // Snap back with a wobble.
            Vector3 toRest = Rest - _pouchLocal;
            _pouchVelocity += toRest * (220f * Time.deltaTime);
            _pouchVelocity *= Mathf.Exp(-9f * Time.deltaTime);
            _pouchLocal += _pouchVelocity * Time.deltaTime;
        }
        _pouch.localPosition = _pouchLocal;
        Strand(_strandLeft, leftAnchor);
        Strand(_strandRight, rightAnchor);
    }

    private void Strand(Transform strand, Vector3 anchor)
    {
        Vector3 delta = _pouchLocal - anchor;
        float length = Mathf.Max(0.05f, delta.magnitude);
        strand.localPosition = anchor + delta * 0.5f;
        strand.localRotation = Quaternion.LookRotation(delta / length, Vector3.up);
        float thickness = Mathf.Lerp(0.28f, 0.14f, Mathf.Clamp01((length - 2f) / 6f));   // thins as it stretches
        strand.localScale = new Vector3(thickness, thickness, length);
    }
}
