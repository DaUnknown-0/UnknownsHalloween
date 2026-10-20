// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
// Based on The Other Roles (https://github.com/TheOtherRolesAU/TheOtherRoles), GPL-3.0.

/*
 * The Banshee (Crewmate, 2026-10-17)
 *
 * Her scream is an omen for everybody: for a moment EVERY player - crew and impostors alike - sees where every
 * living player is, the Banshee herself included. A marker over each living player (through walls and the
 * shadow) and an arrow at the screen edge for those out of sight. The scream is a double-edged tool: it can
 * expose an impostor walking away from a body, but it also tells the impostors where the lonely crewmates are -
 * and where the Banshee stands. Limited screams per round, a cooldown between them.
 *
 * Registration like the Xenomorph (own mod, Unknown's Collection does not mention it): Boot() from a HarmonyPrepare
 * creates the options and the RPC handler and appends the draft entry, the guesser entry and the handshake gate
 * through postfixes. Crew roles need no extra list in UC (UCPromotion / UCRoleDraft treat everything that is
 * neither in their neutral lists nor an impostor entry as crew).
 *
 * Display: markers live on the UI layer (layer 5) and are drawn by the UI camera, above the shadow of the light
 * system; their position goes world -> main camera viewport -> UI camera world, so they stay on the players even if
 * the two cameras ever differ. Out-of-sight players get TOR's edge arrow (Objects.Arrow, as the Snitch uses).
 * The wail is synthesised at runtime (no audio asset): a falling, vibrating glide with breath noise.
 *
 * Options 1983-1986, RPC module 237 on UCRpc.CallId 230 (Sub 0 set - host, Sub 1 scream - the Banshee), draft
 * sentinel 237. See ID-Registry.md.
 */

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using HarmonyLib;
using Hazel;
using UnityEngine;
using TheOtherRoles;
using TheOtherRoles.Utilities;
using UnknownsCollection;
using Types = TheOtherRoles.CustomOption.CustomOptionType;

namespace UnknownsHalloween {
    public static class Banshee {
        // Pale wail blue: no other crew role of TOR/UC uses it, reads as "ghostly" next to the role colours.
        public static readonly Color Color = new Color(0.62f, 0.80f, 1.0f);

        // ---- Options (IDs 1983-1986) ----
        public static CustomOption SpawnRate;
        public static CustomOption Cooldown;
        public static CustomOption Screams;
        public static CustomOption RevealTime;      // selections (TOR's float steps accumulate)
        private static readonly string[] RevealLabels = { "1s", "1.5s", "2s", "2.5s", "3s", "4s" };
        private static readonly float[] RevealSeconds = { 1f, 1.5f, 2f, 2.5f, 3f, 4f };

        // ---- Runtime state ----
        public static PlayerControl banshee;
        public static bool active;
        private static byte bansheeId = byte.MaxValue;
        private static int screamsLeft;

        private const byte RpcId = 237;     // module byte on UCRpc.CallId (see ID-Registry.md)
        private const byte DraftId = 237;
        private const byte SubSet = 0;      // playerId (255 = clear), host
        private const byte SubScream = 1;   // seconds (float), the Banshee's own client

        private static readonly System.Random rnd = new System.Random();
        private static TheOtherRoles.Objects.CustomButton screamButton;

        private static RoleInfo info;
        public static RoleInfo BansheeInfo() => info ??= new RoleInfo(
            "Banshee", Color, "Scream to show everyone where everybody is",
            "Your scream reveals all living players - to everyone", RoleId.Crewmate);

        public static bool IsLocalBanshee() =>
            active && banshee != null && PlayerControl.LocalPlayer != null && banshee.PlayerId == PlayerControl.LocalPlayer.PlayerId;

        public static void CreateOptions() {
            try {
                SpawnRate = CustomOption.Create(1983, Types.Crewmate, "Banshee", CustomOptionHolder.rates, null, true);
                Cooldown = CustomOption.Create(1984, Types.Crewmate, "Banshee Scream Cooldown", 30f, 10f, 90f, 2.5f, SpawnRate);
                Screams = CustomOption.Create(1985, Types.Crewmate, "Banshee Number Of Screams", 2f, 1f, 10f, 1f, SpawnRate);
                RevealTime = CustomOption.Create(1986, Types.Crewmate, "Banshee Scream Reveals For", RevealLabels, SpawnRate);
                try { RevealTime.selection = 2; } catch { }          // 2 s
                HalloweenPlugin.Logger?.LogInfo("[Banshee] Options created.");
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"[Banshee] CreateOptions failed: {e}");
            }
        }

        private static float RevealFor() => RevealSeconds[Mathf.Clamp(RevealTime?.getSelection() ?? 2, 0, RevealSeconds.Length - 1)];

        // ---- self registration ----
        private static bool booted;
        private static void Boot() {
            if (booted) return;
            booted = true;
            try {
                CreateOptions();
                UCRpc.Register(RpcId, HandleModuleRpc);
                UCFx.RegisterTick(BansheeReveal.Tick);
                var h = new Harmony("daunknown.unknownshalloween.banshee");
                void Post(Type t, string method, string postfix) {
                    var m = AccessTools.Method(t, method);
                    if (m != null) h.Patch(m, postfix: new HarmonyMethod(typeof(Banshee), postfix));
                    else HalloweenPlugin.Logger?.LogWarning($"[Banshee] {t.Name}.{method} not found - that registration is skipped.");
                }
                Post(typeof(UCRoleDraft), "Entries", nameof(DraftEntriesPostfix));
                Post(typeof(UCGuesser), "AllInfos", nameof(GuesserInfosPostfix));
                Post(typeof(UCGuesser), "Sync", nameof(GuesserSyncPostfix));
                Post(typeof(TeslaVersionHandshake), "AnyUCRoleEnabled", nameof(HandshakePostfix));
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"[Banshee] self registration failed: {e}");
            }
        }

        private static object draftListDone;
        private static void DraftEntriesPostfix(object __result) {
            try {
                if (__result == null || ReferenceEquals(draftListDone, __result)) return;
                draftListDone = __result;
                var make = AccessTools.Method(typeof(UCRoleDraft), "Make");
                var entry = make.Invoke(null, new object[] {
                    DraftId, "Banshee", Color, "Scream to show everyone where everybody is", false,
                    (Func<CustomOption>)(() => SpawnRate), (Func<CustomOption>)(() => null),
                    (Action<byte>)MarkFromDraft, null });
                ((System.Collections.IList)__result).Add(entry);
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"[Banshee] draft entry failed: {e}");
            }
        }

        private static void GuesserInfosPostfix(ref RoleInfo[] __result) {
            try { if (__result != null) __result = __result.Append(BansheeInfo()).ToArray(); } catch { }
        }

        private static MethodInfo guesserSetEntry;
        private static void GuesserSyncPostfix(bool add) {
            try {
                guesserSetEntry ??= AccessTools.Method(typeof(UCGuesser), "SetEntry");
                bool want = add && SpawnRate != null && SpawnRate.getSelection() > 0 && TeslaVersionHandshake.EveryoneHasMod();
                guesserSetEntry?.Invoke(null, new object[] { BansheeInfo(), want, RoleInfo.crewmate });
            } catch { }
        }

        private static void HandshakePostfix(ref bool __result) {
            try { if (SpawnRate != null && SpawnRate.getSelection() > 0) __result = true; } catch { }
        }

        private static string Tr(string key) {
            bool de = false;
            try { de = UCLocalization.ActiveCode == "german"; } catch { }
            switch (key) {
                case "scream": return de ? "SCHREIEN" : "SCREAM";
                default: return key;
            }
        }

        // ---- helpers ----
        private static bool AmHost() => AmongUsClient.Instance != null && AmongUsClient.Instance.AmHost;
        private static bool IsAlive(PlayerControl p) => p != null && p.Data != null && !p.Data.IsDead && !p.Data.Disconnected;
        private static bool InMeeting() => MeetingHud.Instance != null || ExileController.Instance != null;

        // ---- RPC ----
        private static MessageWriter BeginRpc(byte subtype) {
            var w = UCRpc.Begin(RpcId);
            w.Write(subtype);
            return w;
        }

        public static void SendSetBanshee(byte id) {
            try {
                var w = BeginRpc(SubSet);
                w.Write(id);
                AmongUsClient.Instance.FinishRpcImmediately(w);
                ApplySet(id);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Banshee] SendSet failed: {e}"); }
        }

        private static void SendScream(float seconds) {
            try {
                var w = BeginRpc(SubScream);
                w.Write(seconds);
                AmongUsClient.Instance.FinishRpcImmediately(w);
                ApplyScream(seconds);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Banshee] SendScream failed: {e}"); }
        }

        private static void HandleModuleRpc(MessageReader reader) {
            try {
                switch (reader.ReadByte()) {
                    case SubSet: {
                        byte id = reader.ReadByte();
                        if (UCRpc.RequireHost("Banshee.Set")) ApplySet(id);
                        break;
                    }
                    case SubScream: {
                        float secs = reader.ReadSingle();
                        if (UCRpc.RequireOwnerOrHost(banshee, "Banshee.Scream")) ApplyScream(secs);
                        break;
                    }
                }
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"[Banshee] HandleRpc failed: {e}");
            }
        }

        private static void ApplySet(byte id) {
            banshee = id == byte.MaxValue ? null : Helpers.playerById(id);
            active = banshee != null;
            bansheeId = active ? id : byte.MaxValue;
            screamsLeft = Mathf.RoundToInt(Screams?.getFloat() ?? 2f);
            if (!active) return;
            UCPromotion.Claim(id);
            if (IsLocalBanshee() && screamButton != null) { screamButton.MaxTimer = Cooldown?.getFloat() ?? 30f; screamButton.Timer = 10f; }
            HalloweenPlugin.Logger?.LogInfo($"[Banshee] The Banshee is {banshee.Data?.PlayerName}.");
        }

        public static void MarkFromDraft(byte playerId) => ApplySet(playerId);

        private static void ApplyScream(float seconds) {
            if (!active || banshee == null || InMeeting() || !IsAlive(banshee)) return;
            if (IsLocalBanshee()) screamsLeft = Math.Max(0, screamsLeft - 1);
            BansheeReveal.Start(banshee, Mathf.Clamp(seconds, 0.5f, 6f));
            HalloweenPlugin.Logger?.LogInfo($"[Banshee] scream ({seconds:F1} s).");
        }

        // ---- pick (host, random path; the draft goes through MarkFromDraft) ----
        [HarmonyPatch(typeof(IntroCutscene), nameof(IntroCutscene.OnDestroy))]
        static class IntroEndPickPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix() {
                try {
                    if (!AmHost()) return;
                    if (UCRoleDraft.DraftWillRun()) return;
                    if (SpawnRate == null || SpawnRate.getSelection() <= 0) return;
                    if (!TeslaVersionHandshake.EveryoneHasMod()) return;
                    if (rnd.Next(1, 101) > SpawnRate.getSelection() * 10) return;
                    var candidates = PlayerControl.AllPlayerControls.ToArray()
                        .Where(p => UCPromotion.IsPlainCrewmate(p)).ToList();
                    if (candidates.Count == 0) return;
                    SendSetBanshee(candidates[rnd.Next(candidates.Count)].PlayerId);
                } catch (Exception e) {
                    HalloweenPlugin.Logger?.LogError($"[Banshee] IntroEnd pick failed: {e}");
                }
            }
        }

        // ---- button ----
        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Start))]
        static class HudStartPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix(HudManager __instance) {
                try {
                    screamButton = new TheOtherRoles.Objects.CustomButton(
                        () => {
                            if (!IsLocalBanshee() || screamsLeft <= 0) return;
                            SendScream(RevealFor());
                            screamButton.Timer = screamButton.MaxTimer;
                        },
                        () => IsLocalBanshee() && PlayerControl.LocalPlayer.Data != null && !PlayerControl.LocalPlayer.Data.IsDead,
                        () => PlayerControl.LocalPlayer.CanMove && screamsLeft > 0,
                        () => { if (screamButton != null) screamButton.Timer = screamButton.MaxTimer; },
                        HalloweenCostumes.LoadIcon("hw_banshee_icon.png", 200f),
                        TheOtherRoles.Objects.CustomButton.ButtonPositions.lowerRowRight,
                        __instance, KeyCode.F, false, Tr("scream"));
                    screamButton.MaxTimer = Cooldown?.getFloat() ?? 30f;
                    screamButton.Timer = 10f;
                } catch (Exception e) {
                    HalloweenPlugin.Logger?.LogError($"[Banshee] Button creation failed: {e}");
                }
            }
        }

        // Screams left on the button (like TOR's "uses" counters).
        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        static class UsesTextPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix() {
                try {
                    if (!IsLocalBanshee() || screamButton?.actionButton == null) return;
                    var t = screamButton.actionButton.buttonLabelText;
                    if (t == null) return;
                    string want = $"{Tr("scream")} ({screamsLeft})";
                    if (t.text != want) t.text = want;
                } catch { }
            }
        }

        // ---- reset ----
        private static void FullReset() {
            banshee = null;
            active = false;
            bansheeId = byte.MaxValue;
            screamsLeft = 0;
            BansheeReveal.Stop();
            // buttons deliberately NOT nulled (the resetVariables button-timing rule)
        }

        [HarmonyPatch(typeof(RPCProcedure), nameof(RPCProcedure.resetVariables))]
        static class ResetPatch {
            static bool Prepare() { Boot(); return true; }
            public static void Postfix() {
                try { FullReset(); }
                catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Banshee] round reset failed: {e}"); }
            }
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined))]
        static class LobbyResetPatch {
            public static void Postfix() => FullReset();
        }

        // ---- self test (UC_HALLOWEEN_DIAG=banshee): the local player becomes the Banshee and screams ----
        internal static void DiagMakeLocal() { if (PlayerControl.LocalPlayer != null) ApplySet(PlayerControl.LocalPlayer.PlayerId); }
        internal static void DiagScream() => ApplyScream(RevealFor());
    }

    /// <summary>The scream itself on every client: markers over all living players (UI layer, above the shadow),
    /// edge arrows for those out of sight, an expanding ring from the Banshee and the wail.</summary>
    internal static class BansheeReveal {
        private static float until, started;
        private static PlayerControl source;
        private static GameObject root;
        private static readonly Dictionary<byte, (SpriteRenderer dot, SpriteRenderer ring, TheOtherRoles.Objects.Arrow arrow)> marks = new();
        private static SpriteRenderer wave;
        private static Sprite discSprite, ringSprite;
        private static AudioClip wail;

        internal static void Start(PlayerControl from, float seconds) {
            Stop();
            source = from;
            started = Time.time;
            until = Time.time + seconds;
            PlayWail();
        }

        internal static void Stop() {
            until = 0f;
            source = null;
            foreach (var m in marks.Values) {
                try { if (m.arrow?.arrow != null) UnityEngine.Object.Destroy(m.arrow.arrow); } catch { }
            }
            marks.Clear();
            if (root != null) UnityEngine.Object.Destroy(root);
            root = null;
            wave = null;
        }

        private static Sprite Disc(bool ring) {
            if (ring ? ringSprite != null : discSprite != null) return ring ? ringSprite : discSprite;
            const int n = 128;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { hideFlags = HideFlags.HideAndDontSave };
            var px = new Color32[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++) {
                    float dx = (x + 0.5f) / n * 2f - 1f, dy = (y + 0.5f) / n * 2f - 1f, r = Mathf.Sqrt(dx * dx + dy * dy);
                    float a = ring ? Mathf.Clamp01(1f - Mathf.Abs(r - 0.88f) / 0.1f) : Mathf.Clamp01((1f - r) / 0.12f);
                    px[y * n + x] = new Color32(255, 255, 255, (byte)(a * 255));
                }
            tex.SetPixels32(px);
            tex.Apply(false, true);
            var s = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), n);     // 1 unit across
            s.hideFlags |= HideFlags.HideAndDontSave;
            if (ring) ringSprite = s; else discSprite = s;
            return s;
        }

        private static SpriteRenderer MakeSr(string name, Sprite sprite, int order) {
            var go = new GameObject(name) { layer = 5 };
            go.transform.SetParent(root.transform, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sortingOrder = order;
            return sr;
        }

        // World position -> the UI camera's world space (the markers live there, above the shadow).
        private static bool ToUi(Vector3 world, out Vector3 ui) {
            ui = default;
            var main = Camera.main;
            var hud = HudManager.InstanceExists ? HudManager.Instance : null;
            var uiCam = hud != null ? hud.UICamera : null;
            if (main == null || uiCam == null) return false;
            var vp = main.WorldToViewportPoint(world);
            ui = uiCam.ViewportToWorldPoint(new Vector3(vp.x, vp.y, 10f));
            ui.z = -50f;
            return vp.x > -0.05f && vp.x < 1.05f && vp.y > -0.05f && vp.y < 1.05f;
        }

        internal static void Tick() {
            if (until <= 0f) return;
            if (Time.time >= until || MeetingHud.Instance != null || !HudManager.InstanceExists) { Stop(); return; }
            try {
                if (root == null) {
                    root = new GameObject("BansheeReveal") { layer = 5 };
                    UnityEngine.Object.DontDestroyOnLoad(root);
                    wave = MakeSr("wave", Disc(true), 200);
                }
                float t = Time.time - started, left = until - Time.time;
                float fade = Mathf.Clamp01(left / 0.4f) * Mathf.Clamp01(t / 0.15f);
                float pulse = 1f + 0.12f * Mathf.Sin(t * 12f);
                // the shock wave from the Banshee: grows over the first 0.8 s, then is gone
                if (source != null && ToUi(source.GetTruePosition(), out var sp)) {
                    float k = Mathf.Clamp01(t / 0.8f);
                    wave.transform.position = sp;
                    wave.transform.localScale = Vector3.one * Mathf.Lerp(0.5f, 9f, k);
                    wave.color = new Color(Banshee.Color.r, Banshee.Color.g, Banshee.Color.b, (1f - k) * 0.8f);
                } else if (wave != null) wave.color = Color.clear;

                var alive = new HashSet<byte>();
                foreach (var p in PlayerControl.AllPlayerControls.ToArray()) {
                    if (p == null || p.Data == null || p.Data.IsDead || p.Data.Disconnected) continue;
                    alive.Add(p.PlayerId);
                    if (!marks.TryGetValue(p.PlayerId, out var m)) {
                        m = (MakeSr("dot" + p.PlayerId, Disc(false), 202), MakeSr("ring" + p.PlayerId, Disc(true), 201),
                             p == PlayerControl.LocalPlayer ? null : new TheOtherRoles.Objects.Arrow(Color.white));
                        marks[p.PlayerId] = m;
                    }
                    // the colour the player SHOWS right now (camouflage, masquerade, morph stay intact)
                    Color body = Color.white;
                    try {
                        int cid = p.CurrentOutfit != null ? p.CurrentOutfit.ColorId : p.Data.DefaultOutfit.ColorId;
                        body = Palette.PlayerColors[cid];
                    } catch { }
                    bool isBanshee = p == source;
                    var world = (Vector3)p.GetTruePosition() + new Vector3(0f, 0.35f, 0f);
                    bool onScreen = ToUi(world, out var uiPos);
                    m.dot.transform.position = uiPos;
                    // small and see-through: the ring is the marker, the dot only carries the colour (a full dot
                    // covered body and visor of visible players, self test 17.10.)
                    m.dot.transform.localScale = Vector3.one * 0.2f;
                    m.dot.color = new Color(body.r, body.g, body.b, 0.7f * fade);
                    m.ring.transform.position = uiPos + new Vector3(0f, 0f, 0.01f);
                    m.ring.transform.localScale = Vector3.one * (isBanshee ? 0.75f * pulse : 0.5f * pulse);
                    m.ring.color = isBanshee ? new Color(Banshee.Color.r, Banshee.Color.g, Banshee.Color.b, fade) : new Color(1f, 1f, 1f, 0.85f * fade);
                    m.dot.enabled = m.ring.enabled = onScreen;
                    if (m.arrow != null) {
                        m.arrow.Update(world, isBanshee ? Banshee.Color : body);
                        m.arrow.arrow.SetActive(!onScreen);
                    }
                }
                foreach (var id in marks.Keys.Where(k => !alive.Contains(k)).ToList()) {
                    var m = marks[id];
                    if (m.dot != null) m.dot.enabled = false;
                    if (m.ring != null) m.ring.enabled = false;
                    if (m.arrow?.arrow != null) m.arrow.arrow.SetActive(false);
                }
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogWarning($"[Banshee] reveal failed: {e.Message}");
                Stop();
            }
        }

        // ---- the wail: synthesised once (falling glide 900 -> 420 Hz with vibrato, an octave overtone, breath) ----
        private static void PlayWail() {
            try {
                if (!Constants.ShouldPlaySfx() || SoundManager.Instance == null) return;
                if (wail == null) {
                    const int rate = 44100;
                    float len = 1.6f;
                    int n = (int)(rate * len);
                    var data = new float[n];
                    var noise = new System.Random(5);
                    double phase = 0, phase2 = 0;
                    float lp = 0f;
                    for (int i = 0; i < n; i++) {
                        float t = (float)i / rate, u = t / len;
                        float f = Mathf.Lerp(900f, 420f, Mathf.SmoothStep(0f, 1f, u)) * (1f + 0.035f * Mathf.Sin(2f * Mathf.PI * 6.5f * t));
                        phase += 2 * Math.PI * f / rate;
                        phase2 += 2 * Math.PI * f * 2.01 / rate;
                        float env = Mathf.Clamp01(t / 0.12f) * Mathf.Clamp01((len - t) / 0.5f);
                        lp += ((float)noise.NextDouble() * 2f - 1f - lp) * 0.08f;          // soft breath noise
                        data[i] = env * (0.55f * (float)Math.Sin(phase) + 0.18f * (float)Math.Sin(phase2) + 0.22f * lp);
                    }
                    wail = AudioClip.Create("banshee_wail", n, 1, rate, false);
                    wail.SetData(data, 0);
                    wail.hideFlags |= HideFlags.HideAndDontSave;
                }
                SoundManager.Instance.PlaySound(wail, false, 0.9f);
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogWarning($"[Banshee] wail failed: {e.Message}");
            }
        }
    }
}
