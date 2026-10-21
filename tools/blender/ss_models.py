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
    crust, end, slash = "toon:#D9963E", "toon:#C47F2C", "toon:#F3D49A"
    loaf = pivot("Loaf", (0, 0, 0.55), rot=(0, 0, 8))
    sphere("Body", 1.0, mat=crust, scale=(3.6, 0.6, 0.5), parent=loaf, segments=32, rings=14)
    for i in range(5):
        x = -2.2 + i * 1.1
        box(f"Slash{i}", (0.7, 0.18, 0.08), (x, 0, 0.47), rot=(0, 6, 35), mat=slash, bevel=0.03, parent=loaf)
    sphere("TipA", 0.35, (-3.45, 0, 0.0), mat=end, scale=(1, 1.3, 1), parent=loaf)
    sphere("TipB", 0.35, (3.45, 0, 0.0), mat=end, scale=(1, 1.3, 1), parent=loaf)
    rnd = random.Random(12)
    for i in range(16):
        x = rnd.uniform(-3.0, 3.0)
        top = 0.5 * math.sqrt(max(0.0, 1 - (x / 3.6) ** 2))
        sphere(f"Flour{i}", rnd.uniform(0.05, 0.1), (x, rnd.uniform(-0.25, 0.25), top - 0.01), mat="toon:#FFF8EC",
               scale=(1, 1, 0.4), segments=8, rings=4, parent=loaf)
    collider("LoafCol", "box", (7.2, 1.2, 1.0), parent=loaf)
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
    pink, dark = "toon:#FF6FAE", "toon:#E04A8C"
    sphere("Cushion", 2.0, (0, 0, 0.5), mat=pink, scale=(1.0, 1.0, 0.27), segments=32)
    cyl("Neck", 0.45, 1.1, (0, 2.3, 0.35), rot=(-90, 0, 0), mat=pink, radius2=0.3, verts=16)
    torus("Lip", 0.32, 0.09, (0, 2.85, 0.35), rot=(90, 0, 0), mat=dark, seg=16, ring=6)
    collider("Puff", "box", (3.8, 3.8, 0.8), (0, 0, 0.4), zone=bounce("velocity", 1.0, velocity=[0, 22, 0]))
    return dict(name="The Whoopee Cushion", description=f"Pfffbbbt. {kw('Launches', GREEN)} anything that sits on it.",
                rarity="Rare")


def hot_sauce_puddle():
    red, dark = "toon:#D7261E", "toon:#A8140F"
    cyl("Splat", 2.6, 0.12, (0, 0.4, 0.06), mat=red, verts=32, bevel=0.05)
    rnd = random.Random(5)
    for i in range(6):
        a = rnd.uniform(0, 2 * math.pi)
        cyl(f"Drop{i}", rnd.uniform(0.3, 0.6), 0.12, (math.cos(a) * 2.8, 0.4 + math.sin(a) * 2.8, 0.06), mat=red, verts=16)
    bottle = pivot("Bottle", (0, -2.6, 0.75), rot=(-90, 0, 0))
    cyl("Glass", 0.75, 2.6, mat=dark, verts=24, bevel=0.08, parent=bottle)
    cyl("Label", 0.77, 1.2, (0, 0, -0.2), mat=WHITE, verts=24, bevel=0, parent=bottle)
    cyl("Neck", 0.35, 0.9, (0, 0, 1.6), mat=dark, verts=16, parent=bottle)
    cyl("Cap", 0.4, 0.5, (0, 0, 2.2), mat="toon:#3FA34D", verts=16, parent=bottle)
    collider("BottleCol", "box", (1.6, 3.6, 1.5), (0, -2.3, 0.75))
    collider("Spicy", "box", (5.2, 5.0, 1.4), (0, 0.6, 0.7), trigger=True,
             zone={"type": "accel", "acceleration": 45, "setVelocity": True, "velocityOnEnter": 40})
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
    cyl("Base", 2.4, 1.4, (0, 0, 0.7), mat="toon:#3A3F4B", verts=32, bevel=0.15, radius2=2.1)
    for i, colour in enumerate(["toon:#E3263F", "toon:#F2C14E", "toon:#3FA34D"]):
        box(f"Button{i}", (0.45, 0.3, 0.3), (-0.6 + i * 0.6, -2.2, 0.75), rot=(-8, 0, 0), mat=colour, bevel=0.05)
    cyl("Hub", 0.45, 0.5, (0, 0, 1.6), mat=METAL, verts=16)
    torus("JugCollar", 2.25, 0.14, (0, 0, 1.42), mat=METAL)
    cyl("Badge", 0.5, 0.06, (0, -2.25, 1.05), rot=(-80, 0, 0), mat="primary", verts=24, bevel=0.01)
    spin = pivot("Blades", (0, 0, 1.75), anim=dict(type="rotation", axis="Z", min=0, max=360, speed=1.1, curve="linear"))
    for i in range(2):
        arm = pivot(f"Arm{i}", rot=(0, 0, i * 90), parent=spin)
        box(f"Blade{i}", (5.6, 0.55, 0.1), rot=(14, 0, 0), mat=METAL, bevel=0.03, parent=arm)
        collider(f"BladeKill{i}", "box", (5.6, 0.9, 0.7), parent=arm, trigger=True, zone=KILL)
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
    box("Head", (4.0, 3.2, 0.6), (0, 0, 0.3), mat="primary", bevel=0.25)
    for ix in range(7):
        for iy in range(5):
            cyl(f"Bristle{ix}_{iy}", 0.09, 1.0, (-1.65 + ix * 0.55, -1.2 + iy * 0.6, 1.1), mat=BLACK, verts=8, bevel=0)
            sphere(f"Tip{ix}_{iy}", 0.13, (-1.65 + ix * 0.55, -1.2 + iy * 0.6, 1.62), mat=WHITE, segments=8, rings=4)
    run, rise = 5.4, 1.6
    tilt = math.degrees(math.atan2(rise, run))
    handle = pivot("Handle", (0, -1.6 - run / 2, rise / 2), rot=(tilt, 0, 0))
    box("Grip", (1.3, run + 0.4, 0.45), mat="secondary", bevel=0.18, parent=handle)
    collider("HandleCol", "box", (1.3, run + 0.4, 0.45), parent=handle)
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
    glass, label, foam = "toon:#3FBF5A", "toon:#E3263F", "toon:#FFF3D6"
    bottle = pivot("Bottle", (0, 2.2, 1.1), rot=(62, 0, 0))  # neck aimed at the puddle
    cyl("Glass", 1.1, 3.6, mat=glass, verts=24, bevel=0.2, parent=bottle)
    cyl("Label", 1.12, 1.4, (0, 0, -0.3), mat=label, verts=24, bevel=0, parent=bottle)
    cyl("Neck", 0.55, 1.4, (0, 0, 2.3), mat=glass, verts=20, radius2=0.42, parent=bottle)
    collider("BottleCol", "box", (2.2, 2.2, 3.6), parent=bottle)
    cyl("Puddle", 2.2, 0.1, (0, -1.0, 0.05), mat=foam, verts=32, bevel=0.03)
    cycle = 0.18
    keys = [[0, 0.02], [0.68, 0.02], [0.72, 1.1], [0.76, 1], [0.9, 1], [0.95, 0.02], [1, 0.02]]
    # The column's scale and the launch window share one clock cycle, so the spray and the push line up.
    spray = pivot("Spray", (0, -1.0, 0), anim=dict(type="scale", min=(1, 1, 0.0), max=(1, 1, 1), speed=cycle, curve=keys))
    cyl("Column", 1.1, 9.0, (0, 0, 4.5), mat=foam, verts=20, radius2=1.6, parent=spray)
    for i, (x, z) in enumerate([(0.6, 3.0), (-0.7, 5.5), (0.3, 8.0), (-0.2, 9.3)]):
        sphere(f"Fizz{i}", 0.9 + 0.2 * i, (x, 0, z), mat="toon:#C8F0FF", parent=spray)
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
    green, wood = "toon:#3FA34D", "toon:#A0643C"
    box("Head", (4.6, 0.45, 0.3), (0, 4.0, 0.2), mat=green, bevel=0.08)
    for i in range(10):
        x = -2.05 + i * 0.455
        cyl(f"Tine{i}", 0.08, 0.9, (x, 4.0, 0.75), mat=METAL, verts=8, bevel=0)
    swing = pivot("Swing", (0, 3.75, 0.25), motion=dict(channel=0, type="rotation", axis="X", rest=0, active=-75,
                                                       inTime=0.12, holdTime=0.5, outTime=0.8, arm=True))
    box("Handle", (0.35, 8.0, 0.35), (0, -4.0, 0), mat=wood, bevel=0.12, parent=swing)
    box("Grip", (0.45, 1.2, 0.45), (0, -7.6, 0), mat=green, bevel=0.15, parent=swing)
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
    porcelain, water, mat_blue = "toon:#F7F7FA", "toon:#5BC0FF", "toon:#7FD3FF"
    cyl("Pedestal", 1.3, 1.5, (0, 0, 0.75), mat=porcelain, verts=32, radius2=1.0, bevel=0.15)
    cyl("Bowl", 2.0, 0.9, (0, 0, 1.75), mat=porcelain, verts=40, radius2=2.2, bevel=0.15)
    torus("Seat", 1.75, 0.3, (0, 0, 2.3), mat="primary", seg=40, ring=12)
    cyl("Water", 1.55, 0.05, (0, 0, 2.23), mat=water, verts=40, bevel=0)
    swirl = pivot("Swirl", (0, 0, 2.27), anim=dict(type="rotation", axis="Z", min=0, max=360, speed=0.25, curve="linear"))
    # Whole turns only, so snapping back to rest after the flush is invisible.
    flush = pivot("Flush", (0, 0, 0), parent=swirl, motion=dict(channel=0, type="rotation", axis="Z", rest=0, active=-1080,
                                                                 inTime=0.9, holdTime=0.0, outTime=0.01))
    for i in range(3):
        arm = pivot(f"SwirlArm{i}", rot=(0, 0, i * 120), parent=flush)
        box(f"Streak{i}", (0.2, 1.1, 0.03), (0.6, 0.3, 0), rot=(0, 0, 35), mat=WHITE, bevel=0, parent=arm)
    lid = pivot("LidHinge", (0, 1.8, 2.35), rot=(-100, 0, 0))
    cyl("Lid", 1.9, 0.18, (0, -1.9, 0.09), mat="primary", verts=40, bevel=0.06, parent=lid)
    box("Tank", (3.4, 1.4, 2.6), (0, 2.6, 2.6), mat=porcelain, bevel=0.2)
    box("TankLid", (3.6, 1.6, 0.25), (0, 2.6, 3.95), mat=porcelain, bevel=0.1)
    cyl("Handle", 0.12, 0.8, (-1.3, 1.85, 3.4), rot=(0, 90, 0), mat=METAL, verts=10)
    ramp = pivot("StepRamp", (0, -4.0, 1.15), rot=(30, 0, 0))
    box("Mat", (2.8, 4.8, 0.25), mat=mat_blue, bevel=0.12, parent=ramp)
    collider("RampCol", "box", (2.8, 4.8, 0.3), parent=ramp)
    collider("PedestalCol", "box", (2.2, 2.2, 1.4), (0, 0, 0.7))
    collider("TankCol", "box", (3.4, 1.4, 4.0), (0, 2.6, 2.0))
    for i, (x, y) in enumerate([(-2.0, 0), (2.0, 0), (0, 1.6)]):
        collider(f"RimCol{i}", "box", (0.5 if x else 3.6, 3.6 if x else 0.5, 0.8), (x, y, 1.9))
    collider("Bowl", "box", (2.8, 2.8, 1.6), (0, 0, 2.2), trigger=True, zone={"type": "toilet", "delay": 0.35, "channel": 0})
    return dict(name="The Toilet", rarity="Unique", full_art=True, partner="SewerExit",
                description=f"Flush and reflect. Place its {kw('Sewer Exit', PURPLE)} anywhere: vehicles that fall in come out there.")


def sewer_exit():
    pipe, rust = "toon:#3FA34D", "toon:#2E7D3A"
    pipe_pivot = pivot("Pipe", (0, 0, 1.9), rot=(-90, 0, 0))
    cyl("Tube", 1.6, 3.4, mat=pipe, verts=32, bevel=0.1, parent=pipe_pivot)
    torus("MouthRing", 1.6, 0.25, (0, 0, 1.7), mat=rust, parent=pipe_pivot, seg=32, ring=10)
    cyl("Dark", 1.35, 0.05, (0, 0, 1.68), mat="toon:#14201A", verts=32, bevel=0, parent=pipe_pivot)
    for y in (-1.0, 1.0):
        box(f"Support{y}", (2.6, 0.5, 0.6), (0, y, 0.3), mat="toon:#B9B9C4", bevel=0.08)
    sphere("Drip", 0.35, (0, 1.9, 0.2), mat="toon:#5BC0FF", scale=(1.6, 1.2, 0.3))
    collider("PipeCol", "box", (3.2, 3.4, 3.2), (0, 0, 1.9))
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
    return ["StepRamp", "Mat"]


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
}


def build_all(ids=None, render=True):
    results = {}
    for obstacle_id in ids or list(BUILDERS):
        begin(obstacle_id)
        meta = BUILDERS[obstacle_id]()
        results[obstacle_id] = export_obstacle(obstacle_id, render=render, **meta)
    return results
