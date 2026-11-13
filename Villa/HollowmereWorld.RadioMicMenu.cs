// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld.RadioMicMenu - wer am Funktisch sprechen darf, als Karte im UTS-Lobby-Menue (User 06.11.: "Host soll in der
// Lobby auswaehlen koennen, welche Spieler auf dieses Geraet zugreifen koennen, wenn es auf Selected ist. Default DrSuspect und
// ich an, das kann der Host ueberschreiben").
//
// Eintrag "Radio Microphone" (Reihenfolge 62, AppDomain "UTS.LobbyMenu.Add"); ohne UTS bleibt der Chat-Befehl /mic. Je
// Lobby-Spieler ein Knopf, gruen = darf sprechen. Nur der Host schaltet um (MicToggle, dieselbe Liste radio_mic.txt wie /mic,
// auch sich selbst), Gaeste sehen die vom Host verteilte Liste nur lesend. Den Modus (Selected Players / Everyone / Off) stellt
// weiter die Spieloption 2160 ein: TORs updateSelection teilt eine Aenderung nur bei offenem Optionsmenue.

using System;
using System.Linq;
using HarmonyLib;
using UnityEngine;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    internal static class MicMenu
    {
        private static GameObject _root;
        private static readonly Color Accent = new(0.86f, 0.56f, 0.22f);
        private const float W = 1100f, Pad = 34f;
        private const int Cols = 3;

        private static string T(string en, string de) => TrickOrTreat.De() ? de : en;

        internal static void Close() { if (_root != null) UnityEngine.Object.Destroy(_root); _root = null; }
        internal static void RefreshIfOpen() { if (_root != null) Open(); }

        private static PlayerControl[] Players() => PlayerControl.AllPlayerControls.ToArray()
            .Where(p => p != null && p.Data != null && !p.Data.Disconnected).OrderBy(p => p.PlayerId).ToArray();

        private static bool IsHostPlayer(PlayerControl p) => UnknownsNet.SenderIsHost(p);

        internal static void Open()
        {
            try
            {
                Close();
                bool host = AmHost;
                var list = host ? LoadMicList() : null;
                if (host) HostSendMicList();                            // Gaeste sehen den Stand gleich
                var players = Players();
                int rows = Mathf.Max(1, (players.Length + Cols - 1) / Cols);
                _root = HalloweenUI.Canvas("RadioMicMenu", 9500, true);
                HalloweenUI.Backdrop(_root, Close);
                var card = HalloweenUI.CenterPanel(_root, new Vector2(W, 330f + rows * 68f));
                float y = HalloweenUI.Title(card, "Radio Microphone", 16f, 34f, Accent);
                HalloweenUI.CloseButton(card, "", Close);
                HalloweenUI.Text(card, host
                        ? T("Who may speak at the radio in Hollowmere Manor. Click a player to switch. Saved on this PC and sent to every player.",
                            "Wer am Funktisch in Hollowmere Manor sprechen darf. Klick auf einen Spieler schaltet um. Gespeichert auf diesem PC und an alle geschickt.")
                        : T("Read only: the host decides.", "Nur lesen: der Host entscheidet."),
                    19f, host ? HalloweenUI.Muted : HalloweenUI.Warn, new Vector2(Pad, y - 6f), new Vector2(W - 2 * Pad, 54f));
                y -= 66f;
                int mode = MicMode;
                string modeName = mode == 1 ? "Everyone" : mode == 2 ? "Off" : "Selected Players";
                HalloweenUI.Text(card, T("Mode: ", "Modus: ") + modeName + (mode == 0 ? "" :
                        T("  (this list only counts in Selected Players)", "  (die Liste gilt nur bei Selected Players)")),
                    22f, mode == 0 ? Color.white : HalloweenUI.Warn, new Vector2(Pad, y), new Vector2(W - 2 * Pad, 34f), TMPro.FontStyles.Bold);
                y -= 38f;
                HalloweenUI.Text(card, T("The mode is a game setting under Hollowmere Manor.", "Den Modus stellst du in den Spieleinstellungen unter Hollowmere Manor ein."),
                    17f, HalloweenUI.Muted, new Vector2(Pad, y), new Vector2(W - 2 * Pad, 28f));
                y -= 46f;

                float bw = (W - 2 * Pad - (Cols - 1) * 12f) / Cols;
                for (int i = 0; i < players.Length; i++)
                {
                    var p = players[i];
                    bool on = host ? MicListed(p, list) : MicAllowed.Contains(p.PlayerId);
                    byte pid = p.PlayerId;
                    var pos = new Vector2(Pad + (i % Cols) * (bw + 12f), y - (i / Cols) * 68f);
                    HalloweenUI.Button(card, p.Data.PlayerName + (IsHostPlayer(p) ? " (Host)" : ""), pos, new Vector2(bw, 56f),
                        on ? HalloweenUI.Green : HalloweenUI.Grey, () => Toggle(pid), out var txt,
                        new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 20f);
                    if (!on) txt.color = HalloweenUI.Muted;
                }
            }
            catch (Exception e)
            {
                HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} radio mic menu failed: {e}");
                Close();
            }
        }

        private static void Toggle(byte pid)
        {
            if (!AmHost) return;
            var p = Players().FirstOrDefault(x => x.PlayerId == pid);
            if (p == null) return;
            bool? on = MicToggle(p);
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} radio mic: {p.Data.PlayerName} " +
                                            (on == null ? "has no account id" : on.Value ? "may speak" : "may no longer speak"));
            Open();
        }

        private static string Label()
        {
            int mode = MicMode;
            if (mode == 1) return T("Radio Microphone (everyone)", "Radio Microphone (alle)");
            if (mode == 2) return T("Radio Microphone (off)", "Radio Microphone (aus)");
            return "Radio Microphone";
        }

        // ---- Eintrag im UTS-Lobby-Menue ----
        private const string AddKey = "UTS.LobbyMenu.Add";
        private static bool _registered;
        private static float _nextTry;

        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        private static class MenuTick
        {
            private static void Postfix()
            {
                try
                {
                    if (_root != null && (Input.GetKeyDown(KeyCode.Escape) || ShipStatus.Instance != null)) Close();
                    if (_registered || LobbyBehaviour.Instance == null || Time.realtimeSinceStartup < _nextTry) return;
                    _nextTry = Time.realtimeSinceStartup + 1f;
                    if (AppDomain.CurrentDomain.GetData(AddKey) is not Action<string, int, Func<bool>, Func<string>, Action, Color> add) return;
                    add("halloween.radiomic", 62, () => LobbyBehaviour.Instance != null, Label, Open, Accent);
                    _registered = true;
                    HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} radio mic entry added to the UTS lobby menu.");
                }
                catch (Exception e)
                {
                    _registered = true;
                    HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} radio mic menu entry failed: {e.Message}");
                }
            }
        }
    }
}
