  // ---- Entrées : le bloc d'étape vient d'un bord, tombe, tourne, zoome… (au lieu de toujours monter de 34 px)
  HANDLERS.push(function (c, f) {
    var inEl = c.step.querySelector(".in");
    if (!inEl || c.step.classList.contains("step-punch")) return;
    var quiet = c.has(".versus,.diverge,.compare3,.bars,.seuil,.ref-card,.waffle");   // primitives qui bougent déjà elles-mêmes
    var pool = quiet ? ["rise", "zoom"] : c.calm ? ["rise", "L", "R", "zoom"]
      : ["L", "R", "T", "B", "zoom", "skew", "spin", "blur", "drop", "rise", "L", "R"];
    var v = c.force || draw(quiet ? "inq" : "in", pool), s = sign(c.r), from, d = 0.7, ease = "expo.out", ext = null;
    if (v === "L" || v === "R") from = vec(v, c);
    else if (v === "T") { from = vec("T", c, 0.8); ease = "power4.out"; d = 0.65; }
    else if (v === "B") from = vec("B", c, 0.8);
    else if (v === "zoom") from = { scale: quiet || c.calm ? 1.15 : 1.7 };
    else if (v === "skew") { from = { x: c.dx * 0.7 * s, skewX: -14 * s }; ease = "power3.out"; d = 0.6; }
    else if (v === "spin") { from = { rotation: 8 * s, y: 70 * c.k, scale: 0.9 }; ease = "back.out(1.4)"; }
    else if (v === "blur") { from = { filter: "blur(18px)", scale: 1.08 }; ease = "power2.out"; }
    else if (v === "drop") { from = { y: -c.dy * 0.6 }; ease = "bounce.out"; d = 0.9; }
    else { from = { y: 34 }; d = 0.6; }
    d *= between(c.r, 0.9, 1.15);
    var id = "#" + inEl.id;
    tl.fromTo(id, { opacity: 0 }, { opacity: 1, duration: Math.min(0.35, d), ease: "power1.out" }, c.t);
    tl.fromTo(id, from, assign(zero(from), { duration: d, ease: ease }), c.t + between(c.r, 0, 0.06));
    // lignes d'un bloc : elles arrivent en alternant les côtés
    var lines = c.q(".in > .dline");
    if (lines.length > 1) tl.fromTo(lines, { opacity: 0, x: function (i) { return quiet ? 0 : side(i, c.dx * 0.18); }, y: 22 },
      { opacity: 1, x: 0, y: 0, duration: 0.5, ease: "power3.out", stagger: 0.12 }, c.t + 0.1);
    f.entry = true;
  });
  // ---- Kicker et titre de scène : depuis un côté tiré au sort
  HANDLERS.push(function (c, f) {
    var k = c.step.querySelector(".kicker"), s = c.step.querySelector(".stitle");
    if (!k && !s) return;
    if (k) tl.fromTo(c.sel + " .kicker", { opacity: 0, x: side(Math.floor(c.r() * 2), c.dx * 0.35) }, { opacity: 1, x: 0, duration: 0.55, ease: "power3.out" }, c.t);
    if (s) tl.fromTo(c.sel + " .stitle", { opacity: 0, y: -c.dy * 0.2 }, { opacity: 1, y: 0, duration: 0.65, ease: "expo.out" }, c.t + 0.1);
    f.head = true;
  });
  // ---- Respiration : le contenu flotte très légèrement pendant l'étape (jamais en `calme`)
  HANDLERS.push(function (c, f) {
    var z = c.step.querySelector(".zone");
    if (!z || c.calm || c.dur < 1.6) return;
    var per = between(c.r, 1.2, 1.8), amp = (c.ov ? 3 : 5) * sign(c.r), start = c.t + 0.9;
    var reps = Math.max(1, Math.floor((c.t + c.dur - start) / per) - 1);
    tl.to(c.sel + " .zone", { y: amp, duration: per, ease: "sine.inOut", yoyo: true, repeat: reps }, start);
  });
  // ---- Images plein écran : zoom avant, zoom arrière, dérive latérale (toujours cadré : jamais de bord nu)
  HANDLERS.push(function (c, f) {
    var img = c.step.querySelector("img.fond, img.ref-shot");
    if (!img) return;
    var isFond = img.classList.contains("fond"), v = c.force && ["zoom", "L", "R", "T", "B"].indexOf(c.force) >= 0 ? c.force : pick(c.r, ["in", "out", "panL", "panR", "panU"]);
    var from = { scale: 1 }, to = { scale: isFond ? 1.07 : 1.04 };
    if (isFond) {
      var s0 = 1.08, s1 = between(c.r, 1.12, 1.16), a = (s0 - 1) * VW / 2 * 0.85, b = (s0 - 1) * VH / 2 * 0.85;
      if (v === "out") { from = { scale: s1 }; to = { scale: 1.0 }; }
      else if (v === "panL" || v === "L") { from = { scale: s0, x: a }; to = { scale: s1, x: -a }; }
      else if (v === "panR" || v === "R") { from = { scale: s0, x: -a }; to = { scale: s1, x: a }; }
      else if (v === "panU" || v === "T" || v === "B") { from = { scale: s0, y: b }; to = { scale: s1, y: -b }; }
      else { from = { scale: 1 }; to = { scale: s1 }; }
    } else {
      if (v === "out") { from = { scale: 1.05 }; to = { scale: 1 }; }
      else if (v.indexOf("pan") === 0) { var d = VW * 0.008; from = { scale: 1.02, x: -d }; to = { scale: 1.05, x: d }; }
    }
    to.duration = c.dur; to.ease = "none";
    tl.fromTo("#" + img.id, from, to, c.t);
    f.img = true;
  });
  // ---- Fond de scène : dérive lente au lieu du zoom fixe de 5 % (appelé par la composition, une fois)
  _bg = function (dur) {
    if (CFG.level !== "vivant" || (CFG.steps && CFG.steps.__bg === "sobre")) return false;
    var r = rng(CFG.seed ^ hash("bg")), s0 = 1.08, s1 = between(r, 1.11, 1.15), v = pick(r, ["in", "out", "panL", "panR"]);
    var a = (s0 - 1) * VW / 2 * 0.8, from = { scale: s0 }, to = { scale: s1 };
    if (v === "out") { from = { scale: s1 }; to = { scale: s0 }; }
    else if (v === "panL") { from.x = a; to.x = -a; } else if (v === "panR") { from.x = -a; to.x = a; }
    to.duration = dur; to.ease = "none";
    tl.fromTo("#fond-img", from, to, 0);
    return true;
  };
