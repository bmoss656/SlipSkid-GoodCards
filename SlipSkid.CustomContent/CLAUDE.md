# Slip & Skid Custom Content

BepInEx 6 (Unity Mono) plugin for Slip & Skid. netstandard2.1, HarmonyX.
The game uses Unity Netcode for GameObjects. The build is stripped.
Unity version: 2022.3.62.

## Reference
- ./decompiled is the game's Assembly-CSharp, exported with ilspycmd.
  Read and search it; never copy it into src/ and never commit it.
- ./docs/game-notes.md holds what we've learned about the game's code.
  Read it first. Update it whenever you confirm something new.
- Log: <BepInExDir from local.props>/LogOutput.log

## Build
dotnet build -c Release
(Paths come from local.props: GameDir and BepInExDir. Override with -p:GameDir="..." -p:BepInExDir="...".)

## Hard rules
- The card registry is APPEND-ONLY. Never reorder, remove or insert
  cards; clients sync cards by catalog index.
- A disabled card stays registered with rarity Off.
- Any change to the registry order or count bumps the version and gets
  a changelog line.
- Prefer Prefix/Postfix; use a Transpiler only if I agree first.
- Before using any Unity API, confirm it exists in the stripped DLLs in
  Managed/. If it doesn't, say so rather than guessing. Stripping removes
  members too (e.g. MeshCollider.sharedMesh, Mathf.PI), so build to be sure.
- Never touch networked rule data (CustomGameRules etc.) without flagging it.
- Every tunable number goes in BepInEx config under [Card.<Name>].
- Log with the plugin logger, prefixed with the card or system name.

## How custom obstacles work
- `src/Registry/CardRegistry.cs` lists every custom card (append-only) and appends a clone of a
  vanilla "carrier" card to `ObstacleManager.allowedObstacleDescriptions` on every machine.
- The host spawns the carrier's network prefab; `SpawnMarker` packs our slot and the rolled affix
  into `Obstacle.affixIndex`. On every machine, a Prefix on `Obstacle.OnNetworkSpawn` strips the
  carrier (`VisualSwap`) and calls the card's `Build`.
- Most obstacles are `DataObstacle`s: everything (meshes, colliders, zones, animation, card text)
  comes from `assets/obstacles/<Id>.json` plus `<Id>.png` card art, built at runtime by
  `src/Data/DataObstacleBuilder.cs`. No Unity editor or AssetBundles involved.
- Adding one:
  1. Write a builder in `tools/blender/ss_models.py` (helpers in `ss_lib.py`: box/cyl/sphere/torus/
     prism/frustum_box, `collider(..., zone=...)`, `pivot(..., anim=...)`), add it to `BUILDERS`.
  2. In Blender (MCP): exec `ss_lib.py` then `ss_models.py`, `set_repo(<repo>)`, `build_all(["<Id>"])`.
     That writes the JSON and renders the card art.
  3. Append `new DataObstacle("<Id>", "<new fixed guid>")` to `CardRegistry.Entries`, then build.
- Blender conventions: Z up, metres, ground at z=0, front faces -Y (the card camera's side),
  Blender +Y = Unity forward. Material names are specs: `toon:#RRGGBB`, `primary`, `secondary`,
  `pattern` (player colours), `mat:<vanilla material>`. Zone dicts are Unity space.
- Zones: vanilla `kill`, `bounce`, `accel`, `slow`, plus ours in `src/Behaviours/`: `launch` (throw the
  car along a node-local velocity, optional delay), `plate` (fire a TriggerBus channel), `toilet`, `grow`.
- Node extras: `anim` (network-clock rotation/scale/position), `motion` (one-shot TriggeredMotion on a
  channel; `arm` makes colliders under it live only mid-move), `timed` (colliders live in a clock window).
- TriggerBus syncs one-shot motions with a Netcode named message (owner fires, host relays). Effects on
  cars always run only on the car owner's machine.
- Card flags in the JSON: `partner` (placing it hands the owner that obstacle to place next, see
  `ToiletPairing`), `partnerOnly` (registered but never drafted), `fullArt` (`<Id>_card.png` covers the
  card; composite it with `tools/card_art.ps1` from a `render_card_foreground` render).
- Code-built obstacles (like `BumperPillar`) subclass `CustomObstacle` directly.
- Testing: `[Debug] ForceCard = *` fills drafts with custom cards. In a match: F6 spawns the Test Arena
  (a 160 m flat platform 250 m above the map; host first) and puts your car on it; F7 (host) spawns every
  custom obstacle in a grid ahead of your car.
- Bounces: vanilla `BounceZone` reflects the car's velocity, which is already ~0 by OnCollisionEnter, so
  use `push` (fixed speed away) or `bounce` mode `velocity` (fixed launch, like the vanilla Egg).
- `crumble` nodes knock over: their direct children fall as debris (no car collisions while falling),
  then lock solid where the HOST's pieces landed (pose message), until `roundIndex` changes.
- Keep-carrier cards (`carrier` + `keepCarrier` in the JSON) reuse a vanilla card's own logic: `scatter`
  makes a LandMineScatter drop one of ours (Shock Minefield, Grenade Shower); `surface: "reverse"` makes a
  surface swap use our Reverse surface (`ReverseSurface`, appended to `SurfaceManager.surfaces`; steering
  flipped by patching `SphereCarController.Steer`/`AirSteer`).
- `gravity` zone: `LowGravityShape` is a `GravityShape`, so the car's own gravity sum (and jumps) change.
- `spawn` zone: `GameManager.PlacePlayerAtSpawn` (Teleport Grenade).
- `effect` nodes (`BurstEffect`): shock/teleport visuals played on a TriggerBus channel on every machine;
  `consume` hides the obstacle everywhere and the host despawns it (`ObstacleManager.Delete`). Effect
  materials use the `glow:#RRGGBB` spec (unlit copy of the vanilla CheckPointOutline material).
- `slingshot` zone (`SlingshotZone`): band drawn at runtime from car positions on every machine; pull and
  launch only on the car owner. Works from either side, forwards or reversing.
  Add behaviour with the game's own components (KillZone, BounceZone...) via AddComponent.
- Effect settings (sizes, forces) affect collisions on each client, so they must match for every player.
- See docs/game-notes.md for the game internals all of this relies on.

## Done means
It builds, the log shows it registered, and you've told me exactly what
to check in game (solo first, then a two-player online test).
