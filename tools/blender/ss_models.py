"""The obstacle models. Each builder models one obstacle with ss_lib helpers and returns its card text.

Run inside Blender after ss_lib.py:
    exec(open(r"<repo>/tools/blender/ss_models.py").read())
    build_all(["JengaTower"])        # or build_all() for everything

Sizes follow the vanilla props (Fence 3.4 x 2.2 m, Toilet Paper Roll 6 m tall, Torii 6.4 x 8.9 m).
Zone dicts are ZoneData fields and are passed through as-is, so vectors in them are Unity space (Y up).
"""
import math, random

WOOD_A, WOOD_B = "toon:#E9C48C", "toon:#D8AB6E"
METAL = "mat:ToonMetal"
BLACK, WHITE = "toon:#2A2A30", "toon:#F4F4F4"

KILL = {"type": "kill"}


def bounce(mode="radial", factor=1.0, **extra):
    return {"type": "bounce", "mode": mode, "factor": factor, **extra}


def push(speed=18.0, up=5.0):
    """Throw cars straight away at a fixed speed (vanilla reflect-bounces barely move a stopped car)."""
    return {"type": "push", "pushSpeed": speed, "pushUp": up}


def launch_up(speed):
    """Egg-style fixed upward launch on contact (vanilla Egg: custom velocity 12.5 up)."""
    return bounce("velocity", 1.0, velocity=[0, speed, 0])


# ---------------------------------------------------------------- blockers

def jenga_tower():
    rnd = random.Random(7)
    layers, block = 12, (0.85, 2.6, 0.5)
    # Hit it hard enough and every block tumbles (Crumble), then the tower rebuilds itself.
    tower = pivot("Tower", crumble=dict(minSpeed=7, speed=11, settleTime=3))
    for layer in range(layers):
        z = block[2] / 2 + layer * block[2]
        for i in range(3):
            if layer == 7 and i == 1:
                continue  # the one somebody already pulled
            offset = (i - 1) * (block[0] + 0.03)
            jitter = rnd.uniform(-0.06, 0.06)
            mat = "primary" if (layer, i) in [(3, 0), (9, 2)] else (WOOD_A if (layer + i) % 2 else WOOD_B)
            if layer % 2 == 0:
                box(f"Block_{layer}_{i}", block, (offset, jitter, z), mat=mat, bevel=0.05, parent=tower)
            else:
                box(f"Block_{layer}_{i}", (block[1], block[0], block[2]), (jitter, offset, z), mat=mat, bevel=0.05, parent=tower)
    collider("Solid", "box", (2.65, 2.65, layers * block[2]), (0, 0, layers * block[2] / 2), parent=tower)
    return dict(name="The Jenga Tower", description=f"Don't pull the wrong one. Hit it hard to {kw('knock it over', ORANGE)}.",
                rarity="Common")


def book_stack():
    covers = ["primary", "toon:#3FA34D", "secondary", "toon:#8E44AD", "toon:#E3263F"]
    thick, step = 0.5, 0.95
    rnd = random.Random(3)
    for i, cover in enumerate(covers):
        y = i * step - 2 * step
        z = thick / 2 + i * thick
        turn = rnd.uniform(-4, 4)
        book = pivot(f"Book{i}", (rnd.uniform(-0.15, 0.15), y, z), rot=(0, 0, turn))
        box(f"Pages{i}", (3.9, 2.85, thick - 0.12), (0.06, 0, 0), mat="toon:#FFF6E0", bevel=0.02, parent=book)
        box(f"CoverTop{i}", (4.2, 3.0, 0.07), (0, 0, thick / 2 - 0.035), mat=cover, bevel=0.02, parent=book)
        box(f"CoverBottom{i}", (4.2, 3.0, 0.07), (0, 0, -thick / 2 + 0.035), mat=cover, bevel=0.02, parent=book)
        box(f"Spine{i}", (0.12, 3.0, thick), (-2.06, 0, 0), mat=cover, bevel=0.03, parent=book)
        box(f"Band{i}", (0.14, 0.3, thick + 0.01), (-2.07, 0.9, 0), mat="toon:#F2C14E", bevel=0.01, parent=book)
        collider(f"BookCol{i}", "box", (4.2, 3.0, thick), parent=book)
    return dict(name="The Book Stack", description="Required reading. Also a staircase.", rarity="Common")


def baguette():
    crust, dark, crumb, flour = "toon:#C97B30", "toon:#A85E22", "toon:#F2D49A", "toon:#FFF6E6"
    half = 3.7
    loaf = pivot("Loaf", (0, 0, 0.36), rot=(0, 0, 8))

    def shape(x):
        t = min(1.0, abs(x) / half)
        return (1 - t ** 2.6) ** 0.55

    def top(x):   # height of the crust's top surface above the pivot at x
        return 0.62 * shape(x) + 0.06 * (1 - (x / half) ** 2)

    stations = []
    for i in range(33):
        x = -half + 2 * half * i / 32
        k = shape(x)
        wobble = 1 + 0.035 * math.sin(x * 2.1 + 0.6)
        stations.append((x, max(0.07, 0.6 * k) * wobble, max(0.06, 0.62 * k), 0.06 * (1 - (x / half) ** 2)))
    stations = [(-half - 0.1, 0, 0, 0.0)] + stations + [(half + 0.1, 0, 0, 0.0)]
    loft("Crust", stations, mat=crust, segments=28, flat_bottom=0.45, parent=loaf)
    # The scoring: pale crumb bulging out of each cut, with a dark raised crust "ear" along one side.
    for i in range(6):
        x = -2.55 + i * 1.02
        cut = pivot(f"Cut{i}", (x, 0.0, top(x) - 0.06), rot=(0, 0, 32), parent=loaf)
        sphere(f"Crumb{i}", 1.0, (0, -0.03, 0.02), mat=crumb, scale=(0.56, 0.17, 0.1), segments=16, rings=8, parent=cut)
        sphere(f"Ear{i}", 1.0, (0.02, 0.12, 0.07), rot=(18, 0, 0), mat=dark, scale=(0.6, 0.09, 0.09), segments=14, rings=6, parent=cut)
    rnd = random.Random(12)
    for i in range(12):
        x = rnd.uniform(-2.9, 2.9)
        sphere(f"Flour{i}", rnd.uniform(0.04, 0.08), (x, rnd.uniform(-0.28, 0.28), top(x) - 0.03), mat=flour,
               scale=(1, 1, 0.35), segments=8, rings=4, parent=loaf)
    collider("LoafCol", "box", (7.2, 1.2, 1.0), (0, 0, 0.18), parent=loaf)
    return dict(name="The Baguette", description="A speed bump, but French.", rarity="Common")


def rubber_duck():
    yellow, orange = "toon:#FFD43B", "toon:#FF8C1A"
    # Faces -Y, the side the card camera looks at.
    sphere("Body", 1.6, (0, 0, 1.35), mat=yellow, scale=(1.0, 1.3, 0.82))
    cyl("Tail", 0.7, 1.0, (0, 1.9, 1.95), rot=(55, 0, 0), mat=yellow, radius2=0.05, verts=16)
    sphere("Head", 1.05, (0, -1.05, 2.75), mat=yellow)
    sphere("Beak", 0.6, (0, -2.05, 2.55), mat=orange, scale=(1.0, 0.9, 0.38))
    for side in (-1, 1):
        sphere(f"Eye{side}", 0.17, (side * 0.45, -1.88, 3.0), mat=BLACK)
        sphere(f"Shine{side}", 0.06, (side * 0.43, -2.03, 3.08), mat=WHITE)
        sphere(f"Wing{side}", 0.7, (side * 1.45, 0.1, 1.5), mat=yellow, scale=(0.35, 1.0, 0.6))
    collider("BodyCol", "sphere", loc=(0, 0, 1.35), radius=1.7, zone=push(20, 6))
    collider("HeadCol", "sphere", loc=(0, -1.05, 2.75), radius=1.05, zone=push(20, 6))
    return dict(name="The Rubber Duck", description=f"Squeak. {kw('Bounces', BLUE)} vehicles away.", rarity="Uncommon")


def domino_line():
    pips_top = [(-0.55, 1.35), (0, 0.95), (0.55, 0.55)]
    pips_bottom = [(-0.5, -0.55), (0.5, -1.25), (-0.5, -1.25), (0.5, -0.55)]
    # Knock one and they all go, one after another.
    line = pivot("Line", crumble=dict(minSpeed=6, speed=5, stagger=0.15, settleTime=3))
    for i in range(5):
        x = 0.8 if i % 2 else -0.8
        y = -3.2 + i * 1.6
        tile = pivot(f"Domino{i}", (x, y, 2.0), rot=(0, 0, (i % 2) * 14 - 7), parent=line)
        box(f"Tile{i}", (2.2, 0.5, 4.0), mat=BLACK, bevel=0.12, parent=tile)
        box(f"Divider{i}", (1.6, 0.04, 0.08), (0, -0.26, 0), mat=WHITE, bevel=0, parent=tile)
        for j, (px, pz) in enumerate(pips_top + pips_bottom):
            sphere(f"Pip{i}_{j}", 0.2, (px, -0.25, pz), mat=WHITE, scale=(1, 0.35, 1), segments=12, rings=6, parent=tile)
        collider(f"DominoCol{i}", "box", (2.2, 0.5, 4.0), parent=tile)
    return dict(name="The Domino Line", description=f"Knocking them over is your problem. They {kw('topple', ORANGE)} one by one.",
                rarity="Common")


def sponge():
    rnd = random.Random(11)
    box("Foam", (4.4, 3.0, 1.6), (0, 0, 0.8), mat="toon:#FFD84D", bevel=0.25)
    box("Scrubber", (4.4, 3.0, 0.45), (0, 0, 1.83), mat="toon:#3FA34D", bevel=0.12)
    # Pores: dark flattened discs sitting flush with the front and side faces.
    for i in range(18):
        r = rnd.uniform(0.1, 0.22)
        if i % 3:
            loc, scale = (rnd.uniform(-1.9, 1.9), rnd.choice([-1.5, 1.5]), rnd.uniform(0.3, 1.35)), (1, 0.12, 0.8)
        else:
            loc, scale = (rnd.choice([-2.2, 2.2]), rnd.uniform(-1.2, 1.2), rnd.uniform(0.3, 1.35)), (0.12, 1, 0.8)
        sphere(f"Pore{i}", r, loc, mat="toon:#B8860B", scale=scale, segments=12, rings=6)
    collider("Soak", "box", (4.4, 3.0, 2.1), (0, 0, 1.05), trigger=True, zone={"type": "slow", "slowFactor": 3.0})
    return dict(name="The Sponge", description=f"Absorbs water. And {kw('momentum', ORANGE)}.", rarity="Uncommon")


def tin_can_pyramid():
    r, h = 0.65, 1.5
    spots = [(-1.4, 0), (0, 0), (1.4, 0), (-0.7, 1), (0.7, 1), (0, 2)]
    labels = ["toon:#E3263F", "primary", "toon:#3FA34D", "secondary", "toon:#E3263F", "primary"]
    pyramid = pivot("Pyramid", crumble=dict(minSpeed=6, speed=13, settleTime=3))
    for i, ((x, row), label) in enumerate(zip(spots, labels)):
        z = h / 2 + row * h
        can = pivot(f"Can{i}", (x, 0, z), rot=(0, 0, i * 37), parent=pyramid)
        cyl(f"Tin{i}", r, h, mat=METAL, verts=24, bevel=0.03, parent=can)
        cyl(f"Label{i}", r + 0.02, h * 0.62, mat=label, verts=24, bevel=0.0, parent=can)
        torus(f"RimTop{i}", r - 0.04, 0.05, (0, 0, h / 2 - 0.02), mat=METAL, parent=can, seg=24, ring=6)
        collider(f"CanCol{i}", "box", (1.3, 1.3, h), parent=can)
    return dict(name="The Tin Can Pyramid", description=f"Bowling for vehicles. Hit it to {kw('scatter the cans', ORANGE)}.",
                rarity="Common")


# ---------------------------------------------------------------- boosters

def mattress():
    box("Mattress", (4.4, 6.4, 0.9), (0, 0, 0.45), mat="pattern", bevel=0.3)
    box("Pillow", (3.4, 1.5, 0.5), (0, 2.25, 1.1), mat=WHITE, bevel=0.22)
    for ix in range(3):
        for iy in range(4):
            sphere(f"Button{ix}_{iy}", 0.12, (-1.4 + ix * 1.4, -2.5 + iy * 1.2, 0.9), mat=WHITE,
                   scale=(1, 1, 0.5), segments=10, rings=5)
    collider("Bed", "box", (4.4, 6.4, 0.9), (0, 0, 0.45), zone=launch_up(20))
    return dict(name="The Mattress", description=f"Jump on the bed, they said. {kw('Launches', GREEN)} anything that lands on it.",
                rarity="Uncommon")


def whoopee_cushion():
    pink, dark, light = "toon:#FF6FAE", "toon:#D9407F", "toon:#FFB3D3"
    body = [(0, 0.04), (1.5, 0.06), (1.95, 0.22), (2.08, 0.45), (1.98, 0.7), (1.6, 0.9), (0.9, 1.0), (0, 1.03)]
    lathe("Cushion", body, mat=pink, segments=40)
    torus("Seam", 2.07, 0.06, (0, 0, 0.45), mat=dark, seg=48, ring=6)
    lathe("Shine", [(0, 1.035), (0.55, 1.01), (0.75, 0.99), (0, 0.99)], (-0.5, -0.4, 0.0), mat=light, segments=20)
    neck = [(0.55, 0.0), (0.42, 0.4), (0.33, 0.8), (0.33, 1.05), (0.42, 1.15), (0.42, 1.28), (0.3, 1.32)]
    lathe("Neck", neck, (0, 1.75, 0.32), rot=(-90, 0, 0), mat=pink, segments=20, scale=(1, 0.6, 1))
    torus("Lip", 0.36, 0.07, (0, 2.95, 0.32), rot=(90, 0, 0), mat=dark, seg=20, ring=6)
    collider("Puff", "box", (3.8, 3.8, 0.8), (0, 0, 0.4), zone=bounce("velocity", 1.0, velocity=[0, 22, 0]))
    return dict(name="The Whoopee Cushion", description=f"Pfffbbbt. {kw('Launches', GREEN)} anything that sits on it.",
                rarity="Rare")


def hot_sauce_puddle():
    glass, cap, label, chilli, stem = "toon:#B3170F", "toon:#3FA34D", "toon:#FFF3E0", "toon:#E3263F", "toon:#2E8B3A"
    deep, sauce, light, ripple = "toon:#9E120C", "toon:#D7261E", "toon:#F0503A", "toon:#FF8A70"
    shine = "glow:#FFEDE6"   # unlit, so the highlights stay bright like a wet reflection
    size = 1.2   # everything (sauce, bottle, boost zone) is 1.2x the 0.1 puddle
    # The bottle lies on its side behind the puddle, neck pointing into it (+Y, the way the sauce boosts you).
    bottle = pivot("Bottle", (0, -3.3 * size, 0.78 * size), rot=(-90, 0, 0))
    prof = [(0, 0), (0.65, 0), (0.76, 0.1), (0.78, 0.4), (0.78, 1.7), (0.7, 2.0), (0.42, 2.3), (0.3, 2.55), (0.3, 3.1),
            (0.36, 3.15), (0.36, 3.25), (0, 3.25)]
    lathe("Glass", [(r * size, z * size) for r, z in prof], mat=glass, segments=28, parent=bottle)
    lathe("Label", [(0.8 * size, 0.45 * size), (0.8 * size, 1.6 * size)], mat=label, segments=28, parent=bottle)
    # The cap popped off and rolled away.
    lathe("Cap", [(0, 0), (0.38 * size, 0), (0.4 * size, 0.55 * size), (0.3 * size, 0.65 * size), (0, 0.65 * size)],
          (-1.9 * size, -0.9 * size, 0.4 * size), rot=(90, 0, 35), mat=cap, segments=18)
    # A chilli printed on the label, on the side the card camera sees.
    pepper = pivot("Chilli", (0.81 * size, 0, 1.0 * size), rot=(0, 90, 0), parent=bottle)
    pepper.scale = (2.0, 2.0, 1.0)
    loft("ChilliBody", [(-0.45, 0, 0, 0.05), (-0.38, 0.1, 0.05, 0.03), (-0.1, 0.16, 0.06, 0.0), (0.2, 0.14, 0.05, -0.02),
                        (0.36, 0.08, 0.04, -0.06), (0.42, 0, 0, -0.1)], mat=chilli, segments=12, parent=pepper)
    box("ChilliStem", (0.12, 0.05, 0.05), (-0.5, 0, 0.06), rot=(0, -30, 0), mat=stem, bevel=0, parent=pepper)
    nose = Vector((0, -3.3 * size + 3.2 * size, 0))
    # Sauce glugging from the neck: a wobbling blob where it lands, with ripples spreading out.
    glug = pivot("Glug", (nose.x, nose.y + 0.2, 0.0), anim=dict(type="scale", min=(1, 1, 0.8), max=(1.12, 1.12, 1.2),
                                                                 speed=1.1, wrap="pingpong", curve="ease"))
    lathe("GlugBlob", [(0, 0), (0.6, 0.02), (0.42, 0.12), (0.26, 0.24), (0.1, 0.34), (0, 0.38)], mat=light, segments=20,
          parent=glug)
    sphere("GlugShine", 0.11, (-0.14, -0.18, 0.27), mat=shine, scale=(1, 0.6, 0.6), segments=10, rings=6, parent=glug)
    # The puddle: thin, irregular, darker at the edge and lighter towards the middle, with bright streaks.
    cy = 0.6 * size
    rnd = random.Random(5)
    puddle("Sauce", 2.9 * size, 2.7 * size, 0.03, (0, cy, 0), mat=deep, wobble=0.18, seed=11)
    puddle("SauceMid", 2.55 * size, 2.35 * size, 0.036, (0.05, cy + 0.05, 0), mat=sauce, wobble=0.18, seed=11)
    puddle("SaucePool", 1.6 * size, 1.4 * size, 0.042, (0.3, cy + 0.35, 0), rot=(0, 0, 25), mat=light, wobble=0.25, seed=3)
    puddle("Trail", 0.55, 1.0, 0.035, (0.1, nose.y - 0.2, 0), mat=sauce, wobble=0.15, seed=6)
    for i in range(4):
        x, y = rnd.uniform(-1.6, 1.6) * size, cy + rnd.uniform(-1.4, 1.4) * size
        turn = rnd.uniform(25, 35)
        for j, (length, off) in enumerate([(rnd.uniform(0.6, 1.0), 0.0), (rnd.uniform(0.3, 0.55), 0.26)]):
            sphere(f"Glint{i}_{j}", 1.0, (x - off * 0.5, y + off, 0.05), mat=shine, scale=(length, 0.08, 0.012),
                   rot=(0, 0, turn), segments=14, rings=4)
    # Chilli flakes and seeds floating in it.
    for i in range(14):
        x, y = rnd.uniform(-2.2, 2.2) * size, cy + rnd.uniform(-2.0, 2.0) * size
        flake = i % 3 != 0
        sphere(f"Fleck{i}", 1.0, (x, y, 0.046), mat=deep if flake else "toon:#F6D88A",
               scale=(rnd.uniform(0.08, 0.14), rnd.uniform(0.05, 0.1), 0.012), rot=(0, 0, rnd.uniform(0, 180)),
               segments=8, rings=4)
    for i, (cx, cyy, speed) in enumerate([(nose.x, nose.y + 0.2, 0.55), (nose.x, nose.y + 0.2, 0.4), (0.5, cy + 0.6, 0.3)]):
        ring = pivot(f"Ripple{i}", (cx, cyy, 0.05), anim=dict(type="scale", min=(0.2, 0.2, 1), max=(1.0, 1.0, 1), speed=speed,
                                                              curve="linear"))
        torus(f"RippleRing{i}", 1.2 if i < 2 else 1.7, 0.03, mat=ripple, seg=40, ring=4, parent=ring)
    for i in range(7):
        a = rnd.uniform(0, math.tau)
        puddle(f"Drop{i}", rnd.uniform(0.2, 0.4), rnd.uniform(0.18, 0.35), 0.03,
               (math.cos(a) * 3.3 * size, cy + math.sin(a) * 3.1 * size, 0.005 * i), mat=sauce, wobble=0.12, seed=40 + i,
               segments=24)
    collider("BottleCol", "box", (1.6 * size, 3.9 * size, 1.6 * size), (0, -3.3 * size + 1.9 * size, 0.78 * size))
    # Normal grip, but the car's drift spray and skid marks come out sauce red.
    collider("SauceCol", "box", (5.4 * size, 5.0 * size, 0.1), (0, cy, 0.0),
             zone={"type": "oil", "grip": 1.0, "steer": 1.0, "engine": 1.0, "tint": "#D7261E"})
    collider("Spicy", "box", (5.2 * size, 5.0 * size, 1.4 * size), (0, cy, 0.7 * size), trigger=True,
             zone={"type": "accel", "acceleration": 45, "setVelocity": True, "velocityOnEnter": 40})
    collider("SplashCol", "box", (5.8 * size, 5.4 * size, 3.0), (0, cy, 1.5), trigger=True,
             zone={"type": "splash", "colorA": sauce, "colorB": shine, "surfaceHeight": 0.05})
    return dict(name="The Hot Sauce Puddle", description=f"Extra spicy. {kw('Boosts', GREEN)} anything that drives through it.",
                rarity="Rare")


def skateboard():
    # Tail pressed to the ground, nose truck resting on a curb: a ramp rising towards +Y.
    tilt = 14
    board = pivot("Board", (0, 0, 1.04), rot=(tilt, 0, 0))
    box("Deck", (2.3, 7.6, 0.22), mat="primary", bevel=0.1, parent=board)
    box("Grip", (2.2, 7.4, 0.04), (0, 0, 0.13), mat=BLACK, bevel=0.02, parent=board)
    box("Truck", (1.8, 0.4, 0.3), (0, 2.7, -0.3), mat=METAL, bevel=0.05, parent=board)
    for side in (-1, 1):
        cyl(f"Wheel{side}", 0.42, 0.45, (side * 1.0, 2.7, -0.55), rot=(0, 90, 0), mat="secondary", verts=20, parent=board)
    box("Curb", (3.0, 1.6, 0.75), (0, 2.7, 0.375), mat="toon:#B9B9C4", bevel=0.08)
    collider("DeckCol", "box", (2.3, 7.6, 0.3), parent=board)
    collider("Push", "box", (2.3, 7.4, 1.2), (0, 0, 0.75), parent=board, trigger=True,
             zone={"type": "accel", "acceleration": 35, "setVelocity": True, "velocityOnEnter": 32})
    collider("CurbCol", "box", (3.0, 1.6, 0.75), (0, 2.7, 0.375))
    return dict(name="The Skateboard", description=f"Kickflip not included. {kw('Boosts', GREEN)} you up the ramp.",
                rarity="Uncommon")


# ---------------------------------------------------------------- killers

def lego_brick():
    red = "toon:#E3263F"
    box("Brick", (3.2, 1.6, 1.15), (0, 0, 0.575), mat=red, bevel=0.06)
    for ix in range(4):
        for iy in range(2):
            cyl(f"Stud{ix}{iy}", 0.26, 0.22, (-1.2 + ix * 0.8, -0.4 + iy * 0.8, 1.26), mat=red, verts=20, bevel=0.03)
    collider("BrickCol", "box", (3.2, 1.6, 1.15), (0, 0, 0.575))
    collider("Ouch", "box", (3.0, 1.4, 0.6), (0, 0, 1.45), trigger=True,
             zone={"type": "kill", "minSpeed": 6, "axis": "up"})
    return dict(name="The Lego Brick", description=f"You know exactly how this feels. {kw('Destroys', RED)} any vehicle that lands on it.",
                rarity="Rare")


def blender():
    shell, panel, chrome, glass = "toon:#3A3F4B", "toon:#23262E", METAL, "toon:#CFEFFF"
    rounded_rect("Base", (4.6, 4.6), 1.1, 1.2, mat=shell, bevel=0.12)
    lathe("TopPlate", [(2.15, 1.18), (2.2, 1.26), (1.9, 1.36), (0, 1.36)], mat=chrome, segments=40)
    for i, (x, y) in enumerate([(-1.7, -1.7), (1.7, -1.7), (1.7, 1.7), (-1.7, 1.7)]):
        cyl(f"Foot{i}", 0.32, 0.12, (x, y, 0.06), mat=panel, verts=16, bevel=0.03)
    # Control panel on the front face: speed dial and three buttons.
    face = pivot("Panel", (0, -2.31, 0.62))
    rounded_rect("PanelPlate", (3.4, 0.9), 0.3, 0.06, rot=(90, 0, 0), mat=panel, bevel=0.02, parent=face)
    cyl("Dial", 0.32, 0.18, (-1.05, -0.08, 0), rot=(90, 0, 0), mat=chrome, verts=24, bevel=0.04, parent=face)
    box("DialMark", (0.06, 0.06, 0.24), (-1.05, -0.18, 0.12), mat="toon:#E3263F", bevel=0, parent=face)
    for i, colour in enumerate(["toon:#3FA34D", "toon:#F2C14E", "toon:#E3263F"]):
        rounded_rect(f"Button{i}", (0.42, 0.3), 0.1, 0.14, (-0.15 + i * 0.6, -0.04, 0), rot=(90, 0, 0), mat=colour,
                     bevel=0.03, parent=face)
    cyl("Light", 0.07, 0.06, (1.45, -0.05, 0.25), rot=(90, 0, 0), mat="toon:#7CFF7C", verts=12, bevel=0, parent=face)
    cyl("Badge", 0.42, 0.05, (0, -2.33, 0.18), rot=(90, 0, 0), mat="primary", verts=24, bevel=0.01)
    # The jug's broken-off foot ring and the drive coupling.
    lathe("JugFoot", [(1.95, 1.34), (2.08, 1.34), (2.05, 1.62), (1.93, 1.62)], mat=glass, segments=40, closed=True)
    lathe("Hub", [(0.62, 1.34), (0.62, 1.5), (0.4, 1.62), (0.4, 1.8), (0.2, 1.88), (0, 1.88)], mat=chrome, segments=24)
    for i in range(6):
        a = math.radians(i * 60)
        box(f"Tooth{i}", (0.18, 0.22, 0.14), (0.62 * math.cos(a), 0.62 * math.sin(a), 1.45), rot=(0, 0, i * 60), mat=panel, bevel=0.02)
    spin = pivot("Blades", (0, 0, 1.75), anim=dict(type="rotation", axis="Z", min=0, max=360, speed=1.1, curve="linear"))
    blade = [(-2.8, 0, 0, 0.12), (-2.55, 0.16, 0.035, 0.1), (-1.6, 0.27, 0.04, 0.04), (-0.4, 0.3, 0.045, 0),
             (0.4, 0.3, 0.045, 0), (1.6, 0.27, 0.04, 0.04), (2.55, 0.16, 0.035, 0.1), (2.8, 0, 0, 0.12)]
    for i in range(2):
        arm = pivot(f"Arm{i}", rot=(0, 0, i * 90), parent=spin)
        loft(f"Blade{i}", blade, rot=(14 if i == 0 else -14, 0, 0), mat=chrome, segments=12, smooth_angle=30, parent=arm)
        collider(f"BladeKill{i}", "box", (5.6, 0.9, 0.7), parent=arm, trigger=True, zone=KILL)
    lathe("Nut", [(0.22, -0.05), (0.22, 0.12), (0.12, 0.2), (0, 0.2)], mat=chrome, segments=6, parent=spin, smooth_angle=20)
    collider("BaseCol", "box", (4.6, 4.6, 1.4), (0, 0, 0.7))
    return dict(name="The Blender", description=f"Will it blend? Yes. {kw('Destroys', RED)} any vehicle the blades touch.",
                rarity="Rare")


def cheese_grater():
    frustum_box("Body", (3.6, 3.6), (2.4, 2.4), 5.0, mat=METAL, bevel=0.06)
    torus("Handle", 0.9, 0.16, (0, 0, 5.6), rot=(90, 0, 0), mat=BLACK, seg=24, ring=8)
    lean = math.degrees(math.atan2(0.6, 5.0))
    for side in range(4):
        a = side * 90
        face = pivot(f"Face{side}", rot=(0, 0, a))
        for row in range(5):
            z = 0.6 + row * 0.9
            half = 1.8 - 0.6 * (z / 5.0)
            for col in range(3):
                x = (col - 1) * half * 0.6
                box(f"Tooth{side}_{row}_{col}", (0.38, 0.12, 0.22), (x, half + 0.02, z), rot=(lean, 0, 0),
                    mat=BLACK, bevel=0.02, parent=face)
        collider(f"Grate{side}", "box", (3.4, 0.6, 4.6), (0, 1.75, 2.4), parent=face, trigger=True,
                 zone={"type": "kill", "minSpeed": 12, "axis": "forward"})
    collider("Core", "box", (3.0, 3.0, 5.0), (0, 0, 2.5))
    return dict(name="The Cheese Grater", description=f"Grates cars. Finely. {kw('Destroys', RED)} anything that hits its sides too fast.",
                rarity="Uncommon")


def lava_lamp():
    cyl("Base", 1.3, 1.5, (0, 0, 0.75), mat="primary", verts=32, radius2=0.8)
    cyl("Glass", 0.85, 4.0, (0, 0, 3.5), mat="toon:#FF7AC8", verts=32, radius2=0.6, bevel=0.05)
    cyl("Cap", 0.62, 0.8, (0, 0, 5.9), mat="primary", verts=32, radius2=0.25)
    # Blobs already bulge through the glass at rest, and swell well past it.
    blobs = [((0.15, -0.1, 2.2), 0.8, 0.35), ((-0.2, -0.05, 3.5), 0.75, 0.5), ((0.1, -0.15, 4.75), 0.62, 0.6)]
    for i, (loc, radius, speed) in enumerate(blobs):
        blob = pivot(f"Blob{i}", loc, anim=dict(type="scale", min=(0.6, 0.6, 0.6), max=(1.7, 1.7, 1.4),
                                                speed=speed, wrap="pingpong", curve="ease"))
        sphere(f"Goo{i}", radius, mat="toon:#FF4A1C", scale=(1, 1, 1.15), parent=blob)
        collider(f"GooKill{i}", "sphere", radius=radius, parent=blob, trigger=True, zone=KILL)
    collider("BaseCol", "box", (2.4, 2.4, 1.5), (0, 0, 0.75))
    collider("GlassCol", "box", (1.5, 1.5, 4.0), (0, 0, 3.5))
    return dict(name="The Lava Lamp", description=f"Groovy. Lethal. Its blobs {kw('Destroy', RED)} any vehicle they touch.",
                rarity="Rare")


def hairbrush():
    pad, bristle = "toon:#2A2A30", "toon:#4A4E5A"
    rounded_rect("Head", (4.0, 3.2), 1.25, 0.42, mat="primary", bevel=0.14)
    rounded_rect("Cushion", (3.5, 2.7), 1.0, 0.16, (0, 0, 0.38), mat=pad, bevel=0.06)
    i = 0
    for ix in range(9):
        for iy in range(7):
            x, y = -1.68 + ix * 0.42, -1.26 + iy * 0.42 + (0.21 if ix % 2 else 0)
            if (x / 1.62) ** 2 + (y / 1.22) ** 2 > 1:
                continue
            cyl(f"Bristle{i}", 0.055, 0.95, (x, y, 1.0), mat=bristle, verts=8, bevel=0)
            sphere(f"Tip{i}", 0.11, (x, y, 1.5), mat=WHITE, segments=10, rings=6)
            i += 1
    run, rise = 5.4, 1.6
    tilt = math.degrees(math.atan2(rise, run))
    handle = pivot("Handle", (0, -1.6 - run / 2, rise / 2), rot=(tilt, 0, 0))
    length = run + 0.4
    stations = []
    for k in range(13):
        u = k / 12                      # 0 at the far end, 1 at the head
        x = -length / 2 + length * u
        width = 0.62 - 0.22 * u + 0.08 * math.sin(math.pi * min(1.0, u * 1.6))
        stations.append((x, width, 0.24, 0.0))
    # Rounded far end.
    stations = [(-length / 2 - 0.3, 0, 0, 0.0), (-length / 2 - 0.2, 0.42, 0.17, 0.0), (-length / 2 - 0.08, 0.56, 0.22, 0.0)] + stations
    loft("Grip", stations, rot=(0, 0, 90), mat="secondary", segments=20, flat_bottom=0.4, parent=handle)
    rounded_rect("GripInlay", (0.5, 2.6), 0.24, 0.06, (0, -1.0, 0.2), mat=pad, bevel=0.02, parent=handle)
    cyl("HangHole", 0.16, 0.05, (0, -2.45, 0.235), mat=pad, verts=16, bevel=0, parent=handle)
    collider("HandleCol", "box", (1.3, length, 0.45), parent=handle)
    collider("HeadCol", "box", (4.0, 3.2, 0.6), (0, 0, 0.3))
    collider("Bristles", "box", (3.9, 3.1, 1.1), (0, 0, 1.15), trigger=True, zone=KILL)
    return dict(name="The Hairbrush", description=f"Bad hair day. The bristles {kw('Destroy', RED)} vehicles, the handle is a ramp.",
                rarity="Uncommon")


# ---------------------------------------------------------------- animated

def revolving_door():
    radius, height = 4.0, 4.2
    cyl("Floor", radius, 0.15, (0, 0, 0.075), mat="toon:#B9B9C4", verts=40, bevel=0.03)
    torus("TopRing", radius, 0.18, (0, 0, height + 0.1), mat="primary")
    for i in range(4):
        a = math.radians(45 + i * 90)
        cyl(f"RingPost{i}", 0.14, height, (math.cos(a) * radius, math.sin(a) * radius, height / 2), mat="secondary", verts=12)
    spin = pivot("Door", (0, 0, 0), anim=dict(type="rotation", axis="Z", min=0, max=360, speed=0.18, curve="linear"))
    cyl("Post", 0.25, height + 0.2, (0, 0, height / 2 + 0.1), mat=METAL, parent=spin)
    for i in range(4):
        a = i * 90
        wing = pivot(f"Wing{i}", rot=(0, 0, a), parent=spin)
        box(f"Glass{i}", (0.12, radius - 0.35, height - 0.4), (0, radius / 2 + 0.05, height / 2), mat="toon:#BFE6FF",
            bevel=0.02, parent=wing)
        box(f"Frame{i}", (0.2, radius - 0.3, 0.2), (0, radius / 2 + 0.05, height - 0.25), mat=METAL, bevel=0.03, parent=wing)
        box(f"Handle{i}", (0.3, 0.1, 1.1), (0, radius - 0.7, 1.4), mat="secondary", bevel=0.03, parent=wing)
        collider(f"WingCol{i}", "box", (0.4, radius - 0.3, height - 0.3), (0, radius / 2 + 0.05, height / 2), parent=wing)
    return dict(name="The Revolving Door", description="After you. No, after YOU.", rarity="Uncommon")


def mini_golf_windmill():
    white, turf = "toon:#F4EFE6", "toon:#3FBF5A"
    box("Turf", (8.0, 10.0, 0.08), (0, -1.5, 0.04), mat=turf, bevel=0.02)
    box("WallL", (1.2, 5.0, 5.0), (-1.9, 0, 2.5), mat=white, bevel=0.06)
    box("WallR", (1.2, 5.0, 5.0), (1.9, 0, 2.5), mat=white, bevel=0.06)
    box("Lintel", (2.6, 5.0, 2.2), (0, 0, 3.9), mat=white, bevel=0.06)
    box("Trim", (5.2, 5.2, 0.3), (0, 0, 5.1), mat="primary", bevel=0.05)
    prism("Roof", 5.6, 5.6, 2.6, (0, 0, 5.25), mat="secondary")
    box("Door", (1.0, 0.1, 1.4), (-1.9, -2.55, 1.2), mat="toon:#8B4A2B", bevel=0.02)
    hub_z, front = 4.3, -2.75
    cyl("Axle", 0.3, 0.6, (0, front + 0.15, hub_z), rot=(90, 0, 0), mat=METAL, verts=16)
    spin = pivot("Sails", (0, front - 0.2, hub_z), anim=dict(type="rotation", axis="Y", min=0, max=360, speed=0.22, curve="linear"))
    for i in range(4):
        arm = pivot(f"SailArm{i}", rot=(0, i * 90, 0), parent=spin)
        box(f"Spar{i}", (0.25, 0.2, 4.2), (0, 0, 2.1), mat="toon:#8B4A2B", bevel=0.03, parent=arm)
        box(f"Sail{i}", (1.0, 0.1, 3.2), (0.65, 0, 2.5), mat=white, bevel=0.02, parent=arm)
        collider(f"SailCol{i}", "box", (1.6, 0.5, 4.2), (0.4, 0, 2.1), parent=arm)
    for name, size, loc in [("WallLCol", (1.2, 5.0, 5.0), (-1.9, 0, 2.5)), ("WallRCol", (1.2, 5.0, 5.0), (1.9, 0, 2.5)),
                            ("LintelCol", (2.6, 5.0, 2.2), (0, 0, 3.9)), ("RoofCol", (5.6, 5.6, 2.6), (0, 0, 6.4))]:
        collider(name, "box", size, loc)
    return dict(name="The Mini-Golf Windmill", description="Par 3. Time your shot through the sails.", rarity="Rare")


def metronome():
    wood = "toon:#8B4A2B"
    frustum_box("Body", (3.2, 2.2), (1.2, 1.0), 5.5, mat=wood, bevel=0.08)
    box("Face", (1.8, 0.08, 3.6), (0, -1.0, 2.4), rot=(-11, 0, 0), mat="toon:#F2E3C6", bevel=0.02)
    for i in range(7):
        box(f"Tick{i}", (0.5 - (i % 2) * 0.2, 0.05, 0.05), (0, -1.08 + i * 0.07, 1.3 + i * 0.45), rot=(-11, 0, 0),
            mat=BLACK, bevel=0)
    swing = pivot("Pendulum", (0, -1.35, 0.9), anim=dict(type="rotation", axis="Y", min=-40, max=40, speed=0.45,
                                                         wrap="pingpong", curve="ease"))
    box("Arm", (0.25, 0.2, 6.2), (0, 0, 3.1), mat=METAL, bevel=0.03, parent=swing)
    box("Weight", (1.1, 0.6, 0.9), (0, 0, 4.4), mat="secondary", bevel=0.12, parent=swing)
    collider("ArmCol", "box", (0.7, 0.7, 6.2), (0, 0, 3.1), parent=swing, zone=push(18, 4))
    collider("WeightCol", "box", (1.2, 0.8, 1.0), (0, 0, 4.4), parent=swing, zone=push(18, 4))
    collider("BodyCol", "box", (2.6, 1.9, 5.5), (0, 0, 2.75))
    return dict(name="The Metronome", description=f"Keep the beat. Its arm {kw('bounces', BLUE)} you out of time.",
                rarity="Uncommon")


def whack_a_mole():
    box("Cabinet", (7.2, 3.6, 1.6), (0, 0, 0.8), mat="primary", bevel=0.15)
    box("Panel", (7.0, 0.1, 1.0), (0, -1.82, 0.8), mat="secondary", bevel=0.03)
    for i in range(3):
        x = -2.3 + i * 2.3
        cyl(f"Hole{i}", 0.95, 0.06, (x, 0, 1.62), mat=BLACK, verts=24, bevel=0)
        start = 0.04 + i / 3  # each mole pops in its own third of the cycle
        keys = [[0, 0], [start, 0], [start + 0.06, 1], [start + 0.22, 1], [start + 0.28, 0], [1, 0]]
        mole = pivot(f"Mole{i}", (x, 0, 1.6), anim=dict(type="scale", min=(1, 1, 0.05), max=(1, 1, 1), speed=0.33,
                                                         curve=keys))
        cyl(f"MoleBody{i}", 0.75, 1.6, (0, 0, 0.8), mat="toon:#8A5A3C", verts=20, parent=mole)
        sphere(f"MoleHead{i}", 0.75, (0, 0, 1.6), mat="toon:#8A5A3C", parent=mole)
        sphere(f"Nose{i}", 0.2, (0, -0.72, 1.6), mat="toon:#FF8FB1", parent=mole)
        for side in (-1, 1):
            sphere(f"MoleEye{i}{side}", 0.11, (side * 0.3, -0.62, 1.95), mat=BLACK, parent=mole)
        collider(f"MoleCol{i}", "box", (1.5, 1.5, 2.35), (0, 0, 1.17), parent=mole, zone=launch_up(14))
    collider("CabinetCol", "box", (7.2, 3.6, 1.6), (0, 0, 0.8))
    return dict(name="The Whack-a-Mole", description=f"Bonk. Moles pop up and {kw('bounce', BLUE)} you into the air.",
                rarity="Rare")


def jack_in_the_box():
    box("Box", (3.0, 3.0, 3.0), (0, 0, 1.5), mat="pattern", bevel=0.12)
    for z in (0.1, 2.9):
        box(f"EdgeBand{z}", (3.1, 3.1, 0.22), (0, 0, z), mat="secondary", bevel=0.05)
    lid = pivot("LidHinge", (0, 1.5, 3.0), rot=(-115, 0, 0))
    box("Lid", (3.0, 3.0, 0.2), (0, -1.5, 0.1), mat="secondary", bevel=0.05, parent=lid)
    cyl("CrankShaft", 0.12, 0.8, (1.85, 0, 1.6), rot=(0, 90, 0), mat=METAL, verts=10)
    box("CrankArm", (0.15, 0.15, 0.9), (2.25, 0, 1.25), mat=METAL, bevel=0.03)
    sphere("CrankKnob", 0.22, (2.25, 0, 0.8), mat="toon:#E3263F")
    keys = [[0, 0], [0.55, 0], [0.6, 1.15], [0.64, 0.92], [0.68, 1], [0.9, 1], [1, 0]]
    jester = pivot("Jester", (0, 0, 2.9), anim=dict(type="scale", min=(1, 1, 0.04), max=(1, 1, 1), speed=0.25, curve=keys))
    for i in range(5):
        torus(f"Coil{i}", 0.55, 0.1, (0, 0, 0.3 + i * 0.4), mat=METAL, parent=jester, seg=20, ring=6)
    sphere("JesterHead", 0.95, (0, 0, 2.9), mat="toon:#FFE3C9", parent=jester)
    sphere("RedNose", 0.25, (0, -0.95, 2.85), mat="toon:#E3263F", parent=jester)
    for side in (-1, 1):
        sphere(f"JesterEye{side}", 0.12, (side * 0.35, -0.82, 3.15), mat=BLACK, parent=jester)
        cyl(f"Hat{side}", 0.45, 1.5, (side * 0.6, 0, 3.9), rot=(0, side * 35, 0), mat="primary" if side < 0 else "secondary",
            radius2=0.05, verts=16, parent=jester)
        sphere(f"Bell{side}", 0.2, (side * 1.05, 0, 4.5), mat="toon:#F2C14E", parent=jester)
    collider("JesterCol", "box", (2.0, 2.0, 2.2), (0, 0, 2.9), parent=jester, zone=bounce("velocity", 1.0, velocity=[0, 26, 0]))
    collider("BoxCol", "box", (3.0, 3.0, 3.0), (0, 0, 1.5))
    return dict(name="The Jack-in-the-Box", description=f"Surprise! Pops out and {kw('launches', GREEN)} anything above it.",
                rarity="Rare")


def turntable():
    wood = "toon:#7A4B2A"
    box("Plinth", (9.0, 9.0, 0.8), (0, 0, 0.4), mat=wood, bevel=0.12)
    for x in (-4.0, 4.0):
        for y in (-4.0, 4.0):
            cyl(f"Foot{x}{y}", 0.35, 0.15, (x, y, 0.0), mat=BLACK, verts=16, bevel=0.03)
    cyl("SpeedKnob", 0.4, 0.3, (-3.7, -3.7, 0.95), mat=METAL, verts=20, bevel=0.05)
    box("Switch", (0.8, 0.4, 0.2), (-2.6, -3.9, 0.9), mat="secondary", bevel=0.06)
    box("Trim", (9.1, 9.1, 0.12), (0, 0, 0.8), mat="primary", bevel=0.03)
    spin = pivot("Platter", (0, 0, 0.95), anim=dict(type="rotation", axis="Z", min=0, max=360, speed=0.45, curve="linear"))
    cyl("Record", 3.9, 0.2, mat=BLACK, verts=48, bevel=0.03, parent=spin)
    for i in range(4):
        torus(f"Groove{i}", 1.8 + i * 0.5, 0.025, (0, 0, 0.1), mat="toon:#44444C", parent=spin, seg=48, ring=4)
    cyl("Label", 1.1, 0.22, mat="secondary", verts=32, bevel=0.01, parent=spin)
    box("LabelStripe", (2.0, 0.3, 0.23), mat="primary", bevel=0, parent=spin)
    for i in range(8):
        a = i * 45
        r = 2.7
        collider(f"Fling{i}", "box", (2.0, 2.0, 0.9), (math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r, 0.5),
                 rot=(0, 0, a), parent=spin, trigger=True, zone={"type": "accel", "acceleration": 30})
    cyl("ArmBase", 0.55, 0.6, (3.6, 3.6, 1.1), mat=METAL, verts=20)
    arm = pivot("Tonearm", (3.6, 3.6, 1.45), rot=(0, 0, 135))
    box("ArmRod", (0.18, 4.2, 0.18), (0, 2.0, 0), mat=METAL, bevel=0.03, parent=arm)
    box("Needle", (0.45, 0.7, 0.3), (0, 4.1, -0.15), mat="secondary", bevel=0.05, parent=arm)
    collider("PlinthCol", "box", (9.0, 9.0, 0.8), (0, 0, 0.4))
    collider("RecordCol", "box", (7.6, 7.6, 0.25), (0, 0, 0.95))
    collider("ArmBaseCol", "box", (1.1, 1.1, 0.7), (3.6, 3.6, 1.15))
    return dict(name="The Turntable", description=f"Spin it back. {kw('Flings', GREEN)} vehicles off the edge.", rarity="Rare")


# ---------------------------------------------------------------- triggered and timed (new behaviours)
# Launch velocities are Unity local space: x right, y up, z forward (= Blender +Y).

def toaster():
    chrome, slot_black = METAL, "toon:#1E1E24"
    box("Body", (5.0, 3.2, 2.0), (0, 0, 1.0), mat=chrome, bevel=0.35)
    box("CrumbTray", (3.2, 0.12, 0.3), (0, -1.62, 0.25), mat=BLACK, bevel=0.04)
    for x in (-2.1, 2.1):
        for y in (-1.25, 1.25):
            cyl(f"Foot{x}{y}", 0.22, 0.12, (x, y, 0.02), mat=BLACK, verts=16, bevel=0.03)
    cyl("Dial", 0.28, 0.12, (2.55, -0.9, 1.0), rot=(0, 90, 0), mat="secondary", verts=20, bevel=0.03)
    for side in (-1, 1):
        box(f"Panel{side}", (0.08, 2.6, 1.3), (side * 2.52, 0, 1.0), mat="primary", bevel=0.03)
    for i, y in enumerate((-0.6, 0.6)):
        box(f"Slot{i}", (4.0, 0.55, 0.06), (0, y, 2.0), mat=slot_black, bevel=0)
        pop = pivot(f"Toast{i}", (0, y, 0), motion=dict(channel=0, type="position", rest=(0, 0, 0), active=(0, 0, 2.2),
                                                       startDelay=0.45, inTime=0.1, holdTime=1.2, outTime=0.6))
        box(f"Bread{i}", (3.6, 0.35, 2.2), (0, 0, 1.1), mat="toon:#E0A458", bevel=0.15, parent=pop)
        box(f"Crust{i}", (3.7, 0.3, 0.25), (0, 0, 2.2), mat="toon:#B5742E", bevel=0.1, parent=pop)
    lever = pivot("Lever", (2.7, 0, 0), motion=dict(channel=0, type="position", rest=(0, 0, 0), active=(0, 0, -0.8),
                                                    inTime=0.08, holdTime=0.37, outTime=0.08))
    box("LeverKnob", (0.5, 0.7, 0.35), (0, 0, 1.6), mat=BLACK, bevel=0.1, parent=lever)
    for sign in (-1, 1):
        ramp = pivot(f"Ramp{sign}", (0, sign * 3.2, 1.0), rot=(-sign * 32, 0, 0))
        box(f"RampTop{sign}", (4.6, 3.8, 0.25), mat="toon:#B9B9C4", bevel=0.06, parent=ramp)
        collider(f"RampCol{sign}", "box", (4.6, 3.8, 0.3), parent=ramp)
    collider("BodyCol", "box", (5.0, 3.2, 2.0), (0, 0, 1.0))
    collider("Ding", "box", (4.6, 3.0, 1.4), (0, 0, 2.7), trigger=True, zone={"type": "plate", "channel": 0, "cooldown": 2.5})
    collider("Pop", "box", (4.6, 3.0, 1.4), (0, 0, 2.7), trigger=True,
             zone={"type": "launch", "velocity": [0, 26, 0], "setVelocity": True, "delay": 0.45, "cooldown": 2.5})
    return dict(name="The Toaster", description=f"Pops when done. You are done. {kw('Launches', GREEN)} anything on top.",
                rarity="Rare")


SLING_BAND_Z = 1.4


def slingshot():
    wood = "toon:#A0643C"
    for side in (-1, 1):
        cyl(f"Prong{side}", 0.32, 4.6, (side * 2.3, 0, 2.3), rot=(0, side * 8, 0), mat=wood, verts=16, bevel=0.06)
        sphere(f"Tip{side}", 0.4, (side * 2.6, 0, 4.6), mat=wood)
        cyl(f"Wrap{side}", 0.36, 0.5, (side * 2.15, 0, SLING_BAND_Z), mat="toon:#E3263F", verts=16, bevel=0.03)
        box(f"Stake{side}", (1.1, 1.1, 0.5), (side * 2.2, 0, 0.25), mat="toon:#6B4A2B", bevel=0.12)
        collider(f"ProngCol{side}", "box", (0.7, 0.7, 4.6), (side * 2.35, 0, 2.3))
    # The band itself is built and stretched at runtime by SlingshotZone (it follows the car).
    # Long trigger so a car stays inside while it's stretched back up to maxStretch either side.
    collider("Sling", "box", (4.4, 18.0, 3.0), (0, 0, SLING_BAND_Z), trigger=True,
             zone={"type": "slingshot", "anchorLeft": [-2.15, 0, 0], "anchorRight": [2.15, 0, 0], "halfWidth": 1.8,
                   "maxStretch": 7, "spring": 9, "launchBase": 14, "launchPerMetre": 5, "launchUp": 4})
    return dict(name="The Slingshot",
                description=f"Drive into the band from either side. It stretches until you stop, then {kw('flings', GREEN)} you back.",
                rarity="Rare")


def slingshot_card_extras():
    """Render-only band for the card art (in game it's drawn by SlingshotZone)."""
    anchor_x, pouch_y = 2.15, -2.75   # stretched towards the card camera (-Y)
    length = math.hypot(anchor_x, pouch_y)
    angle = math.degrees(math.atan2(anchor_x, -pouch_y))   # turns the box's long Y axis towards the pouch
    for side in (-1, 1):
        box(f"CardRubber{side}", (0.2, length, 0.22), (side * anchor_x / 2, pouch_y / 2, SLING_BAND_Z), rot=(0, 0, -side * angle),
            mat="toon:#E3263F", bevel=0.05)
    box("CardPouch", (1.0, 0.45, 1.1), (0, pouch_y, SLING_BAND_Z), mat="toon:#6B3E26", bevel=0.15)


def shaken_soda():
    glass, label, foam, cap = "toon:#3FBF5A", "toon:#E3263F", "toon:#FFF3D6", "toon:#E3263F"
    bottle = pivot("Bottle", (0, 2.2, 1.1), rot=(62, 0, 0))  # neck aimed at the puddle
    profile = [(0.0, -1.8), (0.55, -1.8), (0.95, -1.72), (1.1, -1.45), (1.12, -1.2), (1.05, -0.95), (1.12, -0.7),
               (1.12, 0.6), (1.05, 0.85), (1.12, 1.05), (1.08, 1.35), (0.85, 1.8), (0.55, 2.2), (0.46, 2.45),
               (0.46, 2.75), (0.56, 2.78), (0.56, 2.86), (0.4, 2.9), (0.0, 2.9)]
    lathe("Glass", profile, mat=glass, segments=28, parent=bottle)
    cyl("Label", 1.15, 1.25, (0, 0, -0.05), mat=label, verts=28, bevel=0, parent=bottle)
    cyl("LabelStripe", 1.16, 0.18, (0, 0, -0.05), mat=WHITE, verts=28, bevel=0, parent=bottle)
    for i in range(5):
        a = math.radians(i * 72)
        sphere(f"Petal{i}", 0.42, (0.55 * math.cos(a), 0.55 * math.sin(a), -1.72), mat=glass, scale=(1, 1, 0.45),
               segments=12, rings=6, parent=bottle)
    collider("BottleCol", "box", (2.2, 2.2, 3.6), parent=bottle)
    # The cap that popped off, lying in the foam.
    lathe("Cap", [(0, 0), (0.5, 0), (0.52, 0.05), (0.52, 0.4), (0.44, 0.46), (0, 0.46)], (1.9, -2.6, 0.0), rot=(0, 12, 30),
          mat=cap, segments=18)
    rnd = random.Random(5)
    for i in range(9):
        a, r = rnd.uniform(0, math.tau), rnd.uniform(0.4, 1.7)
        sphere(f"Foam{i}", rnd.uniform(0.55, 0.9), (math.cos(a) * r, -1.0 + math.sin(a) * r, 0.02), mat=foam,
               scale=(1, 1, 0.22), segments=16, rings=6)
    cyl("Puddle", 2.2, 0.06, (0, -1.0, 0.03), mat=foam, verts=32, bevel=0.02)
    cycle = 0.18
    keys = [[0, 0.02], [0.68, 0.02], [0.72, 1.1], [0.76, 1], [0.9, 1], [0.95, 0.02], [1, 0.02]]
    # The column's scale and the launch window share one clock cycle, so the spray and the push line up.
    spray = pivot("Spray", (0, -1.0, 0), anim=dict(type="scale", min=(1, 1, 0.0), max=(1, 1, 1), speed=cycle, curve=keys))
    column = [(0.75, 0), (0.6, 2.0), (0.7, 4.5), (0.95, 7.0), (1.25, 8.6), (0.9, 9.3), (0, 9.5)]
    lathe("Column", column, mat=foam, segments=20, parent=spray)
    for i, (x, z, r) in enumerate([(0.75, 1.8, 0.35), (-0.8, 3.4, 0.45), (0.85, 5.0, 0.4), (-0.95, 6.6, 0.55),
                                   (1.0, 8.0, 0.6), (-0.7, 9.0, 0.7), (0.3, 9.6, 0.65)]):
        sphere(f"Fizz{i}", r, (x, 0.25 * (-1) ** i, z), mat="toon:#C8F0FF", segments=16, rings=8, parent=spray)
    blast = pivot("Blast", (0, -1.0, 0), timed=dict(speed=cycle, start=0.70, end=0.93))
    collider("Erupt", "box", (3.4, 3.4, 3.0), (0, 0, 1.5), parent=blast, trigger=True,
             zone={"type": "launch", "velocity": [0, 32, 0], "setVelocity": True, "cooldown": 1.5})
    return dict(name="The Shaken Soda", description=f"Do not open. Erupts every few seconds, {kw('launching', GREEN)} anything above it.",
                rarity="Rare")


def mousetrap():
    wood, metal, cheese = "toon:#D9A066", METAL, "toon:#FFD43B"
    box("Board", (4.2, 8.0, 0.35), (0, 0, 0.175), mat=wood, bevel=0.08)
    box("TriggerPlate", (1.8, 1.4, 0.12), (0, 2.4, 0.41), mat=metal, bevel=0.03)
    prism("Cheese", 1.4, 1.0, 0.9, (0, 2.4, 0.47), rot=(0, 0, 90), mat=cheese)
    for side in (-1, 1):
        for i in range(3):
            torus(f"Spring{side}{i}", 0.3, 0.07, (side * 0.9 + side * i * 0.18, 0, 0.55), rot=(0, 90, 0), mat=metal, seg=16, ring=6)
    snap = pivot("Snap", (0, 0, 0.5), motion=dict(channel=0, type="rotation", axis="X", rest=0, active=-180,
                                                  startDelay=0.12, inTime=0.12, holdTime=1.4, outTime=1.2, arm=True))
    for side in (-1, 1):
        box(f"BarSide{side}", (0.14, 3.4, 0.14), (side * 1.7, -1.7, 0.05), mat=metal, bevel=0.03, parent=snap)
    box("BarEnd", (3.54, 0.14, 0.14), (0, -3.4, 0.05), mat=metal, bevel=0.03, parent=snap)
    collider("SnapKill", "box", (3.6, 3.5, 1.4), (0, -1.75, 0.3), parent=snap, trigger=True, zone=KILL)
    collider("BoardCol", "box", (4.2, 8.0, 0.35), (0, 0, 0.175))
    collider("Bait", "box", (3.8, 3.4, 1.4), (0, 2.1, 1.0), trigger=True, zone={"type": "plate", "channel": 0, "cooldown": 4.0})
    return dict(name="The Mousetrap", description=f"Cheese sold separately. Snaps shut and {kw('Destroys', RED)} whoever goes for the cheese.",
                rarity="Rare")


def garden_rake():
    green, wood, wood_dark = "toon:#3FA34D", "toon:#B5773F", "toon:#94592B"
    box("Head", (4.6, 0.4, 0.3), (0, 4.0, 0.25), mat=green, bevel=0.1)
    for i in range(12):
        x = -2.15 + i * (4.3 / 11)
        cyl(f"Tine{i}", 0.07, 0.75, (x, 4.0, 0.62), mat=METAL, verts=8, bevel=0)
        sphere(f"TineTip{i}", 0.09, (x, 3.94, 1.0), mat=METAL, scale=(1, 1.6, 1), segments=8, rings=4)
    swing = pivot("Swing", (0, 3.75, 0.25), motion=dict(channel=0, type="rotation", axis="X", rest=0, active=-75,
                                                       inTime=0.12, holdTime=0.5, outTime=0.8, arm=True))
    cyl("Ferrule", 0.25, 0.9, (0, -0.45, 0.03), rot=(90, 0, 0), mat=METAL, verts=16, bevel=0.03, parent=swing)
    cyl("Handle", 0.19, 7.0, (0, -4.4, 0.03), rot=(90, 0, 0), mat=wood, verts=16, bevel=0.03, parent=swing)
    for k in range(4):
        cyl(f"Grain{k}", 0.195, 0.06, (0, -2.4 - k * 1.3, 0.03), rot=(90, 0, 0), mat=wood_dark, verts=16, bevel=0, parent=swing)
    cyl("Grip", 0.26, 1.3, (0, -7.6, 0.03), rot=(90, 0, 0), mat=green, verts=16, bevel=0.08, parent=swing)
    sphere("GripCap", 0.27, (0, -8.25, 0.03), mat=green, scale=(1, 0.5, 1), segments=16, rings=8, parent=swing)
    collider("Smack", "box", (1.6, 8.0, 1.6), (0, -4.0, 0.3), parent=swing, trigger=True,
             zone={"type": "launch", "velocity": [0, 24, 0], "setVelocity": True, "cooldown": 1.5})
    collider("HeadCol", "box", (4.6, 0.45, 0.3), (0, 4.0, 0.2))
    collider("Tines", "box", (4.6, 1.6, 1.2), (0, 4.0, 0.8), trigger=True, zone={"type": "plate", "channel": 0, "cooldown": 2.0})
    return dict(name="The Garden Rake", description=f"A classic. Step on it and the handle {kw('launches', GREEN)} you.",
                rarity="Uncommon")


def pizza_cutter():
    cheese, crust, pepperoni = "toon:#F7C548", "toon:#D9963E", "toon:#C0392B"
    cyl("Pizza", 7.0, 0.22, (0, 0, 0.11), mat=cheese, verts=48, bevel=0.05)
    torus("Crust", 7.0, 0.35, (0, 0, 0.25), mat=crust, seg=48, ring=10)
    rnd = random.Random(9)
    for i in range(12):
        a, r = rnd.uniform(0, 2 * math.pi), rnd.uniform(1.0, 6.0)
        cyl(f"Pepperoni{i}", 0.6, 0.08, (math.cos(a) * r, math.sin(a) * r, 0.25), mat=pepperoni, verts=16, bevel=0.02)
    slide = pivot("Slide", (0, 0, 0), anim=dict(type="position", min=(-5.0, 0, 0), max=(5.0, 0, 0), speed=0.2,
                                                wrap="pingpong", curve="ease"))
    roll = pivot("Roll", (0, 0, 2.45), parent=slide, anim=dict(type="rotation", axis="Y", min=0, max=-260, speed=0.2,
                                                               wrap="pingpong", curve="ease"))
    cyl("Blade", 2.2, 0.16, rot=(90, 0, 0), mat=METAL, verts=40, bevel=0.04, parent=roll)
    cyl("Hub", 0.45, 0.5, rot=(90, 0, 0), mat=BLACK, verts=16, parent=roll)
    for i in range(4):
        box(f"Spoke{i}", (0.2, 0.18, 1.6), (0, 0, 0), rot=(0, i * 45, 0), mat="toon:#9AA0A8", bevel=0.02, parent=roll)
    handle = pivot("Handle", (0, 0, 2.45), rot=(-30, 0, 0), parent=slide)
    box("Fork", (0.35, 0.8, 1.2), (0, 0, 0.6), mat=METAL, bevel=0.05, parent=handle)
    box("Grip", (0.7, 0.7, 3.2), (0, 0, 2.6), mat="primary", bevel=0.25, parent=handle)
    collider("Cut", "box", (4.4, 0.7, 4.4), (0, 0, 2.45), parent=slide, trigger=True, zone=KILL)
    return dict(name="The Pizza Cutter", description=f"One slice per lap. Rolls back and forth, {kw('Destroying', RED)} anything in its path.",
                rarity="Rare")


def magnifying_glass():
    frame, handle = "primary", "toon:#3A2A20"
    torus("Rim", 2.9, 0.35, (0, 0, 3.2), rot=(90, 0, 0), mat=frame, seg=40, ring=12)
    cyl("Lens", 2.75, 0.06, (0, 0, 3.2), rot=(90, 0, 0), mat="toon:#BFE6FF", verts=40, bevel=0)
    sphere("Glint", 0.35, (-1.2, -0.06, 4.4), mat=WHITE, scale=(1, 0.2, 0.6))
    stick = pivot("Stick", (2.3, 0, 1.2), rot=(0, 50, 0))
    cyl("Handle", 0.42, 3.2, (0, 0, -0.4), mat=handle, verts=16, bevel=0.1, parent=stick)
    cyl("Collar", 0.55, 0.5, (0, 0, 1.3), mat="secondary", verts=16, parent=stick)
    box("Stand", (2.2, 1.6, 0.4), (3.3, 0, 0.2), mat=BLACK, bevel=0.1)
    collider("StandCol", "box", (2.2, 1.6, 0.4), (3.3, 0, 0.2))
    collider("Magnify", "box", (4.0, 1.4, 4.0), (0, 0, 2.6), trigger=True, zone={"type": "grow", "growScale": 2.2, "duration": 8})
    return dict(name="The Magnifying Glass", description=f"Objects may appear larger. Makes any vehicle that drives through it {kw('huge', PURPLE)}.",
                rarity="Rare")


def toilet():
    porcelain, shade, water = "toon:#F7F7FA", "toon:#DADBE3", "toon:#5BC0FF"
    oval = (1, 1.15, 1)
    # Bowl and pedestal as one turned piece, slightly oval like the real thing.
    lathe("Bowl", [(1.05, 0.0), (1.25, 0.08), (1.05, 0.3), (0.95, 0.9), (1.2, 1.35), (1.75, 1.75), (2.05, 2.05),
                   (2.1, 2.2), (1.85, 2.24), (1.6, 2.05), (0, 1.95)], mat=porcelain, segments=40, scale=oval)
    cyl("Water", 1.55, 0.04, (0, 0, 2.06), mat=water, verts=40, bevel=0)
    torus("Seat", 1.8, 0.24, (0, 0, 2.38), mat="primary", seg=40, ring=12)
    swirl = pivot("Swirl", (0, 0, 2.1), anim=dict(type="rotation", axis="Z", min=0, max=360, speed=0.25, curve="linear"))
    # Whole turns only, so snapping back to rest after the flush is invisible.
    flush = pivot("Flush", (0, 0, 0), parent=swirl, motion=dict(channel=0, type="rotation", axis="Z", rest=0, active=-1080,
                                                                 inTime=0.9, holdTime=0.0, outTime=0.01))
    for i in range(3):
        arm = pivot(f"SwirlArm{i}", rot=(0, 0, i * 120), parent=flush)
        box(f"Streak{i}", (0.2, 1.1, 0.03), (0.6, 0.3, 0), rot=(0, 0, 35), mat=WHITE, bevel=0, parent=arm)
    # The tank sits just behind the bowl's rim (rim back edge y=2.42, tank front y=2.5), and the lid stands on the
    # rim leaning 3 degrees back, so its back face just meets the tank lid's front edge instead of passing through.
    lid = pivot("LidHinge", (0, 2.1, 2.42), rot=(-93, 0, 0))
    lathe("Lid", [(0, 0), (1.85, 0), (1.95, 0.08), (1.85, 0.18), (0, 0.2)], (0, -1.95, 0), mat="primary", segments=40,
          parent=lid)
    tank_y = 3.2
    rounded_rect("Tank", (3.4, 1.4), 0.35, 2.7, (0, tank_y, 1.3), mat=porcelain, bevel=0.12)
    rounded_rect("TankLid", (3.6, 1.6), 0.4, 0.25, (0, tank_y, 4.0), mat=porcelain, bevel=0.08)
    cyl("Handle", 0.1, 0.7, (-1.25, tank_y - 0.82, 3.55), rot=(0, 90, 0), mat=METAL, verts=12)
    cyl("HandleBoss", 0.2, 0.08, (-1.25, tank_y - 0.73, 3.55), rot=(90, 0, 0), mat=METAL, verts=16, bevel=0.02)
    box("Pipe", (0.5, 1.2, 0.5), (0, 2.2, 1.05), mat=shade, bevel=0.15)
    collider("PedestalCol", "box", (2.4, 2.6, 1.5), (0, 0, 0.75))
    collider("TankCol", "box", (3.4, 1.4, 4.0), (0, tank_y, 2.0))
    for i, x in enumerate((-2.15, 2.15)):
        collider(f"RimCol{i}", "box", (0.5, 4.2, 0.9), (x, 0, 1.95))
    # No ramp of its own (build one with other cards). The flush zone covers the bowl from just above the road to
    # well over the rim and reaches the tank's face, so driving into the front, landing in the bowl or hitting
    # the tank all flush you.
    collider("Bowl", "box", (4.4, 4.4, 5.5), (0, 0.3, 3.25), trigger=True, zone={"type": "toilet", "delay": 0.3, "channel": 0})
    return dict(name="The Toilet", rarity="Unique", full_art=True, partner="SewerExit",
                description=f"Flush and reflect. Place its {kw('Sewer Exit', PURPLE)} anywhere: vehicles that drive in come out there.")


def sewer_exit():
    concrete, dark, pipe = "toon:#B9B9C4", "toon:#14201A", "toon:#4F8F5A"
    # Concrete headwall with the pipe mouth facing -Y (the front), where flushed cars shoot out.
    rounded_rect("Wall", (4.6, 1.2), 0.25, 4.0, (0, 0.9, 0), mat=concrete, bevel=0.1)
    box("WallCap", (4.9, 1.5, 0.3), (0, 0.9, 4.1), mat=concrete, bevel=0.08)
    mouth = pivot("Pipe", (0, 0, 1.9), rot=(90, 0, 0))
    # A hollow pipe (no end caps) with a dark plate deep inside: nothing shares a depth with anything else,
    # so the opening can't flicker.
    lathe("Tube", [(1.55, -0.3), (1.55, 1.4), (1.75, 1.45), (1.75, 1.75), (1.35, 1.75), (1.35, -0.3)],
          mat=pipe, segments=32, parent=mouth, closed=True)
    cyl("Dark", 1.37, 0.06, (0, 0, 0.0), mat=dark, verts=32, bevel=0, parent=mouth)
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        sphere(f"Rivet{i}", 0.09, (1.62 * math.cos(a), 1.62 * math.sin(a), 1.76), mat=METAL, scale=(1, 1, 0.6),
               segments=8, rings=4, parent=mouth)
    for k, x in enumerate((-0.75, 0.0, 0.75)):
        box(f"Grate{k}", (0.1, 2.5, 0.1), (x, 0, 1.64), mat=METAL, bevel=0, parent=mouth)
    collider("PipeCol", "box", (3.6, 2.0, 3.6), (0, -0.5, 1.9))
    collider("WallCol", "box", (4.6, 1.2, 4.2), (0, 0.9, 2.1))
    return dict(name="The Sewer Exit", rarity="Unique", partner_only=True,
                description="Where the Toilet sends you. Flushed vehicles shoot out of here.")


# ---------------------------------------------------------------- road pieces and zones (batch 3)

ASPHALT, LINE_WHITE, LINE_YELLOW = "toon:#3A3D46", "toon:#F4F4F4", "toon:#F2C14E"


def long_ramp():
    width, length, height = 3.6, 9.0, 2.4
    wedge("Ramp", width, length, height, mat="pattern", bevel=0.08)
    angle = math.atan2(height, length)
    for i in range(4):
        t = 0.2 + i * 0.2
        y, z = -length / 2 + length * t, height * t + 0.02
        chevron = pivot(f"Chevron{i}", (0, y, z), rot=(math.degrees(angle), 0, 0))
        for side in (-1, 1):
            box(f"ChevronArm{i}{side}", (1.1, 0.22, 0.04), (side * 0.42, 0, 0), rot=(0, 0, side * 35), mat=WHITE, bevel=0.01,
                parent=chevron)
    for side in (-1, 1):
        wedge(f"Rail{side}", 0.2, length, height + 0.25, (side * (width / 2 + 0.1), 0, 0), mat="secondary", bevel=0.04)
    ramp_colliders("Ramp", width, length, height)
    return dict(name="The Long Ramp", description=f"Like the cheese, but twice as long. {kw('Launches', GREEN)} you further.",
                rarity="Common")


def long_road():
    width, length, thick = 7.0, 26.0, 0.3
    box("Deck", (width, length, thick), (0, 0, thick / 2), mat=ASPHALT, bevel=0.06)
    for i in range(9):
        box(f"Dash{i}", (0.25, 1.6, 0.02), (0, -length / 2 + 1.6 + i * 2.9, thick + 0.01), mat=LINE_WHITE, bevel=0)
    for side in (-1, 1):
        box(f"Edge{side}", (0.2, length - 0.4, 0.02), (side * (width / 2 - 0.35), 0, thick + 0.01), mat=LINE_YELLOW, bevel=0)
    for end in (-1, 1):
        # Lips rise towards the deck (a wedge rises along +Y, so the +Y end is turned round).
        wedge(f"Lip{end}", width, 1.6, thick, (0, end * (length / 2 + 0.8), 0), rot=(0, 0, 180 if end > 0 else 0),
              mat=ASPHALT, bevel=0.03)
    collider("DeckCol", "box", (width, length, thick), (0, 0, thick / 2))
    for end in (-1, 1):
        angle = math.degrees(math.atan2(thick, 1.6))
        collider(f"LipCol{end}", "box", (width, 1.62, 0.12), (0, end * (length / 2 + 0.8), thick / 2 - 0.04),
                 rot=(-end * angle, 0, 0))
    return dict(name="The Long Road", description="A nice long flat bit of road. Build whatever you like on it.",
                rarity="Common")


def curved_road():
    r_in, r_out, sweep, thick = 9.0, 16.0, 90.0, 0.3
    mid = (r_in + r_out) / 2
    # Arc centred so the middle of the road sits on the obstacle's origin.
    ox, oy = -mid * math.cos(math.radians(45)), -mid * math.sin(math.radians(45))
    arc_slab("Deck", r_in, r_out, sweep, thick, (ox, oy, thick), mat=ASPHALT, segments=36)
    arc_slab("EdgeIn", r_in + 0.25, r_in + 0.45, sweep, 0.02, (ox, oy, thick + 0.02), mat=LINE_YELLOW, segments=36, bevel=0)
    arc_slab("EdgeOut", r_out - 0.45, r_out - 0.25, sweep, 0.02, (ox, oy, thick + 0.02), mat=LINE_YELLOW, segments=36, bevel=0)
    for i in range(12):
        arc_slab(f"Dash{i}", mid - 0.12, mid + 0.12, 4.0, 0.02, (ox, oy, thick + 0.02), start_deg=2 + i * 7.5,
                 mat=LINE_WHITE, segments=3, bevel=0)
    steps = 9
    chord = 2 * r_out * math.sin(math.radians(sweep / steps / 2)) * 1.08
    for i in range(steps):
        a = (i + 0.5) * sweep / steps
        x, y = ox + math.cos(math.radians(a)) * mid, oy + math.sin(math.radians(a)) * mid
        collider(f"DeckCol{i}", "box", (r_out - r_in, chord, thick), (x, y, thick / 2), rot=(0, 0, a))
    return dict(name="The Curved Road", description="A quarter turn of road. Make the track go where you want.",
                rarity="Common")


def low_gravity_zone():
    # 24 m across and 20 m tall; 15% of normal gravity inside (factor 0.85 of the map's gravity cancelled).
    radius = 12.0
    cyl("Pad", radius, 0.2, (0, 0, 0.1), mat="toon:#2B2F5A", verts=64, bevel=0.05)
    torus("Neon", radius - 0.25, 0.2, (0, 0, 0.25), mat="mat:PurpleUnlit", seg=96, ring=8)
    for i in range(8):
        a = math.radians(i * 45)
        cyl(f"Emitter{i}", 0.6, 0.9, (math.cos(a) * (radius - 1.0), math.sin(a) * (radius - 1.0), 0.45), mat=METAL, verts=20)
    sphere("Dome", radius, (0, 0, 0), mat="mat:Bubble", scale=(1, 1, 0.85), segments=64, rings=32)
    drift = pivot("Drift", (0, 0, 8.0), anim=dict(type="rotation", axis="Z", min=0, max=360, speed=0.04, curve="linear"))
    rnd = random.Random(21)
    for i in range(8):
        a = math.radians(i * 45 + rnd.uniform(-15, 15))
        r = rnd.uniform(3.0, 8.0)
        sphere(f"Rock{i}", rnd.uniform(0.5, 1.1), (math.cos(a) * r, math.sin(a) * r, rnd.uniform(-3.0, 3.0)),
               mat="toon:#9AA0A8", scale=(1, 0.8, 0.7), segments=12, rings=8, parent=drift)
    collider("Field", "box", (radius * 2, radius * 2, 20.0), (0, 0, 10.0), trigger=True, zone={"type": "gravity", "gravityFactor": 0.85})
    return dict(name="The Low Gravity Zone", description=f"One small step for car. Everything inside {kw('floats', PURPLE)}.",
                rarity="Rare")


def drawbridge():
    width, ramp_len, height, landing, gap = 6.0, 5.0, 2.5, 2.0, 6.0
    half = gap / 2
    for end in (-1, 1):
        y_ramp = end * (half + landing + ramp_len / 2)
        wedge(f"Ramp{end}", width, ramp_len, height, (0, y_ramp, 0), rot=(0, 0, 180 if end > 0 else 0), mat=ASPHALT)
        box(f"Landing{end}", (width, landing, height), (0, end * (half + landing / 2), height / 2), mat="toon:#B9B9C4", bevel=0.08)
        box(f"Stripe{end}", (width, 0.35, 0.03), (0, end * (half + 0.2), height + 0.01), mat="secondary", bevel=0)
        collider(f"LandingCol{end}", "box", (width, landing, height), (0, end * (half + landing / 2), height / 2))
        # The ramp leads up towards the gap from both ends.
        slope = pivot(f"RampCols{end}", (0, y_ramp, 0), rot=(0, 0, 180 if end > 0 else 0))
        ramp_colliders(f"Ramp{end}", width, ramp_len, height, parent=slope)
    box("Housing", (1.6, gap + 1.0, 1.4), (width / 2 + 3.6, 0, height + 0.6), mat="primary", bevel=0.15)
    box("HousingBase", (1.0, gap, height), (width / 2 + 3.6, 0, height / 2), mat="toon:#B9B9C4", bevel=0.08)
    collider("HousingCol", "box", (1.6, gap + 1.0, height + 1.3), (width / 2 + 3.6, 0, (height + 1.3) / 2))
    # In for most of the cycle, slides out sideways under the housing, waits, slides back.
    keys = [[0, 0], [0.5, 0], [0.6, 1], [0.85, 1], [0.95, 0], [1, 0]]
    deck = pivot("Deck", (0, 0, height), anim=dict(type="position", min=(0, 0, 0), max=(width + 1.5, 0, 0), speed=1 / 7.0,
                                                    curve=keys))
    box("DeckTop", (width, gap + 0.3, 0.45), (0, 0, -0.225), mat="toon:#8B6A4A", bevel=0.06, parent=deck)
    for i in range(6):
        box(f"Plank{i}", (width - 0.2, 0.08, 0.03), (0, -half + 0.5 + i * 1.0, 0.01), mat="toon:#6B4E33", bevel=0, parent=deck)
    for side in (-1, 1):
        box(f"Hazard{side}", (0.25, gap + 0.3, 0.5), (side * (width / 2 - 0.12), 0, -0.2), mat="pattern", bevel=0.03, parent=deck)
    collider("DeckCol", "box", (width, gap + 0.3, 0.45), (0, 0, -0.225), parent=deck)
    return dict(name="The Drawbridge", description=f"Mind the gap. Its bridge {kw('slides away', ORANGE)} every few seconds.",
                rarity="Rare")


def shock_mine():
    box("Base", (1.3, 1.3, 0.25), (0, 0, 0.125), mat=BLACK, bevel=0.1)
    cyl("Plate", 0.55, 0.18, (0, 0, 0.32), mat="toon:#FFC83D", verts=32, bevel=0.04)
    for i in range(4):
        a = i * 90 + 45
        box(f"Stripe{i}", (0.18, 0.75, 0.05), (math.cos(math.radians(a)) * 0.0, 0, 0.27), rot=(0, 0, a), mat=BLACK, bevel=0)
    bolt = pivot("Bolt", (0, 0, 0.45), rot=(0, 0, 20))
    box("BoltA", (0.14, 0.5, 0.06), (0.06, 0.12, 0), rot=(0, 0, -25), mat="toon:#4FD3FF", bevel=0.01, parent=bolt)
    box("BoltB", (0.14, 0.5, 0.06), (-0.06, -0.12, 0), rot=(0, 0, -25), mat="toon:#4FD3FF", bevel=0.01, parent=bolt)
    sphere("Light", 0.09, (0.45, 0.45, 0.3), mat="mat:RedBlinkingLight", segments=12, rings=8)
    # Launch height goes with speed squared: 52 m/s is about 3x the height of the old 30 m/s.
    collider("Zap", "box", (1.6, 1.6, 1.0), (0, 0, 0.5), trigger=True,
             zone={"type": "launch", "velocity": [0, 52, 0], "setVelocity": True, "cooldown": 1.0, "channel": 0})
    pivot("ShockFx", (0, 0, 0.2), effect=dict(channel=0, kind="shock", consume=True))
    return dict(name="The Shock Mine", description=f"Not deadly, just shocking. {kw('Launches', GREEN)} any vehicle sky-high. Single use.",
                rarity="Uncommon")


def teleport_grenade():
    body = pivot("Grenade", (0, 0, 0.62), rot=(0, 12, 0))
    sphere("Shell", 0.55, mat="toon:#7A3CFF", scale=(1, 1, 1.2), parent=body)
    torus("Band", 0.56, 0.07, (0, 0, 0), mat="mat:PurpleUnlit", parent=body, seg=32, ring=8)
    for z in (-0.3, 0.3):
        torus(f"Groove{z}", 0.5, 0.04, (0, 0, z), mat="toon:#4A1FA8", parent=body, seg=32, ring=6)
    cyl("Cap", 0.22, 0.25, (0, 0, 0.72), mat=METAL, verts=16, parent=body)
    box("Lever", (0.12, 0.2, 0.75), (0.25, 0, 0.55), rot=(0, 20, 0), mat=METAL, bevel=0.03, parent=body)
    torus("Pin", 0.15, 0.03, (-0.22, 0, 0.82), rot=(90, 0, 0), mat=METAL, parent=body, seg=16, ring=6)
    collider("Warp", "box", (1.6, 1.6, 1.5), (0, 0, 0.75), trigger=True, zone={"type": "spawn", "cooldown": 1.5, "channel": 0})
    pivot("WarpFx", (0, 0, 0.3), effect=dict(channel=0, kind="teleport", consume=True))
    return dict(name="The Teleport Grenade", description=f"Back to square one. {kw('Teleports', PURPLE)} any vehicle that hits it to the start. Single use.",
                rarity="Uncommon")


def shock_minefield():
    return dict(name="The Shock Minefield", rarity="Legendary", full_art=True, carrier="LandMineScatter", keep_carrier=True,
                scatter="ShockMine", scatter_count=10,
                description=f"{kw('Scatters', BLUE)} 10 shock mines on the {kw('road tiles', BLUE)} and {kw('obstacles', ORANGE)}.")


def grenade_shower():
    return dict(name="The Grenade Shower", rarity="Legendary", full_art=True, carrier="LandMineScatter", keep_carrier=True,
                scatter="TeleportGrenade", scatter_count=10,
                description=f"{kw('Scatters', BLUE)} 10 teleport grenades on the {kw('road tiles', BLUE)} and {kw('obstacles', ORANGE)}.")


def reverse_road():
    return dict(name="The Reverse", rarity="UltraRare", full_art=True, carrier="SurfaceSwapAsphalt_M", keep_carrier=True,
                surface="reverse",
                description=f"Turns {kw('road tiles', BLUE)} and {kw('obstacles', ORANGE)} into {kw('reverse road', PURPLE)}: "
                            f"steering is flipped on it, even in the air.")


def scatter_card_scene(piece_id, card_id, count=10):
    """Render-only collection: copies of a piece's meshes scattered for a full-art card."""
    import bpy
    from mathutils import Matrix
    src = bpy.data.collections[f"SS_{piece_id}"]
    begin(card_id)
    target = bpy.data.collections[f"SS_{card_id}"]
    rnd = random.Random(8)
    meshes = [o for o in src.all_objects if o.type == "MESH" and not o.hide_render]
    for i in range(count):
        a, r = rnd.uniform(0, 2 * math.pi), (rnd.uniform(1.2, 3.4) if i else 0.0)
        s = rnd.uniform(0.85, 1.15)
        placement = (Matrix.Translation((math.cos(a) * r, math.sin(a) * r, 0))
                     @ Matrix.Rotation(rnd.uniform(0, 2 * math.pi), 4, "Z") @ Matrix.Diagonal((s, s, s, 1)))
        for o in meshes:
            dup = o.copy()
            dup.parent = None
            target.objects.link(dup)
            dup.matrix_world = placement @ o.matrix_world


def reverse_card_scene(card_id="ReverseCard"):
    """Render-only: a purple road patch with crossed steering arrows and a confused car."""
    begin(card_id)
    box("Road", (8.0, 8.0, 0.4), (0, 0, -0.2), mat="toon:#6B2FB8", bevel=0.15)
    for i in range(4):
        box(f"Dash{i}", (0.3, 1.0, 0.02), (0, -3 + i * 2, 0.01), mat="toon:#E8C8FF", bevel=0)
    for side in (-1, 1):
        arrow = pivot(f"Arrow{side}", (side * 2.2, -0.5, 0.6), rot=(0, 0, side * 35))
        box(f"Shaft{side}", (0.35, 2.6, 0.2), mat=WHITE, bevel=0.06, parent=arrow)
        prism(f"Head{side}", 1.2, 0.2, 0.9, (0, 1.3, -0.1), rot=(-90, 0, 0), mat=WHITE, parent=arrow)
    car = pivot("Car", (0, 0.6, 0.55), rot=(0, 0, 25))
    box("CarBody", (1.4, 2.4, 0.6), mat="toon:#E3263F", bevel=0.2, parent=car)
    box("CarCabin", (1.2, 1.1, 0.55), (0, -0.2, 0.55), mat="toon:#BFE6FF", bevel=0.15, parent=car)
    for x in (-0.72, 0.72):
        for y in (-0.8, 0.8):
            cyl(f"Wheel{x}{y}", 0.3, 0.26, (x, y, -0.3), rot=(0, 90, 0), mat=BLACK, verts=16, parent=car)
    for i, (x, y) in enumerate([(-0.6, 0.9), (0.2, 1.5), (0.8, 0.7)]):
        sphere(f"Swirl{i}", 0.18, (x, y + 0.6, 1.6 + i * 0.25), mat="toon:#FFD43B")


def toilet_card_extras():
    """Render-only props for the Toilet's full-art card: a car diving into the bowl and a splash.
    Call after export_obstacle (they are never exported); returns the names to hide on the card render."""
    # Into the Toilet's collection whatever was built last, so the card render (and its clean-up) finds them.
    globals()["_current"] = bpy.data.collections["SS_Toilet"]
    car = pivot("CardCar", (0.1, -0.2, 3.3), rot=(-62, 0, 24))
    box("CardCarBody", (1.2, 2.0, 0.55), mat="toon:#E3263F", bevel=0.18, parent=car)
    box("CardCarCabin", (1.0, 0.95, 0.5), (0, -0.2, 0.5), mat="toon:#BFE6FF", bevel=0.15, parent=car)
    for x in (-0.62, 0.62):
        for y in (-0.68, 0.68):
            cyl(f"CardWheel{x}{y}", 0.28, 0.24, (x, y, -0.28), rot=(0, 90, 0), mat=BLACK, verts=16, parent=car)
    rnd = random.Random(4)
    for i in range(18):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(1.5, 2.4)
        sphere(f"CardSplash{i}", rnd.uniform(0.09, 0.22), (math.cos(a) * r, math.sin(a) * r * 0.85, 2.4 + rnd.uniform(0, 1.4)),
               mat="toon:#7FD3FF", scale=(1, 1, 1.5))
    return []


# ---------------------------------------------------------------- batch 5 (0.2.0)

def baby_oil():
    plastic, cap, label, band = "toon:#FFD3E3", "toon:#F06BA8", WHITE, "toon:#F06BA8"
    deep, oil, light, ripple = "toon:#D48A2C", "toon:#EBAA44", "toon:#F7CB6E", "toon:#FADB94"
    shine = "glow:#FFF8E6"   # unlit, so the highlights stay bright like a wet reflection
    k = 1.45   # bottle scale
    # The bottle lies tipped forward, nose down, glugging oil onto the road. Oval cross-section like the real thing.
    bottle = pivot("Bottle", (0.9, 4.6, 0.75 * k), rot=(96, 0, -18))
    oval = (1, 0.62, 1)
    prof = [(0, 0), (0.9, 0), (1.08, 0.12), (1.12, 0.5), (1.1, 2.6), (1.0, 3.1), (0.7, 3.5), (0.42, 3.7), (0.42, 3.85), (0, 3.85)]
    lathe("Body", [(r * k, z * k) for r, z in prof], mat=plastic, segments=36, scale=oval, parent=bottle)
    lathe("Label", [(1.13 * k, 0.75 * k), (1.13 * k, 2.45 * k)], mat=label, segments=36, scale=oval, parent=bottle)
    lathe("Band", [(1.14 * k, 1.95 * k), (1.14 * k, 2.25 * k)], mat=band, segments=36, scale=oval, parent=bottle)
    lathe("Cap", [(0, 3.8 * k), (0.5 * k, 3.8 * k), (0.52 * k, 4.3 * k), (0.38 * k, 4.45 * k), (0, 4.45 * k)], mat=cap,
          segments=24, parent=bottle)
    box("Spout", (0.4, 0.18, 0.5), (0, -0.42, 4.6 * k), mat=cap, bevel=0.05, parent=bottle)
    for i in range(3):
        sphere(f"Bubble{i}", (0.13 - i * 0.03) * k, ((0.4 - i * 0.25) * k, 0.7 * k, (1.3 + i * 0.4) * k), mat=WHITE,
               segments=10, rings=6, parent=bottle)
    # Oil glugging out of the spout: a wobbling blob where it lands, with ripples spreading out.
    nose = Vector((0.9, 4.6, 0.75 * k)) + Vector((-0.307, -0.946, -0.1045)) * (4.5 * k)
    glug = pivot("Glug", (nose.x, nose.y, 0.0), anim=dict(type="scale", min=(1, 1, 0.8), max=(1.12, 1.12, 1.2), speed=1.3,
                                                         wrap="pingpong", curve="ease"))
    lathe("GlugBlob", [(0, 0), (0.65, 0.02), (0.45, 0.12), (0.28, 0.26), (0.12, 0.38), (0, 0.42)], mat=light, segments=20,
          parent=glug)
    sphere("GlugShine", 0.12, (-0.15, -0.2, 0.3), mat=shine, scale=(1, 0.6, 0.6), segments=10, rings=6, parent=glug)
    # The slick: thin, irregular, darker at the edge and lighter towards the middle, with bright streaks.
    # `size` scales the whole spill around its centre `cy`; the colliders below use the same numbers.
    size, cy = 1.4, -5.0
    rnd = random.Random(21)
    puddle("Slick", 4.9 * size, 4.4 * size, 0.03, (0, cy, 0), mat=deep, wobble=0.2, seed=4)
    puddle("SlickMid", 4.3 * size, 3.8 * size, 0.036, (0.1, cy + 0.1, 0), mat=oil, wobble=0.2, seed=4)
    puddle("SlickPool", 2.9 * size, 2.4 * size, 0.042, (0.4 * size, cy + 0.4 * size, 0), rot=(0, 0, 20), mat=light,
           wobble=0.25, seed=9)
    puddle("Trail", 1.3, 2.4, 0.035, (nose.x + 0.4, nose.y - 1.2, 0), rot=(0, 0, 15), mat=oil, wobble=0.15, seed=2)
    # Reflections: long glints in pairs, like a window caught in the oil.
    for i in range(6):
        x, y = rnd.uniform(-2.4, 2.4) * size, cy + rnd.uniform(-2.2, 2.0) * size
        turn = rnd.uniform(25, 35)
        for j, (length, off) in enumerate([(rnd.uniform(0.9, 1.6), 0.0), (rnd.uniform(0.4, 0.8), 0.32)]):
            sphere(f"Glint{i}_{j}", 1.0, (x - off * 0.5, y + off, 0.05), mat=shine, scale=(length, 0.09, 0.012),
                   rot=(0, 0, turn), segments=14, rings=4)
    for i in range(10):
        x, y = rnd.uniform(-2.8, 2.8) * size, cy + rnd.uniform(-2.6, 2.4) * size
        sphere(f"Fleck{i}", 1.0, (x, y, 0.048), mat=shine, scale=(rnd.uniform(0.08, 0.16),) * 2 + (0.01,), segments=10, rings=4)
    # Ripples spreading from where the oil lands and across the pool (each ring loops at its own pace).
    for i, (cx, cyy, speed) in enumerate([(nose.x, nose.y, 0.55), (nose.x, nose.y, 0.42), (0.6, cy + 0.6, 0.3),
                                          (-1.6, cy - 1.4, 0.24)]):
        ring = pivot(f"Ripple{i}", (cx, cyy, 0.05), anim=dict(type="scale", min=(0.2, 0.2, 1), max=(1.0, 1.0, 1), speed=speed,
                                                              curve="linear"))
        torus(f"RippleRing{i}", 1.6 if i < 2 else 2.4, 0.035, mat=ripple, seg=40, ring=4, parent=ring)
    for i in range(9):
        a = rnd.uniform(0, math.tau)
        puddle(f"Drop{i}", rnd.uniform(0.25, 0.45), rnd.uniform(0.2, 0.4), 0.03,
               (math.cos(a) * 5.6 * size, cy + math.sin(a) * 5.0 * size, 0), mat=oil, wobble=0.12, seed=30 + i, segments=24)
    centre = Vector((0.9, 4.6, 0.75 * k)) + Vector((-0.307, -0.946, -0.1045)) * (2.2 * k)
    collider("BottleCol", "box", (2.2 * k, 4.6 * k, 1.4 * k), (centre.x, centre.y, 0.7 * k), rot=(0, 0, -18))
    # Thin solid slab carrying the oil surface: the car reads its grip from whatever it's standing on.
    collider("SlickCol", "box", (9.2 * size, 8.6 * size, 0.1), (0, cy, 0.0), zone={"type": "oil", "grip": 0.06, "steer": 0.35, "engine": 0.6})
    # Droplets kicked up by every car on the slick (visual only, on every machine).
    collider("SplashCol", "box", (9.6 * size, 9.0 * size, 3.0), (0, cy, 1.5), trigger=True,
             zone={"type": "splash", "colorA": oil, "colorB": shine, "surfaceHeight": 0.05})
    return dict(name="The Baby Oil", description=f"Gentle on skin. Leaves a slick with {kw('no grip', ORANGE)}: good luck steering.",
                rarity="Uncommon")


def vacuum():
    shell, dark, metal, hose, gloom = "primary", "toon:#2A2D35", METAL, "toon:#3A3F4B", "toon:#0C0D10"
    # Canister at the back, shuddering when it catches something.
    can = pivot("Canister", (0, 5.0, 0))
    can.scale = (1.35, 1.35, 1.35)   # sized to match the big floor nozzle
    shudder = pivot("Shudder", parent=can, motion=dict(channel=0, type="scale", rest=(1, 1, 1), active=(1.08, 1.08, 1.12),
                                                       inTime=0.15, holdTime=0.55, outTime=0.25))
    lathe("Body", [(0, 0.25), (1.75, 0.25), (1.95, 0.55), (2.0, 1.6), (1.85, 2.3), (1.4, 2.65), (0, 2.75)], mat=shell,
          segments=40, parent=shudder)
    torus("Bumper", 1.98, 0.16, (0, 0, 0.5), mat=dark, seg=40, ring=8, parent=shudder)
    lathe("Lid", [(0, 2.6), (1.45, 2.6), (1.6, 2.72), (1.3, 3.0), (0, 3.05)], mat=dark, segments=40, parent=shudder)
    torus("CarryHandle", 0.75, 0.13, (0, 0, 3.0), rot=(90, 0, 0), mat=dark, seg=24, ring=8, parent=shudder)
    cyl("PowerButton", 0.22, 0.12, (0.95, -0.6, 2.82), rot=(-20, 0, 0), mat="toon:#E3263F", verts=16, bevel=0.03, parent=shudder)
    for k in range(5):
        box(f"Vent{k}", (0.9, 0.08, 0.1), (0, 1.97, 1.0 + k * 0.22), mat=dark, bevel=0.02, parent=shudder)
    for x in (-1.2, 1.2):
        cyl(f"Wheel{x}", 0.42, 0.3, (x, 0.6, 0.42), rot=(0, 90, 0), mat=dark, verts=20, bevel=0.06, parent=can)
    cyl("Inlet", 0.42, 0.5, (0, -1.95, 1.2), rot=(90, 0, 0), mat=dark, verts=20, bevel=0.05, parent=can)
    # Ribbed hose looping from the canister inlet up and over to the wand.
    p0, p1, p2 = Vector((0, 2.4, 1.62)), Vector((0.6, 1.1, 6.2)), Vector((0, -0.6, 4.8))
    for k in range(24):
        t = k / 23
        p = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2
        d = (2 * (1 - t) * (p1 - p0) + 2 * t * (p2 - p1)).normalized()
        rot = d.to_track_quat("Z", "Y").to_euler()
        torus(f"HoseRib{k}", 0.34, 0.11, tuple(p), rot=tuple(math.degrees(a) for a in rot), mat=hose, seg=16, ring=6)
    # Metal wand down to the floor nozzle's roof.
    wand_top, wand_bottom = Vector((0, -0.6, 4.8)), Vector((0, -3.4, 2.75))
    mid = (wand_top + wand_bottom) / 2
    dirn = (wand_top - wand_bottom)
    rot = dirn.normalized().to_track_quat("Z", "Y").to_euler()
    cyl("Wand", 0.24, dirn.length, tuple(mid), rot=tuple(math.degrees(a) for a in rot), mat=metal, verts=16, bevel=0.02)
    cyl("Grip", 0.32, 0.8, tuple(wand_top), rot=tuple(math.degrees(a) for a in rot), mat=dark, verts=16, bevel=0.06)
    cyl("Neck", 0.5, 0.5, (0, -3.4, 2.8), mat=dark, verts=20, bevel=0.06)
    # The floor nozzle: big enough to swallow a car. Open at the front (-Y) and underneath, with a dark chamber
    # inside: roof, two cheeks and a back. Mouth plane y=-6.0, chamber back y=-3.2, roof underside z=2.2.
    hx, front, back, roof = 3.2, -6.0, -2.8, 2.2
    depth, cy = back - front, (front + back) / 2
    rounded_rect("Roof", (2 * hx, depth), 0.8, 0.5, (0, cy, roof), mat=shell, bevel=0.14)
    rounded_rect("RoofStripe", (4.2, 0.5), 0.2, 0.05, (0, cy - 0.6, roof + 0.5), mat="secondary", bevel=0.02)
    for side in (-1, 1):
        box(f"Cheek{side}", (0.6, depth, roof), (side * (hx - 0.3), cy, roof / 2), mat=shell, bevel=0.14)
        box(f"LipSide{side}", (0.34, 0.34, roof + 0.1), (side * (hx - 0.25), front - 0.05, roof / 2), mat=dark, bevel=0.1)
        cyl(f"Wheel{side}", 0.38, 0.3, (side * (hx - 0.2), back - 0.25, 0.38), rot=(0, 90, 0), mat=dark, verts=20, bevel=0.06)
    box("Back", (2 * hx - 1.2, 0.4, roof), (0, back - 0.2, roof / 2), mat=shell, bevel=0.1)
    box("LipTop", (2 * hx + 0.1, 0.34, 0.34), (0, front - 0.05, roof + 0.05), mat=dark, bevel=0.1)
    # Dark lining just inside the walls (never flush with them, so nothing flickers).
    inner = hx - 0.62
    box("ThroatRoof", (2 * inner, depth - 0.45, 0.04), (0, cy + 0.2, roof - 0.05), mat=gloom, bevel=0)
    box("ThroatBack", (2 * inner, 0.04, roof - 0.1), (0, back - 0.45, roof / 2), mat=gloom, bevel=0)
    for side in (-1, 1):
        box(f"ThroatSide{side}", (0.04, depth - 0.45, roof - 0.1), (side * inner, cy + 0.2, roof / 2), mat=gloom, bevel=0)
    box("ThroatFloor", (2 * inner, depth - 0.45, 0.02), (0, cy + 0.2, 0.012), mat=gloom, bevel=0)
    # Brush bristles hanging from the top lip.
    for k in range(22):
        x = -inner + 0.15 + k * (2 * inner - 0.3) / 21
        box(f"Bristle{k}", (0.1, 0.1, 0.32), (x, front + 0.1, roof - 0.18), mat="toon:#F2C14E", bevel=0)
    # Suction lines being drawn into the mouth (they never collide).
    for k in range(6):
        x = -2.0 + k * 0.8
        flow = pivot(f"Flow{k}", (x, -11.0, 0.5 + 0.35 * (k % 3)), anim=dict(type="position", min=(0, -5.0, 0), max=(0, 4.6, 0),
                                                                               speed=0.8 + 0.11 * k, curve="linear"))
        sphere(f"Streak{k}", 1.0, mat=WHITE, scale=(0.08, 0.9, 0.08), segments=10, rings=6, parent=flow)
    collider("CanisterCol", "box", (5.4, 5.4, 4.0), (0, 5.0, 2.0))
    collider("RoofCol", "box", (2 * hx, depth, 0.5), (0, cy, roof + 0.25))
    for side in (-1, 1):
        collider(f"CheekCol{side}", "box", (0.6, depth, roof), (side * (hx - 0.3), cy, roof / 2))
    collider("BackCol", "box", (2 * hx, 0.4, roof), (0, back - 0.2, roof / 2))
    # Suction from 14 m out in front, through the mouth, to the back of the chamber. Unity space, node-local:
    # `mouth` is the chamber's middle (0, 0.6, -4.0) as seen from this node at (0, 1.7, -11.5). Inside the mouth
    # (escapeDistance) there's no escape; the catch comes once the car is right inside (catchDistance).
    collider("Suction", "box", (8.0, 17.4, 3.4), (0, -11.5, 1.7), trigger=True,
             zone={"type": "vacuum", "mouth": [0, -1.1, 7.5], "pull": 28, "pullSpeedFar": 5, "pullSpeed": 13,
                   "reach": 16, "catchDistance": 1.0, "escapeDistance": 2.1, "escapeFactor": 0.55,
                   "holdTime": 1.0, "velocity": [0, 5, -42], "cooldown": 2.0, "channel": 0})
    return dict(name="The Vacuum", description=f"Sucks. {kw('Pulls', BLUE)} vehicles in, then {kw('spits them out', GREEN)} at full blast.",
                rarity="Rare")


def wind_tunnel():
    shell, rib, floor, stripe, dark = "toon:#D9DEE6", "toon:#F2C14E", ASPHALT, LINE_YELLOW, "toon:#2A2D35"
    length, r_in, r_out, wall = 26.0, 4.2, 4.6, 1.5
    half = length / 2
    # Straight side walls topped by a half-round roof; arc_slab sweeps an arch, extruded along the tunnel.
    for side in (-1, 1):
        box(f"Wall{side}", (r_out - r_in, length, wall), (side * (r_in + r_out) / 2, 0, wall / 2), mat=shell, bevel=0.04)
    # arc_slab extrudes down its local Z, which the 90 degree turn points along +Y: start at the front.
    roof = arc_slab("Roof", r_in, r_out, 180, length, (0, -half, wall), mat=shell, segments=32, bevel=0.04)
    roof.rotation_euler = (math.radians(90), 0, 0)
    for k, y in enumerate((-half + 0.4, -half / 3, half / 3, half - 0.4)):
        ring = arc_slab(f"Rib{k}", r_out - 0.05, r_out + 0.3, 180, 0.8, (0, y - 0.4, wall), mat=rib, segments=32, bevel=0.05)
        ring.rotation_euler = (math.radians(90), 0, 0)
        for side in (-1, 1):
            box(f"RibLeg{k}{side}", (0.35, 0.8, wall), (side * (r_out + 0.12), y, wall / 2), mat=rib, bevel=0.04)
    # Hazard chevrons on the entrance rib.
    for k in range(7):
        a = math.radians(12 + k * 26)
        box(f"Hazard{k}", (0.5, 0.06, 0.32), ((r_out + 0.15) * math.cos(a), -half - 0.03, wall + (r_out + 0.15) * math.sin(a)),
            rot=(0, -math.degrees(a) + 90, 0), mat=dark, bevel=0)
    box("Floor", (2 * r_in, length, 0.04), (0, 0, 0.02), mat=floor, bevel=0)
    for k in range(6):
        y = -half + 3 + k * 4.2
        prism(f"Arrow{k}", 1.6, 0.04, 1.2, (0, y, 0.045), rot=(-90, 0, 0), mat=stripe, bevel=0)
    # Two big wall fans near the exit, blowing back down the tunnel.
    for side in (-1, 1):
        x = side * (r_in - 1.25)
        lathe(f"FanHousing{side}", [(1.1, -0.6), (1.2, -0.5), (1.2, 0.5), (1.0, 0.6), (1.0, -0.45)],
              (x, half - 2.2, 2.6), rot=(90, 0, 0), mat=dark, segments=32, closed=True)
        spin = pivot(f"Fan{side}", (x, half - 2.2, 2.6), rot=(90, 0, 0),
                     anim=dict(type="rotation", axis="Z", min=0, max=360, speed=1.6, curve="linear"))
        for b in range(5):
            blade = pivot(f"FanBlade{side}_{b}", rot=(0, 0, b * 72), parent=spin)
            box(f"Blade{side}_{b}", (0.42, 0.85, 0.06), (0, 0.55, 0), rot=(0, 25, 0), mat=METAL, bevel=0.03, parent=blade)
        sphere(f"FanHub{side}", 0.3, (x, half - 2.5, 2.6), mat=rib, scale=(1, 0.7, 1), segments=16, rings=8)
        for g in range(4):
            torus(f"FanGuard{side}_{g}", 0.3 + g * 0.26, 0.03, (x, half - 2.85, 2.6), rot=(90, 0, 0), mat=METAL, seg=32, ring=4)
    # Gusts streaming back towards the entrance (never collide).
    for k in range(10):
        x = -3.0 + (k % 5) * 1.5
        z = 1.0 + (k // 5) * 2.0 + 0.3 * (k % 2)
        gust = pivot(f"Gust{k}", (x, 0, z), anim=dict(type="position", min=(0, half - 1, 0), max=(0, -half - 2, 0),
                                                      speed=0.55 + 0.07 * k, curve="linear"))
        sphere(f"GustStreak{k}", 1.0, mat=WHITE, scale=(0.06, 1.4, 0.06), segments=10, rings=6, parent=gust)
    for side in (-1, 1):
        collider(f"FanCol{side}", "box", (2.4, 1.3, 2.4), (side * (r_in - 1.25), half - 2.2, 2.6))
    # Colliders: walls and a ring of slabs following the arch.
    for side in (-1, 1):
        collider(f"WallCol{side}", "box", (r_out - r_in + 0.2, length, wall), (side * (r_in + r_out) / 2, 0, wall / 2))
    r = (r_in + r_out) / 2
    for k in range(6):
        a = 15 + k * 30
        ar = math.radians(a)
        chord = 2 * r * math.sin(math.radians(15)) + 0.3
        collider(f"ArchCol{k}", "box", (chord, length, 0.5), (r * math.cos(ar), 0, wall + r * math.sin(ar)), rot=(0, -(a + 90), 0))
    # The wind itself. Unity space: the way through is +Z (Blender +Y), so cars enter at the front (-Y).
    collider("Wind", "box", (2 * r_in, length, wall + r_in - 0.3), (0, 0, (wall + r_in - 0.3) / 2), trigger=True,
             zone={"type": "wind", "direction": [0, 0, 1], "wind": 45, "passSpeed": 30})
    return dict(name="The Wind Tunnel", description=f"Floor it. Too slow and the fans {kw('blow you back out', BLUE)}.",
                rarity="Rare")


def speed_bump():
    yellow, black, white, red = "toon:#F2C14E", "toon:#22242A", WHITE, "toon:#E3263F"
    width, half_depth, height = 9.0, 0.85, 0.34
    # Striped hump: one loft per stripe so the stripes follow the curve; the outer ends round off.
    n = 9
    for i in range(n):
        x0, x1 = -width / 2 + i * width / n, -width / 2 + (i + 1) * width / n
        stations = [(x0, half_depth, height, 0), (x1, half_depth, height, 0)]
        if i == 0:
            stations = [(x0 - 0.2, 0, 0, 0), (x0 - 0.12, half_depth * 0.7, height * 0.7, 0)] + stations
        if i == n - 1:
            stations = stations + [(x1 + 0.12, half_depth * 0.7, height * 0.7, 0), (x1 + 0.2, 0, 0, 0)]
        loft(f"Stripe{i}", stations, rot=(0, 0, 0), mat=yellow if i % 2 == 0 else black, segments=24, flat_bottom=1.0)
    for i in range(n - 1):
        x = -width / 2 + (i + 1) * width / n
        box(f"CatsEye{i}", (0.16, 0.22, 0.08), (x, -0.25, height - 0.02), rot=(18, 0, 0), mat=white, bevel=0.02)
    # Speed limit sign and a speed camera on a post beside the road.
    post = pivot("Post", (width / 2 + 1.3, 0.4, 0))
    cyl("Pole", 0.12, 4.2, (0, 0, 2.1), mat=METAL, verts=12, bevel=0.02, parent=post)
    cyl("SignBack", 0.95, 0.08, (0, -0.1, 3.6), rot=(90, 0, 0), mat=white, verts=40, bevel=0.02, parent=post)
    torus("SignRing", 0.82, 0.11, (0, -0.16, 3.6), rot=(90, 0, 0), mat=red, seg=40, ring=8, parent=post)
    digits("Limit", "20", 0.75, (0, -0.17, 3.6), mat=black, parent=post)
    rounded_rect("Camera", (0.7, 1.1), 0.12, 0.7, (0, 0.15, 2.0), mat=yellow, bevel=0.06, parent=post)
    cyl("Lens", 0.2, 0.12, (0, -0.42, 2.38), rot=(90, 0, 0), mat=black, verts=20, bevel=0.03, parent=post)
    flash = pivot("Flash", (0, -0.5, 2.38), parent=post, motion=dict(channel=0, type="scale", rest=(0.01, 0.01, 0.01),
                                                                     active=(1, 1, 1), inTime=0.05, holdTime=0.15, outTime=0.3))
    sphere("FlashGlow", 0.55, mat="glow:#FFFFFF", segments=16, rings=8, parent=flash)
    # A shallow tent of colliders over the hump, and the speed check above it.
    for side in (-1, 1):
        collider(f"Slope{side}", "box", (width, half_depth + 0.1, 0.16), (0, side * half_depth / 2, height / 2 - 0.08),
                 rot=(-side * math.degrees(math.atan2(height, half_depth)), 0, 0))
    collider("PostCol", "box", (0.4, 0.4, 4.2), (width / 2 + 1.3, 0.4, 2.1))
    collider("Check", "box", (width, 2.0, 2.6), (0, 0, 1.3), trigger=True,
             zone={"type": "speedbump", "minSpeed": 20, "up": 22, "keep": 0.9, "cooldown": 1.0, "channel": 0})
    return dict(name="The Speed Bump", description=f"Slow down. Cross it too fast and it {kw('launches', GREEN)} you.",
                rarity="Common")


def pinball_flipper():
    bat, rubber, inset, chrome, plate = WHITE, "toon:#E3263F", "primary", METAL, "toon:#1F2A6B"
    length, r1, r2, height = 7.2, 1.0, 0.45, 1.1
    # Playfield patch under it, with rollover lights (flat, never collides).
    rounded_rect("Playfield", (11.0, 7.6), 1.2, 0.05, (3.0, 0.3, 0), mat=plate, bevel=0.02)
    for i, (x, y) in enumerate([(2.0, 2.6), (3.6, 2.9), (5.2, 2.6), (6.8, 1.9)]):
        cyl(f"Light{i}", 0.3, 0.04, (x, y, 0.06), mat="glow:#FFD84A" if i % 2 else "glow:#FF5AA8", verts=20, bevel=0)
    # Inlane guide rail behind the pivot.
    for k in range(9):
        a = math.radians(110 + k * 12)
        cyl(f"Rail{k}", 0.1, 0.6, (2.2 * math.cos(a), 2.2 * math.sin(a) + 0.2, 0.3), mat=chrome, verts=10, bevel=0)
        sphere(f"RailKnob{k}", 0.16, (2.2 * math.cos(a), 2.2 * math.sin(a) + 0.2, 0.65), mat=rubber, segments=12, rings=6)
    # The flipper rests angled down and swings up 60 degrees when something touches it.
    node = pivot("Flipper", rot=(0, 0, -25))
    swing = pivot("BatSwing", parent=node, motion=dict(channel=0, type="rotation", axis="Z", rest=0, active=60,
                                                     inTime=0.09, holdTime=0.35, outTime=0.45))
    taper_capsule("Bat", r1, r2, length, height, (0, 0, 0.08), mat=bat, bevel=0.12, parent=swing)
    taper_capsule("Rubber", r1 + 0.07, r2 + 0.07, length, 0.36, (0, 0, 0.45), mat=rubber, bevel=0.1, parent=swing)
    taper_capsule("Inset", r1 * 0.55, r2 * 0.5, length - 1.4, 0.05, (0.6, 0, height + 0.08), mat=inset, bevel=0.02, parent=swing)
    lathe("PivotCap", [(0, 1.2), (0.55, 1.2), (0.6, 1.28), (0.42, 1.45), (0, 1.48)], mat=chrome, segments=24, parent=swing)
    collider("BatCol", "box", (length + 0.4, 1.6, height), (length / 2 - 0.2, 0, height / 2 + 0.08), parent=swing)
    # The kick: same swing, but its launch trigger only lives mid-swing. Launch is perpendicular to the bat
    # (Blender +Y in the bat's own frame = Unity forward), with some lift.
    kick = pivot("Kick", parent=node, motion=dict(channel=0, type="rotation", axis="Z", rest=0, active=60,
                                                   inTime=0.09, holdTime=0.35, outTime=0.45, arm=True))
    collider("Flip", "box", (length + 0.6, 3.2, 2.4), (length / 2, 1.2, 1.2), parent=kick, trigger=True,
             zone={"type": "launch", "velocity": [0, 12, 34], "setVelocity": True, "cooldown": 1.0})
    collider("Touch", "box", (length + 1.0, 4.4, 2.0), (length / 2, 0.8, 1.0), parent=node, trigger=True,
             zone={"type": "plate", "channel": 0, "cooldown": 1.2})
    collider("PostCol", "box", (2.0, 2.0, 1.4), (0, 0, 0.7))
    return dict(name="The Pinball Flipper", description=f"Tilt! Touch it and it {kw('flips', GREEN)} you back onto the track. Or off it.",
                rarity="Rare")


BUILDERS = {
    "JengaTower": jenga_tower,
    "BookStack": book_stack,
    "Baguette": baguette,
    "RubberDuck": rubber_duck,
    "DominoLine": domino_line,
    "Sponge": sponge,
    "TinCanPyramid": tin_can_pyramid,
    "Mattress": mattress,
    "WhoopeeCushion": whoopee_cushion,
    "HotSaucePuddle": hot_sauce_puddle,
    "Skateboard": skateboard,
    "LegoBrick": lego_brick,
    "Blender": blender,
    "CheeseGrater": cheese_grater,
    "LavaLamp": lava_lamp,
    "Hairbrush": hairbrush,
    "RevolvingDoor": revolving_door,
    "MiniGolfWindmill": mini_golf_windmill,
    "Metronome": metronome,
    "WhackAMole": whack_a_mole,
    "JackInTheBox": jack_in_the_box,
    "Turntable": turntable,
    "Toaster": toaster,
    "Slingshot": slingshot,
    "ShakenSoda": shaken_soda,
    "Mousetrap": mousetrap,
    "GardenRake": garden_rake,
    "PizzaCutter": pizza_cutter,
    "MagnifyingGlass": magnifying_glass,
    "Toilet": toilet,
    "SewerExit": sewer_exit,
    "LongRamp": long_ramp,
    "LongRoad": long_road,
    "CurvedRoad": curved_road,
    "LowGravityZone": low_gravity_zone,
    "Drawbridge": drawbridge,
    "ShockMine": shock_mine,
    "TeleportGrenade": teleport_grenade,
    "ShockMinefield": shock_minefield,
    "GrenadeShower": grenade_shower,
    "ReverseRoad": reverse_road,
    "BabyOil": baby_oil,
    "Vacuum": vacuum,
    "WindTunnel": wind_tunnel,
    "SpeedBump": speed_bump,
    "PinballFlipper": pinball_flipper,
}


def build_all(ids=None, render=True):
    results = {}
    for obstacle_id in ids or list(BUILDERS):
        begin(obstacle_id)
        meta = BUILDERS[obstacle_id]()
        results[obstacle_id] = export_obstacle(obstacle_id, render=render, **meta)
    return results
