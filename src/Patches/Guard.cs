using System;
using System.Collections.Generic;
using Unity.Netcode;

namespace SlipSkid.CustomContent;

// Every Harmony patch body runs inside Guard: an exception in our code must never escape into the game's
// method, where it would break vanilla behaviour and every other mod patched onto the same method.
// Each distinct failure is logged once (patches can run every frame), then the patch steps aside.
internal static class Guard
{
    private static readonly HashSet<string> Reported = new();

    internal static void Run(string system, Action body)
    {
        try
        {
            body();
        }
        catch (Exception e)
        {
            Report(system, e);
        }
    }

    // For prefixes that may skip the original: on failure, let the original (and other mods) run.
    internal static bool Prefix(string system, Func<bool> body)
    {
        try
        {
            return body();
        }
        catch (Exception e)
        {
            Report(system, e);
            return true;
        }
    }

    // Named message handlers: a short or malformed message (say, from a different Good Cards version) is
    // logged and dropped instead of throwing into Netcode's message processing.
    internal static CustomMessagingManager.HandleNamedMessageDelegate Handler(string system,
        CustomMessagingManager.HandleNamedMessageDelegate handler) =>
        (sender, reader) =>
        {
            try
            {
                handler(sender, reader);
            }
            catch (Exception e)
            {
                Report(system, e);
            }
        };

    internal static void Report(string system, Exception e)
    {
        if (Reported.Add($"{system}|{e.GetType().Name}|{e.Message}"))
            Plugin.Log.LogError($"{system}: {e}");
    }
}
