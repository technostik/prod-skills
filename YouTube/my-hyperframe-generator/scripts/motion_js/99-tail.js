  return {
    step: function (step, sel, t, dur) {
      var c = ctxFor(step, sel, t, dur), f = {};
      if (!c) return f;
      for (var i = 0; i < HANDLERS.length; i++) HANDLERS[i](c, f);
      return f;
    },
    bg: function (dur) { return typeof _bg === "function" && !!_bg(dur); }
  };
})(tl, __MCFG__);
