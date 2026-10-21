// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
// Based on The Other Roles (https://github.com/TheOtherRolesAU/TheOtherRoles), GPL-3.0.

/*
 * Trick or Treat (2026-10-20): candies on the map, in the spirit of the candy event of Roblox DOORS.
 *
 *  - Host setting in its own menu (lobby menu entry, TrickOrTreatMenu.cs), off by default. At the start of the round and after every meeting the host scatters a number of
 *    candies (host option) over random walkable spots of the current map; the old ones are gone.
 *  - 12 candy kinds. Which kind does what is drawn by the host once per round (one seed, the same for everybody).
 *    Only the player who eats learns the effect (name plus a short line). Impostors eat too and get their own
 *    version of some effects. Ghosts cannot eat; running effects end with the death of the eater.
 *  - Eating = the Use button next to a candy. No limit per player. "Whole round" effects end with the x-th meeting
 *    after eating (host option); timed effects end when a meeting starts.
 *
 * Network: module byte 238 on UC's channel 230 (like the Banshee on 237). Host-authoritative:
 *   Sub 0 spawn     host -> all   [seed int][kinds ushort][effects uint][phase][n] n x [x short*100][y short*100][kind]
 *   Sub 1 eat req   any  -> host  [phase][candy]
 *   Sub 2 eaten     host -> all   [phase][candy][player][effect][p1][p2][impostor]
 *   Sub 3 shield    killer -> all [target][effect]   (a candy shield took a kill)
 *   Sub 4 recomplete host -> all  [player][n] n x [task id uint]   (after the Extra Chore task rebuild)
 *   Sub 5 rules     host -> all   [on][count][meetings][range][kinds ushort][effects uint]   (menu settings)
 *   Sub 6 cabinets  host -> all   [n] n x [x short*100][y short*100]   (own maps: the cabinets of the round, once)
 *   Sub 7 search    any  -> host  [phase][cabinet]
 *   Sub 8 searched  host -> all   [phase][cabinet][player][candy or 255]   (the cabinet stands open; a candy follows as Sub 2)
 *   Sub 9..13       candy bag, Trick Candy (TrickOrTreatPlus.cs)
 * Sub 2 carries the candy kind at the end; candy 254 = eaten from the bag, 253 = the Sugar Shock, 255 = self test.
 * On the own maps (Atlas and Halloween maps) the candies hide in cabinets instead of lying on the floor, see
 * TrickOrTreatCabinets.cs. A candy in a cabinet travels in Sub 0 with the cabinet's position.
 * Every client keeps the same list of running effects per player, so speed, size, shields, looks, glow, crows
 * and hiccups match everywhere; purely personal effects (vision, blur, sounds, arrows) only act on the eater.
 *
 * Patches go on game (Il2Cpp) methods where possible; the shield sits on TOR's checkMuderAttempt like the Medic
 * shield, with the Copycat's KillButton.DoClick fallback for the tiering detour loss.
 *
 * Rules from the host's Trick or Treat menu (TrickOrTreatMenu.cs, Sub 5), RPC module 238. See ID-Registry.md. Self test: UC_HALLOWEEN_DIAG=candy (TrickOrTreatDiag.cs).
 */

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using Hazel;
using UnityEngine;
using TheOtherRoles;
using UnknownsCollection;
using static TheOtherRoles.TheOtherRoles;

namespace UnknownsHalloween {
    internal enum Treat : byte {
        IronTaffy, SugarRush, CinnamonStick, NightOwl, ShortcutCaramel, PrizeInside, GuidingMint, LuckyLolly,
        EchoDrop, RockCandy, FogFudge, ExtraChore, Hiccups, LightsOut, Earmuffs, Jinkies, Butterfingers, Glowing,
        CrowCompany, Gobstopper, HardCandy, Brittle, Nausea, Regurgitate, VolatileStarlight, NothingQ, SwapSweet,
        ShrinkSherbet, BigBite,
        // 2026-10-21 (Hexenkessel picks)
        DoubleDip, CandyCornCompass, PeekAPop, StickyToffee, VentMint, FizzPop, HomingHumbug, TattletaleTaffy,
        BrainFreeze, ReverseGummy, WrapperTrail, SugarCrash, CopycatCaramel, GhostlyGum,
        Count
    }

    /// <summary>One running effect of one player (the same object on every client).</summary>
    internal sealed class ActiveTreat {
        public byte Owner;
        public Treat Fx;
        public bool Imp;
        public byte P1;
        public float Left;          // seconds left (timed effects)
        public int Meetings;        // meetings left (whole-round effects)
        public bool Round;
        public bool Used;           // shields: spent
        public int Saved = -1;      // Gobstopper: emergencies before
        public float Next;          // Hiccups: next hiccup (Time.time)
        public float Started;
        public bool Entered;        // Vent Mint (crew): the one vent trip has begun
    }

    public static class TrickOrTreat {
        internal const string LogPrefix = "[Halloween/Treats]";
        internal static readonly Color Orange = new Color(1f, 0.55f, 0.12f);

        // ---- rules: the host's Trick or Treat menu (TrickOrTreatMenu.cs), synced through Sub 5 ----
        private static readonly float[] RangeValues = { 0.6f, 0.9f, 1.25f };

        internal static bool On() {
            if (TrickOrTreatDiag.On) return true;
            return TreatSettings.Current.Enabled;
        }
        internal static int Count() => Mathf.Clamp(TreatSettings.Current.Count * Omens.CandyFactor(), 1, 30);   // x2 under the Harvest omen (Omens.cs)
        internal static int MeetingsFor() => Mathf.Clamp(TreatSettings.Current.Meetings, 1, 5);
        internal static float Range() => RangeValues[Mathf.Clamp(TreatSettings.Current.Range, 0, RangeValues.Length - 1)];

        // ---- candy kinds ----
        internal static readonly string[] KindNames = {
            "Pumpkin Caramel", "Spider Lolly", "Bat Gummy", "Eyeball Gum", "Tombstone Truffle", "Witch Licorice",
            "Ghost Floss", "Moon Drop", "Bone Biscuit", "Sour Worm", "Candy Apple", "Zombie Tooth",
            "Midnight Bonbon",
        };
        internal const int KindCount = 12;              // the drawn kinds; the deadly one comes on top
        internal const byte PoisonKind = 12;            // Midnight Bonbon: always the same look, always deadly
        internal const byte FxPoison = 250;             // its "effect" byte in Sub 2
        internal static readonly HashSet<byte> poisoned = new();

        // ---- network ----
        private const byte RpcId = 238;
        private const byte SubSpawn = 0, SubEatReq = 1, SubEaten = 2, SubShield = 3, SubRecomplete = 4;
        internal const byte SubRules = 5;
        internal const byte SubCabinets = 6, SubSearchReq = 7, SubSearched = 8;

        // ---- state (same on every client) ----
        internal sealed class Candy {
            public byte Index; public Vector2 Pos; public byte Kind; public bool Eaten; public byte Cab = TreatCabinets.None;
            // asked the host, no answer yet; a silent refusal (distance, phase) frees the candy again after 3 s (audit N-1)
            private float pendingAt = -10f;
            public bool Pending { get => Time.time - pendingAt < 3f; set => pendingAt = value ? Time.time : -10f; }
        }
        internal static readonly List<Candy> candies = new();
        internal static int seed;
        internal static byte phase;
        private static long mappedKey = long.MinValue;
        internal static uint roundKinds = TreatSettings.AllKinds;
        internal static ulong roundEffects = TreatSettings.AllEffects;   // the rules the spawn came with
        private static readonly Treat[] mapping = new Treat[KindCount];
        internal static readonly Dictionary<byte, List<ActiveTreat>> active = new();
        private static readonly Dictionary<byte, ActiveTreat> lastCandy = new();
        private static bool wasMeeting;
        private static readonly System.Random rnd = new System.Random();

        // ---- helpers ----
        internal static bool AmHost() => AmongUsClient.Instance != null && AmongUsClient.Instance.AmHost;
        internal static bool IsAlive(PlayerControl p) => p != null && p.Data != null && !p.Data.IsDead && !p.Data.Disconnected;
        internal static bool InMeeting() => MeetingHud.Instance != null || ExileController.Instance != null;
        internal static bool FreePlay() { try { return AmongUsClient.Instance != null && AmongUsClient.Instance.NetworkMode == NetworkModes.FreePlay; } catch { return false; } }
        internal static bool InRound() {
            try {
                var ac = AmongUsClient.Instance;
                return ac != null && (ac.GameState == InnerNet.InnerNetClient.GameStates.Started || ac.NetworkMode == NetworkModes.FreePlay)
                    && ShipStatus.Instance != null && PlayerControl.LocalPlayer != null;
            } catch { return false; }
        }
        internal static bool? LangOverride;           // the self test writes both languages
        internal static bool De() { if (LangOverride.HasValue) return LangOverride.Value; try { return UCLocalization.ActiveCode == "german"; } catch { return false; } }
        internal static bool IsImp(PlayerControl p) { try { return p != null && p.Data != null && p.Data.Role != null && p.Data.Role.IsImpostor; } catch { return false; } }

        internal static Treat EffectOf(byte kind) {
            EnsureMapping();
            return mapping[Mathf.Clamp(kind, 0, KindCount - 1)];
        }

        // The draw of the round: every client derives the same effect per kind from the host's seed and the active
        // effects the spawn message carried. Fewer active effects than kinds: effects are handed out twice.
        internal static List<Treat> EffectPool(ulong mask) {
            var pool = new List<Treat>();
            for (int i = 0; i < (int)Treat.Count; i++) if ((mask & (1UL << i)) != 0) pool.Add((Treat)i);
            if (pool.Count == 0) for (int i = 0; i < (int)Treat.Count; i++) pool.Add((Treat)i);
            return pool;
        }

        private static void EnsureMapping() {
            long key = ((long)seed << 32) ^ (long)(roundEffects * 4099UL) ^ roundKinds;
            if (mappedKey == key) return;
            mappedKey = key;
            var rng = new System.Random(seed);
            var all = EffectPool(roundEffects);
            var pool = all.Where(t => t != Treat.LuckyLolly).ToList();
            bool lucky = all.Contains(Treat.LuckyLolly) && rng.NextDouble() < 0.3;     // the rare one
            if (lucky || pool.Count == 0) pool.Add(Treat.LuckyLolly);
            for (int i = pool.Count - 1; i > 0; i--) { int j = rng.Next(i + 1); (pool[i], pool[j]) = (pool[j], pool[i]); }
            int n = 0;
            for (int k = 0; k < KindCount; k++) {
                if ((roundKinds & (1u << k)) == 0) { mapping[k] = pool[0]; continue; }
                mapping[k] = pool[n % pool.Count];
                n++;
            }
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} draw of the round: " + string.Join(", ", Enumerable.Range(0, KindCount)
                .Where(k => (roundKinds & (1u << k)) != 0).Select(k => $"{KindNames[k]}={mapping[k]}")));
        }

        // ---- self registration (like the Banshee) ----
        private static bool booted;
        private static void Boot() {
            if (booted) return;
            booted = true;
            try {
                TreatSettings.Load();
                UCRpc.Register(RpcId, HandleModuleRpc);
                UCFx.RegisterTick(Tick);
                var h = new Harmony("daunknown.unknownshalloween.treats");
                var m = AccessTools.Method(typeof(TeslaVersionHandshake), "AnyUCRoleEnabled");
                if (m != null) h.Patch(m, postfix: new HarmonyMethod(typeof(TrickOrTreat), nameof(HandshakePostfix)));
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"{LogPrefix} self registration failed: {e}");
            }
        }

        private static void HandshakePostfix(ref bool __result) {
            try { if (TreatSettings.Current.Enabled) __result = true; } catch { }
        }

        // ================================================================ RPC
        internal static void Send(byte sub, Action<MessageWriter> write) {
            if (FreePlay()) return;                         // nobody to tell
            try {
                var w = UCRpc.Begin(RpcId);
                w.Write(sub);
                write(w);
                AmongUsClient.Instance.FinishRpcImmediately(w);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} send {sub} failed: {e}"); }
        }

        private static void HandleModuleRpc(MessageReader r) {
            try {
                byte sub = r.ReadByte();
                switch (sub) {
                    case SubSpawn: {
                        int s = r.ReadInt32();
                        uint kinds = r.ReadUInt16();
                        ulong effects = r.ReadUInt64();
                        byte ph = r.ReadByte();
                        int n = r.ReadByte();
                        var list = new List<Candy>();
                        for (int i = 0; i < n; i++) {
                            float x = r.ReadInt16() / 100f, y = r.ReadInt16() / 100f;
                            list.Add(new Candy { Index = (byte)i, Pos = new Vector2(x, y), Kind = r.ReadByte() });
                        }
                        if (UCRpc.RequireHost("Treats.Spawn")) ApplySpawn(s, kinds, effects, ph, list);
                        break;
                    }
                    case SubEatReq: {
                        byte ph = r.ReadByte(), idx = r.ReadByte();
                        if (AmHost()) HostEat(UCRpc.Sender, ph, idx, null);
                        break;
                    }
                    case SubEaten: {
                        byte ph = r.ReadByte(), idx = r.ReadByte(), pid = r.ReadByte(), fx = r.ReadByte(), p1 = r.ReadByte(), p2 = r.ReadByte();
                        bool imp = r.ReadBoolean();
                        byte kind = r.ReadByte();
                        if (UCRpc.RequireHost("Treats.Eaten")) ApplyEaten(ph, idx, pid, (Treat)fx, p1, p2, imp, kind);
                        break;
                    }
                    case SubShield: {
                        byte target = r.ReadByte(), fx = r.ReadByte();
                        // only a living killer next to the target may say a shield took his kill (audit N-8)
                        var killer = UCRpc.Sender;
                        var victim = Helpers.playerById(target);
                        if (killer == null || victim == null || killer.PlayerId == target || !IsAlive(killer)
                            || Vector2.Distance(killer.GetTruePosition(), victim.GetTruePosition()) > 4f) {
                            HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} shield message for {target} from {killer?.Data?.PlayerName ?? "?"} ignored.");
                            break;
                        }
                        ApplyShieldUsed(target, (Treat)fx, false);
                        break;
                    }
                    case SubRules: {
                        var rules = TreatRules.Read(r);
                        if (UCRpc.RequireHost("Treats.Rules")) TreatSettings.ApplyFromHost(rules);
                        break;
                    }
                    case SubCabinets:
                    case SubSearchReq:
                    case SubSearched:
                        TreatCabinets.HandleRpc(sub, r);
                        break;
                    case TreatPlus.SubTakeReq: case TreatPlus.SubTaken: case TreatPlus.SubBagEatReq:
                    case TreatPlus.SubTrickReq: case TreatPlus.SubTrickPlaced:
                        TreatPlus.HandleRpc(sub, r);
                        break;
                    case SubRecomplete: {
                        byte pid = r.ReadByte();
                        int n = r.ReadByte();
                        var ids = new List<uint>();
                        for (int i = 0; i < n; i++) ids.Add(r.ReadUInt32());
                        if (UCRpc.RequireHost("Treats.Recomplete")) ApplyRecomplete(pid, ids);
                        break;
                    }
                }
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"{LogPrefix} HandleRpc failed: {e}");
            }
        }

        // ================================================================ spawn (host)
        internal static void HostSpawn() {
            try {
                if (!AmHost() || !On() || ShipStatus.Instance == null) return;
                if (!FreePlay() && !HalloweenHandshake.Ready()) return;
                if (seed == 0) seed = rnd.Next(1, int.MaxValue);
                byte ph = (byte)(phase + 1);
                var rules = TreatSettings.Current;
                uint kinds = rules.Kinds & TreatSettings.AllKinds;
                ulong effects = rules.Effects & TreatSettings.AllEffects;
                if (kinds == 0) kinds = TreatSettings.AllKinds;
                if (effects == 0) effects = TreatSettings.AllEffects;
                var kindList = Enumerable.Range(0, KindCount).Where(k => (kinds & (1u << k)) != 0).ToList();
                bool poison = rules.Poison;
                int want = Count() + (poison ? 1 : 0);
                List<Vector2> spots;
                if (TreatCabinets.Style() != null) {
                    // own maps: twice as many cabinets as candies, placed once per round; the candies move in
                    TreatCabinets.HostEnsure(want * 2);
                    spots = TreatCabinets.HostFill(want);
                    if (spots.Count < want) spots.AddRange(PickSpots(want - spots.Count));
                } else spots = PickSpots(want);
                var list = new List<Candy>();
                for (int i = 0; i < spots.Count; i++)
                    list.Add(new Candy { Index = (byte)i, Pos = spots[i], Kind = (byte)kindList[rnd.Next(kindList.Count)] });
                if (poison && list.Count > 0) list[list.Count - 1].Kind = PoisonKind;      // exactly one per spawn
                if (ph == 1) TreatSettings.Broadcast();      // the rules once more right at the start of the round
                Send(SubSpawn, w => {
                    w.Write(seed);
                    w.Write((ushort)kinds);
                    w.Write(effects);
                    w.Write(ph);
                    w.Write((byte)list.Count);
                    foreach (var c in list) {
                        w.Write(unchecked((ushort)(short)Mathf.RoundToInt(c.Pos.x * 100f)));
                        w.Write(unchecked((ushort)(short)Mathf.RoundToInt(c.Pos.y * 100f)));
                        w.Write(c.Kind);
                    }
                });
                // the receivers get the positions rounded to 1/100; the host uses the same
                foreach (var c in list) c.Pos = new Vector2(Mathf.Round(c.Pos.x * 100f) / 100f, Mathf.Round(c.Pos.y * 100f) / 100f);
                ApplySpawn(seed, kinds, effects, ph, list);
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"{LogPrefix} spawn failed: {e}");
            }
        }

        private static void ApplySpawn(int s, uint kinds, ulong effects, byte ph, List<Candy> list) {
            seed = s;
            roundKinds = kinds;
            roundEffects = effects;
            phase = ph;
            candies.Clear();
            candies.AddRange(list);
            EnsureMapping();
            TreatCabinets.OnSpawn();
            TreatFx.RebuildCandies();
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} part {ph}: {list.Count} candies " + string.Join(" ", list.Select(c => FormattableString.Invariant($"[{KindNames[c.Kind]} {c.Pos.x:F1},{c.Pos.y:F1}]"))));
        }

        // Random walkable spots. A point only counts when a player can actually get there: the free floor test alone
        // (no collider within the candy radius) also accepted points in the hollow space inside thick walls, which
        // has no collider of its own. So the host samples the room areas once per map and keeps only the points
        // that connect to a known reachable point (players, vents) through a chain of clear circle casts.
        private const float ReachRadius = 0.25f, ReachStep = 6.5f, UsableClear = 1.4f;
        internal static IntPtr reachShip;
        internal static readonly List<(Vector2 p, PlainShipRoom room)> reachable = new();

        internal static bool Blocked(Vector2 p, float r, int mask) {
            try {
                foreach (var c in Physics2D.OverlapCircleAll(p, r, mask)) if (c != null && !c.isTrigger) return true;
            } catch { return true; }
            return false;
        }

        internal static bool Clear(Vector2 a, Vector2 b, int mask) {
            var d = b - a;
            float len = d.magnitude;
            if (len < 0.01f) return true;
            try {
                foreach (var h in Physics2D.CircleCastAll(a, ReachRadius, d / len, len, mask))
                    if (h.collider != null && !h.collider.isTrigger) return false;
            } catch { return false; }
            return true;
        }

        internal static void BuildReachable(ShipStatus ship) {
            reachable.Clear();
            reachShip = ship.Pointer;
            int mask = Constants.ShipAndObjectsMask;
            var known = new List<Vector2>();
            try {
                foreach (var pc in PlayerControl.AllPlayerControls)
                    if (pc != null && pc.Data != null && !pc.Data.Disconnected) known.Add(pc.GetTruePosition());
            } catch { }
            try {
                foreach (var v in ship.AllVents) {
                    if (v == null) continue;
                    var c = (Vector2)v.transform.position;
                    // the line from the vent must be clear too: a vent close to a wall would otherwise seed a point
                    // behind it, in the void outside the room, and the chain grew from there (21.10., Skeld engines)
                    foreach (var off in new[] { new Vector2(0.7f, 0f), new Vector2(-0.7f, 0f), new Vector2(0f, -0.6f), new Vector2(0f, 0.6f) })
                        if (!Blocked(c + off, 0.3f, mask) && Clear(c, c + off, mask)) known.Add(c + off);
                }
            } catch { }
            var samples = new List<(Vector2 p, PlainShipRoom room)>();
            var rooms = new List<PlainShipRoom>();
            try { foreach (var r in ship.AllRooms) if (r != null && r.roomArea != null && r.RoomId != SystemTypes.Outside) rooms.Add(r); } catch { }
            foreach (var room in rooms) {
                var bb = room.roomArea.bounds;
                int want = Mathf.Clamp(Mathf.RoundToInt(bb.size.x * bb.size.y / 3f), 8, 60);
                for (int t = 0; t < want * 4 && want > 0; t++) {
                    var p = new Vector2(Mathf.Lerp(bb.min.x, bb.max.x, (float)rnd.NextDouble()), Mathf.Lerp(bb.min.y, bb.max.y, (float)rnd.NextDouble()));
                    if (!room.roomArea.OverlapPoint(p) || Blocked(p, 0.42f, mask)) continue;
                    samples.Add((p, room));
                    want--;
                }
            }
            // nothing next to something the Use button also wants (consoles, the emergency button, vents): the
            // vanilla target wins there and the candy could not be eaten (21.10., Midnight Bonbon at the Skeld button)
            var usable = new List<Vector2>();
            try { foreach (var c in UnityEngine.Object.FindObjectsOfType<Console>()) if (c != null) usable.Add(c.transform.position); } catch { }
            try { foreach (var c in UnityEngine.Object.FindObjectsOfType<SystemConsole>()) if (c != null) usable.Add(c.transform.position); } catch { }
            try { foreach (var v in ship.AllVents) if (v != null) usable.Add(v.transform.position); } catch { }
            int before = samples.Count;
            samples.RemoveAll(sp => usable.Any(u => (u - sp.p).sqrMagnitude < UsableClear * UsableClear));
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} spots: {before - samples.Count} sampled points dropped next to {usable.Count} usables");
            var open = new List<(Vector2 p, PlainShipRoom room)>(samples);
            for (int pass = 0; pass < 8 && open.Count > 0 && known.Count > 0; pass++) {
                int added = 0;
                for (int i = open.Count - 1; i >= 0; i--) {
                    var p = open[i].p;
                    var near = known.Where(k => (k - p).sqrMagnitude < ReachStep * ReachStep).OrderBy(k => (k - p).sqrMagnitude).Take(6);
                    if (!near.Any(k => Clear(k, p, mask))) continue;
                    known.Add(p);
                    reachable.Add(open[i]);
                    open.RemoveAt(i);
                    added++;
                }
                if (added == 0) break;
            }
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} spots: {reachable.Count} reachable of {samples.Count} sampled points in {rooms.Count} rooms");
        }

        private static List<Vector2> PickSpots(int n) {
            var spots = new List<Vector2>();
            var ship = ShipStatus.Instance;
            if (ship == null) return spots;
            if (reachShip != ship.Pointer || reachable.Count == 0) BuildReachable(ship);
            bool Spread(Vector2 p) {
                foreach (var s in spots) if ((s - p).sqrMagnitude < 2.5f * 2.5f) return false;
                return true;
            }
            // round-robin over the rooms in random order, a random reachable point of each
            var byRoom = reachable.GroupBy(x => x.room).Select(g => g.Select(x => x.p).OrderBy(_ => rnd.Next()).ToList()).OrderBy(_ => rnd.Next()).ToList();
            for (int pass = 0; pass < 6 && spots.Count < n && byRoom.Count > 0; pass++) {
                foreach (var list in byRoom) {
                    if (spots.Count >= n) break;
                    for (int i = 0; i < list.Count; i++) {
                        if (!Spread(list[i])) continue;
                        spots.Add(list[i]);
                        list.RemoveAt(i);
                        break;
                    }
                }
            }
            if (spots.Count < n) {
                // fallback: next to the vents (always walkable)
                try {
                    int mask = Constants.ShipAndObjectsMask;
                    var vents = ship.AllVents.ToArray().Where(v => v != null).OrderBy(_ => rnd.Next()).ToList();
                    foreach (var v in vents) {
                        if (spots.Count >= n) break;
                        var c = (Vector2)v.transform.position;
                        foreach (var off in new[] { new Vector2(0.7f, 0f), new Vector2(-0.7f, 0f), new Vector2(0f, -0.6f), new Vector2(0f, 0.6f) })
                            if (!Blocked(c + off, 0.42f, mask) && Clear(c, c + off, mask) && Spread(c + off)) { spots.Add(c + off); break; }
                    }
                } catch { }
            }
            return spots;
        }

        // ================================================================ eating
        internal static Candy NearestCandy(PlayerControl lp, out float dist) {
            dist = float.MaxValue;
            Candy best = null;
            if (lp == null) return null;
            var me = lp.GetTruePosition();
            foreach (var c in candies) {
                if (c.Eaten || c.Pending || c.Cab != TreatCabinets.None) continue;     // cabinet candies come out by searching
                float d = Vector2.Distance(me, c.Pos);
                if (d < dist) { dist = d; best = c; }
            }
            return best;
        }

        /// <summary>Local player presses Use next to a candy.</summary>
        internal static void RequestEat(Candy c) {
            var lp = PlayerControl.LocalPlayer;
            if (c == null || c.Eaten || c.Pending || !IsAlive(lp)) return;
            if (AmHost()) { HostEat(lp, phase, c.Index, null); return; }
            c.Pending = true;
            Send(SubEatReq, w => { w.Write(phase); w.Write(c.Index); });
        }

        /// <summary>Host: validate, resolve the random parts, tell everyone. forced = the self test picks the effect.</summary>
        internal static void HostEat(PlayerControl eater, byte ph, byte idx, Treat? forced) {
            try {
                if (!AmHost() || eater == null || !IsAlive(eater) || InMeeting()) return;
                if (forced.HasValue) { HostResolve(eater, phase, byte.MaxValue, forced.Value, byte.MaxValue); return; }
                if (ph != phase) return;
                var c = candies.FirstOrDefault(k => k.Index == idx);
                if (c == null || c.Eaten) return;
                float reach = c.Cab != TreatCabinets.None ? TreatCabinets.SearchRange() : Range();
                if (Vector2.Distance(eater.GetTruePosition(), c.Pos) > reach + 0.9f) return;   // latency slack
                if (c.Kind == PoisonKind) { HostPoison(eater, ph, idx); return; }
                // a Trick Candy (TrickOrTreatPlus.cs) looks like any other kind but always hinders
                var fx = TreatPlus.HostTakeTrick(c.Index) ? TreatPlus.HostTrickEffect() : EffectOf(c.Kind);
                HostResolve(eater, ph, idx, fx, c.Kind);
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"{LogPrefix} HostEat failed: {e}");
            }
        }

        // Effects that stand for another one: the card names the stand-in, the player gets the real one (P1).
        internal static bool IsStandIn(Treat fx) => fx == Treat.VolatileStarlight || fx == Treat.CopycatCaramel;

        /// <summary>Host: the candy is gone already (floor, cabinet, bag); roll the random parts and tell everyone.
        /// idx: the candy, 254 from the bag, 253 the Sugar Shock, 255 the self test.</summary>
        internal static void HostResolve(PlayerControl eater, byte ph, byte idx, Treat fx, byte kind) {
            byte p1 = byte.MaxValue, p2 = byte.MaxValue;
            if (fx == Treat.VolatileStarlight || fx == Treat.CopycatCaramel) {
                Treat real;
                if (fx == Treat.CopycatCaramel && TreatPlus.HostLastOtherEffect(eater.PlayerId, out var copied)) real = copied;
                else {
                    var pool = EffectPool(roundEffects).Where(t => !IsStandIn(t) && t != Treat.Regurgitate).ToList();
                    if (pool.Count == 0) pool = EffectPool(TreatSettings.AllEffects).Where(t => !IsStandIn(t) && t != Treat.Regurgitate).ToList();
                    real = pool[rnd.Next(pool.Count)];
                }
                p1 = (byte)real;
                p2 = RollParam(real, eater);
            } else p1 = RollParam(fx, eater);
            bool imp = IsImp(eater);
            byte pid = eater.PlayerId;
            Send(SubEaten, w => { w.Write(ph); w.Write(idx); w.Write(pid); w.Write((byte)fx); w.Write(p1); w.Write(p2); w.Write(imp); w.Write(kind); });
            ApplyEaten(ph, idx, pid, fx, p1, p2, imp, kind);
            var realFx = IsStandIn(fx) ? (Treat)p1 : fx;
            HostSideEffects(eater, realFx, imp);
            TreatPlus.HostAfterEat(eater, realFx, idx);
        }

        // ---- Midnight Bonbon: the eater dies on the spot, the body stays (a kill without a killer) ----
        // Host-authoritative through TOR's own UncheckedMurderPlayer (Helpers.MurderPlayer, victim = source = target,
        // no animation): every client runs TOR's MurderPlayer path, so the end-of-game check, the body, the ghost,
        // Lovers dying together and GameHistory work as for any kill. It never goes through checkMuderAttempt, so no
        // shield (Medic, Iron Taffy, Hard Candy, Armored, Time Master) stops it.
        internal static void HostPoison(PlayerControl eater, byte ph, byte idx) {
            try {
                if (!AmHost() || !IsAlive(eater) || InMeeting()) return;
                byte pid = eater.PlayerId;
                bool imp = IsImp(eater);
                Send(SubEaten, w => { w.Write(ph); w.Write(idx); w.Write(pid); w.Write(FxPoison); w.Write(byte.MaxValue); w.Write(byte.MaxValue); w.Write(imp); w.Write(PoisonKind); });
                ApplyEaten(ph, idx, pid, (Treat)FxPoison, byte.MaxValue, byte.MaxValue, imp, PoisonKind);
                if (FreePlay()) {
                    HideNextKillAnimation();
                    eater.MurderPlayer(eater, MurderResultFlags.Succeeded);
                } else Helpers.MurderPlayer(eater, eater, false);
                HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {eater.Data?.PlayerName} ate the Midnight Bonbon and died.");
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} poison failed: {e}"); }
        }

        private static System.Reflection.FieldInfo hideAnimField, firstKillField;
        private static void HideNextKillAnimation() {
            try {
                hideAnimField ??= AccessTools.Field(AccessTools.TypeByName("TheOtherRoles.Patches.KillAnimationCoPerformKillPatch"), "hideNextAnimation");
                hideAnimField?.SetValue(null, true);
            } catch { }
        }

        // TOR's MurderPlayer postfix treats the self kill as a kill by the victim: undo what makes no sense for a candy.
        private static string firstKillBefore;
        [HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.MurderPlayer))]
        static class PoisonMurderPatch {
            [HarmonyPriority(Priority.First)]
            public static void Prefix([HarmonyArgument(0)] PlayerControl target) {
                try {
                    if (target == null || !poisoned.Contains(target.PlayerId)) return;
                    firstKillField ??= AccessTools.Field(AccessTools.TypeByName("TheOtherRoles.TORMapOptions"), "firstKillName");
                    firstKillBefore = firstKillField?.GetValue(null) as string;
                } catch { }
            }
            [HarmonyPriority(Priority.Last)]
            public static void Postfix(PlayerControl __instance, [HarmonyArgument(0)] PlayerControl target) {
                try {
                    if (target == null || __instance == null || __instance.PlayerId != target.PlayerId || !poisoned.Contains(target.PlayerId)) return;
                    // the first-kill shield of the next game is for a player an impostor picked, not for a candy victim
                    if (string.IsNullOrEmpty(firstKillBefore) && firstKillField != null) firstKillField.SetValue(null, "");
                    // a Bait would "report" its own body from the grave
                    foreach (var k in Bait.active.Keys.ToList()) if (k.player != null && k.player.PlayerId == target.PlayerId) Bait.active.Remove(k);
                } catch { }
            }
        }

        // No kill cutscene for the candy victim (it would show him killing himself, in a costume scene even).
        // First, so the costume hook (which honours __runOriginal) stays quiet as well.
        [HarmonyPatch(typeof(KillOverlay), nameof(KillOverlay.ShowKillAnimation), typeof(NetworkedPlayerInfo), typeof(NetworkedPlayerInfo))]
        static class PoisonOverlayPatch {
            [HarmonyPriority(Priority.First)]
            public static bool Prefix([HarmonyArgument(0)] NetworkedPlayerInfo killer, [HarmonyArgument(1)] NetworkedPlayerInfo victim) {
                try {
                    if (killer != null && victim != null && killer.PlayerId == victim.PlayerId && poisoned.Contains(victim.PlayerId)) return false;
                } catch { }
                return true;
            }
        }

        // Ghost and end-screen role lines: "killed by <himself>" becomes the candy.
        [HarmonyPatch(typeof(RoleInfo), nameof(RoleInfo.GetRolesString))]
        static class PoisonRoleStringPatch {
            public static void Postfix(PlayerControl p, ref string __result) {
                try {
                    if (poisoned.Count == 0 || p == null || __result == null || !poisoned.Contains(p.PlayerId) || p.Data == null || !p.Data.IsDead) return;
                    int i = __result.IndexOf(" - killed by ", StringComparison.Ordinal);
                    if (i >= 0) __result = __result.Substring(0, i) + " - <color=#B98CFF>Midnight Bonbon</color>";
                } catch { }
            }
        }

        private static byte RollParam(Treat fx, PlayerControl eater) {
            switch (fx) {
                case Treat.SwapSweet: {
                    var others = PlayerControl.AllPlayerControls.ToArray().Where(p => IsAlive(p) && p.PlayerId != eater.PlayerId).ToList();
                    return others.Count == 0 ? byte.MaxValue : others[rnd.Next(others.Count)].PlayerId;
                }
                case Treat.NothingQ: return (byte)rnd.Next(4);
                default: return byte.MaxValue;
            }
        }

        // Things only the host can do: the shared sabotage timer and the server-visible task list.
        private static void HostSideEffects(PlayerControl eater, Treat fx, bool imp) {
            try {
                if (fx == Treat.PrizeInside && imp) {
                    var sab = GetSab();
                    if (sab != null) { sab.Timer = 0f; sab.IsDirty = true; }      // dirty: the guests' sabotage menus hear it too (audit M-5)
                    HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} Prize Inside: sabotage cooldown reset ({(sab != null ? "ok" : "no system")}).");
                } else if (fx == Treat.ExtraChore && !imp) {
                    HostExtraTask(eater);
                }
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} host side effect failed: {e.Message}"); }
        }

        private static SabotageSystemType GetSab() {
            var ship = ShipStatus.Instance;
            if (ship == null || ship.Systems == null) return null;
            if (!ship.Systems.TryGetValue(SystemTypes.Sabotage, out ISystemType sys) || sys == null) return null;
            return sys.TryCast<SabotageSystemType>();
        }

        // Extra Chore: rebuild the eater's list with one more short task (the Gambler/Auditor path: PlayerTuning's
        // HUD teardown plus the vanilla RpcSetTasks the server sees), then the eater re-completes what was done.
        private static void HostExtraTask(PlayerControl p) {
            var data = p?.Data;
            var ship = ShipStatus.Instance;
            if (data == null || data.Tasks == null || ship == null) return;
            var have = new List<byte>();
            var done = new List<uint>();
            for (int i = 0; i < data.Tasks.Count; i++) {
                var t = data.Tasks[i];
                if (t == null) return;
                have.Add(t.TypeId);
                if (t.Complete) done.Add(t.Id);
            }
            var pool = new List<byte>();
            void AddPool(Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<NormalPlayerTask> arr) {
                if (arr == null) return;
                foreach (var t in arr) if (t != null && !have.Contains((byte)t.Index)) pool.Add((byte)t.Index);
            }
            AddPool(ship.ShortTasks);
            if (pool.Count == 0) AddPool(ship.LongTasks);
            if (pool.Count == 0) { HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} Extra Chore: no free task left."); return; }
            have.Add(pool[rnd.Next(pool.Count)]);
            bool ok = PlayerTuning.SendSetTasks(p.PlayerId, have.ToArray());
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} Extra Chore for {data.PlayerName}: {(ok ? "task added" : "refused")} ({have.Count} tasks, {done.Count} to re-complete).");
            if (!ok) return;
            var ids = done.Take(255).ToList();
            byte pid = p.PlayerId;
            Send(SubRecomplete, w => { w.Write(pid); w.Write((byte)ids.Count); foreach (var id in ids) w.Write(id); });
            ApplyRecomplete(pid, ids);
        }

        // The eater's own client re-completes once the reset has landed (Gambler's RecompleteTick).
        private static readonly List<uint> recompleteIds = new();
        private static float recompleteSince = -1f;
        private static void ApplyRecomplete(byte pid, List<uint> ids) {
            var lp = PlayerControl.LocalPlayer;
            if (lp == null || lp.PlayerId != pid || ids.Count == 0) return;
            recompleteIds.Clear();
            recompleteIds.AddRange(ids);
            recompleteSince = Time.time;
        }

        private static void RecompleteTick() {
            if (recompleteIds.Count == 0) return;
            var me = PlayerControl.LocalPlayer;
            if (me == null || me.Data == null || me.Data.Tasks == null || me.myTasks == null) return;
            bool landed = true;
            foreach (uint id in recompleteIds) {
                var info = me.Data.FindTaskById(id);
                if (info == null || info.Complete) landed = false;
                bool obj = false;
                foreach (var t in me.myTasks) if (t != null && t.Id == id) { obj = true; break; }
                if (!obj) landed = false;
            }
            if (!landed && Time.time - recompleteSince < 3f) return;
            int n = 0;
            foreach (uint id in recompleteIds) {
                var info = me.Data.FindTaskById(id);
                if (info == null || info.Complete) continue;
                try { me.RpcCompleteTask(id); n++; } catch { }
            }
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} re-completed {n}/{recompleteIds.Count} task(s) after the Extra Chore.");
            recompleteIds.Clear();
        }

        // ================================================================ applying an eaten candy (every client)
        private static void ApplyEaten(byte ph, byte idx, byte pid, Treat fx, byte p1, byte p2, bool imp, byte kind) {
            var c = idx >= TreatPlus.IdxSugarShock ? null : candies.FirstOrDefault(k => k.Index == idx);
            if (c != null && ph == phase) { c.Eaten = true; c.Pending = false; TreatFx.RemoveCandy(c); }
            if (idx == TreatPlus.IdxBag) TreatPlus.RemoveFromBag(pid, kind);
            var p = Helpers.playerById(pid);
            if (p == null) return;
            if (idx != TreatPlus.IdxSugarShock) { try { HwTitles.OnCandyEaten(pid, (byte)fx == FxPoison); } catch { } }   // titles of the evening (HwTitles.cs)
            bool local = PlayerControl.LocalPlayer != null && PlayerControl.LocalPlayer.PlayerId == pid;
            if ((byte)fx == FxPoison) {
                poisoned.Add(pid);
                if (local) { TreatFx.Munch(); TreatFx.ShowPoisonCard(); }
                HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {p.Data?.PlayerName} ate the Midnight Bonbon.");
                return;
            }
            string kindName = idx == TreatPlus.IdxSugarShock ? TreatPlus.SugarShockName() : kind < KindNames.Length ? KindNames[kind] : "Test Candy";
            Treat shown = fx;
            Treat real = fx;
            byte param = p1;
            if (IsStandIn(fx)) { real = (Treat)p1; param = p2; }
            string extra = null;

            if (real == Treat.Regurgitate) {
                bool undone = false;
                if (lastCandy.TryGetValue(pid, out var last) && last != null && List(pid).Contains(last)) {
                    End(last, "regurgitated");
                    undone = true;
                }
                lastCandy.Remove(pid);
                extra = undone ? null : (De() ? "Da war nichts, was wieder hochkommen konnte." : "There was nothing to bring back up.");
            } else {
                var a = Start(p, real, imp, param, ref extra);
                lastCandy[pid] = a;     // null for one-shot effects: nothing left to undo
            }
            if (local) {
                TreatFx.Munch();
                TreatFx.ShowPopup(kind < KindNames.Length ? kind : (byte)0, kindName, shown, real, imp, param, extra);
            }
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {p.Data?.PlayerName} ate {kindName}: {shown}{(shown != real ? " as " + real : "")}{(imp ? " (impostor)" : "")}.");
        }

        internal static List<ActiveTreat> List(byte pid) {
            if (!active.TryGetValue(pid, out var l)) { l = new List<ActiveTreat>(); active[pid] = l; }
            return l;
        }

        internal static float Seconds(Treat fx) {
            switch (fx) {
                case Treat.SugarRush: return 5f;
                case Treat.GuidingMint: return 20f;
                case Treat.EchoDrop: return 10f;
                case Treat.RockCandy: return 30f;
                case Treat.FogFudge: return 60f;
                case Treat.Hiccups: return 60f;
                case Treat.LightsOut: return 10f;
                case Treat.Earmuffs: return 60f;
                case Treat.Jinkies: return 20f;
                case Treat.Butterfingers: return 30f;
                case Treat.Glowing: return 60f;
                case Treat.CrowCompany: return 30f;
                case Treat.Nausea: return 20f;
                case Treat.NothingQ: return 12f;
                case Treat.SwapSweet: return 30f;
                case Treat.CandyCornCompass: return 15f;
                case Treat.PeekAPop: return 5f;
                case Treat.FizzPop: return 15f;
                case Treat.BrainFreeze: return 3f;
                case Treat.ReverseGummy: return 10f;
                case Treat.WrapperTrail: return 30f;
                case Treat.SugarCrash: return 40f;
                case Treat.GhostlyGum: return 20f;
                case Treat.DoubleDip: case Treat.TattletaleTaffy: return float.MaxValue;   // until the next meeting is over
                default: return 0f;
            }
        }

        internal static bool IsRound(Treat fx) =>
            fx == Treat.IronTaffy || fx == Treat.CinnamonStick || fx == Treat.NightOwl || fx == Treat.Gobstopper
            || fx == Treat.HardCandy || fx == Treat.Brittle || fx == Treat.ShrinkSherbet || fx == Treat.BigBite
            || fx == Treat.StickyToffee || fx == Treat.VentMint || fx == Treat.HomingHumbug;

        /// <summary>Lives through the next meeting and ends when it is over (the vote, the meeting report).</summary>
        internal static bool IsMeetingBound(Treat fx) => fx == Treat.DoubleDip || fx == Treat.TattletaleTaffy;

        private static ActiveTreat Start(PlayerControl p, Treat fx, bool imp, byte param, ref string extra) {
            bool local = p == PlayerControl.LocalPlayer;
            // one-shot effects
            switch (fx) {
                case Treat.ShortcutCaramel:
                    if (local) { if (imp) KillTimerDelta(-2.5f); else extra = CompleteRandomTask(); }
                    return null;
                case Treat.PrizeInside:
                    if (local && !imp) extra = RandomTaskStep();
                    return null;
                case Treat.ExtraChore:
                    if (local && imp) KillTimerDelta(2.5f);
                    return null;
                case Treat.LuckyLolly:
                    try { p.RemainingEmergencies++; } catch { }
                    return null;
            }
            // the same effect again just refreshes the running one
            var list = List(p.PlayerId);
            var a = list.FirstOrDefault(x => x.Fx == fx);
            if (a == null) {
                a = new ActiveTreat { Owner = p.PlayerId, Fx = fx, Imp = imp, P1 = param, Started = Time.time };
                list.Add(a);
                OnBegin(p, a, ref extra);
            } else {
                a.Used = false;
                a.Imp = imp;
                if (fx == Treat.SwapSweet && param != a.P1) { a.P1 = param; OnBegin(p, a, ref extra); }
            }
            a.Round = IsRound(fx);
            a.Left = Seconds(fx);
            a.Meetings = MeetingsFor();
            if (fx == Treat.GuidingMint && local && !TreatFx.AnyBody()) {
                extra = De() ? "Hier gibt es nichts zu finden." : "There is nothing to find.";
                list.Remove(a);
                return null;
            }
            return a;
        }

        private static void OnBegin(PlayerControl p, ActiveTreat a, ref string extra) {
            switch (a.Fx) {
                case Treat.Gobstopper:
                    try { a.Saved = p.RemainingEmergencies; p.RemainingEmergencies = 0; } catch { }
                    break;
                case Treat.SwapSweet: {
                    var t = Helpers.playerById(a.P1);
                    if (t != null && t.Data != null) {
                        var o = t.Data.DefaultOutfit;
                        try { p.setLook(o.PlayerName, o.ColorId, o.HatId, o.VisorId, o.SkinId, o.PetId); } catch { }
                    } else extra = De() ? "Niemand da, mit dem du tauschen könntest." : "Nobody around to swap with.";
                    break;
                }
                case Treat.Hiccups:
                    a.Next = Time.time + 1.2f;
                    break;
                default:
                    TreatPlus.OnBegin(p, a, ref extra);
                    break;
            }
        }

        /// <summary>Ends an effect on this client (every client calls it for the same reasons).</summary>
        internal static void End(ActiveTreat a, string why) {
            if (a == null) return;
            if (active.TryGetValue(a.Owner, out var l)) l.Remove(a);
            var p = Helpers.playerById(a.Owner);
            try {
                switch (a.Fx) {
                    case Treat.Gobstopper:
                        if (p != null && a.Saved >= 0) p.RemainingEmergencies = Math.Max(p.RemainingEmergencies, a.Saved);
                        break;
                    case Treat.SwapSweet:
                        if (p != null && !TorLookActive(p)) p.setDefaultLook();
                        break;
                    case Treat.ShrinkSherbet:
                    case Treat.BigBite:
                        if (p != null && SizeFactor(p.PlayerId) == 1f) RestoreSize(p);
                        break;
                }
            } catch { }
            TreatPlus.OnEnd(p, a);
            TreatFx.OnEnd(a);
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {a.Fx} of player {a.Owner} ended ({why}).");
        }

        private static void EndAll(byte pid, string why) {
            if (!active.TryGetValue(pid, out var l)) return;
            foreach (var a in l.ToList()) End(a, why);
        }

        internal static bool Has(byte pid, Treat fx) => active.TryGetValue(pid, out var l) && l.Any(a => a.Fx == fx && !a.Used);
        internal static ActiveTreat Get(byte pid, Treat fx) => active.TryGetValue(pid, out var l) ? l.FirstOrDefault(a => a.Fx == fx && !a.Used) : null;

        // ---- one-shot helpers (eater's own client) ----
        private static string CompleteRandomTask() {
            var me = PlayerControl.LocalPlayer;
            var open = OpenTasks(me);
            if (open.Count == 0) return De() ? "Du hattest keine offene Aufgabe mehr." : "You had no open task left.";
            var t = open[rnd.Next(open.Count)];
            try { me.RpcCompleteTask(t.Id); } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} complete task: {e.Message}"); }
            return TaskName(t);
        }

        private static string RandomTaskStep() {
            var me = PlayerControl.LocalPlayer;
            var open = OpenTasks(me);
            if (open.Count == 0) return De() ? "Du hattest keine offene Aufgabe mehr." : "You had no open task left.";
            var t = open[rnd.Next(open.Count)];
            try { t.NextStep(); } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} task step: {e.Message}"); }
            return TaskName(t);
        }

        private static string TaskName(PlayerTask t) {
            try {
                string n = DestroyableSingleton<TranslationController>.Instance.GetString(t.TaskType);
                return "(" + n + ")";
            } catch { return null; }
        }

        internal static List<NormalPlayerTask> OpenTasks(PlayerControl me) {
            var res = new List<NormalPlayerTask>();
            if (me == null || me.myTasks == null) return res;
            foreach (var t in me.myTasks) {
                if (t == null || t.IsComplete) continue;
                var n = t.TryCast<NormalPlayerTask>();
                if (n == null) continue;
                try { if (PlayerTask.TaskIsEmergency(t)) continue; } catch { }
                res.Add(n);
            }
            return res;
        }

        private static float pendingKillDelta;
        private static void KillTimerDelta(float d) {
            var lp = PlayerControl.LocalPlayer;
            if (lp == null) return;
            if (d > 0f || lp.killTimer > 0.05f) ApplyKillDelta(d);
            else pendingKillDelta += d;          // ready right now: the next cooldown gets the cut
        }

        private static void ApplyKillDelta(float d) {
            var lp = PlayerControl.LocalPlayer;
            try {
                float max = GameOptionsManager.Instance.currentNormalGameOptions.KillCooldown;
                lp.killTimer = Mathf.Max(0f, lp.killTimer + d);
                if (HudManager.InstanceExists) HudManager.Instance.KillButton.SetCoolDown(lp.killTimer, Mathf.Max(max, lp.killTimer));
                HalloweenPlugin.Logger?.LogInfo(FormattableString.Invariant($"{LogPrefix} kill cooldown {d:+0.0;-0.0} s -> {lp.killTimer:F1} s"));
            } catch { }
        }

        // ================================================================ queries for the patches
        internal static float SpeedMult(byte pid) {
            if (!active.TryGetValue(pid, out var l) || l.Count == 0) return TreatPlus.StuckMult(pid);
            float m = 1f;
            foreach (var a in l) {
                switch (a.Fx) {
                    case Treat.SugarRush: m *= 1.4f; break;
                    case Treat.CinnamonStick: m *= 1.08f; break;
                    case Treat.RockCandy: m *= 0.7f; break;
                    case Treat.HardCandy: m *= 0.9f; break;
                    case Treat.Brittle: m *= 1.15f; break;
                    case Treat.Nausea: m *= 1.2f; break;
                    case Treat.ShrinkSherbet: m *= 1.05f; break;
                    case Treat.BigBite: m *= 0.95f; break;
                    case Treat.BrainFreeze: m = 0f; break;
                    case Treat.SugarCrash: m *= a.Left > 20f ? 1.3f : 0.7f; break;
                }
            }
            return m * TreatPlus.StuckMult(pid);
        }

        internal static float VisionMult(byte pid, out bool lightsOut) {
            lightsOut = false;
            if (!active.TryGetValue(pid, out var l) || l.Count == 0) return 1f;
            float m = 1f;
            foreach (var a in l) {
                switch (a.Fx) {
                    case Treat.NightOwl: m *= 1.2f; break;
                    case Treat.FogFudge: m *= 0.75f; break;
                    case Treat.Brittle: m *= 0.8f; break;
                    case Treat.LightsOut: lightsOut = true; break;
                    case Treat.NothingQ: if (a.P1 == 1) m *= 0.4f; break;     // the fake lights sabotage
                }
            }
            return m;
        }

        internal static float SizeFactor(byte pid) {
            if (!active.TryGetValue(pid, out var l) || l.Count == 0) return 1f;
            float m = 1f;
            foreach (var a in l) {
                if (a.Fx == Treat.ShrinkSherbet) m *= 0.78f;
                else if (a.Fx == Treat.BigBite) m *= 1.25f;
            }
            return m;
        }

        // Which candy shield (if any) stops this kill. Iron Taffy (crew) and Hard Candy stop any kill, the impostor's
        // Iron Taffy only a Sheriff shot.
        internal static ActiveTreat ShieldFor(PlayerControl killer, PlayerControl target) {
            if (target == null || !active.TryGetValue(target.PlayerId, out var l)) return null;
            bool sheriff = false;
            try { sheriff = killer != null && Sheriff.sheriff != null && killer.PlayerId == Sheriff.sheriff.PlayerId; } catch { }
            foreach (var a in l) {
                if (a.Used) continue;
                if (a.Fx == Treat.HardCandy) return a;
                if (a.Fx == Treat.IronTaffy && (!a.Imp || sheriff)) return a;
            }
            return null;
        }

        internal static bool KillBlocked(PlayerControl killer) {
            if (killer == null) return false;
            var a = Get(killer.PlayerId, Treat.Butterfingers);
            return a != null && a.Imp;
        }

        /// <summary>A shield took the kill: tell everyone (the killer's client calls this).</summary>
        internal static void UseShield(PlayerControl killer, PlayerControl target, ActiveTreat a) {
            a.Used = true;
            byte tid = target.PlayerId, fx = (byte)a.Fx;
            Send(SubShield, w => { w.Write(tid); w.Write(fx); });
            ApplyShieldUsed(tid, a.Fx, true);
            try { target.ShowFailedMurder(); } catch { }
        }

        private static void ApplyShieldUsed(byte target, Treat fx, bool fromHere) {
            var a = active.TryGetValue(target, out var l) ? l.FirstOrDefault(x => x.Fx == fx) : null;
            if (a == null) return;
            a.Used = true;
            if (fx == Treat.IronTaffy) End(a, "shield used");          // Hard Candy keeps its speed malus for the round
            var lp = PlayerControl.LocalPlayer;
            if (lp != null && lp.PlayerId == target) TreatFx.ShieldFlash(fx);
            if (!fromHere) { try { Helpers.playerById(target)?.ShowFailedMurder(); } catch { } }
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {fx} of player {target} stopped a kill.");
        }

        private static bool TorLookActive(PlayerControl p) {
            try {
                if (Camouflager.camouflageTimer > 0f || Helpers.MushroomSabotageActive()) return true;
                if (Morphling.morphTimer > 0f && Morphling.morphling == p) return true;
            } catch { }
            return false;
        }

        private static void RestoreSize(PlayerControl p) {
            try {
                p.transform.localScale = new Vector3(0.7f, 0.7f, 1f);
                var col = p.Collider.CastFast<CircleCollider2D>();
                if (col != null) col.radius = Mini.defaultColliderRadius;
            } catch { }
        }

        // ================================================================ tick (every frame, every client)
        internal static void Tick() {
            try {
                TreatSettings.Tick();
                TreatMenu.Tick();
                TrickOrTreatDiag.Tick();
                if (!InRound()) {
                    if (candies.Count > 0 || active.Count > 0 || TreatCabinets.Any || TreatPlus.Any) FullReset();
                    return;
                }
                if (!On()) { if (candies.Count > 0 || active.Count > 0 || TreatCabinets.Any || TreatPlus.Any) FullReset(); return; }
                if (InMeeting()) {
                    wasMeeting = true;
                    TreatFx.Tick(true);
                    TreatPlus.Tick(true);
                    return;
                }
                if (wasMeeting) {
                    wasMeeting = false;
                    foreach (var kv in active.ToList())
                        foreach (var a in kv.Value.ToList()) if (IsMeetingBound(a.Fx)) End(a, "meeting over");
                    TreatPlus.OnMeetingEnd();
                    if (AmHost()) HostSpawn();
                }
                float dt = Time.deltaTime;
                foreach (var kv in active.ToList()) {
                    var p = Helpers.playerById(kv.Key);
                    if (!IsAlive(p)) { if (kv.Value.Count > 0) EndAll(kv.Key, "eater died"); continue; }
                    foreach (var a in kv.Value.ToList()) {
                        if (a.Round) continue;
                        a.Left -= dt;
                        if (a.Left <= 0f) End(a, "time up");
                    }
                }
                if (pendingKillDelta != 0f) {
                    var lp = PlayerControl.LocalPlayer;
                    if (lp != null && lp.killTimer > 0.05f) { ApplyKillDelta(pendingKillDelta); pendingKillDelta = 0f; }
                }
                RecompleteTick();
                TreatFx.Tick(false);
                TreatPlus.Tick(false);
                TreatUse.Tick();
            } catch (Exception e) {
                if (!tickErrorLogged) { tickErrorLogged = true; HalloweenPlugin.Logger?.LogError($"{LogPrefix} tick failed (logged once): {e}"); }
            }
        }
        private static bool tickErrorLogged;

        /// <summary>Meeting start: timed effects end, whole-round effects count one meeting down, the candies go.</summary>
        internal static void OnMeetingStart() {
            TreatPlus.OnMeetingStart();
            foreach (var kv in active.ToList())
                foreach (var a in kv.Value.ToList()) {
                    if (IsMeetingBound(a.Fx)) continue;          // ends when the meeting is over
                    if (!a.Round) { End(a, "meeting"); continue; }
                    a.Meetings--;
                    if (a.Meetings <= 0) End(a, "meetings over");
                }
            candies.Clear();
            TreatCabinets.CancelSearch();
            TreatFx.RebuildCandies();
        }

        internal static void FullReset() {
            foreach (var kv in active.ToList()) EndAll(kv.Key, "reset");
            active.Clear();
            lastCandy.Clear();
            poisoned.Clear();
            candies.Clear();
            seed = 0;
            phase = 0;
            mappedKey = long.MinValue;
            wasMeeting = false;
            pendingKillDelta = 0f;
            recompleteIds.Clear();
            TreatFx.Clear();
            TreatPlus.Clear();
            TreatCabinets.Clear();
            TreatUse.Release();
        }

        // ================================================================ patches
        [HarmonyPatch(typeof(RPCProcedure), nameof(RPCProcedure.resetVariables))]
        static class ResetPatch {
            static bool Prepare() { Boot(); return true; }
            public static void Postfix() {
                try { FullReset(); } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} round reset failed: {e}"); }
            }
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined))]
        static class LobbyResetPatch {
            public static void Postfix() { try { FullReset(); } catch { } }
        }

        [HarmonyPatch(typeof(IntroCutscene), nameof(IntroCutscene.OnDestroy))]
        static class IntroEndPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix() {
                try {
                    if (AmHost() && On()) HostSpawn();
                } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} intro spawn failed: {e}"); }
            }
        }

        [HarmonyPatch(typeof(MeetingHud), nameof(MeetingHud.Start))]
        static class MeetingStartPatch {
            public static void Postfix() { try { if (On()) OnMeetingStart(); } catch { } }
        }

        // ---- speed: velocity multiply on the owner and on the remote prediction (the Giant pattern) ----
        [HarmonyPatch(typeof(PlayerPhysics), nameof(PlayerPhysics.FixedUpdate))]
        static class SpeedOwnerPatch {
            public static void Postfix(PlayerPhysics __instance) {
                try {
                    if (!__instance.AmOwner || __instance.myPlayer == null || __instance.myPlayer.Data == null) return;
                    TrickOrTreatDiag.DriveWalk(__instance);
                    if (active.Count == 0 && !TreatPlus.AnyStuck) return;
                    if (__instance.myPlayer.Data.IsDead || !__instance.myPlayer.CanMove) return;
                    byte pid = __instance.myPlayer.PlayerId;
                    if (Has(pid, Treat.ReverseGummy)) __instance.body.velocity = -__instance.body.velocity;   // the owner's input only
                    float m = SpeedMult(pid);
                    if (Mathf.Abs(m - 1f) < 0.0001f) return;
                    __instance.body.velocity *= m;
                } catch { }
            }
        }

        [HarmonyPatch(typeof(CustomNetworkTransform), nameof(CustomNetworkTransform.FixedUpdate))]
        static class SpeedRemotePatch {
            public static void Postfix(CustomNetworkTransform __instance) {
                try {
                    if ((active.Count == 0 && !TreatPlus.AnyStuck) || __instance.AmOwner || __instance.myPlayer == null || __instance.myPlayer.Data == null) return;
                    float m = SpeedMult(__instance.myPlayer.PlayerId);
                    if (Mathf.Abs(m - 1f) < 0.0001f || __instance.myPlayer.Data.IsDead) return;
                    __instance.body.velocity *= m;
                } catch { }
            }
        }

        // ---- vision: multiplicative, after UC's pipeline ----
        [HarmonyPatch(typeof(ShipStatus), nameof(ShipStatus.CalculateLightRadius))]
        static class VisionPatch {
            [HarmonyPriority(Priority.LowerThanNormal)]
            public static void Postfix(ref float __result, ShipStatus __instance, [HarmonyArgument(0)] NetworkedPlayerInfo p) {
                try {
                    if (active.Count == 0 || p == null || p.IsDead || __instance == null) return;
                    float m = VisionMult(p.PlayerId, out bool dark);
                    if (m != 1f) __result *= m;
                    if (dark) __result = Mathf.Min(__result, __instance.MinLightRadius * 0.6f);
                } catch { }
            }
        }

        // ---- size: after TOR's per-frame size reset and the Giant ----
        [HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.FixedUpdate))]
        static class SizePatch {
            [HarmonyPriority(Priority.Last)]
            public static void Postfix(PlayerControl __instance) {
                try {
                    if (active.Count == 0 || __instance == null) return;
                    float f = SizeFactor(__instance.PlayerId);
                    if (f == 1f) return;
                    if (Camouflager.camouflageTimer > 0f || Helpers.MushroomSabotageActive()) return;
                    if (Mini.mini != null && Mini.mini.PlayerId == __instance.PlayerId) return;
                    float scale = 0.7f * f;
                    __instance.transform.localScale = new Vector3(scale, scale, 1f);
                    var col = __instance.Collider.CastFast<CircleCollider2D>();
                    if (col != null) col.radius = Mini.defaultColliderRadius * 0.7f / scale;   // the body keeps its vanilla footprint
                } catch { }
            }
        }

        // ---- shields + Butterfingers on the kill check (the Medic's choke point) ----
        [HarmonyPatch(typeof(Helpers), nameof(Helpers.checkMuderAttempt))]
        static class KillCheckPatch {
            public static void Postfix([HarmonyArgument(0)] PlayerControl killer, [HarmonyArgument(1)] PlayerControl target, ref MurderAttemptResult __result) {
                try {
                    if (active.Count == 0 || __result != MurderAttemptResult.PerformKill) return;
                    // the Bomber probes checkMuderAttempt(bomber, bomber) before planting: not a kill (audit M-6)
                    if (killer != null && target != null && killer.PlayerId == target.PlayerId) return;
                    if (KillBlocked(killer)) { __result = MurderAttemptResult.SuppressKill; return; }
                    var a = ShieldFor(killer, target);
                    if (a == null) return;
                    UseShield(killer, target, a);
                    __result = MurderAttemptResult.BlankKill;     // the kill cooldown resets, like a blank
                } catch { }
            }
        }

        // Fallback on the Il2Cpp kill button (tiering can drop the managed detour above, see Copycat).
        [HarmonyPatch(typeof(KillButton), nameof(KillButton.DoClick))]
        static class KillButtonPatch {
            [HarmonyPriority(Priority.First)]
            public static void Prefix(KillButton __instance) {
                try {
                    if (active.Count == 0 || __instance == null) return;
                    var lp = PlayerControl.LocalPlayer;
                    var target = __instance.currentTarget;
                    if (lp == null || target == null || __instance.isCoolingDown) return;
                    if (KillBlocked(lp)) { __instance.currentTarget = null; return; }
                    var a = ShieldFor(lp, target);
                    if (a == null) return;
                    UseShield(lp, target, a);
                    __instance.currentTarget = null;
                    lp.SetKillTimer(GameOptionsManager.Instance.currentNormalGameOptions.KillCooldown);
                } catch { }
            }
        }

        // ---- Butterfingers: no tasks (crew), no vents (impostor). Postfixes: TOR's prefixes on both would win otherwise ----
        [HarmonyPatch(typeof(Console), nameof(Console.CanUse))]
        static class ConsolePatch {
            public static void Postfix(Console __instance, [HarmonyArgument(0)] NetworkedPlayerInfo pc, ref bool canUse, ref bool couldUse, ref float __result) {
                try {
                    if (active.Count == 0 || pc == null || pc.Object == null || !couldUse) return;
                    var a = Get(pc.PlayerId, Treat.Butterfingers);
                    if (a == null || a.Imp) return;
                    var task = __instance.FindTask(pc.Object);
                    if (task == null || task.TryCast<NormalPlayerTask>() == null) return;      // sabotage fixes stay open
                    canUse = couldUse = false;
                    __result = float.MaxValue;
                } catch { }
            }
        }

        [HarmonyPatch(typeof(Vent), nameof(Vent.CanUse))]
        static class VentPatch {
            public static void Postfix([HarmonyArgument(0)] NetworkedPlayerInfo pc, ref bool canUse, ref bool couldUse, ref float __result) {
                try {
                    if (active.Count == 0 || pc == null || pc.Object == null || pc.Object.inVent) return;    // never lock anyone in
                    var a = Get(pc.PlayerId, Treat.Butterfingers);
                    if (a == null || !a.Imp) return;
                    canUse = couldUse = false;
                    __result = float.MaxValue;
                } catch { }
            }
        }

        // The fake sabotage line in the task list (Nothing?): TOR deletes foreign ImportantTextTasks every frame,
        // so the line goes into the text instead.
        [HarmonyPatch(typeof(TaskPanelBehaviour), nameof(TaskPanelBehaviour.SetTaskText))]
        static class TaskTextPatch {
            public static void Prefix([HarmonyArgument(0)] ref string str) {
                try {
                    string line = TreatFx.FakeTaskLine();
                    if (!string.IsNullOrEmpty(line)) str = line + "\n" + str;
                } catch { }
            }
        }

        // ---- self test hooks ----
        internal static void DiagEat(Treat fx) => HostEat(PlayerControl.LocalPlayer, phase, byte.MaxValue, fx);
        internal static void DiagEatAs(PlayerControl p, Treat fx) => HostEat(p, phase, byte.MaxValue, fx);
        internal static void DiagMeeting() { OnMeetingStart(); wasMeeting = true; }
        internal static string DiagState() => string.Join("; ", active.Where(kv => kv.Value.Count > 0).Select(kv =>
            $"{kv.Key}: " + string.Join(",", kv.Value.Select(a => a.Round ? $"{a.Fx}({a.Meetings}m{(a.Used ? " used" : "")})" : FormattableString.Invariant($"{a.Fx}({a.Left:F0}s)")))));
    }
}
