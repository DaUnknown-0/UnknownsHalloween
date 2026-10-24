// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
// Based on The Other Roles (https://github.com/TheOtherRolesAU/TheOtherRoles), GPL-3.0.

/*
 * Trick or Treat, second batch (2026-10-21, the "Hexenkessel" picks). Lives next to TrickOrTreat.cs:
 *
 *  - Candy bag (menu switch): the Use button TAKEs a candy into the bag (two at most) instead of eating it. A
 *    button of its own (BAG) opens a card with everything in the bag; a click there eats that candy. The Use button
 *    never eats from the bag (it would fight consoles and the meeting button for the target). The effect is drawn
 *    when it is eaten, from the same mapping as on the floor. Cabinet candies go into the bag as well.
 *  - Trick Candy (menu switch): every impostor lays one candy between two meetings (own button). It looks like any
 *    drawn kind and always hinders, whoever eats it. Only the host knows which candies are tricks.
 *  - Sugar Shock (menu switch): the third candy one player eats between two meetings brings a Sugar Crash on top.
 *  - The new effects that need more than a number: Double Dip (TOR's vote tally), Candy Corn Compass, Peek-a-Pop,
 *    Sticky Toffee, Vent Mint, Fizz Pop (TOR's footprints), Homing Humbug (own button), Tattletale Taffy, Brain Freeze,
 *    Wrapper Trail, Ghostly Gum. Speed, Reverse Gummy and Sugar Crash sit in TrickOrTreat.SpeedMult and its patch.
 *
 * Network (module 238, after Sub 8 of TrickOrTreat.cs):
 *   Sub 9  take req     any  -> host  [phase][candy]
 *   Sub 10 taken        host -> all   [phase][candy][player][kind]
 *   Sub 11 bag eat req  any  -> host  [slot]            (then Sub 2 with candy 254)
 *   Sub 12 trick req    imp  -> host  (empty: the host lays it at the impostor's feet)
 *   Sub 13 trick placed host -> all   [phase][candy][player][x short*100][y short*100][kind]
 */

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using Hazel;
using UnityEngine;
using TheOtherRoles;
using TheOtherRoles.Objects;
using UnknownsCollection;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using static TheOtherRoles.TheOtherRoles;

namespace UnknownsHalloween {
    internal static class TreatPlus {
        private const string LogPrefix = TrickOrTreat.LogPrefix;
        private static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {s}");

        internal const byte SubTakeReq = 9, SubTaken = 10, SubBagEatReq = 11, SubTrickReq = 12, SubTrickPlaced = 13;
        internal const byte IdxBag = 254, IdxSugarShock = 253;
        internal const int BagSize = 2;
        private static readonly System.Random rnd = new System.Random();

        internal static bool Any => bags.Count > 0 || stuckUntil.Count > 0 || wrappers.Count > 0 || links.Count > 0 || trickUsed.Count > 0;

        // ================================================================ RPC
        internal static void HandleRpc(byte sub, MessageReader r) {
            switch (sub) {
                case SubTakeReq: {
                    byte ph = r.ReadByte(), idx = r.ReadByte();
                    if (TrickOrTreat.AmHost()) HostTake(UCRpc.Sender, ph, idx);
                    break;
                }
                case SubTaken: {
                    byte ph = r.ReadByte(), idx = r.ReadByte(), pid = r.ReadByte(), kind = r.ReadByte();
                    if (UCRpc.RequireHost("Treats.Taken")) ApplyTaken(ph, idx, pid, kind);
                    break;
                }
                case SubBagEatReq: {
                    byte slot = r.ReadByte();
                    if (TrickOrTreat.AmHost()) HostBagEat(UCRpc.Sender, slot);
                    break;
                }
                case SubTrickReq:
                    if (TrickOrTreat.AmHost()) HostTrick(UCRpc.Sender);
                    break;
                case SubTrickPlaced: {
                    byte ph = r.ReadByte(), idx = r.ReadByte(), pid = r.ReadByte();
                    var pos = new Vector2(r.ReadInt16() / 100f, r.ReadInt16() / 100f);
                    byte kind = r.ReadByte();
                    if (UCRpc.RequireHost("Treats.Trick")) ApplyTrickPlaced(ph, idx, pid, pos, kind);
                    break;
                }
            }
        }

        // ================================================================ candy bag
        private static readonly Dictionary<byte, List<byte>> bags = new();          // kinds, the same on every client
        private static readonly Dictionary<byte, List<bool>> hostBagTricks = new(); // host: which bag slot is a Trick Candy
        private static float bagEatAt = -10f;

        internal static bool BagOn() => TreatSettings.Current.Bag;
        internal static int BagCount(byte pid) => bags.TryGetValue(pid, out var b) ? b.Count : 0;
        internal static byte BagKind(byte pid, int i) => bags.TryGetValue(pid, out var b) && i < b.Count ? b[i] : (byte)0;

        private static List<byte> Bag(byte pid) {
            if (!bags.TryGetValue(pid, out var b)) { b = new List<byte>(); bags[pid] = b; }
            return b;
        }

        internal static void RemoveFromBag(byte pid, byte kind) {
            if (!bags.TryGetValue(pid, out var b)) return;
            int i = b.IndexOf(kind);
            if (i < 0) return;
            b.RemoveAt(i);
            if (TrickOrTreat.AmHost() && hostBagTricks.TryGetValue(pid, out var t) && i < t.Count) t.RemoveAt(i);
            if (b.Count == 0) bags.Remove(pid);
        }

        internal static void RequestTake(TrickOrTreat.Candy c) {
            var lp = PlayerControl.LocalPlayer;
            if (c == null || c.Eaten || c.Pending || !TrickOrTreat.IsAlive(lp)) return;
            if (TrickOrTreat.AmHost()) { HostTake(lp, TrickOrTreat.phase, c.Index); return; }
            c.Pending = true;
            TrickOrTreat.Send(SubTakeReq, w => { w.Write(TrickOrTreat.phase); w.Write(c.Index); });
        }

        /// <summary>Host, cabinets: into the bag while it has room, eaten on the spot otherwise.</summary>
        internal static void HostTakeOrEat(PlayerControl p, byte ph, byte idx) {
            if (p != null && BagOn() && BagCount(p.PlayerId) < BagSize) HostTake(p, ph, idx);
            else TrickOrTreat.HostEat(p, ph, idx, null);
        }

        private static void HostTake(PlayerControl p, byte ph, byte idx) {
            try {
                if (!TrickOrTreat.AmHost() || !TrickOrTreat.IsAlive(p) || TrickOrTreat.InMeeting() || ph != TrickOrTreat.phase) return;
                var c = TrickOrTreat.candies.FirstOrDefault(k => k.Index == idx);
                if (c == null || c.Eaten) return;
                float reach = c.Cab != TreatCabinets.None ? TreatCabinets.SearchRange() : TrickOrTreat.Range();
                if (Vector2.Distance(p.GetTruePosition(), c.Pos) > reach + 0.9f) return;
                if (!BagOn() || BagCount(p.PlayerId) >= BagSize) { TrickOrTreat.HostEat(p, ph, idx, null); return; }
                bool trick = HostTakeTrick(idx);
                byte pid = p.PlayerId, kind = c.Kind;
                TrickOrTreat.Send(SubTaken, w => { w.Write(ph); w.Write(idx); w.Write(pid); w.Write(kind); });
                ApplyTaken(ph, idx, pid, kind);
                if (!hostBagTricks.TryGetValue(pid, out var t)) { t = new List<bool>(); hostBagTricks[pid] = t; }
                t.Add(trick);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} take failed: {e}"); }
        }

        private static void ApplyTaken(byte ph, byte idx, byte pid, byte kind) {
            var c = TrickOrTreat.candies.FirstOrDefault(k => k.Index == idx);
            if (c != null && ph == TrickOrTreat.phase) { c.Eaten = true; c.Pending = false; TreatFx.RemoveCandy(c); }
            Bag(pid).Add(kind);
            var lp = PlayerControl.LocalPlayer;
            if (lp != null && lp.PlayerId == pid) {
                TreatFx.Play(Rustle(), 0.7f, 0f);
                string name = kind < TrickOrTreat.KindNames.Length ? TrickOrTreat.KindNames[kind] : "?";
                TreatFx.ShowHint(TrickOrTreat.De() ? $"{name} in der Tüte ({BagCount(pid)}/{BagSize})" : $"{name} in the bag ({BagCount(pid)}/{BagSize})");
            }
            Log($"player {pid} put {(kind < TrickOrTreat.KindNames.Length ? TrickOrTreat.KindNames[kind] : kind.ToString())} into the bag ({BagCount(pid)}).");
        }

        internal static void RequestBagEat(int slot) {
            var lp = PlayerControl.LocalPlayer;
            if (!TrickOrTreat.IsAlive(lp) || slot < 0 || slot >= BagCount(lp.PlayerId) || Time.time - bagEatAt < 0.8f) return;
            bagEatAt = Time.time;
            byte s = (byte)slot;
            if (TrickOrTreat.AmHost()) { HostBagEat(lp, s); return; }
            TrickOrTreat.Send(SubBagEatReq, w => w.Write(s));
        }

        private static void HostBagEat(PlayerControl p, byte slot) {
            try {
                if (!TrickOrTreat.AmHost() || !TrickOrTreat.IsAlive(p) || TrickOrTreat.InMeeting()) return;
                if (!bags.TryGetValue(p.PlayerId, out var b) || slot >= b.Count) return;
                byte kind = b[slot];
                // RemoveFromBag drops the first slot of this kind: read the trick flag of exactly that slot
                int first = b.IndexOf(kind);
                bool trick = hostBagTricks.TryGetValue(p.PlayerId, out var t) && first >= 0 && first < t.Count && t[first];
                if (kind == TrickOrTreat.PoisonKind) { TrickOrTreat.HostPoison(p, TrickOrTreat.phase, IdxBag); return; }
                var fx = trick ? HostTrickEffect() : TrickOrTreat.EffectOf(kind);
                TrickOrTreat.HostResolve(p, TrickOrTreat.phase, IdxBag, fx, kind);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} bag eat failed: {e}"); }
        }

        // ================================================================ Trick Candy
        private static readonly HashSet<byte> hostTricks = new();     // candy indices (host)
        private static readonly HashSet<byte> trickUsed = new();      // impostors who laid theirs since the last meeting

        /// <summary>Host: was this candy a Trick Candy? Forgets it (the candy is leaving the floor).</summary>
        internal static bool HostTakeTrick(byte idx) => hostTricks.Remove(idx);

        internal static bool IsBad(Treat fx) {
            var c = TreatFx.Tint(fx);
            return c.r > 0.9f && c.g < 0.5f;          // the red ones of the menu
        }

        internal static Treat HostTrickEffect() {
            var pool = TrickOrTreat.EffectPool(TrickOrTreat.roundEffects).Where(IsBad).ToList();
            if (pool.Count == 0) pool = TrickOrTreat.EffectPool(TreatSettings.AllEffects).Where(IsBad).ToList();
            return pool[rnd.Next(pool.Count)];
        }

        internal static bool CanTrick(PlayerControl lp) =>
            TrickOrTreat.On() && TreatSettings.Current.Trick && TrickOrTreat.IsAlive(lp) && TrickOrTreat.IsImp(lp)
            && !trickUsed.Contains(lp.PlayerId) && !TrickOrTreat.InMeeting() && TrickOrTreat.phase > 0;

        private static void RequestTrick() {
            var lp = PlayerControl.LocalPlayer;
            if (!CanTrick(lp) || lp.inVent) return;
            if (TrickOrTreat.AmHost()) { HostTrick(lp); return; }
            TrickOrTreat.Send(SubTrickReq, w => { });
            trickUsed.Add(lp.PlayerId);               // the button goes at once; the host's answer confirms it
        }

        private static void HostTrick(PlayerControl p) {
            try {
                if (!TrickOrTreat.AmHost() || p == null) return;
                if (!TrickOrTreat.On() || !TreatSettings.Current.Trick || !TrickOrTreat.IsAlive(p) || !TrickOrTreat.IsImp(p) || TrickOrTreat.InMeeting()) return;
                if (hostTrickBy.Contains(p.PlayerId) || TrickOrTreat.candies.Count >= 200) return;
                var kinds = Enumerable.Range(0, TrickOrTreat.KindCount).Where(k => (TrickOrTreat.roundKinds & (1u << k)) != 0).ToList();
                if (kinds.Count == 0) return;
                byte kind = (byte)kinds[rnd.Next(kinds.Count)];
                byte idx = (byte)(TrickOrTreat.candies.Count == 0 ? 0 : TrickOrTreat.candies.Max(c => c.Index) + 1);
                if (idx >= IdxSugarShock) return;
                var pos = p.GetTruePosition();
                pos = new Vector2(Mathf.Round(pos.x * 100f) / 100f, Mathf.Round(pos.y * 100f) / 100f);
                byte ph = TrickOrTreat.phase, pid = p.PlayerId;
                hostTrickBy.Add(pid);
                hostTricks.Add(idx);
                TrickOrTreat.Send(SubTrickPlaced, w => {
                    w.Write(ph); w.Write(idx); w.Write(pid);
                    w.Write(unchecked((ushort)(short)Mathf.RoundToInt(pos.x * 100f))); w.Write(unchecked((ushort)(short)Mathf.RoundToInt(pos.y * 100f)));
                    w.Write(kind);
                });
                ApplyTrickPlaced(ph, idx, pid, pos, kind);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} trick failed: {e}"); }
        }
        private static readonly HashSet<byte> hostTrickBy = new();

        private static void ApplyTrickPlaced(byte ph, byte idx, byte pid, Vector2 pos, byte kind) {
            trickUsed.Add(pid);
            if (ph != TrickOrTreat.phase) return;
            TrickOrTreat.candies.Add(new TrickOrTreat.Candy { Index = idx, Pos = pos, Kind = kind });
            TreatFx.RebuildCandies();
            var lp = PlayerControl.LocalPlayer;
            if (lp != null && lp.PlayerId == pid) TreatFx.ShowHint(TrickOrTreat.De() ? "Trick Candy gelegt" : "Trick Candy laid");
            Log($"player {pid} laid a Trick Candy ({TrickOrTreat.KindNames[kind]}) at {pos.x:F1},{pos.y:F1}.");
        }

        // ================================================================ Sugar Shock, Copycat Caramel (host)
        private static readonly Dictionary<byte, int> hostEats = new();
        private static readonly List<(byte pid, Treat fx)> hostLast = new();

        internal static string SugarShockName() => TrickOrTreat.De() ? "Zuckerschock" : "Sugar Shock";

        internal static void HostAfterEat(PlayerControl eater, Treat real, byte idx) {
            if (eater == null || idx == IdxSugarShock || idx == byte.MaxValue) return;
            if (!TrickOrTreat.IsStandIn(real) && real != Treat.Regurgitate) {
                hostLast.Add((eater.PlayerId, real));
                if (hostLast.Count > 32) hostLast.RemoveAt(0);
            }
            hostEats.TryGetValue(eater.PlayerId, out int n);
            hostEats[eater.PlayerId] = ++n;
            if (n == 3 && TreatSettings.Current.Shock && TrickOrTreat.IsAlive(eater)) {
                Log($"{eater.Data?.PlayerName} ate a third candy since the meeting: Sugar Shock.");
                TrickOrTreat.HostResolve(eater, TrickOrTreat.phase, IdxSugarShock, Treat.SugarCrash, byte.MaxValue);
            }
        }

        internal static bool HostLastOtherEffect(byte pid, out Treat fx) {
            for (int i = hostLast.Count - 1; i >= 0; i--)
                if (hostLast[i].pid != pid) { fx = hostLast[i].fx; return true; }
            fx = Treat.NothingQ;
            return false;
        }

        // ================================================================ effect hooks
        internal static void OnBegin(PlayerControl p, ActiveTreat a, ref string extra) {
            bool local = p == PlayerControl.LocalPlayer;
            switch (a.Fx) {
                case Treat.PeekAPop:
                    if (local) OpenAdmin();
                    break;
                case Treat.VentMint:
                    // every client links the same pair (the host drew it, P1); only the eater may use it
                    if (a.Imp && !LinkPair(a.P1, a.Owner) && local)
                        extra = TrickOrTreat.De() ? "Auf dieser Karte ist kein Vent mehr frei." : "No vent left to link on this map.";
                    break;
                case Treat.HomingHumbug:
                    if (local && IsSubmerged()) extra = TrickOrTreat.De() ? "Auf dieser Karte wirkt sie nicht." : "It does nothing on this map.";
                    break;
            }
        }

        internal static void OnEnd(PlayerControl p, ActiveTreat a) {
            bool local = p != null && p == PlayerControl.LocalPlayer;
            switch (a.Fx) {
                case Treat.PeekAPop:
                    if (local) CloseAdmin();
                    break;
                case Treat.VentMint:
                    if (a.Imp) UnlinkVents(a.Owner);
                    if (local && !a.Imp) HideVentButton();
                    break;
                case Treat.GhostlyGum:
                    SetAlpha(p, 1f);
                    break;
            }
        }

        // ---- meetings ----
        private static readonly List<(byte pid, byte room)> tattleNotes = new();
        private static bool tattlePosted;

        internal static void OnMeetingStart() {
            hostEats.Clear();
            trickUsed.Clear();
            hostTrickBy.Clear();
            hostTricks.Clear();
            tattleNotes.Clear();
            tattlePosted = false;
            foreach (var kv in TrickOrTreat.active) {
                if (!kv.Value.Any(a => a.Fx == Treat.TattletaleTaffy)) continue;
                var p = Helpers.playerById(kv.Key);
                if (!TrickOrTreat.IsAlive(p)) continue;
                var room = HwMechanics.RoomAt(p.GetTruePosition());
                tattleNotes.Add((kv.Key, room != null ? (byte)room.RoomId : byte.MaxValue));
            }
            ClearScreen();
        }

        internal static void OnMeetingEnd() {
            tattleNotes.Clear();
            tattlePosted = false;
        }

        private static void PostTattle() {
            if (tattlePosted || tattleNotes.Count == 0 || MeetingHud.Instance == null) return;
            var hud = HudManager.InstanceExists ? HudManager.Instance : null;
            if (hud == null || hud.Chat == null) return;
            tattlePosted = true;
            bool de = TrickOrTreat.De();
            foreach (var (pid, room) in tattleNotes) {
                var p = Helpers.playerById(pid);
                string name = p?.Data?.PlayerName ?? "?";
                string where = HwMechanics.RoomName(room) ?? (de ? "irgendwo im Nirgendwo" : "somewhere nowhere");
                string line = de ? $"Tattletale Taffy: {name} war zu Beginn des Meetings in {where}." : $"Tattletale Taffy: {name} was in {where} when the meeting began.";
                try { hud.Chat.AddChatWarning(line); } catch { }
                Log($"tattle: {name} in {where}.");
            }
        }

        // ================================================================ Sticky Toffee
        private static readonly Dictionary<byte, float> stuckUntil = new();
        internal static bool AnyStuck => stuckUntil.Count > 0;
        internal static float StuckMult(byte pid) => stuckUntil.TryGetValue(pid, out float t) && Time.time < t ? 0.5f : 1f;

        [HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.MurderPlayer))]
        static class StickyMurderPatch {
            public static void Postfix(PlayerControl __instance, [HarmonyArgument(0)] PlayerControl target) {
                try {
                    if (__instance == null || target == null || __instance.PlayerId == target.PlayerId) return;
                    if (target.Data == null || !target.Data.IsDead) return;
                    var a = TrickOrTreat.Get(target.PlayerId, Treat.StickyToffee);
                    if (a == null) return;
                    stuckUntil[__instance.PlayerId] = Time.time + 5f;
                    TrickOrTreat.End(a, "toffee stuck to the killer");
                    Log($"{__instance.Data?.PlayerName} is stuck in Sticky Toffee for 5 s.");
                } catch { }
            }
        }

        // ================================================================ Vent Mint
        // Crew: Vent.CanUse says yes for one trip (enter, move, exit). TOR's prefix answers first, this postfix widens it.
        [HarmonyPatch(typeof(Vent), nameof(Vent.CanUse))]
        static class VentMintCanUsePatch {
            public static void Postfix(Vent __instance, [HarmonyArgument(0)] NetworkedPlayerInfo pc, ref bool canUse, ref bool couldUse, ref float __result) {
                try {
                    if (TrickOrTreat.active.Count == 0 || pc == null || pc.Object == null || pc.IsDead || couldUse) return;
                    var a = TrickOrTreat.Get(pc.PlayerId, Treat.VentMint);
                    if (a == null || a.Imp) return;
                    var o = pc.Object;
                    if (a.Entered && !o.inVent) return;
                    if (__instance.name.StartsWith("JackInTheBoxVent_")) return;
                    couldUse = o.CanMove || o.inVent;
                    Vector3 center = o.Collider.bounds.center, at = __instance.transform.position;
                    float d = Vector2.Distance(center, at);
                    canUse = couldUse && d <= __instance.UsableDistance && !PhysicsHelpers.AnythingBetween(o.Collider, center, at, Constants.ShipOnlyMask, false);
                    __result = d;
                } catch { }
            }
        }

        private static void TickVentMint(PlayerControl lp) {
            var a = TrickOrTreat.Get(lp.PlayerId, Treat.VentMint);
            if (a == null || a.Imp) return;
            if (lp.inVent) a.Entered = true;
            else if (a.Entered) {
                TrickOrTreat.End(a, "vent trip done");
                return;
            }
            try {
                var vb = HudManager.InstanceExists ? HudManager.Instance.ImpostorVentButton : null;
                if (vb != null && !vb.isActiveAndEnabled && HudManager.Instance.ReportButton.isActiveAndEnabled) vb.Show();
            } catch { }
        }

        private static void HideVentButton() {
            try {
                var lp = PlayerControl.LocalPlayer;
                if (lp == null || lp.roleCanUseVents()) return;
                if (HudManager.InstanceExists) HudManager.Instance.ImpostorVentButton.Hide();
            } catch { }
        }

        // Impostor: two vents with a free arrow get linked. Since 21.10. on EVERY client (audit): a link only the eater
        // knew made the host and the others disagree about his vent jump. The host draws the pair as an index into a
        // list every client builds the same way (vents by Id); a TryMoveToVent prefix keeps everybody else off it.
        private static readonly List<(Vent vent, int slot, byte owner)> links = new();

        private static Vent SlotGet(Vent v, int s) => s == 0 ? v.Left : s == 1 ? v.Right : v.Center;
        private static void SlotSet(Vent v, int s, Vent to) { if (s == 0) v.Left = to; else if (s == 1) v.Right = to; else v.Center = to; }
        private static int FreeSlot(Vent v) { for (int s = 0; s < 3; s++) if (SlotGet(v, s) == null) return s; return -1; }
        private static bool Linked(Vent a, Vent b) { for (int s = 0; s < 3; s++) if (SlotGet(a, s) == b) return true; return false; }

        /// <summary>All candidate pairs, the same list on every client: vents with a free arrow by Id, not linked yet,
        /// more than 4 m apart.</summary>
        private static List<(Vent a, Vent b, float d)> VentPairs() {
            var pairs = new List<(Vent a, Vent b, float d)>();
            var ship = ShipStatus.Instance;
            if (ship == null) return pairs;
            var free = ship.AllVents.ToArray().Where(v => v != null && !v.name.StartsWith("JackInTheBoxVent_") && FreeSlot(v) >= 0)
                .OrderBy(v => v.Id).ToList();
            for (int i = 0; i < free.Count; i++)
                for (int j = i + 1; j < free.Count; j++) {
                    if (Linked(free[i], free[j])) continue;
                    float d = Vector2.Distance(free[i].transform.position, free[j].transform.position);
                    if (d > 4f) pairs.Add((free[i], free[j], d));
                }
            return pairs;
        }

        /// <summary>Host: one of the farther half, as an index into VentPairs (255: none).</summary>
        internal static byte HostPickVentPair() {
            try {
                var pairs = VentPairs();
                if (pairs.Count == 0) return byte.MaxValue;
                var far = Enumerable.Range(0, Math.Min(pairs.Count, 254)).OrderByDescending(i => pairs[i].d).Take(Math.Max(1, pairs.Count / 2)).ToList();
                return (byte)far[rnd.Next(far.Count)];
            } catch { return byte.MaxValue; }
        }

        private static bool LinkPair(byte index, byte owner) {
            try {
                var pairs = VentPairs();
                if (index == byte.MaxValue || index >= pairs.Count) return false;
                var (va, vb, dist) = pairs[index];
                int sa = FreeSlot(va), sb = FreeSlot(vb);
                if (sa < 0 || sb < 0) return false;
                SlotSet(va, sa, vb);
                SlotSet(vb, sb, va);
                links.Add((va, sa, owner));
                links.Add((vb, sb, owner));
                Log($"Vent Mint: vents {va.Id} and {vb.Id} linked for player {owner} ({dist:F0} m).");
                return true;
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} vent link failed: {e.Message}"); return false; }
        }

        private static void UnlinkVents(byte? owner = null) {
            int n = 0;
            for (int i = links.Count - 1; i >= 0; i--) {
                var (v, s, o) = links[i];
                if (owner.HasValue && o != owner.Value) continue;
                try { if (v != null) SlotSet(v, s, null); } catch { }
                links.RemoveAt(i);
                n++;
            }
            if (n > 0) Log("Vent Mint: vent link removed.");
        }

        private static bool IsForeignLink(Vent from, Vent to) {
            var lp = PlayerControl.LocalPlayer;
            if (from == null || to == null || lp == null) return false;
            foreach (var (v, s, o) in links)
                if (v == from && SlotGet(v, s) == to) return o != lp.PlayerId;
            return false;
        }

        // A link that belongs to another player: the arrow may show, the jump does not happen.
        [HarmonyPatch(typeof(Vent), nameof(Vent.TryMoveToVent))]
        static class ForeignLinkPatch {
            public static bool Prefix(Vent __instance, [HarmonyArgument(0)] Vent otherVent, ref bool __result) {
                try {
                    if (links.Count == 0 || !IsForeignLink(__instance, otherVent)) return true;
                    __result = false;
                    return false;
                } catch { return true; }
            }
        }


        // ================================================================ Peek-a-Pop
        private static bool peekOpened;
        private static void OpenAdmin() {
            try {
                var hud = HudManager.InstanceExists ? HudManager.Instance : null;
                if (hud == null) return;
                if (!MapBehaviour.Instance || !MapBehaviour.Instance.isActiveAndEnabled) {
                    hud.InitMap();
                    MapBehaviour.Instance.ShowCountOverlay(allowedToMove: true, showLivePlayerPosition: true, includeDeadBodies: false);
                    peekOpened = true;
                }
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} admin map failed: {e.Message}"); }
        }

        private static void CloseAdmin() {
            if (!peekOpened) return;
            peekOpened = false;
            try { if (MapBehaviour.Instance != null && MapBehaviour.Instance.IsOpen) MapBehaviour.Instance.Close(); } catch { }
        }

        // ================================================================ Double Dip
        // TOR's own tally (the Mayor's spot): a postfix on its private CalculateVotes adds the second vote. TOR swaps the
        // Swapper's votes inside that method already, so the extra vote follows the swap.
        [HarmonyPatch]
        static class DoubleDipTallyPatch {
            static System.Reflection.MethodBase TargetMethod() =>
                AccessTools.Method(typeof(RPCProcedure).Assembly.GetType("TheOtherRoles.Patches.MeetingHudPatch+MeetingCalculateVotesPatch"), "CalculateVotes");   // straight from TOR (TypeByName scans every assembly)
            static bool Prepare() {
                bool ok = TargetMethod() != null;
                if (!ok) HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} TOR's vote tally not found, Double Dip counts once.");
                return ok;
            }
            public static void Postfix([HarmonyArgument(0)] MeetingHud hud, Dictionary<byte, int> __result) {
                try {
                    if (__result == null || hud == null || TrickOrTreat.active.Count == 0) return;
                    foreach (var area in hud.playerStates) {
                        if (area == null || !TrickOrTreat.Has(area.TargetPlayerId, Treat.DoubleDip)) continue;
                        byte to = area.VotedFor;
                        if (to == 252 || to == 254 || to == 255) continue;          // 253 is the skip, TOR counts it as a key
                        var voter = Helpers.playerById(area.TargetPlayerId);
                        if (!TrickOrTreat.IsAlive(voter)) continue;
                        to = Swapped(to);
                        __result.TryGetValue(to, out int n);
                        __result[to] = n + 1;
                        Log($"Double Dip: {voter.Data?.PlayerName}'s vote counts twice.");
                    }
                } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} double dip tally: {e.Message}"); }
            }
        }

        private static byte Swapped(byte id) {
            try {
                if (id == 253 || Swapper.swapper == null || Swapper.swapper.Data == null || Swapper.swapper.Data.IsDead) return id;
                if (Swapper.playerId1 == byte.MaxValue || Swapper.playerId2 == byte.MaxValue) return id;
                if (id == Swapper.playerId1) return Swapper.playerId2;
                if (id == Swapper.playerId2) return Swapper.playerId1;
            } catch { }
            return id;
        }

        // The second vote icon on the results, next to the votes already shown for that target.
        [HarmonyPatch(typeof(MeetingHud), nameof(MeetingHud.PopulateResults))]
        static class DoubleDipIconPatch {
            public static void Postfix(MeetingHud __instance, [HarmonyArgument(0)] Il2CppStructArray<MeetingHud.VoterState> states) {
                try {
                    if (__instance == null || states == null || TrickOrTreat.active.Count == 0) return;
                    var extra = new Dictionary<byte, int>();
                    foreach (var s in states) {
                        if (!TrickOrTreat.Has(s.VoterId, Treat.DoubleDip)) continue;
                        var info = GameData.Instance.GetPlayerById(s.VoterId);
                        if (info == null || info.IsDead) continue;
                        byte key = s.SkippedVote ? (byte)253 : s.VotedForId;
                        if (!s.SkippedVote && (key == 252 || key == 254 || key == 255)) continue;
                        int shown = 0;
                        foreach (var o in states) {
                            var oi = GameData.Instance.GetPlayerById(o.VoterId);
                            if (oi == null || oi.IsDead) continue;
                            if (s.SkippedVote ? o.SkippedVote : (!o.SkippedVote && o.VotedForId == key)) shown++;
                        }
                        try { if (Mayor.mayor != null && Mayor.voteTwice && states.Any(o => o.VoterId == Mayor.mayor.PlayerId && (s.SkippedVote ? o.SkippedVote : o.VotedForId == key))) shown++; } catch { }
                        extra.TryGetValue(key, out int before);
                        extra[key] = before + 1;
                        Transform parent;
                        if (s.SkippedVote) parent = __instance.SkippedVoting.transform;
                        else {
                            byte showOn = Swapped(key);
                            var area = __instance.playerStates.FirstOrDefault(x => x != null && x.TargetPlayerId == showOn);
                            if (area == null) continue;
                            parent = area.transform;
                        }
                        __instance.BloopAVoteIcon(info, shown + before, parent);
                    }
                } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} double dip icon: {e.Message}"); }
            }
        }

        // ================================================================ the candy button (Homing Humbug, Trick Candy)
        private static CustomButton candyButton, bagButton;
        private static Sprite homeSprite, trickSprite;

        private static bool WantsHome(PlayerControl lp) => TrickOrTreat.IsAlive(lp) && TrickOrTreat.Has(lp.PlayerId, Treat.HomingHumbug);

        // No snap halfway up a ladder, on a zipline or a moving platform (Airship, Fungle): the other clients keep the
        // ride going and the player ends up in two places (audit 21.10.; CanMove alone does not say so for sure).
        private static bool FreeToSnap(PlayerControl lp) {
            try { return lp.CanMove && !lp.inVent && !lp.onLadder && !lp.inMovingPlat && !lp.walkingToVent; } catch { return false; }
        }

        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Start))]
        static class HudStartPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix(HudManager __instance) {
                try {
                    candyButton = new CustomButton(
                        OnButton,
                        () => { var lp = PlayerControl.LocalPlayer; return lp != null && (WantsHome(lp) || CanTrick(lp)); },
                        () => { var lp = PlayerControl.LocalPlayer; return lp != null && FreeToSnap(lp) && !(WantsHome(lp) && IsSubmerged()); },
                        () => { if (candyButton != null) candyButton.Timer = 0f; },
                        TrickSprite(), CustomButton.ButtonPositions.lowerRowLeft, __instance, null, false, "TRICK");
                    candyButton.MaxTimer = 0f;
                    candyButton.Timer = 0f;
                } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} candy button failed: {e}"); }
                try {
                    // the bag: left of TOR's upper row (upperRowFarLeft is -3, nothing of TOR sits at -4)
                    bagButton = new CustomButton(
                        TreatBagMenu.Toggle,
                        () => { var lp = PlayerControl.LocalPlayer; return lp != null && TrickOrTreat.On() && BagOn() && TrickOrTreat.IsAlive(lp) && BagCount(lp.PlayerId) > 0; },
                        () => !TrickOrTreat.InMeeting(),
                        () => { if (bagButton != null) bagButton.Timer = 0f; TreatBagMenu.Close(); },
                        TreatFx.MenuIcon(), new Vector3(-4f, 1f, 0f), __instance, null, false, "BAG");
                    bagButton.MaxTimer = 0f;
                    bagButton.Timer = 0f;
                } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} bag button failed: {e}"); }
            }
        }

        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        static class ButtonLookPatch {
            [HarmonyPriority(Priority.Last)]                // after TOR's own button update in the same HudManager.Update
            public static void Postfix() {
                try {
                    var lp = PlayerControl.LocalPlayer;
                    if (candyButton == null || lp == null) return;
                    bool de = TrickOrTreat.De();
                    if (WantsHome(lp)) { candyButton.Sprite = HomeSprite(); candyButton.buttonText = de ? "HEIM" : "HOME"; }
                    else { candyButton.Sprite = TrickSprite(); candyButton.buttonText = "TRICK"; }
                    if (bagButton != null) {
                        int n = BagCount(lp.PlayerId);
                        bagButton.buttonText = (de ? "TÜTE" : "BAG") + $" ({n})";
                        if (bagButton.HasButton != null && !bagButton.HasButton()) bagButton.setActive(false);   // an empty bag: gone, not greyed
                    }
                } catch { }
            }
        }

        private static void OnButton() {
            var lp = PlayerControl.LocalPlayer;
            if (lp == null || !lp.CanMove || lp.inVent) return;
            if (WantsHome(lp)) { GoHome(lp); return; }
            RequestTrick();
        }

        private static void GoHome(PlayerControl lp) {
            var a = TrickOrTreat.Get(lp.PlayerId, Treat.HomingHumbug);
            if (a == null || IsSubmerged() || !FreeToSnap(lp)) return;
            try {
                var ship = ShipStatus.Instance;
                var at = ship.MeetingSpawnCenter + new Vector2(0.35f * Mathf.Cos(lp.PlayerId * 1.3f), 0.25f * Mathf.Sin(lp.PlayerId * 1.3f));
                lp.NetTransform.RpcSnapTo(at);
                TreatFx.Play(Rustle(), 0.6f, 0f);
                Log($"Homing Humbug: {lp.Data?.PlayerName} went back to the meeting spot.");
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} homing failed: {e.Message}"); }
            TrickOrTreat.End(a, "used");
        }

        internal static bool IsSubmerged() {
            try { return SubmergedCompatibility.IsSubmerged; } catch { return false; }
        }

        private static Sprite HomeSprite() {
            if (homeSprite != null) return homeSprite;
            // a candy cane: red and white stripes, the hook at the top
            var c = new TreatFx.Canvas(128, 128);
            var red = TreatFx.C(0.88f, 0.12f, 0.16f); var white = TreatFx.C(0.98f, 0.96f, 0.94f);
            Vector2 prev = new Vector2(44, 14);
            var path = new List<Vector2>();
            for (int i = 0; i <= 20; i++) path.Add(new Vector2(44, 14 + i * 3.6f));
            for (int i = 1; i <= 16; i++) { float ang = Mathf.PI - i / 16f * Mathf.PI; path.Add(new Vector2(64 + 20 * Mathf.Cos(ang), 86 + 20 * Mathf.Sin(ang))); }
            for (int i = 1; i < path.Count; i++) c.Line(path[i - 1].x, path[i - 1].y, path[i].x, path[i].y, 15f, white);
            for (int i = 1; i < path.Count; i++) if ((i / 3) % 2 == 0) c.Line(path[i - 1].x, path[i - 1].y, path[i].x, path[i].y, 15f, red);
            c.Outline(TreatFx.C(0.08f, 0.04f, 0.1f), 3);
            homeSprite = Sprite.Create(c.ToTexture("treat_home"), new Rect(0, 0, 128, 128), new Vector2(0.5f, 0.5f), 128f);
            homeSprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return homeSprite;
        }

        private static Sprite TrickSprite() {
            if (trickSprite != null) return trickSprite;
            // a lollipop with a dark spiral and two little horns: the candy that bites back
            var c = new TreatFx.Canvas(128, 128);
            c.Line(64, 6, 64, 54, 6f, TreatFx.C(0.95f, 0.92f, 0.85f));
            c.Disc(64, 78, 36, TreatFx.C(0.62f, 0.12f, 0.2f));
            for (int i = 0; i < 60; i++) {
                float t = i / 60f, ang = t * Mathf.PI * 5f, r = 4 + t * 30;
                float t2 = (i + 1) / 60f, ang2 = t2 * Mathf.PI * 5f, r2 = 4 + t2 * 30;
                c.Line(64 + r * Mathf.Cos(ang), 78 + r * Mathf.Sin(ang), 64 + r2 * Mathf.Cos(ang2), 78 + r2 * Mathf.Sin(ang2), 4f, TreatFx.C(0.18f, 0.03f, 0.08f));
            }
            c.Tri(36, 104, 44, 124, 52, 108, TreatFx.C(0.18f, 0.03f, 0.08f));
            c.Tri(92, 104, 84, 124, 76, 108, TreatFx.C(0.18f, 0.03f, 0.08f));
            c.Outline(TreatFx.C(0.08f, 0.04f, 0.1f), 3);
            trickSprite = Sprite.Create(c.ToTexture("treat_trick"), new Rect(0, 0, 128, 128), new Vector2(0.5f, 0.5f), 128f);
            trickSprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return trickSprite;
        }

        // ================================================================ per frame
        // Per-frame helpers without LINQ, closures or fresh collections (audit 21.10.).
        private static bool HasFx(List<ActiveTreat> l, Treat fx) {
            if (l == null) return false;
            foreach (var a in l) if (a.Fx == fx) return true;
            return false;
        }
        private static readonly HashSet<byte> wantBuf = new HashSet<byte>();
        private static readonly List<byte> keyBuf = new List<byte>();
        private static List<byte> KeysOf<T>(Dictionary<byte, T> d) { keyBuf.Clear(); keyBuf.AddRange(d.Keys); return keyBuf; }
        private static List<byte> Copy(HashSet<byte> h) { keyBuf.Clear(); keyBuf.AddRange(h); return keyBuf; }

        internal static void Tick(bool meeting) {
            TreatBagMenu.Tick(meeting);
            if (stuckUntil.Count > 0)
                foreach (var id in KeysOf(stuckUntil)) if (Time.time >= stuckUntil[id]) stuckUntil.Remove(id);
            TickWrappers(meeting);
            if (meeting) {
                ClearScreen();
                PostTattle();
                return;
            }
            var lp = PlayerControl.LocalPlayer;
            if (lp == null) return;
            var mine = TrickOrTreat.active.TryGetValue(lp.PlayerId, out var l) ? l : null;
            TickCompass(HasFx(mine, Treat.CandyCornCompass) ? lp : null);
            TickFizz(HasFx(mine, Treat.FizzPop) ? lp : null);
            TickFrost(HasFx(mine, Treat.BrainFreeze));
            TickTattleArrows(lp);
            TickVentMint(lp);
            TickGhostly();
            TickSticky(lp);
        }

        private static void ClearScreen() {
            TickCompass(null);
            TickFrost(false);
            foreach (var a in tattleArrows.Values) { try { if (a?.arrow != null) UnityEngine.Object.Destroy(a.arrow); } catch { } }
            tattleArrows.Clear();
            CloseAdmin();
        }

        internal static void Clear() {
            TreatBagMenu.Close();
            ClearScreen();
            UnlinkVents();
            bags.Clear();
            hostBagTricks.Clear();
            hostTricks.Clear();
            hostTrickBy.Clear();
            trickUsed.Clear();
            hostEats.Clear();
            hostLast.Clear();
            stuckUntil.Clear();
            tattleNotes.Clear();
            tattlePosted = false;
            foreach (var w in wrappers) if (w.sr != null) UnityEngine.Object.Destroy(w.sr.gameObject);
            wrappers.Clear();
            lastDrop.Clear();
            foreach (var pid in ghostly.ToList()) SetAlpha(Helpers.playerById(pid), 1f, true);
            ghostly.Clear();
            foreach (var sr in stickyGlows.Values) if (sr != null) UnityEngine.Object.Destroy(sr.gameObject);
            stickyGlows.Clear();
        }

        // ---- Candy Corn Compass: TOR's edge arrow to the nearest living player ----
        private static Arrow compass;
        private static float compassSearch;
        private static Vector3 compassTarget;
        private static void TickCompass(PlayerControl lp) {
            if (lp == null) {
                if (compass != null) { try { if (compass.arrow != null) UnityEngine.Object.Destroy(compass.arrow); } catch { } compass = null; }
                return;
            }
            if (Time.time >= compassSearch) {
                compassSearch = Time.time + 0.25f;
                PlayerControl best = null; float bd = float.MaxValue;
                foreach (var p in PlayerControl.AllPlayerControls.ToArray()) {
                    if (p == null || p == lp || !TrickOrTreat.IsAlive(p)) continue;
                    float d = Vector2.Distance(lp.GetTruePosition(), p.GetTruePosition());
                    if (d < bd) { bd = d; best = p; }
                }
                if (best == null) { TickCompass(null); return; }
                compassTarget = best.transform.position;
            }
            if (compass == null) compass = new Arrow(new Color(1f, 0.78f, 0.25f));
            compass.Update(compassTarget);
            compass.arrow.SetActive(true);
        }

        // ---- Fizz Pop: TOR's Detective footprints of everyone, on this client only ----
        private static float fizzNext;
        private static void TickFizz(PlayerControl lp) {
            if (lp == null || Time.time < fizzNext) return;
            fizzNext = Time.time + Mathf.Max(0.25f, Detective.footprintIntervall);
            try {
                foreach (var p in PlayerControl.AllPlayerControls.ToArray())
                    if (p != null && p != lp && TrickOrTreat.IsAlive(p) && !p.inVent) FootprintHolder.Instance.MakeFootprint(p);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} footprints: {e.Message}"); fizzNext = Time.time + 5f; }
        }

        // ---- Brain Freeze: frost on the screen edge (the speed is 0 in SpeedMult) ----
        private static SpriteRenderer frostSr;
        private static Sprite frostSprite;
        private static float frostSince = -1f;
        private static void TickFrost(bool want) {
            if (!want) {
                if (frostSr != null) frostSr.enabled = false;
                frostSince = -1f;
                return;
            }
            if (frostSince < 0f) { frostSince = Time.time; TreatFx.Play(Crackle(), 0.7f, 0f); }
            if (frostSr == null) frostSr = TreatFx.UiSr("TreatFrost", FrostSprite(), 155);
            TreatFx.Cover(frostSr, -47f);
            float a = Mathf.Clamp01((Time.time - frostSince) / 0.25f);
            frostSr.color = new Color(1f, 1f, 1f, 0.85f * a);
            frostSr.enabled = true;
        }

        private static Sprite FrostSprite() {
            if (frostSprite != null) return frostSprite;
            const int w = 160, h = 90;
            var px = new Color[w * h];
            var noise = new System.Random(21);
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++) {
                    float dx = Mathf.Abs((x + 0.5f) / w * 2f - 1f), dy = Mathf.Abs((y + 0.5f) / h * 2f - 1f);
                    float edge = Mathf.Max(dx, dy);
                    float n = (float)noise.NextDouble();
                    float a = Mathf.Clamp01((edge - 0.62f) / 0.38f + (n - 0.5f) * 0.25f);
                    px[y * w + x] = new Color(0.82f, 0.93f, 1f, a * a);
                }
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp };
            tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            tex.SetPixels(px);
            tex.Apply(false, false);
            frostSprite = Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), h);       // 1 unit high
            frostSprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return frostSprite;
        }

        // ---- Tattletale Taffy, live part: the impostors get an arrow to the eater for 10 s ----
        private static readonly Dictionary<byte, Arrow> tattleArrows = new();
        private static void TickTattleArrows(PlayerControl lp) {
            var want = wantBuf; want.Clear();
            if (TrickOrTreat.IsImp(lp) && TrickOrTreat.IsAlive(lp)) {
                foreach (var kv in TrickOrTreat.active) {
                    if (kv.Key == lp.PlayerId) continue;
                    var a = kv.Value.FirstOrDefault(x => x.Fx == Treat.TattletaleTaffy);
                    if (a == null || Time.time - a.Started > 10f) continue;
                    var p = Helpers.playerById(kv.Key);
                    if (!TrickOrTreat.IsAlive(p)) continue;
                    want.Add(kv.Key);
                    if (!tattleArrows.TryGetValue(kv.Key, out var arrow) || arrow == null || arrow.arrow == null) {
                        arrow = new Arrow(new Color(1f, 0.25f, 0.25f));
                        tattleArrows[kv.Key] = arrow;
                    }
                    arrow.Update(p.transform.position);
                    arrow.arrow.SetActive(true);
                }
            }
            foreach (var id in KeysOf(tattleArrows)) {
                if (want.Contains(id)) continue;
                try { if (tattleArrows[id]?.arrow != null) UnityEngine.Object.Destroy(tattleArrows[id].arrow); } catch { }
                tattleArrows.Remove(id);
            }
        }

        // ---- Ghostly Gum (every client): the Phantom's own fade on the cosmetics ----
        private static readonly HashSet<byte> ghostly = new();
        private static void TickGhostly() {
            foreach (var kv in TrickOrTreat.active) {
                if (!HasFx(kv.Value, Treat.GhostlyGum)) continue;
                var p = Helpers.playerById(kv.Key);
                if (!TrickOrTreat.IsAlive(p)) continue;
                ghostly.Add(kv.Key);
                SetAlpha(p, 0.4f);
            }
            if (ghostly.Count == 0) return;
            foreach (var id in Copy(ghostly)) {
                if (TrickOrTreat.Has(id, Treat.GhostlyGum)) continue;
                // still in a vent: try again next frame (audit 21.10.: removed anyway, he stayed see-through)
                var p = Helpers.playerById(id);
                if (p != null && p.inVent) continue;
                SetAlpha(p, 1f);
                ghostly.Remove(id);
            }
        }

        // force: the round reset, where nobody is left to try again later
        private static void SetAlpha(PlayerControl p, float a, bool force = false) {
            try { if (p != null && p.cosmetics != null && (force || !p.inVent)) p.cosmetics.SetPhantomRoleAlpha(a); } catch { }
        }

        // ---- Sticky Toffee (every client): a caramel glow under the stuck killer while it lasts ----
        private static readonly Dictionary<byte, SpriteRenderer> stickyGlows = new();
        private static void TickSticky(PlayerControl lp) {
            var want = wantBuf; want.Clear();
            float k = TreatFx.UiPerWorld();
            foreach (var kv in stuckUntil) {
                var p = Helpers.playerById(kv.Key);
                if (!TrickOrTreat.IsAlive(p) || p.inVent || Time.time >= kv.Value) continue;
                if (p != lp && Vector2.Distance(p.GetTruePosition(), lp.GetTruePosition()) > 6f) continue;
                if (!TreatFx.ToUi((Vector3)p.GetTruePosition() + new Vector3(0f, 0.05f, 0f), out var ui)) continue;
                want.Add(kv.Key);
                if (!stickyGlows.TryGetValue(kv.Key, out var sr) || sr == null) { sr = TreatFx.UiSr("sticky" + kv.Key, TreatFx.Glow(), 184); stickyGlows[kv.Key] = sr; }
                sr.transform.position = ui + new Vector3(0f, 0f, 0.5f);
                sr.transform.localScale = new Vector3(1.5f, 0.6f, 1f) * k;
                sr.color = new Color(0.78f, 0.45f, 0.12f, 0.6f);
                sr.enabled = true;
            }
            foreach (var id in KeysOf(stickyGlows)) {
                if (want.Contains(id)) continue;
                if (stickyGlows[id] != null) UnityEngine.Object.Destroy(stickyGlows[id].gameObject);
                stickyGlows.Remove(id);
            }
        }

        // ---- Wrapper Trail (every client): wrappers drop behind the eater and fade after 25 s ----
        private static readonly List<(SpriteRenderer sr, float born)> wrappers = new();
        private static readonly Dictionary<byte, Vector2> lastDrop = new();
        private static Sprite[] wrapperSprites;
        private const float WrapperLife = 25f;

        private static void TickWrappers(bool meeting) {
            float t = Time.time;
            if (!meeting) {
                foreach (var kv in TrickOrTreat.active) {
                    if (!HasFx(kv.Value, Treat.WrapperTrail)) continue;
                    var p = Helpers.playerById(kv.Key);
                    if (!TrickOrTreat.IsAlive(p) || p.inVent) continue;
                    var at = p.GetTruePosition();
                    if (lastDrop.TryGetValue(kv.Key, out var last) && (at - last).sqrMagnitude < 0.9f * 0.9f) continue;
                    lastDrop[kv.Key] = at;
                    if (wrappers.Count >= 150) { if (wrappers[0].sr != null) UnityEngine.Object.Destroy(wrappers[0].sr.gameObject); wrappers.RemoveAt(0); }
                    var go = new GameObject("wrapper") { layer = 11 };
                    var pos = at + new Vector2((float)rnd.NextDouble() * 0.2f - 0.1f, (float)rnd.NextDouble() * 0.1f - 0.05f);
                    go.transform.position = new Vector3(pos.x, pos.y, pos.y / 1000f + 0.0008f);
                    go.transform.rotation = Quaternion.Euler(0f, 0f, (float)rnd.NextDouble() * 360f);
                    var sr = go.AddComponent<SpriteRenderer>();
                    sr.sprite = Wrapper(rnd.Next(3));
                    wrappers.Add((sr, t));
                }
            }
            for (int i = wrappers.Count - 1; i >= 0; i--) {
                var w = wrappers[i];
                float age = t - w.born;
                if (w.sr == null || age > WrapperLife) { if (w.sr != null) UnityEngine.Object.Destroy(w.sr.gameObject); wrappers.RemoveAt(i); continue; }
                w.sr.color = new Color(1f, 1f, 1f, Mathf.Clamp01((WrapperLife - age) / 5f));
            }
        }

        private static Sprite Wrapper(int v) {
            if (wrapperSprites == null || wrapperSprites[v] == null) {
                wrapperSprites ??= new Sprite[3];
                var cols = new[] { TreatFx.C(1f, 0.55f, 0.12f), TreatFx.C(0.6f, 0.25f, 0.85f), TreatFx.C(0.35f, 0.85f, 0.35f) };
                for (int i = 0; i < 3; i++) {
                    if (wrapperSprites[i] != null) continue;
                    var c = new TreatFx.Canvas(40, 24);
                    var col = cols[i]; var dark = TreatFx.C(col.r * 0.6f, col.g * 0.6f, col.b * 0.6f);
                    c.Tri(14, 12, 3, 20, 3, 4, dark);          // twisted ends
                    c.Tri(26, 12, 37, 20, 37, 4, dark);
                    c.Ellipse(20, 12, 8, 6.5f, col);
                    c.Line(15, 9, 25, 15, 1.2f, TreatFx.C(1f, 1f, 1f, 0.5f));
                    c.Outline(TreatFx.C(0.08f, 0.04f, 0.1f), 1);
                    wrapperSprites[i] = Sprite.Create(c.ToTexture("treat_wrapper" + i), new Rect(0, 0, 40, 24), new Vector2(0.5f, 0.5f), 40f / 0.3f);
                    wrapperSprites[i].hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                }
            }
            return wrapperSprites[v];
        }

        // ================================================================ self test hooks (TrickOrTreatDiag.cs)
        internal static bool DiagCompass => compass != null && compass.arrow != null && compass.arrow.activeSelf;
        internal static int DiagWrappers => wrappers.Count;
        internal static int DiagLinks => links.Count;
        internal static bool DiagPeek => peekOpened && MapBehaviour.Instance != null && MapBehaviour.Instance.IsOpen;
        internal static bool DiagFrost => frostSr != null && frostSr.enabled;
        internal static string DiagTattle => string.Join(",", tattleNotes.Select(n => $"{n.pid}@{HwMechanics.RoomName(n.room) ?? "-"}"));
        internal static int DiagEats(byte pid) => hostEats.TryGetValue(pid, out int n) ? n : 0;
        internal static bool DiagBagButton => bagButton != null && bagButton.actionButton != null && bagButton.actionButton.gameObject.activeSelf;
        internal static bool DiagButton { get { var lp = PlayerControl.LocalPlayer; return lp != null && (WantsHome(lp) || CanTrick(lp)); } }
        internal static void DiagHome() { var lp = PlayerControl.LocalPlayer; if (lp != null) GoHome(lp); }
        /// <summary>The host lays a Trick Candy for p, impostor or not (freeplay dummies are crew).</summary>
        internal static void DiagTrickAs(PlayerControl p) {
            if (p == null) return;
            byte ph = TrickOrTreat.phase, pid = p.PlayerId;
            byte idx = (byte)(TrickOrTreat.candies.Count == 0 ? 0 : TrickOrTreat.candies.Max(c => c.Index) + 1);
            var pos = p.GetTruePosition();
            pos = new Vector2(Mathf.Round(pos.x * 100f) / 100f, Mathf.Round(pos.y * 100f) / 100f);
            hostTricks.Add(idx);
            ApplyTrickPlaced(ph, idx, pid, pos, 0);
        }

        // ================================================================ sounds
        private static AudioClip rustleClip, crackleClip;
        private static AudioClip Rustle() {
            if (rustleClip != null) return rustleClip;
            var noise = new System.Random(5);
            float lp = 0f;
            rustleClip = TreatFx.MakeClip("treat_rustle", 0.35f, (t, len) => {
                // crinkling paper: noise bursts in a quick flutter
                float env = Mathf.Clamp01(t / 0.02f) * Mathf.Clamp01((len - t) / 0.12f) * (0.55f + 0.45f * Mathf.Sin(t * 95f));
                lp += (((float)noise.NextDouble() * 2f - 1f) - lp) * 0.7f;
                return 0.45f * env * lp;
            });
            return rustleClip;
        }

        private static AudioClip Crackle() {
            if (crackleClip != null) return crackleClip;
            var noise = new System.Random(9);
            crackleClip = TreatFx.MakeClip("treat_crackle", 0.5f, (t, len) => {
                // ice: sparse sharp ticks over a falling hiss
                float tick = noise.NextDouble() < 0.012 ? 1f : 0f;
                float hiss = ((float)noise.NextDouble() * 2f - 1f) * 0.15f * Mathf.Exp(-t * 6f);
                return 0.6f * tick + hiss;
            });
            return crackleClip;
        }
    }

    /// <summary>The candy bag card: everything in the bag, a click eats that candy (HalloweenUI look).</summary>
    internal static class TreatBagMenu {
        private static GameObject root;
        private static int shownCount = -1;
        internal static bool IsOpen => root != null;

        internal static void Toggle() { if (root != null) Close(); else Open(); }

        internal static void Close() {
            if (root != null) UnityEngine.Object.Destroy(root);
            root = null;
            shownCount = -1;
        }

        internal static void Tick(bool meeting) {
            if (root == null) return;
            var lp = PlayerControl.LocalPlayer;
            int n = lp != null ? TreatPlus.BagCount(lp.PlayerId) : 0;
            if (meeting || !TrickOrTreat.IsAlive(lp) || n == 0) { Close(); return; }
            if (Input.GetKeyDown(KeyCode.Escape)) { Close(); return; }
            if (n != shownCount) Open();               // the bag changed (a candy taken or eaten): draw anew
        }

        private static void Open() {
            try {
                Close();
                var lp = PlayerControl.LocalPlayer;
                if (lp == null) return;
                int n = TreatPlus.BagCount(lp.PlayerId);
                if (n == 0) return;
                bool de = TrickOrTreat.De();
                const float cell = 300f, gap = 24f, pad = 34f;
                float w = Mathf.Max(pad * 2 + n * cell + (n - 1) * gap, 560f), h = 470f;
                root = HalloweenUI.Canvas("TreatBagMenu", 9400, true);
                HalloweenUI.Backdrop(root, Close);
                var card = HalloweenUI.CenterPanel(root, new Vector2(w, h));
                float y = HalloweenUI.Title(card, de ? "Süßigkeiten-Tüte" : "Candy Bag", 16f, 34f, TrickOrTreat.Orange);
                HalloweenUI.Button(card, "X", new Vector2(-HalloweenUI.FrameW - 12f, -HalloweenUI.FrameW - 12f), new Vector2(54f, 54f), HalloweenUI.Red, Close,
                    out _, new Vector2(1, 1), new Vector2(1, 1), new Vector2(1, 1), 36f);
                float x0 = (w - (n * cell + (n - 1) * gap)) / 2f;
                for (int i = 0; i < n; i++) {
                    int slot = i;
                    byte kind = TreatPlus.BagKind(lp.PlayerId, i);
                    string name = kind < TrickOrTreat.KindNames.Length ? TrickOrTreat.KindNames[kind] : "?";
                    var b = HalloweenUI.Button(card, name, new Vector2(x0 + i * (cell + gap), y - 20f), new Vector2(cell, 300f), HalloweenUI.Field,
                        () => { TreatPlus.RequestBagEat(slot); Close(); }, out var txt, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 24f);
                    txt.alignment = TMPro.TextAlignmentOptions.Bottom;
                    txt.rectTransform.offsetMin = new Vector2(8f, 14f);
                    var icon = new GameObject("Icon");
                    icon.transform.SetParent(b.transform, false);
                    var irt = HalloweenUI.Rect(icon, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f));
                    irt.anchoredPosition = new Vector2(0f, -18f);
                    irt.sizeDelta = new Vector2(210f, 210f);
                    var img = icon.AddComponent<UnityEngine.UI.Image>();
                    img.sprite = TreatFx.KindSprite(kind);
                    img.preserveAspect = true;
                    img.raycastTarget = false;
                }
                HalloweenUI.Text(card, de ? "Klick auf eine Süßigkeit, um sie zu essen." : "Click a candy to eat it.", 18f, HalloweenUI.Muted,
                    new Vector2(pad, y - 340f), new Vector2(w - 2 * pad, 28f));
                shownCount = n;
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogWarning($"{TrickOrTreat.LogPrefix} bag menu failed: {e}");
                Close();
            }
        }
    }
}
