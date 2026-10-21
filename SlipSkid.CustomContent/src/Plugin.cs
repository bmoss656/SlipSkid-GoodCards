using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.Mono;
using HarmonyLib;

namespace SlipSkid.CustomContent;

[BepInPlugin(Guid, Name, Version)]
public class Plugin : BaseUnityPlugin
{
    public const string Guid = "brad.slipskid.customcontent";
    public const string Name = "Custom Content";
    public const string Version = "0.1.0";

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
        DebugSpawner.Update();
    }
}
