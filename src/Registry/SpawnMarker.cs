namespace SlipSkid.CustomContent;

// Packs a registry slot, the rolled affix and an optional pair key into Obstacle.affixIndex. Every vanilla
// reader treats a negative affixIndex as "no affix", so the marker is invisible to the game.
// Layout: -(1000 + pair * 100000 + slot * 100 + affix). Pair 0 means "no pair", which is the 0.1.x format.
// The pair key ties a Toilet to its Sewer Exit on every machine (NetworkObjectIds get recycled, so spawn
// order can't be trusted for that).
internal static class SpawnMarker
{
    private const int Base = 1000;
    private const int AffixSlots = 100;
    private const int PairStride = 100000;   // room for 1000 slots
    internal const int MaxPair = 20000;      // keeps the packed value inside int

    internal static int Encode(int slot, int affixIndex, int pair = 0)
    {
        int affix = affixIndex < 0 ? 0 : affixIndex;
        if (affix >= AffixSlots)
        {
            Plugin.Log.LogWarning($"SpawnMarker: affix {affix} doesn't fit, dropping it");
            affix = 0;
        }
        if (pair < 0 || pair > MaxPair)
            pair = 0;
        return -(Base + pair * PairStride + slot * AffixSlots + affix);
    }

    internal static bool TryDecode(int value, out int slot, out int affixIndex) =>
        TryDecode(value, out slot, out affixIndex, out _);

    internal static bool TryDecode(int value, out int slot, out int affixIndex, out int pair)
    {
        slot = -1;
        affixIndex = 0;
        pair = 0;
        if (value > -Base)
            return false;
        int packed = -value - Base;
        pair = packed / PairStride;
        packed %= PairStride;
        slot = packed / AffixSlots;
        affixIndex = packed % AffixSlots;
        return true;
    }
}
