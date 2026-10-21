# Obstacle ideas

**Status (2026-10-21):** all 30 are built as DataObstacles (`assets/obstacles/`, models in
`tools/blender/ss_models.py`), none tested in game yet. The Toilet changed design: it's a Unique full-art
card that also hands you a Sewer Exit to place, and flushed vehicles come out of the exit.

Batch 3 (also built): Long Ramp, Long Road, Curved Road, Low Gravity Zone, Drawbridge, Shock Mine,
Teleport Grenade, plus full-art cards: Shock Minefield and Grenade Shower (scatter 10), and The Reverse
(a surface swap like Ice/Sand whose road flips your steering, even in the air).

Giant everyday objects, in the same spirit as the vanilla Cheese Wedge, Pea and Stinky Sock.
None of these duplicate a vanilla card (checked against the 67-card catalog dump).

**Build** says how far the current system (see CLAUDE.md, "How custom obstacles work") gets you:
- **Ready**: Unity primitives plus vanilla components (`KillZone`, `BounceZone`, `AccelerationZone`,
  `SlowDownZone`, `Zone`, `NetworkAnimatedRotation`, `NetworkAnimatedScale`). Same recipe as The Bumper.
- **Small code**: also needs one new MonoBehaviour of ours, e.g. a sliding mover (vanilla only has
  rotation and scale animators; subclass `NetworkAnimatedTransformation` so it uses the network clock),
  a timed trigger, or a custom launch force.
- **Research**: touches car state or respawning; read the game code first.

Every obstacle can start as primitives and get a real model (AssetBundle) later.

## Blockers

| # | Card | Card text | How it works | Build |
|---|------|-----------|--------------|-------|
| 1 | The Jenga Tower | Don't pull the wrong one. | Tall stack of offset cube blocks, solid. | Ready |
| 2 | The Book Stack | Required reading. Also a staircase. | Cubes stepped up like stairs, so you can drive over it or into it. | Ready |
| 3 | The Baguette | A speed bump, but French. | Long cylinder lying across the road; jolts cars that hit it fast. | Ready |
| 4 | The Rubber Duck | Squeak. | Solid duck with a soft, low-factor `BounceZone`. Needs a model to look right. | Ready |
| 5 | The Domino Line | Knocking them over is your problem. | Zig-zag row of standing slabs (static for now; physics would mean a RigidBody carrier). | Ready |
| 6 | The Sponge | Absorbs water. And momentum. | Looks solid, but it's a trigger with a strong `SlowDownZone`: you plough through slowly. | Ready |
| 7 | The Tin Can Pyramid | Bowling for vehicles. | Stacked cylinders, solid. | Ready |

## Boosters and launchers

| # | Card | Card text | How it works | Build |
|---|------|-----------|--------------|-------|
| 8 | The Mattress | Jump on the bed, they said. | Flat slab, `BounceZone` with a custom upward normal: a trampoline. | Ready |
| 9 | The Whoopee Cushion | Pfffbbbt. | Flat cushion; driving over it gives a big up-and-forward kick (`BounceZone` custom velocity). | Ready |
| 10 | The Hot Sauce Puddle | Extra spicy. Extra fast. | Red floor puddle with a strong `AccelerationZone`. | Ready |
| 11 | The Skateboard | Kickflip not included. | A ramp with an `AccelerationZone` along it. | Ready |
| 12 | The Toaster | Pops when done. You are done. | Drive into the slot; after a short delay you're launched straight up. | Small code |
| 13 | The Slingshot | Pull back. Let go. | Y-frame with a band zone; half a second after you enter, you're flung forward hard. | Small code |
| 14 | The Shaken Soda | Do not open. | Bottle that erupts on a timer; the geyser column launches anything above it. | Small code |

## Killers

| # | Card | Card text | How it works | Build |
|---|------|-----------|--------------|-------|
| 15 | The Lego Brick | You know exactly how this feels. | Small brick that only kills when you land on it from above (`KillZone.alignedVelocityToKill`, Up). | Ready |
| 16 | The Blender | Will it blend? Yes. | Spinning blades in a jug: `NetworkAnimatedRotation` with `KillZone` blades. | Ready |
| 17 | The Cheese Grater | Grates cars. Finely. | Safe to drive over the top; the sides kill you if you hit them fast (aligned-velocity `KillZone`s). | Ready |
| 18 | The Lava Lamp | Groovy. Lethal. | Glass column whose blobs swell and shrink (`NetworkAnimatedScale`); the blobs are `KillZone`s. | Ready |
| 19 | The Hairbrush | Bad hair day. | The bristles kill; the handle is a safe ramp over them, if you line up. | Ready |
| 20 | The Mousetrap | Cheese sold separately. | Touch the plate and the bar snaps over after a beat (`Zone` delay, then a `KillZone` and a snap rotation). | Small code |
| 21 | The Garden Rake | A classic. | Drive over the tines and the handle swings up and smacks you. | Small code |
| 22 | The Pizza Cutter | One slice per lap. | Wheel rolling back and forth across the road; touching it kills. Needs our sliding mover. | Small code |

## Animated

| # | Card | Card text | How it works | Build |
|---|------|-----------|--------------|-------|
| 23 | The Revolving Door | After you. No, after YOU. | Rotating cross of solid panels; time your way through. | Ready |
| 24 | The Mini-Golf Windmill | Par 3. | Blades sweep across the doorway; go through the hole between them. | Ready |
| 25 | The Metronome | Keep the beat. | Pendulum arm swinging side to side that bounces you (not a kill). | Ready |
| 26 | The Whack-a-Mole | Bonk. | Moles pop up in turn (`NetworkAnimatedScale`, staggered via each easing curve) and bounce you. | Ready |
| 27 | The Jack-in-the-Box | Surprise! | The lid opens on a timer and the jester springs out, launching anything above it sky-high. | Ready |
| 28 | The Turntable | Spin it back. | Big rotating disc you drive across; it flings you off the edge. Moving-collider physics needs testing. | Ready, test first |

## Weird ones

| # | Card | Card text | How it works | Build |
|---|------|-----------|--------------|-------|
| 29 | The Toilet | Flush and reflect. | Drive in, get flushed back to your last checkpoint. | Research |
| 30 | The Magnifying Glass | Objects may appear larger. | The opposite of the Shrink Ray: your car is huge for a while (`SphereCarController.scaleModifier`). | Research |

## Suggested build order
1. **The Revolving Door**: first animated obstacle (rotation with solid colliders).
2. **The Blender**: first killer (rotation plus `KillZone`).
3. **The Mattress**: a controlled bounce, which also fixes The Bumper's jump.
