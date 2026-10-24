// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HwModalDiag - Selbsttest der Eingabesperre der Halloween-Menues (HalloweenUI.ModalOpen), nur mit
// UC_HALLOWEEN_DIAG=modal im Freeplay: ein Test-Knopf (PassiveButton) wird ohne Menue, mit offenem Trick-or-Treat-
// Menue, nach dem Schliessen und mit offenem Omen-Menue angeklickt; pro Schritt eine Logzeile mit Klickzahl und
// Laufsperre, dann "diag: all done" und Ende.

using System;
using System.Collections;
using BepInEx.Unity.IL2CPP.Utils.Collections;
using HarmonyLib;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class HwModalDiag {
        private const string P = "[Halloween/ModalDiag]";
        private static readonly bool On = (Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "") == "modal";
        private static float at = -1f;
        private static bool done;
        private static int clicks;

        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        static class TickPatch {
            static bool Prepare() => On;
            public static void Postfix(HudManager __instance) {
                if (done || PlayerControl.LocalPlayer == null || ShipStatus.Instance == null) return;
                if (at < 0f) { at = Time.time + 3f; return; }
                if (Time.time < at) return;
                done = true;
                __instance.StartCoroutine(Run().WrapToIl2Cpp());
            }
        }

        private static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{P} {s}");

        private static IEnumerator Run() {
            var go = new GameObject("ModalDiagButton") { layer = 5 };
            go.AddComponent<BoxCollider2D>().size = Vector2.one;
            var pb = go.AddComponent<PassiveButton>();
            pb.OnClick = new UnityEngine.UI.Button.ButtonClickedEvent();
            pb.OnClick.AddListener((Action)(() => clicks++));
            var lp = PlayerControl.LocalPlayer;

            void Click() { try { pb.ReceiveClickDown(); pb.ReceiveClickUp(); } catch (Exception e) { Log($"click failed: {e.Message}"); } }
            string State(string step) => $"{step}: clicks {clicks}, modal {HalloweenUI.ModalOpen}, moveable {lp.moveable}, {HalloweenUI.ModalDebug()}";

            Click(); yield return null; yield return null;
            Log(State("no menu"));
            int before = clicks;

            // The real menus (Trick or Treat, Omens, Lobby games) are lobby-only; a blocking canvas built the same way
            // (HalloweenUI.Canvas(..., blocking: true)) stands in for them.
            var menu = HalloweenUI.Canvas("ModalDiagMenu", 9500, true);
            for (int i = 0; i < 3; i++) yield return null;
            Click(); yield return null;
            Log(State("menu open") + (clicks == before && !lp.moveable ? " -> BLOCKED, frozen" : " -> LEAKED"));

            UnityEngine.Object.Destroy(menu);
            for (int i = 0; i < 3; i++) yield return null;
            Click(); yield return null;
            Log(State("menu closed") + (clicks > before && lp.moveable ? " -> works again, can move" : " -> STILL BLOCKED"));

            before = clicks;
            menu = HalloweenUI.Canvas("ModalDiagMenu2", 9500, true);
            menu.SetActive(false);
            for (int i = 0; i < 3; i++) yield return null;
            Click(); yield return null;
            Log(State("hidden menu") + (clicks > before ? " -> not blocking (correct)" : " -> BLOCKS while hidden"));
            UnityEngine.Object.Destroy(menu);

            UnityEngine.Object.Destroy(go);
            Log("diag: all done");
            yield return new WaitForSeconds(0.5f);
            Application.Quit();
        }
    }
}
