"""Slip & Skid obstacle authoring helpers for Blender (5.x).

Model an obstacle with the helpers below, then call export_obstacle() to write
assets/obstacles/<Id>.json (read by the plugin's DataObstacle) and render <Id>.png card art.

Conventions (Blender side):
- Metres, ground at z = 0, the obstacle centred on the origin. Blender +Y becomes Unity forward (+Z).
- Material names ARE the plugin's material specs: "toon:#RRGGBB", "primary", "secondary",
  "pattern", or "mat:<vanilla material name>" (e.g. "mat:Magma", "mat:BoostPad").
- Colliders are separate proxy objects made with collider(); they never render. Zones live on them.
- Animated parts hang under an empty made with pivot(..., anim=...).

Run inside Blender:  exec(open(r"<repo>/tools/blender/ss_lib.py").read())
"""
import bpy, bmesh, json, math, os
from mathutils import Vector, Matrix, Quaternion

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) if "__file__" in globals() else None
OUT_DIR = None  # set by set_repo()

# Colours used only for the Blender render of player-coloured / vanilla effect materials.
RENDER_COLOURS = {
    "primary": (0.18, 0.55, 1.0), "secondary": (1.0, 0.6, 0.12), "pattern": (0.18, 0.55, 1.0),
    "mat:Magma": (1.0, 0.35, 0.05), "mat:Bubble": (0.7, 0.93, 1.0), "mat:BoostPad": (0.2, 1.0, 0.45),
    "mat:MegaBoostPad": (1.0, 0.3, 0.9), "mat:Flames": (1.0, 0.55, 0.1), "mat:ToonMetal": (0.75, 0.78, 0.82),
}
EMISSIVE = {"mat:Magma", "mat:BoostPad", "mat:MegaBoostPad", "mat:Flames"}

# Text colours matching the vanilla card keywords.
RED, BLUE, GREEN, ORANGE, PURPLE = "#E3263F", "#2F7BFF", "#2BB34A", "#F29A1F", "#A040E0"


def kw(word, colour):
    return f"<color={colour}>{word}</color>"


def set_repo(repo):
    global REPO, OUT_DIR
    REPO = repo
    OUT_DIR = os.path.join(repo, "assets", "obstacles")
    os.makedirs(OUT_DIR, exist_ok=True)


# ---------------------------------------------------------------- scene

def reset_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


_current = None


def begin(obstacle_id):
    """Start a new obstacle in its own collection (removes an older one of the same id)."""
    global _current
    name = f"SS_{obstacle_id}"
    old = bpy.data.collections.get(name)
    if old:
        for obj in list(old.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    _current = coll
    return coll


def material(spec):
    mat = bpy.data.materials.get(spec)
    if mat:
        return mat
    mat = bpy.data.materials.new(spec)
    mat.use_nodes = True
    if spec.startswith("toon:") or spec.startswith("glow:"):
        h = spec[6:12]
        rgb = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    else:
        rgb = RENDER_COLOURS.get(spec, (0.8, 0.8, 0.8))
    rgb = tuple(c ** 2.2 for c in rgb)  # sRGB to linear for the render
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = 0.55
    if spec in EMISSIVE or spec.startswith("glow:"):
        bsdf.inputs["Emission Color"].default_value = (*rgb, 1)
        bsdf.inputs["Emission Strength"].default_value = 2.0
    if spec == "mat:Bubble":
        bsdf.inputs["Alpha"].default_value = 0.45
    if spec == "mat:ToonMetal":
        bsdf.inputs["Metallic"].default_value = 0.6
        bsdf.inputs["Roughness"].default_value = 0.3
    mat.diffuse_color = (*rgb, 1)
    return mat


def _link(obj, parent):
    _current.objects.link(obj)
    if parent is not None:
        obj.parent = parent
        obj.matrix_parent_inverse = Matrix.Identity(4)


def _finish_mesh(obj, mat, bevel, smooth_angle):
    if isinstance(mat, (list, tuple)):
        for m in mat:
            obj.data.materials.append(material(m))
    else:
        obj.data.materials.append(material(mat))
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(40)
        mod.harden_normals = False
    obj.data.shade_smooth()
    obj.data.set_sharp_from_angle(angle=math.radians(smooth_angle))
    return obj


def _mesh_obj(name, bm, loc, rot, parent):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    obj.location = loc
    obj.rotation_euler = tuple(math.radians(a) for a in rot)
    _link(obj, parent)
    return obj


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), mat="toon:#FFFFFF", bevel=0.06, parent=None, smooth_angle=30):
    """Box of `size` (x, y, z) centred on `loc`."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    return _finish_mesh(_mesh_obj(name, bm, loc, rot, parent), mat, bevel, smooth_angle)


def cyl(name, radius, depth, loc=(0, 0, 0), rot=(0, 0, 0), mat="toon:#FFFFFF", verts=32, bevel=0.04,
        parent=None, radius2=None, smooth_angle=40):
    """Cylinder (or cone/frustum with radius2) along local Z, centred on `loc`."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts, radius1=radius,
                          radius2=radius if radius2 is None else radius2, depth=depth)
    return _finish_mesh(_mesh_obj(name, bm, loc, rot, parent), mat, bevel, smooth_angle)


def sphere(name, radius, loc=(0, 0, 0), rot=(0, 0, 0), mat="toon:#FFFFFF", scale=(1, 1, 1), segments=32,
           rings=16, parent=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    return _finish_mesh(_mesh_obj(name, bm, loc, rot, parent), mat, 0, 80)


def torus(name, major, minor, loc=(0, 0, 0), rot=(0, 0, 0), mat="toon:#FFFFFF", parent=None, seg=48, ring=14):
    bm = bmesh.new()
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for j in range(ring):
            b = 2 * math.pi * j / ring
            r = major + minor * math.cos(b)
            bm.verts.new((r * math.cos(a), r * math.sin(a), minor * math.sin(b)))
    bm.verts.ensure_lookup_table()
    for i in range(seg):
        for j in range(ring):
            a, b = i * ring + j, i * ring + (j + 1) % ring
            c, d = ((i + 1) % seg) * ring + (j + 1) % ring, ((i + 1) % seg) * ring + j
            bm.faces.new((bm.verts[a], bm.verts[d], bm.verts[c], bm.verts[b]))
    return _finish_mesh(_mesh_obj(name, bm, loc, rot, parent), mat, 0, 80)


def prism(name, width, depth, height, loc=(0, 0, 0), rot=(0, 0, 0), mat="toon:#FFFFFF", bevel=0.05, parent=None):
    """Triangular prism (roof/wedge): ridge along Y, base `width` along X, centred on loc at its base."""
    bm = bmesh.new()
    w, d = width / 2, depth / 2
    v = [bm.verts.new(p) for p in [(-w, -d, 0), (w, -d, 0), (0, -d, height), (-w, d, 0), (w, d, 0), (0, d, height)]]
    for f in [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]:
        bm.faces.new([v[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish_mesh(_mesh_obj(name, bm, loc, rot, parent), mat, bevel, 30)


def frustum_box(name, bottom, top, height, loc=(0, 0, 0), rot=(0, 0, 0), mat="toon:#FFFFFF", bevel=0.05, parent=None):
    """Box tapering from `bottom` (x, y) at z=0 to `top` (x, y) at z=height, placed at loc."""
    bm = bmesh.new()
    bx, by, tx, ty = bottom[0] / 2, bottom[1] / 2, top[0] / 2, top[1] / 2
    v = [bm.verts.new(p) for p in [(-bx, -by, 0), (bx, -by, 0), (bx, by, 0), (-bx, by, 0),
                                   (-tx, -ty, height), (tx, -ty, height), (tx, ty, height), (-tx, ty, height)]]
    for f in [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]:
        bm.faces.new([v[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish_mesh(_mesh_obj(name, bm, loc, rot, parent), mat, bevel, 30)


def wedge(name, width, length, height, loc=(0, 0, 0), rot=(0, 0, 0), mat="toon:#FFFFFF", bevel=0.06, parent=None):
    """Ramp: rises along +Y from z=0 at y=-length/2 to `height` at y=+length/2. loc is its base centre."""
    bm = bmesh.new()
    w, l = width / 2, length / 2
    v = [bm.verts.new(p) for p in [(-w, -l, 0), (w, -l, 0), (w, l, 0), (-w, l, 0), (-w, l, height), (w, l, height)]]
    for f in [(0, 1, 2, 3), (3, 2, 5, 4), (0, 4, 5, 1), (0, 3, 4), (1, 5, 2)]:
        bm.faces.new([v[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish_mesh(_mesh_obj(name, bm, loc, rot, parent), mat, bevel, 30)


def ramp_colliders(name, width, length, height, loc=(0, 0, 0), parent=None):
    """Colliders for wedge(): a thick slab under the slope plus a filler block under its high half."""
    angle = math.degrees(math.atan2(height, length))
    slope = math.hypot(length, height)
    thick = 0.6
    nx = math.sin(math.radians(angle))   # slope normal is (0, -sin, cos)
    nz = math.cos(math.radians(angle))
    cx, cy, cz = loc[0], loc[1] + thick / 2 * nx, loc[2] + height / 2 - thick / 2 * nz
    collider(f"{name}Slope", "box", (width, slope, thick), (cx, cy, cz), rot=(angle, 0, 0), parent=parent)
    collider(f"{name}Fill", "box", (width, length / 2, height / 2), (loc[0], loc[1] + length / 4, loc[2] + height / 4), parent=parent)


def arc_slab(name, r_in, r_out, angle_deg, thickness, loc=(0, 0, 0), start_deg=0, mat="toon:#FFFFFF", segments=24,
             bevel=0.05, parent=None):
    """Flat curved slab (annulus sector) between radii, sweeping `angle_deg` from `start_deg`, top at loc z."""
    bm = bmesh.new()
    rings = []
    for i in range(segments + 1):
        a = math.radians(start_deg + angle_deg * i / segments)
        c, s = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((c * r, s * r, z)) for r, z in
                      [(r_in, 0), (r_out, 0), (r_out, -thickness), (r_in, -thickness)]])
    for i in range(segments):
        a, b = rings[i], rings[i + 1]
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish_mesh(_mesh_obj(name, bm, loc, (0, 0, 0), parent), mat, bevel, 30)


def lathe(name, profile, loc=(0, 0, 0), rot=(0, 0, 0), mat="toon:#FFFFFF", segments=32, scale=(1, 1, 1), parent=None,
          smooth_angle=50, bevel=0.0, closed=False):
    """Surface of revolution around local Z. `profile` is [(radius, z), ...] from bottom to top; a radius of 0
    closes that end to a point, otherwise the ends are capped flat. `closed` treats the profile as a loop
    (rings, tubes) with no caps. `scale` squashes it (e.g. oval bowls)."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r <= 1e-5:
            rings.append([bm.verts.new((0, 0, z))])
            continue
        ring = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            ring.append(bm.verts.new((r * math.cos(a) * scale[0], r * math.sin(a) * scale[1], z * scale[2])))
        rings.append(ring)
    pairs = len(rings) if closed else len(rings) - 1
    for k in range(pairs):
        a, b = rings[k], rings[(k + 1) % len(rings)]
        if len(a) == 1 and len(b) == 1:
            continue
        for i in range(segments):
            j = (i + 1) % segments
            if len(a) == 1:
                bm.faces.new((a[0], b[i], b[j]))
            elif len(b) == 1:
                bm.faces.new((a[i], b[0], a[j]))
            else:
                bm.faces.new((a[i], b[i], b[j], a[j]))
    if not closed and len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if not closed and len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish_mesh(_mesh_obj(name, bm, loc, rot, parent), mat, bevel, smooth_angle)


def loft(name, stations, loc=(0, 0, 0), rot=(0, 0, 0), mat="toon:#FFFFFF", segments=24, parent=None, smooth_angle=60,
         flat_bottom=0.0):
    """Tapered body along local X from elliptical cross sections. `stations` is [(x, half_width_y, half_height_z,
    z_offset), ...]; a station with zero size closes the end to a point. `flat_bottom` (0..1) squashes the lower
    half of every section (loaves and handles that sit on the ground)."""
    bm = bmesh.new()
    rings = []
    for x, ry, rz, dz in stations:
        if ry <= 1e-5 or rz <= 1e-5:
            rings.append([bm.verts.new((x, 0, dz))])
            continue
        ring = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            s = math.sin(a)
            z = rz * s * (1 - flat_bottom if s < 0 else 1)
            ring.append(bm.verts.new((x, ry * math.cos(a), dz + z)))
        rings.append(ring)
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        for i in range(segments):
            j = (i + 1) % segments
            if len(a) == 1:
                bm.faces.new((a[0], b[j], b[i]))
            elif len(b) == 1:
                bm.faces.new((a[i], a[j], b[0]))
            else:
                bm.faces.new((a[i], a[j], b[j], b[i]))
    if len(rings[0]) > 1:
        bm.faces.new(rings[0])
    if len(rings[-1]) > 1:
        bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish_mesh(_mesh_obj(name, bm, loc, rot, parent), mat, 0, smooth_angle)


def rounded_rect(name, size, radius, height, loc=(0, 0, 0), rot=(0, 0, 0), mat="toon:#FFFFFF", corner_segments=6,
                 bevel=0.06, parent=None):
    """Slab with rounded corners in plan: `size` (x, y), corner `radius`, `height` up from loc's z."""
    bm = bmesh.new()
    hx, hy = size[0] / 2 - radius, size[1] / 2 - radius
    pts = []
    for cx, cy, start in [(hx, hy, 0), (-hx, hy, 90), (-hx, -hy, 180), (hx, -hy, 270)]:
        for i in range(corner_segments + 1):
            a = math.radians(start + 90 * i / corner_segments)
            pts.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    bottom = [bm.verts.new((x, y, 0)) for x, y in pts]
    top = [bm.verts.new((x, y, height)) for x, y in pts]
    n = len(pts)
    bm.faces.new(list(reversed(bottom)))
    bm.faces.new(top)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish_mesh(_mesh_obj(name, bm, loc, rot, parent), mat, bevel, 30)


def taper_capsule(name, r1, r2, length, height, loc=(0, 0, 0), rot=(0, 0, 0), mat="toon:#FFFFFF", segments=20,
                  bevel=0.08, parent=None):
    """Upright slab whose plan is a tapered capsule: a circle of r1 at the origin joined by tangents to a
    circle of r2 at (length, 0). Rises `height` from loc's z (pinball flipper bats)."""
    d = length
    k = (r1 - r2) / d
    ang = math.acos(max(-1.0, min(1.0, k)))   # tangent touch angle, measured from +X
    pts = []
    for i in range(segments + 1):             # big end: from +ang round the back to -ang
        a = ang + (2 * math.pi - 2 * ang) * i / segments
        pts.append((r1 * math.cos(a), r1 * math.sin(a)))
    for i in range(segments + 1):             # small end: from -ang round the front to +ang
        a = -ang + 2 * ang * i / segments
        pts.append((d + r2 * math.cos(a), r2 * math.sin(a)))
    bm = bmesh.new()
    bottom = [bm.verts.new((x, y, 0)) for x, y in pts]
    top = [bm.verts.new((x, y, height)) for x, y in pts]
    n = len(pts)
    bm.faces.new(list(reversed(bottom)))
    bm.faces.new(top)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish_mesh(_mesh_obj(name, bm, loc, rot, parent), mat, bevel, 35)


def puddle(name, rx, ry, height, loc=(0, 0, 0), rot=(0, 0, 0), mat="toon:#FFFFFF", wobble=0.18, seed=1, segments=72,
           parent=None):
    """Flat liquid pool: an irregular rounded outline (radii rx, ry, edge wobble as a fraction) with a soft
    domed rim, `height` thick, sitting on loc."""
    rnd = __import__("random").Random(seed)
    waves = [(rnd.uniform(0.4, 1.0) * wobble / (n * 0.6), n, rnd.uniform(0, 2 * math.pi)) for n in (2, 3, 5, 7)]
    bm = bmesh.new()
    rings = []
    for scale, z in [(1.0, 0.0), (0.985, height * 0.55), (0.94, height * 0.9), (0.88, height)]:
        ring = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            r = 1 + sum(amp * math.sin(n * a + ph) for amp, n, ph in waves)
            ring.append(bm.verts.new((rx * r * scale * math.cos(a), ry * r * scale * math.sin(a), z)))
        rings.append(ring)
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        for i in range(segments):
            j = (i + 1) % segments
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(rings[-1])
    bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish_mesh(_mesh_obj(name, bm, loc, rot, parent), mat, 0, 70)


_SEGMENTS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
             "7": "abc", "8": "abcdefg", "9": "abcdfg"}


def digits(name, text, height, loc=(0, 0, 0), rot=(0, 0, 0), mat="toon:#14141A", depth=0.05, parent=None):
    """Seven-segment number `text` in the XZ plane (readable from -Y), centred on loc. Returns its pivot."""
    root = pivot(name, loc, rot, parent=parent)
    w, t = height * 0.5, height * 0.12
    gap = w * 0.45
    total = len(text) * w + (len(text) - 1) * gap
    for i, ch in enumerate(text):
        cx = -total / 2 + w / 2 + i * (w + gap)
        h2, w2 = height / 2, w / 2
        seg = {"a": ((cx, h2 - t / 2), (w, t)), "g": ((cx, 0), (w, t)), "d": ((cx, -h2 + t / 2), (w, t)),
               "f": ((cx - w2 + t / 2, h2 / 2), (t, h2)), "b": ((cx + w2 - t / 2, h2 / 2), (t, h2)),
               "e": ((cx - w2 + t / 2, -h2 / 2), (t, h2)), "c": ((cx + w2 - t / 2, -h2 / 2), (t, h2))}
        for s in _SEGMENTS.get(ch, ""):
            (x, z), (sx, sz) = seg[s]
            box(f"{name}_{i}{s}", (sx, depth, sz), (x, 0, z), mat=mat, bevel=0, parent=root)
    return root


def pivot(name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, anim=None, motion=None, timed=None, crumble=None, effect=None):
    """Empty used as a node; with `anim` its children animate on the network clock. anim keys:
    type "rotation": axis "X"/"Y"/"Z" (Blender), min/max degrees.
    type "scale": min/max (x, y, z) Blender scale.
    type "position": min/max (x, y, z) Blender offsets.
    speed (cycles per second), wrap "loop"/"pingpong", curve "linear"/"ease"/[[t, v], ...].
    `motion` is a one-shot TriggeredMotion: channel, type (as anim), axis, rest/active (degrees or
    vectors), startDelay, inTime, holdTime, outTime, cooldown, arm (colliders under it only live mid-move).
    `timed` = dict(speed, start, end): colliders under it only work in that window of the clock cycle.
    `crumble` = dict(minSpeed, speed, stagger, resetTime): knock-over; its direct children with meshes
    become debris when a car hits a solid collider under it.
    `effect` = dict(channel, kind "shock"/"teleport", consume): a one-off visual when that channel fires;
    consume makes the obstacle single-use."""
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_size = 0.5
    obj.location = loc
    obj.rotation_euler = tuple(math.radians(a) for a in rot)
    _link(obj, parent)
    if anim:
        obj["ss_anim"] = json.dumps(anim)
    if motion:
        obj["ss_motion"] = json.dumps(motion)
    if timed:
        obj["ss_timed"] = json.dumps(timed)
    if crumble:
        obj["ss_crumble"] = json.dumps(crumble)
    if effect:
        obj["ss_effect"] = json.dumps(effect)
    return obj


def collider(name, kind, size=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), parent=None, trigger=False, zone=None, radius=1.0):
    """Collider proxy: kind "box" (size x, y, z) or "sphere" (radius). zone is a dict of ZoneData fields."""
    bm = bmesh.new()
    if kind == "sphere":
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=6, radius=radius)
    else:
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    obj = _mesh_obj(name, bm, loc, rot, parent)
    obj["ss_collider"] = kind
    obj["ss_trigger"] = bool(trigger)
    if zone:
        obj["ss_zone"] = json.dumps(zone)
    obj.display_type = "WIRE"
    obj.hide_render = True
    return obj


# ---------------------------------------------------------------- export

def _b2u(v):
    return [round(v[0], 4), round(v[2], 4), round(v[1], 4)]


def _quat_b2u(q):
    # Swapping Y/Z mirrors space, which reverses rotation direction: (w, x, y, z) -> (-x, -z, -y, w).
    return [round(-q.x, 5), round(-q.z, 5), round(-q.y, 5), round(q.w, 5)]


def _euler_b2u(axis, degrees):
    # A Blender rotation about X/Y/Z is a Unity rotation about X/Z/Y in the opposite direction.
    v = [0, 0, 0]
    v[{"X": 0, "Y": 2, "Z": 1}[axis]] = -degrees
    return v


def _motion_b2u(motion):
    m = dict(motion)
    kind = m.get("type", "rotation")
    out = {k: m[k] for k in ("channel", "startDelay", "inTime", "holdTime", "outTime", "cooldown", "arm") if k in m}
    out["type"] = kind
    if kind == "rotation":
        out["rest"] = _euler_b2u(m.get("axis", "X"), m.get("rest", 0.0))
        out["active"] = _euler_b2u(m.get("axis", "X"), m.get("active", 90.0))
    else:
        default = (1, 1, 1) if kind == "scale" else (0, 0, 0)
        out["rest"] = _b2u(m.get("rest", default))
        out["active"] = _b2u(m.get("active", default))
    return out


def _anim_b2u(anim):
    a = dict(anim)
    out = {"type": a.get("type", "rotation"), "speed": a.get("speed", 1.0), "wrap": a.get("wrap", "loop")}
    if out["type"] == "rotation":
        out["min"] = _euler_b2u(a.get("axis", "Z"), a.get("min", 0.0))
        out["max"] = _euler_b2u(a.get("axis", "Z"), a.get("max", 360.0))
    elif out["type"] == "position":
        out["min"], out["max"] = _b2u(a.get("min", (0, 0, 0))), _b2u(a.get("max", (0, 0, 0)))
    else:
        out["min"], out["max"] = _b2u(a.get("min", (1, 1, 1))), _b2u(a.get("max", (1, 1, 1)))
    curve = a.get("curve", "linear")
    if curve == "linear":
        out["curve"] = [[0, 0, 1, 1], [1, 1, 1, 1]]
    elif curve == "ease":
        out["curve"] = [[0, 0], [1, 1]]
    else:
        out["curve"] = curve
    return out


def _mesh_data(obj, depsgraph):
    ev = obj.evaluated_get(depsgraph)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    normals = me.corner_normals
    verts, norms, lookup = [], [], {}
    subs = {}
    for tri in me.loop_triangles:
        idx = []
        for li in tri.loops:
            vi = me.loops[li].vertex_index
            n = normals[li].vector
            key = (vi, round(n.x, 3), round(n.y, 3), round(n.z, 3))
            if key not in lookup:
                lookup[key] = len(verts) // 3
                verts += _b2u(me.vertices[vi].co)
                norms += _b2u(n)
            idx.append(lookup[key])
        mat_index = tri.material_index if tri.material_index < len(obj.material_slots) else 0
        spec = obj.material_slots[mat_index].material.name if obj.material_slots else "toon:#FFFFFF"
        # Mirroring the axes flips handedness, so reverse the winding.
        subs.setdefault(spec, []).extend([idx[0], idx[2], idx[1]])
    ev.to_mesh_clear()
    return {"vertices": verts, "normals": norms,
            "submeshes": [{"material": k, "triangles": v} for k, v in subs.items()]}


def _collider_data(obj):
    xs = [v.co for v in obj.data.vertices]
    lo = Vector((min(v.x for v in xs), min(v.y for v in xs), min(v.z for v in xs)))
    hi = Vector((max(v.x for v in xs), max(v.y for v in xs), max(v.z for v in xs)))
    centre, size = (lo + hi) / 2, hi - lo
    data = {"type": obj["ss_collider"], "center": _b2u(centre), "trigger": bool(obj.get("ss_trigger", False))}
    if data["type"] == "sphere":
        data["radius"] = round(max(size) / 2, 4)
    else:
        data["size"] = [abs(c) for c in _b2u(size)]
    return data


def export_obstacle(obstacle_id, name, description, rarity="Common", render=True, full_art=False, partner=None,
                    partner_only=False, carrier=None, keep_carrier=False, scatter=None, scatter_count=10, surface=None):
    coll = bpy.data.collections[f"SS_{obstacle_id}"]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    objs = list(coll.all_objects)
    order, seen = [], set()

    def visit(o):
        if o.name in seen:
            return
        seen.add(o.name)
        order.append(o)
        for c in sorted([c for c in objs if c.parent == o], key=lambda c: c.name):
            visit(c)

    for root in sorted([o for o in objs if o.parent is None or o.parent not in objs], key=lambda o: o.name):
        visit(root)

    index = {o.name: i for i, o in enumerate(order)}
    nodes = []
    lo = Vector((1e9, 1e9, 0))
    hi = Vector((-1e9, -1e9, 0))
    for o in order:
        parent_world = o.parent.matrix_world if o.parent in objs else Matrix.Identity(4)
        local = parent_world.inverted() @ o.matrix_world
        loc, rot, scl = local.decompose()
        node = {"name": o.name, "parent": index.get(o.parent.name, -1) if o.parent else -1,
                "pos": _b2u(loc), "rot": _quat_b2u(rot), "scale": [round(scl.x, 4), round(scl.z, 4), round(scl.y, 4)]}
        if "ss_anim" in o:
            node["anim"] = _anim_b2u(json.loads(o["ss_anim"]))
        if "ss_motion" in o:
            node["motion"] = _motion_b2u(json.loads(o["ss_motion"]))
        if "ss_timed" in o:
            node["timed"] = json.loads(o["ss_timed"])
        if "ss_crumble" in o:
            node["crumble"] = json.loads(o["ss_crumble"])
        if "ss_effect" in o:
            node["effect"] = json.loads(o["ss_effect"])
        if "ss_collider" in o:
            node["collider"] = _collider_data(o)
            if "ss_zone" in o:
                node["zone"] = json.loads(o["ss_zone"])
        elif o.type == "MESH":
            node["mesh"] = _mesh_data(o, depsgraph)
            for corner in o.bound_box:
                w = o.matrix_world @ Vector(corner)
                lo.x, lo.y, hi.x, hi.y = min(lo.x, w.x), min(lo.y, w.y), max(hi.x, w.x), max(hi.y, w.y)
        nodes.append(node)

    footprint = [(0, 0, 0)]
    if hi.x >= lo.x:   # no meshes (cards that keep their vanilla carrier) keep just the centre
        footprint += [(lo.x, lo.y, 0), (hi.x, lo.y, 0), (hi.x, hi.y, 0), (lo.x, hi.y, 0)]
    data = {"version": 1, "name": name, "description": description, "rarity": rarity,
            "fullArt": full_art, "partner": partner, "partnerOnly": partner_only,
            "carrier": carrier, "keepCarrier": keep_carrier, "scatter": scatter, "scatterCount": scatter_count,
            "surface": surface, "forbiddenPoints": [_b2u(p) for p in footprint], "nodes": nodes}
    path = os.path.join(OUT_DIR, f"{obstacle_id}.json")
    with open(path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    result = {"json": path, "nodes": len(nodes), "kb": round(os.path.getsize(path) / 1024, 1)}
    if render and any(o.type == "MESH" and not o.hide_render for o in objs):
        result["png"] = render_thumbnail(obstacle_id)
    return result


# ---------------------------------------------------------------- thumbnail

def render_thumbnail(obstacle_id, size=512):
    return _render(obstacle_id, os.path.join(OUT_DIR, f"{obstacle_id}.png"), size, size,
                   Vector((1.0, -1.1, 0.62)), ortho=True, fill=2.25)


def render_card_foreground(obstacle_id, width=720, height=1024, direction=(0.75, -1.0, 0.35), fill=1.25):
    """Dramatic perspective render for a full-art card, composited later by tools/card_art.ps1."""
    out = os.path.join(REPO, "tools", "blender", "renders")
    os.makedirs(out, exist_ok=True)
    return _render(obstacle_id, os.path.join(out, f"{obstacle_id}_card_fg.png"), width, height,
                   Vector(direction), ortho=False, fill=fill, shadow=False)


def _render(obstacle_id, path, width, height, direction, ortho, fill, shadow=True):
    scene = bpy.context.scene
    coll = bpy.data.collections[f"SS_{obstacle_id}"]
    for c in scene.collection.children:
        c.hide_render = c != coll and c.name != "SS_Studio"
    studio = _studio()
    studio["catcher"].hide_render = not shadow

    meshes = [o for o in coll.all_objects if o.type == "MESH" and not o.hide_render]
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre = (lo + hi) / 2
    radius = (hi - lo).length / 2

    cam = studio["camera"]
    direction = direction.normalized()
    cam.data.clip_end = 1000
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = radius * fill
        cam.location = centre + direction * (radius * 6 + 10)
    else:
        cam.data.type = "PERSP"
        cam.data.lens = 35
        # Distance at which the bounding sphere spans `fill` times the narrower frame side.
        half_fov = math.atan(cam.data.sensor_width / (2 * cam.data.lens) * min(width, height) / max(width, height))
        cam.location = centre + direction * (radius / math.sin(half_fov) / fill)
    cam.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    studio["catcher"].location = (centre.x, centre.y, 0)
    studio["catcher"].scale = (radius * 4, radius * 4, 1)

    scene.camera = cam
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.film_transparent = True
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def _studio():
    coll = bpy.data.collections.get("SS_Studio")
    if not coll:
        coll = bpy.data.collections.new("SS_Studio")
        bpy.context.scene.collection.children.link(coll)
    objs = {o.name: o for o in coll.objects}
    if "SS_Camera" not in objs:
        cam = bpy.data.objects.new("SS_Camera", bpy.data.cameras.new("SS_Camera"))
        coll.objects.link(cam)
        sun = bpy.data.objects.new("SS_Sun", bpy.data.lights.new("SS_Sun", "SUN"))
        sun.data.energy = 4.0
        sun.data.angle = math.radians(12)
        sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(30))
        coll.objects.link(sun)
        bpy.ops.mesh.primitive_plane_add(size=2)
        plane = bpy.context.active_object
        plane.name = "SS_ShadowCatcher"
        for c in plane.users_collection:
            c.objects.unlink(plane)
        coll.objects.link(plane)
        plane.is_shadow_catcher = True
        world = bpy.context.scene.world or bpy.data.worlds.new("World")
        bpy.context.scene.world = world
        world.use_nodes = True
        bg = world.node_tree.nodes.get("Background")
        bg.inputs["Color"].default_value = (1, 1, 1, 1)
        bg.inputs["Strength"].default_value = 0.35
        objs = {o.name: o for o in coll.objects}
    return {"camera": objs["SS_Camera"], "catcher": objs["SS_ShadowCatcher"]}
