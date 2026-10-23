# Good Cards

**40 new cards for the Slip & Skid draft**: giant household obstacles, traps that snap shut, launchers,
road pieces to build your own track, and a few very silly epic cards.

> **Everyone in the lobby needs Good Cards, and the same version.** The host's card list is copied to every
> player when they join, so other card mods load in any order, but a player without Good Cards can't show its cards.

## The cards

### Blockers and road pieces
| Card | Rarity | What it does |
|---|---|---|
| The Bumper | Uncommon | A solid pillar that pushes any vehicle that hits it away. |
| The Jenga Tower | Common | Hit it hard and it tumbles; the blocks lock where they fall until next round. |
| The Book Stack | Common | Required reading. Also a staircase. |
| The Baguette | Common | A speed bump, but French. |
| The Rubber Duck | Uncommon | Squeak. Bounces vehicles away. |
| The Sponge | Uncommon | Absorbs water. And momentum. |
| The Long Ramp | Common | Like the cheese, but twice as long. |
| The Long Road | Common | A long flat strip of road to build on. |
| The Curved Road | Common | A quarter turn of road. |
| The Drawbridge | Rare | Mind the gap: the bridge slides away every few seconds. |
| The Speed Bump | Common | Harmless at a crawl. Cross it too fast and it launches you. |

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
| The Metronome | Uncommon | A swinging arm that bounces you out of time. |
| The Turntable | Rare | Spin it back: flings vehicles off the edge. |
| The Pinball Flipper | Rare | Touch it and it flips you back onto the track. Or off it. |
| The Vacuum | Rare | Pulls nearby vehicles into its nozzle, then spits them back out at full blast. |

### Killers
| Card | Rarity | What it does |
|---|---|---|
| The Lego Brick | Rare | You know exactly how this feels: destroys any vehicle that lands on it. |
| The Blender | Rare | Will it blend? Yes. |
| The Cheese Grater | Uncommon | Safe on top; the sides destroy anything that hits them too fast. |
| The Lava Lamp | Rare | Its swelling blobs destroy any vehicle they touch. |
| The Hairbrush | Uncommon | The bristles destroy vehicles; the handle is a ramp over them. |
| The Mousetrap | Rare | Go for the cheese and it snaps shut. |

### Weird ones
| Card | Rarity | What it does |
|---|---|---|
| The Revolving Door | Uncommon | After you. No, after YOU. |
| The Mini-Golf Windmill | Rare | Par 3: time your way through the sails. |
| The Low Gravity Zone | Rare | A big dome where gravity drops to 15%. |
| The Magnifying Glass | Rare | Drive through the lens and your car is huge for 8 seconds. |
| The Baby Oil | Uncommon | A tipped-over bottle and a big slick with almost no grip. |
| The Wind Tunnel | Rare | A long tunnel with fans blowing against you: too slow and you're blown back out. |
| The Teleport Grenade | Uncommon | Hit it and you're sent back to the start. Single use. |

### Epic (full-art) cards
| Card | Rarity | What it does |
|---|---|---|
| The Toilet | Unique | Place the toilet, then place its Sewer Exit anywhere. Drive into the bowl to get flushed and shot out of the exit. |
| The Reverse | Ultra Rare | A surface swap like Ice or Sand: on reverse road your steering is flipped, even in the air. |
| The Shock Minefield | Legendary | Scatters 10 Shock Mines. |
| The Grenade Shower | Legendary | Scatters 10 Teleport Grenades. |

Knocked-over pieces, used mines and grenades, and the Toilet all work online: every player sees the same thing.

## Config

`BepInEx/config/slipskid.goodcards.cfg` (created on first launch):

- `[Draft] CustomCardChance` (host only, default 0.2): the chance that each draft card is a Good Cards card,
  so about one card in five. The rest come from the vanilla cards and any other card mods.
- `[Card.<Name>] Rarity`: how often each card comes up when a Good Cards card is drawn, or `Off` to never offer
  it. Only the host's setting matters. Off keeps the card registered, so lobbies stay in sync.
- `[Card.BumperPillar] Width / Height / BounceFactor`: The Bumper's size and push. Must match for every player.
- `[Debug]` (for testing, host only):
  - `ForceCard`: a card id (e.g. `Toilet`) puts it in the first draft slot; `*` fills every slot with
    Good Cards; a comma-separated list (e.g. `LongRoad,CurvedRoad`) fills every slot from just those.
  - `EnableDebugKeys`: in a match, F6 spawns a big flat test arena above the map and puts you on it;
    F7 (host) spawns every Good Cards obstacle ahead of you.
  - `VerboseLog`: logs the vanilla card catalog, materials and zone settings at startup (for modders).

## Compatibility

- Needs BepInExPack SlipSkid (installed automatically by mod managers).
- Works alongside other card mods (MoreCards, EvenMoreCards) and MoreCustomisations. The game sends draft
  cards and road surfaces by their position in a list that every card mod adds to. Good Cards makes every
  player's list match the host's when they join, whatever order the mods load in.
- If someone is missing a card mod the host has, the host stops drafting that mod's cards (the log says which).
  If someone doesn't have Good Cards at all, the host stops drafting Good Cards cards. Other card mods
  can't do this, so the safest lobby is still one where everyone has the same mods.
- Players can't join while the host is in a match or on the level select screen (that's the base game).
- Good Cards only changes its own cards. Errors in its code are caught and logged, so they can't break the
  game or another mod. Don't keep an old copy installed next to this one: BepInEx will refuse to load both.

## Credits

- Made with a lot of help from AI tools (Claude) for the code, models and card art.
  All models and art were made for this mod; nothing is taken from the game or other games.
- Built on BepInEx and HarmonyX.
