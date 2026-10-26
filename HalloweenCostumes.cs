// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * HalloweenCostumes - full-body costume hats (Freddy, Jason, Xenomorph, Ghostface, since
 *   2026-10-13 Thing, Predator, Sadako, since 2026-10-16 Spider, BVB Fan, Angel Ghost, since 2026-10-20
 *   Pumpkin Head, Reaper, Vampire, Medusa, since 2026-10-25 Weeping Angel) with
 *   - a 16-frame idle loop and a 12-frame walk loop at 10 fps,
 *   - a back layer (dark trouser openings / robe hem) and a ladder pose,
 *   - a frame-by-frame kill cutscene per costume in the vanilla kill-overlay slot.
 *
 * Until 2026-10-05 this lived in Unknown's Collection (UCHalloween.cs, kept out of git); now it is
 * its own mod. The hats still go through the registration path of the regular UC hats:
 *   - UCHats' private ResolveHatsDirectory / Register / SetBounceNode are reached by reflection
 *     (they do not care which assembly the hats come from).
 *   - Extraction and sprite loading are done HERE, because UCHats reads embedded resources from its
 *     own assembly and the images now sit in this one (logical name UnknownsHalloween.Resources.hats.<file>).
 *   - Setup runs from a HarmonyPrepare of the kill hook, which this plugin's PatchAll calls during
 *     Load(). Unknown's Collection has loaded by then (hard dependency), long before TOR's hat
 *     loader coroutine is done.
 *
 * Kill cutscenes play ONLY when the killer is wearing the matching costume (current outfit, so a
 * camouflaged or morphed killer never shows it), on a normal field kill that no role cutscene of
 * UCKillOverlay has already claimed, and only if the HOST has them on (option 1793, then one per
 * costume from 1970). Audience is whoever the vanilla overlay would have shown to.
 * Each frame is five images: killer (back), the victim split into an untinted part (outline,
 * visor) plus a body mask and a shade mask that are tinted in the victim's colours, and the
 * foreground (blade tip, blood, impact). Scenes with killer layers (spider v2) add the killer's own
 * crewmate under and partly over the costume, split the same way and tinted in the killer's colours.
 * The victim deliberately does NOT go through the game's
 * player material: that shader obeys sprite masks, and an open chat window cut a rectangle out of
 * the victim in the first playtest (2026-10-05).
 * Sound is the vanilla kill-overlay stinger (own synthesized tracks were tried and dropped on
 * 2026-10-05: "passen einfach nicht zu Among Us").
 * Frames are decoded one at a time and thrown away again - a whole strip in memory would cost
 * well over 200 MB in a 32-bit process.
 *
 * HalloweenCostumes.Preview("freddy" | "jason" | "xeno" | "ghost" | "thing" | "predator" | "sadako" | "spider" | "pumpkin" | "reaper"
 * | "vampire" | "medusa") plays a cutscene locally as if the
 * local player had just been killed (Role Control: /killanim).
 */

using HarmonyLib;
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using BepInEx.Unity.IL2CPP.Utils;
using TheOtherRoles;
using TheOtherRoles.Modules.CustomHats;
using UnityEngine;
using UnknownsCollection;

namespace UnknownsHalloween {
    public static class HalloweenCostumes {
        private const string Res = "UnknownsHalloween.Resources.hats.";
        private const float HatFps = 10f;
        private const float KillFps = 15f;
        private const int IdleFrames = 16;
        private const int WalkFrames = 12;     // = the 12 sprites of the crewmate's own run cycle
        // Which walk frame the run cycle starts on. The painted legs are tied to the crewmate's
        // own run animation; if the legs look out of step in a playtest, this is the one knob.
        private const int WalkPhaseOffset = 0;

        private sealed class Costume {
            public string Key;          // file key of the hat frames  (hw_<Key>_...)
            public string KillKey;      // file key of the kill frames (hk_<KillKey>_...); null = no cutscene (vanilla kill)
            public string Name;         // hat name in the shop
            public string HatId;
            public int KillFrames;
            public int[] Flashes;       // frames on which the red band flashes
            public float KillHold;      // seconds the last kill frame stays up before the overlay closes (0 = closes right away)
            public bool HasLegs;        // walk loop has painted legs -> hide the back layer while running
            public Sprite[] Idle, Walk;
            public bool HasAccent;      // highlight masks (hw_<Key>_acc_N) that are tinted in the wearer's colour
            public Sprite[] IdleAcc, WalkAcc;
            public bool FramesTried;
            public KillScene[] Alt;     // further cutscenes of this costume; one of all is picked at random
            public bool HidesBody;      // the image IS the figure: body, skin and visor cosmetic are hidden (HalloweenCorpse.BodylessHats)
            public bool NoLiveBob;      // no walk bob at all: idle frames while walking, sync held while alive (User 2026-10-24)
            public bool KillerLayers;   // the main cutscene shows the crewmate under the costume in the KILLER's colour (u*/o* layers)
            // Still walk (spider, 2026-10-17): the crewmate keeps its idle pose while moving (no run
            // animation, no bob, StillWalkPatch) and the costume plays its own walk loop on its own clock,
            // WalkFps frames per second, as many frames as hw_<Key>_walk_N exist (painted on the idle pose).
            public bool StillWalk;
            public float WalkFps = HatFps;
            public float IdleFps = HatFps;   // own idle clock (Weeping Angel: 16 GPT frames tell a little story, 10 fps was too hectic)
            // Take-off (Weeping Angel flies, User 2026-10-26): the first WalkIntro walk frames rise from the ground and play once
            // when the wearer starts moving, then the rest loops; on stopping they play backwards (landing) before the idle frames.
            public int WalkIntro;
            // Live legs (spider, 2026-10-17): on a real player the hat shows hw_<Key>_body_N (no legs) and
            // SpiderLegs works out and draws the eight legs every frame. Shop, previews and anything without a
            // live player keep the classic frames with painted legs.
            public bool LiveLegs;
            public Sprite[] Body, BodyAcc;
        }

        private sealed class KillScene {
            public string Key;          // file key (hk_<Key>_...)
            public int Frames;
            public int[] Flashes;
            public float Hold;          // seconds the last frame stays up (Costume.KillHold)
            public bool Killer;         // has the u*/o* layers (crewmate under / parts over the costume, killer's colour)
        }

        private static readonly Dictionary<Costume, KillScene> mainScene = new();

        /// <summary>The costume's own cutscene or one of its alternatives. <paramref name="key"/> names
        /// one exactly (preview); otherwise every kill draws afresh. The cutscene only ever plays on
        /// the victim's client, so the draw needs no syncing.</summary>
        private static KillScene PickScene(Costume c, string key = null) {
            if (!mainScene.TryGetValue(c, out var main))
                mainScene[c] = main = new KillScene { Key = c.KillKey, Frames = c.KillFrames, Flashes = c.Flashes, Hold = c.KillHold, Killer = c.KillerLayers };
            if (c.Alt == null || c.Alt.Length == 0) return main;
            if (key != null) return c.Alt.FirstOrDefault(x => x.Key == key) ?? main;
            int i = UnityEngine.Random.Range(0, c.Alt.Length + 1);
            return i == 0 ? main : c.Alt[i - 1];
        }

        private static readonly Costume[] Costumes = {
            // 2026-10-26 (User: legs barely moved, "nicht immer das gleiche Bein nach vorne"): the walk loops of Freddy, Jason,
            // Xenomorph, Ghostface, Predator, Sadako, Pumpkin Head, Vampire and Medusa were redrawn by GPT as a real walk cycle with
            // alternating steps (villa_qwen/walk2.py) and run at 12 fps (one stride pair per second).
            // 2026-10-26 (user: kill scenes "very laggy" with 9 drawings): every GPT scene is a 4x4 sheet now (16 drawings,
            // 3 game frames each = 48 frames) with a soft cross-fade where a drawing barely moves; flashes = drawing index * 3.
            // 2026-10-25: costume frames redrawn by GPT (gpt_costume.py freddy): whole figure, cyan sweater stripes = wearer's colour.
            new Costume { Key = "freddy", KillKey = "freddy", Name = "Halloween Freddy", KillFrames = 48, Flashes = new[] { 27, 30 }, HasLegs = false,
                HasAccent = true, HidesBody = true, StillWalk = true, WalkFps = 12f, IdleFps = 8f },
            // 2026-10-25: costume frames redrawn by GPT (gpt_costume.py), cyan parts = wearer's colour.
            new Costume { Key = "jason", KillKey = "jason", Name = "Halloween Jason", KillFrames = 48, Flashes = new[] { 24, 30 }, HasLegs = false, HasAccent = true, HidesBody = true, StillWalk = true, WalkFps = 12f, IdleFps = 8f,
                // diagonal slash (main) or the lift (2026-10-26: redrawn by GPT: grabbed by the head, lifted, thrown down)
                Alt = new[] { new KillScene { Key = "jasonlift", Frames = 48, Flashes = new[] { 36 } } } },
            // 2026-10-26: costume frames redrawn by GPT (gpt_costume.py xenomorph): whole figure, cyan lattice/ribs/tail = wearer's
            // colour, light blue visor stays; idle shows no inner jaw (user), that belongs to the bite scene only.
            new Costume { Key = "xenomorph", KillKey = "xeno", Name = "Halloween Xenomorph", KillFrames = 48, Flashes = new[] { 30, 33 }, HasLegs = false, HasAccent = true,
                HidesBody = true, StillWalk = true, WalkFps = 12f, IdleFps = 8f,
                // tail stab (main) or the inner-jaw bite (2026-10-26: redrawn by GPT, impact flash at the visor hit)
                Alt = new[] { new KillScene { Key = "xenobite", Frames = 48, Flashes = new[] { 30, 33 } } } },
            // 2026-10-07: rebuilt after the Dead-by-Daylight mori (yank down, three stabs, head hauled up, selfie, rip);
            // 2026-10-25 the same mori redrawn by GPT (kill_frames.py): flashes on the three stabs and the selfie
            // 2026-10-25: costume frames redrawn by GPT (gpt_costume.py), cyan parts = wearer's colour.
            new Costume { Key = "ghostface", KillKey = "ghostface", Name = "Halloween Ghostface", KillFrames = 48, Flashes = new[] { 21, 27, 33, 42 }, HasLegs = false, HasAccent = true, HidesBody = true, StillWalk = true, WalkFps = 12f, IdleFps = 8f },
            // 2026-10-13: three more (kill5_<key>.py): assimilation, wrist blades, out of the vent
            // costume: the first Thing (0.1.0.8, opened head on the real body) again; User 2026-10-26 after the GPT figure was too
            // wide and the cut-out head never sat right. The kill scene stays the GPT one from 0.1.3.17: the head opens,
            // tentacles hug the victim in, gulp (flash), burp
            new Costume { Key = "thing", KillKey = "thing", Name = "Halloween Thing", KillFrames = 48, Flashes = new[] { 39 }, HasLegs = false, HasAccent = true },
            // 2026-10-25: costume frames redrawn by GPT (gpt_costume.py), cyan parts = wearer's colour.
            new Costume { Key = "predator", KillKey = "predator", Name = "Halloween Predator", KillFrames = 48, Flashes = new[] { 36, 39 }, HasLegs = false, HasAccent = true, HidesBody = true, StillWalk = true, WalkFps = 12f, IdleFps = 8f },
            // 2026-10-26: costume frames redrawn by GPT (gpt_costume.py sadako): whole figure, cyan ribbon belt = wearer's colour.
            new Costume { Key = "sadako", KillKey = "sadako", Name = "Halloween Sadako", KillFrames = 48, Flashes = new[] { 36, 42 }, HasLegs = false,
                HasAccent = true, HidesBody = true, StillWalk = true, WalkFps = 12f, IdleFps = 8f },
            // 2026-10-16: knitted spider costume (spider.py), BVB fan (bvb.py) and the angel ghost (angel.py,
            // the real body is hidden). Only costumes with a KillKey get a cutscene and a host option.
            // abseil behind the victim, cocoon from the feet up, bite, the cocoon tips over (kill5_spider.py).
            // 2026-10-17 spider v2: the killer's own crewmate under the costume, in the killer's colour
            new Costume { Key = "spider", KillKey = "spider", Name = "Halloween Spider", KillFrames = 48, Flashes = new[] { 21, 24 }, HasLegs = false, HasAccent = true,
                // Spidertron: the body glides level, every leg steps on its own (SpiderLegs); the walk loop
                // is only the fallback for players the live legs cannot run on. 2026-10-25 (User: new look, keep the
                // per-leg concept): body frames and leg parts redrawn by GPT, cyan face patch = wearer's colour.
                StillWalk = true, WalkFps = 12f, LiveLegs = true, HidesBody = true },
            new Costume { Key = "bvb", KillKey = null, Name = "Halloween BVB Fan", HasLegs = false, HasAccent = true },
            new Costume { Key = "angel", KillKey = null, Name = "Halloween Angel Ghost", HasLegs = false, HasAccent = true, HidesBody = true, NoLiveBob = true,
                // 2026-10-24: floats like the reaper - idle pose under it (StillWalk) and its own gentle idle float while
                // walking; the 12 walk frames have a ~40 px bob painted in, so NoLiveBob skips them
                // (2026-10-25: a GPT redraw was compared and the user kept this one)
                StillWalk = true, WalkFps = 12f },
            // 2026-10-20: Pumpkin Head (pumpkin.py; the glow jumps over to the victim and goes out, kill5_pumpkin.py)
            // and Reaper (reaper.py; floats on the idle pose like the spider, one scythe swing and the soul rises,
            // kill5_reaper.py). Appended at the end so their options take 1978 and 1979.
            // 2026-10-25: costume frames redrawn by GPT (gpt_costume.py pumpkin): whole figure, cyan scarf = wearer's colour.
            new Costume { Key = "pumpkin", KillKey = "pumpkin", Name = "Halloween Pumpkin Head", KillFrames = 48, Flashes = new[] { 24, 30 }, HasLegs = false, HasAccent = true,
                HidesBody = true, StillWalk = true, WalkFps = 12f, IdleFps = 8f },
            new Costume { Key = "reaper", KillKey = "reaper", Name = "Halloween Reaper", KillFrames = 48, Flashes = new[] { 24, 27 }, HasLegs = false, HasAccent = true,
                StillWalk = true, WalkFps = 12f, HidesBody = true, IdleFps = 8f },   // 25.10.: GPT frames, cyan rope belt = wearer's colour
            // 2026-10-20 (Grafik-Lieferung, vampire.py / medusa.py, kill5_vampire.py / kill5_medusa.py): Vampire (the cape
            // closes around the victim, bat swarm; player colour in the cape lining, collar and medallion band) and
            // Medusa (the gaze turns the victim to stone; player colour in the sash and the snakes' tongues). Normal
            // 12-frame walk on the run cycle. Their options take 1944 and 1945 (1970-1979 is full).
            new Costume { Key = "vampire", KillKey = "vampire", Name = "Halloween Vampire", KillFrames = 48, Flashes = new[] { 30, 36 }, HasLegs = false, HasAccent = true,
                HidesBody = true, StillWalk = true, WalkFps = 12f, IdleFps = 8f },   // 25.10.: GPT frames, cyan cape lining = wearer's colour
            // the scene ends on the grey statue; without a hold it would only stand for one frame (1/15 s)
            // 2026-10-25: costume frames redrawn by GPT (villa_qwen/gpt_costume.py medusa): the image IS the figure now
            // (HidesBody), the sash is the accent in the wearer's colour; snakes sway, curl, strike and hiss (IdleFps 8),
            // the walk loop lets them trail like ribbons on its own clock (StillWalk). The kill scene stays.
            // 2026-10-25: kill scene redrawn from GPT frames (villa_qwen/kill_frames.py, hybrid: 18 GPT frames, then her gaze frames with
            // the victim petrifying step by step in the stone GPT painted, then she sways beside the statue): 45 frames,
            // flashes when the gaze hits and when the statue is complete.
            new Costume { Key = "medusa", KillKey = "medusa", Name = "Halloween Medusa", KillFrames = 45, Flashes = new[] { 14, 33 }, HasLegs = false, HasAccent = true,
                KillHold = 1.2f, HidesBody = true, StillWalk = true, WalkFps = 12f, IdleFps = 8f },
            // 2026-10-25 (User: Engelskin nach Vorbild der Karten-Engel, jedes Bild von GPT; villa_qwen/angel_costume.py): Weeping
            // Angel. The image IS the figure (stone crewmate with wings), the visor glows in the wearer's colour (accent). Idle:
            // weeps, peeks with a cracked visor, hides again (IdleFps 6). Walk: stalks with claws on its own clock (StillWalk).
            // Kill: the four Weeping Angel scenes of Hollowmere Manor (hk_angel_a1..a4, "Blink" with three flashes). Option 1946.
            new Costume { Key = "weepingangel", KillKey = "angel_a1", Name = "Halloween Weeping Angel", KillFrames = 45, Flashes = new[] { 8, 17, 24 }, KillHold = 0.4f,
                // 2026-10-26 (User: "er fliegt wirklich, die Fluegel flattern"): walking is a GPT flight cycle (villa_qwen/walk2.py), the
                // figure hovers over its own shadow; the first 4 walk frames take off (and play backwards when it lands).
                HasLegs = false, HasAccent = true, HidesBody = true, StillWalk = true, WalkFps = 12f, IdleFps = 6f, WalkIntro = 4,
                Alt = new[] {
                    new KillScene { Key = "angel_a2", Frames = 45, Flashes = new[] { 8, 17, 24 }, Hold = 0.4f },
                    new KillScene { Key = "angel_a3", Frames = 45, Flashes = new[] { 8, 17, 24 }, Hold = 0.4f },
                    new KillScene { Key = "angel_a4", Frames = 45, Flashes = new[] { 8, 17, 24 }, Hold = 0.4f } } },
        };

        // ==================== host options (2026-10-07) ====================
        //
        // The host decides for the whole lobby whether the costume cutscenes play at all and which
        // of them (TOR settings, General tab, block "Unknown's Halloween"). Until now this followed
        // UC's local "UC Kill Animations" toggle, which is gone. ID 1793 is the header (the Xenomorph
        // role holds 1785-1792); one toggle per costume from 1970 on. Until 2026-10-13 those sat on
        // 1794-1797, which UC's Faker took on 2026-10-08 (two options per ID in TOR's sync).
        public static CustomOption Anims;
        private static readonly Dictionary<string, CustomOption> perCostume = new();

        private static void CreateOptions() {
            try {
                var g = CustomOption.CustomOptionType.General;
                Anims = CustomOption.Create(1793, g, "Halloween Costume Kill Animations", true, null, true, null, "Unknown's Halloween");
                // 1970-1979 for the first ten costumes with a cutscene, then 1944-1949 (ID-Registry.md; 1980 is the
                // Masquerade). The order of the table decides, so new costumes always go to the end.
                int id = 1970;
                foreach (var c in Costumes) {
                    if (c.KillKey == null) continue;
                    if (id == 1980) id = 1944;
                    if (id == 1950) { HalloweenPlugin.Logger?.LogWarning($"[Halloween] no free option id for {c.Name}"); continue; }
                    perCostume[c.Key] = CustomOption.Create(id++, g, "Kill Animation: " + c.Name.Replace("Halloween ", ""), true, Anims);
                }
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"[Halloween] CreateOptions failed: {e}");
            }
            Masquerade.CreateOptions();                          // 1980-1981, right below the costume block
        }

        private static bool On(CustomOption o, bool fallback) {
            try { return o == null ? fallback : o.getBool(); } catch { return fallback; }
        }

        private static bool Enabled => On(Anims, true);
        private static bool CostumeEnabled(Costume c) => Enabled && (!perCostume.TryGetValue(c.Key, out var o) || On(o, true));

        private static readonly Dictionary<string, Costume> ByHatName = new();
        private static readonly Dictionary<string, Costume> ByHatId = new();

        /// <summary>Kostuem-Schluessel ("sadako", "xeno" ...) zu einer Hut-Id, sonst null (Rauswurf-Sonderszenen).</summary>
        internal static string CostumeKeyOfHat(string hatId) =>
            hatId != null && ByHatId.TryGetValue(hatId, out var c) ? c.Key : null;
        private static readonly HashSet<string> OwnFiles = new();

        private static bool setupDone;
        private static bool loggedAnimError, loggedKillError;
        private static Action<HatParent> setBounceNode;
        private static Func<string, Sprite> loadHatSprite;

        // ==================== setup ====================

        private static void Setup() {
            if (setupDone) return;
            setupDone = true;
            CreateOptions();
            try {
                const BindingFlags priv = BindingFlags.NonPublic | BindingFlags.Static;
                var hats = typeof(UCHats);
                var mDir = hats.GetMethod("ResolveHatsDirectory", priv);
                var mRegister = hats.GetMethod("Register", priv);
                var mBounce = hats.GetMethod("SetBounceNode", priv);
                if (mDir == null || mRegister == null) {
                    HalloweenPlugin.Logger?.LogWarning("[Halloween] UCHats helpers not found - costumes skipped.");
                    return;
                }
                if (mBounce != null) setBounceNode = (Action<HatParent>)Delegate.CreateDelegate(typeof(Action<HatParent>), mBounce);
                loadHatSprite = LoadHatSprite;
                registerHats = () => RegisterHats(mDir, mRegister);

                var harmony = new Harmony("daunknown.unknownshalloween.costumes");
                var dl = AccessTools.Method(typeof(CustomHatManager), "GenerateDownloadList");
                if (dl != null)
                    harmony.Patch(dl, postfix: new HarmonyMethod(AccessTools.Method(typeof(HalloweenCostumes), nameof(StripOwnFiles))));
                var late = AccessTools.Method(typeof(HatParent), nameof(HatParent.LateUpdate));
                if (late != null)
                    harmony.Patch(late, postfix: new HarmonyMethod(AccessTools.Method(typeof(HalloweenCostumes), nameof(HatLateUpdate))));

                UCFx.RegisterTick(Tick);
                UCFx.RegisterTick(TickLock);
                UCFx.RegisterTick(Masquerade.Tick);
                UCFx.RegisterReset(ResetAll);
            } catch (Exception ex) {
                HalloweenPlugin.Logger?.LogError($"[Halloween] setup failed: {ex}");
                return;
            }
            // The frames live in the asset packages (HalloweenAssets): the hats join the shop right away on a normal
            // start, otherwise once the download is done. Without the packages there are no costumes at all.
            if (!HalloweenAssets.Ready("hats_"))
                HalloweenPlugin.Logger?.LogInfo("[Halloween] costume hats wait for their asset packages.");
            HalloweenAssets.WhenReady("hats_", () => registerHats());
        }

        private static Action registerHats;

        /// <summary>Costume hats are in the shop (their asset packages are there and the registration went through).</summary>
        internal static bool HatsRegistered { get; private set; }

        private static void RegisterHats(MethodInfo mDir, MethodInfo mRegister) {
            try {
                string dir = mDir.Invoke(null, null) as string;
                if (dir == null) {
                    HalloweenPlugin.Logger?.LogWarning("[Halloween] hats directory not resolved - costumes skipped.");
                    return;
                }

                bool Extract(string res, string file) => ExtractIfNeeded(dir, Res + res, file);

                var pending = new List<CustomHat>();
                var byName = new Dictionary<string, Costume>();
                foreach (var c in Costumes) {
                    string main = $"UC_HW_{c.Key}.png", back = $"UC_HW_{c.Key}_back.png", climb = $"UC_HW_{c.Key}_climb.png";
                    // TOR draws the registered hat itself (cosmetics menu, meeting icons) with the 450-wide calibration:
                    // costumes on a wider canvas ship a 450 cut-out as hw_<key>_main.png (2026-10-26)
                    string mainRes = HalloweenAssets.Exists(Res + $"hw_{c.Key}_main.png") ? $"hw_{c.Key}_main.png" : $"hw_{c.Key}_1.png";
                    if (!Extract(mainRes, main)) continue;
                    bool backOk = Extract($"hw_{c.Key}_back.png", back);
                    bool climbOk = Extract($"hw_{c.Key}_climb.png", climb);
                    OwnFiles.Add(main); OwnFiles.Add(back); OwnFiles.Add(climb);
                    var hat = new CustomHat {
                        Name = c.Name, Author = "DaUnknown-0", Package = "Unknown's Halloween",
                        Resource = main, Adaptive = false, Bounce = true, Behind = backOk,
                    };
                    if (backOk) hat.BackResource = back;
                    if (climbOk) hat.ClimbResource = climb;
                    pending.Add(hat);
                    byName[c.Name] = c;
                }
                // the corpse costume (HalloweenCorpse): same registration, own drawing
                var corpseHat = HalloweenCorpse.MakeHat(Extract);
                if (corpseHat != null) { pending.Add(corpseHat); OwnFiles.Add(HalloweenCorpse.FileName); }
                if (pending.Count == 0) return;
                if (!(bool)mRegister.Invoke(null, new object[] { pending })) return;
                // Register removes hats that lost a name collision from the list it was handed.
                foreach (var hat in pending) {
                    if (!byName.TryGetValue(hat.Name, out var c)) continue;
                    c.HatId = UCHats.HatIdOf(c.Name);
                    ByHatName[c.Name] = c;
                    if (c.HidesBody) HalloweenCorpse.BodylessHats.Add(c.Name);
                    ByHatId[c.HatId] = c;
                }
                HatsRegistered = true;
                KickTorHatLoader();
                HalloweenPlugin.Logger?.LogInfo($"[Halloween] registered {ByHatName.Count} costume hat(s).");
            } catch (Exception ex) {
                HalloweenPlugin.Logger?.LogError($"[Halloween] costume registration failed: {ex}");
            }
        }

        // TOR moves UnregisteredHats into the HatManager on GetHatById until the list is empty once, then never again
        // (HatManagerPatches.isLoaded). Hats that arrive later (download finished mid-session) need that pass once more.
        private static void KickTorHatLoader() {
            try {
                var t = typeof(CustomHatManager).Assembly.GetType("TheOtherRoles.Modules.CustomHats.Patches.HatManagerPatches");
                var f = t?.GetField("isLoaded", BindingFlags.NonPublic | BindingFlags.Static);
                if (f != null && f.GetValue(null) is bool loaded && loaded) {
                    f.SetValue(null, false);
                    HalloweenPlugin.Logger?.LogInfo("[Halloween] costume hats arrived after TOR's hat loading, adding them now.");
                }
            } catch (Exception ex) {
                HalloweenPlugin.Logger?.LogWarning($"[Halloween] late hat registration: {ex.Message}");
            }
        }

        private static void StripOwnFiles(List<string> __result) {
            try { __result?.RemoveAll(f => OwnFiles.Contains(f)); } catch { }
        }

        // Embedded (icons) or from the asset packages (all costume and kill frames, HalloweenAssets).
        private static byte[] ReadResource(string logicalName) => HalloweenAssets.Read(logicalName);

        // Writes the embedded PNG into TheOtherHats when it is missing or differs (UCHats' rule:
        // a normal start does no I/O beyond one read, new artwork still refreshes the file).
        private static bool ExtractIfNeeded(string dir, string resourceName, string fileName) {
            try {
                byte[] data = ReadResource(resourceName);
                if (data == null) {
                    HalloweenPlugin.Logger?.LogWarning($"[Halloween] embedded resource missing: {resourceName}");
                    return false;
                }
                if (!Directory.Exists(dir)) Directory.CreateDirectory(dir);
                string path = Path.Combine(dir, fileName);
                if (File.Exists(path)) {
                    var existing = File.ReadAllBytes(path);
                    if (existing.Length == data.Length && existing.SequenceEqual(data)) return true;
                }
                File.WriteAllBytes(path, data);
                HalloweenPlugin.Logger?.LogInfo($"[Halloween] wrote {fileName}.");
                return true;
            } catch (Exception ex) {
                HalloweenPlugin.Logger?.LogError($"[Halloween] could not extract {fileName}: {ex.Message}");
                return false;
            }
        }

        // Same calibration as UCHats.LoadHatSprite / TOR's CreateHatSprite: pivot (0.53, 0.575) and
        // pixelsPerUnit = texture.width * 0.375, DXT5 without a CPU copy (the hat-memory diet).
        // 2026-10-26: frames may be WIDER than the 450x562 hat canvas (Xenomorph tail, Thing tentacles at real crewmate
        // size): the scale then comes from the height (base width = height * 450/562) and the extra width is padding
        // on both sides, so a 450x562 frame behaves exactly as before.
        private static Sprite LoadHatSprite(string logicalName) {
            try {
                byte[] data = ReadResource(logicalName);
                if (data == null) return null;
                var texture = new Texture2D(2, 2, TextureFormat.ARGB32, true);
                if (!ImageConversion.LoadImage(texture, data, false)) return null;
                try { texture.Compress(true); } catch { }
                texture.Apply(false, true);
                float baseW = Mathf.Min(texture.width, texture.height * (450f / 562f));
                float pivotX = ((texture.width - baseW) * 0.5f + 0.53f * baseW) / texture.width;
                var sprite = Sprite.Create(texture, new Rect(0, 0, texture.width, texture.height),
                    new Vector2(pivotX, 0.575f), baseW * 0.375f);
                if (sprite == null) return null;
                texture.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                sprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                return sprite;
            } catch (Exception ex) {
                HalloweenPlugin.Logger?.LogWarning($"[Halloween] sprite load failed ({logicalName}): {ex.Message}");
                return null;
            }
        }

        // Plain sprite from this assembly (the role's button icon), cached per file.
        private static readonly Dictionary<string, Sprite> iconCache = new();
        internal static Sprite LoadIcon(string file, float pixelsPerUnit) {
            if (iconCache.TryGetValue(file, out var cached) && cached != null) return cached;
            try {
                byte[] data = ReadResource(Res + file);
                if (data == null) return null;
                var tex = new Texture2D(2, 2, TextureFormat.ARGB32, false);
                if (!ImageConversion.LoadImage(tex, data, false)) return null;
                tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                var sprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), pixelsPerUnit);
                sprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                iconCache[file] = sprite;
                return sprite;
            } catch { return null; }
        }

        // ==================== hat animation (idle / walk) ====================

        private static void EnsureFrames(Costume c) {
            if (c.FramesTried) return;
            c.FramesTried = true;
            var idle = new Sprite[IdleFrames];
            for (int i = 0; i < idle.Length; i++) {
                idle[i] = loadHatSprite(Res + $"hw_{c.Key}_{i + 1}.png");
                if (idle[i] == null) {
                    HalloweenPlugin.Logger?.LogWarning($"[Halloween] {c.Name}: idle frame {i + 1} missing - hat stays static.");
                    return;
                }
            }
            c.Idle = idle;
            if (c.LiveLegs) {
                // body frames without legs (+ accent masks); missing ones simply switch the live legs off
                var body = new Sprite[IdleFrames];
                var bodyAcc = new Sprite[IdleFrames];
                bool ok = true;
                for (int i = 0; i < IdleFrames && ok; i++) {
                    body[i] = loadHatSprite(Res + $"hw_{c.Key}_body_{i + 1}.png");
                    bodyAcc[i] = loadHatSprite(Res + $"hw_{c.Key}_body_acc_{i + 1}.png");
                    ok = body[i] != null;
                }
                if (ok) { c.Body = body; c.BodyAcc = bodyAcc.All(s => s != null) ? bodyAcc : null; }
                else HalloweenPlugin.Logger?.LogWarning($"[Halloween] {c.Name}: body frames missing - live legs off.");
            }
            int walkCount = WalkFrames;
            if (c.StillWalk) {
                // own loop: as many frames as the resources hold (up to 96)
                walkCount = 0;
                while (walkCount < 96 && HalloweenAssets.Exists(Res + $"hw_{c.Key}_walk_{walkCount + 1}.png")) walkCount++;
                if (walkCount == 0) return;
            }
            var walk = new Sprite[walkCount];
            for (int i = 0; i < walk.Length; i++) {
                walk[i] = loadHatSprite(Res + $"hw_{c.Key}_walk_{i + 1}.png");
                if (walk[i] == null) {
                    HalloweenPlugin.Logger?.LogWarning($"[Halloween] {c.Name}: walk frame {i + 1} missing - walk loop off.");
                    return;
                }
            }
            c.Walk = walk;
            if (!c.HasAccent) return;
            // Optional: without the masks the costume simply shows no player colour.
            var idleAcc = new Sprite[IdleFrames];
            for (int i = 0; i < idleAcc.Length; i++)
                if ((idleAcc[i] = loadHatSprite(Res + $"hw_{c.Key}_acc_{i + 1}.png")) == null) return;
            var walkAcc = new Sprite[walkCount];
            for (int i = 0; i < walkAcc.Length; i++)
                if ((walkAcc[i] = loadHatSprite(Res + $"hw_{c.Key}_walk_acc_{i + 1}.png")) == null) return;
            c.IdleAcc = idleAcc;
            c.WalkAcc = walkAcc;
        }

        // ---- accent layer: the costume's highlights in the wearer's colour ----
        //
        // Xenomorph and Ghostface are black all over, so the player colour cannot show through
        // anywhere. Their highlights (tail spikes, ribs, dome reflex, hood rim, cloth folds) are
        // therefore a second sprite per frame: a white mask whose alpha is the highlight strength.
        // It sits as a child renderer right in front of the hat's front layer, with the same
        // material, flip and mask settings, tinted in the body colour of whoever wears the hat.
        private static readonly Dictionary<int, SpriteRenderer> accents = new();

        private static void HideAccent(HatParent hat) {
            if (accents.Count == 0 || hat == null) return;
            if (accents.TryGetValue(hat.GetInstanceID(), out var sr) && sr != null && sr.enabled) sr.enabled = false;
        }

        private static void ShowAccent(HatParent hat, SpriteRenderer front, Sprite sprite) {
            int id = hat.GetInstanceID();
            if (!accents.TryGetValue(id, out var sr) || sr == null) {
                if (accents.Count > 256) accents.Clear();
                var go = new GameObject("HalloweenAccent") { layer = front.gameObject.layer };
                go.transform.SetParent(front.transform, false);
                go.transform.localPosition = new Vector3(0f, 0f, -0.0002f);
                sr = go.AddComponent<SpriteRenderer>();
                accents[id] = sr;
            }
            if (sr.sprite != sprite) sr.sprite = sprite;
            if (sr.sharedMaterial != front.sharedMaterial) sr.sharedMaterial = front.sharedMaterial;
            sr.flipX = front.flipX;
            sr.maskInteraction = front.maskInteraction;
            sr.sortingLayerID = front.sortingLayerID;
            sr.sortingOrder = front.sortingOrder;
            if (sr.gameObject.layer != front.gameObject.layer) sr.gameObject.layer = front.gameObject.layer;
            Color body = Color.white;
            try {
                int colorId = hat.matProperties.ColorId;
                var bodies = Palette.PlayerColors;
                if (bodies != null && colorId >= 0 && colorId < bodies.Length) body = bodies[colorId];
            } catch { }
            // The game drives the front layer's alpha for ghosts and invisibility - follow it.
            sr.color = new Color(body.r, body.g, body.b, front.color.a);
            if (!sr.enabled) sr.enabled = true;
        }

        // HatParent -> wearing player. Shop previews and the lobby dummy have none (always idle).
        private static readonly Dictionary<int, (PlayerControl pc, float recheck)> owners = new();

        // ---- no walk bob for a living wearer (Angel Ghost) ----
        // The bob is SpriteAnimNodeSync snapping the front layer to the head node of the run cycle. While the wearer
        // is alive and off the ladder the sync is switched off, but only while he stands still, so the picture stays
        // at its idle height. As a ghost (own float animation) or on a ladder it runs as usual.
        private static readonly HashSet<int> heldBob = new();

        private static PowerTools.SpriteAnimNodeSync SyncOf(HatParent hat) {
            try { return hat.SpriteSyncNode != null ? hat.SpriteSyncNode : hat.GetComponent<PowerTools.SpriteAnimNodeSync>(); } catch { return null; }
        }

        private static void HoldBob(HatParent hat) {
            try {
                var sync = SyncOf(hat);
                if (sync == null) return;
                var pc = OwnerOf(hat);
                bool alive = pc != null && pc.Data != null && !pc.Data.IsDead && !pc.onLadder;
                if (alive) {
                    if (sync.enabled && !StillWalkMoving(pc)) { sync.enabled = false; heldBob.Add(hat.GetInstanceID()); }
                } else if (!sync.enabled) {
                    sync.enabled = true;
                    heldBob.Remove(hat.GetInstanceID());
                }
            } catch { }
        }

        private static void ReleaseBob(HatParent hat) {
            if (heldBob.Count == 0 || !heldBob.Remove(hat.GetInstanceID())) return;
            try { var sync = SyncOf(hat); if (sync != null) sync.enabled = true; } catch { }
        }

        private static PlayerControl OwnerOf(HatParent hat) {
            int id = hat.GetInstanceID();
            if (owners.TryGetValue(id, out var e) && (e.pc != null || Time.time < e.recheck)) return e.pc;
            PlayerControl pc = null;
            try { pc = hat.GetComponentInParent<PlayerControl>(); } catch { }
            if (owners.Count > 256) owners.Clear();
            owners[id] = (pc, Time.time + 2f);
            return pc;
        }

        // Runs after TOR's LateUpdatePrefix (which skips the original for cached custom hats), so
        // this is the last writer of the sprite in the frame - same slot UCHats uses for its hats.
        private static bool legsShown;

        // Live legs need a living, walking player on the map (no vent, ladder or moving platform).
        private static bool LiveLegsAllowed(PlayerControl pc) {
            try {
                return pc.Data != null && !pc.Data.IsDead && !pc.inVent && !pc.onLadder && !pc.inMovingPlat;
            } catch { return false; }
        }

        private static void HatLateUpdate(HatParent __instance) {
            bool accentShown = false;
            legsShown = false;
            try {
                if (HalloweenCorpse.Handle(__instance)) { HideAccent(__instance); SpiderLegs.Hide(__instance); return; }
                accentShown = HatLateUpdateCore(__instance);
                if (!legsShown) SpiderLegs.Hide(__instance);
            } catch (Exception ex) {
                if (!loggedAnimError) {
                    loggedAnimError = true;
                    HalloweenPlugin.Logger?.LogError($"[Halloween] hat animation failed (logged once): {ex}");
                }
            }
            // Any other hat, the ladder and corpse poses, a hidden front layer: no highlights.
            if (!accentShown) {
                try { HideAccent(__instance); } catch { }
            }
        }

        // Returns whether the accent layer is showing for this hat in this frame.
        private static bool HatLateUpdateCore(HatParent __instance) {
            if (__instance == null) return false;
            var hat = __instance.Hat;
            Costume c = null;
            bool ours = hat != null && ByHatName.TryGetValue(hat.name, out c);
            if (!ours || !c.NoLiveBob) ReleaseBob(__instance);      // hat changed: the next hat bobs normally again
            if (!ours) return false;

            setBounceNode?.Invoke(__instance);
            if (c.NoLiveBob) HoldBob(__instance);

            var front = __instance.FrontLayer;
            var back = __instance.BackLayer;
            if (DiagOn && DiagTick(__instance, front, back)) return false;
            if (front == null || !front.enabled || front.sprite == null) return false;
            // Ladder / corpse pose: SetClimbAnim and SetFloorAnim switch the back layer off and put
            // their own image on the front layer. Never write over that.
            if (back == null || !back.enabled) return false;

            EnsureFrames(c);
            if (c.Idle == null) return false;

            if (c.LiveLegs && c.Body != null) {
                var owner = OwnerOf(__instance);
                if (owner != null && LiveLegsAllowed(owner)) {
                    int bi = Mathf.FloorToInt(Time.time * HatFps) % IdleFrames;
                    var bf = c.Body[bi];
                    if (bf != null && front.sprite != bf) front.sprite = bf;
                    if (SpiderLegs.Drive(__instance, owner, front, back)) {
                        legsShown = true;
                        if (c.BodyAcc == null) return false;
                        ShowAccent(__instance, front, c.BodyAcc[bi]);
                        return true;
                    }
                }
            }

            bool running = false;
            float cycle = -1f;
            int introFrame = -1;
            if (c.Walk != null && !c.NoLiveBob && c.StillWalk) {
                // No run animation to read (StillWalkPatch keeps the idle pose): moving = real velocity.
                var pc = OwnerOf(__instance);
                if (pc != null && StillWalkMoving(pc)) {
                    running = true;
                    if (!walkStart.TryGetValue(pc.PlayerId, out float t0)) {
                        t0 = Time.time;
                        // moving again while landing: take off from the height reached so far
                        if (landStart.TryGetValue(pc.PlayerId, out float l1)) {
                            int left = c.WalkIntro - 1 - Mathf.FloorToInt((Time.time - l1) * c.WalkFps);
                            if (left > 0) t0 -= left / c.WalkFps;
                        }
                        walkStart[pc.PlayerId] = t0;
                    }
                    landStart.Remove(pc.PlayerId);
                    int intro = Mathf.Clamp(c.WalkIntro, 0, c.Walk.Length - 1);
                    if (intro > 0) {
                        int k = Mathf.FloorToInt((Time.time - t0) * c.WalkFps);
                        introFrame = k < intro ? k : intro + (k - intro) % (c.Walk.Length - intro);
                    } else cycle = ((Time.time - t0) * c.WalkFps / c.Walk.Length) % 1f;
                } else if (pc != null) {
                    if (walkStart.Remove(pc.PlayerId) && c.WalkIntro > 0) landStart[pc.PlayerId] = Time.time;
                    if (c.WalkIntro > 0 && landStart.TryGetValue(pc.PlayerId, out float l0)) {
                        int k = Mathf.FloorToInt((Time.time - l0) * c.WalkFps);
                        int intro = Mathf.Clamp(c.WalkIntro, 0, c.Walk.Length - 1);
                        if (k < intro) { running = true; introFrame = intro - 1 - k; }
                        else landStart.Remove(pc.PlayerId);
                    }
                }
            } else if (c.Walk != null && !c.NoLiveBob) {
                var pc = OwnerOf(__instance);
                if (pc != null) {
                    try {
                        var anims = pc.MyPhysics != null ? pc.MyPhysics.Animations : null;
                        if (anims != null && anims.IsPlayingRunAnimation()) {
                            running = true;
                            var animator = anims.Animator != null ? anims.Animator.m_animator : null;
                            if (animator != null) {
                                float t = animator.GetCurrentAnimatorStateInfo(0).normalizedTime;
                                cycle = t - Mathf.Floor(t);
                            }
                        }
                    } catch { }
                }
            }

            Sprite frame;
            if (running) {
                int n = c.Walk.Length;
                int i = introFrame >= 0 ? introFrame : cycle >= 0f ? Mathf.FloorToInt(cycle * n) : Mathf.FloorToInt(Time.time * HatFps);
                if (!c.StillWalk) i += WalkPhaseOffset;
                frame = c.Walk[(i % n + n) % n];
            } else {
                frame = c.Idle[Mathf.FloorToInt(Time.time * c.IdleFps) % IdleFrames];
            }
            if (frame != null && front.sprite != frame) front.sprite = frame;

            // The back layer holds the dark trouser openings of the standing pose. While the
            // painted legs walk, they would stay behind as fixed blobs on the floor.
            // (Renderer.forceRenderingOff is stripped from this game build, hence the scale.)
            SetHidden(back, running && c.HasLegs);

            Sprite[] accStrip = running ? c.WalkAcc : c.IdleAcc;
            if (accStrip == null || frame == null) return false;
            ShowAccent(__instance, front, accStrip[Array.IndexOf(running ? c.Walk : c.Idle, frame)]);
            return true;
        }

        // Hides a layer without touching `enabled` (the pose guards read that) or its colour (the
        // game drives alpha for ghosts and invisibility).
        private static void SetHidden(SpriteRenderer sr, bool hide) {
            if (sr == null) return;
            var t = sr.transform;
            bool hidden = t.localScale.x == 0f;
            if (hidden != hide) t.localScale = hide ? Vector3.zero : Vector3.one;
        }

        // ---- still walk (spider): idle pose while moving, the costume's own walk loop ----

        // When each player started moving; the loop starts at frame 0 (the planted idle stance) every time.
        private static readonly Dictionary<byte, float> walkStart = new();
        // When a flying costume (WalkIntro) stopped: the take-off frames run backwards from there (landing).
        private static readonly Dictionary<byte, float> landStart = new();

        private static bool WearsStillWalk(PlayerControl pc) {
            try {
                var hatId = pc.CurrentOutfit != null ? pc.CurrentOutfit.HatId : null;
                return hatId != null && ByHatId.TryGetValue(hatId, out var c) && c.StillWalk;
            } catch { return false; }
        }

        private static bool StillWalkMoving(PlayerControl pc) {
            try {
                if (pc.onLadder || pc.inVent || pc.inMovingPlat) return false;
                var body = pc.MyPhysics != null ? pc.MyPhysics.body : null;
                return body != null && body.velocity.sqrMagnitude > 0.01f;
            } catch { return false; }
        }

        // HandleAnimation picks run or idle from body.velocity. For a still-walk costume the velocity is
        // zero for the duration of this one call, so the game itself settles on the idle animation
        // (no run cycle, no bob, no switching back and forth); the physics step runs elsewhere and is
        // untouched. The facing direction is then set from the real velocity. Ghosts, ladders, vents
        // and moving platforms keep the vanilla handling.
        [HarmonyPatch(typeof(PlayerPhysics), nameof(PlayerPhysics.HandleAnimation))]
        static class StillWalkPatch {
            static void Prefix(PlayerPhysics __instance, [HarmonyArgument(0)] bool amDead, out Vector2? __state) {
                __state = null;
                try {
                    if (amDead || __instance == null || __instance.body == null || ByHatId.Count == 0) return;
                    var pc = __instance.myPlayer;
                    if (pc == null || pc.onLadder || pc.inVent || pc.inMovingPlat || !WearsStillWalk(pc)) return;
                    __state = __instance.body.velocity;
                    __instance.body.velocity = Vector2.zero;
                } catch { __state = null; }
            }

            static void Postfix(PlayerPhysics __instance, Vector2? __state) {
                if (__state == null) return;
                try {
                    var v = __state.Value;
                    __instance.body.velocity = v;
                    // Through the cosmetics layer: it turns body, hat, visor and skin together.
                    // (PlayerPhysics.FlipX alone turned only the body - playtest 2026-10-17: crewmate
                    // looking left inside a costume looking right.)
                    var cos = __instance.myPlayer != null ? __instance.myPlayer.cosmetics : null;
                    if (cos == null || Mathf.Abs(v.x) <= 0.01f) return;
                    bool left = v.x < 0f;
                    if (cos.FlipX != left) cos.SetFlipX(left);
                } catch { }
            }
        }

        // ==================== costume lock ====================
        //
        // While a Xenomorph can turn up in the round, nobody may WEAR the Xenomorph costume as an
        // ordinary hat - otherwise a harmless player looks exactly like the creature. "Can turn up"
        // means: the Xenomorph role is enabled here, or another mod says so through the AppDomain key
        // "Unknowns.XenoActive" (Unknown's Hunt sets it for Hunt Mode and for the NPC creature).
        // Same three layers as the role costumes in UCHats: grey chip, blocked equip, and a tick that
        // swaps an already saved costume for no hat.

        private const string XenoKey = "xenomorph";
        private const string NoHatId = "hat_NoHat";
        private static float lastLockFix;

        private static bool XenoLocked() {
            try {
                if (Xenomorph.RoleEnabled()) return true;
                return AppDomain.CurrentDomain.GetData("Unknowns.XenoActive") is bool b && b;
            } catch { return false; }
        }

        private static bool IsLockedHat(string productId) {
            if (string.IsNullOrEmpty(productId)) return false;
            return ByHatId.TryGetValue(productId, out var c) && c.Key == XenoKey && XenoLocked();
        }

        // The hat the player really chose (last saved hat that is not the Xenomorph costume).
        private static string lastOwnHat;
        private static bool roleTouchedHat;

        // Playtest 2026-10-05: leaving a round as the transformed Xenomorph left the costume in the
        // player's SAVED outfit - the next round started with it on, whatever he wore before. The
        // creature look must never reach the save: while the local player is the Xenomorph a saved
        // costume is written back at once, and after the round it is also put back on the player.
        private static void GuardSavedHat(AmongUs.Data.Player.PlayerCustomizationData customization) {
            string xenoId = Costumes.FirstOrDefault(x => x.Key == XenoKey)?.HatId;
            if (xenoId == null) return;
            string hat = customization.Hat;
            bool isRole = Xenomorph.IsLocalXenomorph();
            if (hat != xenoId) { if (!string.IsNullOrEmpty(hat)) lastOwnHat = hat; if (!isRole) roleTouchedHat = false; if (isRole) roleTouchedHat = true; return; }
            if (isRole) {
                roleTouchedHat = true;
                customization.Hat = lastOwnHat ?? NoHatId;
                return;
            }
            if (!roleTouchedHat) return;
            roleTouchedHat = false;
            string back = lastOwnHat ?? NoHatId;
            customization.Hat = back;
            var lp = PlayerControl.LocalPlayer;
            if (lp != null) lp.RpcSetHat(back);
            HalloweenPlugin.Logger?.LogInfo($"[Halloween] the creature look had reached the saved outfit - restored '{back}'.");
        }

        private static void TickLock() {
            try {
                var customization = AmongUs.Data.DataManager.Player?.Customization;
                if (customization == null) return;
                GuardSavedHat(customization);
                if (!IsLockedHat(customization.Hat)) return;
                if (Time.time - lastLockFix < 1f) return;
                lastLockFix = Time.time;
                string back = lastOwnHat ?? NoHatId;
                customization.Hat = back;
                var lp = PlayerControl.LocalPlayer;
                if (lp != null) lp.RpcSetHat(back);
                HalloweenPlugin.Logger?.LogInfo("[Halloween] the Xenomorph costume is locked in this lobby - hat removed.");
                if (lp != null && HudManager.InstanceExists && HudManager.Instance.Chat != null)
                    HudManager.Instance.Chat.AddChat(lp, "The Xenomorph costume cannot be worn while a Xenomorph is enabled.");
            } catch { }
        }

        private static HatData ChipHat(ColorChip chip) {
            if (chip == null) return null;
            try { var tagged = chip.Tag; if (tagged != null) { var hat = tagged.TryCast<HatData>(); if (hat != null) return hat; } } catch { }
            try { return chip.Inner != null ? chip.Inner.Hat : null; } catch { return null; }
        }

        [HarmonyPatch(typeof(HatsTab), nameof(HatsTab.OnEnable))]
        static class LockTabPatch {
            [HarmonyPriority(Priority.Low)]
            static void Postfix(HatsTab __instance) {
                try {
                    if (__instance == null || __instance.ColorChips == null || !XenoLocked()) return;
                    foreach (ColorChip chip in __instance.ColorChips) {
                        var hat = ChipHat(chip);
                        if (hat == null || !IsLockedHat(hat.ProductId)) continue;
                        try { chip.SetUnavailable(); } catch { }
                        try { if (chip.Button != null) chip.Button.enabled = false; } catch { }
                    }
                } catch { }
            }
        }

        [HarmonyPatch(typeof(HatsTab), nameof(HatsTab.ClickEquip))]
        static class LockEquipPatch {
            static bool Prefix(HatsTab __instance) {
                try { var hat = __instance != null ? __instance.currentHat : null; if (hat != null && IsLockedHat(hat.ProductId)) return false; } catch { }
                return true;
            }
        }

        // ==================== kill cutscene: selection ====================

        private static Costume CostumeOfKiller(NetworkedPlayerInfo killer, NetworkedPlayerInfo victim) {
            try {
                // Masked kills arrive as (victim, victim); meeting kills are guesses, not costume kills.
                if (killer == null || victim == null || killer.PlayerId == victim.PlayerId) return null;
                if (MeetingHud.Instance != null) return null;
                // The Xenomorph ROLE in its creature form wears the costume through setLook, which does
                // not show up in CurrentOutfit.
                if (Xenomorph.IsTransformed(killer.PlayerId)) return Costumes.FirstOrDefault(x => x.KillKey == "xeno" && x.HatId != null);
                string hatId = null;
                var pc = killer.Object;
                // What the killer LOOKS like right now - a camouflaged or morphed killer shows no costume.
                if (pc != null && pc.CurrentOutfit != null) hatId = pc.CurrentOutfit.HatId;
                else if (killer.DefaultOutfit != null) hatId = killer.DefaultOutfit.HatId;
                return hatId != null && ByHatId.TryGetValue(hatId, out var c) && c.KillKey != null ? c : null;
            } catch { return null; }
        }

        private static int ColorIdOf(NetworkedPlayerInfo info) {
            try { if (info?.DefaultOutfit != null) return info.DefaultOutfit.ColorId; } catch { }
            return 0;
        }

        // The killer's colour as it looks right now (same outfit CostumeOfKiller read the costume from).
        private static int KillerColorIdOf(NetworkedPlayerInfo info) {
            try { var pc = info?.Object; if (pc != null && pc.CurrentOutfit != null) return pc.CurrentOutfit.ColorId; } catch { }
            return ColorIdOf(info);
        }

        [HarmonyPatch(typeof(KillOverlay), nameof(KillOverlay.ShowKillAnimation),
            typeof(NetworkedPlayerInfo), typeof(NetworkedPlayerInfo))]
        static class KillHook {
            // Called by the plugin-wide PatchAll during Load() - the earliest point this file gets.
            static bool Prepare() {
                Setup();
                return true;
            }

            // Last, and only if nobody before us (UCKillOverlay's role cutscenes) has already
            // replaced the vanilla overlay: HarmonyX runs every prefix even after one returned false.
            [HarmonyPriority(Priority.Last)]
            static bool Prefix([HarmonyArgument(0)] NetworkedPlayerInfo killer,
                               [HarmonyArgument(1)] NetworkedPlayerInfo victim, bool __runOriginal) {
                try {
                    if (!__runOriginal || !Enabled || ByHatId.Count == 0) return true;
                    var c = CostumeOfKiller(killer, victim);
                    if (c == null || !CostumeEnabled(c)) return true;
                    queue.Add((c, PickScene(c), ColorIdOf(victim), KillerColorIdOf(killer), Time.time + 20f));
                    return false;                       // suppress the vanilla overlay
                } catch (Exception e) {
                    HalloweenPlugin.Logger?.LogError($"[Halloween] kill hook: {e}");
                    return true;
                }
            }
        }

        /// <summary>Plays a cutscene without a costume behind it (Ravenhollow's demon, 2026-10-24) for the local
        /// victim: frames hk_&lt;key&gt;_back/vrest/vbody/vshade/front_NN, no killer layers. False when the frames are
        /// not there (the caller then shows nothing).</summary>
        public static bool PlayStandaloneScene(string key, int frames, int[] flashes, float hold, int victimColor) {
            try {
                Setup();
                if (!HalloweenAssets.Exists(Res + $"hk_{key}_back_01.png")) return false;
                var c = new Costume { Key = key, KillKey = key, Name = key };
                var scene = new KillScene { Key = key, Frames = frames, Flashes = flashes, Hold = hold, Killer = false };
                queue.Add((c, scene, victimColor, victimColor, Time.time + 20f));
                return true;
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogWarning($"[Halloween] standalone scene {key}: {e.Message}");
                return false;
            }
        }

        /// <summary>Plays a costume cutscene locally as if the local player had just been killed.
        /// Returns a short status line. Keys: freddy, jason (slash), jasonlift, jasonrandom, xeno (tail stab),
        /// xenobite, xenomorph (random of both), ghost / ghostface. "&lt;costume&gt;random" draws like a real kill.</summary>
        // Scenes without a costume (map deaths): key, file key, frames, flashes, hold. Kept in step with
        // GraveyardWorld.Demon* and HollowmereWorld.AngelScene*.
        private static readonly (string Key, string Label, int Frames, int[] Flashes, float Hold)[] Standalone = {
            ("demon", "Demon (pentagram)", 48, new[] { 22, 36 }, 0.5f),
            ("angel_a1", "Weeping Angel: Mourning", 45, new[] { 8, 17, 24 }, 0.4f),
            ("angel_a2", "Weeping Angel: Hooded", 45, new[] { 8, 17, 24 }, 0.4f),
            ("angel_a3", "Weeping Angel: Cherub", 45, new[] { 8, 17, 24 }, 0.4f),
            ("angel_a4", "Weeping Angel: Ruined", 45, new[] { 8, 17, 24 }, 0.4f),
        };

        /// <summary>Every playable kill scene as "key|Label" (Role Control builds its list from this, by reflection):
        /// each costume's main scene, its alternatives, "random" for costumes with several, then the map scenes.</summary>
        public static string[] SceneList() {
            var list = new List<string>();
            foreach (var c in Costumes) {
                if (c.KillKey == null) continue;
                string name = c.Name.Replace("Halloween ", "");
                bool alts = c.Alt != null && c.Alt.Length > 0;
                list.Add($"{c.KillKey}|{name}{(alts ? ": 1" : "")}");
                if (alts) {
                    for (int i = 0; i < c.Alt.Length; i++) list.Add($"{c.Alt[i].Key}|{name}: {i + 2}");
                    list.Add($"{c.Key}random|{name}: Random");
                }
            }
            foreach (var s in Standalone) list.Add($"{s.Key}|{s.Label}");
            return list.ToArray();
        }

        /// <summary>Plays a scene on another player's screen (host only; Role Control). The target client plays it
        /// locally as if it had been killed; nobody dies. RPC module 236 sub 15.</summary>
        public static string PreviewFor(string key, byte targetId) {
            try {
                var lp = PlayerControl.LocalPlayer;
                if (lp != null && lp.PlayerId == targetId) return Preview(key);
                if (AmongUsClient.Instance == null || !AmongUsClient.Instance.AmHost) return "Only the host can play a scene for someone else.";
                var w = UCRpc.Begin(HollowmereIntro.RpcModule);
                w.Write(HollowmereWorld.SubScenePreview);
                w.Write(targetId);
                w.Write(key ?? "");
                AmongUsClient.Instance.FinishRpcImmediately(w);
                return $"Scene '{key}' sent to player {targetId}.";
            } catch (Exception e) {
                return "Fehler: " + e.Message;
            }
        }

        internal static void HandleScenePreview(Hazel.MessageReader reader) {
            byte target = reader.ReadByte();
            string key = reader.ReadString();
            if (!UCRpc.RequireHost("Halloween.ScenePreview")) return;
            var lp = PlayerControl.LocalPlayer;
            if (lp == null || lp.PlayerId != target) return;
            HalloweenPlugin.Logger?.LogInfo("[Halloween] host played kill scene for you: " + Preview(key));
        }

        public static string Preview(string key) {
            try {
                Setup();
                key = (key ?? string.Empty).Trim().ToLowerInvariant();
                foreach (var s in Standalone) {
                    if (s.Key != key && !(key.Length >= 4 && s.Key.StartsWith(key))) continue;
                    if (HudManager.Instance == null) return "Kein HUD - erst in eine Lobby oder Runde gehen.";
                    int col = 0;
                    try { col = PlayerControl.LocalPlayer.Data.DefaultOutfit.ColorId; } catch { }
                    EndSequence();
                    queue.Clear();
                    return PlayStandaloneScene(s.Key, s.Frames, s.Flashes ?? Array.Empty<int>(), s.Hold, col)
                        ? $"Kill-Szene {s.Label} wird abgespielt." : $"Szene {s.Label}: Bilder noch nicht geladen.";
                }
                bool random = key.EndsWith("random", StringComparison.Ordinal);
                if (random) key = key.Substring(0, key.Length - "random".Length);
                var c = Costumes.Where(x => x.KillKey != null).FirstOrDefault(x => x.Key == key || x.KillKey == key
                                                     || (x.Alt != null && x.Alt.Any(s => s.Key == key))
                                                     || (key.Length >= 3 && x.Key.StartsWith(key)));
                if (c == null) return "Unbekannt. Moeglich: " + string.Join(", ", SceneList().Select(s => s.Split('|')[0]));
                if (HudManager.Instance == null) return "Kein HUD - erst in eine Lobby oder Runde gehen.";
                int color = 0;
                try { color = PlayerControl.LocalPlayer.Data.DefaultOutfit.ColorId; } catch { }
                EndSequence();
                queue.Clear();
                // An alternative's own key plays exactly that scene, the costume's main key the main one.
                var scene = !random && (key == c.KillKey || (c.Alt != null && c.Alt.Any(s => s.Key == key))) ? PickScene(c, key) : PickScene(c);
                // With killer layers the local player is the killer; the victim gets a contrast colour (as in the preview page).
                int victim = color;
                if (scene.Killer) {
                    int n = 18;
                    try { n = Palette.PlayerColors.Length; } catch { }
                    victim = (color + 5) % Mathf.Max(1, n);
                }
                queue.Add((c, scene, victim, color, Time.time + 20f));
                return $"Kill-Szene {c.Name} wird abgespielt.";
            } catch (Exception e) {
                return "Fehler: " + e.Message;
            }
        }

        // ==================== kill cutscene: playback ====================

        private static readonly List<(Costume c, KillScene scene, int victimColor, int killerColor, float expires)> queue = new();
        // Back to front. u* = the killer's crewmate under the costume, o* = its parts in front of the costume,
        // v* = the victim; each split into an untinted rest plus a body and a shade mask (split_victim.py).
        // Scenes without killer layers (KillScene.Killer false) skip the u*/o* files entirely.
        private static readonly string[] Layers = { "urest", "ubody", "ushade", "back", "orest", "obody", "oshade", "vrest", "vbody", "vshade", "front" };
        private static readonly int[] KillerBody = { 1, 5 }, KillerShade = { 2, 6 };
        private const int LayerBody = 8, LayerShade = 9;
        private static bool IsKillerLayer(int i) => Layers[i][0] == 'u' || Layers[i][0] == 'o';
        private const float StageWidth = 9.44f;
        private static readonly Color BandDark = new Color(0.588f, 0.055f, 0.078f, 1f);
        private static readonly Color BandFlash = new Color(0.925f, 0.235f, 0.204f, 1f);

        private static GameObject root;
        private static Costume active;
        private static KillScene activeScene;
        private static float startTime;
        private static int shownFrame;
        private static SpriteRenderer band;
        private static readonly SpriteRenderer[] layerSr = new SpriteRenderer[Layers.Length];

        private static void Tick() {
            try {
                for (int i = queue.Count - 1; i >= 0; i--)
                    if (Time.time > queue[i].expires) queue.RemoveAt(i);

                bool uiBlocked = MeetingHud.Instance != null || ExileController.Instance != null;
                if (root != null) {
                    if (uiBlocked) { EndSequence(); return; }
                    int frame = Mathf.FloorToInt((Time.time - startTime) * KillFps);
                    if (frame >= activeScene.Frames) {
                        // the last frame stays up for the scene's hold (Medusa's statue), then the overlay closes
                        if (Time.time - startTime < activeScene.Frames / KillFps + activeScene.Hold) return;
                        EndSequence();
                        return;
                    }
                    if (frame != shownFrame) {
                        if (frame > shownFrame + 1) statSkipped += frame - shownFrame - 1;
                        float t0 = Time.realtimeSinceStartup;
                        ShowFrame(frame);
                        statSlowest = Mathf.Max(statSlowest, Time.realtimeSinceStartup - t0);
                        statShown++;
                    }
                    return;
                }
                if (queue.Count == 0 || uiBlocked) return;
                var hud = HudManager.Instance;
                if (hud == null) return;
                var next = queue[0];
                queue.RemoveAt(0);
                Build(hud, next.c, next.scene, next.victimColor, next.killerColor);
            } catch (Exception e) {
                if (!loggedKillError) {
                    loggedKillError = true;
                    HalloweenPlugin.Logger?.LogError($"[Halloween] kill cutscene failed (logged once): {e}");
                }
                EndSequence();
            }
        }

        private static AudioClip playingStinger;

        // The stinger the vanilla overlay would have played (we suppress that overlay, so its sound
        // has to be started here). The stab sound itself comes from MurderPlayer and is untouched.
        private static void PlayVanillaStinger(HudManager hud) {
            try {
                if (!Constants.ShouldPlaySfx() || SoundManager.Instance == null) return;
                var overlay = hud != null ? hud.KillOverlay : null;
                var anims = overlay != null ? overlay.KillAnims : null;
                if (anims == null || anims.Length == 0 || anims[0] == null || anims[0].Stinger == null) return;
                var src = SoundManager.Instance.PlaySound(anims[0].Stinger, false, 1f);
                if (src != null) src.volume = anims[0].StingerVolume;
                playingStinger = anims[0].Stinger;
                if (DiagOn) HalloweenPlugin.Logger?.LogInfo($"[Halloween] vanilla stinger '{anims[0].Stinger.name}' volume {anims[0].StingerVolume:F2}");
            } catch (Exception e) {
                if (DiagOn) HalloweenPlugin.Logger?.LogWarning($"[Halloween] stinger failed: {e.Message}");
            }
        }

        private static SpriteRenderer MakeSr(string name, int order, int layer) {
            var go = new GameObject(name) { layer = layer };
            go.transform.SetParent(root.transform, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = order;
            return sr;
        }

        private static void Build(HudManager hud, Costume c, KillScene scene, int victimColor, int killerColor) {
            int layer = hud.gameObject.layer;
            root = new GameObject("HalloweenKill") { layer = layer };
            root.transform.SetParent(hud.transform, false);
            root.transform.localPosition = new Vector3(0f, 0f, -500f);
            active = c;
            activeScene = scene;
            startTime = Time.time;
            shownFrame = -1;

            // Stage: black field with the red slanted band of the vanilla kill overlay.
            var white = UCAssets.OverlayWhite;
            var dim = MakeSr("dim", 0, layer);
            dim.sprite = white;
            dim.color = new Color(0.04f, 0.024f, 0.04f, 1f);
            dim.transform.localScale = new Vector3(400f, 400f, 1f);
            band = MakeSr("band", 1, layer);
            band.sprite = white;
            band.color = BandDark;
            float unit = white != null ? Mathf.Max(0.0001f, white.bounds.size.y) : 0.04f;
            band.transform.localScale = new Vector3(400f, 5.2f / unit, 1f);
            band.transform.localRotation = Quaternion.Euler(0f, 0f, 6.8f);

            // The stage is 9.44 x 5.9 units (the HUD camera shows 6 units of height); the scale follows
            // from the width of whatever resolution the frames were exported at (ShowFrame).
            for (int i = 0; i < Layers.Length; i++) {
                layerSr[i] = MakeSr(Layers[i], 10 + i, layer);
                layerSr[i].maskInteraction = SpriteMaskInteraction.None;
            }
            // Body and shade masks are white; the renderer colour tints them in the victim's (v*) or
            // the killer's (u*, o*) colours.
            Tint(LayerBody, LayerShade, victimColor);
            foreach (int k in new[] { 0, 1 }) Tint(KillerBody[k], KillerShade[k], killerColor);
            var sc = scene;
            KillFramePrefetch.Start(scene.Frames, Layers.Length, (f, l) => FramePath(sc, f, l));
            ShowFrame(0);
            PlayVanillaStinger(hud);
        }

        private static void Tint(int bodyLayer, int shadeLayer, int colorId) {
            Color body = Color.red, shade = new Color(0.5f, 0f, 0f, 1f);
            try {
                var bodies = Palette.PlayerColors;
                var shades = Palette.ShadowColors;
                if (bodies != null && colorId >= 0 && colorId < bodies.Length) body = bodies[colorId];
                if (shades != null && colorId >= 0 && colorId < shades.Length) shade = shades[colorId];
            } catch { }
            layerSr[bodyLayer].color = new Color(body.r, body.g, body.b, 1f);
            layerSr[shadeLayer].color = new Color(shade.r, shade.g, shade.b, 1f);
        }

        // The picture each layer currently shows, and one texture + sprite per decoded picture for the whole scene: a
        // layer that holds still or comes back to an earlier picture costs nothing (KillFramePrefetch, 2026-10-26).
        private static readonly KillFramePrefetch.Picture[] shownPic = new KillFramePrefetch.Picture[Layers.Length];
        private static readonly Dictionary<KillFramePrefetch.Picture, (Texture2D tex, Sprite sprite, float fit)> picSprites = new();

        private static string FramePath(KillScene scene, int frame, int layer) =>
            !scene.Killer && IsKillerLayer(layer) ? null : Res + $"hk_{scene.Key}_{Layers[layer]}_{frame + 1:00}.png";

        private static bool loggedRawError;

        private static void ShowFrame(int frame) {
            shownFrame = frame;
            for (int i = 0; i < Layers.Length; i++) {
                string path = FramePath(activeScene, frame, i);
                if (path == null) continue;
                var pic = KillFramePrefetch.Get(frame, i, path);
                if (pic == null || pic == shownPic[i]) continue;
                if (!picSprites.TryGetValue(pic, out var entry)) {
                    var tex = new Texture2D(Math.Max(2, pic.W), Math.Max(2, pic.H), TextureFormat.RGBA32, false);
                    tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                    bool ok;
                    ok = false;
                    if (pic.Rgba != null && pic.W > 1 && pic.H > 1 && pic.Rgba.Length == pic.W * pic.H * 4) {
                        // pinned managed array straight into the texture (no Il2Cpp array copy)
                        var pin = System.Runtime.InteropServices.GCHandle.Alloc(pic.Rgba, System.Runtime.InteropServices.GCHandleType.Pinned);
                        try {
                            tex.LoadRawTextureData(pin.AddrOfPinnedObject(), pic.Rgba.Length);
                            tex.Apply(false, true);
                            ok = true;
                        } catch (Exception e) {
                            if (!loggedRawError) {
                                loggedRawError = true;
                                HalloweenPlugin.Logger?.LogWarning($"[Halloween] raw kill frame upload failed ({pic.W}x{pic.H}, {pic.Rgba.Length} bytes, texture {tex.width}x{tex.height} {tex.format} mips {tex.mipmapCount}): {e.Message}");
                            }
                        } finally { pin.Free(); }
                    }
                    if (!ok) {
                        UnityEngine.Object.Destroy(tex);
                        tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                        tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                        ok = ImageConversion.LoadImage(tex, pic.Png, true);
                    }
                    if (!ok) { UnityEngine.Object.Destroy(tex); continue; }
                    // Cropped frames (tmp/halloween_hats_v2/killcrop.py) carry their place on the stage; the
                    // pivot puts the stage centre where the full frame's centre was, so nothing moves.
                    int stageW = tex.width;
                    var pivot = new Vector2(0.5f, 0.5f);
                    if (TryReadCrop(pic.Png, out int cw, out int ch, out int cx, out int cy)) {
                        stageW = cw;
                        pivot = new Vector2((cw * 0.5f - cx) / Mathf.Max(1, tex.width),
                                            (ch * 0.5f - (ch - cy - tex.height)) / Mathf.Max(1, tex.height));
                    }
                    var sprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), pivot, 100f);
                    sprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                    entry = (tex, sprite, StageWidth * 100f / Mathf.Max(1, stageW));
                    picSprites[pic] = entry;
                    pic.Rgba = null;                                            // on the GPU now
                }
                if (layerSr[i] != null) {
                    layerSr[i].transform.localScale = new Vector3(entry.fit, entry.fit, 1f);
                    layerSr[i].sprite = entry.sprite;
                }
                shownPic[i] = pic;
            }
            if (band != null) band.color = Array.IndexOf(activeScene.Flashes, frame) >= 0
                ? (HalloweenPlugin.Calm ? Color.Lerp(BandDark, BandFlash, 0.2f) : BandFlash) : BandDark;
        }

        /// <summary>The "hkcrop" text chunk of a cropped kill frame: stage width/height and the top-left corner of
        /// the cropped picture on it. Read from the PNG bytes up to the first IDAT; false = uncropped file.</summary>
        private static bool TryReadCrop(byte[] png, out int stageW, out int stageH, out int x, out int y) {
            stageW = stageH = x = y = 0;
            try {
                int p = 8;                                                      // after the PNG signature
                while (p + 8 <= png.Length) {
                    int len = (png[p] << 24) | (png[p + 1] << 16) | (png[p + 2] << 8) | png[p + 3];
                    if (len < 0 || p + 12 + len > png.Length) return false;
                    bool idat = png[p + 4] == 'I' && png[p + 5] == 'D' && png[p + 6] == 'A' && png[p + 7] == 'T';
                    if (idat) return false;
                    bool text = png[p + 4] == 't' && png[p + 5] == 'E' && png[p + 6] == 'X' && png[p + 7] == 't';
                    if (text) {
                        string s = System.Text.Encoding.Latin1.GetString(png, p + 8, len);
                        if (s.StartsWith("hkcrop\0", StringComparison.Ordinal)) {
                            var v = s.Substring(7).Split(',');
                            return v.Length == 4 && int.TryParse(v[0], out stageW) && int.TryParse(v[1], out stageH)
                                && int.TryParse(v[2], out x) && int.TryParse(v[3], out y) && stageW > 0 && stageH > 0;
                        }
                    }
                    p += 12 + len;
                }
            } catch { }
            return false;
        }

        // playback statistics of the running scene (logged with UC_HALLOWEEN_DIAG, 2026-10-26)
        private static int statShown, statSkipped;
        private static float statSlowest;

        private static void EndSequence() {
            if (DiagOn && activeScene != null)
                HalloweenPlugin.Logger?.LogInfo($"[Halloween] diag playback {activeScene.Key}: {statShown + 1} frames shown, {statSkipped} skipped, slowest change {statSlowest * 1000f:F1} ms, {picSprites.Count} pictures");
            statShown = statSkipped = 0; statSlowest = 0f;
            KillFramePrefetch.Stop();
            for (int i = 0; i < shownPic.Length; i++) shownPic[i] = null;
            foreach (var e in picSprites.Values) {
                if (e.sprite != null) UnityEngine.Object.Destroy(e.sprite);
                if (e.tex != null) UnityEngine.Object.Destroy(e.tex);
            }
            picSprites.Clear();
            if (root != null) UnityEngine.Object.Destroy(root);
            root = null;
            active = null;
            activeScene = null;
            band = null;
            for (int i = 0; i < Layers.Length; i++) layerSr[i] = null;
        }

        // ==================== self test (only with the environment variable UC_HALLOWEEN_DIAG=1) ====================
        //
        // Starts a freeplay round on its own, puts each costume on the local player, photographs
        // standing / walking / every kill scene into <game>\UCShots\halloween\ and, once, the bare
        // crewmate together with the hat canvas rectangle in screen pixels - the measurement the
        // costume artwork is calibrated against. Ends with "[Halloween] diag: all done" and quits.
        // Nothing here runs without the environment variable; no config entry, nothing to forget on.

        // "1" = everything, "role" = only the Xenomorph role steps, "corpse" = the corpse probe (HalloweenCorpse).
        private static readonly string DiagMode = Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "";
        private static readonly bool DiagOn = DiagMode == "1" || DiagMode == "role" || DiagMode == "corpse" || DiagMode == "spider" || DiagMode == "masquerade" || DiagMode == "banshee"
                                             || DiagMode.StartsWith("costumes:", StringComparison.Ordinal);
        private static bool diagHideHat;
        private static string diagRectTag;
        private static float diagWalk, diagWalkY;
        private static bool diagRunInPlace;
        private static string diagDir;

        private static bool DiagTick(HatParent hat, SpriteRenderer front, SpriteRenderer back) {
            try {
                var lp = PlayerControl.LocalPlayer;
                if (lp == null || OwnerOf(hat) != lp) return false;
                if (diagRectTag != null && front != null && front.sprite != null && Camera.main != null) {
                    var sp = front.sprite;
                    float ppu = sp.pixelsPerUnit;
                    // via the parent: the layer itself may be scaled to zero (hidden) right now
                    var par = front.transform.parent;
                    var lpz = front.transform.localPosition;
                    var a = par.TransformPoint(lpz + new Vector3(-sp.pivot.x / ppu, -sp.pivot.y / ppu, 0f));
                    var b = par.TransformPoint(lpz + new Vector3((sp.rect.width - sp.pivot.x) / ppu, (sp.rect.height - sp.pivot.y) / ppu, 0f));
                    var sa = Camera.main.WorldToScreenPoint(a);
                    var sb = Camera.main.WorldToScreenPoint(b);
                    float nt = -1f;
                    try { nt = lp.MyPhysics.Animations.Animator.m_animator.GetCurrentAnimatorStateInfo(0).normalizedTime; } catch { }
                    HalloweenPlugin.Logger?.LogInfo(FormattableString.Invariant(
                        $"[Halloween] rect {diagRectTag} {sa.x:F2} {sa.y:F2} {sb.x:F2} {sb.y:F2} screen {Screen.width} {Screen.height} flip {(front.flipX ? 1 : 0)} run {nt:F3} frontLocal {front.transform.localPosition.x:F4} {front.transform.localPosition.y:F4}"));
                    diagRectTag = null;
                }
                SetHidden(front, diagHideHat);
                if (diagHideHat) {
                    SetHidden(back, true);
                    return true;
                }
            } catch { }
            return false;
        }

        [HarmonyPatch(typeof(MainMenuManager), nameof(MainMenuManager.Start))]
        static class DiagMenuPatch {
            static bool fired;
            static void Postfix(MainMenuManager __instance) {
                if (!DiagOn || fired) return;
                fired = true;
                __instance.StartCoroutine(DiagEnterFreeplay());
            }
        }

        private static IEnumerator DiagEnterFreeplay() {
            HalloweenPlugin.Logger?.LogInfo("[Halloween] diag: waiting for the login ...");
            float t0 = Time.time;
            while (true) {
                bool ok = false;
                try { ok = EOSManager.Instance != null && EOSManager.Instance.HasFinishedLoginFlow(); } catch { }
                if (ok) break;
                if (Time.time - t0 > 60f) { HalloweenPlugin.Logger?.LogError("[Halloween] diag: login timeout"); yield break; }
                yield return null;
            }
            try {
                var popover = UnityEngine.Object.FindObjectOfType<FreeplayPopover>(true);
                if (popover == null) { HalloweenPlugin.Logger?.LogError("[Halloween] diag: no FreeplayPopover"); yield break; }
                for (var t = popover.transform; t != null; t = t.parent) if (!t.gameObject.activeSelf) t.gameObject.SetActive(true);
                popover.Show();
                popover.PlayMap(MapNames.Skeld);
                HalloweenPlugin.Logger?.LogInfo("[Halloween] diag: freeplay started");
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Halloween] diag: freeplay failed: {e}"); }
        }

        [HarmonyPatch(typeof(PlayerPhysics), nameof(PlayerPhysics.FixedUpdate))]
        static class DiagWalkPatch {
            static void Postfix(PlayerPhysics __instance) {
                try {
                    if (!DiagOn || (diagWalk == 0f && diagWalkY == 0f) || __instance == null || !__instance.AmOwner || __instance.body == null) return;
                    __instance.body.velocity = new Vector2(diagWalk * 2.5f, diagWalkY * 2.5f);
                } catch { }
            }
        }

        // Runs on the spot: the run animation plays while the player does not move, so the hat
        // canvas rectangle logged with each shot is exact (no camera lag).
        [HarmonyPatch(typeof(PlayerPhysics), nameof(PlayerPhysics.HandleAnimation))]
        static class DiagRunInPlacePatch {
            static bool Prefix(PlayerPhysics __instance) {
                try {
                    if (!DiagOn || !diagRunInPlace || __instance == null || !__instance.AmOwner) return true;
                    if (!__instance.Animations.IsPlayingRunAnimation()) __instance.Animations.PlayRunAnimation();
                    return false;
                } catch { return true; }
            }
        }

        private static List<(float wait, Action act)> diagSteps;
        private static int diagStep;
        private static float diagAt = -1f;

        // The corpse probe (HalloweenCorpse.ProbeSteps) walks the player through the same hook.
        internal static void DiagSetWalk(float dir) => diagWalk = dir;

        // Every sprite renderer of the player with everything Unity sorts by (layer, order, queue, world z).
        private static void DiagDumpRenderers(PlayerControl lp, string tag) {
            try {
                var cam = Camera.main;
                foreach (var sr in lp.GetComponentsInChildren<SpriteRenderer>(true)) {
                    if (sr == null) continue;
                    string path = sr.name;
                    for (var t = sr.transform.parent; t != null && t != lp.transform; t = t.parent) path = t.name + "/" + path;
                    var mat = sr.sharedMaterial;
                    HalloweenPlugin.Logger?.LogInfo(FormattableString.Invariant(
                        $"[Halloween] sr {tag} {path} on {(sr.enabled && sr.gameObject.activeInHierarchy ? 1 : 0)} layer {sr.sortingLayerName}({sr.sortingLayerID}) order {sr.sortingOrder} z {sr.transform.position.z:R} lz {sr.transform.localPosition.z:R} queue {(mat != null ? mat.renderQueue : -1)} mat {(mat != null ? mat.name : "-")} prio {sr.rendererPriority} sprite {(sr.sprite != null ? sr.sprite.name : "-")}"));
                }
                if (cam != null) HalloweenPlugin.Logger?.LogInfo(FormattableString.Invariant($"[Halloween] cam z {cam.transform.position.z:R} ortho {cam.orthographic} sortmode {cam.transparencySortMode} axis {cam.transparencySortAxis}"));
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"[Halloween] diag dump: {e.Message}"); }
        }

        private static void DiagShot(string name) {
            try {
                ScreenCapture.CaptureScreenshot(Path.Combine(diagDir, name + ".png"));
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"[Halloween] diag shot {name}: {e.Message}"); }
        }

        private static void DiagBuild(PlayerControl lp) {
            diagDir = Path.Combine(BepInEx.Paths.GameRootPath, "UCShots", "halloween");
            Directory.CreateDirectory(diagDir);
            var steps = new List<(float, Action)>();
            void Add(float wait, Action act) => steps.Add((wait, act));
            var worn = Costumes.Where(c => c.HatId != null).ToList();
            if (DiagMode == "corpse") {
                HalloweenCorpse.ProbeSteps(lp, steps, diagDir, DiagShot);
                Add(1.0f, () => HalloweenPlugin.Logger?.LogInfo("[Halloween] diag: all done"));
                Add(0f, () => Application.Quit());
                diagSteps = steps;
                return;
            }

            if (DiagMode == "banshee") {
                // Banshee: become her, walk away from the dummies (some go out of sight), scream
                Add(3.0f, () => Banshee.DiagMakeLocal());
                Add(0.5f, () => { diagWalk = 1f; });
                Add(1.4f, () => { diagWalk = 0f; });
                Add(0.6f, () => Banshee.DiagScream());
                Add(0.2f, () => DiagShot("banshee_0"));
                Add(0.5f, () => DiagShot("banshee_1"));
                Add(0.8f, () => DiagShot("banshee_2"));
                Add(1.5f, () => DiagShot("banshee_after"));
                Add(1.0f, () => HalloweenPlugin.Logger?.LogInfo("[Halloween] diag: all done"));
                Add(0f, () => Application.Quit());
                diagSteps = steps;
                return;
            }
            if (DiagMode == "masquerade") {
                // Masquerade: the freeplay dummies dressed up, then a reshuffle as after a meeting
                Add(3.0f, () => DiagShot("masq_part0"));
                Add(0.3f, () => { diagWalk = 0.65f; });
                Add(0.6f, () => { diagWalk = 0f; DiagShot("masq_part0_walk"); });
                Add(0.5f, () => Masquerade.DiagNextPart());
                Add(1.0f, () => DiagShot("masq_part1"));
                Add(0.5f, () => Masquerade.DiagNextPart());
                Add(1.0f, () => DiagShot("masq_part2"));
                Add(1.0f, () => HalloweenPlugin.Logger?.LogInfo("[Halloween] diag: all done"));
                Add(0f, () => Application.Quit());
                diagSteps = steps;
                return;
            }
            if (DiagMode.StartsWith("costumes:", StringComparison.Ordinal)) {
                // UC_HALLOWEEN_DIAG=costumes:vampire,medusa - only these costumes: standing, walking right and left,
                // then each kill scene with shots through to the end (and after it, to see whether the last frame holds)
                var keys = DiagMode.Substring("costumes:".Length).Split(',').Select(k => k.Trim()).Where(k => k.Length > 0).ToList();
                var pick = Costumes.Where(c => c.HatId != null && keys.Contains(c.Key)).ToList();
                Add(0.5f, () => { try { lp.RpcSetColor(10); } catch { } });
                // size reference: the plain crewmate without a costume (2026-10-26)
                Add(0.6f, () => { try { lp.RpcSetHat("hat_NoHat"); } catch { } });
                Add(1.0f, () => DiagShot("plain_idle"));
                foreach (var c in pick) {
                    var cc = c;
                    Add(1.6f, () => lp.RpcSetHat(cc.HatId));
                    Add(0.4f, () => DiagShot(cc.Key + "_idle_0"));
                    Add(0.5f, () => DiagShot(cc.Key + "_idle_1"));
                    Add(0.3f, () => { diagWalk = 0.65f; });
                    for (int k = 0; k < 4; k++) { int kk = k; Add(0.13f, () => DiagShot(cc.Key + "_walk_" + kk)); }
                    Add(0.1f, () => { diagWalk = -0.65f; });
                    Add(0.5f, () => DiagShot(cc.Key + "_walkleft"));
                    Add(0.1f, () => { diagWalk = 0f; });
                    Add(0.15f, () => DiagShot(cc.Key + "_land"));                // flying costume: landing frames
                    Add(0.65f, () => { try { lp.RpcSetColor(4); } catch { } });
                    Add(0.6f, () => DiagShot(cc.Key + "_idle_color4"));
                    Add(0.2f, () => { try { lp.RpcSetColor(10); } catch { } });
                }
                if (keys.Contains("corpseswap")) {
                    // User 2026-10-26: a whole-figure costume, then the corpse, then another costume left the player invisible
                    string jason = Costumes.FirstOrDefault(c => c.Key == "jason")?.HatId, ghost = Costumes.FirstOrDefault(c => c.Key == "ghostface")?.HatId;
                    string corpse = UCHats.HatIdOf(HalloweenCorpse.HatName);
                    Add(1.0f, () => { if (jason != null) lp.RpcSetHat(jason); });
                    Add(0.8f, () => DiagShot("swap_1_jason"));
                    Add(0.2f, () => { if (corpse != null) lp.RpcSetHat(corpse); });
                    Add(0.8f, () => DiagShot("swap_2_corpse"));
                    Add(0.2f, () => { if (ghost != null) lp.RpcSetHat(ghost); });
                    Add(0.8f, () => DiagShot("swap_3_ghostface"));
                    Add(0.2f, () => { if (corpse != null) lp.RpcSetHat(corpse); });
                    Add(0.3f, () => { diagWalk = 0.65f; });
                    Add(0.5f, () => DiagShot("swap_4_corpse_walk"));
                    Add(0.1f, () => { diagWalk = 0f; });
                    Add(0.2f, () => { if (jason != null) lp.RpcSetHat(jason); });
                    Add(0.8f, () => DiagShot("swap_5_jason"));
                }
                void SceneShots(string shotKey, string sceneKey, int frames, float hold) {
                    float len = frames / KillFps;
                    // shots at 15/35/55/75/95 % of the scene, 0.5 s after its end (Medusa: statue still held) and after the hold
                    var shots = new List<(string tag, float t)>();
                    foreach (float f in new[] { 0.15f, 0.35f, 0.55f, 0.75f, 0.95f }) shots.Add(((shots.Count).ToString(), len * f));
                    shots.Add(("hold", len + 0.5f));
                    shots.Add(("after", len + hold + 1.0f));
                    Add(shots[0].t + 0.05f, () => HalloweenPlugin.Logger?.LogInfo("[Halloween] diag preview: " + Preview(sceneKey)));
                    for (int i = 0; i < shots.Count; i++) {
                        string tag = shotKey + "_kill_" + shots[i].tag;
                        Add(i + 1 < shots.Count ? shots[i + 1].t - shots[i].t : 0.5f, () => DiagShot(tag));
                    }
                }
                foreach (var c in pick) {
                    if (c.KillKey == null) continue;
                    SceneShots(c.Key, c.KillKey, c.KillFrames, c.KillHold);
                    // alternative scenes too (2026-10-26: xenobite, jasonlift redrawn)
                    if (c.Alt != null) foreach (var s in c.Alt) SceneShots(s.Key, s.Key, s.Frames, s.Hold);
                }
                Add(1.0f, () => HalloweenPlugin.Logger?.LogInfo("[Halloween] diag: all done"));
                Add(0f, () => Application.Quit());
                diagSteps = steps;
                return;
            }
            if (DiagMode == "spider") {
                // live legs (SpiderLegs): how the game sorts the player's renderers, then walk, stop, turn
                var sp = Costumes.FirstOrDefault(c => c.Key == "spider" && c.HatId != null);
                Add(0.5f, () => { try { lp.RpcSetColor(10); } catch { } });
                if (sp != null) {
                    Add(1.0f, () => lp.RpcSetHat(sp.HatId));
                    Add(1.5f, () => { DiagDumpRenderers(lp, "idle"); DiagShot("spider_idle"); });
                    // 0.65 x 2.5 units/s ~ 450 bean units/s, what a real round measured (diagWalk 1 = 635)
                    Add(0.3f, () => { diagWalk = 0.65f; });
                    for (int k = 0; k < 8; k++) { int kk = k; Add(0.12f, () => DiagShot("spider_walk_" + kk)); }
                    Add(0.1f, () => DiagDumpRenderers(lp, "walk"));
                    Add(0.1f, () => { diagWalk = 0f; });
                    for (int k = 0; k < 6; k++) { int kk = k; Add(0.15f, () => DiagShot("spider_stop_" + kk)); }
                    Add(0.5f, () => { diagWalk = -0.65f; });
                    for (int k = 0; k < 6; k++) { int kk = k; Add(0.12f, () => DiagShot("spider_left_" + kk)); }
                    Add(0.1f, () => { diagWalk = 0f; });
                    Add(1.2f, () => DiagShot("spider_end"));
                    // up and down the map (2026-10-17: feet slid and legs folded there)
                    Add(0.3f, () => { diagWalkY = 0.65f; });
                    for (int k = 0; k < 6; k++) { int kk = k; Add(0.12f, () => DiagShot("spider_up_" + kk)); }
                    Add(0.1f, () => { diagWalkY = 0f; });
                    Add(0.9f, () => { diagWalkY = -0.65f; });
                    for (int k = 0; k < 6; k++) { int kk = k; Add(0.12f, () => DiagShot("spider_down_" + kk)); }
                    Add(0.1f, () => { diagWalkY = 0f; });
                    Add(1.0f, () => DiagShot("spider_end2"));
                }
                Add(1.0f, () => HalloweenPlugin.Logger?.LogInfo("[Halloween] diag: all done"));
                Add(0f, () => Application.Quit());
                diagSteps = steps;
                return;
            }
            Add(0.5f, () => { try { lp.RpcSetColor(10); } catch { } });
            if (DiagMode == "role") worn.Clear();
            if (worn.Count > 0) {
                // --- calibration: the bare crewmate with the hat canvas rectangle, standing and walking
                string oldSkin = null;
                try { oldSkin = lp.Data.DefaultOutfit.SkinId; } catch { }
                Add(0.3f, () => { try { lp.RpcSetSkin("skin_None"); } catch { } });
                Add(2.0f, () => lp.RpcSetHat(worn[0].HatId));
                Add(0.25f, () => { diagHideHat = true; });
                Add(0.5f, () => { diagRectTag = "calib_idle"; DiagShot("calib_idle"); });
                Add(0.6f, () => { diagRunInPlace = true; });
                for (int k = 0; k < 44; k++) {
                    int kk = k;
                    Add(0.071f, () => { diagRectTag = "calib_run_" + kk; DiagShot("calib_run_" + kk); });
                }
                Add(0.3f, () => { diagRunInPlace = false; });
                Add(0.7f, () => { diagWalk = 1f; });
                for (int k = 0; k < 6; k++) {
                    int kk = k;
                    Add(0.11f, () => { diagRectTag = "calib_walk_" + kk; DiagShot("calib_walk_" + kk); });
                }
                Add(0.4f, () => { diagWalk = 0f; diagHideHat = false; });
                Add(0.3f, () => { try { if (!string.IsNullOrEmpty(oldSkin)) lp.RpcSetSkin(oldSkin); } catch { } });
            }
            foreach (var name in DiagMode == "role" ? new string[0] : new[] { "Virus", "Werbetafel", UCHats.WerewolfHatName, UCHats.HunterHatName }) {
                string id = UCHats.HatIdOf(name), tag = "uc_" + name.Replace(' ', '_').ToLowerInvariant();
                Add(1.6f, () => lp.RpcSetHat(id));
                Add(0.4f, () => DiagShot(tag + "_idle"));
                Add(0.6f, () => { diagWalk = 1f; });
                for (int k = 0; k < 4; k++) {
                    int kk = k;
                    Add(0.13f, () => DiagShot(tag + "_walk_" + kk));
                }
                Add(0.7f, () => { diagWalk = -1f; });
                Add(1.15f, () => { diagWalk = 0f; });
            }
            foreach (var c in worn) {
                var cc = c;
                Add(1.6f, () => lp.RpcSetHat(cc.HatId));
                Add(0.4f, () => { diagRectTag = cc.Key + "_idle"; DiagShot(cc.Key + "_idle"); });
                Add(0.6f, () => { diagWalk = 1f; });
                for (int k = 0; k < 4; k++) {
                    int kk = k;
                    Add(0.13f, () => { diagRectTag = cc.Key + "_walk_" + kk; DiagShot(cc.Key + "_walk_" + kk); });
                }
                Add(0.7f, () => { diagWalk = -1f; });
                Add(0.2f, () => DiagShot(cc.Key + "_walkleft"));
                Add(0.6f, () => { diagWalk = 0f; });
            }
            // --- the Xenomorph ROLE: set, transform, run, kill a dummy, revert
            void Log(string what) => HalloweenPlugin.Logger?.LogInfo("[Halloween] role: " + what + " | " + Xenomorph.DiagState());
            Add(1.0f, () => { Xenomorph.SendSetXenomorph(lp.PlayerId); Log("set"); });
            Add(0.6f, () => DiagShot("role_human"));
            Add(1.2f, () => { Xenomorph.DiagForm(true); Log("form on"); });
            Add(0.2f, () => { Log("after look"); DiagShot("role_form"); });
            Add(0.5f, () => { diagWalk = 1f; });
            Add(0.2f, () => DiagShot("role_run"));
            Add(0.6f, () => { diagWalk = -1f; });
            Add(0.6f, () => { diagWalk = 0f; HalloweenPlugin.Logger?.LogInfo("[Halloween] role: " + Xenomorph.DiagKillNearest()); });
            Add(0.9f, () => DiagShot("role_kill_1"));
            Add(1.3f, () => DiagShot("role_kill_2"));
            Add(1.4f, () => { Xenomorph.DiagForm(false); Log("form off"); });
            Add(0.6f, () => { Log("reverted"); DiagShot("role_reverted"); });
            foreach (var c in DiagMode == "role" ? new Costume[0] : Costumes) {
                if (c.KillKey == null) continue;
                var cc = c;
                var keys = new List<string> { cc.KillKey };
                if (cc.Alt != null) foreach (var alt in cc.Alt) keys.Add(alt.Key);
                foreach (var key in keys) {
                    var kk = key;
                    Add(0.55f, () => HalloweenPlugin.Logger?.LogInfo("[Halloween] diag preview: " + Preview(kk)));
                    Add(0.55f, () => DiagShot(kk + "_kill_1"));
                    Add(0.75f, () => DiagShot(kk + "_kill_2"));
                    Add(0.9f, () => DiagShot(kk + "_kill_3"));
                    Add(1.0f, () => DiagShot(kk + "_kill_4"));
                    Add(1.0f, () => DiagShot(kk + "_kill_5"));
                }
            }
            Add(1.0f, () => HalloweenPlugin.Logger?.LogInfo("[Halloween] diag: all done"));
            Add(0f, () => Application.Quit());
            diagSteps = steps;
        }

        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        static class DiagHudPatch {
            static void Postfix() {
                try {
                    if (!DiagOn) return;
                    if (AmongUsClient.Instance == null || AmongUsClient.Instance.NetworkMode != NetworkModes.FreePlay) return;
                    var lp = PlayerControl.LocalPlayer;
                    if (ShipStatus.Instance == null || lp == null) { diagAt = -1f; return; }
                    float now = Time.realtimeSinceStartup;
                    if (diagAt < 0f) { diagAt = now + 8f; return; }
                    if (now < diagAt) return;
                    if (diagSteps == null) DiagBuild(lp);
                    if (diagStep >= diagSteps.Count) return;
                    var step = diagSteps[diagStep++];
                    try { step.act(); } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"[Halloween] diag step {diagStep}: {e.Message}"); }
                    diagAt = now + step.wait;
                } catch { }
            }
        }

        private static void ResetAll() {
            HalloweenCorpse.ResetAll();
            EndSequence();
            queue.Clear();
            SpiderLegs.Clear();
        }
    }
}
