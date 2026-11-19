  // ---- Versus : les colonnes arrivent chacune de leur côté, puis la gauche recule et la droite s'impose (états finaux inchangés).
  HANDLERS.push(function (c, f) {
    if (!c.has(".versus")) return;
    var vert = c.r() < 0.3 && !c.calm;       // variante : la gauche tombe, la droite monte
    tl.fromTo(c.sel + " .vsep", { scaleY: 0 }, { scaleY: 1, duration: 0.5, ease: "power2.out" }, c.t + 0.15);
    tl.fromTo(c.sel + " .vcol.left", vert ? { opacity: 0, y: -c.dy * 0.5, scale: 1, x: 0 } : { opacity: 0, x: -c.dx * 0.8, scale: 1 },
      { opacity: 1, x: -24, y: 0, scale: 0.82, duration: 0.75, ease: "power3.out" }, c.t + 0.2);
    tl.fromTo(c.sel + " .vcol.right", vert ? { opacity: 0, y: c.dy * 0.5, scale: 0.9, x: 0 } : { opacity: 0, x: c.dx * 0.8, scale: 0.9 },
      { opacity: 1, x: 0, y: 0, scale: 1.16, duration: 0.85, ease: "back.out(1.4)" }, c.t + 0.3);
    f.versus = true;
  });
  // ---- Diverge : le tronc vient de la gauche, chaque flèche part de lui avec un rebond ; ordre ↗ puis ↘ conservé.
  HANDLERS.push(function (c, f) {
    if (!c.has(".diverge")) return;
    var up = c.sel + " .branch.up", dn = c.sel + " .branch.down", e = c.calm ? "power3.out" : "elastic.out(1, 0.6)", d = c.calm ? 0.5 : 0.8;
    if (c.has(".trunk")) tl.fromTo(c.sel + " .trunk", { opacity: 0, x: -c.dx * 0.4 }, { opacity: 1, x: 0, duration: 0.6, ease: "expo.out" }, c.t + 0.1);
    tl.fromTo(up + " .darr-big", { opacity: 0, x: -90 * c.k, y: 90 * c.k, scale: 0.4 }, { opacity: 1, x: 0, y: 0, scale: 1, duration: d, ease: e }, c.t + 0.35);
    tl.fromTo(dn + " .darr-big", { opacity: 0, x: -90 * c.k, y: -90 * c.k, scale: 0.4 }, { opacity: 1, x: 0, y: 0, scale: 1, duration: d, ease: e }, c.t + 0.85);
    tl.fromTo(up + " .dsub", { opacity: 0, x: c.dx * 0.15 }, { opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }, c.t + 0.6);
    tl.fromTo(dn + " .dsub", { opacity: 0, x: c.dx * 0.15 }, { opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }, c.t + 1.1);
    if (!c.calm) {
      tl.to(up + " .darr-big", { scale: 1.3, duration: 0.25, yoyo: true, repeat: 1, ease: "power2.inOut" }, c.t + 1.2);
      tl.to(dn + " .darr-big", { scale: 1.3, duration: 0.25, yoyo: true, repeat: 1, ease: "power2.inOut" }, c.t + 1.7);
    }
    f.diverge = true;
  });
  // ---- Carte de référence : arrive inclinée d'un côté, lignes alternées, surlignage balayé, zoom lent.
  HANDLERS.push(function (c, f) {
    var card = c.step.querySelector(".ref-card");
    if (!card) return;
    var rs = "#" + card.id, v = vec(c.force && ["L", "R", "T", "B"].indexOf(c.force) >= 0 ? c.force : draw("card", ["L", "R", "B"]), c, 0.5);
    tl.fromTo(rs, { opacity: 0 }, { opacity: 1, duration: 0.35, ease: "power1.out" }, c.t);
    tl.fromTo(rs, assign({ rotation: sign(c.r) * 3 * c.k }, v), assign(zero(v), { rotation: 0, duration: 0.75, ease: "expo.out" }), c.t);
    tl.fromTo(rs + " > div", { opacity: 0, x: function (i) { return side(i, 60 * c.k); } }, { opacity: 1, x: 0, duration: 0.5, ease: "power3.out", stagger: 0.12 }, c.t + 0.2);
    tl.to(rs + " .hl", { color: "#F0B429", backgroundSize: "100% 100%", duration: 0.7, ease: "power2.inOut" }, c.t + 1.0);
    tl.fromTo(rs, { scale: 1 }, { scale: 1.03, duration: c.dur, ease: "none", immediateRender: false }, c.t);
    f.ref = true;
  });
  // ---- Barres : chaque barre pousse avec sa propre courbe (sans dépassement), les libellés arrivent en alternance.
  HANDLERS.push(function (c, f) {
    var fills = c.q(".bfill");
    if (!fills.length) return;
    fills.forEach(function (el, i) {
      tl.fromTo(el, { scaleX: 0 }, { scaleX: parseFloat(el.getAttribute("data-w")) / 100, transformOrigin: "left center",
        duration: between(c.r, 0.7, 1.1), ease: pick(c.r, ["power3.out", "expo.out", "circ.out"]) }, c.t + 0.3 + i * 0.14);
    });
    tl.fromTo(c.sel + " .blab", { opacity: 0, x: function (i) { return side(i, c.dx * 0.2); } }, { opacity: 1, x: 0, duration: 0.5, ease: "power3.out", stagger: 0.14 }, c.t + 0.2);
    f.bars = true;
  });
  // ---- Seuil : le remplissage rejoint la valeur, le repère tombe et rebondit.
  HANDLERS.push(function (c, f) {
    if (!c.has(".sfill")) return;
    tl.fromTo(c.sel + " .sfill", { scaleX: 0 }, { scaleX: function (i, el) { return parseFloat(el.getAttribute("data-w")) / 100; }, transformOrigin: "left center",
      duration: between(c.r, 0.8, 1.2), ease: pick(c.r, ["power3.out", "expo.out"]) }, c.t + 0.3);
    tl.fromTo(c.sel + " .stick", { opacity: 0, y: -c.dy * 0.25 }, { opacity: 0.9, y: 0, duration: c.calm ? 0.45 : 0.8, ease: c.calm ? "power3.out" : "bounce.out" }, c.t + 0.55);
    f.seuil = true;
  });
  // ---- Compare3 : les trois lignes entrent en alternant gauche / droite.
  HANDLERS.push(function (c, f) {
    if (!c.has(".crow")) return;
    tl.fromTo(c.sel + " .crow", { opacity: 0, x: function (i) { return side(i, c.dx * 0.3); } }, { opacity: 1, x: 0, duration: 0.55, ease: "power3.out", stagger: 0.16 }, c.t + 0.15);
    f.compare3 = true;
  });
