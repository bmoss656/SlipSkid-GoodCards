# Good Cards

**41 new cards for the Slip & Skid draft**: giant household obstacles, traps that snap shut, launchers,
road pieces to build your own track, and a few very silly epic cards.

> **Everyone in the lobby needs Good Cards, and the same version.** Cards are synced by their position in
> the card list, so mismatched versions will offer different cards on different screens.

## The cards

### Blockers and road pieces
| Card | Rarity | What it does |
|---|---|---|
| The Bumper | Uncommon | A solid pillar that pushes any vehicle that hits it away. |
| The Jenga Tower | Common | Hit it hard and it tumbles; the blocks lock where they fall until next round. |
| The Book Stack | Common | Required reading. Also a staircase. |
| The Baguette | Common | A speed bump, but French. |
| The Rubber Duck | Uncommon | Squeak. Bounces vehicles away. |
| The Domino Line | Common | Knock one and they all topple, one after another. |
| The Sponge | Uncommon | Absorbs water. And momentum. |
| The Tin Can Pyramid | Common | Bowling for vehicles: hit it to scatter the cans. |
| The Long Ramp | Common | Like the cheese, but twice as long. |
| The Long Road | Common | A long flat strip of road to build on. |
| The Curved Road | Common | A quarter turn of road. |
| The Drawbridge | Rare | Mind the gap: the bridge slides away every few seconds. |

### Launchers and boosters
| Card | Rarity | What it does |
|---|---|---|
| The Mattress | Uncommon | Jump on the bed: launches anything that lands on it. |
| The Whoopee Cushion | Rare | Pfffbbbt. Launches anything that sits on it. |
| The Hot Sauce Puddle | Rare | Extra spicy: boosts anything that drives through it. |
| The Skateboard | Uncommon | A boost ramp. Kickflip not included. |
| The Toaster | Rare | Drive over the top: ding, the toast pops and so do you. |
| The Slingshot | Rare | Drive into the band from either side, forwards or reversing. It stretches until you stop, then flings you back. |
| The Shaken Soda | Rare | Erupts every few seconds, launching anything above it. |
| The Shock Mine | Uncommon | Not deadly, just shocking: launches you sky-high. Single use. |
| The Jack-in-the-Box | Rare | Surprise! Pops out and launches anything above it. |
| The Garden Rake | Uncommon | Step on the tines and the handle launches you. |
| The Metronome | Uncommon | A swinging arm that bounces you out of time. |
| The Whack-a-Mole | Rare | Moles pop up and bounce you into the air. |
| The Turntable | Rare | Spin it back: flings vehicles off the edge. |

### Killers
| Card | Rarity | What it does |
|---|---|---|
| The Lego Brick | Rare | You know exactly how this feels: destroys any vehicle that lands on it. |
| The Blender | Rare | Will it blend? Yes. |
| The Cheese Grater | Uncommon | Safe on top; the sides destroy anything that hits them too fast. |
| The Lava Lamp | Rare | Its swelling blobs destroy any vehicle they touch. |
| The Hairbrush | Uncommon | The bristles destroy vehicles; the handle is a ramp over them. |
| The Mousetrap | Rare | Go for the cheese and it snaps shut. |
| The Pizza Cutter | Rare | Rolls back and forth, slicing anything in its path. |

### Weird ones
| Card | Rarity | What it does |
|---|---|---|
| The Revolving Door | Uncommon | After you. No, after YOU. |
| The Mini-Golf Windmill | Rare | Par 3: time your way through the sails. |
| The Low Gravity Zone | Rare | A big dome where gravity drops to 15%. |
| The Magnifying Glass | Rare | Drive through the lens and your car is huge for 8 seconds. |
| The Teleport Grenade | Uncommon | Hit it and you're sent back to the start. Single use. |

### Epic (full-art) cards
| Card | Rarity | What it does |
|---|---|---|
| The Toilet | Unique | Place the toilet, then place its Sewer Exit anywhere. Cars that fall in get flushed and shot out of the exit. |
| The Reverse | Ultra Rare | A surface swap like Ice or Sand: on reverse road your steering is flipped, even in the air. |
| The Shock Minefield | Legendary | Scatters 10 Shock Mines. |
| The Grenade Shower | Legendary | Scatters 10 Teleport Grenades. |

Knocked-over pieces, used mines and grenades, and the Toilet all work online: every player sees the same thing.

## Config

`BepInEx/config/slipskid.goodcards.cfg` (created on first launch):

- `[Card.<Name>] Rarity`: how often each card is offered, or `Off` to never offer it. **Keep this the same
  for every player.** Off keeps the card registered, so lobbies stay in sync.
- `[Card.BumperPillar] Width / Height / BounceFactor`: The Bumper's size and push. Must match for every player.
- `[Debug]` (for testing, host only):
  - `ForceCard`: a card id (e.g. `Toilet`) puts it in the first draft slot; `*` fills every slot with
    Good Cards; a comma-separated list (e.g. `LongRoad,CurvedRoad`) fills every slot from just those.
  - `EnableDebugKeys`: in a match, F6 spawns a big flat test arena above the map and puts you on it;
    F7 (host) spawns every Good Cards obstacle ahead of you.
  - `VerboseLog`: logs the vanilla card catalog, materials and zone settings at startup (for modders).

## Compatibility

- Needs BepInExPack SlipSkid (installed automatically by mod managers).
- Not tested alongside other card mods (MoreCards, EvenMoreCards). They also add cards to the same list,
  so if you combine them, make sure every player has exactly the same mods.

## Credits

- Made with a lot of help from AI tools (Claude) for the code, models and card art.
  All models and art were made for this mod; nothing is taken from the game or other games.
- Built on BepInEx and HarmonyX.
