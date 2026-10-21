// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Pumpkin Carving windows (HalloweenUI look): the carving window (24x24 grid on the pumpkin, paint / erase,
 * brush size, mirror, clear, 60 s timer, done) and the vote window (every lantern as a tile, click to vote,
 * result). The player stands still while a window is open.
 * Drawing: left mouse button paints with the chosen tool, the right one always erases; between two frames the
 * stroke is filled in (a fast drag leaves no gaps).
 */

using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

namespace UnknownsHalloween {
    internal static class PumpkinCarvingUI {
        private static string T(string en, string de) => LobbyGames.T(en, de);
        internal const float CarveSeconds = 60f;

        // ---------------------------------------------------------------- carving window
        private static GameObject carveRoot;
        private static RectTransform gridRect;
        private static Texture2D carveTex;
        private static TMPro.TextMeshProUGUI timerText;
        private static readonly Dictionary<string, GameObject> toolButtons = new();
        internal static byte[] Bits = new byte[PumpkinCarving.Bytes];
        private static float carveEndsAt;
        internal static bool Erase, Big, Mirror;
        private static int lastCol = -1, lastRow = -1;
        private static bool dirty;
        internal static bool CarveOpen => carveRoot != null;

        internal static void OpenCarve() {
            try {
                if (!LobbyGames.CarvingOn && !LobbyGamesDiag.Active) return;
                CloseCarve();
                CloseVote();
                var lp = PlayerControl.LocalPlayer;
                Bits = lp != null && PumpkinCarving.Faces.TryGetValue(lp.PlayerId, out var mine) ? (byte[])mine.Clone() : new byte[PumpkinCarving.Bytes];
                Erase = false; Big = false; Mirror = false;
                carveEndsAt = Time.realtimeSinceStartup + CarveSeconds;
                Freeze(true);

                carveRoot = HalloweenUI.Canvas("PumpkinCarve", 9600, true);
                HalloweenUI.Backdrop(carveRoot, null);
                const float W = 1340f, H = 1010f, Pad = 34f, Pic = 840f;
                var card = HalloweenUI.CenterPanel(carveRoot, new Vector2(W, H));
                HalloweenUI.Title(card, "Pumpkin Carving", 16f, 34f, LobbyGames.Pumpkin);
                HalloweenUI.Button(card, "X", new Vector2(-HalloweenUI.FrameW - 12f, -HalloweenUI.FrameW - 12f), new Vector2(54f, 54f), HalloweenUI.Red, () => CloseCarve(),
                    out _, new Vector2(1, 1), new Vector2(1, 1), new Vector2(1, 1), 36f);

                // the pumpkin and the grid on its carving area (x 136-376, y 156-396 of 512)
                float s = Pic / LobbyArt.PumpkinSize;
                var pic = Img(card, LobbyArt.UiSprite("pumpkin", LobbyArt.Pumpkin()), new Vector2(Pad, -110f), new Vector2(Pic, Pic));
                pic.raycastTarget = false;
                carveTex = LobbyArt.FaceTexture(Bits, PumpkinCarving.Lit, carveTex);
                var areaPos = new Vector2(Pad + LobbyArt.PumpkinAreaX * s, -110f - LobbyArt.PumpkinAreaY * s);
                var areaSize = new Vector2(LobbyArt.PumpkinAreaW * s, LobbyArt.PumpkinAreaW * s);
                var shade = Raw(card, HalloweenUI.Solid().texture, areaPos, areaSize);       // the carved-out cells read darker until they glow
                shade.color = new Color(0f, 0f, 0f, 0.10f);
                var face = Raw(card, carveTex, areaPos, areaSize);
                gridRect = face.rectTransform;
                Raw(card, LobbyArt.GridLines(), areaPos, areaSize);

                // the tools on the right
                float x = Pad + Pic + 34f, colW = W - x - Pad;
                float y = -120f;
                HalloweenUI.Text(card, T("Time left", "Restzeit"), 20f, HalloweenUI.Muted, new Vector2(x, y), new Vector2(colW, 28f));
                timerText = HalloweenUI.Text(card, "60", 64f, Color.white, new Vector2(x, y - 26f), new Vector2(colW, 80f), TMPro.FontStyles.Bold);
                y -= 130f;
                toolButtons.Clear();
                toolButtons["paint"] = Tool(card, T("Carve", "Schnitzen"), x, y, colW / 2f - 6f, () => { Erase = false; Paint(); });
                toolButtons["erase"] = Tool(card, T("Erase", "Radieren"), x + colW / 2f + 6f, y, colW / 2f - 6f, () => { Erase = true; Paint(); });
                y -= 66f;
                toolButtons["small"] = Tool(card, T("Thin", "Fein"), x, y, colW / 2f - 6f, () => { Big = false; Paint(); });
                toolButtons["big"] = Tool(card, T("Thick", "Dick"), x + colW / 2f + 6f, y, colW / 2f - 6f, () => { Big = true; Paint(); });
                y -= 66f;
                toolButtons["mirror"] = Tool(card, T("Mirror", "Spiegeln"), x, y, colW, () => { Mirror = !Mirror; Paint(); });
                y -= 66f;
                HalloweenUI.Button(card, T("Start over", "Neu anfangen"), new Vector2(x, y), new Vector2(colW, 52f), HalloweenUI.Amber,
                    () => { Bits = new byte[PumpkinCarving.Bytes]; dirty = true; }, out _, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 20f);
                y -= 84f;
                HalloweenUI.Text(card, T("Left mouse button: tool. Right mouse button: erase. The carved parts glow on your lantern.",
                                         "Linke Maustaste: Werkzeug. Rechte Maustaste: radieren. Was du ausschneidest, leuchtet auf deiner Laterne."),
                    18f, HalloweenUI.Muted, new Vector2(x, y), new Vector2(colW, 120f));
                HalloweenUI.Button(card, T("Done", "Fertig"), new Vector2(x, -H + 44f + 70f), new Vector2(colW, 70f), HalloweenUI.Green, Submit,
                    out _, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 30f);
                Paint();
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogWarning($"{LobbyGames.LogPrefix} carving window failed: {e}");
                CloseCarve();
            }
        }

        private static GameObject Tool(GameObject card, string label, float x, float y, float w, Action click) =>
            HalloweenUI.Button(card, label, new Vector2(x, y), new Vector2(w, 52f), HalloweenUI.Grey, click, out _, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 20f);

        private static void Paint() {
            void C(string k, bool on) { if (toolButtons.TryGetValue(k, out var b) && b != null) HalloweenUI.Recolor(b, on ? HalloweenUI.Teal : HalloweenUI.Grey); }
            C("paint", !Erase); C("erase", Erase); C("small", !Big); C("big", Big); C("mirror", Mirror);
        }

        internal static void Submit() {
            if (carveRoot == null) return;
            PumpkinCarving.SubmitLocal(Bits);
            CloseCarve();
        }

        internal static void CloseCarve() {
            if (carveRoot != null) UnityEngine.Object.Destroy(carveRoot);
            carveRoot = null;
            gridRect = null;
            timerText = null;
            toolButtons.Clear();
            lastCol = lastRow = -1;
            if (voteRoot == null) Freeze(false);
        }

        /// <summary>Paints (or erases) one brush stamp at a cell; also the self test's way of drawing.</summary>
        internal static void Stamp(int col, int row, bool erase) {
            int r = Big ? 1 : 0;
            for (int dy = -r; dy <= r; dy++)
                for (int dx = -r; dx <= r; dx++) {
                    if (dx != 0 && dy != 0) continue;   // thick = a small plus
                    PumpkinCarving.Set(Bits, col + dx, row + dy, !erase);
                    if (Mirror) PumpkinCarving.Set(Bits, PumpkinCarving.Grid - 1 - (col + dx), row + dy, !erase);
                }
            dirty = true;
        }

        private static void Stroke(int c0, int r0, int c1, int r1, bool erase) {
            int n = Mathf.Max(Mathf.Abs(c1 - c0), Mathf.Abs(r1 - r0));
            for (int i = 0; i <= n; i++) {
                float t = n == 0 ? 0f : (float)i / n;
                Stamp(Mathf.RoundToInt(Mathf.Lerp(c0, c1, t)), Mathf.RoundToInt(Mathf.Lerp(r0, r1, t)), erase);
            }
        }

        internal static void Tick() {
            if (carveRoot != null) CarveTick();
            if (voteRoot != null) VoteTick();
        }

        private static void CarveTick() {
            float left = carveEndsAt - Time.realtimeSinceStartup;
            if (timerText != null) {
                HalloweenUI.SetText(timerText, Mathf.Max(0, Mathf.CeilToInt(left)).ToString());
                timerText.color = left < 10f ? HalloweenUI.Bad : Color.white;
            }
            if (left <= 0f && !LobbyGamesDiag.HoldTimer) { Submit(); return; }
            if (Input.GetKeyDown(KeyCode.Escape)) { CloseCarve(); return; }
            bool lmb = Input.GetMouseButton(0), rmb = Input.GetMouseButton(1);
            if ((lmb || rmb) && gridRect != null
                && RectTransformUtility.ScreenPointToLocalPointInRectangle(gridRect, Input.mousePosition, null, out Vector2 local)) {
                var size = gridRect.rect.size;
                // pivot top-left: x 0..w, y -h..0
                float fx = (local.x - gridRect.rect.xMin) / size.x, fy = (gridRect.rect.yMax - local.y) / size.y;
                if (fx >= 0f && fx < 1f && fy >= 0f && fy < 1f) {
                    int col = Mathf.FloorToInt(fx * PumpkinCarving.Grid), row = Mathf.FloorToInt(fy * PumpkinCarving.Grid);
                    bool erase = rmb || Erase;
                    if (lastCol >= 0) Stroke(lastCol, lastRow, col, row, erase); else Stamp(col, row, erase);
                    lastCol = col; lastRow = row;
                } else lastCol = lastRow = -1;
            } else lastCol = lastRow = -1;
            if (dirty) { dirty = false; carveTex = LobbyArt.FaceTexture(Bits, PumpkinCarving.Lit, carveTex); }
        }

        // ---------------------------------------------------------------- vote window
        private static GameObject voteRoot;
        private static int builtVersion = -1, builtSecs = -1;
        private static float resultCloseAt = -1f;
        internal static bool VoteOpen => voteRoot != null;

        internal static void OpenVote() {
            if (carveRoot != null) return;           // finish carving first; the card offers the vote afterwards
            BuildVote();
        }

        internal static void ShowResult() {
            if (carveRoot != null) return;
            resultCloseAt = Time.realtimeSinceStartup + 10f;
            BuildVote();
        }

        internal static void CloseVote() {
            if (voteRoot != null) UnityEngine.Object.Destroy(voteRoot);
            voteRoot = null;
            builtVersion = -1;
            resultCloseAt = -1f;
            if (carveRoot == null) Freeze(false);
        }

        internal static void CloseAll() { CloseCarve(); CloseVote(); }

        private static void VoteTick() {
            if (Input.GetKeyDown(KeyCode.Escape)) { CloseVote(); return; }
            if (resultCloseAt > 0f && Time.realtimeSinceStartup >= resultCloseAt && !LobbyGamesDiag.HoldTimer) { CloseVote(); return; }
            int secs = PumpkinCarving.VoteSecondsLeft();
            if (builtVersion != PumpkinCarving.Version || (PumpkinCarving.VotePhase == 1 && secs != builtSecs)) BuildVote();
        }

        private static void BuildVote() {
            try {
                if (voteRoot != null) UnityEngine.Object.Destroy(voteRoot);
                builtVersion = PumpkinCarving.Version;
                builtSecs = PumpkinCarving.VoteSecondsLeft();
                Freeze(true);
                voteRoot = HalloweenUI.Canvas("PumpkinVote", 9600, true);
                HalloweenUI.Backdrop(voteRoot, () => CloseVote());
                const float W = 1500f, Pad = 34f;
                int rowsShown = Mathf.Clamp((Mathf.Min(PumpkinCarving.Faces.Count, 15) + 4) / 5, 1, 3);
                float H = PumpkinCarving.VotePhase == 2 ? 760f : 190f + rowsShown * 246f + 30f;
                var card = HalloweenUI.CenterPanel(voteRoot, new Vector2(W, H));
                HalloweenUI.Title(card, T("Pumpkin Vote", "Kürbis-Wahl"), 16f, 34f, LobbyGames.Pumpkin);
                HalloweenUI.Button(card, "X", new Vector2(-HalloweenUI.FrameW - 12f, -HalloweenUI.FrameW - 12f), new Vector2(54f, 54f), HalloweenUI.Red, () => CloseVote(),
                    out _, new Vector2(1, 1), new Vector2(1, 1), new Vector2(1, 1), 36f);
                var lp = PlayerControl.LocalPlayer;
                byte me = lp != null ? lp.PlayerId : PumpkinCarving.None;

                if (PumpkinCarving.VotePhase == 2 && PumpkinCarving.WinnerFace != null) {
                    LanternImage(card, PumpkinCarving.WinnerFace, new Vector2(W / 2f - 230f, -130f), 460f, true);
                    HalloweenUI.Text(card, PumpkinCarving.WinnerName, 46f, new Color(1f, 0.85f, 0.3f), new Vector2(Pad, -610f), new Vector2(W - 2 * Pad, 60f),
                        TMPro.FontStyles.Bold, TMPro.TextAlignmentOptions.Top);
                    int votes = PumpkinCarving.Tally.TryGetValue(PumpkinCarving.WinnerId, out int v) ? v : 0;
                    HalloweenUI.Text(card, T($"wins with {votes} vote(s). The pumpkin stands at the spawn point next round.",
                                             $"gewinnt mit {votes} Stimme(n). Der Kürbis steht in der nächsten Runde am Startpunkt."),
                        24f, HalloweenUI.Muted, new Vector2(Pad, -680f), new Vector2(W - 2 * Pad, 40f), TMPro.FontStyles.Normal, TMPro.TextAlignmentOptions.Top);
                    return;
                }

                bool open = PumpkinCarving.VotePhase == 1;
                HalloweenUI.Text(card, open
                        ? T($"Pick the best pumpkin (not your own). {builtSecs} s left.", $"Wähle den besten Kürbis (nicht deinen eigenen). Noch {builtSecs} s.")
                        : T("No vote running.", "Keine Abstimmung."),
                    24f, Color.white, new Vector2(Pad, -110f), new Vector2(W - 2 * Pad - 300f, 36f), TMPro.FontStyles.Bold);
                if (open && LobbyGames.CanEdit())
                    HalloweenUI.Button(card, T("End now", "Jetzt beenden"), new Vector2(-Pad, -100f), new Vector2(260f, 50f), HalloweenUI.Amber,
                        () => PumpkinCarving.HostEndVote(false), out _, new Vector2(1, 1), new Vector2(1, 1), new Vector2(1, 1), 20f);

                const int cols = 5;
                float tw = (W - 2 * Pad - (cols - 1) * 16f) / cols, th = 230f;
                int i = 0;
                foreach (var kv in PumpkinCarving.Faces.OrderBy(k => k.Key)) {
                    byte pid = kv.Key;
                    bool mine = pid == me, chosen = pid == PumpkinCarving.MyBallot;
                    var pos = new Vector2(Pad + (i % cols) * (tw + 16f), -170f - (i / cols) * (th + 16f));
                    var tile = new GameObject("Tile");
                    tile.transform.SetParent(card.transform, false);
                    var rt = HalloweenUI.Rect(tile, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1));
                    rt.anchoredPosition = pos; rt.sizeDelta = new Vector2(tw, th);
                    HalloweenUI.Stretch(HalloweenUI.Rounded(tile, chosen ? HalloweenUI.FieldLight : HalloweenUI.Field, HalloweenUI.RadiusTile));
                    if (chosen) HalloweenUI.Stretch(HalloweenUI.Ring(tile, HalloweenUI.Green, HalloweenUI.RadiusTile, 4));
                    LanternImage(tile, kv.Value, new Vector2(tw / 2f - 75f, -8f), 150f, false);
                    HalloweenUI.Text(tile, LobbyGames.NameOf(pid), 20f, Color.white, new Vector2(8f, -160f), new Vector2(tw - 16f, 30f),
                        TMPro.FontStyles.Bold, TMPro.TextAlignmentOptions.Top);
                    int votes = PumpkinCarving.Tally.TryGetValue(pid, out int nv) ? nv : 0;
                    HalloweenUI.Text(tile, mine ? T("your pumpkin", "dein Kürbis") : T($"{votes} vote(s)", $"{votes} Stimme(n)"), 17f, HalloweenUI.Muted,
                        new Vector2(8f, -192f), new Vector2(tw - 16f, 26f), TMPro.FontStyles.Normal, TMPro.TextAlignmentOptions.Top);
                    if (open && !mine) HalloweenUI.Hover(tile, HalloweenUI.RadiusTile, () => PumpkinCarving.CastLocal(pid));
                    i++;
                    if (i >= 15) break;
                }
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogWarning($"{LobbyGames.LogPrefix} vote window failed: {e}");
                CloseVote();
            }
        }

        // ---------------------------------------------------------------- pieces
        private static readonly Dictionary<string, Texture2D> uiFaces = new();

        /// <summary>A lantern as UI: halo, pumpkin, the face on its field (x 40-120, y 50-130 of 160), crown on top.</summary>
        internal static void LanternImage(GameObject parent, byte[] bits, Vector2 topLeft, float size, bool crown) {
            float s = size / LobbyArt.LanternSize;
            var glow = Img(parent, LobbyArt.UiSprite("glow", LobbyArt.LanternGlow()), topLeft, new Vector2(size, size));
            glow.raycastTarget = false;
            Img(parent, LobbyArt.UiSprite("lantern", LobbyArt.Lantern()), topLeft, new Vector2(size, size)).raycastTarget = false;
            string key = Convert.ToBase64String(bits);
            if (!uiFaces.TryGetValue(key, out var tex) || tex == null) {
                if (uiFaces.Count > 64) TrimFaces();
                tex = LobbyArt.FaceTexture(bits, PumpkinCarving.Lit);
                uiFaces[key] = tex;
            }
            Raw(parent, tex, topLeft + new Vector2(LobbyArt.LanternFaceX * s, -LobbyArt.LanternFaceY * s),
                new Vector2(LobbyArt.LanternFaceW * s, LobbyArt.LanternFaceW * s)).raycastTarget = false;
            if (crown) Img(parent, LobbyArt.UiSprite("crown", LobbyArt.Crown()), topLeft + new Vector2(size * 0.32f, size * 0.14f), new Vector2(size * 0.36f, size * 0.36f)).raycastTarget = false;
        }

        // The cache was emptied without Destroy, the textures (DontUnloadUnusedAsset) stayed for the whole session
        // (audit 21.10.). Rare (more than 64 faces): every face no open window shows right now is destroyed.
        private static void TrimFaces() {
            var inUse = new HashSet<IntPtr>();
            try {
                foreach (var ri in UnityEngine.Object.FindObjectsOfType<RawImage>())
                    if (ri != null && ri.texture != null) inUse.Add(ri.texture.Pointer);
            } catch { }
            var keep = new Dictionary<string, Texture2D>();
            foreach (var kv in uiFaces) {
                if (kv.Value == null) continue;
                if (inUse.Contains(kv.Value.Pointer)) keep[kv.Key] = kv.Value;
                else UnityEngine.Object.Destroy(kv.Value);
            }
            uiFaces.Clear();
            foreach (var kv in keep) uiFaces[kv.Key] = kv.Value;
        }

        private static Image Img(GameObject parent, Sprite sprite, Vector2 topLeft, Vector2 size) {
            var go = new GameObject("Img");
            go.transform.SetParent(parent.transform, false);
            var rt = HalloweenUI.Rect(go, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1));
            rt.anchoredPosition = topLeft; rt.sizeDelta = size;
            var img = go.AddComponent<Image>();
            img.sprite = sprite;
            img.preserveAspect = true;
            img.raycastTarget = false;
            return img;
        }

        private static RawImage Raw(GameObject parent, Texture tex, Vector2 topLeft, Vector2 size) {
            var go = new GameObject("Raw");
            go.transform.SetParent(parent.transform, false);
            var rt = HalloweenUI.Rect(go, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1));
            rt.anchoredPosition = topLeft; rt.sizeDelta = size;
            var img = go.AddComponent<RawImage>();
            img.texture = tex;
            img.raycastTarget = false;
            return img;
        }

        // the player stands still while a window is open (clicks would walk otherwise)
        private static bool frozen;
        private static void Freeze(bool on) {
            try {
                var lp = PlayerControl.LocalPlayer;
                if (lp == null) { frozen = false; return; }
                if (on && !frozen) { if (lp.moveable) { lp.moveable = false; frozen = true; } }
                else if (!on && frozen) { lp.moveable = true; frozen = false; }
            } catch { frozen = false; }
        }
    }
}
