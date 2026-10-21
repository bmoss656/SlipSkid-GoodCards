namespace SlipSkid.CustomContent;

// Packs a registry slot and the rolled affix into Obstacle.affixIndex. Every vanilla reader
// treats a negative affixIndex as "no affix", so the marker is invisible to the game.
internal static class SpawnMarker
{
    private const int Base = 1000;
    private const int AffixSlots = 100;

    internal static int Encode(int slot, int affixIndex)
    {
        int affix = affixIndex < 0 ? 0 : affixIndex;
        if (affix >= AffixSlots)
        {
            Plugin.Log.LogWarning($"SpawnMarker: affix {affix} doesn't fit, dropping it");
            affix = 0;
        }
        return -(Base + slot * AffixSlots + affix);
    }

    internal static bool TryDecode(int value, out int slot, out int affixIndex)
    {
        slot = -1;
        affixIndex = 0;
        if (value > -Base)
            return false;
        int packed = -value - Base;
        slot = packed / AffixSlots;
        affixIndex = packed % AffixSlots;
        return true;
    }
}
