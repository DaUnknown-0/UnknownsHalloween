// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Trick or Treat: everything you see and hear (TrickOrTreat.cs holds the rules and the network).
 *
 *  - Candies: thirteen pictures (Resources/treats/candy_<kind>.png, 256 px, floor shadow baked in), DXT5 at
 *    runtime, on the world layer 11. Without the resources the old runtime drawings (Draw) stand in.
 *  - The eater's card: candy_card.png (640x200) with the candy in the left field (x 26-194) and kind, effect name
 *    and one line in the right field (x 210-614), top of the screen, only on the eater's client.
 *    A small list of the eater's running effects on the left edge.
 *  - Effects with a picture: glow and crows (every client), Echo Drop silhouettes, blur, sway, fake sabotage,
 *    Guiding Mint arrow (eater only). Sounds (crunch, hiccup, alarm) are synthesised like the Banshee's wail.
 *  - Screen overlays live on the UI layer (5) above the light system's shadow, positioned through the UI camera.
 */

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using TMPro;
using UnityEngine;
using TheOtherRoles;

namespace UnknownsHalloween {
    internal static class TreatFx {
        private const string LogPrefix = TrickOrTreat.LogPrefix;

        // ================================================================ texts
        internal static string Name(Treat fx) {
            switch (fx) {
                case Treat.IronTaffy: return "Iron Taffy";
                case Treat.SugarRush: return "Sugar Rush";
                case Treat.CinnamonStick: return "Cinnamon Stick";
                case Treat.NightOwl: return "Night Owl";
                case Treat.ShortcutCaramel: return "Shortcut Caramel";
                case Treat.PrizeInside: return "Prize Inside";
                case Treat.GuidingMint: return "Guiding Mint";
                case Treat.LuckyLolly: return "Lucky Lolly";
                case Treat.EchoDrop: return "Echo Drop";
                case Treat.RockCandy: return "Rock Candy";
                case Treat.FogFudge: return "Fog Fudge";
                case Treat.ExtraChore: return "Extra Chore";
                case Treat.Hiccups: return "Hiccups";
                case Treat.LightsOut: return "Lights Out";
                case Treat.Earmuffs: return "Earmuffs";
                case Treat.Jinkies: return "Jinkies";
                case Treat.Butterfingers: return "Butterfingers";
                case Treat.Glowing: return "Glowing";
                case Treat.CrowCompany: return "Crow Company";
                case Treat.Gobstopper: return "Gobstopper";
                case Treat.HardCandy: return "Hard Candy";
                case Treat.Brittle: return "Brittle";
                case Treat.Nausea: return "Nausea";
                case Treat.Regurgitate: return "Regurgitate";
                case Treat.VolatileStarlight: return "Volatile Starlight";
                case Treat.NothingQ: return "Nothing?";
                case Treat.SwapSweet: return "Swap Sweet";
                case Treat.ShrinkSherbet: return "Shrink Sherbet";
                case Treat.BigBite: return "Big Bite";
                case Treat.DoubleDip: return "Double Dip";
                case Treat.CandyCornCompass: return "Candy Corn Compass";
                case Treat.PeekAPop: return "Peek-a-Pop";
                case Treat.StickyToffee: return "Sticky Toffee";
                case Treat.VentMint: return "Vent Mint";
                case Treat.FizzPop: return "Fizz Pop";
                case Treat.HomingHumbug: return "Homing Humbug";
                case Treat.TattletaleTaffy: return "Tattletale Taffy";
                case Treat.BrainFreeze: return "Brain Freeze";
                case Treat.ReverseGummy: return "Reverse Gummy";
                case Treat.WrapperTrail: return "Wrapper Trail";
                case Treat.SugarCrash: return "Sugar Crash";
                case Treat.CopycatCaramel: return "Copycat Caramel";
                case Treat.GhostlyGum: return "Ghostly Gum";
                default: return fx.ToString();
            }
        }

        private static string Rounds(bool de) {
            int n = TrickOrTreat.MeetingsFor();
            if (de) return n == 1 ? "bis zum nächsten Meeting" : $"für {n} Meetings";
            return n == 1 ? "until the next meeting" : $"for {n} meetings";
        }

        internal static string Line(Treat fx, bool imp, byte param) {
            bool de = TrickOrTreat.De();
            string r = Rounds(de);
            switch (fx) {
                case Treat.IronTaffy:
                    return imp ? (de ? $"Der nächste Sheriff-Schuss auf dich scheitert ({r})." : $"The next Sheriff shot at you fails ({r}).")
                               : (de ? $"Der nächste Kill gegen dich scheitert ({r})." : $"The next kill on you fails ({r}).");
                case Treat.SugarRush: return de ? "5 s lang 40 % schneller." : "40% faster for 5 s.";
                case Treat.CinnamonStick: return de ? $"8 % schneller, {r}." : $"8% faster, {r}.";
                case Treat.NightOwl: return de ? $"20 % mehr Sicht, {r}." : $"20% more vision, {r}.";
                case Treat.ShortcutCaramel:
                    return imp ? (de ? "Deine Kill-Abklingzeit sinkt einmal um 2,5 s." : "Your kill cooldown drops by 2.5 s, once.")
                               : (de ? "Eine deiner Aufgaben ist erledigt." : "One of your tasks is done.");
                case Treat.PrizeInside:
                    return imp ? (de ? "Die Sabotage-Abklingzeit steht auf 0." : "The sabotage cooldown is back to 0.")
                               : (de ? "Ein offener Aufgabenschritt hat sich selbst erledigt." : "An open task step finished itself.");
                case Treat.GuidingMint: return de ? "20 s lang zeigt ein Pfeil zur nächsten Leiche." : "For 20 s an arrow points to the nearest body.";
                case Treat.LuckyLolly: return de ? "Du hast einen Notfallknopf mehr." : "You get one more emergency meeting.";
                case Treat.EchoDrop: return de ? "10 s lang siehst du Spieler im Umkreis von 6 m durch Wände." : "For 10 s you see players within 6 m through walls.";
                case Treat.RockCandy: return de ? "30 s lang 30 % langsamer." : "30% slower for 30 s.";
                case Treat.FogFudge: return de ? "60 s lang 25 % weniger Sicht." : "25% less vision for 60 s.";
                case Treat.ExtraChore:
                    return imp ? (de ? "Deine Kill-Abklingzeit wächst einmal um 2,5 s." : "Your kill cooldown grows by 2.5 s, once.")
                               : (de ? "Du hast eine Aufgabe mehr." : "You got one more task.");
                case Treat.Hiccups: return de ? "60 s Schluckauf. Wer in der Nähe ist, hört ihn." : "60 s of hiccups. Players nearby can hear them.";
                case Treat.LightsOut: return de ? "10 s lang gehen deine Lichter aus. Nur deine." : "Your lights go out for 10 s. Only yours.";
                case Treat.Earmuffs: return de ? "60 s lang hörst du keine Spielgeräusche." : "No game sounds for you for 60 s.";
                case Treat.Jinkies: return de ? "20 s lang verschwimmt deine Sicht." : "Your sight blurs for 20 s.";
                case Treat.Butterfingers:
                    return imp ? (de ? "30 s lang kein Venten und kein Kill." : "No venting and no kill for 30 s.")
                               : (de ? "30 s lang kannst du keine Aufgaben öffnen." : "You cannot open tasks for 30 s.");
                case Treat.Glowing: return de ? "60 s lang leuchtest du, auch im Dunkeln." : "You glow for 60 s, even in the dark.";
                case Treat.CrowCompany: return de ? "30 s lang kreisen Krähen über dir. Alle sehen sie." : "Crows circle above you for 30 s. Everyone sees them.";
                case Treat.Gobstopper: return de ? $"Dein Notfallknopf ist weg, {r}." : $"Your emergency button is gone, {r}.";
                case Treat.HardCandy: return de ? $"10 % langsamer, dafür gegen einen Kill gepanzert ({r})." : $"10% slower, but armored against one kill ({r}).";
                case Treat.Brittle: return de ? $"15 % schneller, 20 % weniger Sicht, {r}." : $"15% faster, 20% less vision, {r}.";
                case Treat.Nausea: return de ? "20 s lang schwankt dein Bild, dafür 20 % schneller." : "Your view sways for 20 s, but you are 20% faster.";
                case Treat.Regurgitate: return de ? "Die Wirkung deiner letzten Süßigkeit ist weg." : "The effect of your last candy is gone.";
                case Treat.NothingQ: return de ? "Nichts passiert. Oder doch?" : "Nothing happens. Or does it?";
                case Treat.SwapSweet: {
                    var t = Helpers.playerById(param);
                    string n = t != null && t.Data != null ? t.Data.PlayerName : "?";
                    return de ? $"30 s lang siehst du für alle aus wie {n}." : $"For 30 s you look like {n} to everyone.";
                }
                case Treat.ShrinkSherbet: return de ? $"Du bist kleiner und 5 % schneller, {r}." : $"You are smaller and 5% faster, {r}.";
                case Treat.BigBite: return de ? $"Du bist größer und 5 % langsamer, {r}." : $"You are bigger and 5% slower, {r}.";
                case Treat.DoubleDip: return de ? "Deine Stimme zählt im nächsten Meeting doppelt." : "Your vote counts twice in the next meeting.";
                case Treat.CandyCornCompass: return de ? "15 s lang zeigt ein Pfeil zum nächsten lebenden Spieler." : "For 15 s an arrow points to the nearest living player.";
                case Treat.PeekAPop: return de ? "5 s lang siehst du die Admin-Karte." : "You see the admin map for 5 s.";
                case Treat.StickyToffee: return de ? $"Wer dich tötet, klebt danach 5 s lang fest ({r})." : $"Whoever kills you is stuck for 5 s afterwards ({r}).";
                case Treat.VentMint:
                    return imp ? (de ? $"Zwei Vents sind für dich verbunden, {r}." : $"Two vents are linked for you, {r}.")
                               : (de ? $"Du darfst einmal venten ({r})." : $"You may use a vent once ({r}).");
                case Treat.FizzPop: return de ? "15 s lang siehst du die Fußspuren aller Spieler." : "For 15 s you see everyone's footprints.";
                case Treat.HomingHumbug: return de ? $"Ein Knopf bringt dich einmal zurück zum Treffpunkt ({r})." : $"A button takes you back to the meeting spot once ({r}).";
                case Treat.TattletaleTaffy: return de ? "Die Impostoren sehen dich 10 s lang, im nächsten Meeting alle, wo du warst." : "The impostors see you for 10 s, the next meeting tells everyone where you were.";
                case Treat.BrainFreeze: return de ? "3 s lang eingefroren." : "Frozen for 3 s.";
                case Treat.ReverseGummy: return de ? "10 s lang ist deine Steuerung vertauscht." : "Your controls are reversed for 10 s.";
                case Treat.WrapperTrail: return de ? "30 s lang hinterlässt du eine Spur aus Bonbonpapier." : "For 30 s you leave a trail of candy wrappers.";
                case Treat.SugarCrash: return de ? "20 s lang 30 % schneller, dann 20 s lang 30 % langsamer." : "30% faster for 20 s, then 30% slower for 20 s.";
                case Treat.GhostlyGum: return de ? "20 s lang bist du für alle halb durchsichtig." : "You are half see-through for everyone for 20 s.";
                default: return "";
            }
        }

        // Good, bad or odd: only the colour of the name on the card.
        internal static Color Tint(Treat fx) {
            switch (fx) {
                case Treat.IronTaffy: case Treat.SugarRush: case Treat.CinnamonStick: case Treat.NightOwl: case Treat.ShortcutCaramel:
                case Treat.PrizeInside: case Treat.GuidingMint: case Treat.LuckyLolly: case Treat.EchoDrop:
                case Treat.DoubleDip: case Treat.CandyCornCompass: case Treat.PeekAPop: case Treat.StickyToffee: case Treat.VentMint:
                case Treat.FizzPop: case Treat.HomingHumbug:
                    return new Color(0.55f, 1f, 0.45f);
                case Treat.RockCandy: case Treat.FogFudge: case Treat.ExtraChore: case Treat.Hiccups: case Treat.LightsOut:
                case Treat.Earmuffs: case Treat.Jinkies: case Treat.Butterfingers: case Treat.Glowing: case Treat.CrowCompany: case Treat.Gobstopper:
                case Treat.TattletaleTaffy: case Treat.BrainFreeze: case Treat.ReverseGummy: case Treat.WrapperTrail:
                    return new Color(1f, 0.45f, 0.4f);
                default:
                    return new Color(0.85f, 0.6f, 1f);
            }
        }

        private static string Hex(Color c) => ColorUtility.ToHtmlStringRGB(c);

        // ================================================================ drawing
        internal sealed class Canvas {
            public readonly int W, H;
            public readonly Color[] Px;
            public Canvas(int w, int h) { W = w; H = h; Px = new Color[w * h]; }

            private void Put(int x, int y, Color c, float cov) {
                if (x < 0 || y < 0 || x >= W || y >= H || cov <= 0f) return;
                float a = c.a * Mathf.Clamp01(cov);
                var d = Px[y * W + x];
                float oa = a + d.a * (1f - a);
                if (oa <= 0f) return;
                Px[y * W + x] = new Color((c.r * a + d.r * d.a * (1f - a)) / oa, (c.g * a + d.g * d.a * (1f - a)) / oa, (c.b * a + d.b * d.a * (1f - a)) / oa, oa);
            }

            public void Ellipse(float cx, float cy, float rx, float ry, Color c) {
                for (int y = (int)(cy - ry - 2); y <= cy + ry + 2; y++)
                    for (int x = (int)(cx - rx - 2); x <= cx + rx + 2; x++) {
                        float dx = (x + 0.5f - cx) / rx, dy = (y + 0.5f - cy) / ry;
                        float d = (Mathf.Sqrt(dx * dx + dy * dy) - 1f) * Mathf.Min(rx, ry);
                        Put(x, y, c, 0.5f - d);
                    }
            }
            public void Disc(float cx, float cy, float r, Color c) => Ellipse(cx, cy, r, r, c);

            public void Ring(float cx, float cy, float rx, float ry, float w, Color c) {
                for (int y = (int)(cy - ry - w - 2); y <= cy + ry + w + 2; y++)
                    for (int x = (int)(cx - rx - w - 2); x <= cx + rx + w + 2; x++) {
                        float dx = (x + 0.5f - cx) / rx, dy = (y + 0.5f - cy) / ry;
                        float d = Mathf.Abs(Mathf.Sqrt(dx * dx + dy * dy) - 1f) * Mathf.Min(rx, ry);
                        Put(x, y, c, w * 0.5f + 0.5f - d);
                    }
            }

            public void Line(float x0, float y0, float x1, float y1, float w, Color c) {
                float minx = Mathf.Min(x0, x1) - w - 2, maxx = Mathf.Max(x0, x1) + w + 2, miny = Mathf.Min(y0, y1) - w - 2, maxy = Mathf.Max(y0, y1) + w + 2;
                var a = new Vector2(x0, y0); var ab = new Vector2(x1 - x0, y1 - y0);
                float len2 = Mathf.Max(ab.sqrMagnitude, 0.0001f);
                for (int y = (int)miny; y <= maxy; y++)
                    for (int x = (int)minx; x <= maxx; x++) {
                        var p = new Vector2(x + 0.5f, y + 0.5f);
                        float t = Mathf.Clamp01(Vector2.Dot(p - a, ab) / len2);
                        float d = Vector2.Distance(p, a + ab * t);
                        Put(x, y, c, w * 0.5f + 0.5f - d);
                    }
            }

            public void Rect(float x0, float y0, float x1, float y1, Color c) {
                for (int y = (int)y0 - 1; y <= y1 + 1; y++)
                    for (int x = (int)x0 - 1; x <= x1 + 1; x++) {
                        float cx = Mathf.Min(x + 1f, x1) - Mathf.Max(x, x0), cy = Mathf.Min(y + 1f, y1) - Mathf.Max(y, y0);
                        Put(x, y, c, Mathf.Clamp01(cx) * Mathf.Clamp01(cy));
                    }
            }

            public void Tri(float ax, float ay, float bx, float by, float cx, float cy, Color c) {
                float minx = Mathf.Min(ax, Mathf.Min(bx, cx)), maxx = Mathf.Max(ax, Mathf.Max(bx, cx));
                float miny = Mathf.Min(ay, Mathf.Min(by, cy)), maxy = Mathf.Max(ay, Mathf.Max(by, cy));
                for (int y = (int)miny - 1; y <= maxy + 1; y++)
                    for (int x = (int)minx - 1; x <= maxx + 1; x++) {
                        int hit = 0;
                        for (int s = 0; s < 4; s++) {
                            float px = x + 0.25f + 0.5f * (s & 1), py = y + 0.25f + 0.5f * (s >> 1);
                            float d1 = (px - bx) * (ay - by) - (ax - bx) * (py - by);
                            float d2 = (px - cx) * (by - cy) - (bx - cx) * (py - cy);
                            float d3 = (px - ax) * (cy - ay) - (cx - ax) * (py - ay);
                            bool neg = d1 < 0 || d2 < 0 || d3 < 0, pos = d1 > 0 || d2 > 0 || d3 > 0;
                            if (!(neg && pos)) hit++;
                        }
                        Put(x, y, c, hit / 4f);
                    }
            }

            public void Erase(float cx, float cy, float r) {
                for (int y = (int)(cy - r - 2); y <= cy + r + 2; y++)
                    for (int x = (int)(cx - r - 2); x <= cx + r + 2; x++) {
                        if (x < 0 || y < 0 || x >= W || y >= H) continue;
                        float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(cx, cy)) - r;
                        float keep = Mathf.Clamp01(d + 0.5f);
                        var p = Px[y * W + x]; p.a *= keep; Px[y * W + x] = p;
                    }
            }

            // a dark rim around everything drawn (reads on any floor)
            public void Outline(Color c, int w) {
                var src = (Color[])Px.Clone();
                for (int y = 0; y < H; y++)
                    for (int x = 0; x < W; x++) {
                        float best = 0f;
                        for (int oy = -w; oy <= w; oy++)
                            for (int ox = -w; ox <= w; ox++) {
                                int sx = x + ox, sy = y + oy;
                                if (sx < 0 || sy < 0 || sx >= W || sy >= H || ox * ox + oy * oy > w * w + 1) continue;
                                best = Mathf.Max(best, src[sy * W + sx].a);
                            }
                        var d = src[y * W + x];
                        if (best <= d.a) continue;
                        float a = best - d.a;          // rim only where the drawing is not
                        float oa = d.a + a * c.a;
                        Px[y * W + x] = new Color(Mathf.Lerp(c.r, d.r, d.a / Mathf.Max(oa, 0.001f)), Mathf.Lerp(c.g, d.g, d.a / Mathf.Max(oa, 0.001f)), Mathf.Lerp(c.b, d.b, d.a / Mathf.Max(oa, 0.001f)), oa);
                    }
            }

            public Texture2D ToTexture(string name) {
                var tex = new Texture2D(W, H, TextureFormat.RGBA32, false) { name = name, filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp };
                tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                tex.SetPixels(Px);
                tex.Apply(false, false);
                return tex;
            }
        }

        internal static Color C(float r, float g, float b, float a = 1f) => new Color(r, g, b, a);

        private static Texture2D[] kindTex;
        private static Sprite[] kindSprites;
        internal const float CandyWorldSize = 0.42f;

        internal static Texture2D KindTexture(int k) {
            if (kindTex == null || kindTex[k] == null) BuildKinds();
            return kindTex[k];
        }

        internal static Sprite KindSprite(int k) {
            if (kindSprites == null || kindSprites[k] == null) BuildKinds();
            return kindSprites[k];
        }

        // ---- artwork from the resources (Grafik-Lieferung 2026-10-20) ----
        private const string TreatRes = "UnknownsHalloween.Resources.treats.";
        // Picture size of a candy in the world. The 256 px pictures carry margin and the floor shadow, so the
        // candy itself ends up about as big as the old 64 px drawing at CandyWorldSize.
        internal const float CandyPictureSize = 0.5f;
        // Where the floor sits in the picture (from the bottom): the baked shadow's middle.
        private const float CandyFloorPivot = 0.09f;
        private static bool[] kindIsPicture;

        /// <summary>File name of a kind's picture, e.g. candy_midnight_bonbon.png.</summary>
        internal static string KindFile(int k) =>
            "candy_" + new string(TrickOrTreat.KindNames[k].ToLowerInvariant().Select(ch => char.IsLetterOrDigit(ch) ? ch : '_').ToArray()) + ".png";

        internal static byte[] ReadTreatRes(string file) {
            try {
                using var stream = System.Reflection.Assembly.GetExecutingAssembly().GetManifestResourceStream(TreatRes + file);
                if (stream == null) return null;
                var data = new byte[stream.Length];
                int read = 0;
                while (read < data.Length) {
                    int n = stream.Read(data, read, data.Length - read);
                    if (n <= 0) break;
                    read += n;
                }
                return read == data.Length ? data : null;
            } catch { return null; }
        }

        // PNG -> DXT5 with mipmaps and without a CPU copy (same diet as the costume hats).
        internal static Texture2D LoadTreatTexture(string file) {
            try {
                var data = ReadTreatRes(file);
                if (data == null) return null;
                var tex = new Texture2D(2, 2, TextureFormat.ARGB32, true) { name = "treat_" + file };
                if (!ImageConversion.LoadImage(tex, data, false)) { UnityEngine.Object.Destroy(tex); return null; }
                tex.wrapMode = TextureWrapMode.Clamp;
                tex.filterMode = FilterMode.Bilinear;
                try { tex.Compress(true); } catch { }
                tex.Apply(false, true);
                tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                return tex;
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} picture {file} failed: {e.Message}");
                return null;
            }
        }

        private static Sprite cardSprite, menuIconSprite;
        private static bool cardTried, menuIconTried;

        /// <summary>The empty card (640x200), 1 unit wide; null without the resource.</summary>
        internal static Sprite CardSprite() {
            if (cardTried) return cardSprite;
            cardTried = true;
            var tex = LoadTreatTexture("candy_card.png");
            if (tex == null) return null;
            cardSprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), tex.width);
            cardSprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return cardSprite;
        }

        /// <summary>Pumpkin pail with candies (128 px) for the menu; falls back to the Midnight Bonbon.</summary>
        internal static Sprite MenuIcon() {
            if (menuIconTried) return menuIconSprite ?? KindSprite(TrickOrTreat.PoisonKind);
            menuIconTried = true;
            var tex = LoadTreatTexture("candy_menu_icon.png");
            if (tex != null) {
                menuIconSprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), tex.width);
                menuIconSprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            }
            return menuIconSprite ?? KindSprite(TrickOrTreat.PoisonKind);
        }

        /// <summary>True when kind k shows the delivered picture (shadow included), false for the runtime drawing.</summary>
        internal static bool KindIsPicture(int k) {
            if (kindIsPicture == null) BuildKinds();
            return kindIsPicture[k];
        }

        private static void BuildKinds() {
            kindTex = new Texture2D[TrickOrTreat.KindCount + 1];
            kindSprites = new Sprite[TrickOrTreat.KindCount + 1];
            var isPic = new bool[TrickOrTreat.KindCount + 1];
            for (int k = 0; k <= TrickOrTreat.KindCount; k++) {
                var tex = LoadTreatTexture(KindFile(k));
                Sprite s;
                if (tex != null) {
                    kindTex[k] = tex;
                    isPic[k] = true;
                    s = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, CandyFloorPivot), tex.width / CandyPictureSize);
                } else {
                    var cv = new Canvas(64, 64);
                    Draw(cv, k);
                    cv.Outline(C(0.08f, 0.04f, 0.1f), 2);
                    kindTex[k] = cv.ToTexture("treat_" + k);
                    s = Sprite.Create(kindTex[k], new Rect(0, 0, 64, 64), new Vector2(0.5f, 0.5f), 64f / CandyWorldSize);
                }
                s.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                kindSprites[k] = s;
            }
            kindIsPicture = isPic;
        }

        private static void Draw(Canvas c, int k) {
            var white = C(1f, 1f, 1f, 0.6f);
            switch (k) {
                case 0: { // Pumpkin Caramel
                    var o = C(1f, 0.55f, 0.1f); var d = C(0.82f, 0.36f, 0.04f);
                    c.Ellipse(32, 27, 22, 18, o);
                    c.Ring(32, 27, 12, 17.5f, 1.6f, d);
                    c.Line(32, 10, 32, 44, 1.8f, d);
                    c.Rect(29.5f, 43, 34.5f, 53, C(0.3f, 0.55f, 0.15f));
                    c.Ellipse(39, 50, 6, 2.6f, C(0.38f, 0.66f, 0.2f));
                    c.Ellipse(21, 33, 3.5f, 5f, white);
                    break;
                }
                case 1: { // Spider Lolly
                    c.Line(32, 3, 32, 28, 3f, C(0.96f, 0.93f, 0.86f));
                    c.Disc(32, 40, 18, C(0.6f, 0.25f, 0.85f));
                    c.Ring(32, 40, 11, 11, 2.2f, C(0.82f, 0.55f, 1f));
                    var b = C(0.06f, 0.03f, 0.08f);
                    for (int s = -1; s <= 1; s += 2)
                        for (int i = 0; i < 4; i++) {
                            float ly = 44 - i * 3.2f;
                            c.Line(32, 41, 32 + s * 8, ly + 3, 1.3f, b);
                            c.Line(32 + s * 8, ly + 3, 32 + s * 12, ly - 2, 1.3f, b);
                        }
                    c.Disc(32, 39, 4.6f, b);
                    c.Disc(32, 45, 3.2f, b);
                    c.Disc(31, 46, 0.9f, C(1f, 0.2f, 0.2f)); c.Disc(33.2f, 46, 0.9f, C(1f, 0.2f, 0.2f));
                    break;
                }
                case 2: { // Bat Gummy
                    var g = C(0.42f, 0.18f, 0.6f);
                    c.Tri(32, 38, 4, 46, 14, 22, g);
                    c.Tri(32, 38, 60, 46, 50, 22, g);
                    c.Disc(12, 27, 5, g); c.Disc(52, 27, 5, g);
                    c.Erase(19, 24, 4.5f); c.Erase(45, 24, 4.5f);
                    c.Ellipse(32, 31, 7.5f, 11, C(0.5f, 0.22f, 0.7f));
                    c.Tri(27, 39, 25, 48, 31, 41, g); c.Tri(37, 39, 39, 48, 33, 41, g);
                    c.Disc(29.3f, 35, 1.8f, C(1f, 0.85f, 0.2f)); c.Disc(34.7f, 35, 1.8f, C(1f, 0.85f, 0.2f));
                    c.Ellipse(29, 28, 1.8f, 3.5f, C(1f, 1f, 1f, 0.35f));
                    break;
                }
                case 3: { // Eyeball Gum
                    c.Disc(32, 32, 20, C(0.97f, 0.95f, 0.9f));
                    var v = C(0.85f, 0.15f, 0.15f);
                    c.Line(13, 30, 22, 31, 1.1f, v); c.Line(22, 31, 25, 27, 1f, v);
                    c.Line(50, 22, 42, 26, 1.1f, v); c.Line(30, 13, 31, 22, 1.1f, v); c.Line(46, 46, 41, 41, 1f, v);
                    c.Disc(35, 35, 8.5f, C(0.2f, 0.55f, 0.9f));
                    c.Disc(35, 35, 4.2f, C(0.03f, 0.03f, 0.06f));
                    c.Disc(38, 38.5f, 2f, C(1f, 1f, 1f, 0.9f));
                    break;
                }
                case 4: { // Tombstone Truffle
                    c.Ellipse(32, 12, 23, 6.5f, C(0.4f, 0.24f, 0.12f));
                    var s = C(0.6f, 0.62f, 0.67f);
                    c.Rect(16, 12, 48, 38, s);
                    c.Disc(32, 38, 16, s);
                    var d = C(0.34f, 0.35f, 0.4f);
                    c.Rect(30, 18, 34, 45, d);
                    c.Rect(24.5f, 34, 39.5f, 38, d);
                    c.Ellipse(21, 40, 2.4f, 5f, white);
                    c.Ellipse(32, 9.5f, 18, 2.2f, C(0.55f, 0.36f, 0.2f));
                    break;
                }
                case 5: { // Witch Licorice
                    c.Line(13, 10, 50, 52, 8f, C(0.13f, 0.07f, 0.17f));
                    for (int i = 1; i < 7; i++) {
                        float t = i / 7f, x = Mathf.Lerp(13, 50, t), y = Mathf.Lerp(10, 52, t);
                        c.Line(x - 3.4f, y + 2.6f, x + 3.4f, y - 2.6f, 2.2f, C(0.6f, 0.22f, 0.8f));
                    }
                    c.Disc(51, 53, 5f, C(0.42f, 0.92f, 0.3f));
                    c.Disc(49.5f, 54.5f, 1.6f, C(1f, 1f, 1f, 0.7f));
                    break;
                }
                case 6: { // Ghost Floss
                    var w = C(0.97f, 0.97f, 1f);
                    c.Line(32, 2, 32, 14, 2.6f, C(0.9f, 0.85f, 0.7f));
                    c.Rect(18, 16, 46, 36, w);
                    c.Disc(32, 38, 14, w);
                    c.Disc(21.5f, 16, 4.2f, w); c.Disc(32, 15, 4.2f, w); c.Disc(42.5f, 16, 4.2f, w);
                    c.Disc(18, 30, 5, C(0.9f, 0.85f, 1f)); c.Disc(46, 30, 5, C(0.9f, 0.85f, 1f));
                    var b = C(0.08f, 0.06f, 0.12f);
                    c.Ellipse(27, 37, 2.6f, 3.6f, b); c.Ellipse(37, 37, 2.6f, 3.6f, b);
                    c.Ellipse(32, 27, 2.2f, 3f, b);
                    break;
                }
                case 7: { // Moon Drop
                    c.Disc(31, 31, 21, C(1f, 0.92f, 0.5f, 0.25f));
                    c.Disc(31, 31, 18, C(1f, 0.93f, 0.55f));
                    c.Erase(40, 37, 14.5f);
                    c.Disc(24, 24, 2.4f, C(0.92f, 0.8f, 0.4f)); c.Disc(20, 33, 1.6f, C(0.92f, 0.8f, 0.4f));
                    c.Disc(48, 18, 2.2f, C(1f, 1f, 0.9f)); c.Disc(53, 30, 1.4f, C(1f, 1f, 0.9f));
                    break;
                }
                case 8: { // Bone Biscuit
                    var b = C(0.94f, 0.88f, 0.72f);
                    c.Rect(17, 27, 47, 37, b);
                    c.Disc(15, 25.5f, 6.5f, b); c.Disc(15, 38.5f, 6.5f, b); c.Disc(49, 25.5f, 6.5f, b); c.Disc(49, 38.5f, 6.5f, b);
                    c.Line(20, 29, 44, 29, 1.6f, C(0.8f, 0.7f, 0.52f));
                    c.Disc(26, 33, 1.1f, C(0.7f, 0.55f, 0.35f)); c.Disc(32, 34, 1.1f, C(0.7f, 0.55f, 0.35f)); c.Disc(38, 33, 1.1f, C(0.7f, 0.55f, 0.35f));
                    break;
                }
                case 9: { // Sour Worm
                    Vector2 prev = Vector2.zero;
                    for (int i = 0; i <= 24; i++) {
                        float t = i / 24f;
                        var p = new Vector2(9 + 44 * t, 31 + 10 * Mathf.Sin(t * Mathf.PI * 2.2f));
                        if (i > 0) c.Line(prev.x, prev.y, p.x, p.y, 8.5f, (i / 3) % 2 == 0 ? C(0.35f, 0.88f, 0.25f) : C(1f, 0.82f, 0.18f));
                        prev = p;
                    }
                    c.Disc(prev.x, prev.y, 4.6f, C(1f, 0.82f, 0.18f));
                    c.Disc(prev.x + 0.5f, prev.y + 1.6f, 1.3f, C(0.05f, 0.05f, 0.05f));
                    for (int i = 0; i < 7; i++) c.Disc(12 + i * 6.5f, 31 + 10 * Mathf.Sin((i * 6.5f + 3) / 44f * Mathf.PI * 2.2f) + 2, 0.8f, C(1f, 1f, 1f, 0.85f));
                    break;
                }
                case 10: { // Candy Apple
                    c.Rect(30.5f, 40, 33.5f, 59, C(0.68f, 0.48f, 0.27f));
                    c.Disc(32, 27, 19, C(0.86f, 0.1f, 0.13f));
                    c.Disc(25, 27, 12, C(0.95f, 0.18f, 0.2f));
                    c.Ellipse(24, 33, 3.5f, 6f, C(1f, 1f, 1f, 0.65f));
                    c.Ellipse(40, 46, 6f, 2.8f, C(0.35f, 0.7f, 0.2f));
                    break;
                }
                case 12: { // Midnight Bonbon: the only wrapped one, glossy black in silver foil, a violet shimmer
                    var foil = C(0.80f, 0.82f, 0.88f); var foilD = C(0.55f, 0.57f, 0.64f);
                    c.Tri(14, 32, 1, 45, 1, 19, foil); c.Tri(50, 32, 63, 45, 63, 19, foil);
                    c.Line(4, 41, 14, 33, 1.2f, foilD); c.Line(4, 23, 14, 31, 1.2f, foilD);
                    c.Line(60, 41, 50, 33, 1.2f, foilD); c.Line(60, 23, 50, 31, 1.2f, foilD);
                    c.Ellipse(13.5f, 32, 3.2f, 5f, foilD); c.Ellipse(50.5f, 32, 3.2f, 5f, foilD);
                    c.Disc(32, 32, 19.5f, C(0.55f, 0.3f, 0.95f, 0.35f));
                    c.Disc(32, 32, 17f, C(0.06f, 0.04f, 0.09f));
                    c.Ring(32, 32, 12f, 12f, 1.4f, C(0.42f, 0.22f, 0.62f));
                    c.Ellipse(25.5f, 39, 4.5f, 2.6f, C(1f, 1f, 1f, 0.55f));
                    c.Disc(39, 24, 1.3f, C(0.75f, 0.6f, 1f)); c.Disc(35, 36, 0.9f, C(0.75f, 0.6f, 1f)); c.Disc(28, 26, 0.8f, C(0.75f, 0.6f, 1f));
                    break;
                }
                default: { // Zombie Tooth
                    var t = C(0.64f, 0.78f, 0.52f);
                    c.Tri(17, 29, 29, 29, 22, 6, t);
                    c.Tri(35, 29, 47, 29, 42, 6, t);
                    c.Rect(17, 26, 47, 44, t);
                    c.Disc(24.5f, 43, 7.5f, t); c.Disc(39.5f, 43, 7.5f, t);
                    c.Disc(37, 34, 4.5f, C(0.36f, 0.46f, 0.26f));
                    c.Line(26, 44, 29, 36, 1.3f, C(0.3f, 0.36f, 0.22f)); c.Line(29, 36, 26, 30, 1.3f, C(0.3f, 0.36f, 0.22f));
                    c.Ellipse(22, 38, 2.2f, 4.5f, white);
                    break;
                }
            }
        }

        private static Sprite[] crowSprites;
        private static Sprite Crow(int frame) {
            if (crowSprites == null || crowSprites[0] == null) {
                crowSprites = new Sprite[2];
                for (int f = 0; f < 2; f++) {
                    var c = new Canvas(40, 26);
                    var b = C(0.07f, 0.06f, 0.09f);
                    if (f == 0) { c.Tri(13, 12, 24, 12, 9, 25, b); c.Tri(17, 12, 26, 12, 20, 23, C(0.13f, 0.12f, 0.16f)); }
                    else { c.Tri(13, 11, 24, 11, 8, 2, b); c.Tri(17, 11, 26, 11, 21, 3, C(0.13f, 0.12f, 0.16f)); }
                    c.Ellipse(19, 12, 8.5f, 4f, b);
                    c.Tri(9, 12, 3, 15, 3, 9, b);
                    c.Disc(28, 14, 4f, b);
                    c.Tri(31, 15.5f, 37, 14, 31, 12.5f, C(0.85f, 0.65f, 0.15f));
                    c.Disc(29, 15, 0.9f, C(1f, 0.9f, 0.4f));
                    var tex = c.ToTexture("treat_crow" + f);
                    crowSprites[f] = Sprite.Create(tex, new Rect(0, 0, 40, 26), new Vector2(0.5f, 0.5f), 40f / 0.42f);
                    crowSprites[f].hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                }
            }
            return crowSprites[frame & 1];
        }

        private static Sprite glowSprite, pixelSprite;
        internal static Sprite Glow() {
            if (glowSprite != null) return glowSprite;
            const int n = 96;
            var px = new Color[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++) {
                    float dx = (x + 0.5f) / n * 2f - 1f, dy = (y + 0.5f) / n * 2f - 1f, r = Mathf.Sqrt(dx * dx + dy * dy);
                    float a = Mathf.Clamp01(1f - r);
                    px[y * n + x] = new Color(1f, 1f, 1f, a * a);
                }
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear };
            tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            tex.SetPixels(px);
            tex.Apply(false, false);
            glowSprite = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), n);      // 1 unit across
            glowSprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return glowSprite;
        }

        internal static Sprite Pixel() {
            if (pixelSprite != null) return pixelSprite;
            var tex = new Texture2D(4, 4, TextureFormat.RGBA32, false);
            var px = new Color[16];
            for (int i = 0; i < 16; i++) px[i] = Color.white;
            tex.SetPixels(px);
            tex.Apply(false, false);
            tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            pixelSprite = Sprite.Create(tex, new Rect(0, 0, 4, 4), new Vector2(0.5f, 0.5f), 4f);    // 1 unit
            pixelSprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return pixelSprite;
        }

        // ================================================================ world candies
        private static GameObject candyRoot;
        private static readonly Dictionary<byte, (GameObject go, SpriteRenderer sr, SpriteRenderer shadow, float phase)> candyObjs = new();

        internal static void RebuildCandies() {
            foreach (var o in candyObjs.Values) if (o.go != null) UnityEngine.Object.Destroy(o.go);
            candyObjs.Clear();
            if (TrickOrTreat.candies.Count == 0 || ShipStatus.Instance == null) return;
            if (candyRoot == null) candyRoot = new GameObject("TrickOrTreatCandies") { layer = 11 };
            foreach (var c in TrickOrTreat.candies) {
                if (c.Eaten || c.Cab != TreatCabinets.None) continue;      // hidden in a cabinet
                var go = new GameObject("candy" + c.Index) { layer = 11 };
                go.transform.SetParent(candyRoot.transform, false);
                go.transform.position = new Vector3(c.Pos.x, c.Pos.y, c.Pos.y / 1000f + 0.0005f);
                SpriteRenderer shSr = null;
                if (!KindIsPicture(c.Kind)) {               // the pictures bring their own floor shadow
                    var sh = new GameObject("shadow") { layer = 11 };
                    sh.transform.SetParent(go.transform, false);
                    sh.transform.localPosition = new Vector3(0f, -0.17f, 0.0002f);
                    sh.transform.localScale = new Vector3(0.36f, 0.1f, 1f);
                    shSr = sh.AddComponent<SpriteRenderer>();
                    shSr.sprite = Glow();
                    shSr.color = new Color(0f, 0f, 0f, 0.55f);
                }
                var art = new GameObject("art") { layer = 11 };
                art.transform.SetParent(go.transform, false);
                var sr = art.AddComponent<SpriteRenderer>();
                sr.sprite = KindSprite(c.Kind);
                candyObjs[c.Index] = (go, sr, shSr, c.Index * 0.77f);
            }
        }

        internal static void RemoveCandy(TrickOrTreat.Candy c) {
            if (c == null || !candyObjs.TryGetValue(c.Index, out var o)) return;
            if (o.go != null) {
                Puff(o.go.transform.position, c.Kind);
                UnityEngine.Object.Destroy(o.go);
            }
            candyObjs.Remove(c.Index);
        }

        private static readonly List<(SpriteRenderer sr, Vector3 v, float until)> puffs = new();
        private static void Puff(Vector3 at, byte kind) {
            try {
                var col = new[] { C(1f, 0.6f, 0.15f), C(0.7f, 0.35f, 0.95f), C(0.5f, 0.25f, 0.7f), C(1f, 1f, 1f), C(0.65f, 0.67f, 0.7f), C(0.6f, 0.25f, 0.8f),
                                   C(1f, 1f, 1f), C(1f, 0.93f, 0.55f), C(0.94f, 0.88f, 0.72f), C(0.4f, 0.9f, 0.3f), C(0.9f, 0.15f, 0.15f), C(0.64f, 0.78f, 0.52f) }[kind % 12];
                for (int i = 0; i < 7; i++) {
                    var go = new GameObject("puff") { layer = 11 };
                    go.transform.position = at + new Vector3(0f, 0f, -0.01f);
                    go.transform.localScale = Vector3.one * 0.09f;
                    var sr = go.AddComponent<SpriteRenderer>();
                    sr.sprite = Glow();
                    sr.color = col;
                    float ang = i / 7f * Mathf.PI * 2f;
                    puffs.Add((sr, new Vector3(Mathf.Cos(ang), Mathf.Sin(ang), 0f) * 0.9f, Time.time + 0.45f));
                }
            } catch { }
        }

        // ================================================================ per frame
        internal static void Tick(bool meeting) {
            float t = Time.time;
            // candies bob a little; the pictures (baked shadow, pivot on the floor) only breathe, so the shadow stays put
            foreach (var o in candyObjs.Values) {
                if (o.sr == null) continue;
                if (o.shadow == null) {
                    float b = 0.035f * Mathf.Sin(t * 2.6f + o.phase);
                    o.sr.transform.localScale = new Vector3(1f - b * 0.6f, 1f + b, 1f);
                    continue;
                }
                o.sr.transform.localPosition = new Vector3(0f, 0.05f + 0.035f * Mathf.Sin(t * 2.6f + o.phase), 0f);
                o.sr.transform.localRotation = Quaternion.Euler(0f, 0f, 6f * Mathf.Sin(t * 1.7f + o.phase));
            }
            for (int i = puffs.Count - 1; i >= 0; i--) {
                var p = puffs[i];
                if (p.sr == null || t >= p.until) { if (p.sr != null) UnityEngine.Object.Destroy(p.sr.gameObject); puffs.RemoveAt(i); continue; }
                p.sr.transform.position += p.v * Time.deltaTime;
                var col = p.sr.color; col.a = Mathf.Clamp01((p.until - t) / 0.45f); p.sr.color = col;
            }
            TickPopup();
            TickHint();
            var lp = PlayerControl.LocalPlayer;
            if (meeting || lp == null) {
                HideScreenFx();
                TickCrows(true);
                TickGlow(true);
                return;
            }
            var mine = TrickOrTreat.active.TryGetValue(lp.PlayerId, out var l) ? l : null;
            bool Has(Treat fx) => mine != null && mine.Any(a => a.Fx == fx);
            TickStatus(mine);
            TickArrow(Has(Treat.GuidingMint) ? lp : null);
            TickEcho(Has(Treat.EchoDrop) ? lp : null);
            TickBlur(Has(Treat.Jinkies));
            TickSway(Has(Treat.Nausea));
            TickMute(Has(Treat.Earmuffs));
            TickFake(mine?.FirstOrDefault(a => a.Fx == Treat.NothingQ));
            TickFlash();
            TickCrows(false);
            TickGlow(false);
            TickHiccups(lp);
        }

        internal static void OnEnd(ActiveTreat a) {
            // the per-frame drawers notice on their own; only camera and audio need an immediate hand back
            var lp = PlayerControl.LocalPlayer;
            if (lp == null || a.Owner != lp.PlayerId) return;
            if (a.Fx == Treat.Nausea) TickSway(false);
            if (a.Fx == Treat.Earmuffs) TickMute(false);
            if (a.Fx == Treat.Jinkies) TickBlur(false);
        }

        private static void HideScreenFx() {
            TickArrow(null);
            TickEcho(null);
            TickBlur(false);
            TickSway(false);
            TickMute(false);
            TickFake(null);
            if (statusText != null) statusText.gameObject.SetActive(false);
            if (flashSr != null) flashSr.enabled = false;
        }

        internal static void Clear() {
            HideScreenFx();
            foreach (var o in candyObjs.Values) if (o.go != null) UnityEngine.Object.Destroy(o.go);
            candyObjs.Clear();
            TickCrows(true, true);
            TickGlow(true, true);
            if (popupRoot != null) UnityEngine.Object.Destroy(popupRoot);
            popupRoot = null;
            if (hintText != null) hintText.gameObject.SetActive(false);
        }

        // ---- UI helpers (Banshee's world -> UI camera mapping) ----
        internal static Camera UiCam() => HudManager.InstanceExists ? HudManager.Instance.UICamera : null;

        internal static bool ToUi(Vector3 world, out Vector3 ui) {
            ui = default;
            var main = Camera.main;
            var uiCam = UiCam();
            if (main == null || uiCam == null) return false;
            var vp = main.WorldToViewportPoint(world);
            ui = uiCam.ViewportToWorldPoint(new Vector3(vp.x, vp.y, 10f));
            ui.z = -50f;
            return vp.x > -0.1f && vp.x < 1.1f && vp.y > -0.1f && vp.y < 1.1f;
        }

        internal static float UiPerWorld() {
            var main = Camera.main; var uiCam = UiCam();
            if (main == null || uiCam == null || main.orthographicSize <= 0f) return 1f;
            return uiCam.orthographicSize / main.orthographicSize;
        }

        internal static SpriteRenderer UiSr(string name, Sprite s, int order) {
            var go = new GameObject(name) { layer = 5 };
            UnityEngine.Object.DontDestroyOnLoad(go);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = s;
            sr.sortingOrder = order;
            return sr;
        }

        internal static void Cover(SpriteRenderer sr, float z) {
            var uiCam = UiCam();
            if (uiCam == null || sr == null) return;
            var c = uiCam.transform.position;
            sr.transform.position = new Vector3(c.x, c.y, z);
            float h = uiCam.orthographicSize * 2.2f;
            sr.transform.localScale = new Vector3(h * uiCam.aspect * 1.05f, h, 1f);
        }

        internal static TextMeshPro NewText(string name) {
            var hud = HudManager.InstanceExists ? HudManager.Instance : null;
            if (hud == null || hud.KillButton == null || hud.KillButton.cooldownTimerText == null) return null;
            var t = UnityEngine.Object.Instantiate(hud.KillButton.cooldownTimerText, hud.transform);
            t.name = name;
            t.enableWordWrapping = false;
            t.richText = true;
            t.gameObject.SetActive(true);
            return t;
        }

        // ================================================================ the eater's card
        private static GameObject popupRoot;
        private static TextMeshPro popupText, popupBody;      // popupBody only with the card picture
        private static SpriteRenderer popupIcon, popupBack;
        private static bool popupPicture;
        private static float popupAt;
        private const float PopupLife = 6.5f;

        internal static void ShowPopup(byte kind, string kindName, Treat shown, Treat real, bool imp, byte param, string extra) {
            try {
                var hud = HudManager.InstanceExists ? HudManager.Instance : null;
                if (hud == null) return;
                if (popupRoot == null) {
                    popupRoot = new GameObject("TreatCard") { layer = 5 };
                    popupRoot.transform.SetParent(hud.transform, false);
                    var card = CardSprite();
                    popupPicture = card != null;
                    popupBack = UiSr("back", card ?? Pixel(), 300);
                    popupBack.transform.SetParent(popupRoot.transform, false);
                    popupIcon = UiSr("icon", KindSprite(0), 302);
                    popupIcon.transform.SetParent(popupRoot.transform, false);
                    popupText = NewText("TreatCardText");
                    if (popupText != null) {
                        popupText.transform.SetParent(popupRoot.transform, false);
                        popupText.alignment = TextAlignmentOptions.Left;
                        popupText.rectTransform.pivot = new Vector2(0f, 0.5f);
                    }
                    if (popupPicture) {
                        popupBody = NewText("TreatCardBody");
                        if (popupBody != null) {
                            popupBody.transform.SetParent(popupRoot.transform, false);
                            popupBody.alignment = TextAlignmentOptions.TopLeft;
                            popupBody.rectTransform.pivot = new Vector2(0f, 1f);
                        }
                        if (popupText != null) popupText.alignment = TextAlignmentOptions.BottomLeft;
                        // the card picture is opaque (order 300): both texts have to sort above it
                        if (popupText != null) popupText.sortingOrder = 305;
                        if (popupBody != null) popupBody.sortingOrder = 305;
                    }
                }
                popupIcon.sprite = KindSprite(kind);
                popupIcon.enabled = true;
                string name = TreatFx.Name(shown);
                var tint = Tint(real);
                string body;
                if (TrickOrTreat.IsStandIn(shown)) {
                    body = (TrickOrTreat.De() ? "wirkt wie " : "acts as ") + $"<color=#{Hex(Tint(real))}>{TreatFx.Name(real)}</color>: " + Line(real, imp, param);
                    tint = Tint(shown);
                } else body = Line(real, imp, param);
                if (!string.IsNullOrEmpty(extra)) body = real == Treat.Regurgitate || real == Treat.GuidingMint || real == Treat.SwapSweet ? extra : body + " " + extra;
                // User 2026-10-21: the card names the candy and the effect, without the line that explains it
                if (EffectsHidden) {
                    string real2 = TrickOrTreat.IsStandIn(shown) ? $" <color=#{Hex(Tint(real))}>({TreatFx.Name(real)})</color>" : "";
                    SetCardText(kindName, $"<color=#{Hex(tint)}>{name}</color>{real2}", "");
                }
                else SetCardText(kindName, $"<color=#{Hex(tint)}>{name}</color>", body);
                popupAt = Time.time;
                popupRoot.SetActive(true);
                LayoutPopup();
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} card failed: {e.Message}"); }
        }

        // User 2026-10-20: the card does not explain the effect. Since 2026-10-21 it names candy and effect (no line
        // text). Kept as a switch so the explaining texts stay available.
        internal static bool EffectsHidden => true;

        internal static string PoisonLine(bool de) => de
            ? "Diese Süßigkeit war tödlich. Deine Leiche liegt dort, wo du gegessen hast."
            : "This one was deadly. Your body lies where you ate it.";

        internal static void ShowPoisonCard() {
            ShowPopup(TrickOrTreat.PoisonKind, TrickOrTreat.KindNames[TrickOrTreat.PoisonKind], Treat.NothingQ, Treat.NothingQ, false, byte.MaxValue, null);
            if (popupText == null) return;
            bool de = TrickOrTreat.De();
            SetCardText(TrickOrTreat.KindNames[TrickOrTreat.PoisonKind], $"<color=#B98CFF>{(de ? "Tödlich" : "Deadly")}</color>", EffectsHidden ? "" : PoisonLine(de));
        }

        // ---- a short line in the middle of the screen (an empty cabinet), only on the searcher's client ----
        private static TextMeshPro hintText;
        private static float hintAt = -100f;
        private const float HintLife = 2.2f;
        internal static string HintShown => hintText != null && hintText.gameObject.activeSelf ? hintText.text : "";

        internal static void ShowHint(string text) {
            try {
                if (hintText == null) {
                    hintText = NewText("TreatHint");
                    if (hintText == null) return;
                    hintText.alignment = TextAlignmentOptions.Center;
                    hintText.rectTransform.pivot = new Vector2(0.5f, 0.5f);
                    hintText.rectTransform.sizeDelta = new Vector2(10f, 2f);
                    hintText.sortingOrder = 305;
                }
                hintText.text = $"<color=#FFB060>{text}</color>";
                hintText.gameObject.SetActive(true);
                hintAt = Time.time;
                TickHint();
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} hint failed: {e.Message}"); }
        }

        private static void TickHint() {
            if (hintText == null || !hintText.gameObject.activeSelf) return;
            float t = Time.time - hintAt;
            var uiCam = UiCam();
            if (t > HintLife || uiCam == null || TrickOrTreat.InMeeting()) { hintText.gameObject.SetActive(false); return; }
            var at = uiCam.ViewportToWorldPoint(new Vector3(0.5f, 0.64f, 10f));
            hintText.transform.position = new Vector3(at.x, at.y + 0.08f * Mathf.Clamp01(t / 0.3f), -62f);
            hintText.transform.localScale = Vector3.one * 0.62f;
            hintText.alpha = Mathf.Clamp01(t / 0.15f) * (1f - Mathf.Clamp01((t - (HintLife - 0.6f)) / 0.6f));
        }

        // Kind (small, orange) and effect name above the card's divider, the line below it. Without the card picture
        // all three go into one text as before.
        private static void SetCardText(string kindName, string nameRich, string body) {
            if (popupText == null) return;
            if (nameRich == null) {
                // name only (effects hidden): the candy name as the title, the line below only when given
                popupText.text = $"<color=#FFB060>{kindName}</color>";
                if (popupBody != null) popupBody.text = body ?? "";
                else if (!string.IsNullOrEmpty(body)) popupText.text += $"\n<size=48%>{body}</size>";
                return;
            }
            if (popupPicture && popupBody != null) {
                popupText.text = $"<size=62%><color=#FFB060>{kindName}</color></size>\n{nameRich}";
                popupBody.text = body;
            } else popupText.text = $"<size=55%><color=#FFB060>{kindName}</color></size>\n{nameRich}\n<size=48%>{body}</size>";
        }

        // card picture layout in its own pixels (640x200, from the top left), see the Grafik-Lieferung
        private const float CardPxW = 640f, CardPxH = 200f;
        private const float CardIconX = 110f, CardIconY = 100f, CardIconPx = 150f;    // field x 26-194
        private const float CardTextX = 228f, CardTextR = 600f;                       // field x 210-614
        private const float CardTitleTop = 22f, CardTitleBottom = 70f, CardBodyTop = 84f, CardBodyBottom = 172f;

        private static float textBase = -1f;

        private static void LayoutPopup() {
            var uiCam = UiCam();
            if (uiCam == null || popupRoot == null) return;
            var top = uiCam.ViewportToWorldPoint(new Vector3(0.5f, 0.8f, 10f));
            float w = uiCam.orthographicSize * uiCam.aspect;
            if (popupPicture) {
                float cw = Mathf.Min(5.8f, w * 1.5f), u = cw / CardPxW;
                float l = top.x - cw / 2f, tp = top.y + CardPxH * u / 2f;
                Vector3 At(float px, float py, float z) => new Vector3(l + px * u, tp - py * u, z);
                popupBack.transform.position = new Vector3(top.x, top.y, -60f);
                popupBack.transform.localScale = new Vector3(cw, cw, 1f);                  // sprite is 1 unit wide
                var isp = popupIcon.sprite;
                float pivotUp = isp != null && isp.rect.height > 0f ? 0.5f - isp.pivot.y / isp.rect.height : 0f;   // picture pivot sits on the floor
                popupIcon.transform.position = At(CardIconX, CardIconY + pivotUp * CardIconPx, -61f);
                float iconUnits = popupIcon.sprite != null ? popupIcon.sprite.bounds.size.x : 1f;
                popupIcon.transform.localScale = Vector3.one * (CardIconPx * u / Mathf.Max(iconUnits, 0.01f));
                const float ts = 0.42f;
                if (popupText != null) {
                    if (textBase < 0f) textBase = popupText.fontSize;
                    popupText.transform.position = At(CardTextX, CardTitleBottom, -61f);
                    popupText.transform.localScale = Vector3.one * ts;
                    popupText.rectTransform.pivot = new Vector2(0f, 0f);
                    popupText.rectTransform.sizeDelta = new Vector2((CardTextR - CardTextX) * u / ts, (CardTitleBottom - CardTitleTop) * u / ts);
                    popupText.enableWordWrapping = false;
                    popupText.enableAutoSizing = true;
                    popupText.fontSizeMax = textBase * 1.15f;
                    popupText.fontSizeMin = textBase * 0.3f;
                }
                if (popupBody != null) {
                    popupBody.transform.position = At(CardTextX, CardBodyTop, -61f);
                    popupBody.transform.localScale = Vector3.one * ts;
                    popupBody.rectTransform.sizeDelta = new Vector2((CardTextR - CardTextX) * u / ts, (CardBodyBottom - CardBodyTop) * u / ts);
                    popupBody.enableWordWrapping = true;
                    popupBody.enableAutoSizing = true;
                    popupBody.fontSizeMax = (textBase > 0f ? textBase : popupBody.fontSize) * 0.72f;
                    popupBody.fontSizeMin = (textBase > 0f ? textBase : popupBody.fontSize) * 0.22f;
                }
                return;
            }
            float cardW = Mathf.Min(7.2f, w * 1.7f), cardH = 1.25f;
            float left = top.x - cardW / 2f;
            popupBack.transform.position = new Vector3(top.x, top.y, -60f);
            popupBack.transform.localScale = new Vector3(cardW, cardH, 1f);
            popupIcon.transform.position = new Vector3(left + 0.62f, top.y, -61f);
            popupIcon.transform.localScale = Vector3.one * (0.95f / CandyWorldSize);
            if (popupText != null) {
                popupText.transform.position = new Vector3(left + 1.25f, top.y, -61f);
                popupText.transform.localScale = Vector3.one * 0.42f;
                popupText.rectTransform.sizeDelta = new Vector2((cardW - 1.4f) / 0.42f, 3f);
                popupText.enableWordWrapping = true;
            }
        }

        private static void TickPopup() {
            if (popupRoot == null || !popupRoot.activeSelf) return;
            float t = Time.time - popupAt;
            if (t > PopupLife || TrickOrTreat.InMeeting()) { popupRoot.SetActive(false); return; }
            float a = Mathf.Clamp01(t / 0.25f) * (1f - Mathf.Clamp01((t - (PopupLife - 0.8f)) / 0.8f));
            LayoutPopup();
            float pop = 1f + 0.12f * Mathf.Max(0f, 1f - t / 0.25f);
            popupIcon.transform.localScale *= pop;
            popupBack.color = popupPicture ? new Color(1f, 1f, 1f, a) : new Color(0.07f, 0.04f, 0.1f, 0.82f * a);
            popupIcon.color = new Color(1f, 1f, 1f, a);
            if (popupText != null) popupText.alpha = a;
            if (popupBody != null) popupBody.alpha = a;
        }

        // ---- running effects of the local player, left edge ----
        private static TextMeshPro statusText;
        private static void TickStatus(List<ActiveTreat> mine) {
            if (mine == null || mine.Count == 0) { if (statusText != null) statusText.gameObject.SetActive(false); return; }
            if (statusText == null) {
                statusText = NewText("TreatStatus");
                if (statusText == null) return;
                statusText.alignment = TextAlignmentOptions.TopLeft;
                statusText.rectTransform.pivot = new Vector2(0f, 1f);
                statusText.rectTransform.sizeDelta = new Vector2(12f, 6f);
            }
            var uiCam = UiCam();
            if (uiCam == null) return;
            var p = uiCam.ViewportToWorldPoint(new Vector3(0.012f, 0.6f, 10f));
            statusText.transform.position = new Vector3(p.x, p.y, -55f);
            statusText.transform.localScale = Vector3.one * 0.3f;
            var sb = new System.Text.StringBuilder();
            bool de = TrickOrTreat.De();
            foreach (var a in mine) {
                string left = a.Round ? (de ? $"{a.Meetings} M." : $"{a.Meetings} mtg")
                    : TrickOrTreat.IsMeetingBound(a.Fx) ? (de ? "Meeting" : "meeting") : $"{Mathf.CeilToInt(Mathf.Max(0f, a.Left))}s";
                sb.Append($"<color=#{Hex(Tint(a.Fx))}>{Name(a.Fx)}</color> <color=#FFFFFFAA>{left}</color>\n");
            }
            string s = sb.ToString();
            if (statusText.text != s) statusText.text = s;
            statusText.gameObject.SetActive(true);
        }

        // ---- Guiding Mint: TOR's edge arrow to the nearest body ----
        private static TheOtherRoles.Objects.Arrow mintArrow;
        internal static bool AnyBody() {
            try { return UnityEngine.Object.FindObjectsOfType<DeadBody>().Any(b => b != null && !b.Reported); } catch { return false; }
        }
        private static float mintSearch;
        private static Vector3 mintTarget;
        private static void TickArrow(PlayerControl lp) {
            if (lp == null) {
                if (mintArrow != null) { try { if (mintArrow.arrow != null) UnityEngine.Object.Destroy(mintArrow.arrow); } catch { } mintArrow = null; }
                return;
            }
            if (Time.time >= mintSearch) {
                mintSearch = Time.time + 0.5f;
                DeadBody best = null; float bd = float.MaxValue;
                foreach (var b in UnityEngine.Object.FindObjectsOfType<DeadBody>()) {
                    if (b == null || b.Reported) continue;
                    float d = Vector2.Distance(lp.GetTruePosition(), b.transform.position);
                    if (d < bd) { bd = d; best = b; }
                }
                if (best == null) { TickArrow(null); return; }
                mintTarget = best.transform.position;
            }
            if (mintArrow == null) mintArrow = new TheOtherRoles.Objects.Arrow(new Color(0.55f, 1f, 0.75f));
            mintArrow.Update(mintTarget);
            mintArrow.arrow.SetActive(true);
        }

        // ---- Echo Drop: white silhouettes of everyone within 6 m, above the shadow ----
        private static readonly Dictionary<byte, SpriteRenderer> echoes = new();
        private static Material silhouetteMat;
        private static void TickEcho(PlayerControl lp) {
            var want = new HashSet<byte>();
            if (lp != null) {
                try {
                    if (silhouetteMat == null) {
                        var sh = Shader.Find("GUI/Text Shader");
                        if (sh != null) { silhouetteMat = new Material(sh); silhouetteMat.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset; }
                    }
                    float k = UiPerWorld();
                    float pulse = 0.5f + 0.15f * Mathf.Sin(Time.time * 6f);
                    foreach (var p in PlayerControl.AllPlayerControls.ToArray()) {
                        if (p == null || p == lp || !TrickOrTreat.IsAlive(p)) continue;
                        if (Vector2.Distance(p.GetTruePosition(), lp.GetTruePosition()) > 6f) continue;
                        var body = p.cosmetics?.currentBodySprite?.BodySprite;
                        if (body == null || body.sprite == null) continue;
                        if (!ToUi(body.transform.position, out var ui)) continue;
                        want.Add(p.PlayerId);
                        if (!echoes.TryGetValue(p.PlayerId, out var sr) || sr == null) {
                            sr = UiSr("echo" + p.PlayerId, body.sprite, 190);
                            if (silhouetteMat != null) sr.material = silhouetteMat;
                            echoes[p.PlayerId] = sr;
                        }
                        sr.sprite = body.sprite;
                        sr.flipX = body.flipX;
                        sr.transform.position = ui;
                        sr.transform.localScale = body.transform.lossyScale * k;
                        sr.color = silhouetteMat != null ? new Color(0.75f, 0.95f, 1f, pulse) : new Color(0.3f, 0.4f, 0.5f, pulse);
                        sr.enabled = true;
                    }
                } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} echo: {e.Message}"); }
            }
            foreach (var id in echoes.Keys.ToList()) {
                if (want.Contains(id)) continue;
                if (echoes[id] != null) UnityEngine.Object.Destroy(echoes[id].gameObject);
                echoes.Remove(id);
            }
        }

        // ---- Jinkies: a second camera renders the view at a tenth of the resolution, drawn blurred over it ----
        private static Camera blurCam;
        private static RenderTexture blurRt;
        private static Texture2D blurTex;
        private static SpriteRenderer blurSr, blurSr2;
        private static bool blurFailed;
        private static void TickBlur(bool want) {
            if (!want || blurFailed) {
                if (blurSr != null) { UnityEngine.Object.Destroy(blurSr.gameObject); blurSr = null; }
                if (blurSr2 != null) { UnityEngine.Object.Destroy(blurSr2.gameObject); blurSr2 = null; }
                if (blurCam != null) { UnityEngine.Object.Destroy(blurCam.gameObject); blurCam = null; }
                if (blurRt != null) { blurRt.Release(); UnityEngine.Object.Destroy(blurRt); blurRt = null; }
                if (!want) blurFailed = false;
                return;
            }
            try {
                var main = Camera.main; var uiCam = UiCam();
                if (main == null || uiCam == null) return;
                int w = Mathf.Max(32, Screen.width / 12), h = Mathf.Max(18, Screen.height / 12);
                if (blurRt == null || blurRt.width != w || blurRt.height != h) {
                    if (blurRt != null) { blurRt.Release(); UnityEngine.Object.Destroy(blurRt); }
                    blurRt = new RenderTexture(w, h, 16) { filterMode = FilterMode.Bilinear };
                    blurTex = new Texture2D(w, h, TextureFormat.RGB24, false) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp };
                    blurTex.hideFlags |= HideFlags.HideAndDontSave;
                    var spr = Sprite.Create(blurTex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), h / (uiCam.orthographicSize * 2f));
                    if (blurSr == null) blurSr = UiSr("TreatBlur", spr, -1000); else blurSr.sprite = spr;
                    if (blurSr2 == null) blurSr2 = UiSr("TreatBlur2", spr, -999); else blurSr2.sprite = spr;
                }
                if (blurCam == null) {
                    var go = new GameObject("TreatBlurCam");
                    UnityEngine.Object.DontDestroyOnLoad(go);
                    blurCam = go.AddComponent<Camera>();
                    blurCam.enabled = false;
                }
                blurCam.CopyFrom(main);
                blurCam.targetTexture = blurRt;
                blurCam.Render();
                var prev = RenderTexture.active;
                RenderTexture.active = blurRt;
                blurTex.ReadPixels(new Rect(0, 0, w, h), 0, 0, false);
                blurTex.Apply(false);
                RenderTexture.active = prev;
                var c = uiCam.transform.position;
                float t = Time.time;
                blurSr.transform.position = new Vector3(c.x, c.y, -40f);
                blurSr.color = new Color(1f, 1f, 1f, 0.93f);
                blurSr2.transform.position = new Vector3(c.x + 0.12f * Mathf.Sin(t * 1.9f), c.y + 0.07f * Mathf.Cos(t * 1.3f), -40.5f);
                blurSr2.color = new Color(1f, 1f, 1f, 0.4f);
            } catch (Exception e) {
                blurFailed = true;
                HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} blur failed: {e.Message}");
            }
        }

        // ---- Nausea: the main camera rolls slowly ----
        private static bool swaying;
        private static void TickSway(bool want) {
            var main = Camera.main;
            if (main == null) return;
            if (!want) {
                if (swaying) { main.transform.localRotation = Quaternion.identity; swaying = false; }
                return;
            }
            swaying = true;
            float t = Time.time;
            main.transform.localRotation = Quaternion.Euler(0f, 0f, 6f * Mathf.Sin(t * 1.3f) + 2f * Mathf.Sin(t * 3.1f));
        }

        // ---- Earmuffs ----
        private static bool muted;
        private static float mutedFrom = 1f;
        private static void TickMute(bool want) {
            if (want && !muted) { mutedFrom = AudioListener.volume; AudioListener.volume = 0f; muted = true; }
            else if (!want && muted) { AudioListener.volume = mutedFrom <= 0.001f ? 1f : mutedFrom; muted = false; }
        }

        // The end screen and the main menu have no HUD, so no Tick turns the sound back on: a round that
        // ended under Earmuffs had a silent jingle and a silent menu until the next lobby (audit 21.10.).
        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameEnd))]
        static class UnmuteAtGameEndPatch {
            [HarmonyPrefix]
            public static void Prefix() { try { TickMute(false); } catch { } }
        }

        [HarmonyPatch(typeof(MainMenuManager), nameof(MainMenuManager.Start))]
        static class UnmuteInMenuPatch {
            public static void Postfix() { try { TickMute(false); } catch { } }
        }

        // ---- Nothing?: a fake sabotage only the eater sees ----
        private static SpriteRenderer fakeSr;
        private static ActiveTreat fake;
        private static float fakeBeep;
        internal static string FakeTaskLine() {
            if (fake == null || TrickOrTreat.InMeeting()) return null;
            float since = Time.time - fake.Started;
            if (since < 2f) return null;
            int left = Mathf.Max(1, Mathf.CeilToInt(30f - since));
            bool de = TrickOrTreat.De();
            switch (fake.P1) {
                case 0: return $"<color=#FF0000FF>{(de ? "Reaktorschmelze in" : "Reactor Meltdown in")} {left} (0/2)</color>";
                case 1: return $"<color=#FF0000FF>{(de ? "Licht reparieren" : "Fix Lights")} (0%)</color>";
                case 2: return $"<color=#FF0000FF>{(de ? "Sauerstoff erschöpft in" : "Oxygen depleted in")} {left} (0/2)</color>";
                default: return $"<color=#FF0000FF>{(de ? "Kommunikation sabotiert" : "Comms Sabotaged")}</color>";
            }
        }

        private static void TickFake(ActiveTreat a) {
            fake = a;
            bool red = a != null && (a.P1 == 0 || a.P1 == 2) && Time.time - a.Started >= 2f;
            if (!red) { if (fakeSr != null) fakeSr.enabled = false; return; }
            if (fakeSr == null) fakeSr = UiSr("TreatFakeAlarm", Pixel(), 150);
            Cover(fakeSr, -48f);
            float s = Mathf.Sin((Time.time - a.Started) * Mathf.PI);
            fakeSr.color = new Color(1f, 0f, 0f, 0.28f * s * s);
            fakeSr.enabled = true;
            if (Time.time >= fakeBeep) { fakeBeep = Time.time + 1f; Play(Alarm(), 0.55f, 0f); }
        }

        // ---- shield flash for the saved player ----
        private static SpriteRenderer flashSr;
        private static float flashAt = -10f;
        private static Color flashColor;
        internal static void ShieldFlash(Treat fx) {
            flashAt = Time.time;
            flashColor = fx == Treat.HardCandy ? new Color(1f, 0.85f, 0.4f) : new Color(0.7f, 0.85f, 1f);
            try {
                ShowPopup(0, TrickOrTreat.De() ? "Gerettet" : "Saved", fx, fx, false, byte.MaxValue,
                    TrickOrTreat.De() ? "Ein Kill gegen dich ist gescheitert." : "A kill on you just failed.");
                // effects hidden: say that a kill failed, not which candy stopped it (and no candy picture)
                if (EffectsHidden && popupIcon != null) popupIcon.enabled = false;
                if (EffectsHidden) SetCardText(TrickOrTreat.De() ? "Gerettet" : "Saved", null,
                    TrickOrTreat.De() ? "Ein Kill gegen dich ist gescheitert." : "A kill on you just failed.");
            } catch { }
        }
        private static void TickFlash() {
            float t = Time.time - flashAt;
            if (t > 0.9f) { if (flashSr != null) flashSr.enabled = false; return; }
            if (flashSr == null) flashSr = UiSr("TreatFlash", Pixel(), 160);
            Cover(flashSr, -49f);
            flashSr.color = new Color(flashColor.r, flashColor.g, flashColor.b, 0.45f * (1f - t / 0.9f));
            flashSr.enabled = true;
        }

        // ---- Glowing (every client): a soft halo above the shadow, within normal sight of the viewer ----
        private static readonly Dictionary<byte, SpriteRenderer> glows = new();
        private static void TickGlow(bool hide, bool destroy = false) {
            var want = new HashSet<byte>();
            var lp = PlayerControl.LocalPlayer;
            if (!hide && lp != null) {
                float reach = 6f;
                try { reach = Mathf.Max(4f, ShipStatus.Instance.MaxLightRadius * GameOptionsManager.Instance.currentNormalGameOptions.CrewLightMod * 1.2f); } catch { }
                float k = UiPerWorld();
                foreach (var kv in TrickOrTreat.active) {
                    if (!kv.Value.Any(a => a.Fx == Treat.Glowing)) continue;
                    var p = Helpers.playerById(kv.Key);
                    if (!TrickOrTreat.IsAlive(p) || p.inVent) continue;
                    if (p != lp && Vector2.Distance(p.GetTruePosition(), lp.GetTruePosition()) > reach) continue;
                    if (!ToUi((Vector3)p.GetTruePosition() + new Vector3(0f, 0.3f, 0f), out var ui)) continue;
                    want.Add(kv.Key);
                    if (!glows.TryGetValue(kv.Key, out var sr) || sr == null) { sr = UiSr("glow" + kv.Key, Glow(), 185); glows[kv.Key] = sr; }
                    float pulse = 1f + 0.08f * Mathf.Sin(Time.time * 3f + kv.Key);
                    sr.transform.position = ui + new Vector3(0f, 0f, 0.5f);
                    sr.transform.localScale = Vector3.one * 1.9f * k * pulse;
                    sr.color = new Color(0.75f, 1f, 0.45f, 0.32f);
                    sr.enabled = true;
                }
            }
            foreach (var id in glows.Keys.ToList()) {
                if (want.Contains(id)) continue;
                if (glows[id] != null) { if (destroy || !TrickOrTreat.Has(id, Treat.Glowing)) UnityEngine.Object.Destroy(glows[id].gameObject); else { glows[id].enabled = false; continue; } }
                glows.Remove(id);
            }
        }

        // ---- Crow Company (every client): three crows circling over the eater, world layer ----
        private static readonly Dictionary<byte, SpriteRenderer[]> crows = new();
        private static void TickCrows(bool hide, bool destroy = false) {
            var want = new HashSet<byte>();
            if (!hide) {
                foreach (var kv in TrickOrTreat.active) {
                    if (!kv.Value.Any(a => a.Fx == Treat.CrowCompany)) continue;
                    var p = Helpers.playerById(kv.Key);
                    if (!TrickOrTreat.IsAlive(p)) continue;
                    want.Add(kv.Key);
                    if (!crows.TryGetValue(kv.Key, out var srs) || srs == null || srs[0] == null) {
                        srs = new SpriteRenderer[3];
                        for (int i = 0; i < 3; i++) {
                            var go = new GameObject("crow") { layer = 11 };
                            srs[i] = go.AddComponent<SpriteRenderer>();
                        }
                        crows[kv.Key] = srs;
                    }
                    var c = (Vector3)p.GetTruePosition();
                    float t = Time.time;
                    for (int i = 0; i < 3; i++) {
                        float ang = t * 1.8f + i * (Mathf.PI * 2f / 3f);
                        float r = 0.62f + 0.08f * Mathf.Sin(t * 2.3f + i);
                        var pos = c + new Vector3(Mathf.Cos(ang) * r, 1.05f + Mathf.Sin(ang) * r * 0.35f + 0.06f * Mathf.Sin(t * 5f + i), 0f);
                        pos.z = p.transform.position.z - 0.5f;
                        var sr = srs[i];
                        sr.transform.position = pos;
                        sr.sprite = Crow(((int)(t * 7f) + i) & 1);
                        sr.flipX = Mathf.Sin(ang) > 0f;       // nose along the flight direction
                        sr.color = Color.white;
                        sr.enabled = !p.inVent;
                    }
                }
            }
            foreach (var id in crows.Keys.ToList()) {
                if (want.Contains(id)) continue;
                bool keep = !destroy && TrickOrTreat.Has(id, Treat.CrowCompany);
                foreach (var sr in crows[id]) if (sr != null) { if (keep) sr.enabled = false; else UnityEngine.Object.Destroy(sr.gameObject); }
                if (!keep) crows.Remove(id);
            }
        }

        // ---- Hiccups (every client): a hic every 8 s, loud for the eater, by distance and side for the others ----
        private static void TickHiccups(PlayerControl lp) {
            foreach (var kv in TrickOrTreat.active) {
                var a = kv.Value.FirstOrDefault(x => x.Fx == Treat.Hiccups);
                if (a == null || Time.time < a.Next) continue;
                a.Next = Time.time + 8f;
                var p = Helpers.playerById(kv.Key);
                if (!TrickOrTreat.IsAlive(p)) continue;
                float vol, pan = 0f;
                if (p == lp) vol = 0.9f;
                else {
                    var d = p.GetTruePosition() - lp.GetTruePosition();
                    vol = 0.9f * Mathf.Clamp01(1f - d.magnitude / 7f);
                    pan = Mathf.Clamp(d.x / 5f, -1f, 1f);
                }
                if (vol < 0.04f) continue;
                Play(Hic(), vol, pan);
                HalloweenPlugin.Logger?.LogInfo(FormattableString.Invariant($"{LogPrefix} hic of player {kv.Key} (volume {vol:F2})."));
            }
        }

        // ================================================================ sounds (synthesised once)
        private static AudioClip hicClip, munchClip, alarmClip;

        internal static void Play(AudioClip clip, float vol, float pan) {
            try {
                if (clip == null || !Constants.ShouldPlaySfx() || SoundManager.Instance == null) return;
                var src = SoundManager.Instance.PlaySound(clip, false, vol);
                if (src != null) src.panStereo = pan;
            } catch { }
        }

        internal static AudioClip MakeClip(string name, float len, Func<float, float, float> f) {
            const int rate = 44100;
            int n = (int)(rate * len);
            var data = new float[n];
            for (int i = 0; i < n; i++) data[i] = Mathf.Clamp(f((float)i / rate, len), -1f, 1f);
            var clip = AudioClip.Create(name, n, 1, rate, false);
            clip.SetData(data, 0);
            clip.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return clip;
        }

        private static AudioClip Hic() {
            if (hicClip != null) return hicClip;
            var noise = new System.Random(11);
            double ph = 0;
            hicClip = MakeClip("treat_hic", 0.22f, (t, len) => {
                // a glottal click, then a quick rising "ic"
                float click = t < 0.012f ? ((float)noise.NextDouble() * 2f - 1f) * (1f - t / 0.012f) : 0f;
                float f = Mathf.Lerp(330f, 720f, Mathf.Clamp01((t - 0.01f) / 0.09f));
                ph += 2 * Math.PI * f / 44100;
                float env = Mathf.Clamp01((t - 0.008f) / 0.01f) * Mathf.Clamp01((len - t) / 0.12f) * Mathf.Exp(-t * 9f);
                float voice = (float)(Math.Sin(ph) + 0.35 * Math.Sin(ph * 2) + 0.15 * Math.Sin(ph * 3));
                return 0.8f * click + 0.55f * env * voice;
            });
            return hicClip;
        }

        internal static void Munch() {
            if (munchClip == null) {
                var noise = new System.Random(3);
                float lp = 0f;
                munchClip = MakeClip("treat_munch", 0.45f, (t, len) => {
                    // three crunches
                    float e = 0f;
                    foreach (float s in new[] { 0f, 0.13f, 0.27f }) { float u = t - s; if (u >= 0f) e += Mathf.Exp(-u * 38f); }
                    lp += (((float)noise.NextDouble() * 2f - 1f) - lp) * 0.45f;
                    return 0.7f * e * lp;
                });
            }
            Play(munchClip, 0.8f, 0f);
        }

        private static AudioClip Alarm() {
            if (alarmClip != null) return alarmClip;
            double ph = 0;
            alarmClip = MakeClip("treat_alarm", 0.5f, (t, len) => {
                float f = t < 0.25f ? 880f : 660f;
                ph += 2 * Math.PI * f / 44100;
                float env = Mathf.Clamp01(t / 0.01f) * Mathf.Clamp01((len - t) / 0.05f);
                return 0.35f * env * (Math.Sin(ph) > 0 ? 1f : -1f);
            });
            return alarmClip;
        }
    }

    /// <summary>The Use button next to a candy or a cabinet (AtlasUse's pattern: re-applied every frame, click through
    /// a listener on the PassiveButton plus the E key; vanilla targets such as consoles win).</summary>
    internal static class TreatUse {
        private static bool owned;
        private static IntPtr hooked;
        private static TrickOrTreat.Candy current;
        private static TreatCabinets.Cabinet currentCab;
        private static readonly Dictionary<int, Sprite> icons = new();
        private static float iconWidth = -1f;
        internal static bool Owned => owned;
        internal static string Label => owned && HudManager.InstanceExists && HudManager.Instance.UseButton?.buttonLabelText != null ? HudManager.Instance.UseButton.buttonLabelText.text : "";
        internal static float IconWidth => iconWidth > 0f ? iconWidth : 1f;

        internal static void Tick() {
            var hud = HudManager.InstanceExists ? HudManager.Instance : null;
            var ub = hud != null ? hud.UseButton : null;
            var lp = PlayerControl.LocalPlayer;
            TrickOrTreat.Candy c = null;
            TreatCabinets.Cabinet cab = null;
            if (ub != null && TrickOrTreat.IsAlive(lp) && lp.CanMove && !lp.inVent && Minigame.Instance == null && ub.currentTarget == null
                && !TreatCabinets.AtlasOwnsUse()) {
                c = TrickOrTreat.NearestCandy(lp, out float d);
                if (c != null && d > TrickOrTreat.Range()) c = null;
                if (c == null) cab = TreatCabinets.Target(lp);
            }
            TreatCabinets.TickSearch(lp, ub, cab);
            if (c == null && cab == null) { Release(); return; }
            try {
                if (hooked != ub.Pointer) {
                    var pb = ub.GetComponent<PassiveButton>();
                    if (pb != null) pb.OnClick.AddListener((Action)OnClick);
                    hooked = ub.Pointer;
                }
                if (!ub.gameObject.activeSelf) ub.gameObject.SetActive(true);
                if (hud.PetButton != null && hud.PetButton.gameObject.activeSelf) hud.PetButton.gameObject.SetActive(false);
                if (iconWidth < 0f && ub.graphic != null && ub.graphic.sprite != null) iconWidth = ub.graphic.sprite.bounds.size.x;
                ub.SetEnabled();
                owned = true;
                current = c;
                currentCab = cab;
                Paint(ub);
                if (c != null && Input.GetKeyDown(KeyCode.E) && KeyboardFree()) OnClick();
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{TrickOrTreat.LogPrefix} use button: {e.Message}"); }
        }

        // Sprite and label again at the very end of HudManager.Update: other postfixes in the same frame (and the
        // vanilla target refresh) set the button back to USE, which left the candy offering "USE" now and then.
        private static void Paint(ActionButton ub) {
            if (currentCab != null) {
                if (ub.graphic != null) ub.graphic.sprite = TreatCabinets.SearchIcon();
                if (ub.buttonLabelText != null) ub.buttonLabelText.text = TrickOrTreat.De() ? "DURCHSUCHEN" : "SEARCH";
                try { ub.SetCooldownFill(TreatCabinets.Searching ? 1f - TreatCabinets.Progress : 0f); } catch { }
                return;
            }
            if (current == null) return;
            if (ub.graphic != null) ub.graphic.sprite = Icon(current.Kind);
            bool take = TreatPlus.BagOn() && PlayerControl.LocalPlayer != null && TreatPlus.BagCount(PlayerControl.LocalPlayer.PlayerId) < TreatPlus.BagSize;
            if (ub.buttonLabelText != null) ub.buttonLabelText.text = take ? (TrickOrTreat.De() ? "NEHMEN" : "TAKE") : (TrickOrTreat.De() ? "ESSEN" : "EAT");
        }

        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        private static class LatePaint {
            [HarmonyPriority(Priority.Last)]
            private static void Postfix(HudManager __instance) {
                try {
                    if (!owned || (current == null && currentCab == null) || __instance.UseButton == null) return;
                    if (__instance.UseButton.currentTarget != null) { owned = false; current = null; currentCab = null; return; }
                    Paint(__instance.UseButton);
                } catch { }
            }
        }

        internal static void Release() {
            current = null;
            bool hadCab = currentCab != null;
            currentCab = null;
            if (!owned) return;
            owned = false;
            try {
                if (!HudManager.InstanceExists) return;
                if (hadCab) HudManager.Instance.UseButton.SetCooldownFill(0f);
                HudManager.Instance.UseButton.SetTarget(null);
            } catch { }
        }

        internal static bool KeyboardFree() {
            try {
                var chat = HudManager.InstanceExists ? HudManager.Instance.Chat : null;
                if (chat != null && chat.IsOpenOrOpening) return false;
                if (MapBehaviour.Instance != null && MapBehaviour.Instance.IsOpen) return false;
                if (Minigame.Instance != null) return false;
            } catch { }
            return true;
        }

        private static Sprite Icon(int kind) {
            if (icons.TryGetValue(kind, out var s) && s != null) return s;
            float w = iconWidth > 0f ? iconWidth : 1f;
            var tex = TreatFx.KindTexture(kind);
            // the pictures carry margin and shadow: let them fill a little more of the button
            float fill = TreatFx.KindIsPicture(kind) ? 1.05f : 0.85f;
            s = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), tex.width / (w * fill));
            s.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            icons[kind] = s;
            return s;
        }

        internal static void OnClick() {
            if (!owned) return;
            if (currentCab != null) { TreatCabinets.OnClick(currentCab); return; }
            if (current == null) return;
            var c = current;
            current = null;
            if (TreatPlus.BagOn() && PlayerControl.LocalPlayer != null && TreatPlus.BagCount(PlayerControl.LocalPlayer.PlayerId) < TreatPlus.BagSize) TreatPlus.RequestTake(c);
            else TrickOrTreat.RequestEat(c);
        }
    }
}
