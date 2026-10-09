// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * HalloweenCostumes - four full-body costume hats (Freddy, Jason, Xenomorph, Ghostface) with
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
 * UCKillOverlay has already claimed, and only if the HOST has them on (options 1793-1797, one per
 * costume). Audience is whoever the vanilla overlay would have shown to.
 * Each frame is five images: killer (back), the victim split into an untinted part (outline,
 * visor) plus a body mask and a shade mask that are tinted in the victim's colours, and the
 * foreground (blade tip, blood, impact). The victim deliberately does NOT go through the game's
 * player material: that shader obeys sprite masks, and an open chat window cut a rectangle out of
 * the victim in the first playtest (2026-10-05).
 * Sound is the vanilla kill-overlay stinger (own synthesized tracks were tried and dropped on
 * 2026-10-05: "passen einfach nicht zu Among Us").
 * Frames are decoded one at a time and thrown away again - a whole strip in memory would cost
 * well over 200 MB in a 32-bit process.
 *
 * HalloweenCostumes.Preview("freddy" | "jason" | "xeno" | "ghost") plays a cutscene locally as if the
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
            public string KillKey;      // file key of the kill frames (hk_<KillKey>_...)
            public string Name;         // hat name in the shop
            public string HatId;
            public int KillFrames;
            public int[] Flashes;       // frames on which the red band flashes
            public bool HasLegs;        // walk loop has painted legs -> hide the back layer while running
            public Sprite[] Idle, Walk;
            public bool HasAccent;      // highlight masks (hw_<Key>_acc_N) that are tinted in the wearer's colour
            public Sprite[] IdleAcc, WalkAcc;
            public bool FramesTried;
            public KillScene[] Alt;     // further cutscenes of this costume; one of all is picked at random
        }

        private sealed class KillScene {
            public string Key;          // file key (hk_<Key>_...)
            public int Frames;
            public int[] Flashes;
        }

        private static readonly Dictionary<Costume, KillScene> mainScene = new();

        /// <summary>The costume's own cutscene or one of its alternatives. <paramref name="key"/> names
        /// one exactly (preview); otherwise every kill draws afresh. The cutscene only ever plays on
        /// the victim's client, so the draw needs no syncing.</summary>
        private static KillScene PickScene(Costume c, string key = null) {
            if (!mainScene.TryGetValue(c, out var main))
                mainScene[c] = main = new KillScene { Key = c.KillKey, Frames = c.KillFrames, Flashes = c.Flashes };
            if (c.Alt == null || c.Alt.Length == 0) return main;
            if (key != null) return c.Alt.FirstOrDefault(x => x.Key == key) ?? main;
            int i = UnityEngine.Random.Range(0, c.Alt.Length + 1);
            return i == 0 ? main : c.Alt[i - 1];
        }

        private static readonly Costume[] Costumes = {
            new Costume { Key = "freddy", KillKey = "freddy", Name = "Halloween Freddy", KillFrames = 46, Flashes = new[] { 14, 20 }, HasLegs = false },
            new Costume { Key = "jason", KillKey = "jason", Name = "Halloween Jason", KillFrames = 46, Flashes = new[] { 16, 30 }, HasLegs = false,
                // diagonal slash (main) or the one-armed lift with the machete run through (2026-10-07)
                Alt = new[] { new KillScene { Key = "jasonlift", Frames = 60, Flashes = new[] { 25, 45 } } } },
            new Costume { Key = "xenomorph", KillKey = "xeno", Name = "Halloween Xenomorph", KillFrames = 46, Flashes = new[] { 17, 22 }, HasLegs = false, HasAccent = true,
                // tail stab (main) or the inner-jaw bite
                Alt = new[] { new KillScene { Key = "xenobite", Frames = 46, Flashes = new[] { 18, 31 } } } },
            // 2026-10-07: rebuilt after the Dead-by-Daylight mori (yank down, three stabs, head hauled up, selfie, rip)
            new Costume { Key = "ghostface", KillKey = "ghostface", Name = "Halloween Ghostface", KillFrames = 66, Flashes = new[] { 19, 23, 27, 44, 56 }, HasLegs = false, HasAccent = true },
        };

        // ==================== host options (2026-10-07) ====================
        //
        // The host decides for the whole lobby whether the costume cutscenes play at all and which
        // of them (TOR settings, General tab, block "Unknown's Halloween"). Until now this followed
        // UC's local "UC Kill Animations" toggle, which is gone. IDs 1793-1797 (the Xenomorph role
        // holds 1785-1792).
        public static CustomOption Anims;
        private static readonly Dictionary<string, CustomOption> perCostume = new();

        private static void CreateOptions() {
            try {
                var g = CustomOption.CustomOptionType.General;
                Anims = CustomOption.Create(1793, g, "Halloween Costume Kill Animations", true, null, true, null, "Unknown's Halloween");
                int id = 1794;
                foreach (var c in Costumes)
                    perCostume[c.Key] = CustomOption.Create(id++, g, "Kill Animation: " + c.Name.Replace("Halloween ", ""), true, Anims);
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"[Halloween] CreateOptions failed: {e}");
            }
        }

        private static bool On(CustomOption o, bool fallback) {
            try { return o == null ? fallback : o.getBool(); } catch { return fallback; }
        }

        private static bool Enabled => On(Anims, true);
        private static bool CostumeEnabled(Costume c) => Enabled && (!perCostume.TryGetValue(c.Key, out var o) || On(o, true));

        private static readonly Dictionary<string, Costume> ByHatName = new();
        private static readonly Dictionary<string, Costume> ByHatId = new();
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
                    if (!Extract($"hw_{c.Key}_1.png", main)) continue;
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
                    ByHatId[c.HatId] = c;
                }

                var harmony = new Harmony("daunknown.unknownshalloween.costumes");
                var dl = AccessTools.Method(typeof(CustomHatManager), "GenerateDownloadList");
                if (dl != null)
                    harmony.Patch(dl, postfix: new HarmonyMethod(AccessTools.Method(typeof(HalloweenCostumes), nameof(StripOwnFiles))));
                var late = AccessTools.Method(typeof(HatParent), nameof(HatParent.LateUpdate));
                if (late != null)
                    harmony.Patch(late, postfix: new HarmonyMethod(AccessTools.Method(typeof(HalloweenCostumes), nameof(HatLateUpdate))));

                UCFx.RegisterTick(Tick);
                UCFx.RegisterTick(TickLock);
                UCFx.RegisterReset(ResetAll);
                HalloweenPlugin.Logger?.LogInfo($"[Halloween] registered {ByHatName.Count} costume hat(s).");
            } catch (Exception ex) {
                HalloweenPlugin.Logger?.LogError($"[Halloween] setup failed: {ex}");
            }
        }

        private static void StripOwnFiles(List<string> __result) {
            try { __result?.RemoveAll(f => OwnFiles.Contains(f)); } catch { }
        }

        private static byte[] ReadResource(string logicalName) {
            using Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(logicalName);
            if (stream == null) return null;
            var data = new byte[stream.Length];
            int read = 0;
            while (read < data.Length) {
                int n = stream.Read(data, read, data.Length - read);
                if (n <= 0) break;
                read += n;
            }
            return read == data.Length ? data : null;
        }

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
        private static Sprite LoadHatSprite(string logicalName) {
            try {
                byte[] data = ReadResource(logicalName);
                if (data == null) return null;
                var texture = new Texture2D(2, 2, TextureFormat.ARGB32, true);
                if (!ImageConversion.LoadImage(texture, data, false)) return null;
                try { texture.Compress(true); } catch { }
                texture.Apply(false, true);
                var sprite = Sprite.Create(texture, new Rect(0, 0, texture.width, texture.height),
                    new Vector2(0.53f, 0.575f), texture.width * 0.375f);
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
            var walk = new Sprite[WalkFrames];
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
            var walkAcc = new Sprite[WalkFrames];
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
        private static void HatLateUpdate(HatParent __instance) {
            bool accentShown = false;
            try {
                if (HalloweenCorpse.Handle(__instance)) { HideAccent(__instance); return; }
                accentShown = HatLateUpdateCore(__instance);
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
            if (hat == null || !ByHatName.TryGetValue(hat.name, out var c)) return false;

            setBounceNode?.Invoke(__instance);

            var front = __instance.FrontLayer;
            var back = __instance.BackLayer;
            if (DiagOn && DiagTick(__instance, front, back)) return false;
            if (front == null || !front.enabled || front.sprite == null) return false;
            // Ladder / corpse pose: SetClimbAnim and SetFloorAnim switch the back layer off and put
            // their own image on the front layer. Never write over that.
            if (back == null || !back.enabled) return false;

            EnsureFrames(c);
            if (c.Idle == null) return false;

            bool running = false;
            float cycle = -1f;
            if (c.Walk != null) {
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
                int i = cycle >= 0f ? Mathf.FloorToInt(cycle * WalkFrames) : Mathf.FloorToInt(Time.time * HatFps);
                frame = c.Walk[((i + WalkPhaseOffset) % WalkFrames + WalkFrames) % WalkFrames];
            } else {
                frame = c.Idle[Mathf.FloorToInt(Time.time * HatFps) % IdleFrames];
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
                return hatId != null && ByHatId.TryGetValue(hatId, out var c) ? c : null;
            } catch { return null; }
        }

        private static int ColorIdOf(NetworkedPlayerInfo info) {
            try { if (info?.DefaultOutfit != null) return info.DefaultOutfit.ColorId; } catch { }
            return 0;
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
                    queue.Add((c, PickScene(c), ColorIdOf(victim), Time.time + 20f));
                    return false;                       // suppress the vanilla overlay
                } catch (Exception e) {
                    HalloweenPlugin.Logger?.LogError($"[Halloween] kill hook: {e}");
                    return true;
                }
            }
        }

        /// <summary>Plays a costume cutscene locally as if the local player had just been killed.
        /// Returns a short status line. Keys: freddy, jason (slash), jasonlift, jasonrandom, xeno (tail stab),
        /// xenobite, xenomorph (random of both), ghost / ghostface. "&lt;costume&gt;random" draws like a real kill.</summary>
        public static string Preview(string key) {
            try {
                Setup();
                key = (key ?? string.Empty).Trim().ToLowerInvariant();
                bool random = key.EndsWith("random", StringComparison.Ordinal);
                if (random) key = key.Substring(0, key.Length - "random".Length);
                var c = Costumes.FirstOrDefault(x => x.Key == key || x.KillKey == key
                                                     || (x.Alt != null && x.Alt.Any(s => s.Key == key))
                                                     || (key.Length >= 3 && x.Key.StartsWith(key)));
                if (c == null) return "Unbekannt. Moeglich: freddy, jason, jasonlift, jasonrandom, xeno, xenobite, xenomorph (zufaellig), ghost.";
                if (HudManager.Instance == null) return "Kein HUD - erst in eine Lobby oder Runde gehen.";
                int color = 0;
                try { color = PlayerControl.LocalPlayer.Data.DefaultOutfit.ColorId; } catch { }
                EndSequence();
                queue.Clear();
                // An alternative's own key plays exactly that scene, the costume's main key the main one.
                var scene = !random && (key == c.KillKey || (c.Alt != null && c.Alt.Any(s => s.Key == key))) ? PickScene(c, key) : PickScene(c);
                queue.Add((c, scene, color, Time.time + 20f));
                return $"Kill-Szene {c.Name} wird abgespielt.";
            } catch (Exception e) {
                return "Fehler: " + e.Message;
            }
        }

        // ==================== kill cutscene: playback ====================

        private static readonly List<(Costume c, KillScene scene, int victimColor, float expires)> queue = new();
        private static readonly string[] Layers = { "back", "vrest", "vbody", "vshade", "front" };
        private const int LayerBody = 2, LayerShade = 3;
        private const float StageWidth = 9.44f;
        private static readonly Color BandDark = new Color(0.588f, 0.055f, 0.078f, 1f);
        private static readonly Color BandFlash = new Color(0.925f, 0.235f, 0.204f, 1f);

        private static GameObject root;
        private static Costume active;
        private static KillScene activeScene;
        private static float startTime;
        private static int shownFrame;
        private static SpriteRenderer band;
        private static readonly SpriteRenderer[] layerSr = new SpriteRenderer[5];
        private static readonly Texture2D[] layerTex = new Texture2D[5];
        private static readonly Sprite[] layerSprite = new Sprite[5];

        private static void Tick() {
            try {
                for (int i = queue.Count - 1; i >= 0; i--)
                    if (Time.time > queue[i].expires) queue.RemoveAt(i);

                bool uiBlocked = MeetingHud.Instance != null || ExileController.Instance != null;
                if (root != null) {
                    if (uiBlocked) { EndSequence(); return; }
                    int frame = Mathf.FloorToInt((Time.time - startTime) * KillFps);
                    if (frame >= activeScene.Frames) { EndSequence(); return; }
                    if (frame != shownFrame) ShowFrame(frame);
                    return;
                }
                if (queue.Count == 0 || uiBlocked) return;
                var hud = HudManager.Instance;
                if (hud == null) return;
                var next = queue[0];
                queue.RemoveAt(0);
                Build(hud, next.c, next.scene, next.victimColor);
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

        private static void Build(HudManager hud, Costume c, KillScene scene, int victimColor) {
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
            // Body and shade masks are white; the renderer colour tints them in the victim's colours.
            Color body = Color.red, shade = new Color(0.5f, 0f, 0f, 1f);
            try {
                var bodies = Palette.PlayerColors;
                var shades = Palette.ShadowColors;
                if (bodies != null && victimColor >= 0 && victimColor < bodies.Length) body = bodies[victimColor];
                if (shades != null && victimColor >= 0 && victimColor < shades.Length) shade = shades[victimColor];
            } catch { }
            layerSr[LayerBody].color = new Color(body.r, body.g, body.b, 1f);
            layerSr[LayerShade].color = new Color(shade.r, shade.g, shade.b, 1f);
            ShowFrame(0);
            PlayVanillaStinger(hud);
        }

        // Bytes of the frame each layer currently shows. An identical next file (the layer holds still, 14 % of all
        // layer frames) keeps texture and sprite instead of decoding the same picture again.
        private static readonly byte[][] layerData = new byte[5][];

        private static void ShowFrame(int frame) {
            shownFrame = frame;
            for (int i = 0; i < Layers.Length; i++) {
                byte[] data = ReadResource(Res + $"hk_{activeScene.Key}_{Layers[i]}_{frame + 1:00}.png");
                if (data == null) continue;
                if (layerData[i] != null && layerSprite[i] != null && data.AsSpan().SequenceEqual(layerData[i])) continue;
                if (layerTex[i] == null) {
                    layerTex[i] = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                    layerTex[i].hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                }
                if (!ImageConversion.LoadImage(layerTex[i], data, false)) continue;
                layerData[i] = data;
                var tex = layerTex[i];
                // Cropped frames (tmp/halloween_hats_v2/killcrop.py) carry their place on the stage; the
                // pivot puts the stage centre where the full frame's centre was, so nothing moves.
                int stageW = tex.width, stageH = tex.height;
                var pivot = new Vector2(0.5f, 0.5f);
                if (TryReadCrop(data, out int cw, out int ch, out int cx, out int cy)) {
                    stageW = cw; stageH = ch;
                    pivot = new Vector2((cw * 0.5f - cx) / Mathf.Max(1, tex.width),
                                        (ch * 0.5f - (ch - cy - tex.height)) / Mathf.Max(1, tex.height));
                }
                var sprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), pivot, 100f);
                float fit = StageWidth * 100f / Mathf.Max(1, stageW);
                if (layerSr[i] != null) layerSr[i].transform.localScale = new Vector3(fit, fit, 1f);
                sprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                if (layerSr[i] != null) layerSr[i].sprite = sprite;
                if (layerSprite[i] != null) UnityEngine.Object.Destroy(layerSprite[i]);
                layerSprite[i] = sprite;
            }
            if (band != null) band.color = Array.IndexOf(activeScene.Flashes, frame) >= 0 ? BandFlash : BandDark;
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

        private static void EndSequence() {
            for (int i = 0; i < layerData.Length; i++) layerData[i] = null;
            if (root != null) UnityEngine.Object.Destroy(root);
            root = null;
            active = null;
            activeScene = null;
            band = null;
            for (int i = 0; i < Layers.Length; i++) {
                layerSr[i] = null;
                if (layerSprite[i] != null) UnityEngine.Object.Destroy(layerSprite[i]);
                layerSprite[i] = null;
                if (layerTex[i] != null) UnityEngine.Object.Destroy(layerTex[i]);
                layerTex[i] = null;
            }
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
        private static readonly bool DiagOn = DiagMode == "1" || DiagMode == "role" || DiagMode == "corpse";
        private static bool diagHideHat;
        private static string diagRectTag;
        private static float diagWalk;
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
                    if (!DiagOn || diagWalk == 0f || __instance == null || !__instance.AmOwner || __instance.body == null) return;
                    __instance.body.velocity = new Vector2(diagWalk * 2.5f, 0f);
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
        }
    }
}
