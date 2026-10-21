using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.Mono;
using HarmonyLib;

namespace SlipSkid.CustomContent;

[BepInPlugin(Guid, Name, Version)]
public class Plugin : BaseUnityPlugin
{
    // Never change Guid after release: it names every player's config file.
    public const string Guid = "slipskid.goodcards";
    public const string Name = "Good Cards";
    public const string Version = "0.1.0";   // keep in step with thunderstore/manifest.json

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
        TriggerBus.Update();
        if (CardConfig.DebugKeys.Value)
            DebugSpawner.Update();
    }
}
