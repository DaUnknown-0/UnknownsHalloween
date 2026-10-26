// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
// Based on The Other Roles (https://github.com/TheOtherRolesAU/TheOtherRoles), GPL-3.0.

/*
 * UNKNOWN'S HALLOWEEN - add-on for Unknown's Collection.
 *
 *   - HalloweenCostumes.cs: four full-body costume hats (Freddy, Jason, Xenomorph, Ghostface) with
 *     idle/walk animation and a kill cutscene per costume.
 *   - Xenomorph.cs: the Xenomorph role (neutral killer, transformation on a button).
 *   - Villa/: the map "Hollowmere Manor" for Unknown's Atlas (soft dependency; registered only when
 *     Atlas is installed, through Atlas' public AtlasMaps API).
 *
 * Split out of Unknown's Collection on 2026-10-05 so the costumes of third-party characters live in a
 * repository of their own: whatever happens to this repo never touches Unknown's Collection.
 * Everything still runs on UC's infrastructure (RPC channel 230, option tabs, draft, guesser,
 * tick/reset hooks), hence the hard dependency. Nothing in Unknown's Collection mentions this mod;
 * the hooks into UC are reflection and Harmony postfixes from this side.
 *
 * Family plumbing like the other mods: Mod Manager registration (AppDomain), self-updater
 * (HalloweenUpdater), version line in the shared "Unknown's Collective" readout. The version is
 * stamped from the git tag by the release workflow.
 */

using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using HarmonyLib;
using UnityEngine;

namespace UnknownsHalloween;

[BepInPlugin(PluginGuid, PluginName, PluginVersion)]
[BepInProcess("Among Us.exe")]
[BepInDependency("me.eisbison.theotherroles", BepInDependency.DependencyFlags.HardDependency)]
[BepInDependency("com.tormod.unknownscollection", BepInDependency.DependencyFlags.HardDependency)]
[BepInDependency(AtlasGuid, BepInDependency.DependencyFlags.SoftDependency)]
public class HalloweenPlugin : BasePlugin
{
    public const string PluginGuid = "com.daunknown.unknownshalloween";
    public const string PluginName = "Unknown's Halloween";
    public const string PluginVersion = "0.1.3.25";
    public static readonly System.Version Version = System.Version.Parse(PluginVersion);
    private const string AtlasGuid = "com.daunknown0.atlas";

    public static ManualLogSource Logger { get; private set; }
    public static ConfigEntry<bool> CfgEnabled;
    // Accessibility (2026-10-26, user): local switch, damps every screen flash of this mod (kill-scene band, Omens thunder,
    // candy shield flash, fake alarm, Sole Survivor start flash) for players sensitive to flashing light.
    public static ConfigEntry<bool> ReduceFlashes;
    /// <summary>true = flashes damped (local "Reduce Flashes" switch).</summary>
    internal static bool Calm => ReduceFlashes != null && ReduceFlashes.Value;

    // Same AppDomain contract as the angel blink switch: UC shows it on its settings page.
    private static void RegisterFlashToggle()
    {
        try
        {
            var domain = System.AppDomain.CurrentDomain;
            lock (domain)
            {
                if (domain.GetData("Unknowns.Options.Toggles") is not System.Collections.Generic.List<object> list)
                {
                    list = new System.Collections.Generic.List<object>();
                    domain.SetData("Unknowns.Options.Toggles", list);
                }
                list.Add(new object[] { (System.Func<string>)(() => "Reduce Flashes"), (System.Func<bool>)(() => Calm),
                                        (System.Action<bool>)(v => { if (ReduceFlashes != null) ReduceFlashes.Value = v; }) });
            }
        }
        catch (System.Exception e) { Logger?.LogWarning($"[Halloween] flash toggle not registered: {e.Message}"); }
    }

    public override void Load()
    {
        Logger = Log;
        CfgEnabled = Config.Bind("General", "Enabled", true, "Master switch of Unknown's Halloween.");
        HollowmereWorld.BlinkEffect = Config.Bind("Weeping Angels", "BlinkEffect", true,
            "Show the eyelid blink on your screen when the Weeping Angels make you blink. Off = no visual effect; you still blink (the host decides it).");
        HollowmereWorld.RegisterBlinkToggle();
        ReduceFlashes = Config.Bind("Accessibility", "ReduceFlashes", false,
            "Damp all screen flashes of Unknown's Halloween (kill-scene band, thunder, shield and alarm flashes) on your screen. Only affects you.");
        RegisterFlashToggle();
        HwGuessSpell.LocalSwitch = Config.Bind("Sounds", "GuesserSpellSound", true,
            "Play \"Avada Kedavra ... Kurwa!\" at every Guesser shot (contains a swear word). The host can switch it off for everyone (option 2102).");

        // Mod Manager (hosted by Forgotten Fixes / UsefulTORStuff): AppDomain registry, no compile-time
        // reference. Before the Enabled gate, so a disabled mod still shows up there.
        try
        {
            var modData = new System.Collections.Generic.Dictionary<string, object>
            {
                { "Guid", PluginGuid },
                { "Name", PluginName },
                { "Version", Version },
                { "RepositoryOwner", HalloweenUpdater.RepositoryOwner },
                { "RepositoryName", HalloweenUpdater.RepositoryName },
                { "ButtonColor", new Color(1f, 0.46f, 0.09f) },
                { "Enabled", CfgEnabled },
                { "RuntimeEnabled", CfgEnabled.Value },
            };
            System.AppDomain.CurrentDomain.SetData($"ModManager.RegisteredMod.{PluginGuid}", modData);
        }
        catch (System.Exception ex)
        {
            Logger.LogError($"[Halloween] Failed to register in Mod Manager: {ex}");
        }

        AddComponent<HalloweenUpdater>();

        if (!CfgEnabled.Value)
        {
            Logger.LogInfo($"[Halloween] {PluginName} {PluginVersion}: Enabled=false - patches NOT applied.");
            return;
        }

        // Large artwork (costumes, kill scenes, both maps) comes from the asset repository (HalloweenAssets). Before
        // PatchAll: the costume setup there asks whether the packages are ready.
        var source = Config.Bind("Assets", "DownloadSource", "",
            "Leave empty. Test override for the asset download (only the asset repository or http://127.0.0.1:<port>/).");
        HalloweenAssets.Start(AddComponent<HalloweenAssetHost>(), source.Value);

        // PatchAll runs the HarmonyPrepare hooks that set the costumes and the role up
        // (HalloweenCostumes.KillHook.Prepare, Xenomorph.ResetPatch.Prepare).
        new Harmony(PluginGuid).PatchAll();
        HwDeathCause.Register();

        // Hollowmere Manor needs Unknown's Atlas; without it the map simply does not exist.
        bool atlas = false;
        try { atlas = BepInEx.Unity.IL2CPP.IL2CPPChainloader.Instance.Plugins.ContainsKey(AtlasGuid); } catch { }
        if (atlas)
        {
            // Options and RPC handlers now; the map itself joins Atlas once its packages are there (HalloweenAssets).
            try { RegisterVilla(); }
            catch (System.Exception ex) { Logger.LogError($"[Halloween] Hollowmere Manor registration failed: {ex}"); }
            try { RegisterGraveyard(); }
            catch (System.Exception ex) { Logger.LogError($"[Halloween] Ravenhollow Cemetery registration failed: {ex}"); }
        }
        Logger.LogInfo($"[Halloween] {PluginName} {PluginVersion} loaded{(atlas ? "" : " (Unknown's Atlas missing: no Hollowmere Manor)")}.");
    }

    // Separate method so the Atlas types are only resolved when Atlas is actually installed.
    [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
    private static void RegisterVilla() => HollowmereMap.Register();

    [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
    private static void RegisterGraveyard() => GraveyardMap.Register();
}

// Version line in the top-corner PingTracker readout, folded into the shared "Unknown's
// Collective" line alongside this project family's other mods (see UnknownsCollective.cs).
[HarmonyPatch(typeof(PingTracker), nameof(PingTracker.Update))]
internal static class HalloweenVersionDisplayPatch
{
    private static string cachedLine;

    [HarmonyPriority(Priority.Low)]
    public static void Postfix(PingTracker __instance)
    {
        if (__instance == null || __instance.text == null) return;
        string text = __instance.text.text;
        if (string.IsNullOrEmpty(text)) return;

        cachedLine ??= $"<color=#FF7518>{HalloweenPlugin.PluginName}</color> v{VersionDisplay.Format(HalloweenPlugin.Version)}";
        UnknownsCollective.Contribute(HalloweenPlugin.PluginGuid, cachedLine);
        text = UnknownsCollective.Render(__instance.text, text);
        // TMP rebuilds its mesh on every assignment, even with an identical string
        if (!string.Equals(__instance.text.text, text, System.StringComparison.Ordinal))
            __instance.text.text = text;
    }
}
