// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld.UpperDiag - Autotests fuer das Obergeschoss (Hitbox-Durchgang und eigene Aufgaben, 18.11.). Nur im Freeplay-Autotest
// (AtlasMaps.AutotestRun) mit UC_HALLOWEEN_DIAG:
//   upprobe   : Kollisions-Raster wie im Spiel (Physics2D.OverlapCircleAll mit dem Spielerkreis, ohne Trigger) fuer das Obergeschoss und
//               die beiden Treppenfuesse; Logzeilen "probe hdr <name> x0 y0 step nx ny" und "probe row <name> <j> <Laengen frei/belegt>"
//               (Audits/2026-11-18/hitbox/upper_hitbox.py legt sie ueber die Grafik)
//   upwalk    : echter Rundgang mit Physik (Geschwindigkeit wie ein Spieler, Kollision zaehlt) durch alle Raeume oben, Treppe hinunter,
//               Fotos je Raum; bleibt der Spieler haengen: "STUCK" mit Lage
//   stairedge : beide Treppen am aeussersten Rand des Schachts hinunter und wieder hinauf (Umrechnung quer zur Treppe)
//   uptasks   : jede der sechs eigenen Aufgaben: zuweisen, zur Konsole, Console.Use, Spiel spielt sich selbst, Fotos, "complete"

using System;
using System.Collections.Generic;
using System.Text;
using HarmonyLib;
using UnityEngine;
using UnknownsAtlas;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    // Plan-Meter -> Welt (wie gen_villa.wp: x - 17, 14 - y)
    private static Vector2 Plan(float x, float y) => new(x - 17f, 14f - y);

    private static float PlayerRadius(PlayerControl lp)
    {
        float rad = 0.2f;
        try
        {
            var col = lp.Collider;
            if (col != null && col.TryCast<CircleCollider2D>() != null) rad = col.Cast<CircleCollider2D>().radius * lp.transform.lossyScale.x;
        }
        catch { }
        return rad;
    }

    private static void SnapPlayer(PlayerControl lp, Vector2 truePos)
    {
        try { lp.NetTransform.RpcSnapTo(truePos - (lp.GetTruePosition() - (Vector2)lp.transform.position)); } catch { }
        try { if (HudManager.InstanceExists) HudManager.Instance.PlayerCam.SnapToTarget(); } catch { }
    }

    // ------------------------------------------------------------------ upprobe

    private static readonly (string Name, float X0, float Y0, float X1, float Y1)[] ProbeAreas =
    {
        ("up", -15.6f, 19.6f, 15.6f, 36.6f),       // ganzes Obergeschoss (Plan x 1.4..32.6, y -22.6..-5.6)
        ("hall", -5.0f, 1.0f, 5.0f, 9.5f),          // Freitreppe in der Halle
        ("kitchen", -15.5f, 9.0f, -7.0f, 15.5f),    // Dienstbotentreppe in der Kueche
    };
    private int _probeArea, _probeRow;

    private void DiagProbe(PlayerControl lp)
    {
        const float step = 0.1f;
        if (_probeArea >= ProbeAreas.Length) { _probeArea = 0; _probeRow = 0; _diagTask++; _diagStep = 0; _diagAt = Time.time + 0.5f; return; }
        var a = ProbeAreas[_probeArea];
        int nx = Mathf.RoundToInt((a.X1 - a.X0) / step) + 1, ny = Mathf.RoundToInt((a.Y1 - a.Y0) / step) + 1;
        float rad = PlayerRadius(lp);
        var self = lp.Collider;
        // genau die Ebenen, mit denen der Spieler zusammenstoesst (Atlas legt Moebel und Konsolen-Grundflaechen auf ShortObjects,
        // das in Constants.ShipAndObjectsMask fehlt: der erste Lauf 18.11. sah damit nur die Waende)
        int mask = Physics2D.GetLayerCollisionMask(lp.gameObject.layer);
        if (_probeRow == 0)
        {
            // den eigenen Spieler aus dem Raster nehmen (er steht sonst selbst im Weg, falls der Kreis ihn trifft: er wird ignoriert)
            HalloweenPlugin.Logger.LogInfo(FormattableString.Invariant($"{LogPrefix} probe hdr {a.Name} {a.X0:F2} {a.Y0:F2} {step:F2} {nx} {ny} rad {rad:F3} mask {mask:X} layer {lp.gameObject.layer}"));
        }
        // 30 Zeilen je Bild, damit das Spiel nicht haengt
        for (int k = 0; k < 30 && _probeRow < ny; k++, _probeRow++)
        {
            float y = a.Y0 + _probeRow * step;
            var sb = new StringBuilder();
            int run = 0, cur = 0;
            for (int i = 0; i < nx; i++)
            {
                var q = new Vector2(a.X0 + i * step, y);
                int blocked = 0;
                foreach (var h in Physics2D.OverlapCircleAll(q, rad, mask))
                {
                    if (h == null || h.isTrigger || h == self) continue;
                    blocked = 1; break;
                }
                if (blocked == cur) run++;
                else { sb.Append(run).Append(' '); run = 1; cur = blocked; }
            }
            sb.Append(run);
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} probe row {a.Name} {_probeRow} {sb}");
        }
        if (_probeRow >= ny) { _probeArea++; _probeRow = 0; }
    }

    // ------------------------------------------------------------------ upwalk / stairedge (Physik-Bewegung)

    internal static Vector2? WalkTarget;          // vom FixedUpdate-Postfix gelesen
    internal static float WalkSpeed = 2.5f;

    // Rundgang oben in Plan-Metern: Raum -> Durchgang -> Raum; "*name" = Foto an diesem Punkt
    private static readonly (float X, float Y, string Shot)[] WalkRoute =
    {
        (17.0f, -8.6f, null), (17.0f, -10.0f, "landing"), (12.0f, -9.5f, null), (9.45f, -9.5f, null),
        (4.77f, -9.5f, "nursery"), (4.77f, -10.62f, null), (9.5f, -10.62f, null),
        (9.5f, -11.0f, null), (9.5f, -12.6f, null), (9.5f, -13.5f, "corridor_w"), (5.2f, -13.5f, null), (5.2f, -15.6f, null),
        (5.8f, -17.0f, "attic"), (8.6f, -18.6f, null), (11.0f, -19.9f, null), (12.6f, -19.0f, null), (14.6f, -19.0f, "darkroom"),
        (16.0f, -17.6f, null), (16.0f, -15.2f, null), (16.0f, -13.5f, null), (21.5f, -13.5f, "corridor_mid"), (21.5f, -15.6f, null),
        (21.8f, -17.0f, "bath"), (22.3f, -19.3f, null), (21.0f, -20.2f, "bath_tub"), (22.6f, -19.6f, null), (23.6f, -19.0f, null),
        (25.2f, -19.4f, null), (27.0f, -19.6f, "sewing"), (29.2f, -18.9f, null), (28.3f, -17.0f, null), (28.3f, -15.4f, null),
        (28.3f, -13.5f, "corridor_e"), (30.0f, -13.0f, null), (30.0f, -11.3f, null), (29.5f, -9.6f, "master"), (27.3f, -8.5f, null),
        (23.5f, -8.6f, null), (22.0f, -9.4f, null), (19.8f, -9.4f, null), (17.0f, -8.6f, "back_at_stairs"), (17.0f, -6.6f, null),
    };
    private int _walkI;
    private float _walkBest, _walkSince;
    private int _walkStuck;
    private bool _walkDownSeen;

    private void DiagWalk(PlayerControl lp)
    {
        var pos = lp.GetTruePosition();
        if (_diagStep == 0)
        {
            SnapPlayer(lp, Plan(17.0f, -8.4f));
            _walkI = 0; _walkStuck = 0; _walkDownSeen = false;
            _diagStep = 1; _diagAt = Time.time + 1.0f;
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: upwalk start, {WalkRoute.Length} points");
            return;
        }
        if (_walkI >= WalkRoute.Length)
        {
            // letzter Punkt liegt hinter der Ausloeselinie im Schacht: der Wechsel nach unten muss passiert sein
            WalkTarget = null;
            bool down = pos.y < 15f;
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: upwalk done, stuck {_walkStuck}, down the stairs {(down ? "yes" : "no")} at {pos.x:F2}/{pos.y:F2} -> {(_walkStuck == 0 && down ? "PASS" : "FAIL")}");
            AtlasMaps.Shot("upwalk", "end_hall");
            _diagTask++; _diagStep = 0; _diagAt = Time.time + 1.0f;
            return;
        }
        var p = WalkRoute[_walkI];
        var target = Plan(p.X, p.Y);
        // nach dem Treppenwechsel ist der Rest der Strecke erledigt
        if (pos.y < 15f) { _walkI = WalkRoute.Length; return; }
        float d = Vector2.Distance(pos, target);
        if (_diagStep == 1) { _walkBest = d; _walkSince = Time.time; _diagStep = 2; }
        if (d < 0.18f)
        {
            WalkTarget = null;
            if (p.Shot != null) { AtlasMaps.Shot("upwalk", p.Shot); _diagAt = Time.time + 0.35f; }
            _walkI++; _diagStep = 1;
            return;
        }
        if (d < _walkBest - 0.05f) { _walkBest = d; _walkSince = Time.time; }
        if (Time.time - _walkSince > 1.6f)
        {
            _walkStuck++;
            HalloweenPlugin.Logger.LogWarning(FormattableString.Invariant(
                $"{LogPrefix} diag: upwalk STUCK at world {pos.x:F2}/{pos.y:F2} (plan {pos.x + 17f:F2}/{14f - pos.y:F2}) on the way to plan {p.X:F2}/{p.Y:F2}"));
            AtlasMaps.Shot("upwalk", $"stuck_{_walkI}");
            SnapPlayer(lp, target);
            WalkTarget = null;
            _walkI++; _diagStep = 1; _diagAt = Time.time + 0.6f;
            return;
        }
        WalkTarget = target;
    }

    // Treppen am Rand: oben am aeussersten Rand des Schachts nach Sueden gehen, unten muss man zwischen den Gelaendern ankommen
    private int _edgeI;

    private void DiagStairEdge(PlayerControl lp)
    {
        if (_stairs.Length == 0) { _diagTask++; _diagStep = 0; return; }
        int si = _edgeI / 2;
        if (si >= _stairs.Length) { _edgeI = 0; WalkTarget = null; _diagTask++; _diagStep = 0; _diagAt = Time.time + 0.5f; return; }
        var s = _stairs[si];
        bool left = _edgeI % 2 == 0;
        float x = left ? s.TopX0 + 0.03f : s.TopX1 - 0.03f;
        var pos = lp.GetTruePosition();
        switch (_diagStep)
        {
            case 0:
                SnapPlayer(lp, new Vector2(x, s.UpTrigger + 0.9f));
                _diagStep = 1; _diagAt = Time.time + 0.8f;
                break;
            case 1:
                WalkTarget = new Vector2(x, s.UpTrigger - 1.0f);
                _diagStep = 2; _diagAt = Time.time + 1.4f;
                break;
            case 2:
            {
                WalkTarget = null;
                bool down = Mathf.Abs(pos.y - s.DownArrive) < 1.2f;
                bool between = pos.x >= s.X0 - 0.15f && pos.x <= s.X1 + 0.15f;
                HalloweenPlugin.Logger.LogInfo(FormattableString.Invariant(
                    $"{LogPrefix} diag: stairedge {s.Key} {(left ? "west" : "east")} down from x {x:F2}: at {pos.x:F2}/{pos.y:F2}, span {s.X0:F2}..{s.X1:F2} -> {(down && between ? "PASS" : "FAIL")}"));
                AtlasMaps.Shot($"stairedge_{s.Key}", left ? "west_down" : "east_down");
                // wieder hinauf: am selben Rand unten nach Norden
                WalkTarget = new Vector2(pos.x, s.DownTrigger + 1.0f);
                _diagStep = 3; _diagAt = Time.time + 1.4f;
                break;
            }
            case 3:
            {
                WalkTarget = null;
                bool up = Mathf.Abs(pos.y - s.UpArrive) < 1.2f;
                HalloweenPlugin.Logger.LogInfo(FormattableString.Invariant(
                    $"{LogPrefix} diag: stairedge {s.Key} {(left ? "west" : "east")} up again: at {pos.x:F2}/{pos.y:F2} -> {(up ? "PASS" : "FAIL")}"));
                _edgeI++; _diagStep = 0; _diagAt = Time.time + 0.5f;
                break;
            }
        }
    }

    // ------------------------------------------------------------------ uptasks

    private int _upTaskI;
    private bool _upShotMid, _upShotDone;
    private NormalPlayerTask _upTask;
    private float _upT0;
    private int _upPass, _upFail, _upAbsent;

    private void DiagUpTasks(PlayerControl lp)
    {
        var kinds = HollowmereUpperTasks.Kinds;
        if (_upTaskI >= kinds.Length)
        {
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: uptasks done: pass {_upPass}, fail {_upFail}, absent {_upAbsent}");
            HwUpperMinigame.DiagAuto = false;
            _upTaskI = 0; _diagTask++; _diagStep = 0; _diagAt = Time.time + 0.5f;
            return;
        }
        var (type, kind) = kinds[_upTaskI];
        switch (_diagStep)
        {
            case 0:
            {
                if (_upTaskI == 0)
                {
                    // alle Aufgaben der Karte zuweisen (wie der Atlas-Autotest StepRepro); bei ausgeschaltetem Obergeschoss fehlen die sechs
                    var ids = new List<byte>();
                    var ship = ShipStatus.Instance;
                    foreach (var (arr, list) in new[] { (ship.CommonTasks, "common"), (ship.LongTasks, "long"), (ship.ShortTasks, "short") })
                        if (arr != null) foreach (var t in arr)
                            if (t != null)
                            {
                                ids.Add((byte)t.Index);
                                foreach (var (ut, _) in kinds)
                                    if (t.TaskType == ut) HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: uptasks pool has {ut} ({list}, index {t.Index})");
                            }
                    lp.Data.RpcSetTasks(new Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppStructArray<byte>(ids.ToArray()));
                    HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: uptasks assigned {ids.Count} task(s)");
                    _upPass = _upFail = _upAbsent = 0;
                }
                _diagStep = 1; _diagAt = Time.time + (_upTaskI == 0 ? 2.5f : 0.3f);
                break;
            }
            case 1:
            {
                _upTask = null;
                foreach (var t in lp.myTasks)
                {
                    var n = t != null ? t.TryCast<NormalPlayerTask>() : null;
                    if (n != null && n.TaskType == type) { _upTask = n; break; }
                }
                if (_upTask == null)
                {
                    HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: uptasks {type} ({kind}): not in this round (option 1970 off?) - absent");
                    _upAbsent++; _upTaskI++; _diagStep = 0; return;
                }
                Console con = null;
                foreach (var c in UnityEngine.Object.FindObjectsOfType<Console>())
                {
                    if (c == null) continue;
                    PlayerTask ft = null;
                    try { ft = c.FindTask(lp); } catch { }
                    if (ft != null && ft.Pointer == _upTask.Pointer) { con = c; break; }
                }
                if (con == null) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} diag: uptasks {type}: no console - FAIL"); _upFail++; _upTaskI++; _diagStep = 0; return; }
                _upCon = con;
                SnapPlayer(lp, (Vector2)con.transform.position + new Vector2(0f, -0.65f));
                _diagStep = 2; _diagAt = Time.time + 1.0f;
                break;
            }
            case 2:
            {
                float dist = _upCon.CanUse(lp.Data, out bool can, out bool could);
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: uptasks {type} at {_upCon.name}: CanUse {can}, could {could}, dist {dist:F2}, room {_upTask.StartAt}, list text '{TaskLine(_upTask)}'");
                AtlasMaps.Shot($"uptask_{kind}", "console");
                HwUpperMinigame.DiagAuto = true;
                HwUpperMinigame.DiagProgress = 0f;
                HwUpperMinigame.DiagOpen = null;
                _upShotMid = _upShotDone = false;
                try { _upCon.Use(); } catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} diag: Use failed: {e.Message}"); }
                _upT0 = Time.time;
                _diagStep = 3; _diagAt = Time.time + 0.9f;
                break;
            }
            case 3:
                AtlasMaps.Shot($"uptask_{kind}", "open");
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: uptasks {type}: minigame {(Minigame.Instance != null ? Minigame.Instance.name : "none")}");
                _diagStep = 4; _diagAt = Time.time + 0.2f;
                break;
            case 4:
            {
                var mg = Minigame.Instance;
                if (mg != null && Time.time - _upT0 < 90f)
                {
                    if (!_upShotMid && HwUpperMinigame.DiagProgress >= 0.5f) { _upShotMid = true; AtlasMaps.Shot($"uptask_{kind}", "mid"); _diagAt = Time.time + 0.1f; }
                    else if (!_upShotDone && HwUpperMinigame.DiagProgress >= 0.999f) { _upShotDone = true; AtlasMaps.Shot($"uptask_{kind}", "done"); _diagAt = Time.time + 0.1f; }
                    return;
                }
                if (mg != null) { try { mg.ForceClose(); } catch { } }
                HwUpperMinigame.DiagAuto = false;
                bool done = _upTask.IsComplete;
                bool info = false;
                try { foreach (var ti in lp.Data.Tasks) if (ti != null && ti.Id == _upTask.Id) info = ti.Complete; } catch { }
                bool ok = done && info && HwUpperMinigame.DiagOpen == kind;
                if (ok) _upPass++; else _upFail++;
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: uptasks {type} ({kind}): opened '{HwUpperMinigame.DiagOpen}', complete {done}, data {info}, {Time.time - _upT0:F1}s -> {(ok ? "PASS" : "FAIL")}");
                _upTaskI++; _diagStep = 0; _diagAt = Time.time + 1.0f;
                break;
            }
        }
    }

    private Console _upCon;

    private static string TaskLine(PlayerTask t)
    {
        try
        {
            var sb = new Il2CppSystem.Text.StringBuilder();
            t.AppendTaskText(sb);
            return sb.ToString().Trim();
        }
        catch { return "?"; }
    }
}

/// <summary>Autotest-Laufen mit Physik: der eigene Spieler bekommt die Geschwindigkeit zum Ziel (Kollision zaehlt wie beim Spielen).</summary>
[HarmonyPatch(typeof(PlayerPhysics), nameof(PlayerPhysics.FixedUpdate))]
internal static class HollowmereDiagWalkPatch
{
    public static void Postfix(PlayerPhysics __instance)
    {
        var t = HollowmereWorld.WalkTarget;
        if (t == null) return;
        try
        {
            if (__instance == null || !__instance.AmOwner || __instance.body == null) return;
            var pos = __instance.myPlayer.GetTruePosition();
            var d = t.Value - pos;
            __instance.body.velocity = d.magnitude < 0.05f ? Vector2.zero : d.normalized * HollowmereWorld.WalkSpeed;
        }
        catch { }
    }
}
