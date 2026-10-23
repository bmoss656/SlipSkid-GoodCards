using System.Collections.Generic;
using UnityEngine;
using World;

namespace SlipSkid.CustomContent;

// Liquid slicks (Baby Oil, Hot Sauce): a copy of the default road surface with its own grip and colour. The car reads the surface
// from the SurfaceInfo on whatever its ground raycast hits, so a thin solid collider carrying one is enough.
// - friction: sideways grip (with driftFriction) and how fast the car stops with no throttle.
// - stickyness: how much steering turns the car.
// - accelerationModifier: engine push.
// Built on every machine; it's never added to SurfaceManager.surfaces (those indices go over the network).
internal static class OilSurface
{
    private static readonly Dictionary<(float, float, float, Color32), Surface> Cache = new();

    // `tint` colours the skid marks and the car's drift/wheelspin spray on it.
    internal static Surface Get(float grip, float steer, float engine, Color32 tint)
    {
        var key = (grip, steer, engine, tint);
        if (Cache.TryGetValue(key, out var cached) && cached)
            return cached;
        var template = SurfaceManager.instance ? SurfaceManager.instance.defaultSurface : null;
        if (!template)
        {
            Plugin.Log.LogWarning("Slick: no default surface to copy; it will drive like plain road");
            return null;
        }
        var surface = Object.Instantiate(template);
        surface.name = "GoodCards_Oil";
        surface.hideFlags = HideFlags.DontUnloadUnusedAsset;
        surface.friction = template.friction * grip;
        surface.stickyness = template.stickyness * steer;
        surface.accelerationModifier = template.accelerationModifier * engine;
        surface.skidMarkColor = new Color32(tint.r, tint.g, tint.b, 120);
        surface.wetness = 1f;
        // The car's own drift and wheelspin particles take their colours and amounts from the surface:
        // make them the liquid's colour instead of grey road dust.
        var fx = surface.effects;
        if (fx != null)
        {
            Color main = tint;
            fx.mainColor = main;
            fx.lightColor = Color.Lerp(main, Color.white, 0.6f);
            fx.darkColor = main * 0.8f;
            fx.driftParticlesMax = Mathf.Max(fx.driftParticlesMax, 90);
            fx.slipParticlesMax = Mathf.Max(fx.slipParticlesMax, 90);
        }
        Cache[key] = surface;
        Plugin.Log.LogInfo($"Slick: #{tint.r:X2}{tint.g:X2}{tint.b:X2} surface friction {surface.friction:0.###}, steering {surface.stickyness:0.###}, " +
                           $"engine {surface.accelerationModifier:0.###}");
        return surface;
    }
}
