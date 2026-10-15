// Hollowmere Manor (Arbeitstitel): Grundriss-Daten fuer beide Varianten plus Laufweg-Rechnung.
// Koordinaten in Metern, x nach Osten, y nach SUEDEN (Bildschirmrichtung). Das Haus (34 x 24 m)
// ist der Kern und in beiden Varianten gleich; die grosse Variante oeffnet Garten und Gruft.
// Laufwege wie in UnknownsAtlas/docs/KARTEN_VERKLEINERUNG.md: Raster 0,25 m, 0,3 m Wandabstand,
// 2,5 m/s. Geheimgaenge und Vents zaehlen bei der Rechnung NICHT mit.

const VILLA = {
  speed: 2.5,
  variants: {
    small: { label: "Klein", w: 34, h: 24, spawn: [17, 14] },
    large: { label: "Groß", w: 50, h: 36, spawn: [17, 14] },
  },
  // sys: Skeld-System je Variante (null = Raum ohne System). v: "both" | "large".
  areas: [
    { id: "kueche", name: "Küche", r: [0, 0, 7, 8], v: "both", sys: { small: "LowerEngine", large: "LowerEngine" }, kind: "room",
      text: "Großer Holzherd, an dem die Crew Kaffee kocht. Über die Kellertreppe geht es in den Heizungskeller; der Speiseaufzug fährt hinauf in den Funkraum (Geheimgang, nur nach oben)." },
    { id: "wasch", name: "Waschküche", r: [7, 0, 11, 8], v: "both", sys: { small: "UpperEngine", large: "LowerEngine" }, kind: "room",
      text: "Klein: hier läuft das zweite Aggregat der Crew. Groß: zählt zur Küche, denn das Aggregat steht dann draußen im Crew-Lager." },
    { id: "seance", name: "Séance-Salon", r: [11, 0, 23, 8], v: "both", sys: { small: "Reactor", large: "Reactor" }, kind: "room", dark: true,
      text: "Runder Tisch und Ouija-Brett, also das Filmset für die Hauptszene. Bei der Reaktor-Sabotage eskaliert das Ritual, und zwei Spieler müssen gleichzeitig die Hände auf die beiden Tischenden legen. Hinter dem Wandteppich liegt eine Einbahn-Tür in die Halle." },
    { id: "funk", name: "Funkraum", r: [23, 0, 27, 8], v: "both", sys: { small: "Comms", large: "Comms" }, kind: "room",
      text: "Das alte Dienstbotenzimmer mit Klingeltafel. Die Crew hat hier ihre Funkgeräte und den Satelliten-Empfänger aufgebaut." },
    { id: "rumpel", name: "Rumpelkammer", r: [27, 0, 34, 4], v: "both", sys: { small: "Storage", large: null }, kind: "room", dark: true,
      text: "Ein Dachbodenabteil voller Kisten und Requisiten. Klein: das Lager der Karte. Groß: Abstellraum ohne System, das Lager zieht ins Gewächshaus." },
    { id: "stern", name: "Sternwarte", r: [27, 4, 34, 8], v: "both", sys: { small: "Navigation", large: "Navigation" }, kind: "room",
      text: "Messingteleskop unter der Dachluke. Die Kartentische zeigen den Sternenhimmel über der Villa." },
    { id: "heiz", name: "Heizungskeller", r: [0, 8, 8, 14], v: "both", sys: { small: "Electrical", large: "Electrical" }, kind: "room", dark: true,
      text: "Über die Kellertreppe erreichbar: Kohlekessel, Sicherungskasten und die Hauptleitung zu den Scheinwerfern der Crew. Hier wird das Licht repariert." },
    { id: "flurw", name: "Flur West", r: [8, 8, 11, 14], v: "both", sys: { small: null, large: null }, kind: "hall",
      text: "Verbindet Halle, Waschküche, Keller und Bibliothek." },
    { id: "biblio", name: "Bibliothek", r: [0, 14, 11, 19], v: "both", sys: { small: null, large: null }, kind: "room", dark: true,
      text: "Regale bis zur Decke und Kerzenleuchter. Ein Drehbücherregal führt direkt in die Eingangshalle (Geheimgang in beide Richtungen)." },
    { id: "kapelle", name: "Hauskapelle", r: [0, 19, 11, 24], v: "both", sys: { small: "Shields", large: null }, kind: "room", dark: true,
      text: "Klein: Schutzsiegel am Altar (Shields). Groß: Kerzenraum ohne System, denn die Siegel liegen dann in der Familiengruft. Dort endet der Gruft-Tunnel, und eine Hintertür führt ins Crew-Lager." },
    { id: "halle", name: "Eingangshalle", r: [11, 8, 23, 20], v: "both", sys: { small: "Cafeteria", large: "Cafeteria" }, kind: "room", spawn: true,
      text: "Freitreppe, Kronleuchter und die Standuhr. Spawn und Meeting: Der Notfallknopf ist die Filmklappe der Regie (»Cut!«). Kameraschienen laufen quer durch den Raum." },
    { id: "regie", name: "Regie", r: [11, 20, 15, 24], v: "both", sys: { small: "Security", large: "Security" }, kind: "room",
      text: "Die Monitorwand der Crew, die Kameras sind die Drehkameras am Set. Erklärt die Überwachung ohne Sci-Fi." },
    { id: "windfang", name: "Windfang", r: [15, 20, 19, 24], v: "both", sys: { small: null, large: null }, kind: "hall",
      text: "Klein: Die Haustür ist verrammelt, draußen tobt der Sturm. Groß: Hier geht es hinaus auf den Vorplatz." },
    { id: "maske", name: "Maske", r: [19, 20, 23, 24], v: "both", sys: { small: "MedBay", large: "MedBay" }, kind: "room",
      text: "Schminkstuhl mit Glühbirnenspiegel und Kunstblut-Eimern. Der Scan läuft im Schminkstuhl." },
    { id: "flur_o", name: "Flur Ost", r: [23, 8, 26, 24], v: "both", sys: { small: null, large: null }, kind: "hall",
      text: "Porträtgalerie. Wenn die Uhr schlägt, drehen sich die Bilder." },
    { id: "jagd", name: "Jagdzimmer", r: [26, 8, 34, 13], v: "both", sys: { small: "Weapons", large: "Weapons" }, kind: "room",
      text: "Trophäenwand, Gewehrschrank und ausgestopfter Bär. Die Waffen-Tasks finden am Gewehrschrank statt." },
    { id: "kamin", name: "Kaminzimmer", r: [26, 13, 34, 18], v: "both", sys: { small: "LifeSupp", large: "LifeSupp" }, kind: "room",
      text: "Riesiger offener Kamin. Bei der O2-Sabotage zieht der Kamin nicht mehr und Rauch füllt das Haus. Zweites Ventil im Arbeitszimmer. Groß: Terrassentür nach Osten." },
    { id: "arbeit", name: "Arbeitszimmer", r: [26, 18, 34, 24], v: "both", sys: { small: "Admin", large: "Admin" }, kind: "room",
      text: "Schreibtisch des Hausherrn mit Grundriss der Villa unter Glas. Das ist der Admin-Tisch." },

    { id: "terrasse", name: "Terrasse", r: [34, 2, 40, 26], v: "large", sys: { large: null }, kind: "garden",
      text: "Steinterrasse an der Ostseite. Verbindet Kaminzimmer, Gewächshaus, Friedhof und Brunnenhof." },
    { id: "vorplatz", name: "Vorplatz", r: [12, 24, 24, 30], v: "large", sys: { large: null }, kind: "garden",
      text: "Kiesauffahrt mit den Trucks der Filmcrew und dem Catering-Tisch." },
    { id: "crew", name: "Crew-Lager", r: [0, 24, 12, 36], v: "large", sys: { large: "UpperEngine" }, kind: "garden",
      text: "Zelte, Kabeltrommeln und der große Aggregatwagen. Der zweite Motor der Karte steht hier draußen." },
    { id: "gewaechs", name: "Gewächshaus", r: [40, 2, 50, 12], v: "large", sys: { large: "Storage" }, kind: "room",
      text: "Zerbrochene Glasscheiben, tote Orchideen. Die Crew benutzt es als Requisitenlager (Storage)." },
    { id: "brunnen", name: "Brunnenhof", r: [24, 26, 40, 36], v: "large", sys: { large: null }, kind: "garden", dark: true,
      text: "Versiegelter Brunnen mit einer Ecke Heckenlabyrinth. Kein System, aber viele Sichtschatten." },
    { id: "friedhof", name: "Friedhof", r: [40, 14, 50, 36], v: "large", sys: { large: null }, kind: "garden", dark: true,
      text: "Schiefe Grabsteine und Laternen, die man anzünden kann. Der dunkelste Bereich der Karte." },
    { id: "gruft", name: "Familiengruft", r: [44, 28, 50, 36], v: "large", sys: { large: "Shields" }, kind: "room", dark: true,
      text: "Steinsärge der Familie. Die Schutzsiegel (Shields) liegen hier. Der Tunnel unter dem Garten führt in die Hauskapelle (Einbahn)." },
  ],
  // Oeffnungen: ax "x" = senkrechte Wand bei x = at, Spanne a..b in y; ax "y" = waagerechte Wand.
  // t: "open" | "door" | "secret"; je Variante eigener Typ (fehlt = gibt es dort nicht).
  // oneway: Richtung "from>to" fuer Geheimgaenge.
  openings: [
    // Stand gen_villa.py / villa_layout.py (09.10.): je Variante 7 senkrechte + 6 waagerechte Tueren
    { ax: "x", at: 7, a: 3, b: 5.5, t: { small: "door", large: "door" } },               // Kueche - Waschkueche (LowerEngine)
    { ax: "x", at: 11, a: 3, b: 5.5, t: { small: "door", large: "open" } },              // Waschkueche - Seance (UpperEngine)
    { ax: "x", at: 23, a: 3, b: 5.5, t: { small: "open", large: "open" } },              // Seance - Funkraum
    { ax: "y", at: 8, a: 8.3, b: 10.7, t: { small: "door", large: "open" } },            // Waschkueche - Flur West (UpperEngine)
    { ax: "y", at: 8, a: 23.5, b: 25.5, t: { small: "open", large: "open" } },           // Funkraum - Flur Ost
    { ax: "x", at: 27, a: 0.75, b: 3.25, t: { small: "door", large: "open" } },          // Funkraum - Rumpelkammer (Storage)
    { ax: "y", at: 4, a: 29.5, b: 32, t: { small: "door", large: "open" } },             // Rumpelkammer - Sternwarte (Storage)
    { ax: "y", at: 8, a: 30, b: 32.5, t: { small: "door", large: "open" } },             // Sternwarte - Jagdzimmer (Storage)
    { ax: "y", at: 8, a: 2, b: 4.5, t: { small: "door", large: "door" } },               // Kueche - Heizungskeller (LowerEngine)
    { ax: "x", at: 8, a: 9.5, b: 12, t: { small: "door", large: "door" } },              // Flur West - Heizungskeller (Electrical)
    { ax: "x", at: 11, a: 10.25, b: 12.75, t: { small: "door", large: "door" } },        // Flur West - Halle (Cafeteria)
    { ax: "y", at: 14, a: 8.5, b: 10.5, t: { small: "open", large: "open" } },           // Flur West - Bibliothek
    { ax: "y", at: 14, a: 2, b: 4.5, t: { small: "open", large: "open" } },              // Heizungskeller - Bibliothek
    { ax: "y", at: 19, a: 3, b: 5.5, t: { small: "open", large: "open" } },              // Bibliothek - Kapelle
    { ax: "x", at: 23, a: 10.25, b: 12.75, t: { small: "door", large: "door" } },        // Halle - Flur Ost (Cafeteria)
    { ax: "y", at: 20, a: 15.75, b: 18.25, t: { small: "door", large: "open" } },        // Halle - Windfang (Cafeteria)
    { ax: "y", at: 20, a: 11.75, b: 14.25, t: { small: "door", large: "door" } },        // Halle - Regie (Security)
    { ax: "x", at: 15, a: 21.5, b: 23.5, t: { small: "open", large: "open" } },          // Regie - Windfang
    { ax: "x", at: 19, a: 21.5, b: 23.5, t: { small: "open", large: "open" } },          // Windfang - Maske
    { ax: "x", at: 23, a: 21, b: 23.5, t: { small: "door", large: "door" } },            // Maske - Flur Ost (MedBay)
    { ax: "x", at: 26, a: 9.5, b: 12, t: { small: "open", large: "open" } },             // Flur Ost - Jagdzimmer
    { ax: "x", at: 26, a: 14.5, b: 16.5, t: { small: "open", large: "open" } },          // Flur Ost - Kaminzimmer
    { ax: "x", at: 26, a: 20, b: 22.5, t: { small: "open", large: "open" } },            // Flur Ost - Arbeitszimmer
    { ax: "y", at: 13, a: 27, b: 29.5, t: { small: "open", large: "open" } },            // Jagdzimmer - Kaminzimmer
    { ax: "y", at: 18, a: 27, b: 29.5, t: { small: "open", large: "open" } },            // Kaminzimmer - Arbeitszimmer

    { ax: "y", at: 24, a: 15.75, b: 18.25, t: { large: "door" }, label: "Haustür" },     // Windfang - Vorplatz (Cafeteria)
    { ax: "x", at: 34, a: 14.5, b: 16.5, t: { large: "open" }, label: "Terrassentür" },  // Kaminzimmer - Terrasse
    { ax: "y", at: 24, a: 3, b: 5.5, t: { large: "door" }, label: "Hintertür" },         // Kapelle - Crew-Lager (UpperEngine)
    { ax: "x", at: 12, a: 26.5, b: 29, t: { large: "door" } },                           // Vorplatz - Crew-Lager (UpperEngine)
    { ax: "x", at: 24, a: 26.5, b: 29.5, t: { large: "open" } },                         // Vorplatz - Brunnenhof
    { ax: "y", at: 26, a: 35.75, b: 38.25, t: { large: "door" } },                       // Terrasse - Brunnenhof (Storage)
    { ax: "x", at: 40, a: 5, b: 7.5, t: { large: "door" } },                             // Terrasse - Gewaechshaus (Storage)
    { ax: "x", at: 40, a: 17, b: 19.5, t: { large: "open" }, label: "Friedhofstor" },    // Terrasse - Friedhof
    { ax: "x", at: 40, a: 30, b: 33, t: { large: "open" } },                             // Brunnenhof - Friedhof
    { ax: "y", at: 28, a: 45.75, b: 48.25, t: { large: "door" }, label: "Gruft-Tor" },   // Friedhof - Gruft (Storage)
  ],
  secrets: [
    { id: "teppich", name: "Wandteppich", p: [21, 8], from: [21, 6.5], to: [21, 9.5], oneway: true, v: "both",
      text: "Séance-Salon → Halle. Nur in diese Richtung. Fluchtweg aus der Sackgasse des Rituals." },
    { id: "aufzug", name: "Speiseaufzug", p: null, jump: true, from: [6.2, 0.7], to: [26.3, 6.8], oneway: true, v: "both",
      text: "Küche → Funkraum (das alte Dienstbotenzimmer). Nur nach oben, zurück geht es nicht." },
    { id: "regal", name: "Drehbücherregal", p: [11, 16.5], from: [9.5, 16.5], to: [12.5, 16.5], oneway: false, v: "both",
      text: "Bibliothek ↔ Eingangshalle. Dreht sich hörbar, alle in der Nähe sehen es." },
    { id: "tunnel", name: "Gruft-Tunnel", p: null, jump: true, from: [47, 35.3], to: [1.2, 23.3], oneway: true, v: "large",
      text: "Familiengruft → Hauskapelle, unter dem Garten hindurch. Einbahn: der einzige schnelle Weg vom Friedhof zurück ins Haus." },
  ],
  vents: {
    small: [
      { net: "A", p: [5.6, 6.6] }, { net: "A", p: [5.6, 12.6] }, { net: "A", p: [9.6, 22.8] },
      { net: "B", p: [21.8, 1.2] }, { net: "B", p: [1.4, 17.8] }, { net: "B", p: [22.2, 20.8] },
      { net: "C", p: [33.1, 7.2] }, { net: "C", p: [33.1, 17.2] }, { net: "C", p: [33.1, 23.2] },
    ],
    large: [
      { net: "A", p: [5.6, 6.6] }, { net: "A", p: [5.6, 12.6] }, { net: "A", p: [9.6, 22.8] },
      { net: "B", p: [21.8, 1.2] }, { net: "B", p: [1.4, 17.8] }, { net: "B", p: [22.2, 20.8] },
      { net: "C", p: [33.1, 7.2] }, { net: "C", p: [33.1, 17.2] }, { net: "C", p: [33.1, 23.2] },
      { net: "D", p: [10.8, 34.8] }, { net: "D", p: [26, 34.8] }, { net: "D", p: [48.8, 3.2] }, { net: "D", p: [48.8, 34.8] },
    ],
  },
  candles: {
    small: [[12.1, 1.0], [22.0, 6.9], [2.4, 15.5], [9.6, 20.4]],
    large: [[12.1, 1.0], [22.0, 6.9], [2.4, 15.5], [9.6, 20.4], [43.0, 34.5]],
  },
  cameras: {
    small: [[11.7, 9.4], [25.4, 9.2], [16.0, 0.6], [2.0, 14.6]],
    large: [[11.7, 9.4], [16.0, 0.6], [12.6, 24.6], [40.6, 14.6]],
  },
  clock: [12.35, 8.7],
  meeting: [17, 15.6],
  admin: [30.2, 22.2],
};

// ---------------------------------------------------------------- Laufweg-Rechnung

function villaWalk(variant) {
  const V = VILLA.variants[variant];
  const cell = 0.25, clear = 0.45;           // 0,15 m halbe Wandstaerke + 0,3 m Spielerabstand
  const nx = Math.round(V.w / cell), ny = Math.round(V.h / cell);
  const areas = VILLA.areas.filter(a => a.v === "both" || variant === "large");
  const opens = VILLA.openings.filter(o => o.t[variant] && o.t[variant] !== "secret");
  const segs = [];
  for (const a of areas) {
    const [x0, y0, x1, y1] = a.r;
    segs.push({ ax: "y", at: y0, a: x0, b: x1 }, { ax: "y", at: y1, a: x0, b: x1 },
              { ax: "x", at: x0, a: y0, b: y1 }, { ax: "x", at: x1, a: y0, b: y1 });
  }
  const inside = (x, y) => areas.some(a => x > a.r[0] && x < a.r[2] && y > a.r[1] && y < a.r[3]);
  const blocked = (x, y) => {
    for (const s of segs) {
      const d = s.ax === "x" ? Math.abs(x - s.at) : Math.abs(y - s.at);
      const t = s.ax === "x" ? y : x;
      if (d >= clear || t < s.a - clear || t > s.b + clear) continue;
      const gap = opens.some(o => o.ax === s.ax && Math.abs(o.at - s.at) < 0.01 && t > o.a + 0.3 && t < o.b - 0.3);
      if (!gap) return true;
    }
    return false;
  };
  const walk = new Uint8Array(nx * ny);
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
    const x = (i + 0.5) * cell, y = (j + 0.5) * cell;
    walk[j * nx + i] = inside(x, y) && !blocked(x, y) ? 1 : 0;
  }
  // Dijkstra mit 8 Nachbarn (Diagonale nur, wenn beide Kanten frei sind).
  const dist = new Float64Array(nx * ny).fill(Infinity);   // Float32 rundet und bricht den "d > dist"-Test
  const si = Math.floor(V.spawn[0] / cell), sj = Math.floor(V.spawn[1] / cell);
  dist[sj * nx + si] = 0;
  const heap = [[0, sj * nx + si]];
  const push = (d, k) => { heap.push([d, k]); let c = heap.length - 1; while (c > 0) { const p = (c - 1) >> 1; if (heap[p][0] <= heap[c][0]) break; [heap[p], heap[c]] = [heap[c], heap[p]]; c = p; } };
  const pop = () => { const top = heap[0], last = heap.pop(); if (heap.length) { heap[0] = last; let c = 0; for (;;) { const l = 2 * c + 1, r = l + 1; let m = c; if (l < heap.length && heap[l][0] < heap[m][0]) m = l; if (r < heap.length && heap[r][0] < heap[m][0]) m = r; if (m === c) break; [heap[m], heap[c]] = [heap[c], heap[m]]; c = m; } } return top; };
  const N = [[1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1], [1, 1, Math.SQRT2], [1, -1, Math.SQRT2], [-1, 1, Math.SQRT2], [-1, -1, Math.SQRT2]];
  while (heap.length) {
    const [d, k] = pop();
    if (d > dist[k]) continue;
    const i = k % nx, j = (k - i) / nx;
    for (const [di, dj, w] of N) {
      const a = i + di, b = j + dj;
      if (a < 0 || b < 0 || a >= nx || b >= ny || !walk[b * nx + a]) continue;
      if (di && dj && (!walk[j * nx + a] || !walk[b * nx + i])) continue;
      const nd = d + w * cell, nk = b * nx + a;
      if (nd < dist[nk]) { dist[nk] = nd; push(nd, nk); }
    }
  }
  let far = 0, farK = -1, unreached = 0;
  for (let k = 0; k < nx * ny; k++) {
    if (!walk[k]) continue;
    if (dist[k] === Infinity) { unreached++; continue; }
    if (dist[k] > far) { far = dist[k]; farK = k; }
  }
  const fi = farK % nx, fj = (farK - fi) / nx;
  return { nx, ny, cell, walk, dist, far, farSec: far / VILLA.speed, farPt: [(fi + 0.5) * cell, (fj + 0.5) * cell], unreached };
}

if (typeof module !== "undefined") module.exports = { VILLA, villaWalk };
