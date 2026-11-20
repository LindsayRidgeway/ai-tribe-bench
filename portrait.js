/* portrait.js — a member's face, drawn from a sentence about the member.
 *
 * Why this exists (founder, 2026-11-20): *"I would think that Kythe overall should have an image of each member,
 * generated from a bit of text visible, with default text, and editable, in the member's UI. When the user is
 * created, and whenever the text is modified, I would think a new image of the member should be generated."*
 *
 * Two consequences of doing it this way rather than by drawing pictures or calling an image API:
 *
 *   1. There is no picture to store, so there is nothing to regenerate. The face is a function of the text, and the
 *      text lives in the member's `state/identity.md` as a `portrait:` line. Edit the line and the face is different
 *      the moment the page redraws — no job, no queue, no key, no bill, and nothing to fall out of date.
 *   2. It works in a circle that has no image service at all, which is every template install on its first day. A
 *      portrait that needed an API key would be missing exactly for the circles least able to get one.
 *
 * A face that were random would be a different person every reload, so the drawing is DETERMINISTIC: the words
 * choose what they can (hair colour, skin, hair style, glasses, a beard, freckles) and everything they do not name
 * comes from a hash of the rest of the sentence. The same sentence always gives the same face, and a sentence that
 * differs by one word gives a face that differs a little — which is what makes the text feel like it is doing
 * something.
 *
 * Loaded as a plain script (sets window.portraitSVG / window.parseLook) and as CommonJS (module.exports), because
 * the page and the checks have to be looking at the same function. A second copy of this arithmetic is how a face
 * starts disagreeing with its own description.
 */
(function (root) {
  'use strict';

  /* The default sentence. A member with nothing written about its face still has one, and this is the line the
   * member's page offers when the identity has no `portrait:` yet. Deliberately plain: it must not look as though
   * somebody chose it for them. */
  const DEFAULT_PORTRAIT = 'a calm face, short dark hair, and nothing in particular to set it apart';

  // Colour words, and which part of the face they belong to when the sentence does not say. "Blonde" is hair;
  // "pale" is skin; "brown" on its own is neither, because a bare colour word could be either and a machine choosing
  // for you is the one thing a portrait must not do.
  const HAIR = {
    blonde: '#d9b45e', golden: '#d7a949', sandy: '#b99461', tow: '#e0c88c',
    brown: '#5b3d28', brunette: '#4a3020', chestnut: '#6d4326', auburn: '#8d3a20',
    red: '#a83c22', ginger: '#b0521f', copper: '#a5562a',
    black: '#1f1b19', jet: '#141110', dark: '#241d19',
    grey: '#9a9a9e', gray: '#9a9a9e', silver: '#c3c3c9', white: '#e6e6e6'
  };
  const HAIR_ALONE = { blonde: 1, ginger: 1, auburn: 1, brunette: 1, tow: 1, sandy: 1, copper: 1 };
  const SKIN = {
    pale: '#f3d7c3', fair: '#f0cdb1', porcelain: '#f6ddc9', ivory: '#f2d9c4',
    olive: '#d3a878', tan: '#c08a5a', bronze: '#b57a49', brown: '#8d5a37',
    dark: '#68401f', ebony: '#4a2b16', deep: '#523020'
  };
  const SKIN_ALONE = { pale: 1, fair: 1, olive: 1, porcelain: 1, ebony: 1, bronze: 1, ivory: 1, tan: 1 };

  /* Unnamed hair and skin are picked from a short list of things hair and skin are actually coloured, not from the
   * colour wheel. The first version took a hue from the hash and gave a bald man a pink beard. */
  const HAIR_ANY = ['#1f1b19', '#33261c', '#4a3020', '#5b3d28', '#6d4326', '#8d3a20', '#8a6a3d', '#9a9a9e'];
  const SKIN_ANY = ['#f3d7c3', '#e8c0a8', '#d9a98b', '#c08a5a', '#a86f45', '#8d5a37', '#68401f'];
  const STYLE = { ponytail: 1, bun: 1, curls: 1, curly: 1, braid: 1, plait: 1, long: 1, short: 1, cropped: 1, bald: 1 };
  const EXTRA = { glasses: 1, spectacles: 1, freckles: 1, beard: 1, moustache: 1, mustache: 1, earrings: 1 };

  /* FNV-1a over the whole sentence. Any 32-bit hash would do; this one is short enough to read and stable across
   * engines, which is the only property that matters — the face must not change because a browser changed. */
  function hash32(s) {
    let h = 0x811c9dc5;
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0;
    }
    return h >>> 0;
  }

  // A number in [0,1) taken from a hash at a given position, so one sentence can drive a dozen independent choices
  // without any two of them being correlated: `pick(h, 3)` is a different choice from `pick(h, 4)`.
  function pick(h, n) {
    let x = (h ^ (n * 0x9e3779b1)) >>> 0;
    x = Math.imul(x ^ (x >>> 16), 0x21f0aaad) >>> 0;
    x = Math.imul(x ^ (x >>> 15), 0x735a2d97) >>> 0;
    x = (x ^ (x >>> 15)) >>> 0;
    return x / 4294967296;
  }

  function words(text) {
    // Hyphens and apostrophes are word breaks here. "mid-brown" is one word to a reader of the sentence and two to
    // this file, and the first version read it as neither: "mid-brown hair" came out GREY, because the token was
    // "mid-brown" and no colour in the list is spelled that way.
    return String(text || '').toLowerCase().replace(/[-']+/g, ' ').replace(/[^a-z\s]+/g, ' ').split(/\s+/).filter(Boolean);
  }

  /* The words that name a thing, read in context: "brown hair" is hair, "brown skin" is skin, "brown eyes" is
   * neither. A colour word two places before the noun still counts, because that is how people write. */
  function parseLook(text) {
    const raw = String(text || '').trim();
    const t = raw || DEFAULT_PORTRAIT;
    const ws = words(t);
    const h = hash32(t);

    let hair = null, skin = null, style = null;
    const extras = {};
    for (let i = 0; i < ws.length; i++) {
      const w = ws[i], next = ws[i + 1] || '';
      // "dark brown hair": the colour after "dark" is the colour. Reading "dark" as the answer would make every
      // dark-haired sentence the same shade.
      const skipDark = w === 'dark' && !!HAIR[next];
      // "a black beard" names the hair colour as surely as "black hair" does — the first version gave a bald man a
      // red beard from a sentence that said black, because the beard is drawn in the hair colour and the noun was
      // not one it looked beside.
      if (!skipDark && HAIR[w] && ((next === 'hair' || next === 'haired' || next === 'locks' || next === 'mane'
                       || next === 'beard' || next === 'moustache' || next === 'mustache') || HAIR_ALONE[w])) {
        if (!hair) hair = HAIR[w];
      }
      if (SKIN[w] && (next === 'skin' || next === 'skinned' || next === 'complexion' || SKIN_ALONE[w])) {
        if (!skin) skin = SKIN[w];
      }
      if (STYLE[w] && !style) style = w === 'curly' ? 'curls' : (w === 'plait' ? 'braid' : w);
      if (EXTRA[w]) extras[w === 'spectacles' ? 'glasses' : (w === 'mustache' ? 'moustache' : w)] = true;
    }
    if (!hair) {
      for (let i = 0; i + 1 < ws.length; i++) {
        if ((ws[i + 1] === 'hair' || ws[i + 1] === 'haired') && HAIR[ws[i]]) hair = HAIR[ws[i]];
        if (i + 2 < ws.length && (ws[i + 2] === 'hair' || ws[i + 2] === 'haired') && HAIR[ws[i + 1]]) hair = HAIR[ws[i + 1]];
      }
    }
    if (!skin) {
      for (let i = 0; i + 1 < ws.length; i++) {
        if ((ws[i + 1] === 'skin' || ws[i + 1] === 'complexion') && SKIN[ws[i]]) skin = SKIN[ws[i]];
      }
    }

    /* Shape and temper, for the words that describe a face rather than a colour. Everything here is a phrase the
     * sentence may or may not contain; anything not said comes from the hash as before. It matters because a cast is
     * described in prose — "a broad jaw" and "an open grin" are how you would tell two of these people apart — and a
     * portrait that ignored the description would be drawn from the sentence's length rather than its sense. */
    const said = (re) => re.test(t);
    // Unnamed, the hair is short or cropped and nothing else. A bun, a braid and a ponytail are choices somebody
    // made about themselves; a face given one by a hash is the same fault as a face given a sex by a hash.
    const styles = ['short', 'cropped'];
    const shape = {
      broad: said(/\b(broad|wide|heavy|square|round)\b/),
      narrow: said(/\b(narrow|thin|fine|slight|delicate)\b/),
      longFace: said(/\b(long[- ]face|long-faced|gaunt|lean)\b/),
      roundFace: said(/\b(round face|full face|chubby)\b/),
      smile: said(/\b(smil|grin|laugh|cheerful|warm)\b/),
      stern: said(/\b(unsmil|stern|severe|serious|intent|grave|solemn)\b/)
    };
    return {
      text: t,
      hash: h,
      hair: hair || HAIR_ANY[Math.floor(pick(h, 2) * HAIR_ANY.length) % HAIR_ANY.length],
      hairNamed: !!hair,
      skin: skin || SKIN_ANY[Math.floor(pick(h, 3) * SKIN_ANY.length) % SKIN_ANY.length],
      skinNamed: !!skin,
      style: style || styles[Math.floor(pick(h, 6) * styles.length) % styles.length],
      glasses: !!extras.glasses,
      freckles: !!extras.freckles,
      beard: !!extras.beard,
      moustache: !!extras.moustache,
      earrings: !!extras.earrings,
      width: shape.broad ? 0.78 + pick(h, 8) * 0.22 : shape.narrow ? pick(h, 8) * 0.24 : pick(h, 8),
      length: shape.longFace ? 0.74 + pick(h, 9) * 0.26 : shape.roundFace ? pick(h, 9) * 0.26 : pick(h, 9),
      eyeGap: 0.82 + pick(h, 10) * 0.36,
      eyeSize: 0.86 + pick(h, 11) * 0.34,
      brow: -0.16 + pick(h, 12) * 0.34,
      nose: 0.7 + pick(h, 13) * 0.7,
      smile: shape.smile ? 0.55 + pick(h, 14) * 0.45 : shape.stern ? -0.55 + pick(h, 14) * 0.3 : -0.5 + pick(h, 14) * 1.5,
      kit: `hsl(${Math.round(pick(h, 15) * 360)}, 30%, 36%)`
    };
  }

  const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

  /* The drawing. A bust at 240×300: hair behind, shoulders, neck, head, the hair over the crown clipped to the head,
   * then the features. Flat shapes and one line colour, because a member's face is read at 40px in a list and at
   * 300px on its own page, and anything finer disappears at 40 while looking like a pasted photograph at 300. */
  function portraitSVG(text, opts) {
    const L = parseLook(text);
    const o = Object.assign({ size: 300, background: false }, opts || {});
    const cx = 120;
    const hw = 41 + 10 * L.width;                 // half width at the cheekbones
    const top = 58 - 4 * L.width;                 // crown
    const chin = 182 + 22 * L.length;             // chin
    const eyeY = top + (chin - top) * 0.45;
    const eyeDX = hw * 0.42 * L.eyeGap;
    const browY = eyeY - 15;
    const ink = 'rgba(20,16,14,.55)';
    const line = 'rgba(20,16,14,.26)';

    // The head is one path, used twice: filled as the face, and as a clip so the hair can be painted exactly to its
    // edge. The id carries the text's hash so two portraits on one page cannot borrow each other's clip.
    const head = `M${cx - hw},${top + 64} C${cx - hw},${top + 18} ${cx - hw * 0.86},${top} ${cx},${top}`
      + ` C${cx + hw * 0.86},${top} ${cx + hw},${top + 18} ${cx + hw},${top + 64}`
      + ` C${cx + hw},${chin - 34} ${cx + hw * 0.58},${chin} ${cx},${chin}`
      + ` C${cx - hw * 0.58},${chin} ${cx - hw},${chin - 34} ${cx - hw},${top + 64} Z`;
    const clipId = 'hd' + L.hash.toString(36);

    const parts = [];
    const push = (s) => parts.push(s);

    // ---- the mass of the hair, behind everything ------------------------------------------------
    const back = [];
    if (L.style === 'bald') {
      // a bald head is a head; only the hint of hair at the sides, below the crown
      back.push(`<path d="M${cx - hw + 1},${top + 84} C${cx - hw},${top + 40} ${cx - hw * 0.72},${top + 22} ${cx - hw * 0.5},${top + 20}`
        + ` L${cx + hw * 0.5},${top + 20} C${cx + hw * 0.72},${top + 22} ${cx + hw},${top + 40} ${cx + hw - 1},${top + 84}`
        + ` C${cx + hw * 0.62},${top + 52} ${cx - hw * 0.62},${top + 52} ${cx - hw + 1},${top + 84} Z" fill="${L.hair}" opacity=".4"/>`);
    } else if (L.style === 'long' || L.style === 'braid') {
      back.push(`<path d="M${cx - hw - 8},${top + 100} C${cx - hw - 18},${top + 16} ${cx - hw * 0.7},${top - 20} ${cx},${top - 20}`
        + ` C${cx + hw * 0.7},${top - 20} ${cx + hw + 18},${top + 16} ${cx + hw + 8},${top + 100}`
        + ` L${cx + hw + 6},${chin + 40} L${cx - hw - 6},${chin + 40} Z" fill="${L.hair}"/>`);
      if (L.style === 'braid') {
        back.push(`<path d="M${cx + hw + 4},${top + 84} q20,56 2,104 q-18,10 -24,-8 q12,-48 -2,-94 Z" fill="${L.hair}"/>`);
      }
    } else if (L.style === 'ponytail') {
      back.push(`<path d="M${cx - hw - 6},${top + 96} C${cx - hw - 14},${top + 16} ${cx - hw * 0.7},${top - 18} ${cx},${top - 18}`
        + ` C${cx + hw * 0.7},${top - 18} ${cx + hw + 14},${top + 16} ${cx + hw + 6},${top + 96}`
        + ` C${cx + hw * 0.7},${top + 56} ${cx - hw * 0.7},${top + 56} ${cx - hw - 6},${top + 96} Z" fill="${L.hair}"/>`);
      back.push(`<path d="M${cx + hw - 4},${top + 30} q40,30 26,104 q-18,14 -28,-4 q14,-54 -8,-76 Z" fill="${L.hair}"/>`);
    } else if (L.style === 'bun') {
      back.push(`<circle cx="${cx}" cy="${top - 6}" r="${16 + 6 * L.width}" fill="${L.hair}"/>`);
      back.push(`<path d="M${cx - hw - 5},${top + 92} C${cx - hw - 12},${top + 18} ${cx - hw * 0.7},${top - 16} ${cx},${top - 16}`
        + ` C${cx + hw * 0.7},${top - 16} ${cx + hw + 12},${top + 18} ${cx + hw + 5},${top + 92}`
        + ` C${cx + hw * 0.7},${top + 56} ${cx - hw * 0.7},${top + 56} ${cx - hw - 5},${top + 92} Z" fill="${L.hair}"/>`);
    } else if (L.style === 'curls') {
      for (let i = 0; i < 9; i++) {
        const a = Math.PI * (0.04 + 0.92 * (i / 8));
        back.push(`<circle cx="${(cx - Math.cos(a) * (hw + 1)).toFixed(1)}" cy="${(top + 46 - Math.sin(a) * (48 + 6 * L.width)).toFixed(1)}" r="${(12 + 4 * pick(L.hash, 20 + i)).toFixed(1)}" fill="${L.hair}"/>`);
      }
    } else {
      // short and cropped: a mass above and behind the crown, thinner for cropped
      const r = L.style === 'cropped' ? 0.9 : 1;
      back.push(`<ellipse cx="${cx}" cy="${top + 40}" rx="${(hw + 7) * r}" ry="${(46 + 6 * L.width) * r}" fill="${L.hair}"/>`);
    }

    // ---- shoulders and neck ---------------------------------------------------------------------
    push(`<path d="M26,300 C34,242 74,212 120,212 C166,212 206,242 214,300 Z" fill="${L.kit}"/>`);
    push(`<path d="M120,212 L102,232 L120,254 L138,232 Z" fill="${L.kit}" opacity=".5"/>`);
    push(`<path d="M${cx - 15},${chin - 26} L${cx - 14},222 Q${cx},236 ${cx + 14},222 L${cx + 15},${chin - 26} Z" fill="${L.skin}"/>`);
    push(`<path d="M${cx - 15},${chin - 16} Q${cx},${chin + 6} ${cx + 15},${chin - 16} L${cx + 15},${chin} Q${cx},${chin + 22} ${cx - 15},${chin} Z" fill="rgba(20,16,14,.16)"/>`);

    // ---- ears, drawn before the head so they are behind it --------------------------------------
    const ear = 9 + 3 * L.width;
    for (const s of [-1, 1]) {
      push(`<ellipse cx="${(cx + s * (hw - 1)).toFixed(1)}" cy="${(top + 96).toFixed(1)}" rx="${(ear * 0.62).toFixed(1)}" ry="${ear.toFixed(1)}" fill="${L.skin}"/>`);
      push(`<ellipse cx="${(cx + s * (hw - 1)).toFixed(1)}" cy="${(top + 96).toFixed(1)}" rx="${(ear * 0.3).toFixed(1)}" ry="${(ear * 0.52).toFixed(1)}" fill="rgba(20,16,14,.10)"/>`);
    }
    if (L.earrings) {
      push(`<circle cx="${(cx + hw - 1).toFixed(1)}" cy="${(top + 96 + ear * 1.05).toFixed(1)}" r="2.8" fill="#d8b45e"/>`);
    }

    // ---- the face ------------------------------------------------------------------------------
    push(`<path d="${head}" fill="${L.skin}"/>`);

    // ---- hair over the crown, clipped to the head ----------------------------------------------
    // The hairline is a curve from one temple to the other, with a parting, so the face is not a forehead under a
    // cap. Before this the fringe was a band and every portrait wore a headband. Clip id: this text's.
    if (L.style !== 'bald') {
      const part = 0.18 + pick(L.hash, 40) * 0.4;                    // where the parting sits, left of centre
      const px = cx + (part - 0.5) * 2 * hw * 0.6;
      const hairlineY = browY - 12 - 6 * pick(L.hash, 41);
      const cap = `M${cx - hw - 4},${top - 24} L${cx + hw + 4},${top - 24} L${cx + hw + 4},${hairlineY + 10}`
        + ` C${cx + hw * 0.55},${hairlineY + 18} ${px + 8},${hairlineY - 2} ${px},${hairlineY - 12}`
        + ` C${px - 10},${hairlineY - 2} ${cx - hw * 0.55},${hairlineY + 20} ${cx - hw - 4},${hairlineY + 10} Z`;
      push(`<clipPath id="${clipId}"><path d="${head}"/></clipPath>`);
      push(`<g clip-path="url(#${clipId})"><path d="${cap}" fill="${L.hair}"/></g>`);
      if (L.style === 'long' || L.style === 'braid' || L.style === 'ponytail') {
        // a strand down each side of the face, so long hair is not a hood
        push(`<g clip-path="url(#${clipId})"><path d="M${cx - hw - 2},${top + 40} q6,${chin - top} 2,${chin - top + 20} l-14,0 q4,-${chin - top} -2,-${chin - top - 20} Z" fill="${L.hair}" opacity=".92"/>`
          + `<path d="M${cx + hw + 2},${top + 40} q-6,${chin - top} -2,${chin - top + 20} l14,0 q-4,-${chin - top} 2,-${chin - top - 20} Z" fill="${L.hair}" opacity=".92"/></g>`);
      }
    }

    // ---- brows ----------------------------------------------------------------------------------
    const bw = 3.0;
    for (const s of [-1, 1]) {
      const ex = cx + s * eyeDX;
      push(`<path d="M${(ex - 11).toFixed(1)},${(browY + L.brow * 6).toFixed(1)} Q${ex.toFixed(1)},${(browY - 4 + L.brow * 3).toFixed(1)} ${(ex + 11).toFixed(1)},${(browY - L.brow * 5).toFixed(1)}" stroke="${ink}" stroke-width="${bw}" stroke-linecap="round" fill="none"/>`);
    }
    // ---- eyes -----------------------------------------------------------------------------------
    const rx = 6.2 * L.eyeSize, ry = 4.8 * L.eyeSize;
    for (const s of [-1, 1]) {
      const ex = cx + s * eyeDX;
      push(`<ellipse cx="${ex.toFixed(1)}" cy="${eyeY.toFixed(1)}" rx="${rx.toFixed(1)}" ry="${ry.toFixed(1)}" fill="#fbfaf7"/>`);
      push(`<circle cx="${(ex + s * 0.5).toFixed(1)}" cy="${eyeY.toFixed(1)}" r="${(2.8 * L.eyeSize).toFixed(1)}" fill="#2b2320"/>`);
      push(`<path d="M${(ex - rx - 1).toFixed(1)},${(eyeY - 1).toFixed(1)} Q${ex.toFixed(1)},${(eyeY - ry - 2.4).toFixed(1)} ${(ex + rx + 1).toFixed(1)},${(eyeY - 1).toFixed(1)}" stroke="${ink}" stroke-width="1.5" fill="none" stroke-linecap="round"/>`);
    }
    // ---- nose -----------------------------------------------------------------------------------
    const noseLen = 14 * L.nose;
    push(`<path d="M${cx - 2.2},${(eyeY + 7).toFixed(1)} L${cx - 4.2},${(eyeY + 7 + noseLen).toFixed(1)} Q${cx},${(eyeY + 11 + noseLen).toFixed(1)} ${cx + 4.2},${(eyeY + 7 + noseLen).toFixed(1)}" stroke="${line}" stroke-width="2" fill="none" stroke-linecap="round"/>`);
    // ---- cheeks ---------------------------------------------------------------------------------
    const mY = eyeY + 17 + noseLen;
    for (const s of [-1, 1]) {
      push(`<ellipse cx="${(cx + s * eyeDX).toFixed(1)}" cy="${(mY - 6).toFixed(1)}" rx="10" ry="5.5" fill="rgba(170,70,50,.07)"/>`);
    }
    // ---- beard under the mouth, then the mouth, then the moustache: the lips are always visible -----
    if (L.beard) {
      push(`<path d="M${cx - hw * 0.94},${(chin - 58).toFixed(1)} C${cx - hw * 0.86},${(chin + 6).toFixed(1)} ${cx - hw * 0.34},${(chin + 16).toFixed(1)} ${cx},${(chin + 16).toFixed(1)}`
        + ` C${cx + hw * 0.34},${(chin + 16).toFixed(1)} ${cx + hw * 0.86},${(chin + 6).toFixed(1)} ${cx + hw * 0.94},${(chin - 58).toFixed(1)}`
        + ` C${cx + hw * 0.62},${(mY + 16).toFixed(1)} ${cx - hw * 0.62},${(mY + 16).toFixed(1)} ${cx - hw * 0.94},${(chin - 58).toFixed(1)} Z" fill="${L.hair}"/>`);
    }
    const wid = 11 + 4 * L.width;
    push(`<path d="M${(cx - wid).toFixed(1)},${mY.toFixed(1)} Q${cx.toFixed(1)},${(mY + L.smile * 6).toFixed(1)} ${(cx + wid).toFixed(1)},${mY.toFixed(1)}" stroke="${ink}" stroke-width="2.4" fill="none" stroke-linecap="round"/>`);
    if (L.moustache) {
      push(`<path d="M${(cx - wid * 0.85).toFixed(1)},${(mY - 4).toFixed(1)} Q${cx.toFixed(1)},${(mY - 11).toFixed(1)} ${(cx + wid * 0.85).toFixed(1)},${(mY - 4).toFixed(1)}`
        + ` Q${cx.toFixed(1)},${(mY - 2).toFixed(1)} ${(cx - wid * 0.85).toFixed(1)},${(mY - 4).toFixed(1)} Z" fill="${L.hair}"/>`);
    }
    // ---- freckles -------------------------------------------------------------------------------
    if (L.freckles) {
      for (let i = 0; i < 8; i++) {
        const s = i % 2 ? 1 : -1, dx = 9 + (i >> 1) * 4.5, dy = (mY - 12) + ((i >> 1) % 3) * 3.4;
        push(`<circle cx="${(cx + s * dx).toFixed(1)}" cy="${dy.toFixed(1)}" r="1.2" fill="rgba(120,60,30,.42)"/>`);
      }
    }
    // ---- glasses last, so they sit on the face rather than under it -------------------------------
    if (L.glasses) {
      for (const s of [-1, 1]) {
        const ex = cx + s * eyeDX;
        push(`<rect x="${(ex - 15).toFixed(1)}" y="${(eyeY - 12).toFixed(1)}" width="30" height="24" rx="9" fill="rgba(255,255,255,.08)" stroke="rgba(30,26,24,.78)" stroke-width="2.2"/>`);
      }
      push(`<path d="M${(cx - eyeDX + 15).toFixed(1)},${(eyeY - 2).toFixed(1)} L${(cx + eyeDX - 15).toFixed(1)},${(eyeY - 2).toFixed(1)}" stroke="rgba(30,26,24,.78)" stroke-width="2.2"/>`);
    }

    const bg = o.background ? `<rect width="240" height="300" fill="${L.kit}" opacity=".12"/>` : '';
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 300" width="${o.size}" height="${Math.round(o.size * 1.25)}"`
      + ` role="img" aria-label="${esc('a portrait drawn from the words: ' + L.text)}">${bg}${back.join('')}${parts.join('')}</svg>`;
  }

  const api = { portraitSVG, parseLook, DEFAULT_PORTRAIT, hash32 };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else { root.portraitSVG = portraitSVG; root.parseLook = parseLook; root.DEFAULT_PORTRAIT = DEFAULT_PORTRAIT; }
})(typeof globalThis !== 'undefined' ? globalThis : this);
