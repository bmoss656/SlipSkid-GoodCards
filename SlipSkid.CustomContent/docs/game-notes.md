# Game notes

What we've confirmed about Slip & Skid's code. Unconfirmed guesses go under "Leads".

## Confirmed
- Unity Mono build (no GameAssembly.dll), Unity 2022.3.62.
- Decompiled with ilspycmd 11.1 into ./decompiled (337 files), 2026-10-21.

### Card definition: `Obstacles/ObstacleDescription.cs`
- `ObstacleDescription : ScriptableObject`. Clone with `Object.Instantiate`.
- Fields: `id` (SerializableGuid), `displayName` and `description` (both `LocalizedString`,
  so card text is a localization reference, not a plain string), `prefab` (Obstacle),
  `type` (ObstacleType, includes `Modifier`), `rarity` (ObstacleRarity), `thumbnail`,
  `maxQuantity` (-1 = unlimited, 0 = never rolls), `allowedAffixes`, `generationContexts`,
  plus UI override fields.
- `ObstacleRarity`: Common, Uncommon, Rare, UltraRare, Legendary, Unique. Weights in the
  static `obstacleRarityWeightTable` match the guide (110/60/37/25/12/2). There is no "Off"
  rarity; `maxQuantity = 0` is a candidate way to keep a card registered but never rolled.
- `GetRandomWeightedObstacleDescription(descriptions, selectionHistory, currentList, currentCount)`
  is static and uses `UnityEngine.Random`.

### Catalog: `Obstacles/ObstacleManager.cs`
- `ObstacleManager : MonoBehaviour`, singleton `ObstacleManager.instance`.
- The catalog is ONE array: `public ObstacleDescription[] allowedObstacleDescriptions`
  (a serialized field, so it's set in the scene/prefab, not built in code).
  A second `hiddenObstacleDescriptions` array exists (used when `useHiddenList` is true).
- Cards are synced by index into `allowedObstacleDescriptions`:
  `GetRandomObstacleIndex` returns the index, `GetDescriptionFromIndex(int)` and
  `GetIndexFromDescription` convert back. Appending to the array keeps existing indices.
- `GetRandomObstaclesDescriptions(amount, modifierOnly)` is the draft roll: filters by
  min rarity and game rules (`FilterDescriptionsWithGameRules`), then rolls each slot.
  This is the place to hook `Debug.ForceCard`.
- `AllObstacles` (static `List<Obstacle>`) is the set of spawned obstacles, not the catalog.
  Lookups by `NetworkObject.NetworkObjectId`.

### Draft pipeline: `Game/GameManager.cs`
1. Host: `GenerateObstaclesToSelect(modifierOnly)` (~line 2338) calls
   `ObstacleManager.GetRandomObstaclesDescriptions`, keeps the result in `_obstaclesToSelect`,
   and writes the catalog indices to `networkVariables.obstaclesToSelectIndices` and the
   affix indices to `networkVariables.obstaclesModifiersIndices`. Clients build the draft UI
   from those lists.
2. Players pick: `TryToSelectObstacleDescription(player, slot)` fills `_playerObstaclesSelection`
   (synced as `networkVariables.playersObstaclesSelection`).
3. Host: `GenerateObstaclesToPlace()` calls `ObstacleManager.SpawnObstaclesFromDescriptions`,
   which calls `ObstacleDescription.Spawn(player, pos, rot, scale, inScene, affixIndex)` per pick.
4. `ObstacleDescription.Spawn` does `Object.Instantiate(prefab)`, sets the NetworkVariables
   `playerInfosIndex` and `affixIndex`, then `NetworkObject.SpawnWithOwnership(player.OwnerClientId)`.
   So every card's prefab is a registered NGO network prefab.

### Modifier cards: `Obstacles.ObstacleGameModifiers/`
- A modifier card is an obstacle. `ObstacleGameModifier : Obstacle` (abstract), and each card
  is a subclass with one `ApplyModifier()` override (23 of them, 35 to 125 lines each).
- Flow: spawned like any obstacle. `AfterInit` on the host waits a frame, then
  `PlaceObstacle(ignorePosition: true)`, which sends `PlaceObstacleClientRpc`. That RPC runs
  `OnPlace` on EVERY machine (Obstacle.cs ~line 1521). `ObstacleGameModifier.OnPlace` calls
  `ApplyModifier()`, then the host deletes the obstacle.
- So `ApplyModifier()` runs once on each machine, and each one loops over
  `GameManager.Players` and edits its own local copy of every car. That's how lobby-wide
  modifiers stay in sync without extra networking.
- Examples:
  - `IncreaseAcceleration`: `player.controller.EditSpeed(factor)` for every player.
  - `IncreaseDashForce`: `player.controller.boostSpeed += force`.
  - `IncreaseDashForceRoundOnlyOnFlip`: adds listeners to `controller.onBackFlip`/`onFrontFlip`.
  - `IncreasePlayerCollisionForce`: `GameManager.AddCollisionForce(...)` (game-wide, not per car).
- Card tunables (`accelerationIncreaseFactor`, `dashForceIncrease`...) are serialized on the
  prefab, not on the ObstacleDescription.

### IMPORTANT: `Obstacle.description` comes from the prefab
- `public ObstacleDescription description` on Obstacle is never assigned in code; it's baked
  into each prefab. A client spawning a network prefab gets the prefab's own description.
- So if our cloned card reuses a vanilla prefab (the guide's "borrow a prop" route), clients
  can NOT tell from `obstacle.description` that it came from our card. We need our own marker.

### Car stats: `Player/SphereCarController.cs`
- `UpdateGameRulesValues(customGameRules)` sets the baselines from lobby rules:
  `_speedDefaultValue = 450 * playerAccelerationSpeed`, `_maxSpeedDefaultValue = 45 * playerMaxSpeed`,
  `jumpHeight = 1 * playerJumpForce`, `maxAirJumps = playerJumpCount - 1`,
  `maxBoostCount = playerDashCount`, `boostSpeed = 10 * playerDashForce`.
  Called on controller start and whenever the networked game rules change
  (`GameManagerNetworkVariables.UpdateGameRulesWithNetworkedValue`), so a rules change mid-match
  wipes card modifiers.
- `ClearModifiers()` (private, called on respawn/reset) puts speed, reverseSpeed, driftSpeed,
  maxSpeed, rotation and drift values back to their `_xxxDefaultValue` baselines. Surface
  modifiers change the live values; cards change the baselines.
- Lifetime rule for our cards: to last the match, change a baseline (`EditSpeed`,
  `EditReverseSpeed`, or the `_xxxDefaultValue` fields via AccessTools) or a stat ClearModifiers
  doesn't touch (`jumpHeight`, `boostSpeed`, `maxAirJumps`, `maxBoostCount`). Changing `speed`
  directly is undone on the next respawn.
- Round-only buffs exist: `IncreaseDashForceRoundOnly` adds to `_dashSpeedRoundBuffer`, reset to 0
  at lines ~929, ~1583, ~1591.

### Affix index
- `affixIndex` is a `NetworkVariable<int>`, default -1. Every reader treats `< 0` as "no affix"
  (Obstacle.cs ~1670, UnlockableContentUtils.cs ~578). A negative value is safe to use as a marker.

### Placeable obstacles: `Obstacles/`
- Enums on ObstacleDescription: `ObstacleType` Prop, Surface, Tool, Weapon, Modifier.
  `ObstacleBodyType` Static, RigidBody, Animated. `ObstacleMovementType` Free, Snap, Disallowed.
  `ObstacleRotationType` Free, HorizontalOnly, VerticalOnly, Disallowed.
- Few subclasses: besides modifiers there are only `ObstacleCheckpoint`, `ObstacleScatter`,
  `ObstacleControlledScatter`, `ObstacleDelete`, `ObstacleScorePoint`, `ObstacleSpeedCamera`
  and `ObstacleSurfaceSwap`. Most hazards are a plain `Obstacle` plus behaviour components
  on child objects. Built by composition, which is great for us.
- Behaviour components are plain `MonoBehaviour`s (no NGO code generation, safe to `AddComponent`):
  - `Zone`: trigger with `delay`, `onEnter`/`onEnterBeforeDelay` UnityEvents.
  - `KillZone`: trigger. `componentInParent.Die(parent)`; `parent` is the Obstacle, used for
    kill credit/trap score. Optional `alignedVelocityToKill` (only kills when hit fast along an axis).
  - `BounceZone`: collision. `AddForce(VelocityChange)` with `bounceFactor`, normal options.
  - `AccelerationZone`, `SlowDownZone`, `ZoneWithMinSpeed`, `ScorePointZone`, `SpeedCamera`.
  - `KillRay` / `Ray` (238 lines, not read yet).
- Hit detection is LOCAL. Every zone checks `PlayerNetworking.IsOwner`, so each machine only
  reacts to its own car. A hazard needs no networking of its own: the same component on every
  client is enough.
- Movement: `NetworkAnimatedTransformation` (abstract MonoBehaviour) with `NetworkAnimatedRotation`,
  `NetworkAnimatedScale` etc. Fields: `target`, `min`, `max`, `speed`, `easing` (AnimationCurve),
  events `onReachStart/Middle/End/Custom`. Time comes from `NetworkAnimatedParameter.Time`
  = `NetworkManager.LocalTime.Time * speed * networkAnimationSpeedFactor` (lobby rule
  `animatedObstacleSpeed`). Synced clock, so moving parts are in phase on every screen.
  - Gotcha: `Awake` builds parameters from `min/max/easing` and reads `easing.keys`. When adding one
    at runtime, add it to an INACTIVE GameObject, set the fields, then `SetActive(true)`.
  - `Obstacle.OnNetworkSpawn` caches `_animatedTargets` only when `bodyBodyType == Animated`.
- Rigidbody obstacles use `ChangeOwnerByDistance` (ownership hand-off). Avoid RigidBody carriers for now.

### Obstacle lifecycle (`Obstacles/Obstacle.cs`, 2373 lines)
- `Awake` (~405) caches colliders. `OnNetworkSpawn` (~430) finds `playerInfos` from
  `playerInfosIndex`, copies `spawnState`, then calls `Init`.
- `Init(inScene)` (~1611) RE-CACHES `colliders`, `_meshFilters` and `audioSources`
  (`GetComponentsInChildren`), then `ApplyAffix()` and `AfterInit()`.
- NGO applies NetworkVariable values before `OnNetworkSpawn`. So a **Prefix on
  `Obstacle.OnNetworkSpawn`** can read our marker and swap visuals/colliders BEFORE the game
  caches them. Placement checks and effects then use our meshes.
- Placement: the owner moves it (PlayerControlled state); `PlaceObstacle` sends
  `PlaceObstacleServerRpc`, then `PlaceObstacleClientRpc` sets position/rotation/scale on all machines.
  Forbidden-zone checks use `pointsToCheckForbiddenZones` (local-space points on the prefab),
  so a different-sized model should rewrite these.
- `ignoredEffectsRenderers`, `center` and `anchors` are prefab setup fields worth matching too.

### Affixes
- `Obstacle.ApplyAffix()` (private, called from Init): `affixIndex >= 0` gets
  `ObstacleAffixManager.GetAffixByIndex(i).callbacks.Apply(this)`.
- Giant: `localScale *= 2.25`. Golden: replaces materials where
  `SurfaceManager.IsSwappableMaterial(m)` with `goldenMaterial`, so our obstacle should use
  materials copied from vanilla obstacles if Golden (and surface swaps) should work. Chromed not read yet.
- `scoreOffset` (NetworkVariable) is used by trap scoring (ScoreChunk.cs), so it can't be a marker.

### Details confirmed while writing the obstacle code (2026-10-21)
- `ObstacleManager.Awake` destroys itself if `instance` is already set, so Postfixes must check
  `ObstacleManager.instance == __instance`. `OnDestroy` clears `instance`, so a new manager (new
  scene) runs Awake again with a fresh serialized array. Registration must be repeatable.
- "No affix" is index 0 (`ObstacleAffixManager.None`); the draft fills `(0, None)` by default.
  `GetAffixByIndex` clamps negatives to 0. `IsValid` is `this != None`.
- `Obstacle.SetState` sets `colliders[i].enabled = true` on every cached collider (lines ~575, ~591, ~836),
  so disabling carrier colliders doesn't stick. They must be removed with `DestroyImmediate` before `Init`.
- `SurfaceManager.IsSwappableMaterial` matches by material NAME (contains a swappable material's name).
- `SpeedCamera` and `ScorePointZone` are NetworkBehaviours; the other zones are MonoBehaviours.
  `Obstacles.Ray` clashes with `UnityEngine.Ray`, so always qualify it.
- `GameManager.SpawnObstacleServerRpc` path (~line 3074/3119) uses `useHiddenList: true`.
  `GetDescriptionFromIndex(i, true)` returns `hiddenObstacleDescriptions[i]` when `i < hidden.Length`,
  so an appended card could resolve to a hidden card on that path. Check what uses it.
- Unity stripping removes MEMBERS, not just types, so a string search of the DLL isn't enough;
  only compiling proves an API exists. Confirmed by the compiler:
  - Missing: `MeshCollider.sharedMesh`, `SkinnedMeshRenderer.sharedMesh`, `Mathf.PI`, `LODGroup`.
  - Present: `GameObject.CreatePrimitive`, `Object.DestroyImmediate`, `AddComponent`,
    `GetComponentsInChildren`, `MeshFilter.sharedMesh`, `Renderer.sharedMaterial`, `LayerMask.LayerToName`.
  - Use `System.Math` for constants. For colliders, rely on the ones primitives come with (BoxCollider on Cube).

## Implemented: first placeable obstacle (Route A, borrowed carrier)
Written 2026-10-21. Builds cleanly against BepInEx 6.0.0-be.697 (installed in the game folder);
NOT yet run in game. Code: `src/Registry/`, `src/Obstacles/`, `src/Patches/`, `src/Diagnostics/`.
Marker format: `affixIndex = -(1000 + slot * 100 + affix)`.
The first obstacle is `BumperPillar` (square pillar from the Cube primitive, its BoxCollider, `BounceZone`).
To test: set `[Debug] ForceCard = BumperPillar` on the host.

First run (game v_1.0.30, 2026-10-21):
- Catalog: 67 cards, 1 hidden. Full list is in the `Catalog[i]` log lines.
- Every prefab, including modifiers, has exactly ONE extra NetworkBehaviour besides the Obstacle:
  `ClientNetworkTransform` on the root (owner-authoritative transform sync, which is how a
  player's obstacle moves on everyone's screen while they place it). The original carrier filter
  rejected anything with one, so no carrier was found and the card wasn't registered. Fixed: the
  filter now only rejects `ScorePointZone` and `SpeedCamera`.
- With the fix, the auto-picked carrier should be `Fence` (Catalog[2]: Prop, Static, plain
  Obstacle, 1 solid collider on layer `Obstacle`, no zone parts). Until card text is solved,
  the BumperPillar card looks exactly like "The Fence".
- Plain static props worth knowing as carriers: Fence[2], CheeseWedge[5], Donut[6],
  ToiletPaperRoll[9], WatermelonSlice[41]. Kill hazards use layer `Obstacle` or `MapObstacle`.
- The NullReferenceExceptions at quit come from the game's Steam integration (SteamTimeline,
  SteamFriends), not from us.
- Second run: registered at index 67 with carrier `FenceObstacle`, and ForceCard put it in draft
  slot 0. It shows as "THE FENCE" with 2 stars (our Uncommon) next to the real 1-star Fence.
  The draft UI reads rarity from our clone, but name, text and art from the carrier's fields.
  The session ended at SelectingObstacles, so no spawn/VisualSwap yet.
- "NetworkVariable is written to, but doesn't know its NetworkBehaviour yet" appears during map load
  too, before any of our code runs, so it's vanilla.
- Third run: picked and placed, it spawned as a green cube (the Fence material, tinted by
  `SetObstacleColors` with the player's colours). Hitting it made the car jump rather than bounce
  back. `BounceZone.useCollisionNormal` reflects the car's velocity about the contact normal;
  try `useCustomNormal`, a lower `bounceFactor`, or check which way the contact normal points.

### Materials and shaders (from the runtime dump)
- Vanilla parts use `Shader Graphs/ToonShading` materials (ToonWhite, ToonBlack, ToonRed, ToonYellow,
  ToonGreen, ToonBeige, ToonBrown, ToonWood, ToonMetal), coloured by `_Color` (also `_MainTex`, triplanar).
- Player colours: `PlayerPrimaryColor` (Shader Graphs/PlayerObstaclePrimary), `PlayerSecondaryColor`,
  `PlayerColorsPattern` (stripes; `_PatternIndex`, `_Tiling`). All take `_PlayerPrimaryColor` /
  `_PlayerSecondaryColor`, which `Obstacle.SetObstacleColors` sets on every renderer.
- Effect materials worth reusing by name: BoostPad, MegaBoostPad, Flames, Bubble, MagnetEffect, Magma,
  StopZone, BlinkingLight (RedBlinkingLight, PurpleUnlit), Concrete (Shader Graphs/Surface).
- `MaterialLibrary` collects all of these by name at ObstacleManager.Awake; toon colours are copies of
  ToonWhite with `_Color` set (keeping the name so Golden/surface swaps still match).

### Vanilla sizes (metres, mesh bounds)
Fence 3.4x2.2x0.8, CheeseWedge 2x2x4.3, Donut 5.8x5.6, ToiletPaperRoll 3.6x6.1x3.6, Egg 4.6x1.1x6.5,
WatermelonSlice 4.5x2.2x9.8, Torii 2.1x6.4x8.9, RotatingAxe 16.5 tall, Scissors 9.4x10.4, Pencil 10 long,
BoostPad 3.5x1x3.5, Pea 0.4. Surface swaps are 11 m cubes (Magma XL 20 m).

### Stripped Unity API (compile probe, 2026-10-21)
- Present: full `Mesh` API (SetVertices/Normals/UVs/Colors/Triangles, subMeshCount, indexFormat,
  Recalculate*), `Material` SetColor/HasProperty/shader.GetPropertyCount/Name, `BoxCollider` size/center,
  `SphereCollider` radius/center, `Texture2D` SetPixels32/Apply, `AnimationCurve` + wrap modes,
  4-arg `Keyframe`, `Renderer.materials` setter, Input System `Keyboard.current`, Newtonsoft.Json.
- Missing: `CapsuleCollider` radius/height/direction, `Renderer.sharedMaterials` setter,
  `MeshCollider.sharedMesh`, `SkinnedMeshRenderer.sharedMesh`, `Mathf.PI`, `LODGroup`.

### Zone details for building obstacles
- `AccelerationZone` (needs a `BoxCollider trigger` field, read in Awake): pushes along its
  transform.forward every physics step inside (`acceleration`, ForceMode.Acceleration), optional
  `setVelocityOnEnter`/`velocityOnEnter` kick along the car's forward. No IsOwner check.
- `SlowDownZone`: `AddForce(-velocity * slowDownFactor, Acceleration)` while inside; optional full stop.
- `BounceZone` modes: radial (away from the zone's position), `useCollisionNormal`, `useCustomNormal`
  (world space, not rotated with the obstacle), `useCustomVelocity`.
- Network animators only build their placement preview when the card's body type is Animated
  (`Obstacle.EnablePlacementMode`). Ours ride on a Static carrier, so they animate live while placing.

### Levels
- Tracks are Unity scenes: `Game.Levels.Level.sceneName`, loaded by `Game.SceneManager` with
  `LoadSceneAsync`. A new track would mean building a scene AssetBundle in Unity 2022.3 (the game's
  version), with the game's level scripts resolving; not done. For testing we spawn a Test Arena instead.
- The only height death is the fog plane: `PlayerNetworking` ~line 444 kills a car more than 3.5 m below
  `fogPlane`. Being high above the map is fine.

### Vanilla zone tuning (dumped 2026-10-21)
- Bubble: BounceZone radial, factor 1. Egg: custom normal up + custom velocity (0, 12.5, 0), counterNegative.
  Pencil: collision normal, factor 0.75, counterNegative.
- Fan: AccelerationZone 60. Magnet: -50 (pulls). HoneySplatter: SlowDownZone 4. StopSign: full stop.
- Sword and Nail: KillZone aligned 2.5 up (only kill when landed on). Axe, Scissors, BlackHole, Match,
  LandMine: plain KillZone.
- Radial or reflected bounces feel dead on solid props: the contact has already stopped the car when
  OnCollisionEnter runs. Our `push` zone sets a fixed velocity instead.
- Also stripped: `Rigidbody.mass` setter.

### Gravity, steering and surfaces
- Gravity: `SphereCarController` calls `World.GravityShapesManager.GetGravityAtPoint` every physics step;
  it sums every registered `GravityShape` (MonoBehaviour, registers in OnEnable). Maps use
  `GravityShapeInfinitePlane` (gravity 40). Jump height uses that gravity too.
- Steering: `Steer`, `AirSteer`, `Acceleration`, `Reverse` are auto-properties set from input callbacks.
- Surfaces (`World.Surface`, ScriptableObject): friction, accelerationModifier, stickyness, effects
  (material, previewMaterial, colours, sounds), carModifiers. `SurfaceManager.surfaces[]` is the network
  index used by `GameManager.SwapSurfaceLevelTileNetwork(tileId, index)`; tiles take
  `effects.material` (Instantiate) and set each `SurfaceInfo.surface`. The car reads `SurfaceInfo` from its
  ground raycast (`CurrentSurface`), which isn't updated while airborne.
- `ObstacleSurfaceSwap.surfaceToSwapTo` and `ObstacleScatter.obstacleToScatter`/`count` are plain fields
  on the prefab components, read when placed (`OnPlace`; the scatter spawns pieces on the host with
  `obstacleToScatter.Spawn(..., inScene: true, affixIndex)`).
- `SurfaceManager.GetRandomSurface()` can now return Reverse too (used by random surface effects).

### Rounds
- `networkVariables.roundIndex` (NetworkVariable<int>) is incremented by the host in
  `GameModeStateMachineClassic` on entering `ResetPlayers` after PlacingObstacles or ScoreBoard, i.e. at the
  start of every round, and reset to 0 for a new match (GameManager ~2217). We use it to reset knocked-over
  obstacles at the same moment on every machine.

### Placement flow (for handing a player a second obstacle)
- The host spawns each pick with `SpawnWithOwnership(player)`. `Obstacle.OnNetworkSpawn` (~line 476) calls
  `playerInfos.BindToObstacle(this, IsOwner)` for any obstacle not yet placed, so a freshly spawned owned
  obstacle automatically takes the player's controls.
- Placing: `PlaceObstacleClientRpc` -> owner's `PlayerData.PlaceObstacle` (sets the owner-writable
  `placedObstacle` NetworkVariable, `UnBindFromObstacle`) -> `OnPlace` on every machine.
- Host: `GameManager.CheckIfPlayersPlacedObstacles` ends the phase once every `placedObstacle` is true.
  On timer end (~line 3490) it sets `_hasHandledObstaclePlacementTimer` and force-places each player's
  `currentObstacle`.
- ToiletPairing: owner clears `placedObstacle` in the same frame it was set (host never sees true), host
  spawns the Sewer Exit into the player's hands from the `OnPlace` postfix. If the timer already ran out (or
  the toilet was spawned placed), the exit is dropped already placed and the owner re-sets the flag.
- Pairing rule (same on every machine): a toilet's exit is the lowest-id Sewer Exit of the same player
  spawned after it.

### Car state helpers
- `SphereCarController.Teleport(position, rotation, forward, velocity, angularVelocity)`: used by
  `GameManager.PlacePlayerAtSpawn(player)` and time trial rewinds. Run on the owner.
- Checkpoints: `PlayerData.passedCheckPoints` (NetworkList<ulong> timestamps, by index) and
  `LevelManager.instance.levelDefinition.checkpoints` (`Game.CheckPoint` MonoBehaviours).
- Car modifiers (`Player/CarModifier.cs`): ScriptableObjects with duration, speed/rotation/scale
  `ModifierValue`s (type Additive/Multiplicative, easing curve, value), killOnEnd, disableJump/Dash.
  `modifier.Register(controller, applier)`. `ApplyModifiers` runs `ClearModifiers` first every frame, so
  multiplicative scale doesn't compound. `AddScale` scales the controller's child transforms.

### Full-art cards (`ObstacleSelectionElement.SetStyle`)
- `isFullArt` hides border, icons and rarity stars and lifts the name. `overrideBackGroundMaterial` is the
  card background material, and `overrideBackGroundMaterialTexture` (a Sprite) goes into `backgroundImage`
  and hides the thumbnail. `overrideNameFontMaterial` gives the outlined name font.
- Vanilla full-art cards are the Unique/Legendary modifiers (thumbnails only 128x128; the art is the sprite).
  We copy material, font and shine from the first vanilla full-art card and build a Sprite from our PNG.
- Also stripped: `Mathf.SmoothStep` (use t*t*(3-2t)). Present: `Sprite.Create`, Netcode
  `CustomMessagingManager` named messages, `FastBufferWriter/Reader`, `Unity.Collections.Allocator`.

### Card text and art (`Menus.UI/ObstacleSelectionElement.cs`, `UI/TextProcessor.cs`)
- Draft card: `ObstacleSelectionElement.Init(description, affix)` sets
  `previewImage.texture = description.thumbnail` (a RawImage), and
  `nameLabel.text = TextProcessor.Process(description.displayName)` and the same for `description`.
  Rarity stars and style come from `ObstacleManager.GetSelectionStyle(description)`.
- `TextProcessor.Process(LocalizedString)` = `CustomTmpTags.ProcessTags(s.GetLocalizedString())`.
  Other places (collection grid, rules menu, GameSave stats, Steam timeline, scatter logs) also call
  `GetLocalizedString()` directly. So a Prefix on the parameterless
  `UnityEngine.Localization.LocalizedString.GetLocalizedString()` covers every label.
- `Object.Instantiate` deep-copies a ScriptableObject's serialized classes, so the clone has its
  own `LocalizedString` objects. We map those exact objects to our text (reference equality).
- `CustomTmpTags.ProcessTags` rewrites `<tag>word</tag>` using a serialized tag list; unknown tags
  pass through unchanged, so TextMeshPro's `<color=#hex>` works. The real tag names are logged
  (`TextTag:` and `CardText:` lines) the first time our card's text is shown.
- Stripped build still has `ImageConversion.LoadImage` (UnityEngine.ImageConversionModule) and all
  `GetLocalizedString` overloads. The plugin loads `<Id>.png` from next to the DLL as `thumbnail`.
  Vanilla thumbnail sizes are now in the dump (`thumb=WxH`).

Things to check on first run:
- The `Catalog[...]` lines: which carrier was auto-picked, and is its pivot on the ground?
- The pillar's height/position (assumes the carrier's pivot is at ground level).
- Do the carrier's leftover renderers stay invisible through placement, culling and surface swaps?
- Does the pillar collide (solid layer copied from the carrier) and bounce?
- Giant affix via `[Debug] ForceAffixIndex`.

Original plan, kept for reference:

1. **Dump the catalog.** Postfix `ObstacleManager.Awake`: log every `allowedObstacleDescriptions[i]`
   (index, `name`, `type`, `bodyBodyType`, `rarity`, `prefab.name`, `prefab.GetType().Name`,
   `allowedAffixes.Length`) plus the prefab's child components (KillZone, BounceZone, Zone,
   NetworkAnimatedTransformation, NetworkBehaviour, collider and renderer counts).
2. **Choose a carrier.** A `Prop` with `bodyBodyType == Static`, plain `Obstacle` class, no RigidBody,
   and no NetworkBehaviours on child objects. For a moving obstacle later, an `Animated` carrier.
3. **Register (all machines).** Clone the carrier's ObstacleDescription (new `id`, our rarity), keep
   `prefab` = carrier prefab, append to `allowedObstacleDescriptions`, log its index.
4. **Mark it (host).** Prefix the 6-argument `ObstacleDescription.Spawn`: for our card set
   `affixIndex = -100 - (cardIndex * 16 + (rolledAffix + 1))`. Card and affix both fit, and every
   vanilla reader treats it as "no affix".
5. **Swap it (all machines).** Prefix `Obstacle.OnNetworkSpawn`: if `affixIndex.Value <= -100`,
   decode the card, disable (don't destroy) the carrier's renderers, colliders and zone components,
   then instantiate our visuals as a child. Add behaviour with `AddComponent<KillZone>()` (set `parent`)
   or `BounceZone` etc. on our collider objects, and set `pointsToCheckForbiddenZones`.
   Never destroy objects holding a NetworkBehaviour: NGO indexes them.
6. **Restore affixes.** Prefix `Obstacle.ApplyAffix`: if the marker carries an affix, apply that affix's
   callbacks ourselves and `return false`.
7. **First version without Unity.** Before learning AssetBundles, build the visuals from Unity
   primitives (`GameObject.CreatePrimitive`) with a material copied from the carrier. That proves
   steps 1 to 6. Swap in a bundled model afterwards.

## Plan: modifier card ("Moon Jump", jumpHeight x1.5 for everyone)
Unconfirmed until tested in game. No vanilla card changes jump height, and `jumpHeight` survives
`ClearModifiers`, so the effect lasts the match.

1. **Dump the catalog first.** Postfix `ObstacleManager.Awake` and log every
   `allowedObstacleDescriptions[i]`: index, `name`, `type`, `rarity`, `maxQuantity`,
   `prefab.GetType().Name`, `allowedAffixes.Length`. We need the asset name of the carrier
   (the card whose prefab is an `ObstacleGameModifierIncreaseJumpCount`).
2. **Register (all machines).** In the same Postfix: `Object.Instantiate` the carrier's
   ObstacleDescription, give it a new `id`, our rarity and `maxQuantity` (0 = "Off"), and append it
   to `allowedObstacleDescriptions`. Keep `prefab` pointing at the carrier's prefab, so there's no new
   network prefab. Log `CustomCards: MoonJump at index N`.
3. **Mark it (host).** Prefix the 6-argument `ObstacleDescription.Spawn`: when `__instance` is
   our card, set `ref int affixIndex = -100 - registryIndex`. The NetworkVariable is set before
   `SpawnWithOwnership`, so it reaches clients in the spawn payload.
4. **Apply it (all machines).** Prefix `ObstacleGameModifierIncreaseJumpCount.ApplyModifier`:
   if `affixIndex.Value <= -100`, look up our card, do
   `foreach (var p in GameManager.Players) p.controller.jumpHeight *= factor;`, and
   `return false` to skip the vanilla effect. Otherwise run vanilla as normal.
5. **Force it (host).** Postfix `ObstacleManager.GetRandomObstaclesDescriptions`: when
   `Debug.ForceCard` is set, replace slot 0 with `(ourIndex, ourDescription)` before
   `GenerateObstaclesToSelect` copies the indices into the network lists.
6. **Text.** Still open (see below). Until solved the card shows the carrier's name and text.

Risks to check: whether the carrier prefab ever rolls an affix (check `allowedAffixes` in the
dump; our marker would overwrite it), whether `Awake` runs before anyone hosts or joins, and
`Debug.ForceCard` running only on the host.

## Open questions
- Does `ObstacleManager.Awake` run identically on host and clients, before hosting/joining?
  (`allowedObstacleDescriptions` is serialized, so Awake is the earliest point it's filled.)
- How do we give a cloned card its own text, given `displayName`/`description` are
  `LocalizedString`? Options: patch the UI that reads them, or point them at a custom table entry.
- Does the game expose any LAN or direct-connect option for testing?
