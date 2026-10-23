# SlipSkid-GoodCards

Good Cards: a BepInEx 6 mod for Slip & Skid that adds 40 draft cards (obstacles, traps, launchers, road
pieces and full-art epic cards). The player-facing description is [thunderstore/README.md](thunderstore/README.md).

## Building
1. Install BepInExPack SlipSkid into the game (or an r2modman profile) and launch once.
2. Copy your paths into `local.props` (git-ignored): `GameDir`, and `BepInExDir` if BepInEx isn't in the game folder.
3. `dotnet build -c Release` builds `SlipSkid.GoodCards.dll` and copies it plus `assets/` into
   `BepInEx/plugins/GoodCards`.

## Packaging for Thunderstore
`powershell -ExecutionPolicy Bypass -File tools\package.ps1` writes `dist/GoodCards-<version>.zip`.
Bump the version in both `src/Plugin.cs` and `thunderstore/manifest.json` (the script checks they match)
and add a `thunderstore/CHANGELOG.md` entry.

## Making obstacles
Models are authored in Blender (5.x) from `tools/blender/ss_models.py` using `tools/blender/ss_lib.py`,
which exports `assets/obstacles/<Id>.json` and renders card art. See [docs/game-notes.md](docs/game-notes.md)
for how the game works under the hood.
