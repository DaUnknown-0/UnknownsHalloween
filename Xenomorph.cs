// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
// Based on The Other Roles (https://github.com/TheOtherRolesAU/TheOtherRoles), GPL-3.0.

/*
 * The Xenomorph (Neutral, killer)
 *
 * A lone hunter that wins like the Jackal: alive, no Impostor and no other killing team left, and
 * at least as many Xenomorphs (one) as everybody else together. There is NO reinforcement (design
 * decision 2026-10-05: no egg, no sidekick) - he hunts alone from the first to the last minute.
 *
 * THE TRANSFORMATION is what he plays around. As a human he looks like any Crewmate and cannot
 * kill. One button turns him into the creature for a configured time: he may kill (own cooldown),
 * moves faster, sees like an Impostor, may use vents (option) - and everybody who sees him knows WHAT is coming, though not
 * WHO: the costume covers the player completely and the name tag is blanked for everyone but
 * himself and the dead (the Werewolf's rule and patch position). When the time is up, or a meeting
 * starts, he is human again and the button goes on cooldown.
 *
 * WHY THE GAME DOES NOT END UNDER HIM
 * TOR knows nothing about this role, so its end checks would hand the round to the crew the
 * moment the last Impostor dies ("no killers left") or to the Impostors at parity. A host-side
 * prefix on GameManager.RpcEndGame (Priority.First, the Pelican's guard) swallows exactly those
 * "nobody else can stop us" wins while a Xenomorph is alive: crew by vote/disconnect, Impostors
 * by kill/vote/disconnect and the Jackal team's win. TASK and SABOTAGE wins go through - the crew
 * can still out-task him, a meltdown still kills everybody.
 *
 * JACKAL EXCLUSION (option 1792, default on): with a Jackal in the round the Xenomorph is not
 * rolled, and the draft does not offer him once a Jackal has been picked. Two neutral killer
 * teams with the same win condition tend to stall each other; the option lets the host decide.
 * The other direction cannot be enforced from here in the DRAFT (a Jackal picked after the
 * Xenomorph stays) - TOR owns that pick.
 *
 * LOOK: TOR's own setLook pipeline with the full-body costume hat "Halloween Xenomorph"
 * (registered by HalloweenCostumes.cs). The hat id is only a string here: without that file the role
 * still works, the creature is then simply the camouflage-black body.
 *
 * OWN MOD (since 2026-10-05): the role lives in Unknown's Halloween, not in Unknown's Collection, and
 * Unknown's Collection does not mention it anywhere. It therefore registers ITSELF: Boot() runs from a
 * HarmonyPrepare during this plugin's PatchAll (Unknown's Collection has loaded by then) and
 *   - creates the options and the RPC handler (module byte 235),
 *   - adds the role to the neutral lists of UCPromotion and UCRoleDraft (reflection),
 *   - appends the draft entry, the guesser entry and the handshake gate through postfixes.
 * Not registered this way (they come with the release): the help-menu page, the option colour and
 * the Mixer's role table. Texts are English with a German variant in Tr() below.
 *
 * ARCHITECTURE mirrors Necromancer/Pelican: neutral tag over a plain Crewmate, host-authoritative
 * pick, RPC module 235 on UCRpc.CallId = 230, gated on "everyone has the mod".
 * Options 1785-1792, draft sentinel 228, win reason 35, banner 16. See ID-Registry.md.
 */

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using AmongUs.GameOptions;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using HarmonyLib;
using Hazel;
using TMPro;
using UnityEngine;
using TheOtherRoles;
using TheOtherRoles.Patches;
using TheOtherRoles.Utilities;
using UnknownsCollection;
using static TheOtherRoles.TheOtherRoles;
using Types = TheOtherRoles.CustomOption.CustomOptionType;

namespace UnknownsHalloween {
    public static class Xenomorph {
        // Acid green: no other UC or TOR neutral uses it, and it reads on the black costume.
        public static readonly Color Color = new Color(0.62f, 0.92f, 0.18f);

        // ---- Options (IDs 1785-1792) ----
        public static CustomOption SpawnRate;
        public static CustomOption SpawnMinPlayers;
        public static CustomOption FormDuration;
        public static CustomOption FormCooldown;
        public static CustomOption KillCooldown;
        public static CustomOption FormSpeed;        // selections, not a float option (TOR's float steps accumulate)
        public static CustomOption CanVent;
        public static CustomOption ExcludeJackal;

        private static readonly string[] SpeedLabels = { "1x", "1.1x", "1.2x", "1.3x", "1.4x", "1.5x" };

        // ---- Runtime state ----
        public static PlayerControl xenomorph;
        public static bool active;
        private static byte xenoPlayerId = byte.MaxValue;
        private static bool formActive;
        private static float formEnd;               // local Time.time
        private static bool lookApplied;
        private static float formStart;

        private const int XenomorphWinReason = 35;  // Stalker uses 34
        private const int TeamJackalWinReason = 11; // TOR's CustomGameOverReason.TeamJackalWin
        private const string CostumeHatId = "hat_Halloween_Xenomorph";

        private static byte winnerId = byte.MaxValue;   // survives resetVariables
        private static float nextWinTry, nextGuardLog, nextTick;
        private static bool sawOthersAlive;

        private const byte RpcId = 235;   // module byte on UCRpc.CallId (see ID-Registry.md)
        private const byte DraftId = 228;
        private const byte SubSet = 0;    // playerId (255 = clear), host
        private const byte SubForm = 1;   // on (bool), seconds (float) - the Xenomorph's own client

        private static readonly System.Random rnd = new System.Random();
        private static TheOtherRoles.Objects.CustomButton formButton, killButton;
        private static PlayerControl currentTarget;

        private static RoleInfo info;
        public static RoleInfo XenomorphInfo() => info ??= new RoleInfo(
            "Xenomorph", Color, "Transform, hunt alone and be the last one standing",
            "Hunt them all", RoleId.Crewmate)
        { isNeutral = true };

        public static bool IsLocalXenomorph() =>
            active && xenomorph != null && PlayerControl.LocalPlayer != null
            && xenomorph.PlayerId == PlayerControl.LocalPlayer.PlayerId;
        /// True while this player is the transformed creature (every client agrees: the form is synced).
        public static bool IsTransformed(byte playerId) => active && formActive && playerId == xenoPlayerId;

        public static void CreateOptions() {
            try {
                SpawnRate = CustomOption.Create(1785, Types.Neutral, "Xenomorph", CustomOptionHolder.rates, null, true);
                SpawnMinPlayers = CustomOption.Create(1786, Types.Neutral, "Xenomorph Minimum Players To Spawn", 7f, 4f, 15f, 1f, SpawnRate);
                FormDuration = CustomOption.Create(1787, Types.Neutral, "Transformation Duration", 20f, 5f, 60f, 2.5f, SpawnRate);
                FormCooldown = CustomOption.Create(1788, Types.Neutral, "Transformation Cooldown", 30f, 10f, 90f, 2.5f, SpawnRate);
                KillCooldown = CustomOption.Create(1789, Types.Neutral, "Xenomorph Kill Cooldown", 10f, 2.5f, 45f, 2.5f, SpawnRate);
                FormSpeed = CustomOption.Create(1790, Types.Neutral, "Xenomorph Speed While Transformed", SpeedLabels, SpawnRate);
                CanVent = CustomOption.Create(1791, Types.Neutral, "Xenomorph Can Use Vents While Transformed", true, SpawnRate);
                ExcludeJackal = CustomOption.Create(1792, Types.Neutral, "Jackal And Xenomorph Exclude Each Other", true, SpawnRate);
                HalloweenPlugin.Logger?.LogInfo("[Xenomorph] Options created.");
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"[Xenomorph] CreateOptions failed: {e}");
            }
        }

        // ---- self registration (see the header) ----
        private static bool booted;
        private static void Boot() {
            if (booted) return;
            booted = true;
            try {
                CreateOptions();
                UCRpc.Register(RpcId, HandleModuleRpc);
                const BindingFlags priv = BindingFlags.NonPublic | BindingFlags.Static;
                (typeof(UCPromotion).GetField("NeutralPickers", priv)?.GetValue(null) as HashSet<string>)?.Add("Xenomorph");
                (typeof(UCRoleDraft).GetField("NeutralEntries", priv)?.GetValue(null) as HashSet<string>)?.Add("Xenomorph");
                var h = new Harmony("daunknown.unknownshalloween.xenomorph");
                void Post(Type t, string method, string postfix) {
                    var m = AccessTools.Method(t, method);
                    if (m != null) h.Patch(m, postfix: new HarmonyMethod(typeof(Xenomorph), postfix));
                    else HalloweenPlugin.Logger?.LogWarning($"[Xenomorph] {t.Name}.{method} not found - that registration is skipped.");
                }
                Post(typeof(UCRoleDraft), "Entries", nameof(DraftEntriesPostfix));
                Post(typeof(UCGuesser), "AllInfos", nameof(GuesserInfosPostfix));
                Post(typeof(UCGuesser), "Sync", nameof(GuesserSyncPostfix));
                Post(typeof(TeslaVersionHandshake), "AnyUCRoleEnabled", nameof(HandshakePostfix));
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"[Xenomorph] self registration failed: {e}");
            }
        }

        private static object draftListDone;
        private static void DraftEntriesPostfix(object __result) {
            try {
                if (__result == null || ReferenceEquals(draftListDone, __result)) return;
                draftListDone = __result;
                var make = AccessTools.Method(typeof(UCRoleDraft), "Make");
                var entry = make.Invoke(null, new object[] {
                    DraftId, "Xenomorph", Color, "Transform, hunt alone and be the last one standing", false,
                    (Func<CustomOption>)(() => SpawnRate), (Func<CustomOption>)(() => SpawnMinPlayers),
                    (Action<byte>)MarkFromDraft, (Func<bool>)AllowedBesideJackal });
                ((System.Collections.IList)__result).Add(entry);
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"[Xenomorph] draft entry failed: {e}");
            }
        }

        private static void GuesserInfosPostfix(ref RoleInfo[] __result) {
            try { if (__result != null) __result = __result.Append(XenomorphInfo()).ToArray(); } catch { }
        }

        private static MethodInfo guesserSetEntry;
        private static void GuesserSyncPostfix(bool add) {
            try {
                guesserSetEntry ??= AccessTools.Method(typeof(UCGuesser), "SetEntry");
                bool want = add && SpawnRate != null && SpawnRate.getSelection() > 0 && TeslaVersionHandshake.EveryoneHasMod();
                guesserSetEntry?.Invoke(null, new object[] { XenomorphInfo(), want, RoleInfo.crewmate });
            } catch { }
        }

        private static void HandshakePostfix(ref bool __result) {
            try { if (SpawnRate != null && SpawnRate.getSelection() > 0) __result = true; } catch { }
        }

        /// The role is switched on in this lobby (drives the costume lock in HalloweenCostumes).
        public static bool RoleEnabled() { try { return SpawnRate != null && SpawnRate.getSelection() > 0; } catch { return false; } }

        private static string Tr(string key) {
            bool de = false;
            try { de = UCLocalization.ActiveCode == "german"; } catch { }
            switch (key) {
                case "transform": return de ? "VERWANDELN" : "TRANSFORM";
                case "kill": return "KILL";
                case "revert": return de ? "ZURÜCK" : "REVERT";
                default: return de ? "Nichts Menschliches ist übrig" : "Nothing human is left";
            }
        }

        // ---- helpers ----
        private static bool AmHost() => AmongUsClient.Instance != null && AmongUsClient.Instance.AmHost;
        private static bool IsAlive(PlayerControl p) => p != null && p.Data != null && !p.Data.IsDead && !p.Data.Disconnected;
        private static bool InMeeting() => MeetingHud.Instance != null || ExileController.Instance != null;
        private static int LobbyPlayerCount() =>
            PlayerControl.AllPlayerControls.ToArray().Count(p => p != null && p.Data != null && !p.Data.Disconnected);
        private static float SpeedFactor() => 1f + 0.1f * Mathf.Clamp(FormSpeed?.getSelection() ?? 2, 0, SpeedLabels.Length - 1);
        private static bool JackalInPlay() {
            try { return Jackal.jackal != null || Sidekick.sidekick != null; } catch { return false; }
        }
        /// Draft gate and random-pick gate: with the exclusion on, a Jackal in the round keeps him out.
        public static bool AllowedBesideJackal() => !(ExcludeJackal?.getBool() ?? true) || !JackalInPlay();

        // ---- RPC ----
        private static MessageWriter BeginRpc(byte subtype) {
            var w = UCRpc.Begin(RpcId);
            w.Write(subtype);
            return w;
        }

        public static void SendSetXenomorph(byte id) {
            try {
                var w = BeginRpc(SubSet);
                w.Write(id);
                AmongUsClient.Instance.FinishRpcImmediately(w);
                ApplySet(id);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Xenomorph] SendSet failed: {e}"); }
        }

        private static void SendForm(bool on, float seconds) {
            try {
                var w = BeginRpc(SubForm);
                w.Write(on);
                w.Write(seconds);
                AmongUsClient.Instance.FinishRpcImmediately(w);
                ApplyForm(on, seconds);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Xenomorph] SendForm failed: {e}"); }
        }

        private static void HandleModuleRpc(MessageReader reader) {
            try {
                switch (reader.ReadByte()) {
                    case SubSet: {
                        byte id = reader.ReadByte();
                        if (UCRpc.RequireHost("Xenomorph.Set")) ApplySet(id);
                        break;
                    }
                    case SubForm: {
                        bool on = reader.ReadBoolean();
                        float secs = reader.ReadSingle();
                        if (UCRpc.RequireOwnerOrHost(xenomorph, "Xenomorph.Form")) ApplyForm(on, secs);
                        break;
                    }
                }
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"[Xenomorph] HandleRpc failed: {e}");
            }
        }

        private static void ApplySet(byte id) {
            if (formActive) EndFormLocal();
            xenomorph = Helpers.playerById(id);
            active = xenomorph != null;
            xenoPlayerId = active ? id : byte.MaxValue;
            sawOthersAlive = false;
            if (!active) return;
            UCPromotion.Claim(id);
            // His tasks leave the game server-visibly (the crew task win is server-authoritative; a
            // neutral who never tasks must not hold it hostage - the Necromancer's lesson).
            // (Not in freeplay: an empty list reads as "all tasks done" there and opens the practice popup.)
            if (AmHost() && AmongUsClient.Instance.NetworkMode != NetworkModes.FreePlay) {
                try { xenomorph.Data.RpcSetTasks(new Il2CppStructArray<byte>(0)); }
                catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Xenomorph] task strip failed: {e}"); }
            }
            if (IsLocalXenomorph()) {
                if (formButton != null) { formButton.MaxTimer = 10f; formButton.Timer = 10f; }
                if (killButton != null) { killButton.MaxTimer = KillCooldown?.getFloat() ?? 10f; killButton.Timer = 0f; }
            }
            HalloweenPlugin.Logger?.LogInfo($"[Xenomorph] The Xenomorph is {xenomorph.Data?.PlayerName}.");
        }

        public static void MarkFromDraft(byte playerId) => ApplySet(playerId);

        private static void ApplyForm(bool on, float seconds) {
            if (!active || xenomorph == null) return;
            if (on) {
                if (InMeeting() || !IsAlive(xenomorph)) return;
                formActive = true;
                formStart = Time.time;
                formEnd = Time.time + Mathf.Clamp(seconds, 1f, 120f);
                lookApplied = false;
                HalloweenPlugin.Logger?.LogInfo("[Xenomorph] transformed.");
            } else {
                EndFormLocal();
            }
        }

        private static void EndFormLocal() {
            bool was = formActive;
            formActive = false;
            if (lookApplied && xenomorph != null) {
                try { if (!GlobalCamoActive()) xenomorph.setDefaultLook(); } catch { }
            }
            lookApplied = false;
            if (was && IsLocalXenomorph() && formButton != null) {
                formButton.MaxTimer = FormCooldown?.getFloat() ?? 30f;
                formButton.Timer = formButton.MaxTimer;
                formButton.isEffectActive = false;
                if (formButton.actionButton != null) formButton.actionButton.cooldownTimerText.color = Palette.EnabledColor;
            }
            currentTarget = null;
        }

        private static bool GlobalCamoActive() {
            try { return Camouflager.camouflageTimer > 0f || Helpers.MushroomSabotageActive(); }
            catch { return false; }
        }

        // ---- look: the costume, re-applied when anything resets it (Morphling/Camo ends, light changes) ----
        private static void TickLook() {
            if (!formActive || xenomorph == null) return;
            if (GlobalCamoActive()) return;
            try {
                var hp = xenomorph.cosmetics != null ? xenomorph.cosmetics.hat : null;
                bool wearing = hp != null && hp.Hat != null && hp.Hat.ProductId == CostumeHatId;
                if (lookApplied && wearing) return;
                xenomorph.setLook(xenomorph.Data.PlayerName, 6, CostumeHatId, "", "", "");
                lookApplied = true;
            } catch { lookApplied = true; }   // a broken probe must never turn into a per-frame setLook storm
        }

        // The creature is nameless for everyone but itself and the dead (the Werewolf's patch slot:
        // Priority.Low runs after TOR's own per-frame name pass).
        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        static class NameHidePatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix() {
                try {
                    if (!active || !formActive || xenomorph == null || xenomorph.cosmetics == null) return;
                    var me = PlayerControl.LocalPlayer;
                    if (me == null || me.Data == null || me.Data.IsDead || me.PlayerId == xenoPlayerId) return;
                    var tag = xenomorph.cosmetics.nameText;
                    if (tag != null && !string.IsNullOrEmpty(tag.text)) tag.text = "";
                } catch { }
            }
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
                    if (LobbyPlayerCount() < (SpawnMinPlayers?.getFloat() ?? 7f)) return;
                    if (!AllowedBesideJackal()) {
                        HalloweenPlugin.Logger?.LogInfo("[Xenomorph] a Jackal is in the round - not rolled (exclusion option).");
                        return;
                    }
                    if (rnd.Next(1, 101) > SpawnRate.getSelection() * 10) return;
                    var candidates = PlayerControl.AllPlayerControls.ToArray()
                        .Where(p => UCPromotion.IsPlainCrewmate(p) && !UCPromotion.IsLover(p)).ToList();
                    if (candidates.Count == 0) return;
                    SendSetXenomorph(candidates[rnd.Next(candidates.Count)].PlayerId);
                } catch (Exception e) {
                    HalloweenPlugin.Logger?.LogError($"[Xenomorph] IntroEnd pick failed: {e}");
                }
            }
        }

        // ---- buttons ----
        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Start))]
        static class HudStartPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix(HudManager __instance) {
                try {
                    var killSprite = __instance.KillButton != null && __instance.KillButton.graphic != null
                        ? __instance.KillButton.graphic.sprite : null;
                    Func<bool> mine = () => IsLocalXenomorph() && PlayerControl.LocalPlayer.Data != null && !PlayerControl.LocalPlayer.Data.IsDead;

                    formButton = new TheOtherRoles.Objects.CustomButton(
                        () => SendForm(true, FormDuration?.getFloat() ?? 20f),
                        mine,
                        () => PlayerControl.LocalPlayer.CanMove && !formActive,
                        () => {
                            if (formActive) SendForm(false, 0f);
                            if (formButton != null) { formButton.MaxTimer = FormCooldown?.getFloat() ?? 30f; formButton.Timer = formButton.MaxTimer; formButton.isEffectActive = false; }
                        },
                        // 256 px at 200 px per unit: a touch larger than the 128 px / 115 standard icons
                        // (the user liked the bigger read), but no longer twice their size.
                        HalloweenCostumes.LoadIcon("hw_xenomorph_icon.png", 200f) ?? killSprite,
                        // lowerRowCenter, not lowerRowRight: in creature form he may vent, and TOR puts
                        // the vent button of a non-Impostor venter on lowerRowRight (playtest 2026-10-05:
                        // the two overlapped).
                        TheOtherRoles.Objects.CustomButton.ButtonPositions.lowerRowCenter,
                        __instance, KeyCode.F, true, FormDuration?.getFloat() ?? 20f,
                        () => { if (formActive) SendForm(false, 0f); },
                        false, Tr("transform"));
                    formButton.MaxTimer = FormCooldown?.getFloat() ?? 30f;
                    formButton.Timer = 10f;
                    // Ending the form early: TOR ignores clicks while an effect runs, so the button gets
                    // a second listener (and the hotkey a check in the HUD tick) for exactly that case.
                    try {
                        var pb = formButton.actionButton.GetComponent<PassiveButton>();
                        if (pb != null) pb.OnClick.AddListener((Action)(() => TryEndEarly()));
                    } catch { }

                    killButton = new TheOtherRoles.Objects.CustomButton(
                        () => {
                            if (!IsLocalXenomorph() || !formActive || currentTarget == null) return;
                            if (Helpers.checkMurderAttemptAndKill(xenomorph, currentTarget) == MurderAttemptResult.SuppressKill) return;
                            killButton.Timer = killButton.MaxTimer;
                            currentTarget = null;
                        },
                        () => mine() && formActive,
                        () => currentTarget != null && PlayerControl.LocalPlayer.CanMove,
                        () => { if (killButton != null) killButton.Timer = killButton.MaxTimer; },
                        killSprite,
                        TheOtherRoles.Objects.CustomButton.ButtonPositions.upperRowRight,
                        __instance, KeyCode.Q, false, Tr("kill"));
                    killButton.MaxTimer = KillCooldown?.getFloat() ?? 10f;
                    killButton.Timer = 0f;
                } catch (Exception e) {
                    HalloweenPlugin.Logger?.LogError($"[Xenomorph] Button creation failed: {e}");
                }
            }
        }

        // Not within the first second (the click that started the form must not end it again).
        private static void TryEndEarly() {
            if (!IsLocalXenomorph() || !formActive || Time.time - formStart < 1f) return;
            SendForm(false, 0f);
        }

        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        static class HudUpdatePatch {
            [HarmonyPriority(Priority.Last)]
            public static void Postfix() {
                try {
                    if (!active) return;
                    // The form ends on its clock, in a meeting and with his death - on every client.
                    if (formActive && (Time.time >= formEnd || InMeeting() || !IsAlive(xenomorph))) EndFormLocal();
                    TickLook();

                    if (IsLocalXenomorph()) {
                        if (formActive && Input.GetKeyDown(KeyCode.F)) TryEndEarly();
                        if (formButton != null) formButton.buttonText = formActive ? Tr("revert") : Tr("transform");
                        if (formButton != null) formButton.EffectDuration = FormDuration?.getFloat() ?? 20f;
                        if (killButton != null) killButton.MaxTimer = KillCooldown?.getFloat() ?? 10f;
                        if (formActive && IsAlive(xenomorph) && !InMeeting()) {
                            currentTarget = PlayerControlFixedUpdatePatch.setTarget();
                            if (currentTarget != null) PlayerControlFixedUpdatePatch.setPlayerOutline(currentTarget, Color);
                        } else currentTarget = null;
                    }

                    if (Time.realtimeSinceStartup < nextTick) return;
                    nextTick = Time.realtimeSinceStartup + 0.5f;
                    if (AmHost()) TryWin();
                } catch (Exception e) {
                    HalloweenPlugin.Logger?.LogError($"[Xenomorph] HudUpdate failed: {e}");
                }
            }
        }

        // ---- speed: the owner's own client moves him (movement is client-authoritative) ----
        [HarmonyPatch(typeof(PlayerPhysics), nameof(PlayerPhysics.FixedUpdate))]
        static class SpeedPatch {
            public static void Postfix(PlayerPhysics __instance) {
                try {
                    if (!active || !formActive || __instance == null || !__instance.AmOwner || __instance.body == null) return;
                    if (__instance.myPlayer == null || __instance.myPlayer.PlayerId != xenoPlayerId) return;
                    __instance.body.velocity *= SpeedFactor();
                } catch { }
            }
        }

        // Impostor vision while transformed (not affected by a lights sabotage, like an Impostor).
        // Own postfix instead of a stage in UCVision: no tracked file may mention this role yet.
        // Priority.Low = after UCVision's pipeline, before ChanceMod's multiplier (Priority.Last).
        // Mathf.Max, never an assignment, and it stands down during the Werewolf's night, which
        // redefines everybody's sight on purpose.
        [HarmonyPatch(typeof(ShipStatus), nameof(ShipStatus.CalculateLightRadius))]
        static class VisionPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix(ref float __result, ShipStatus __instance, [HarmonyArgument(0)] NetworkedPlayerInfo p) {
                try {
                    if (!active || !formActive || p == null || __instance == null || p.PlayerId != xenoPlayerId || p.IsDead) return;
                    if (Werewolf.active && Werewolf.wolfForm) return;
                    __result = Mathf.Max(__result, __instance.MaxLightRadius * GameOptionsManager.Instance.currentNormalGameOptions.ImpostorLightMod);
                } catch { }
            }
        }

        [HarmonyPatch(typeof(Helpers), nameof(Helpers.roleCanUseVents))]
        static class VentPatch {
            public static void Postfix(PlayerControl player, ref bool __result) {
                try {
                    if (!active || player == null || player.PlayerId != xenoPlayerId) return;
                    if (formActive && (CanVent?.getBool() ?? true)) __result = true;
                } catch { }
            }
        }

        // ---- win: like the Jackal ----
        private static bool OtherKillerAlive() {
            foreach (var p in PlayerControl.AllPlayerControls.ToArray()) {
                if (!IsAlive(p) || p.PlayerId == xenoPlayerId) continue;
                if (p.Data.Role != null && p.Data.Role.IsImpostor) return true;
                try {
                    if (Jackal.jackal != null && Jackal.jackal.PlayerId == p.PlayerId) return true;
                    if (Sidekick.sidekick != null && Sidekick.sidekick.PlayerId == p.PlayerId) return true;
                } catch { }
                if (Pelican.active && Pelican.pelican != null && Pelican.pelican.PlayerId == p.PlayerId) return true;
            }
            return false;
        }

        private static void TryWin() {
            if (!IsAlive(xenomorph) || InMeeting()) return;
            if (AmongUsClient.Instance == null || !AmongUsClient.Instance.IsGameStarted) return;
            int others = PlayerControl.AllPlayerControls.ToArray().Count(p => IsAlive(p) && p.PlayerId != xenoPlayerId);
            // Armed as soon as anybody else was seen alive (a round that STARTS with him alone must not
            // end at once). The first version waited for two others: a test with a single opponent
            // never armed it, and he stood alone on the ship without winning (playtest 2026-10-05).
            if (others >= 1) sawOthersAlive = true;
            if (others >= 2) return;
            if (!sawOthersAlive || OtherKillerAlive()) return;
            if (Time.time < nextWinTry) return;
            nextWinTry = Time.time + 2f;
            HalloweenPlugin.Logger?.LogInfo("[Xenomorph] nobody left to stop it - ending the game.");
            try { GameManager.Instance.RpcEndGame((GameOverReason)XenomorphWinReason, false); }
            catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Xenomorph] RpcEndGame failed: {e}"); }
        }

        // While he lives, nobody wins on "there is no other killer left" (see the header).
        [HarmonyPatch(typeof(GameManager), nameof(GameManager.RpcEndGame))]
        static class EndGameGuardPatch {
            [HarmonyPriority(Priority.First)]
            public static bool Prefix(ref GameOverReason endReason) {
                try {
                    if (!AmHost() || !active || !IsAlive(xenomorph)) return true;
                    int r = (int)endReason;
                    if (r == XenomorphWinReason) return true;
                    // Nobody else alive: there is nothing left to protect, and an end forced by the host
                    // (bypass / debug tools) has to go through.
                    if (!PlayerControl.AllPlayerControls.ToArray().Any(p => IsAlive(p) && p.PlayerId != xenoPlayerId)) return true;
                    bool block = endReason == GameOverReason.HumansByVote || endReason == GameOverReason.HumansDisconnect
                              || endReason == GameOverReason.ImpostorByKill || endReason == GameOverReason.ImpostorByVote
                              || endReason == GameOverReason.ImpostorDisconnect || r == TeamJackalWinReason;
                    if (!block) return true;
                    if (Time.time >= nextGuardLog) {
                        nextGuardLog = Time.time + 5f;
                        HalloweenPlugin.Logger?.LogInfo($"[Xenomorph] Suppressed end reason {r} - a living Xenomorph is still on the ship.");
                    }
                    return false;
                } catch (Exception e) {
                    HalloweenPlugin.Logger?.LogError($"[Xenomorph] end-game guard failed: {e}");
                    return true;
                }
            }
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameEnd))]
        static class OnGameEndPatch {
            [HarmonyPriority(Priority.Last)]
            public static void Prefix() {
                winnerId = (active && xenoPlayerId != byte.MaxValue) ? xenoPlayerId : byte.MaxValue;
            }

            [HarmonyPriority(Priority.Last)]
            public static void Postfix() {
                try {
                    if (winnerId == byte.MaxValue) return;
                    var xeno = Helpers.playerById(winnerId);
                    if (xeno == null || xeno.Data == null) return;
                    var winners = EndGameResult.CachedWinners;
                    if ((int)TheOtherRoles.Patches.OnGameEndPatch.gameOverReason == XenomorphWinReason) {
                        winners.Clear();
                        winners.Add(new CachedPlayerData(xeno.Data));
                        SetWinCondition(16);   // Necromancer 14, Stalker 15
                        HalloweenPlugin.Logger?.LogInfo("[Xenomorph] The Xenomorph wins alone!");
                        return;
                    }
                    // Any other end: he is a vanilla Crewmate and would stand on the crew's podium.
                    if (winners == null) return;
                    foreach (var w in winners.ToArray().Where(w => UCWinners.IsSameWinner(w, xeno.Data)).ToList())
                        winners.Remove(w);
                } catch (Exception e) {
                    HalloweenPlugin.Logger?.LogError($"[Xenomorph] OnGameEnd failed: {e}");
                }
            }
        }

        private static FieldInfo winConditionField;
        private static void SetWinCondition(int value) {
            try {
                var asm = typeof(CustomOption).Assembly;
                winConditionField ??= asm.GetType("TheOtherRoles.Patches.AdditionalTempData")?.GetField("winCondition", BindingFlags.Public | BindingFlags.Static);
                var wcEnum = asm.GetType("TheOtherRoles.Patches.WinCondition");
                if (winConditionField != null && wcEnum != null) winConditionField.SetValue(null, Enum.ToObject(wcEnum, value));
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"[Xenomorph] SetWinCondition failed: {e}");
            }
        }

        [HarmonyPatch(typeof(EndGameManager), nameof(EndGameManager.SetEverythingUp))]
        static class EndGameFxPatch {
            [HarmonyPriority(Priority.Last)]
            public static void Postfix(EndGameManager __instance) {
                try {
                    if ((int)TheOtherRoles.Patches.OnGameEndPatch.gameOverReason != XenomorphWinReason) return;
                    if (__instance.WinText == null) return;
                    GameObject bonus = UnityEngine.Object.Instantiate(__instance.WinText.gameObject);
                    bonus.transform.position = new Vector3(__instance.WinText.transform.position.x,
                        __instance.WinText.transform.position.y - 0.5f, __instance.WinText.transform.position.z);
                    bonus.transform.localScale = new Vector3(0.7f, 0.7f, 1f);
                    var text = bonus.GetComponent<TMP_Text>();
                    text.text = Tr("banner");
                    text.color = Color;
                } catch (Exception e) {
                    HalloweenPlugin.Logger?.LogError($"[Xenomorph] end-screen FX failed: {e}");
                }
            }
        }

        // His tasks never count (backstop for the frames before the host's server-visible strip lands).
        private static MethodInfo taskSubtract;

        [HarmonyPatch(typeof(GameData), nameof(GameData.RecomputeTaskCounts))]
        static class TaskPatch {
            public static void Postfix(GameData __instance) {
                try {
                    if (!active || xenomorph == null || xenomorph.Data == null) return;
                    // UCTaskCount is internal to Unknown's Collection, hence the reflection.
                    taskSubtract ??= AccessTools.Method(typeof(UCPromotion).Assembly.GetType("UnknownsCollection.UCTaskCount"), "Subtract");
                    taskSubtract?.Invoke(null, new object[] { __instance, xenomorph.Data });
                } catch { }
            }
        }

        [HarmonyPatch(typeof(RoleInfo), nameof(RoleInfo.getRoleInfoForPlayer))]
        static class RoleInfoPatch {
            public static void Postfix(PlayerControl p, ref List<RoleInfo> __result) {
                try {
                    if (!active || xenomorph == null || p == null || p != xenomorph || __result == null) return;
                    bool replaced = false;
                    for (int i = 0; i < __result.Count; i++) {
                        if (__result[i] != null && __result[i].roleId == RoleId.Crewmate) { __result[i] = XenomorphInfo(); replaced = true; }
                    }
                    if (!replaced) __result.Insert(0, XenomorphInfo());
                } catch { }
            }
        }

        // ---- test hooks (called by the self test only; freeplay does not tick TOR's buttons) ----
        internal static void DiagForm(bool on) => SendForm(on, FormDuration?.getFloat() ?? 20f);
        internal static string DiagKillNearest() {
            try {
                if (!active || xenomorph == null) return "no xenomorph";
                PlayerControl best = null;
                float bestD = float.MaxValue;
                foreach (var p in PlayerControl.AllPlayerControls.ToArray()) {
                    if (!IsAlive(p) || p.PlayerId == xenoPlayerId) continue;
                    float d = Vector2.Distance(p.GetTruePosition(), xenomorph.GetTruePosition());
                    if (d < bestD) { bestD = d; best = p; }
                }
                if (best == null) return "no victim";
                var r = Helpers.checkMurderAttemptAndKill(xenomorph, best);
                return $"kill {best.Data?.PlayerName}: {r}, form {formActive}, look {lookApplied}";
            } catch (Exception e) { return "failed: " + e.Message; }
        }
        internal static string DiagState() =>
            $"active {active}, form {formActive}, look {lookApplied}, alive {IsAlive(xenomorph)}, hat {(xenomorph != null && xenomorph.cosmetics != null && xenomorph.cosmetics.hat != null && xenomorph.cosmetics.hat.Hat != null ? xenomorph.cosmetics.hat.Hat.ProductId : "?")}";

        // ---- resets (PlayerId-keyed state also clears on OnGameJoined: the lobby-leak rule) ----
        private static void FullReset() {
            if (formActive) EndFormLocal();
            xenomorph = null;
            active = false;
            xenoPlayerId = byte.MaxValue;
            formActive = false;
            lookApplied = false;
            currentTarget = null;
            sawOthersAlive = false;
            nextWinTry = 0f;
            // buttons deliberately NOT nulled (the resetVariables button-timing rule);
            // winnerId deliberately survives resetVariables (read after the reset at game end).
        }

        [HarmonyPatch(typeof(RPCProcedure), nameof(RPCProcedure.resetVariables))]
        static class ResetPatch {
            // Called by this plugin's PatchAll during Load(): the earliest point this file gets.
            static bool Prepare() { Boot(); return true; }
            public static void Postfix() {
                try { FullReset(); }
                catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Xenomorph] round reset failed: {e}"); }
            }
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined))]
        static class LobbyResetPatch {
            public static void Postfix() { FullReset(); winnerId = byte.MaxValue; }
        }
    }
}
