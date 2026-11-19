// Mouvement « vivant » des primitives : noyau. Inséré dans chaque composition par build.py (scripts/motion.py).
// Déterministe : aucun appel au hasard natif. Tout tirage vient d'un PRNG semé (graine du film + scène + identifiant d'étape),
// donc deux rendus du même storyboard sont identiques, et `--motion-seed` change toutes les variations.
var _M = (function (tl, CFG) {
  var VW = CFG.vw, VH = CFG.vh;
  function hash(s) { var h = 2166136261; s = String(s); for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function rng(seed) {
    var a = seed >>> 0;
    return function () { a = (a + 0x6D2B79F5) >>> 0; var t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  var sceneR = rng(CFG.seed), bags = {};
  function shuffled(a, r) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(r() * (i + 1)), x = a[i]; a[i] = a[j]; a[j] = x; } return a; }
  // Tirage « sac » : toutes les options sortent une fois avant de se répéter (pas deux entrées identiques de suite).
  function draw(name, pool) { var b = bags[name]; if (!b || !b.length) b = bags[name] = shuffled(pool, sceneR); return b.pop(); }
  var ALIAS = { gauche: "L", droite: "R", haut: "T", bas: "B", zoom: "zoom", inclinaison: "skew", rotation: "spin", flou: "blur", chute: "drop", montee: "rise" };
  var HANDLERS = [], _bg = null;
  function ctxFor(step, sel, t, dur) {
    var id = step.getAttribute("data-step"), force = (CFG.steps && CFG.steps[id]) || "", level = CFG.level, dir = null;
    if (force === "sobre") return null;
    if (force === "calme" || force === "vivant") level = force; else if (force) dir = ALIAS[force] || null;
    var ov = !!step.querySelector(".ov"), k = level === "calme" ? 0.55 : 1;
    return {
      step: step, sel: sel, t: t, dur: dur, id: id, ov: ov, k: k, calm: level === "calme", force: dir,
      r: rng(CFG.seed ^ hash(id)),
      dx: (ov ? 0.3 : 0.55) * VW * k, dy: (ov ? 0.25 : 0.5) * VH * k,
      q: function (s) { return Array.prototype.slice.call(step.querySelectorAll(s)); },
      has: function (s) { return step.querySelector(s) !== null; }
    };
  }
  function pick(r, a) { return a[Math.floor(r() * a.length) % a.length]; }
  function between(r, a, b) { return a + (b - a) * r(); }
  function sign(r) { return r() < 0.5 ? -1 : 1; }
  // Décalage de départ pour une direction L, R, T, B.
  function vec(d, c, f) { f = f || 1; return d === "L" ? { x: -c.dx * f } : d === "R" ? { x: c.dx * f } : d === "T" ? { y: -c.dy * f } : { y: c.dy * f }; }
  function side(i, a) { return (i % 2 ? 1 : -1) * a; }
  function zero(from) { var o = {}; for (var k in from) o[k] = (k === "scale") ? 1 : (k === "filter") ? "blur(0px)" : 0; return o; }
  function assign(a, b) { for (var k in b) a[k] = b[k]; return a; }
