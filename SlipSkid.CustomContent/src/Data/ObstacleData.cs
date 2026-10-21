using System.Collections.Generic;

// Fields are filled by Newtonsoft.Json, never assigned in code.
#pragma warning disable CS0649

namespace SlipSkid.CustomContent;

// The JSON written by tools/blender/ss_export.py. Everything is already in Unity space
// (Y up, left-handed, metres), so the loader never converts axes.
internal sealed class ObstacleData
{
    public int version;
    public string name;
    public string description;
    public string rarity;
    public bool fullArt;      // card art is <Id>_card.png covering the whole card
    public string partner;    // id of the obstacle handed over to place after this one
    public bool partnerOnly;  // never drafted, only spawned as a partner
    public string carrier;    // vanilla card to borrow (asset name); default: auto-picked plain prop
    public bool keepCarrier;  // keep the carrier's own look and behaviour (scatters, surface swaps)
    public string scatter;    // ObstacleScatter carrier: id of our obstacle it scatters
    public int scatterCount = 10;
    public string surface;    // ObstacleSurfaceSwap carrier: "reverse"
    public float[][] forbiddenPoints;
    public List<NodeData> nodes = new();
}

// One GameObject. Parents always come before their children in the list.
internal sealed class NodeData
{
    public string name;
    public int parent = -1;
    public float[] pos;
    public float[] rot;   // quaternion x, y, z, w
    public float[] scale;
    public MeshData mesh;
    public ColliderData collider;
    public ZoneData zone;
    public AnimData anim;
    public MotionData motion;
    public TimedData timed;
    public CrumbleData crumble;
    public EffectData effect;
}

// A one-off visual on a TriggerBus channel ("shock" or "teleport"); `consume` uses the obstacle up.
internal sealed class EffectData
{
    public int channel;
    public string kind = "shock";
    public bool consume;
}

// Knock-over: the node's direct children with meshes tumble when a car hits its solid colliders, then
// lock solid where they landed until the next round.
internal sealed class CrumbleData
{
    public int channel = 9;
    public float minSpeed = 8f;
    public float speed = 12f;
    public float stagger;
    public float settleTime = 3f;
}

// A one-shot TriggeredMotion on this node (see TriggerBus channels).
internal sealed class MotionData
{
    public int channel;
    public string type = "rotation";   // "rotation" (Euler), "position" or "scale"
    public float[] rest;
    public float[] active;
    public float startDelay;
    public float inTime = 0.15f;
    public float holdTime = 1f;
    public float outTime = 0.8f;
    public float cooldown = 0.5f;
    public bool arm;   // colliders under the node only work while it's out
}

// Colliders under this node only work during [start, end) of a repeating network-clock cycle.
internal sealed class TimedData
{
    public float speed = 0.2f;
    public float start;
    public float end = 0.5f;
}

internal sealed class MeshData
{
    public float[] vertices;
    public float[] normals;
    public List<SubmeshData> submeshes = new();
}

internal sealed class SubmeshData
{
    // "toon:#RRGGBB", "primary", "secondary", "pattern", or "mat:<vanilla material name>".
    public string material;
    public int[] triangles;
}

internal sealed class ColliderData
{
    public string type;   // "box" or "sphere"
    public float[] center;
    public float[] size;
    public float radius;
    public bool trigger;
}

internal sealed class ZoneData
{
    public string type;   // "kill", "bounce", "accel", "slow", "push", "launch", "plate", "toilet", "grow",
                          // "gravity" (low gravity inside this box), "spawn" (teleport the car back to its start)

    // gravity: fraction of the map's gravity cancelled inside the box (0.7 = 30% gravity).
    public float gravityFactor = 0.7f;

    // push: on contact, throw the car straight away from the node at a fixed speed (plus some lift).
    public float pushSpeed = 18f;
    public float pushUp = 5f;

    // kill: only kills when hit at least this fast along `axis` ("up", "forward", "right"); 0 = always.
    public float minSpeed;
    public string axis;

    // bounce: "radial" (away from the node), "collision" (reflect off the surface), "custom" (along `normal`),
    // or "velocity" (set the car's velocity to `velocity`, world space).
    public string mode = "radial";
    public float factor = 1f;
    public float[] normal;
    public float[] velocity;

    // accel: pushes along the node's forward (+Z) while inside; optional kick on entry.
    public float acceleration = 10f;
    public float velocityOnEnter = 30f;
    public bool setVelocity;

    // slow: fraction of velocity removed per second while inside.
    public float slowFactor = 0.25f;
    public bool stop;

    // launch: throw the car along `velocity` in the node's own space (turns with the obstacle), after `delay`.
    // Uses setVelocity (replace the car's velocity) or adds to it.
    // plate/launch/toilet: `channel` fires TriggeredMotions on that TriggerBus channel (-1 = none).
    public float delay;
    public float cooldown = 1f;
    public int channel = -1;

    // grow: car scale multiplier and how long it lasts.
    public float growScale = 2.2f;
    public float duration = 8f;

    // slingshot: band between two anchors (node space) across the node's X axis; see SlingshotZone.
    public float[] anchorLeft;
    public float[] anchorRight;
    public float halfWidth = 1.9f;
    public float maxStretch = 7f;
    public float spring = 9f;
    public float launchBase = 14f;
    public float launchPerMetre = 5f;
    public float launchUp = 4f;
    public string rubber = "toon:#E3263F";
    public string pouch = "toon:#6B3E26";
}

internal sealed class AnimData
{
    public string type;   // "rotation" (Euler degrees), "scale" or "position"
    public float[] min;
    public float[] max;
    public float speed = 1f;
    public float[][] curve;   // keys [time, value] or [time, value, inTangent, outTangent]
    public string wrap = "loop";   // "loop" or "pingpong"
}
