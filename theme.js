/* ─────────────────────────────────────────────────────────────
   MaySon · Background Themes  (Morning / Afternoon / Night Sky)
   Shared by index.html, menu.html and admin.html.

   • Loaded in <head>, so the saved theme is applied before the page
     paints (no flash of the wrong theme).
   • The choice is stored in localStorage under 'mayson_theme' and is
     kept in sync across open tabs.
   • Night Sky is the default and matches the original MaySon look.
   ───────────────────────────────────────────────────────────── */
(function () {
  'use strict';

  var KEY = 'mayson_theme';
  var SEEN = 'mayson_theme_seen';
  var DEFAULT = 'night';
  var THEMES = {
    morning:   { label: 'Morning',   icon: '🌤️', sub: 'Bright & fresh',    swatch: 'linear-gradient(160deg,#a9d8ff,#fff3d6)' },
    afternoon: { label: 'Afternoon', icon: '🌇', sub: 'Warm golden hour',  swatch: 'linear-gradient(160deg,#ffe9bf,#ffb987)' },
    night:     { label: 'Night Sky', icon: '🌙', sub: 'Stars & moonlight', swatch: 'linear-gradient(160deg,#0d1428,#080c18)' }
  };
  var ORDER = ['morning', 'afternoon', 'night'];

  function getTheme() {
    try { var t = localStorage.getItem(KEY); if (THEMES[t]) return t; } catch (e) {}
    return DEFAULT;
  }
  function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    var fi = document.getElementById('theme-fab-icon');
    if (fi) fi.textContent = THEMES[t].icon;
    var fc = document.getElementById('theme-fab-current');
    if (fc) fc.textContent = THEMES[t].label;
    var opts = document.querySelectorAll('.theme-opt');
    for (var i = 0; i < opts.length; i++) {
      var on = opts[i].getAttribute('data-theme-id') === t;
      opts[i].setAttribute('aria-checked', on ? 'true' : 'false');
      opts[i].classList.toggle('active', on);
    }
  }
  function setTheme(t) {
    if (!THEMES[t]) return;
    var root = document.documentElement;
    root.classList.add('theme-anim');                       // soft cross-fade
    setTimeout(function () { root.classList.remove('theme-anim'); }, 450);
    try { localStorage.setItem(KEY, t); } catch (e) {}
    applyTheme(t);
  }

  applyTheme(getTheme());                                   // apply immediately (we're in <head>)

  /* ── STYLES ─────────────────────────────────────────────── */
  var LIGHT = 'html:is([data-theme="morning"],[data-theme="afternoon"])';
  var css = [
    /* Sky layer sits behind everything; body must be see-through so it shows. */
    'html[data-theme] body{background:transparent!important}',
    '#stars{background:transparent!important}',
    '#theme-sky{position:fixed;inset:0;z-index:-1;pointer-events:none;overflow:hidden}',
    '.ts-sun,.ts-moon,.ts-shoot,.ts-cloud{position:absolute;display:none}',

    /* ── NIGHT SKY (default — identical to the original background) ── */
    'html[data-theme="night"]{color-scheme:dark}',
    'html[data-theme="night"] #theme-sky{background:radial-gradient(ellipse at 20% 50%,rgba(59,130,246,.06) 0%,transparent 60%),radial-gradient(ellipse at 80% 20%,rgba(168,139,250,.06) 0%,transparent 60%),#080c18}',
    'html[data-theme="night"] .ts-moon{display:block;top:9%;right:9%;width:62px;height:62px;border-radius:50%;',
    '  background:radial-gradient(circle at 35% 35%,#ffffff,#dfe6ff 55%,#aebbea);opacity:.85;',
    '  box-shadow:0 0 44px 10px rgba(190,205,255,.22)}',
    'html[data-theme="night"] .ts-shoot{display:block;top:14%;left:78%;width:110px;height:2px;opacity:0;',
    '  background:linear-gradient(90deg,rgba(255,255,255,0),#fff);border-radius:2px;animation:tsShoot 11s ease-in 3s infinite}',
    '@keyframes tsShoot{0%{transform:translate(0,0) rotate(35deg);opacity:0}2%{opacity:.95}9%{transform:translate(-340px,238px) rotate(35deg);opacity:0}100%{transform:translate(-340px,238px) rotate(35deg);opacity:0}}',

    /* ── SHARED LIGHT-THEME RULES ── */
    LIGHT + ' .star{display:none}',
    LIGHT + ' .ts-sun{display:block;border-radius:50%;animation:tsPulse 7s ease-in-out infinite}',
    LIGHT + ' .ts-cloud{display:block;left:0;width:150px;height:42px;border-radius:42px;background:var(--cloud);opacity:.92;',
    '  transform:translateX(-300px);animation:tsDrift var(--dur,120s) linear var(--delay,0s) infinite}',
    LIGHT + ' .ts-cloud::before,' + LIGHT + ' .ts-cloud::after{content:"";position:absolute;border-radius:50%;background:inherit}',
    LIGHT + ' .ts-cloud::before{width:70px;height:70px;top:-34px;left:22px}',
    LIGHT + ' .ts-cloud::after{width:54px;height:54px;top:-22px;left:76px}',
    '.ts-cloud.c1{top:12%;--dur:95s;--delay:-30s}',
    '.ts-cloud.c2{top:27%;--dur:140s;--delay:-95s;scale:.7}',
    '.ts-cloud.c3{top:58%;--dur:170s;--delay:-60s;scale:1.25;opacity:.6!important}',
    '.ts-cloud.c4{top:76%;--dur:120s;--delay:-15s;scale:.85;opacity:.7!important}',
    '@keyframes tsDrift{from{transform:translateX(-300px)}to{transform:translateX(calc(100vw + 300px))}}',
    '@keyframes tsPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.07)}}',

    /* Card shadows read too heavy on light backgrounds */
    LIGHT + ' :is(.auth-card,.puzzle-card,.table-card,.stars-info-card,.modal-box){box-shadow:0 14px 40px rgba(40,70,110,.16)!important}',
    /* Modal scrims: light instead of near-black, so text sitting directly on them stays readable */
    LIGHT + ' :is(#success-overlay,#exit-overlay,#logout-overlay,#stars-info-overlay,.success-overlay,.modal-overlay){background:var(--scrim)!important}',
    /* Elements with hard-coded dark styling */
    LIGHT + ' .puzzle-banner{background:var(--banner)!important}',
    LIGHT + ' .ide-topbar{background:rgba(0,0,0,.05)!important}',
    /* Lesson text colours are written inline as neon hex values; map them to readable ones */
    LIGHT + ' [style*="color:#22d3ee"]{color:var(--cyan)!important}',
    LIGHT + ' [style*="color:#4ade80"]{color:var(--green)!important}',
    LIGHT + ' [style*="color:#3b82f6"]{color:var(--blue)!important}',
    LIGHT + ' [style*="color:#fb923c"]{color:var(--orange)!important}',
    LIGHT + ' [style*="color:#f472b6"]{color:var(--pink)!important}',
    LIGHT + ' [style*="color:#fbbf24"]{color:var(--yellow)!important}',
    LIGHT + ' [style*="color:#f87171"]{color:var(--red)!important}',
    LIGHT + ' [style*="color:#a78bfa"]{color:var(--purple)!important}',

    /* ── MORNING ── */
    'html[data-theme="morning"]{color-scheme:light;',
    '  --bg:#d9eeff;--bg2:#edf7ff;--card:#ffffff;--border:#b7d3ec;--white:#12304f;--dim:#3f5b78;',
    '  --blue:#2563eb;--cyan:#0e7490;--green:#15803d;--yellow:#b45309;--orange:#c2410c;--pink:#be185d;--purple:#6d28d9;--red:#dc2626;',
    '  --scrim:rgba(225,240,255,.88);--banner:linear-gradient(135deg,#cfe6fb,#eaf5ff);--cloud:rgba(255,255,255,.95)}',
    'html[data-theme="morning"] #theme-sky{background:linear-gradient(180deg,#a9d8ff 0%,#d3ecff 52%,#fff3d6 100%)}',
    'html[data-theme="morning"] .ts-sun{top:8%;right:9%;width:88px;height:88px;',
    '  background:radial-gradient(circle at 40% 40%,#fffbe0,#ffe066 65%,#ffd23f);box-shadow:0 0 90px 40px rgba(255,224,102,.55)}',

    /* ── AFTERNOON ── */
    'html[data-theme="afternoon"]{color-scheme:light;',
    '  --bg:#ffe3b8;--bg2:#fff3dc;--card:#fffaf1;--border:#eac88f;--white:#3a2410;--dim:#6b4a2a;',
    '  --blue:#2563eb;--cyan:#0f766e;--green:#15803d;--yellow:#b45309;--orange:#c2410c;--pink:#be185d;--purple:#6d28d9;--red:#dc2626;',
    '  --scrim:rgba(255,240,215,.9);--banner:linear-gradient(135deg,#ffe0a8,#fff1d2);--cloud:rgba(255,244,228,.9)}',
    'html[data-theme="afternoon"] #theme-sky{background:linear-gradient(180deg,#ffe9bf 0%,#ffd6a0 48%,#ffc297 100%)}',
    'html[data-theme="afternoon"] .ts-sun{left:8%;bottom:9%;width:124px;height:124px;',
    '  background:radial-gradient(circle at 40% 40%,#fff2c4,#ffb347 60%,#ff8c3a);box-shadow:0 0 120px 60px rgba(255,150,60,.42)}',

    /* Smooth cross-fade while switching */
    'html.theme-anim,html.theme-anim *{transition:background-color .4s,color .4s,border-color .4s,box-shadow .4s!important}',
    '@media (prefers-reduced-motion:reduce){.ts-cloud,.ts-sun,.ts-shoot{animation:none!important}.ts-cloud{transform:translateX(12vw)}}',

    /* ── PICKER ── */
    '#theme-fab{position:fixed;right:18px;bottom:18px;z-index:90;display:flex;align-items:center;gap:10px;',
    '  padding:6px 18px 6px 6px;border-radius:999px;border:2px solid rgba(255,255,255,.55);cursor:pointer;',
    '  background:linear-gradient(135deg,#7c3aed,#3b82f6);color:#fff;font-family:var(--fb,"Nunito",sans-serif);text-align:left;',
    '  box-shadow:0 8px 28px rgba(76,60,220,.55),0 2px 8px rgba(0,0,0,.25);',
    '  transition:transform .2s cubic-bezier(.34,1.56,.64,1),box-shadow .2s}',
    '#theme-fab:hover{transform:translateY(-3px) scale(1.04);box-shadow:0 12px 36px rgba(76,60,220,.7),0 2px 8px rgba(0,0,0,.25)}',
    '#theme-fab:active{transform:scale(.97)}',
    '#theme-fab-icon{flex-shrink:0;width:38px;height:38px;border-radius:50%;background:rgba(255,255,255,.95);',
    '  display:flex;align-items:center;justify-content:center;font-size:1.3rem;line-height:1}',
    '#theme-fab-text{display:flex;flex-direction:column;line-height:1.15}',
    '#theme-fab-label{font-size:.86rem;font-weight:800;letter-spacing:.01em}',
    '#theme-fab-current{font-size:.7rem;font-weight:700;opacity:.85}',
    /* Attention pulse until the visitor opens the picker for the first time */
    '#theme-fab.attn::before{content:"";position:absolute;inset:-6px;border-radius:999px;border:3px solid #a78bfa;',
    '  pointer-events:none;animation:tsRing 1.8s ease-out infinite}',
    '@keyframes tsRing{0%{transform:scale(.94);opacity:.95}100%{transform:scale(1.16);opacity:0}}',
    /* Speech bubble that explains the button */
    '#theme-tip{position:fixed;right:18px;bottom:84px;z-index:90;max-width:230px;padding:10px 32px 10px 14px;display:none;',
    '  background:var(--card);color:var(--white);border:2px solid #a78bfa;border-radius:14px;',
    '  font-family:var(--fb,"Nunito",sans-serif);font-size:.8rem;font-weight:700;line-height:1.4;',
    '  box-shadow:0 12px 32px rgba(0,0,0,.35);animation:tsBob 2.4s ease-in-out infinite}',
    '#theme-tip.show{display:block}',
    '#theme-tip::after{content:"";position:absolute;bottom:-9px;right:40px;width:14px;height:14px;background:var(--card);',
    '  border-right:2px solid #a78bfa;border-bottom:2px solid #a78bfa;transform:rotate(45deg)}',
    '#theme-tip b{color:#a78bfa}',
    '#theme-tip-x{position:absolute;top:4px;right:6px;width:22px;height:22px;border:none;background:transparent;color:var(--dim);',
    '  font-size:.85rem;font-weight:800;cursor:pointer;border-radius:6px}',
    '#theme-tip-x:hover{color:var(--red)}',
    '@keyframes tsBob{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}',
    '#theme-fab:focus-visible,.theme-opt:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}',
    '#theme-pop{position:fixed;right:18px;bottom:84px;z-index:91;width:286px;padding:14px;display:none;',
    '  background:var(--card);border:1px solid var(--border);border-radius:16px;box-shadow:0 16px 44px rgba(0,0,0,.35);',
    '  font-family:var(--fb,"Nunito",sans-serif);color:var(--white)}',
    '#theme-pop.show{display:block;animation:tsPop .22s cubic-bezier(.34,1.56,.64,1) both}',
    '@keyframes tsPop{from{opacity:0;transform:translateY(8px) scale(.94)}to{opacity:1;transform:none}}',
    '.theme-pop-title{font-size:.95rem;font-weight:800;color:var(--white);padding:2px 4px 2px}',
    '.theme-pop-desc{font-size:.78rem;line-height:1.45;color:var(--white);opacity:.78;padding:0 4px 6px}',
    '.theme-opt{display:flex;align-items:center;gap:12px;width:100%;padding:8px 10px;margin-top:6px;text-align:left;cursor:pointer;',
    '  background:var(--bg2);border:1.5px solid var(--border);border-radius:12px;color:var(--white);font-family:inherit;transition:border-color .15s,transform .15s}',
    '.theme-opt:hover{transform:translateX(-2px);border-color:var(--cyan)}',
    '.theme-opt.active{border-color:var(--cyan);box-shadow:0 0 0 3px rgba(34,211,238,.18)}',
    '.theme-sw{flex-shrink:0;width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.15rem;border:1px solid rgba(128,128,128,.35)}',
    '.theme-txt{flex:1;min-width:0}',
    '.theme-name{display:block;font-size:.86rem;font-weight:800}',
    '.theme-sub{display:block;font-size:.72rem;color:var(--dim);margin-top:1px}',
    '.theme-check{font-size:.95rem;font-weight:900;color:var(--cyan);visibility:hidden}',
    '.theme-opt.active .theme-check{visibility:visible}',
    '@media (max-width:480px){#theme-fab{right:12px;bottom:12px;padding-right:14px}#theme-fab-current{display:none}',
    '  #theme-pop{right:12px;left:12px;width:auto}#theme-tip{right:12px}}',
    '@media (prefers-reduced-motion:reduce){#theme-fab.attn::before,#theme-tip{animation:none!important}}'
  ].join('\n');

  var style = document.createElement('style');
  style.id = 'theme-styles';
  style.textContent = css;
  document.head.appendChild(style);

  /* ── DOM (sky + picker) ─────────────────────────────────── */
  function build() {
    if (document.getElementById('theme-sky')) return;

    var sky = document.createElement('div');
    sky.id = 'theme-sky';
    sky.setAttribute('aria-hidden', 'true');
    sky.innerHTML = '<div class="ts-sun"></div><div class="ts-moon"></div><div class="ts-shoot"></div>' +
      '<div class="ts-cloud c1"></div><div class="ts-cloud c2"></div><div class="ts-cloud c3"></div><div class="ts-cloud c4"></div>';
    document.body.insertBefore(sky, document.body.firstChild);

    var fab = document.createElement('button');
    fab.id = 'theme-fab';
    fab.type = 'button';
    fab.title = 'Change the background: Morning, Afternoon or Night Sky';
    fab.setAttribute('aria-label', 'Change background theme');
    fab.setAttribute('aria-haspopup', 'true');
    fab.setAttribute('aria-expanded', 'false');
    fab.innerHTML = '<span id="theme-fab-icon"></span>' +
      '<span id="theme-fab-text"><span id="theme-fab-label">Change theme</span><span id="theme-fab-current"></span></span>';

    var pop = document.createElement('div');
    pop.id = 'theme-pop';
    pop.setAttribute('role', 'radiogroup');
    pop.setAttribute('aria-label', 'Background theme');
    var html = '<div class="theme-pop-title">🎨 Choose your background</div>' +
      '<div class="theme-pop-desc">Changes how MaySon looks, so you can pick whatever is easiest on your eyes. It doesn\'t affect your levels or progress, and your choice is remembered.</div>';
    ORDER.forEach(function (id) {
      var t = THEMES[id];
      html += '<button type="button" class="theme-opt" role="radio" aria-checked="false" data-theme-id="' + id + '">' +
        '<span class="theme-sw" style="background:' + t.swatch + '">' + t.icon + '</span>' +
        '<span class="theme-txt"><span class="theme-name">' + t.label + '</span><span class="theme-sub">' + t.sub + '</span></span>' +
        '<span class="theme-check">✓</span></button>';
    });
    pop.innerHTML = html;

    var tip = document.createElement('div');
    tip.id = 'theme-tip';
    tip.setAttribute('role', 'note');
    tip.innerHTML = '<b>New:</b> pick a background! Tap this button to switch between Morning, Afternoon and Night Sky.' +
      '<button type="button" id="theme-tip-x" aria-label="Dismiss tip">✕</button>';

    document.body.appendChild(pop);
    document.body.appendChild(tip);
    document.body.appendChild(fab);

    var seen = false;
    try { seen = localStorage.getItem(SEEN) === '1'; } catch (e) {}
    function markSeen() {
      if (seen) return;
      seen = true;
      try { localStorage.setItem(SEEN, '1'); } catch (e) {}
      fab.classList.remove('attn');
      tip.classList.remove('show');
    }
    function placeAboveFab(el, gap) {                       // stays right even if a page moves the button (e.g. the IDE)
      var r = fab.getBoundingClientRect();
      el.style.bottom = Math.max(8, window.innerHeight - r.top + gap) + 'px';
    }
    if (!seen) {
      fab.classList.add('attn');
      tip.classList.add('show');
      placeAboveFab(tip, 12);
      window.addEventListener('resize', function () { if (!seen) placeAboveFab(tip, 12); });
    }
    tip.querySelector('#theme-tip-x').addEventListener('click', function (e) { e.stopPropagation(); markSeen(); });

    function open(v) {
      if (v) { markSeen(); placeAboveFab(pop, 10); }
      pop.classList.toggle('show', v);
      fab.setAttribute('aria-expanded', v ? 'true' : 'false');
    }
    fab.addEventListener('click', function (e) { e.stopPropagation(); open(!pop.classList.contains('show')); });
    pop.addEventListener('click', function (e) {
      e.stopPropagation();
      var b = e.target.closest ? e.target.closest('.theme-opt') : null;
      if (b) { setTheme(b.getAttribute('data-theme-id')); }
    });
    document.addEventListener('click', function () { open(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && pop.classList.contains('show')) { open(false); fab.focus(); } });

    applyTheme(getTheme());
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build);
  else build();

  /* Keep other open tabs/pages in sync */
  window.addEventListener('storage', function (e) { if (e.key === KEY) applyTheme(getTheme()); });

  window.MaySonTheme = { get: getTheme, set: setTheme, themes: Object.keys(THEMES) };
})();
