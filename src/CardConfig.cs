using BepInEx.Configuration;

namespace SlipSkid.CustomContent;

internal static class CardConfig
{
    // When set, the host's roll always offers this card in one slot. Empty = normal rolls.
    internal static ConfigEntry<string> ForceCard;
    internal static ConfigEntry<int> ForceAffixIndex;
    internal static ConfigEntry<bool> DebugKeys;
    internal static ConfigEntry<bool> VerboseLog;

    internal static void Bind(ConfigFile config)
    {
        DebugKeys = config.Bind("Debug", "EnableDebugKeys", false,
            "F6: spawn a flat test arena above the map and drive onto it. F7 (host): spawn every custom obstacle ahead of you.");
        VerboseLog = config.Bind("Debug", "VerboseLog", false,
            "Log the whole vanilla card catalog, materials and zone settings at startup (for modding).");
        ForceCard = config.Bind("Debug", "ForceCard", "",
            "Host only. A custom card id (e.g. BumperPillar) forces it into draft slot 0. * fills every slot with " +
            "custom cards; a comma-separated list (e.g. LongRoad,CurvedRoad) fills every slot from just those. Empty = normal rolls.");
        ForceAffixIndex = config.Bind("Debug", "ForceAffixIndex", 0,
            "Affix for the forced card: 0 = none, otherwise an index into ObstacleAffixManager's list.");
        CardRegistry.BindConfig(config);
    }
}
