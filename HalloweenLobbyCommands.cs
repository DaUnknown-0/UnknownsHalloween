// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * HalloweenLobbyCommands - the mod author's Halloween gags in the lobby (User 2026-11-27; Unknown's Collection and
 * Forgotten Fixes have the others, same shape "<x>.trigger.<y>(<args>)"):
 *
 *   halloween.trigger.scene(all|Name[, key])   a costume kill scene on the target's screen (random, or the key)
 *   halloween.trigger.summon(all|Name[, key])  a summoning scene: diablo, baal, mephisto, cthulhu, ghost (random)
 *   halloween.trigger.angel(all|Name)          the Weeping Angel's scene on the target's screen (the angels themselves
 *                                              are Hollowmere props, not loaded in the lobby)
 *   halloween.trigger.candy(all|Name)          a treat card with a random effect, the munch, nothing applied
 *   halloween.trigger.costume(all|Name)        a random built-in costume for 15 s
 *   halloween.trigger.candyrain()              candies rain down over everybody's screen
 *
 * Only in the lobby, only from the author's account (HalloweenOwner, checked by every client), the chat line stays
 * visible. Local and cosmetic, no RPC; looks go back after the time, at the latest when a game starts.
 */

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using HarmonyLib;
using UnityEngine;
using TheOtherRoles;

namespace UnknownsHalloween;

internal static class HalloweenLobbyCommands
{
    private static readonly Regex Rx = new(@"^\s*halloween\.trigger\.([a-z]+)\s*\((.*)\)\s*$", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
    private static readonly Dictionary<string, float> lastRun = new();
    private static readonly List<(float until, PlayerControl p)> restore = new();
    private static readonly List<(GameObject go, Vector3 vel, float until)> rain = new();
    private static readonly string[] Summons = { "diablo", "baal", "mephisto", "cthulhu", "ghost" };

    private static bool InLobby()
    {
        try
        {
            var c = AmongUsClient.Instance;
            return c != null && c.GameState == InnerNet.InnerNetClient.GameStates.Joined && LobbyBehaviour.Instance != null;
        }
        catch { return false; }
    }

    [HarmonyPatch(typeof(ChatController), nameof(ChatController.AddChat))]
    private static class ChatPatch
    {
        public static void Postfix([HarmonyArgument(0)] PlayerControl sourcePlayer, [HarmonyArgument(1)] string chatText)
        {
            try
            {
                if (string.IsNullOrEmpty(chatText)) return;
                var m = Rx.Match(chatText);
                if (!m.Success || !InLobby() || !HalloweenOwner.Is(sourcePlayer)) return;
                string cmd = m.Groups[1].Value.ToLowerInvariant();
                if (lastRun.TryGetValue(cmd, out float last) && Time.time - last < 4f) return;
                lastRun[cmd] = Time.time;
                var parts = m.Groups[2].Value.Split(',').Select(x => x.Trim()).ToList();
                string who = parts.Count > 0 ? parts[0] : "";
                string key = parts.Count > 1 ? parts[1].ToLowerInvariant() : "";
                var lp = PlayerControl.LocalPlayer;
                bool me = lp != null && Players(who).Any(p => p.PlayerId == lp.PlayerId);
                switch (cmd)
                {
                    case "scene":
                        if (me) Scene(key.Length > 0 ? key : RandomScene());
                        break;
                    case "summon":
                        if (me) Scene("summon_" + (Summons.Contains(key) ? key : Summons[UnityEngine.Random.Range(0, Summons.Length)]));
                        break;
                    case "angel":
                        if (me) Scene("angel_a" + UnityEngine.Random.Range(1, 5));
                        break;
                    case "candy":
                        if (me) Candy();
                        break;
                    case "costume":
                        foreach (var p in Players(who)) Costume(p);
                        break;
                    case "candyrain":
                        CandyRain();
                        break;
                    default: return;
                }
                HalloweenPlugin.Logger?.LogInfo($"[Halloween/LobbyCmd] halloween.trigger.{cmd}({m.Groups[2].Value}).");
            }
            catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"[Halloween/LobbyCmd] failed: {e.Message}"); }
        }
    }

    private static List<PlayerControl> Players(string arg)
    {
        var all = PlayerControl.AllPlayerControls.ToArray().Where(p => p != null && p.Data != null && !p.Data.Disconnected).ToList();
        if (arg.Length == 0 || arg.Equals("all", StringComparison.OrdinalIgnoreCase)) return all;
        var exact = all.Where(p => string.Equals(p.Data.PlayerName?.Trim(), arg, StringComparison.OrdinalIgnoreCase)).ToList();
        if (exact.Count == 1) return exact;
        var start = all.Where(p => (p.Data.PlayerName ?? "").Trim().StartsWith(arg, StringComparison.OrdinalIgnoreCase)).ToList();
        return start.Count == 1 ? start : new List<PlayerControl>();
    }

    private static string RandomScene()
    {
        var keys = HalloweenCostumes.SceneList().Select(s => s.Split('|')[0])
            .Where(k => !k.StartsWith("summon_") && !k.StartsWith("angel_") && k != "demon" && !k.EndsWith("random")).ToList();
        return keys.Count > 0 ? keys[UnityEngine.Random.Range(0, keys.Count)] : "freddy";
    }

    private static void Scene(string key) =>
        HalloweenPlugin.Logger?.LogInfo("[Halloween/LobbyCmd] " + HalloweenCostumes.Preview(key));

    private static void Candy()
    {
        var all = Enum.GetValues(typeof(Treat)).Cast<Treat>().ToList();
        var fx = all[UnityEngine.Random.Range(0, all.Count)];
        TreatFx.ShowPopup(0, "Lobby Candy", fx, fx, false, 0, "");
        TreatFx.Munch();
    }

    private static void Costume(PlayerControl p)
    {
        var hats = HalloweenCostumes.CostumeHatIds();
        if (hats.Count == 0) return;
        var o = p.Data.DefaultOutfit;
        try { p.setLook(p.Data.PlayerName, o.ColorId, hats[UnityEngine.Random.Range(0, hats.Count)], o.VisorId, o.SkinId, o.PetId); } catch { }
        restore.Add((Time.time + 15f, p));
    }

    private static void CandyRain()
    {
        var hud = HudManager.Instance;
        if (hud == null) return;
        for (int i = 0; i < 40; i++)
        {
            Sprite sp;
            try { sp = TreatFx.KindSprite(UnityEngine.Random.Range(0, 12)); } catch { continue; }
            if (sp == null) continue;
            var go = new GameObject("CandyRain") { layer = hud.gameObject.layer };
            go.transform.SetParent(hud.transform, false);
            go.transform.localPosition = new Vector3(UnityEngine.Random.Range(-5.5f, 5.5f), 3.4f + UnityEngine.Random.Range(0f, 4f), -55f);
            go.transform.localScale = Vector3.one * UnityEngine.Random.Range(0.3f, 0.5f);
            go.transform.localRotation = Quaternion.Euler(0f, 0f, UnityEngine.Random.Range(0f, 360f));
            go.AddComponent<SpriteRenderer>().sprite = sp;
            rain.Add((go, new Vector3(UnityEngine.Random.Range(-0.4f, 0.4f), -UnityEngine.Random.Range(1.6f, 3f), UnityEngine.Random.Range(-120f, 120f)), Time.time + 6f));
        }
        try { TreatFx.Munch(); } catch { }
    }

    [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
    private static class TickPatch
    {
        public static void Postfix()
        {
            if (restore.Count == 0 && rain.Count == 0) return;
            bool lobby = InLobby();
            for (int i = restore.Count - 1; i >= 0; i--)
            {
                if (lobby && Time.time < restore[i].until) continue;
                var p = restore[i].p;
                restore.RemoveAt(i);
                try { if (p != null) p.setDefaultLook(); } catch { }
            }
            for (int i = rain.Count - 1; i >= 0; i--)
            {
                var (go, vel, until) = rain[i];
                if (go == null || !lobby || Time.time >= until)
                {
                    if (go != null) UnityEngine.Object.Destroy(go);
                    rain.RemoveAt(i);
                    continue;
                }
                go.transform.localPosition += new Vector3(vel.x, vel.y, 0f) * Time.deltaTime;
                go.transform.localRotation *= Quaternion.Euler(0f, 0f, vel.z * Time.deltaTime);
            }
        }
    }

    [HarmonyPatch(typeof(IntroCutscene), nameof(IntroCutscene.CoBegin))]
    private static class StartPatch
    {
        public static void Prefix()
        {
            foreach (var r in restore) { try { if (r.p != null) r.p.setDefaultLook(); } catch { } }
            restore.Clear();
            foreach (var r in rain) { if (r.go != null) UnityEngine.Object.Destroy(r.go); }
            rain.Clear();
        }
    }
}
