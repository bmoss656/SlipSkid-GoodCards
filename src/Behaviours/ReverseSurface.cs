using System.Linq;
using HarmonyLib;
using Player;
using UnityEngine;
using World;

namespace SlipSkid.CustomContent;

// A road surface that flips your steering, applied like Ice or Sand with a surface-swap card.
// - Surface swaps travel as an index into SurfaceManager.surfaces (GameManager.SwapSurfaceLevelTileNetwork),
//   so every machine appends the same Reverse surface to that array when its SurfaceManager wakes.
// - The car reads its surface from SurfaceInfo under it (CurrentSurface). In the air CurrentSurface keeps
//   the last ground surface, so we look straight down instead: steering stays flipped while you're
//   jumping over reversed road, and comes back once you're over normal road.
internal static class ReverseSurface
{
    internal static Surface Instance { get; private set; }

    private static int _cachedFrame = -1;
    private static SphereCarController _cachedCar;
    private static bool _cachedResult;

    internal static void Register(SurfaceManager manager)
    {
        if (!Instance)
            Instance = Create(manager.defaultSurface);
        if (!Instance || manager.surfaces.Contains(Instance))
            return;
        manager.surfaces = manager.surfaces.Append(Instance).ToArray();
        Plugin.Log.LogInfo($"Surfaces: added Reverse at index {manager.surfaces.Length - 1}");
    }

    private static Surface Create(Surface template)
    {
        if (!template || template.effects == null || !template.effects.material)
        {
            Plugin.Log.LogWarning("Surfaces: no default surface to copy; Reverse surface unavailable");
            return null;
        }
        // Asphalt grip and sounds, purple look.
        var surface = Object.Instantiate(template);
        surface.name = "CustomContent_Reverse";
        surface.hideFlags = HideFlags.DontUnloadUnusedAsset;
        surface.skidMarkColor = new Color32(150, 60, 220, 255);
        var material = new Material(template.effects.material) { name = template.effects.material.name, hideFlags = HideFlags.DontUnloadUnusedAsset };
        material.SetColor("_Color", new Color(0.42f, 0.16f, 0.72f));
        material.SetColor("_ColorSecondary", new Color(0.78f, 0.36f, 1f));
        surface.effects.material = material;
        surface.effects.mainColor = new Color(0.62f, 0.28f, 0.95f);
        surface.effects.lightColor = new Color(0.85f, 0.6f, 1f);
        surface.effects.darkColor = new Color(0.3f, 0.1f, 0.5f);
        return surface;
    }

    internal static bool IsReversed(SphereCarController car)
    {
        if (!Instance || !car || !car.player || !car.player.IsOwner)
            return false;
        if (_cachedFrame == Time.frameCount && _cachedCar == car)
            return _cachedResult;
        bool reversed;
        if (car.OnGround)
            reversed = car.CurrentSurface == Instance;
        else
            reversed = car.sphereRigidbody && Physics.Raycast(car.sphereRigidbody.position, Vector3.down, out var hit, 60f,
                car.floorLayerMask, QueryTriggerInteraction.Ignore)
                && hit.collider.TryGetComponent<SurfaceInfo>(out var info) && info.surface == Instance;
        _cachedFrame = Time.frameCount;
        _cachedCar = car;
        _cachedResult = reversed;
        return reversed;
    }
}

[HarmonyPatch(typeof(SurfaceManager), "Awake")]
internal static class SurfaceManagerAwakePatch
{
    private static void Postfix(SurfaceManager __instance)
    {
        if (SurfaceManager.instance == __instance)
            ReverseSurface.Register(__instance);
    }
}

[HarmonyPatch(typeof(SphereCarController), nameof(SphereCarController.Steer), MethodType.Getter)]
internal static class ReverseSteerPatch
{
    private static void Postfix(SphereCarController __instance, ref float __result)
    {
        if (ReverseSurface.IsReversed(__instance))
            __result = -__result;
    }
}

[HarmonyPatch(typeof(SphereCarController), nameof(SphereCarController.AirSteer), MethodType.Getter)]
internal static class ReverseAirSteerPatch
{
    private static void Postfix(SphereCarController __instance, ref float __result)
    {
        if (ReverseSurface.IsReversed(__instance))
            __result = -__result;
    }
}
