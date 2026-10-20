// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Self test of the Halloween task skins (only with UC_HALLOWEEN_DIAG = tasks). Needs a freeplay round that starts on
 * its own (Unknown's Atlas ForceMap = vanilla:<map>). For every skinned task the map offers: open it once vanilla
 * (hierarchy dump + shot), then skinned (shot "vorher"), solve it through the minigame's own methods, shot
 * "nachher". Screenshots go to <game>\UCShots\hwtasks\, log lines start with "[Halloween/Tasks] diag:", the run
 * ends with "diag: all done" and quits.
 */

using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class HwTaskSkinsDiag {
        private static bool running;
        private static float roundSeen = -1f;
        private static string dir, map = "map";

        private static void Log(string s) => HwTaskSkins.Log("diag: " + s);

        private static void Shot(string name) {
            try { ScreenCapture.CaptureScreenshot(Path.Combine(dir, $"{map}_{name}.png")); Log("shot " + name); }
            catch (Exception e) { Log($"shot {name}: {e.Message}"); }
        }

        private static IEnumerator Wait(float seconds) {
            float until = Time.realtimeSinceStartup + seconds;
            while (Time.realtimeSinceStartup < until) yield return null;
        }

        private static IEnumerator WaitFor(Func<bool> cond, float max) {
            float until = Time.realtimeSinceStartup + max;
            while (Time.realtimeSinceStartup < until) {
                bool ok = false;
                try { ok = cond(); } catch { }
                if (ok) yield break;
                yield return null;
            }
        }

        internal static void Tick() {
            if (!HwTaskSkins.DiagOn || running) return;
            if (!HwMechanics.FreePlay() || ShipStatus.Instance == null || PlayerControl.LocalPlayer == null) return;
            if (roundSeen < 0f) roundSeen = Time.realtimeSinceStartup;
            if (Time.realtimeSinceStartup - roundSeen < 5f) return;
            running = true;
            dir = Path.Combine(BepInEx.Paths.GameRootPath, "UCShots", "hwtasks");
            Directory.CreateDirectory(dir);
            Reactor.Utilities.Coroutines.Start(Run());
        }

        private static string TypeName(UnityEngine.Object o) { try { return o == null ? "null" : o.GetIl2CppType().Name; } catch { return "?"; } }

        private static readonly TaskTypes[] Wanted = {
            TaskTypes.FuelEngines, TaskTypes.ClearAsteroids, TaskTypes.EmptyGarbage, TaskTypes.EmptyChute,
            TaskTypes.PrimeShields, TaskTypes.DivertPower,
        };

        private static IEnumerator Run() {
            var lp = PlayerControl.LocalPlayer;
            var ship = ShipStatus.Instance;
            map = ship.name.Replace("(Clone)", "").Replace(" ", "");
            string atlas = HwMechanics.AtlasMap();
            if (atlas != null) map = "atlas_" + atlas;
            Log($"start: map {ship.name}, atlas '{atlas ?? "null"}', option enabled {HwTaskSkins.Enabled}");
            try {
                void List(string kind, Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<NormalPlayerTask> arr) {
                    if (arr == null) return;
                    foreach (var t in arr) {
                        if (t == null) continue;
                        string stages = "";
                        var ms = t.MinigamePrefab?.TryCast<MultistageMinigame>();
                        if (ms != null && ms.Stages != null) stages = " stages [" + string.Join(", ", ms.Stages.Select(TypeName)) + "]";
                        var dp = t.MinigamePrefab?.TryCast<DivertPowerMetagame>();
                        if (dp != null) stages = $" distribute {TypeName(dp.DistributePrefab)} receive {TypeName(dp.ReceivePrefab)}";
                        Log($"  task {kind} {t.TaskType} -> {TypeName(t.MinigamePrefab)}{stages}");
                    }
                }
                List("common", ship.CommonTasks); List("long", ship.LongTasks); List("short", ship.ShortTasks);
            } catch (Exception e) { Log("task list: " + e.Message); }
            Log("my tasks: " + string.Join(", ", lp.myTasks.ToArray().Select(t => t == null ? "null" : t.TaskType.ToString())));

            string only = Environment.GetEnvironmentVariable("UC_HALLOWEEN_TASKS") ?? "";
            foreach (var type in Wanted) {
                if (only.Length > 0 && !only.Split(',').Contains(type.ToString())) continue;
                PlayerTask task = null;
                foreach (var t in lp.myTasks) if (t != null && t.TaskType == type) { task = t; break; }
                if (task == null) task = AddTask(lp, type);
                if (task == null) { Log($"{type}: not on this map"); continue; }
                int steps = 1;
                var npt = task.TryCast<NormalPlayerTask>();
                if (npt != null) steps = Mathf.Max(1, npt.MaxStep);
                for (int step = 0; step < steps && !task.IsComplete; step++) {
                    string tag = $"{type}_{step + 1}";
                    // vanilla look first (dump + shot)
                    HwTaskSkins.DiagVanilla = true;
                    yield return Open(lp, task);
                    yield return Wait(1.3f);
                    var mg = Minigame.Instance;
                    if (mg == null) { Log($"{tag}: did not open"); HwTaskSkins.DiagVanilla = false; break; }
                    Log($"{tag}: open {TypeName(mg)} step {task.TaskStep}");
                    Dump(mg);
                    Shot($"{tag}_vanilla");
                    yield return Wait(0.3f);
                    yield return CloseNow();
                    HwTaskSkins.DiagVanilla = false;
                    // skinned
                    int before = HwTaskSkins.DiagApplied;
                    yield return Open(lp, task);
                    yield return Wait(1.3f);
                    mg = Minigame.Instance;
                    if (mg == null) { Log($"{tag}: skinned did not open"); break; }
                    Log($"{tag}: skin applied {HwTaskSkins.DiagApplied - before} ({HwTaskSkins.DiagLast})");
                    DumpSkin(mg);
                    Shot($"{tag}_vorher");
                    int stepBefore = task.TaskStep;
                    yield return Solve(mg, task, tag);
                    yield return Wait(0.2f);
                    Shot($"{tag}_nachher");
                    if (task.TaskStep == stepBefore && !task.IsComplete && Minigame.Instance != null) {
                        Log($"{tag}: not solved by the minigame itself, NextStep() as fallback");
                        try { npt?.NextStep(); } catch (Exception e) { Log("next step: " + e.Message); }
                    }
                    yield return Wait(0.6f);
                    yield return WaitFor(() => Minigame.Instance == null, 3f);
                    if (Minigame.Instance != null) yield return CloseNow();
                    Log($"{tag}: task step now {task.TaskStep}, complete {task.IsComplete}");
                    yield return Wait(0.5f);
                }
            }
            yield return Wait(1f);
            Log($"pictures from files: {HwArt.fromFile.Count(f => f.StartsWith("tasks/"))} task pictures");
            Log("all done");
            yield return Wait(0.5f);
            Application.Quit();
        }

        private static uint nextId = 200;
        private static PlayerTask AddTask(PlayerControl lp, TaskTypes type) {
            try {
                var ship = ShipStatus.Instance;
                NormalPlayerTask prefab = null;
                foreach (var arr in new[] { ship.CommonTasks, ship.LongTasks, ship.ShortTasks }) {
                    if (arr == null) continue;
                    foreach (var t in arr) if (t != null && t.TaskType == type) { prefab = t; break; }
                    if (prefab != null) break;
                }
                if (prefab == null) return null;
                var task = UnityEngine.Object.Instantiate(prefab, lp.transform);
                task.Id = nextId++;
                task.Owner = lp;
                task.Initialize();
                lp.myTasks.Add(task);
                Log($"{type}: task added for the test (id {task.Id})");
                return task;
            } catch (Exception e) { Log($"{type}: add task: {e.Message}"); return null; }
        }

        private static IEnumerator CloseNow() {
            try { Minigame.Instance?.Close(); } catch (Exception e) { Log("close: " + e.Message); }
            yield return WaitFor(() => Minigame.Instance == null, 2f);
            if (Minigame.Instance != null) {
                try { UnityEngine.Object.Destroy(Minigame.Instance.gameObject); } catch { }
                yield return Wait(0.2f);
            }
            yield return Wait(0.3f);
        }

        private static IEnumerator Open(PlayerControl lp, PlayerTask task) {
            Console console = null;
            try {
                var list = task.FindConsoles();
                if (list != null && list.Count > 0) console = list[0];
            } catch (Exception e) { Log("find consoles: " + e.Message); }
            if (console == null) {
                foreach (var c in ShipStatus.Instance.AllConsoles) {
                    try { if (c != null && c.FindTask(lp) == task) { console = c; break; } } catch { }
                }
            }
            if (console == null) { Log($"{task.TaskType}: no console"); yield break; }
            try { lp.NetTransform.SnapTo(console.transform.position); } catch { }
            yield return Wait(0.4f);
            try { console.Use(); } catch (Exception e) { Log("use: " + e.Message); }
            yield return WaitFor(() => Minigame.Instance != null, 1.5f);
            if (Minigame.Instance == null) {
                Log($"{task.TaskType}: Use() did not open, instantiating by hand");
                try {
                    var mg = UnityEngine.Object.Instantiate(task.GetMinigamePrefab(), Camera.main.transform, false);
                    mg.transform.localPosition = new Vector3(0f, 0f, -50f);
                    mg.Console = console;
                    mg.Begin(task);
                } catch (Exception e) { Log("manual open: " + e.Message); }
            }
        }

        private static T Find<T>(Minigame mg) where T : Minigame {
            var t = mg.TryCast<T>();
            if (t != null) return t;
            foreach (var m in mg.GetComponentsInChildren<Minigame>()) { var c = m.TryCast<T>(); if (c != null) return c; }
            return null;
        }

        private static IEnumerator Solve(Minigame mg, PlayerTask task, string tag) {
            var sh = Find<ShieldMinigame>(mg);
            if (sh != null) {
                for (int i = 0; i < sh.Shields.Length; i++) {
                    if ((sh.shields & (1 << i)) == 0) { try { sh.ToggleShield(i); } catch (Exception e) { Log("toggle: " + e.Message); } yield return Wait(0.15f); }
                }
                Log($"{tag}: shields bits {sh.shields}");
                yield break;
            }
            var wm = Find<WeaponsMinigame>(mg);
            if (wm != null) {
                try { wm.TimeToSpawn = new FloatRange(0.08f, 0.12f); } catch { }
                float until = Time.realtimeSinceStartup + 25f;
                bool midShot = false;
                int broken = 0;
                while (Time.realtimeSinceStartup < until && !task.IsComplete && Minigame.Instance != null) {
                    var act = wm.asteroidPool.activeChildren;
                    for (int i = act.Count - 1; i >= 0; i--) {
                        var a = act[i]?.TryCast<Asteroid>();
                        if (a == null || !a.gameObject.activeSelf) continue;
                        var sr = a.GetComponent<SpriteRenderer>();
                        if (broken < 3) Log($"{tag}: asteroid idx {a.imgIdx} sprite {sr?.sprite?.name} size {sr?.bounds.size.x:F2} rot {a.transform.localEulerAngles.z:F0}");
                        try { wm.BreakApart(a); broken++; } catch (Exception e) { Log("break: " + e.Message); }
                        break;
                    }
                    if (!midShot && broken >= 4) { yield return Wait(0.08f); Shot($"{tag}_treffer"); midShot = true; }
                    yield return Wait(0.25f);
                }
                Log($"{tag}: broke {broken}");
                yield break;
            }
            var gm = Find<EmptyGarbageMinigame>(mg);
            if (gm != null) {
                Log($"{tag}: garbage handle {gm.Handle?.name} range {gm.HandleRange.min:F2}..{gm.HandleRange.max:F2} blocker {gm.Blocker?.enabled}");
                float until = Time.realtimeSinceStartup + 5f;
                while (Time.realtimeSinceStartup < until && !task.IsComplete && Minigame.Instance != null) {
                    try {
                        gm.leverInput = Time.realtimeSinceStartup < until - 2.5f ? 1f : -1f;
                        var h = gm.Handle.transform; var p = h.localPosition;
                        h.localPosition = new Vector3(p.x, gm.HandleRange.min, p.z);
                    } catch { }
                    yield return null;
                }
                Log($"{tag}: garbage after lever: complete {task.IsComplete}, blocker {gm.Blocker?.enabled}");
                if (!task.IsComplete && Minigame.Instance != null) {
                    try { gm.Blocker.enabled = false; } catch { }
                    yield return WaitFor(() => task.IsComplete || Minigame.Instance == null, 4f);
                    Log($"{tag}: garbage after blocker off: complete {task.IsComplete}");
                }
                yield break;
            }
            var dv = Find<DivertPowerMinigame>(mg);
            if (dv != null) {
                Log($"{tag}: divert slider {dv.sliderId} range {dv.SliderY.min:F2}..{dv.SliderY.max:F2}");
                float until = Time.realtimeSinceStartup + 3f;
                while (Time.realtimeSinceStartup < until && Minigame.Instance != null && task.TaskStep == 0) {
                    try {
                        var t = dv.Sliders[dv.sliderId].transform; var p = t.localPosition;
                        t.localPosition = new Vector3(p.x, dv.SliderY.max, p.z);
                    } catch { }
                    yield return null;
                }
                yield break;
            }
            var rf = Find<RefuelStage>(mg);
            if (rf != null) {
                try { rf.Refuel(); } catch (Exception e) { Log("refuel: " + e.Message); }
                yield return Wait(1.2f);
                Shot($"{tag}_halb");
                yield return WaitFor(() => rf == null || rf.complete, 12f);
                yield break;
            }
            Log($"{tag}: no solver for {TypeName(mg)}");
        }

        private static string Path0(Transform t, Transform root) {
            var sb = new StringBuilder(t.name);
            var p = t.parent;
            while (p != null && p != root) { sb.Insert(0, p.name + "/"); p = p.parent; }
            return sb.ToString();
        }

        private static void Dump(Minigame mg) {
            int lines = 0;
            Log($"dump {TypeName(mg)} root ({mg.transform.position.x:F2}, {mg.transform.position.y:F2}, {mg.transform.position.z:F2})");
            DumpRec(mg.transform, 0, ref lines);
            try {
                var rf = Find<RefuelStage>(mg);
                if (rf != null) Log($"  refuel src {Gauge(rf.srcGauge, mg.transform)} dest {Gauge(rf.destGauge, mg.transform)} duration {rf.RefuelDuration:F2} red {Path0(rf.redLight.transform, mg.transform)} green {Path0(rf.greenLight.transform, mg.transform)}");
                var wm = Find<WeaponsMinigame>(mg);
                if (wm != null) {
                    var pf = wm.asteroidPool.Prefab?.TryCast<Asteroid>();
                    if (pf != null) Log($"  asteroid images [{string.Join(", ", pf.AsteroidImages.Select(SpriteInfo))}] broken [{string.Join(", ", pf.BrokenImages.Select(SpriteInfo))}] explosion {SpriteInfo(pf.Explosion?.sprite)}");
                }
                var gm = Find<EmptyGarbageMinigame>(mg);
                if (gm != null) {
                    Log($"  garbage prefabs [{string.Join(", ", gm.GarbagePrefabs.Select(p => SpriteInfo(p?.sprite)))}]");
                    Log($"  leaf prefabs [{string.Join(", ", gm.LeafPrefabs.Select(p => SpriteInfo(p?.sprite)))}] special [{string.Join(", ", gm.SpecialObjectPrefabs.Select(p => SpriteInfo(p?.sprite)))}]");
                    Log($"  objects {gm.Objects?.Length ?? -1}: [{string.Join(", ", (gm.Objects?.ToArray() ?? new SpriteRenderer[0]).Take(12).Select(o => o == null ? "null" : o.name + ":" + o.sprite?.name))}]");
                }
                var dv = Find<DivertPowerMinigame>(mg);
                if (dv != null) Log($"  divert sliders [{string.Join(", ", dv.Sliders.Select(s => s == null ? "null" : Path0(s.transform, mg.transform)))}] slider {dv.sliderId} y {dv.SliderY.min:F2}..{dv.SliderY.max:F2}");
                var sh = Find<ShieldMinigame>(mg);
                if (sh != null) Log($"  shields [{string.Join(", ", sh.Shields.Select(s => s == null ? "null" : Path0(s.transform, mg.transform)))}] bits {sh.shields} on {sh.OnColor} off {sh.OffColor}");
            } catch (Exception e) { Log("dump fields: " + e.Message); }
        }

        private static string Gauge(VerticalGauge g, Transform root) {
            if (g == null) return "null";
            return $"{Path0(g.transform, root)} value {g.value:F2}/{g.MaxValue:F2} mask {(g.Mask != null ? Path0(g.Mask.transform, root) + " " + SpriteInfo(g.Mask.sprite) : "null")} maskScale {g.maskScale:F2}";
        }

        private static string SpriteInfo(Sprite s) {
            if (s == null) return "null";
            return $"{s.name} {s.rect.width:F0}x{s.rect.height:F0}@{s.pixelsPerUnit:F0} piv ({s.pivot.x / Mathf.Max(1, s.rect.width):F2},{s.pivot.y / Mathf.Max(1, s.rect.height):F2})";
        }

        private static void DumpRec(Transform t, int depth, ref int lines) {
            if (lines > 260 || depth > 8) return;
            lines++;
            var sb = new StringBuilder();
            sb.Append(' ', depth * 2).Append(t.name);
            if (!t.gameObject.activeSelf) sb.Append(" [off]");
            var lp = t.localPosition; var ls = t.localScale;
            sb.Append($" lp({lp.x:F2},{lp.y:F2},{lp.z:F2}) wz {t.position.z:F2} ls({ls.x:F2},{ls.y:F2}) rot {t.localEulerAngles.z:F0}");
            try {
                var comps = t.GetComponents<Component>();
                var names = comps.Where(c => c != null).Select(c => TypeName(c)).Where(n => n != "Transform");
                sb.Append(" {").Append(string.Join(",", names)).Append('}');
            } catch { }
            try {
                var sr = t.GetComponent<SpriteRenderer>();
                if (sr != null) sb.Append($" SR[{SpriteInfo(sr.sprite)} b {sr.bounds.size.x:F2}x{sr.bounds.size.y:F2} col {sr.color.r:F2},{sr.color.g:F2},{sr.color.b:F2},{sr.color.a:F2} ord {sr.sortingOrder} en {sr.enabled} mask {sr.maskInteraction} draw {sr.drawMode}]");
                var mr = t.GetComponent<MeshRenderer>();
                if (mr != null) sb.Append($" MR[ord {mr.sortingOrder} q {mr.sharedMaterial?.renderQueue}]");
                var sm = t.GetComponent<SpriteMask>();
                if (sm != null) sb.Append($" MASK[{SpriteInfo(sm.sprite)} front {sm.frontSortingOrder} back {sm.backSortingOrder}]");
            } catch { }
            HwTaskSkins.Log("diag:  " + sb);
            for (int i = 0; i < t.childCount; i++) DumpRec(t.GetChild(i), depth + 1, ref lines);
        }

        private static void DumpSkin(Minigame mg) {
            try {
                foreach (var sr in mg.GetComponentsInChildren<SpriteRenderer>(true)) {
                    if (sr == null || sr.name != HwTaskSkins.Marker) continue;
                    Log($"  skin {Path0(sr.transform, mg.transform)} at ({sr.transform.position.x:F2}, {sr.transform.position.y:F2}, {sr.transform.position.z:F2}) b {sr.bounds.size.x:F2}x{sr.bounds.size.y:F2} vis {sr.isVisible} ord {sr.sortingOrder}");
                }
            } catch (Exception e) { Log("dump skin: " + e.Message); }
        }
    }
}
