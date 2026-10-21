using System.Collections;
using System.Collections.Generic;
using Game;
using Obstacles;
using Unity.Netcode;
using UnityEngine;

namespace SlipSkid.CustomContent;

// Knock-over: hit the obstacle hard enough and its pieces (the node's direct children that have meshes)
// tumble, then lock where they landed as solid obstacles until the next round starts.
// - The hit is detected by the car's owner and sent through TriggerBus with its direction, so every
//   machine starts the same fall.
// - While falling, pieces are cosmetic (they ignore cars), since each machine's physics differs slightly.
// - Once settled, the host broadcasts where every piece landed; everyone snaps to that layout and the
//   pieces become solid, so cars hit the same rubble on every screen.
// - A new round (roundIndex changes on the host and syncs) puts everything back.
internal sealed class Crumble : MonoBehaviour
{
    private enum State { Standing, Falling, Locked }

    public int channel;
    public float minSpeed = 8f;      // car speed needed to knock it over
    public float speed = 12f;        // how hard the pieces fly
    public float stagger;            // seconds between pieces (dominoes fall in sequence)
    public float settleTime = 3f;    // seconds after the last piece falls before the layout locks

    private const float ClientLockTimeout = 4f;   // lock our own layout if the host's never arrives

    private Obstacle _obstacle;
    private readonly List<Transform> _pieces = new();
    private readonly List<Vector3> _restPositions = new();
    private readonly List<Quaternion> _restRotations = new();
    private readonly List<Rigidbody> _bodies = new();
    private readonly List<BoxCollider> _debris = new();
    private readonly List<(Collider, Collider)> _ignored = new();
    private Collider[] _solids = new Collider[0];
    private State _state;
    private int _round;

    internal Obstacle Obstacle => _obstacle;
    internal int PieceCount => _pieces.Count;

    private void Start()
    {
        _obstacle = GetComponentInParent<Obstacle>();
        for (int i = 0; i < transform.childCount; i++)
        {
            var child = transform.GetChild(i);
            if (child.GetComponentInChildren<MeshRenderer>(true))
            {
                _pieces.Add(child);
                _restPositions.Add(child.localPosition);
                _restRotations.Add(child.localRotation);
            }
        }
        var solids = new List<Collider>();
        foreach (var collider in GetComponentsInChildren<Collider>(true))
        {
            if (collider.isTrigger)
                continue;
            solids.Add(collider);
            collider.gameObject.AddComponent<CrumbleHit>().owner = this;
        }
        _solids = solids.ToArray();
    }

    internal void Knock(Vector3 direction)
    {
        if (_state != State.Standing)
            return;
        _state = State.Falling;
        _round = CurrentRound();
        StartCoroutine(Fall(direction.sqrMagnitude > 0.01f ? direction.normalized : transform.forward));
    }

    private IEnumerator Fall(Vector3 direction)
    {
        var carColliders = new List<Collider>();
        foreach (var player in GameManager.Players)
        {
            if (player && player.playerNetworking)
                carColliders.AddRange(player.playerNetworking.GetComponentsInChildren<Collider>(true));
        }
        Vector3 side = Vector3.Cross(Vector3.up, direction);
        for (int i = 0; i < _pieces.Count; i++)
        {
            if (stagger > 0f && i > 0)
                yield return new WaitForSeconds(stagger);
            var piece = _pieces[i];
            if (!piece)
                continue;
            var rnd = new System.Random(i * 7919 + 17);
            float jitter = (float)rnd.NextDouble();

            var collider = piece.gameObject.AddComponent<BoxCollider>();
            var bounds = LocalBounds(piece);
            collider.center = bounds.center;
            collider.size = bounds.size;
            _debris.Add(collider);
            foreach (var car in carColliders)
            {
                if (!car)
                    continue;
                Physics.IgnoreCollision(collider, car);
                _ignored.Add((collider, car));
            }
            var body = piece.gameObject.AddComponent<Rigidbody>();   // default mass (the stripped build has no mass setter)
            body.velocity = direction * speed * (0.6f + 0.6f * jitter) + Vector3.up * (2f + 4f * (float)rnd.NextDouble())
                            + side * (float)(rnd.NextDouble() - 0.5) * speed * 0.5f;
            body.angularVelocity = side * (3f + 4f * jitter);
            _bodies.Add(body);
        }

        yield return new WaitForSeconds(settleTime);
        if (IsHost())
        {
            Lock();
            TriggerBus.SendPoses(this, CapturePoses());
        }
        else
        {
            yield return new WaitForSeconds(ClientLockTimeout);
            if (_state == State.Falling)
                Lock();
        }
    }

    // Clients: the host's final layout. Snap to it and lock (also fine if we already locked our own).
    internal void ApplyPoses(List<(Vector3, Quaternion)> poses)
    {
        if (_state == State.Standing)
            return;
        if (_state == State.Falling)
        {
            StopAllCoroutines();
            Lock();
        }
        for (int i = 0; i < poses.Count && i < _pieces.Count; i++)
        {
            if (!_pieces[i])
                continue;
            _pieces[i].localPosition = poses[i].Item1;
            _pieces[i].localRotation = poses[i].Item2;
        }
    }

    internal List<(Vector3, Quaternion)> CapturePoses()
    {
        var poses = new List<(Vector3, Quaternion)>(_pieces.Count);
        foreach (var piece in _pieces)
            poses.Add(piece ? (piece.localPosition, piece.localRotation) : (Vector3.zero, Quaternion.identity));
        return poses;
    }

    // Pieces stop moving and become solid: drop the rigidbodies, let cars collide with them again.
    private void Lock()
    {
        foreach (var body in _bodies)
        {
            if (!body)
                continue;
            body.isKinematic = true;   // Destroy waits for the end of the frame; stop physics moving it now
            Destroy(body);
        }
        _bodies.Clear();
        foreach (var (debris, car) in _ignored)
        {
            if (debris && car)
                Physics.IgnoreCollision(debris, car, false);
        }
        _ignored.Clear();
        _state = State.Locked;
    }

    private void LateUpdate()
    {
        if (_state == State.Standing)
            return;
        // Keep the original solid proxies off; the game re-enables colliders on state changes.
        foreach (var solid in _solids)
        {
            if (solid)
                solid.enabled = false;
        }
        if (CurrentRound() != _round)
            Restore();
    }

    private void Restore()
    {
        StopAllCoroutines();
        foreach (var body in _bodies)
        {
            if (body)
                Destroy(body);
        }
        foreach (var debris in _debris)
        {
            if (debris)
                Destroy(debris);
        }
        _bodies.Clear();
        _debris.Clear();
        _ignored.Clear();
        for (int i = 0; i < _pieces.Count; i++)
        {
            if (!_pieces[i])
                continue;
            _pieces[i].localPosition = _restPositions[i];
            _pieces[i].localRotation = _restRotations[i];
        }
        foreach (var solid in _solids)
        {
            if (solid)
                solid.enabled = true;
        }
        _state = State.Standing;
    }

    private static int CurrentRound() =>
        GameManager.instance && GameManager.instance.networkVariables ? GameManager.instance.networkVariables.roundIndex.Value : 0;

    private static bool IsHost() => !NetworkManager.Singleton || NetworkManager.Singleton.IsServer;

    // Bounds of a piece's meshes in the piece's own space, for its debris collider.
    private static Bounds LocalBounds(Transform piece)
    {
        bool any = false;
        var bounds = new Bounds(Vector3.zero, Vector3.one * 0.2f);
        foreach (var filter in piece.GetComponentsInChildren<MeshFilter>(true))
        {
            if (!filter.sharedMesh)
                continue;
            var b = filter.sharedMesh.bounds;
            for (int i = 0; i < 8; i++)
            {
                var corner = new Vector3(i % 2 == 0 ? b.min.x : b.max.x, (i / 2) % 2 == 0 ? b.min.y : b.max.y, i / 4 == 0 ? b.min.z : b.max.z);
                var p = piece.InverseTransformPoint(filter.transform.TransformPoint(corner));
                if (!any) { bounds = new Bounds(p, Vector3.zero); any = true; }
                else bounds.Encapsulate(p);
            }
        }
        return bounds;
    }
}

// On each solid collider of a Crumble: the owner's car hitting it fast enough knocks the whole thing over.
internal sealed class CrumbleHit : MonoBehaviour
{
    public Crumble owner;

    private void OnCollisionEnter(Collision collision)
    {
        if (!owner || !owner.Obstacle || !CarLookup.IsPlaced(owner.Obstacle))
            return;
        if (!CarLookup.TryGetOwnedCar(collision.collider, out _, out var car))
            return;
        if (collision.relativeVelocity.magnitude < owner.minSpeed)
            return;
        // Pieces fly away from the car (relativeVelocity's sign depends on which side reports the hit).
        Vector3 direction = Vector3.ProjectOnPlane(transform.position - car.sphereRigidbody.position, Vector3.up);
        TriggerBus.Fire(owner.Obstacle, owner.channel, direction);
    }
}
