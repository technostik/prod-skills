  // ---- Compteur : durée et courbe tirées au sort, pulsation à l'arrivée, libellé qui arrive d'un côté.
  // La valeur finale est toujours exactement la cible (jamais de dépassement affiché).
  HANDLERS.push(function (c, f) {
    var ctrs = c.q(".ctr");
    if (!ctrs.length) return;
    var end = c.t + 0.15;
    ctrs.forEach(function (el) {
      var obj = { val: 0 }, target = parseFloat(el.getAttribute("data-target")), dec = parseInt(el.getAttribute("data-dec") || "0", 10);
      if (!isFinite(target)) return;
      var d = between(c.r, 0.9, 1.5), ease = pick(c.r, ["power3.out", "expo.out", "power4.out", "circ.out"]);
      tl.to(obj, { val: target, duration: d, ease: ease, onUpdate: function () { el.textContent = _fmt(obj.val, dec); } }, c.t + 0.15);
      end = Math.max(end, c.t + 0.15 + d);
      var big = el.closest(".dline");
      if (big && !c.calm) tl.to(big, { scale: 1.08, duration: 0.14, yoyo: true, repeat: 1, ease: "power2.out" }, c.t + 0.15 + d * 0.9);
    });
    f.count = true;
    if (c.has(".dbig") && c.has(".dsub")) {
      var v = vec(draw("sub", ["L", "R", "B"]), c, 0.25);
      tl.fromTo(c.sel + " .dsub", assign({ opacity: 0 }, v), assign(assign({ opacity: 1 }, zero(v)), { duration: 0.55, ease: "power3.out" }), Math.max(c.t + 0.6, end - 0.25));
    }
  });
  // ---- Barré : sens et vitesse des traits variables, secousse du mot au moment du trait.
  HANDLERS.push(function (c, f) {
    if (!c.has(".sline1")) return;
    var flip = c.r() < 0.5, d1 = between(c.r, 0.28, 0.45), d2 = between(c.r, 0.28, 0.45), t1 = c.t + between(c.r, 0.25, 0.4), t2 = t1 + between(c.r, 0.3, 0.45);
    tl.fromTo(c.sel + " .sline1", { scaleX: 0 }, { scaleX: 1, duration: d1, ease: "power2.inOut", transformOrigin: flip ? "right center" : "left center" }, t1);
    tl.fromTo(c.sel + " .sline2", { scaleX: 0 }, { scaleX: 1, duration: d2, ease: "power2.inOut", transformOrigin: flip ? "left center" : "right center" }, t2);
    if (!c.calm) c.q(".dstrike").forEach(function (w) {
      var a = 5 * sign(c.r);
      tl.to(w, { x: a, duration: 0.05, yoyo: true, repeat: 3, ease: "none" }, t1 + d1 * 0.6);
      tl.set(w, { x: 0 }, t1 + d1 * 0.6 + 0.22);
    });
    f.strike = true;
  });
  // ---- Énumération : chaque nouvel item arrive d'un côté qui alterne ; les précédents s'estompent.
  HANDLERS.push(function (c, f) {
    if (!c.has(".it.new")) return;
    var n = c.q(".it").length, d = c.force && vec(c.force, c, 0.4).x !== undefined ? c.force : (n % 2 ? "R" : "L");
    if (c.r() < 0.25) d = "B";
    var v = vec(d, c, 0.35);
    tl.fromTo(c.sel + " .it.new", assign({ opacity: 0 }, v), assign(assign({ opacity: 1 }, zero(v)), { duration: 0.55, ease: "power3.out" }), c.t + 0.1);
    if (c.has(".it:not(.new)")) tl.fromTo(c.sel + " .it:not(.new)", { opacity: 1 }, { opacity: 0.55, duration: 0.5, ease: "power2.out" }, c.t + 0.1);
    f.enumerate = true;
  });
  // ---- Spotlight : items qui entrent en alternant les côtés, relief avec petite inclinaison.
  HANDLERS.push(function (c, f) {
    if (!c.has(".spot")) return;
    var items = c.q(".spot .it");
    items.forEach(function (el, i) {
      tl.fromTo(el, { opacity: 0, x: side(i, c.dx * 0.3) }, { opacity: 1, x: 0, duration: 0.55, ease: "power3.out" }, c.t + 0.1 + i * 0.12);
    });
    var n = items.length;
    if (n) {
      var lead = 0.1 + 0.55 + (n - 1) * 0.12, per = Math.max(0.5, (c.dur - lead - 0.3) / n);
      items.forEach(function (el, i) {
        var st = c.t + lead + i * per, z = between(c.r, 1.12, 1.22), tilt = c.calm ? 0 : between(c.r, -1.5, 1.5);
        tl.to(el, { scale: z, rotation: tilt, duration: per * 0.35, ease: "power2.out" }, st);
        tl.to(el, { scale: 1, rotation: 0, duration: per * 0.4, ease: "power2.inOut" }, st + per * 0.35);
      });
    }
    f.spot = true;
  });
  // ---- Deux colonnes : les lignes entrent en alternant gauche / droite.
  HANDLERS.push(function (c, f) {
    if (!c.has(".cols2")) return;
    tl.fromTo(c.sel + " .cols2 .dline", { opacity: 0, x: function (i) { return side(i, c.dx * 0.25); }, y: 18 },
      { opacity: 1, x: 0, y: 0, duration: 0.5, ease: "power3.out", stagger: 0.1 }, c.t + 0.15);
    f.cols2 = true;
  });
  // ---- Tampon : lancé de travers depuis un point tiré au sort, claque, secoue légèrement la scène.
  HANDLERS.push(function (c, f) {
    var stamps = c.q(".stamp");
    if (!stamps.length) return;
    stamps.forEach(function (el, i) {
      var r0 = sign(c.r) * between(c.r, 10, 22), rf = sign(c.r) * between(c.r, 1.5, 5), s0 = between(c.r, 2.2, 3.2), t0 = c.t + 0.35 + i * 0.24;
      tl.fromTo(el, { scale: s0, opacity: 0, rotation: r0, x: (c.r() - 0.5) * c.dx * 0.5, y: -c.dy * 0.3 * c.r() },
        { scale: 0.94, opacity: 1, rotation: rf, x: 0, y: 0, duration: 0.24, ease: "power4.in" }, t0);
      tl.to(el, { scale: 1, duration: 0.2, ease: "back.out(3)" }, t0 + 0.24);
      if (!c.calm) {
        var z = c.sel + " .zone", a = (c.ov ? 5 : 10) * sign(c.r), ti = t0 + 0.24;
        tl.to(z, { x: a, duration: 0.04, ease: "none" }, ti).to(z, { x: -a, duration: 0.06, ease: "none" }, ti + 0.04).to(z, { x: 0, duration: 0.07, ease: "power2.out" }, ti + 0.1);
      }
    });
    f.stamp = true;
  });
  // ---- Pastilles : dispersées autour de leur place, dans un ordre mélangé (graine fixe, jamais aléatoire).
  HANDLERS.push(function (c, f) {
    var chips = c.q(".chip");
    if (!chips.length) return;
    shuffled(chips.map(function (_, i) { return i; }), c.r).forEach(function (idx, k) {
      tl.fromTo(chips[idx], { scale: 0, opacity: 0, x: (c.r() - 0.5) * 2 * c.dx * 0.3, y: (c.r() - 0.5) * c.dy * 0.7, rotation: (c.r() - 0.5) * 80 },
        { scale: 1, opacity: 1, x: 0, y: 0, rotation: 0, duration: 0.55, ease: "back.out(2.2)" }, c.t + 0.25 + k * 0.14);
    });
    f.chip = true;
  });
  // ---- Icônes (coche, croix…) : la pastille tourne en entrant, puis le trait se dessine.
  HANDLERS.push(function (c, f) {
    var icons = c.q(".dico");
    if (!icons.length) return;
    icons.forEach(function (el, i) {
      tl.fromTo(el, { scale: 0, rotation: sign(c.r) * (c.calm ? 40 : 140) }, { scale: 1, rotation: 0, duration: 0.5, ease: "back.out(2.2)" }, c.t + 0.2 + i * 0.14);
    });
    tl.fromTo(c.sel + " .dico path", { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.5, ease: "power2.out", stagger: 0.07 }, c.t + 0.45);
    f.icon = true;
  });
  // ---- Flèches : arrivent de directions différentes, puis un va-et-vient (gauche puis droite).
  HANDLERS.push(function (c, f) {
    var arrows = c.q(".darr");
    if (!arrows.length) return;
    arrows.forEach(function (el, i) {
      var v = vec(draw("arr", ["L", "R", "T", "B"]), c, 0.2), s0 = c.t + 0.3 + i * 0.28;
      tl.fromTo(el, assign({ opacity: 0, scale: 0.5, rotation: sign(c.r) * 15 }, v), assign({ opacity: 1, scale: 1, rotation: 0, x: 0, y: 0, duration: 0.6, ease: "back.out(2.4)" }, {}), s0);
      if (!c.calm) tl.to(el, { x: -9, duration: 0.14, ease: "power1.inOut" }, s0 + 0.75).to(el, { x: 9, duration: 0.2, ease: "power1.inOut" }, s0 + 0.89).to(el, { x: 0, duration: 0.14, ease: "power1.inOut" }, s0 + 1.09);
    });
    f.arrow = true;
  });
  // ---- Punchline : mots depuis des directions variées, dernier mot appuyé, avancée ou recul lent.
  HANDLERS.push(function (c, f) {
    if (!c.step.classList.contains("step-punch")) return;
    var words = c.q(".w");
    words.forEach(function (el, i) {
      var v = vec(draw("pw", ["L", "R", "T", "B"]), c, 0.3), from = assign({ opacity: 0, scale: pick(c.r, [0.6, 1.5]), rotation: sign(c.r) * between(c.r, 3, 9) }, v);
      tl.fromTo(el, from, assign(assign({ opacity: 1, rotation: 0 }, zero(v)), { scale: 1, duration: 0.5, ease: pick(c.r, ["back.out(1.7)", "expo.out", "power4.out"]) }), c.t + 0.1 + i * 0.2);
    });
    if (words.length && !c.calm) tl.to(words[words.length - 1], { scale: 1.12, duration: 0.15, yoyo: true, repeat: 1, ease: "power2.out" }, c.t + 0.1 + (words.length - 1) * 0.2 + 0.55);
    var back = c.r() < 0.35;
    tl.fromTo(c.sel + " .punch-text", { scale: back ? 1.05 : 1 }, { scale: back ? 1 : 1.035, duration: c.dur, ease: "none" }, c.t);
    f.punch = true;
  });
