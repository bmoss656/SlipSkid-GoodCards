using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.Mono;
using HarmonyLib;

namespace SlipSkid.CustomContent;

[BepInPlugin(Guid, Name, Version)]
// Earlier builds used other plugin ids. A leftover copy would register every card a second time and
// break lobby sync, so BepInEx must never load both.
[BepInIncompatibility("brad.slipskid.goodcards")]
[BepInIncompatibility("brad.slipskid.customcontent")]
public class Plugin : BaseUnityPlugin
{
    // Never change Guid after release: it names every player's config file.
    public const string Guid = "slipskid.goodcards";
    public const string Name = "Good Cards";
    public const string Version = "0.2.0";   // keep in step with thunderstore/manifest.json

    internal static ManualLogSource Log;

    private void Awake()
    {
        Log = Logger;
        CardConfig.Bind(Config);
        var harmony = new Harmony(Guid);
        harmony.PatchAll();
        foreach (var method in harmony.GetPatchedMethods())
            Log.LogInfo($"Patched {method.DeclaringType?.Name}.{method.Name}");
        Log.LogInfo($"{Name} {Version} loaded");
    }

    private void Update()
    {
        // Each system on its own, so one failing can't stop the others (or spam the log every frame).
        Guard.Run("TriggerBus", TriggerBus.Update);
        Guard.Run("CatalogSync", CatalogSync.Update);
        Guard.Run("Toilet", ToiletPairing.Update);
        if (CardConfig.DebugKeys.Value)
            Guard.Run("DebugSpawner", DebugSpawner.Update);
    }
}
