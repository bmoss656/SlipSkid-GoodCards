# Changelog

## 0.2.0
**Everyone in the lobby must update together** (the cards and online messages changed).

Cards
- 5 new cards: **The Baby Oil** (a slick with almost no grip), **The Vacuum** (drags you into its nozzle,
  then spits you back out), **The Wind Tunnel** (too slow and the fans blow you back out), **The Speed Bump**
  (launches anyone crossing it too fast) and **The Pinball Flipper**.
- Retired 6 cards that didn't add much: Domino Line, Tin Can Pyramid, Garden Rake, Jack-in-the-Box,
  Whack-a-Mole and Pizza Cutter. They no longer come up in drafts. 40 cards in all.
- Good Cards cards are much rarer: each draft card has a 20% chance to be one of ours (host setting
  `[Draft] CustomCardChance`). Before, they took up almost every slot.

Fixes
- Toilet: you can now place its Sewer Exit, and the camera follows it. Works with or without a placement
  timer, and each Toilet always pairs with its own exit.
- Toilet: much easier to get into. The flush zone covers the whole bowl, from just above the road to well over
  the rim, plus the tank, so it no longer acts like a wall. Its bath-mat ramp is gone (build one with other
  cards), and the lid no longer clips through the tank.
- Sewer Exit: cars now shoot out of the pipe's mouth, the side shown on the card. The opening no longer flickers.
- Magnifying Glass: huge cars keep their grip instead of sliding around.
- Shock Mines and Teleport Grenades only go off mid-race, so nothing can use them up during placement.
- Global "turn every road into X" cards now convert Reverse road too.

Playing with other mods
- Works alongside other card mods such as MoreCards and EvenMoreCards: the host's card list is copied
  to every player when they join, so mod load order no longer matters. If a player is missing a card the host
  has, it's never drafted, and mismatched mods or versions are reported in the log.
- An error in Good Cards is logged instead of breaking the game or another mod. Good Cards only rebuilds its
  own obstacles, and BepInEx won't load an old Good Cards build next to this one.

Looks
- The Baby Oil and Hot Sauce puddles look like liquid (glossy and rippling) and splash up under every car that
  drives through; drifting on them sprays oil or sauce. Hot Sauce is 20% bigger.
- New models: Baguette, Hairbrush, Blender, Shaken Soda, Whoopee Cushion, Toilet (and its card art) and
  Sewer Exit.

## 0.1.1
- The config file is now `BepInEx/config/slipskid.goodcards.cfg` (the plugin ID changed). Any settings
  you changed in 0.1.0 go back to their defaults; the old file can be deleted.
- README tidy-up. No card changes: 0.1.0 and 0.1.1 offer the same cards, but everyone in a lobby should
  still update together.

## 0.1.0
- First release: 41 new draft cards (37 obstacles and 4 epic full-art cards), plus the Toilet's Sewer Exit.
  Online play supported; everyone needs the same version.
