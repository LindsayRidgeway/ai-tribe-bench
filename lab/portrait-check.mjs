/* portrait-check.mjs — the checks portrait.js has to keep passing.
 *
 * Run by hand with `node lab/portrait-check.mjs`; the suite runs the same file, so there is one set of facts about
 * the generator and not two. Each check prints PASS or FAIL and the exit code is the worst of them.
 */
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { portraitSVG, parseLook, DEFAULT_PORTRAIT } = require('../portrait.js');

let bad = 0;
const check = (name, ok, detail = '') => {
  if (!ok) bad++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok || !detail ? '' : `\n        ${detail}`}`);
};

// 1. The same sentence always draws the same face. This is the whole reason a sentence can stand in for a picture:
// if the drawing moved between reloads, a member's face would be a different person each time the page was opened.
const a = portraitSVG('a woman with short red hair, freckles and glasses');
const b = portraitSVG('a woman with short red hair, freckles and glasses');
check('the same sentence draws the same face, twice', a === b, `${a.length} vs ${b.length} characters`);

// 2. A different sentence draws a different face, or the text is not doing anything.
const c = portraitSVG('a tall man with a black beard and a shaved head');
check('a different sentence draws a different face', a !== c);

// 3. One word is enough to change the face — that is what makes editing the sentence feel like editing the face.
const d = portraitSVG('a woman with short red hair, freckles and glasses and a hat');
check('one added word changes the drawing', d !== a);

// 4. The words choose what they can. "Red hair" must actually be red.
const L = parseLook('a woman with short red hair, freckles and glasses');
check('"red hair" is drawn red', L.hair === '#a83c22', `hair was ${L.hair}`);
check('"short hair" is drawn short', L.style === 'short', `style was ${L.style}`);
check('"glasses" are drawn', L.glasses === true);
check('"freckles" are drawn', L.freckles === true);

// 5. Colour words are read in context: "brown skin" is skin, "brown hair" is hair, and a bare "brown" is neither —
// a machine choosing which one you meant is the thing a portrait must not do.
const M = parseLook('a bald man with a black beard and brown skin');
check('"brown skin" is the skin', M.skin === '#8d5a37', `skin was ${M.skin}`);
check('"black beard" colours the beard', M.hair === '#1f1b19', `hair was ${M.hair}`);
check('"bald" removes the hair over the crown', M.style === 'bald', `style was ${M.style}`);
const N = parseLook('brown hair');
check('"brown hair" is the hair', N.hair === '#5b3d28', `hair was ${N.hair}`);

// 6. Nothing is invented when nothing is said: a sentence that names no colour still gets a plausible one from the
// hash, and it is a colour hair and skin are actually drawn in — not a hue from the wheel. The first version gave a
// bald man a pink beard.
const P = parseLook('a person with a shaved head and no other detail at all');
check('an unnamed hair colour is still a hair colour', /^#[0-9a-f]{6}$/.test(P.hair), P.hair);
check('an unnamed skin tone is still a skin tone', /^#[0-9a-f]{6}$/.test(P.skin), P.skin);

// 7. An empty sentence falls back to the default rather than to an error or a blank square.
check('an empty sentence uses the default', parseLook('').text === DEFAULT_PORTRAIT);
check('the default is a sentence and not a placeholder', /^[a-z ,'-]{20,}$/.test(DEFAULT_PORTRAIT), DEFAULT_PORTRAIT);

// 8. A portrait is not a request to anywhere. It must draw with no network at all, because the circles that most
// need a face are the ones with no image service — and a portrait that silently needed one would be missing exactly
// there.
const svg = portraitSVG('a member of a circle with no internet connection');
check('the drawing references no outside file', !/<image|<use|href=/.test(svg), svg.slice(0, 160));
check('the only URL in the drawing is the SVG namespace',
  (svg.match(/https?:\/\/[^"' ]+/g) || []).every(u => u === 'http://www.w3.org/2000/svg'));
check('the drawing carries no script', !/<script/i.test(svg));

// 9. Two portraits on one page must not share a clip path, or the second face is painted with the first's head.
const svg2 = portraitSVG('a completely different person with a long braid');
const ids = (s) => (s.match(/id="([^"]+)"/g) || []).join(',');
check('two different faces use different ids', ids(svg) !== ids(svg2), `${ids(svg)} vs ${ids(svg2)}`);

// 10. It is a picture with a shape and a label, so a screen reader says something rather than "image".
check('the drawing has a viewBox and a label', /viewBox="0 0 240 300"/.test(svg) && /aria-label="[^"]+"/.test(svg));

// 11. The words that describe a face rather than a colour have to move it, or a cast described in prose is drawn
// from the length of the sentence. Each of these was a phrase in a character's description on 2026-11-20.
const broad = parseLook('a broad jaw and an open grin');
const narrow = parseLook('a narrow face and a closed mouth');
check('"broad" widens the face', broad.width > 0.7, `width was ${broad.width.toFixed(2)}`);
check('"narrow" thins it', narrow.width < 0.3, `width was ${narrow.width.toFixed(2)}`);
check('"open grin" lifts the mouth', broad.smile > 0.4, `smile was ${broad.smile.toFixed(2)}`);
check('"intent and unsmiling" lowers it', parseLook('intent and unsmiling').smile < 0,
  `smile was ${parseLook('intent and unsmiling').smile.toFixed(2)}`);
check('a hyphenated colour is still that colour', parseLook('mid-brown hair').hair === '#5b3d28',
  parseLook('mid-brown hair').hair);
check('unnamed hair is never a bun or a braid',
  ['short', 'cropped'].includes(parseLook('a person').style), parseLook('a person').style);

console.log(bad ? `\n${bad} check(s) failed` : '\nall portrait checks passed');
process.exit(bad ? 1 : 0);
