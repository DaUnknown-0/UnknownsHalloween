// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
// Based on The Other Roles (https://github.com/TheOtherRolesAU/TheOtherRoles), GPL-3.0.

/*
 * Scaredy-Cat (crew modifier, idea A6, 2026-10-20)
 *
 * When the Scaredy-Cat sees a body he screams on his own: a big exclamation mark pops up over him (a world object,
 * so only those who have him in sight see it) and everybody reads "Someone screams in <room>!" without a name.
 * He does not have to report; the body is given away all the same. Crew only (an impostor would give his own kill
 * away), never together with another modifier.
 *
 *  - Sight check on the carrier's client: the body lies inside his light radius and no shadow wall is in between.
 *  - The host checks before telling everybody: the sender is the carrier and alive, no meeting, the body exists and
 *    lies within the carrier's light radius (host side, with some slack for the lag), every body only once, the
 *    cooldown between two screams. No invented screams.
 *  - The room comes from the rooms of ShipStatus (Atlas maps rename them through TranslationController).
 *
 * Registration like the UC modifiers (Giant, Colorblind): host pick in IntroCutscene.OnDestroy, display through a
 * RoleInfo with the sentinel RoleId 238 appended in getRoleInfoForPlayer; UC's HasAnyModifier learns about him
 * through a postfix in HwMechanics. Options 2060-2062, RPC module 241 Sub 0-2.
 *
 * Pictures: Resources/hw2026/scaredy/scaredy_exclaim.png (128, the mark) and scaredy_icon.png (128, on the banner).
 * Self test: UC_HALLOWEEN_DIAG=scaredy (HwMechanicsDiag.cs).
 */

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using TMPro;
using UnityEngine;
using TheOtherRoles;
using UnknownsCollection;
using Types = TheOtherRoles.CustomOption.CustomOptionType;

namespace UnknownsHalloween {
    internal static class HwScaredyCat {
        // Startled yellow: reads as "alarm" and is no team colour.
        public static readonly Color Color = new Color(1.0f, 0.82f, 0.25f);
        private const string Folder = "scaredy";

        // ---- options (2060-2062) ----
        public static CustomOption SpawnRate, MarkTime, Cooldown;
        private static readonly string[] MarkLabels = { "2s", "3s", "4s", "5s", "6s", "8s" };
        private static readonly float[] MarkSeconds = { 2f, 3f, 4f, 5f, 6f, 8f };
        private static readonly string[] CooldownLabels = { "0s", "5s", "10s", "15s", "20s", "30s" };
        private static readonly float[] CooldownSeconds = { 0f, 5f, 10f, 15f, 20f, 30f };

        internal static void CreateOptions() {
            try {
                SpawnRate = CustomOption.Create(2060, Types.Modifier, "Scaredy-Cat", CustomOptionHolder.rates, null, true);
                MarkTime = CustomOption.Create(2061, Types.Modifier, "Scaredy-Cat Mark Shows For", MarkLabels, SpawnRate);
                Cooldown = CustomOption.Create(2062, Types.Modifier, "Scaredy-Cat Scream Cooldown", CooldownLabels, SpawnRate);
                try { MarkTime.selection = 2; Cooldown.selection = 2; } catch { }      // 4 s, 10 s
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Scaredy] options failed: {e}"); }
        }

        internal static bool Enabled() => SpawnRate != null && SpawnRate.getSelection() > 0;
        private static float MarkFor() => MarkSeconds[Mathf.Clamp(MarkTime?.getSelection() ?? 2, 0, MarkSeconds.Length - 1)];
        private static float CooldownFor() => CooldownSeconds[Mathf.Clamp(Cooldown?.getSelection() ?? 2, 0, CooldownSeconds.Length - 1)];

        // ---- state ----
        internal static PlayerControl carrier;
        internal static bool active;
        private static readonly HashSet<byte> seenLocal = new();      // carrier client: bodies already reported
        private static readonly HashSet<byte> screamedHost = new();   // host: bodies already screamed about
        private static float lastScreamHost = -100f, nextLook;
        private static readonly System.Random rnd = new System.Random();
        internal static int DiagScreams;                              // self test: screams applied
        internal static string LastText = "";

        internal const RoleId RoleIdSentinel = (RoleId)238;
        private static RoleInfo info;
        internal static RoleInfo Info() => info ??= new RoleInfo(
            "Scaredy-Cat", Color, "You scream when you see a body", "Screams at every body", RoleIdSentinel, false, true);

        internal static bool IsCarrier(PlayerControl p) => active && carrier != null && p != null && p.PlayerId == carrier.PlayerId;
        internal static bool IsLocalCarrier() => IsCarrier(PlayerControl.LocalPlayer);

        // ---- RPC ----
        internal static void HandleRpc(byte sub, Hazel.MessageReader r) {
            switch (sub) {
                case HwMechanics.SubScaredySet: {
                    byte id = r.ReadByte();
                    if (UCRpc.RequireHost("Scaredy.Set")) ApplySet(id);
                    break;
                }
                case HwMechanics.SubScaredySaw: {
                    byte body = r.ReadByte();
                    if (HwMechanics.AmHost()) HostSaw(UCRpc.Sender, body);
                    break;
                }
                case HwMechanics.SubScaredyScream: {
                    byte who = r.ReadByte(), body = r.ReadByte(), room = r.ReadByte();
                    if (UCRpc.RequireHost("Scaredy.Scream")) ApplyScream(who, body, room);
                    break;
                }
            }
        }

        internal static void SendSet(byte id) {
            HwMechanics.Send(HwMechanics.SubScaredySet, w => w.Write(id));
            ApplySet(id);
        }

        private static void ApplySet(byte id) {
            carrier = id == byte.MaxValue ? null : Helpers.playerById(id);
            active = carrier != null;
            seenLocal.Clear();
            if (!active) return;
            HwMechanics.Log($"Scaredy-Cat is {carrier.Data?.PlayerName}.");
            // modifier pattern: no Claim (he keeps his role), only the reveal cue for the carrier
            try { if (IsLocalCarrier()) UCRevealFx.PlayReveal(); } catch { }
        }

        // ---- pick (host) ----
        [HarmonyPatch(typeof(IntroCutscene), nameof(IntroCutscene.OnDestroy))]
        static class IntroEndPickPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix() {
                try {
                    if (!HwMechanics.AmHost() || active || !Enabled()) return;
                    if (!TeslaVersionHandshake.EveryoneHasMod()) return;
                    if (rnd.Next(1, 101) > SpawnRate.getSelection() * 10) return;
                    var candidates = PlayerControl.AllPlayerControls.ToArray().Where(IsCandidate).ToList();
                    if (candidates.Count == 0) return;
                    SendSet(candidates[rnd.Next(candidates.Count)].PlayerId);
                } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Scaredy] pick failed: {e}"); }
            }
        }

        private static bool IsCandidate(PlayerControl p) {
            try {
                if (!UCPromotion.IsAlive(p) || p.Data.Role == null || p.Data.Role.IsImpostor) return false;
                if (UCPromotion.HasAnyModifier(p)) return false;
                var ri = RoleInfo.getRoleInfoForPlayer(p, false).FirstOrDefault();
                return ri == null || !ri.isNeutral;
            } catch { return false; }
        }

        // ---- display: append the modifier like the UC modifiers do ----
        [HarmonyPatch(typeof(RoleInfo), nameof(RoleInfo.getRoleInfoForPlayer))]
        static class RoleInfoPatch {
            public static void Postfix(PlayerControl p, [HarmonyArgument(1)] bool showModifier, ref List<RoleInfo> __result) {
                try {
                    if (!active || carrier == null || p == null || p != carrier || __result == null || !showModifier) return;
                    if (!__result.Contains(Info())) __result.Add(Info());
                } catch { }
            }
        }

        // ---- sight check (carrier client) ----
        internal static void Tick() {
            TickMarks();
            TickBanner();
            if (!active || !IsLocalCarrier() || !HwMechanics.InRound() || HwMechanics.InMeeting()) return;
            var lp = PlayerControl.LocalPlayer;
            if (!HwMechanics.IsAlive(lp) || Time.time < nextLook) return;
            nextLook = Time.time + 0.2f;
            float radius = 3f;
            try { radius = ShipStatus.Instance.CalculateLightRadius(lp.Data); } catch { }
            var me = lp.GetTruePosition();
            foreach (var db in UnityEngine.Object.FindObjectsOfType<DeadBody>()) {
                if (db == null || seenLocal.Contains(db.ParentId) || !Visible(db)) continue;
                var bp = db.TruePosition;
                if ((bp - me).magnitude > radius) continue;
                if (PhysicsHelpers.AnythingBetween(me, bp, Constants.ShadowMask, false)) continue;
                seenLocal.Add(db.ParentId);
                HwMechanics.Log($"carrier sees body {db.ParentId} at {(bp - me).magnitude:F1} u (light {radius:F1}).");
                if (HwMechanics.AmHost()) HostSaw(lp, db.ParentId);
                else HwMechanics.Send(HwMechanics.SubScaredySaw, w => w.Write(db.ParentId));
            }
        }

        // a body hidden by a role (Shade, Faker clean-up ...) has its renderers switched off
        private static bool Visible(DeadBody db) {
            try {
                if (!db.gameObject.activeInHierarchy) return false;
                if (db.bodyRenderers == null || db.bodyRenderers.Length == 0) return true;
                foreach (var r in db.bodyRenderers) if (r != null && r.enabled && r.color.a > 0.2f) return true;
                return false;
            } catch { return true; }
        }

        // ---- host check ----
        private static void HostSaw(PlayerControl from, byte bodyId) {
            try {
                if (!active || carrier == null || from == null || from.PlayerId != carrier.PlayerId) { HwMechanics.Warn($"scaredy: saw from non-carrier {from?.PlayerId}"); return; }
                if (!HwMechanics.IsAlive(carrier) || HwMechanics.InMeeting() || screamedHost.Contains(bodyId)) return;
                if (Time.time - lastScreamHost < CooldownFor()) { HwMechanics.Log("scaredy: scream refused (cooldown)."); return; }
                var db = UnityEngine.Object.FindObjectsOfType<DeadBody>().FirstOrDefault(b => b != null && b.ParentId == bodyId);
                if (db == null) { HwMechanics.Log($"scaredy: body {bodyId} not found on the host."); return; }
                float radius = 3f;
                try { radius = ShipStatus.Instance.CalculateLightRadius(carrier.Data); } catch { }
                float dist = (db.TruePosition - carrier.GetTruePosition()).magnitude;
                if (dist > radius * 1.3f + 0.75f) { HwMechanics.Log($"scaredy: body {bodyId} too far ({dist:F1} > {radius:F1})."); return; }
                screamedHost.Add(bodyId);
                lastScreamHost = Time.time;
                var room = HwMechanics.RoomAt(carrier.GetTruePosition());
                byte rid = room != null ? (byte)room.RoomId : byte.MaxValue;
                byte cid = carrier.PlayerId;
                HwMechanics.Send(HwMechanics.SubScaredyScream, w => { w.Write(cid); w.Write(bodyId); w.Write(rid); });
                ApplyScream(cid, bodyId, rid);
            } catch (Exception e) { HwMechanics.Warn($"scaredy host check failed: {e.Message}"); }
        }

        // ---- the scream on every client ----
        private sealed class Mark { public PlayerControl P; public float Start, Until; public SpriteRenderer Sr; }
        private static readonly List<Mark> marks = new();

        private static void ApplyScream(byte who, byte bodyId, byte room) {
            var p = Helpers.playerById(who);
            if (p == null) return;
            DiagScreams++;
            float secs = MarkFor();
            foreach (var m in marks.Where(m => m.P == p).ToList()) { Destroy(m); marks.Remove(m); }
            var go = new GameObject("ScaredyMark") { layer = 11 };
            UnityEngine.Object.DontDestroyOnLoad(go);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = ExclaimSprite();
            marks.Add(new Mark { P = p, Start = Time.time, Until = Time.time + secs, Sr = sr });
            string name = HwMechanics.RoomName(room);
            bool de = HwMechanics.De();
            string text = name == null
                ? (de ? "Jemand kreischt ganz in der Nähe!" : "Someone screams nearby!")
                : (de ? $"Jemand kreischt in {name}!" : $"Someone screams in {name}!");
            LastText = text;
            ShowBanner(text);
            PlayShriek(p);
            TickMarks();
            HwMechanics.Log($"scream: carrier {who}, body {bodyId}, room {room} -> \"{text}\"");
        }

        private static void Destroy(Mark m) { try { if (m.Sr != null) UnityEngine.Object.Destroy(m.Sr.gameObject); } catch { } }

        private static void TickMarks() {
            if (marks.Count == 0) return;
            for (int i = marks.Count - 1; i >= 0; i--) {
                var m = marks[i];
                if (m.P == null || m.Sr == null || Time.time >= m.Until || HwMechanics.InMeeting()) { Destroy(m); marks.RemoveAt(i); continue; }
                float t = Time.time - m.Start, left = m.Until - Time.time;
                // pop with an overshoot, then a nervous wobble
                float pop = t < 0.25f ? Mathf.Lerp(0.2f, 1.25f, t / 0.25f) : t < 0.4f ? Mathf.Lerp(1.25f, 1f, (t - 0.25f) / 0.15f) : 1f;
                float wob = Mathf.Sin(t * 22f) * 6f * Mathf.Clamp01(1.2f - t * 0.4f);
                var pos = m.P.transform.position;
                m.Sr.transform.position = new Vector3(pos.x, pos.y + 0.95f + 0.04f * Mathf.Sin(t * 9f), pos.z - 0.02f);
                m.Sr.transform.localScale = Vector3.one * pop;
                m.Sr.transform.localRotation = Quaternion.Euler(0f, 0f, wob);
                m.Sr.color = new Color(1f, 1f, 1f, Mathf.Clamp01(left / 0.4f));
                // invisible in a vent, like the player
                try { m.Sr.enabled = !m.P.inVent; } catch { }
            }
        }

        // ---- the banner for everybody (icon + line, top of the screen) ----
        private static GameObject bannerRoot;
        private static TextMeshPro bannerText;
        private static SpriteRenderer bannerIcon;
        private static float bannerAt = -100f;
        private const float BannerLife = 4f;

        private static void ShowBanner(string text) {
            try {
                var hud = HudManager.InstanceExists ? HudManager.Instance : null;
                if (hud == null) return;
                if (bannerRoot == null) {
                    bannerRoot = new GameObject("ScaredyBanner") { layer = 5 };
                    bannerRoot.transform.SetParent(hud.transform, false);
                    var ig = new GameObject("icon") { layer = 5 };
                    ig.transform.SetParent(bannerRoot.transform, false);
                    bannerIcon = ig.AddComponent<SpriteRenderer>();
                    bannerIcon.sprite = IconSprite();
                    bannerIcon.sortingOrder = 305;
                    bannerText = TreatFx.NewText("ScaredyBannerText");
                    if (bannerText != null) {
                        bannerText.transform.SetParent(bannerRoot.transform, false);
                        bannerText.alignment = TextAlignmentOptions.Left;
                        bannerText.rectTransform.pivot = new Vector2(0f, 0.5f);
                        bannerText.rectTransform.sizeDelta = new Vector2(12f, 1f);
                        bannerText.sortingOrder = 305;
                    }
                }
                if (bannerText != null) bannerText.text = $"<color=#FFD040>{text}</color>";
                bannerRoot.SetActive(true);
                bannerAt = Time.time;
                TickBanner();
            } catch (Exception e) { HwMechanics.Warn($"scaredy banner failed: {e.Message}"); }
        }

        private static void TickBanner() {
            if (bannerRoot == null || !bannerRoot.activeSelf) return;
            float t = Time.time - bannerAt;
            var hud = HudManager.InstanceExists ? HudManager.Instance : null;
            var cam = hud != null ? hud.UICamera : null;
            if (t > BannerLife || cam == null || MeetingHud.Instance != null) { bannerRoot.SetActive(false); return; }
            float a = Mathf.Clamp01(t / 0.15f) * (1f - Mathf.Clamp01((t - (BannerLife - 0.6f)) / 0.6f));
            float w = bannerText != null ? Mathf.Min(bannerText.preferredWidth * 0.6f, 7f) : 3f;
            var at = cam.ViewportToWorldPoint(new Vector3(0.5f, 0.72f, 10f));
            float shake = t < 0.5f ? Mathf.Sin(t * 60f) * 0.04f * (1f - t / 0.5f) : 0f;
            float x0 = at.x - (w + 0.75f) * 0.5f + shake;
            bannerIcon.transform.position = new Vector3(x0 + 0.3f, at.y, -62f);
            bannerIcon.transform.localScale = Vector3.one * 0.6f;
            bannerIcon.color = new Color(1f, 1f, 1f, a);
            if (bannerText != null) {
                bannerText.transform.position = new Vector3(x0 + 0.75f, at.y, -62f);
                bannerText.transform.localScale = Vector3.one * 0.6f;
                bannerText.alpha = a;
            }
        }

        // ---- sound: a short startled shriek (synthesised, no asset) ----
        private static AudioClip shriek;
        private static void PlayShriek(PlayerControl from) {
            try {
                if (!Constants.ShouldPlaySfx() || SoundManager.Instance == null) return;
                if (shriek == null) {
                    const int rate = 44100;
                    float len = 0.75f;
                    int n = (int)(rate * len);
                    var data = new float[n];
                    var noise = new System.Random(11);
                    double ph = 0, ph2 = 0;
                    float lp = 0f;
                    for (int i = 0; i < n; i++) {
                        float t = (float)i / rate, u = t / len;
                        // a quick jump up, a shaky hold, a falling tail
                        float f = (u < 0.12f ? Mathf.Lerp(900f, 1750f, u / 0.12f) : Mathf.Lerp(1750f, 1150f, (u - 0.12f) / 0.88f))
                                  * (1f + 0.05f * Mathf.Sin(2f * Mathf.PI * 13f * t));
                        ph += 2 * Math.PI * f / rate;
                        ph2 += 2 * Math.PI * f * 1.5 / rate;
                        float env = Mathf.Clamp01(t / 0.02f) * Mathf.Clamp01((len - t) / 0.3f);
                        lp += ((float)noise.NextDouble() * 2f - 1f - lp) * 0.25f;
                        data[i] = env * (0.45f * (float)Math.Sin(ph) + 0.15f * (float)Math.Sin(ph2) + 0.2f * lp);
                    }
                    shriek = AudioClip.Create("scaredy_shriek", n, 1, rate, false);
                    shriek.SetData(data, 0);
                    shriek.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                }
                float vol = 0.8f;
                try {
                    var lp = PlayerControl.LocalPlayer;
                    float d = lp != null && from != null ? (lp.GetTruePosition() - from.GetTruePosition()).magnitude : 0f;
                    vol = Mathf.Lerp(0.85f, 0.3f, Mathf.Clamp01(d / 12f));
                } catch { }
                SoundManager.Instance.PlaySound(shriek, false, vol);
            } catch (Exception e) { HwMechanics.Warn($"scaredy shriek failed: {e.Message}"); }
        }

        // ---- pictures (placeholders drawn at runtime) ----
        internal static Sprite ExclaimSprite() => HwArt.Get(Folder, "scaredy_exclaim.png", 0.6f, new Vector2(0.5f, 0.1f), DrawExclaim);
        internal static Sprite IconSprite() => HwArt.Get(Folder, "scaredy_icon.png", 1f, new Vector2(0.5f, 0.5f), DrawIcon);

        internal static TreatFx.Canvas DrawExclaim() {
            var cv = new TreatFx.Canvas(128, 128);
            var ink = HwArt.C(0.18f, 0.10f, 0.05f);
            // spiky burst
            for (int i = 0; i < 12; i++) {
                float a0 = i * Mathf.PI * 2f / 12f, a1 = a0 + Mathf.PI / 12f, a2 = a0 + Mathf.PI * 2f / 12f;
                cv.Tri(64f, 70f, 64f + Mathf.Cos(a0) * 62f, 70f + Mathf.Sin(a0) * 56f, 64f + Mathf.Cos(a1) * 40f, 70f + Mathf.Sin(a1) * 36f, ink);
                cv.Tri(64f, 70f, 64f + Mathf.Cos(a1) * 40f, 70f + Mathf.Sin(a1) * 36f, 64f + Mathf.Cos(a2) * 62f, 70f + Mathf.Sin(a2) * 56f, ink);
            }
            for (int i = 0; i < 12; i++) {
                float a0 = i * Mathf.PI * 2f / 12f, a1 = a0 + Mathf.PI / 12f, a2 = a0 + Mathf.PI * 2f / 12f;
                var y = HwArt.C(1f, 0.85f, 0.2f);
                cv.Tri(64f, 70f, 64f + Mathf.Cos(a0) * 55f, 70f + Mathf.Sin(a0) * 49f, 64f + Mathf.Cos(a1) * 34f, 70f + Mathf.Sin(a1) * 30f, y);
                cv.Tri(64f, 70f, 64f + Mathf.Cos(a1) * 34f, 70f + Mathf.Sin(a1) * 30f, 64f + Mathf.Cos(a2) * 55f, 70f + Mathf.Sin(a2) * 49f, y);
            }
            cv.Disc(64f, 70f, 34f, HwArt.C(1f, 0.92f, 0.45f));
            // the mark
            var red = HwArt.C(0.85f, 0.12f, 0.08f);
            cv.Tri(52f, 100f, 76f, 100f, 64f, 58f, red);
            cv.Disc(64f, 100f, 12f, red);
            cv.Disc(64f, 45f, 7.5f, red);
            return cv;
        }

        internal static TreatFx.Canvas DrawIcon() {
            var cv = new TreatFx.Canvas(128, 128);
            cv.Disc(64f, 64f, 60f, HwArt.C(0.16f, 0.10f, 0.06f));
            cv.Disc(64f, 64f, 55f, HwArt.C(1f, 0.82f, 0.25f));
            // a startled cat face: ears, wide eyes, open mouth
            var dark = HwArt.C(0.16f, 0.10f, 0.06f);
            cv.Tri(26f, 70f, 40f, 112f, 56f, 84f, dark);
            cv.Tri(102f, 70f, 88f, 112f, 72f, 84f, dark);
            cv.Disc(64f, 60f, 36f, dark);
            cv.Disc(50f, 66f, 10f, HwArt.C(1f, 1f, 1f));
            cv.Disc(78f, 66f, 10f, HwArt.C(1f, 1f, 1f));
            cv.Disc(50f, 66f, 3.5f, dark);
            cv.Disc(78f, 66f, 3.5f, dark);
            cv.Ellipse(64f, 42f, 7f, 9f, HwArt.C(0.85f, 0.2f, 0.25f));
            cv.Line(30f, 50f, 48f, 52f, 2f, HwArt.C(1f, 1f, 1f));
            cv.Line(98f, 50f, 80f, 52f, 2f, HwArt.C(1f, 1f, 1f));
            return cv;
        }

        // ---- reset ----
        internal static void OnMeeting() {
            foreach (var m in marks) Destroy(m);
            marks.Clear();
            if (bannerRoot != null) bannerRoot.SetActive(false);
        }

        internal static void Reset() {
            OnMeeting();
            carrier = null;
            active = false;
            seenLocal.Clear();
            screamedHost.Clear();
            lastScreamHost = -100f;
        }

        // ---- self test ----
        internal static void DiagMakeLocal() { if (PlayerControl.LocalPlayer != null) ApplySet(PlayerControl.LocalPlayer.PlayerId); }
    }
}
