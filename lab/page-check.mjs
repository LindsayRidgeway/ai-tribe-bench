/* page-check.mjs — drive the page the way a person's browser does, with no network and no model.

   Why this exists. `ait.html` is the product for everyone who does not use a terminal, and until
   2026-11-12 it had no test at all: every claim about it was a claim about a browser session somebody
   had watched. That is how Gwen's #9 lived — filing a conversation wrote no chapter, and the only way
   to find out was to file one and go looking for the file that was not there.

   What it is. Node, no dependencies: the real `ait.html` is read, its script is evaluated in a fake
   browser (a document that holds text, a localStorage, a `fetch` that answers as GitHub's contents API
   and as one engine would), and the functions themselves are called. Nothing about the page is copied
   into this file; if the page changes, this tests the change.

   Run: node lab/page-check.mjs          (tests.py runs it, so `python3 tests.py` covers it too)
*/
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import crypto from 'node:crypto';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const PAGE = path.join(HERE, '..', 'ait.html');

/* ---- the fake repository ---------------------------------------------------------------- */

const files = new Map();          // path -> {text, sha}
const failWrites = new Set();     // paths whose PUT is refused, to test the failure orders
const clashWrites = new Set();    // paths whose PUT answers 409: somebody else wrote the file since it was read
const calls = [];                 // every request, for the failure messages to be specific
const dispatches = [];            // every workflow_dispatch, with the inputs the page sent it
const actions = { runs: [], onPoll: null, secrets: [], secretsDenied: false, installationsDenied: false,
                  secretPublicKey: null, secretWrites: [], secretWriteDenied: false,
                  // Which account answers `/user`, what `/user/repos` says it owns, and which of those are *not*
                  // circles. A page that can only ever see one repository cannot be asked whether it finds a
                  // circle by searching rather than by being told the name.
                  login: 'someone', userRepos: [], notCircles: [], denyUser: false };
// What GitHub says about the repository itself. `private` is the one field the page reads out of it, and on
// 2026-11-15 it read nothing: an owner could turn a tribe public and the page went on saying nothing while the
// record — every journal, every word said to a member — became readable by anyone. Kept here so a check can
// answer either way, and absent (`undefined`) for the third case, a page that was never told.
const repoMeta = {private: true};
// `secrets` are the NAME cards the repository will admit to holding — never values, which GitHub does not
// return to anyone. `secretsDenied` stands in for a token without admin, which is a real and silent case.

/* Content, not identity: git's blob sha is a hash of the file and of nothing else, so two files with the same text
   have the same sha — in this fake as in a real repository. The page's update compares those shas and treats equality
   as "no change", and a fake that salted them per file would make that comparison untestable. */
function shaOf(text){
  return crypto.createHash('sha1').update(String(text)).digest('hex');
}

/* The template, as a repository the page can read without a token: a head commit, the files at it, and earlier
   commits by sha — which is what makes "did the owner edit this file?" answerable. `sha: null` stands for a template
   that cannot be read at all (private, no network), where the page must say so rather than say "up to date". */
const tpl = {sha: null, files: new Map(), refs: new Map()};
function seedTemplate(p, text, ref){
  if (!ref) tpl.files.set(p, text);
  else {
    if (!tpl.refs.has(ref)) tpl.refs.set(ref, new Map());
    tpl.refs.get(ref).set(p, text);
  }
}
function templateTree(ref){
  if (!ref || ref === tpl.sha || ref === 'head' || ref === 'main') return tpl.files;
  return tpl.refs.get(ref) || null;
}
function seed(p, text){ files.set(p, {text, sha: shaOf(text, files.size)}); }
function listing(prefix){
  const seen = new Map();
  for (const p of files.keys()){
    if (!p.startsWith(prefix ? prefix + '/' : '')) continue;
    const rest = p.slice((prefix ? prefix + '/' : '').length);
    const head = rest.split('/')[0];
    const isFile = !rest.includes('/');
    if (!seen.has(head)) seen.set(head, {name: head, path: p, type: isFile ? 'file' : 'dir',
      sha: isFile ? files.get(p).sha : 'dir', size: isFile ? files.get(p).text.length : 0});
  }
  return [...seen.values()];
}

function jsonResponse(status, data){
  const text = JSON.stringify(data);
  return {ok: status >= 200 && status < 300, status, statusText: String(status), json: async () => data,
          text: async () => text};
}

function githubFetch(url, init = {}){
  const u = new URL(url);
  const p = decodeURIComponent(u.pathname);          // /repos/<owner>/<repo>/contents/<path>
  const method = (init.method || 'GET').toUpperCase();
  calls.push(method + ' ' + p);
  // Actions: a dispatch is accepted and forgotten; the run list is what the page reads back, and its answer is
  // the only thing that decides whether a press of "Wake now" is reported as done.
  if (/^\/repos\/[^/]+\/[^/]+\/actions\/workflows\/[^/]+\/dispatches$/.test(p)){
    // A dispatch answers with nothing but a 204, so the inputs are kept here: a form that fills the wrong
    // field is invisible from the page and from the run's conclusion, and only this can say it happened.
    let inputs = {};
    try { inputs = JSON.parse(init.body || '{}').inputs || {}; } catch(e){ inputs = {}; }
    const wf = decodeURIComponent(p.split('/')[6] || '');
    // Every installed tribe is missing workflows the page knows about, and GitHub answers 404 for a dispatch
    // to a workflow that is not there. The fake can do that too, or the page's honest sentence is untested.
    if (actions.missingWorkflows && actions.missingWorkflows.includes(wf))
      return jsonResponse(404, {message: 'Not Found'});
    dispatches.push({workflow: wf, inputs});
    return jsonResponse(204, {});
  }
  if (/^\/user\/installations$/.test(p)){
    // App-only: a classic token is refused here, in GitHub's own words, and that is the founder's 2026-11-19 wall.
    if (actions.installationsDenied)
      return jsonResponse(403, {message: 'You must authenticate with an access token authorized to a GitHub App in '
        + 'order to list installations'});
    return jsonResponse(200, {total_count: 0, installations: []});
  }
  if (/^\/repos\/[^/]+\/[^/]+\/actions\/secrets\/public-key$/.test(p)){
    // GitHub hands the page a key to seal with, and a sealed box cannot be opened by the key that made it — so the
    // harness can check exactly what a person is promised: what lands in the repository is unreadable as it stands.
    if (!actions.secretPublicKey) return jsonResponse(404, {message: 'Not Found'});
    return jsonResponse(200, {key_id: 'k1', key: actions.secretPublicKey});
  }
  if (/^\/repos\/[^/]+\/[^/]+\/actions\/secrets\/[A-Z0-9_]+$/.test(p)){
    if (actions.secretWriteDenied) return jsonResponse(403, {message: 'Resource not accessible by integration'});
    actions.secretWrites.push({name: p.split('/').pop(), body: JSON.parse(init.body || '{}')});
    return jsonResponse(201, {});
  }
  if (/^\/repos\/[^/]+\/[^/]+\/actions\/secrets$/.test(p)){
    if (actions.secretsDenied) return jsonResponse(403, {message: 'Must have admin rights to Repository.'});
    return jsonResponse(200, {total_count: actions.secrets.length, secrets: actions.secrets.map(n => ({name: n}))});
  }
  if (/^\/repos\/[^/]+\/[^/]+\/actions\/runs$/.test(p)){
    // A run does its work between the dispatch and the poll: the callback stands in for the runner.
    if (actions.onPoll){ const once = actions.onPoll; actions.onPoll = null; once(files); }
    return jsonResponse(200, {workflow_runs: actions.runs.slice()});
  }

  if (/^\/repos\/[^/]+\/[^/]+\/commits\/main$/.test(p)){
    if (!tpl.sha) return jsonResponse(404, {message: 'Not Found'});
    return jsonResponse(200, {sha: tpl.sha, commit: {message: 'the template'}});
  }
  const tm = p.match(/^\/repos\/([^/]+)\/([^/]+)\/git\/trees\/(.+)$/);
  if (tm){
    const tree = tm[2] === 'ai-tribe-template' ? templateTree(decodeURIComponent(tm[3])) : files;
    if (!tree) return jsonResponse(404, {message: 'Not Found'});
    // The tribe's map holds {text, sha}; the template's holds the text. A tree entry is the sha of the content either
    // way, and getting that wrong here would make every comparison in the page's update look like an edit.
    const body = k => { const v = tree.get(k); return typeof v === 'string' ? v : (v || {}).text || ''; };
    return jsonResponse(200, {sha: tpl.sha, tree: [...tree.keys()].map(k =>
      ({path: k, type: 'blob', mode: '100644', sha: shaOf(body(k))}))});
  }

  if (/^\/user$/.test(p)){
    if (actions.denyUser) return jsonResponse(401, {message: 'Bad credentials'});
    return jsonResponse(200, {login: actions.login, name: ''});
  }
  if (/^\/user\/repos$/.test(p)) return jsonResponse(200, actions.userRepos);
  // A per-repository answer, so "one of these is a circle and one is not" is testable: until 2026-11-19 the fake
  // held exactly one repository, which made every name in the world a circle.
  {
    const cir = p.match(/^\/repos\/([^/]+)\/([^/]+)\/contents\/\.tribe-manifest\.json$/);
    if (cir && actions.notCircles.includes(cir[1] + '/' + cir[2])) return jsonResponse(404, {message: 'Not Found'});
  }
  const m = p.match(/^\/repos\/([^/]+)\/([^/]+)(?:\/contents\/?(.*))?$/);
  if (!m) return jsonResponse(404, {message: 'Not Found'});
  const rest = m[3] || '';
  if (!rest){
    const meta = {full_name: m[1] + '/' + m[2], default_branch: 'main'};
    if (repoMeta.private !== undefined) meta.private = repoMeta.private;
    return jsonResponse(200, meta);
  }

  // The template is read by the page and never written by it, so it answers from its own shelf: a read of a template
  // path must never be answered with a tribe file that happens to have the same name.
  if (m[2] === 'ai-tribe-template'){
    const shelf = templateTree(u.searchParams.get('ref')) || new Map();
    if (method === 'GET' && shelf.has(rest))
      return jsonResponse(200, {content: Buffer.from(shelf.get(rest)).toString('base64'),
                                sha: shaOf(shelf.get(rest)), path: rest});
    return jsonResponse(404, {message: 'Not Found'});
  }
  if (method === 'GET'){
    if (files.has(rest)) return jsonResponse(200, {content: Buffer.from(files.get(rest).text).toString('base64'),
                                                  sha: files.get(rest).sha, path: rest});
    const dir = listing(rest);
    if (dir.length) return jsonResponse(200, dir);
    return jsonResponse(404, {message: 'Not Found'});
  }

  if (method === 'PUT'){
    if (failWrites.has(rest)) return jsonResponse(500, {message: 'the repository said no'});
    if (clashWrites.has(rest)) return jsonResponse(409, {message: 'sha does not match'});
    if (actions.busy[rest] > 0){ actions.busy[rest]--; return jsonResponse(409, {message: 'Git Repository is empty.'}); }
    const body = JSON.parse(init.body || '{}');
    const text = Buffer.from(String(body.content || ''), 'base64').toString('utf8');
    const prev = files.get(rest);
    if (body.sha && prev && body.sha !== prev.sha) return jsonResponse(409, {message: 'sha does not match'});
    if (body.sha && !prev) return jsonResponse(409, {message: 'sha does not match'});
    files.set(rest, {text, sha: shaOf(text)});
    return jsonResponse(200, {content: {sha: files.get(rest).sha}});
  }
  return jsonResponse(404, {message: 'Not Found'});
}

function sseResponse(text){
  const parts = String(text).match(/[\s\S]{1,40}/g) || [''];
  const chunks = parts.map(x => `data: ${JSON.stringify({choices: [{delta: {content: x}}]})}\n\n`);
  chunks.push('data: [DONE]\n\n');
  let i = 0;
  return {ok: true, status: 200, statusText: 'OK', json: async () => ({}), text: async () => '',
    body: {getReader: () => ({read: async () => i < chunks.length
      ? {value: new TextEncoder().encode(chunks[i++]), done: false} : {value: undefined, done: true}})}};
}

/* the member's own words, when it is asked to write the journal entry for a filed conversation */
const MEMBER_ENTRY = '## 2026-11-12 19:05 UTC — attended session (the keeper present)\n\n'
  + 'They asked what I made and told me to keep it. The boat is in the manifest; the question is open.\n';

/* ---- the fake browser ------------------------------------------------------------------- */

function el(id){
  const e = {
    id, hidden: false, textContent: '', innerHTML: '', value: '', className: '', checked: false,
    dataset: {}, style: {}, files: [], href: '', download: '', nextSibling: null, parentNode: null,
    classList: {add(){}, remove(){}, toggle(){}, contains(){ return false; }},
    // `insertBefore` and `appendChild` record what was inserted instead of doing nothing: a page that offers a
    // person another control (the sign-in that replaces a wrong token) said nothing in this harness until
    // 2026-11-19, when the element it inserted into had no `insertBefore` at all and the branch crashed the run
    // instead of being asserted. `inserted` is what the checks read.
    inserted: [],
    appendChild(c){ e.inserted.push(c); if (c) c.parentNode = e; return c; },
    insertBefore(c, before){ e.inserted.push(c); if (c) { c.parentNode = e; c.nextSibling = before || null; } return c; },
    removeChild(){}, remove(){}, click(){}, focus(){}, blur(){},
    scrollIntoView(){}, setAttribute(){}, getAttribute(){ return null; }, hasAttribute(){ return false; },
    addEventListener(){}, removeEventListener(){}, showModal(){}, close(){},
    querySelector(){ return null; }, querySelectorAll(){ return []; },
    getBoundingClientRect(){ return {top: 0, left: 0, width: 0, height: 0}; },
  };
  return e;
}

const elements = new Map();
const document = {
  getElementById(id){ if (!elements.has(id)) elements.set(id, el(id)); return elements.get(id); },
  querySelector(){ return null; },
  querySelectorAll(){ return []; },
  createElement(tag){ return el(tag); },
  addEventListener(){},
  body: el('body'),
  documentElement: el('html'),
};

const store = new Map();
const localStorage = {
  getItem: (k) => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: (k) => store.delete(k),
};

const clipboardWrites = [];  // what the page asked the browser to copy
const historyWrites = [];    // every address the page put back into the bar, so a leftover query can be checked
const replaceCalls = [];       // where a page that found itself at the retired address sent the browser
const location = {hash: '', search: '', pathname: '/ait.html', href: 'http://localhost/ait.html',
                  host: 'kythe.app', replace(to){ replaceCalls.push(to); },
                  replaceState(){}, assign(){}};

const sandbox = {
  console, document, localStorage, location, fetch: null, setInterval, clearInterval,
  // The page waits three seconds between polls of the run list. A harness that waited would spend its life asleep,
  // and the wait is not what is being tested — the answer is.
  setTimeout: (fn) => setTimeout(fn, 0), clearTimeout,
  TextEncoder, TextDecoder, URL, URLSearchParams, Blob: class {}, atob, btoa, structuredClone,
  crypto: {randomUUID: () => crypto.randomUUID(),
           // A page that seals a secret needs a real random ephemeral keypair; the fake browser's crypto had only
           // `randomUUID`, so the vendored library refused with 'no PRNG'. That gap was the harness's, not the page's.
           getRandomValues: (u8) => globalThis.crypto.getRandomValues(u8)},
  alert(){}, confirm(){ return true; }, prompt(){ return ''; },
  navigator: {userAgent: 'node', clipboard: {writeText: async (t) => { clipboardWrites.push(t); }}},
  history: {replaceState(_a, _b, to){ if (typeof to === 'string') historyWrites.push(to); }, pushState(){}},
  addEventListener(){}, removeEventListener(){}, matchMedia: () => ({matches: false, addEventListener(){}}),
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
const exchanges = [];           // what the page told the token exchange about itself, one entry per code
sandbox.fetch = async (url, init = {}) => {
  const u = String(url);
  if (u.startsWith('https://api.github.com')) return githubFetch(u, init);
  if (/\/chat\/completions$/.test(u)) return sseResponse(MEMBER_ENTRY);
  // The one server this page has: it turns a code into a token with either the App's pair of credentials or the
  // classic one, and `app` is how it is told which. That flag is the whole of the check below.
  if (/\.netlify\/functions\/auth$/.test(u)){
    try { exchanges.push(JSON.parse(init.body || '{}')); } catch(_){ exchanges.push({unparsable: init.body}); }
    return jsonResponse(200, {access_token: 'gho_test_token'});
  }
  return jsonResponse(404, {message: 'this harness does not answer ' + u});
};

/* ---- run the page ---------------------------------------------------------------------- */

export function loadPage(fresh = false){
  const html = fs.readFileSync(PAGE, 'utf8');
  // Every script block, in order, joined as one program — because a browser runs them in one global scope and this
  // harness should see what the browser sees. The page gained a second block on 2026-11-19 (a vendored sealed-box
  // library, so the page can write an Actions secret without sending a person's key through a server of ours), and
  // a harness that read only the first block would have silently stopped testing the page at all.
  const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
  if (!blocks.length) throw new Error('ait.html has no script — did the page move?');
  const source = blocks.join('\n;\n');
  // `fresh` boots the page a second time as a *new* document would: its own globals, the same browser underneath
  // (storage, document, fetch). Without it the context is the one already running and every top-level `const`
  // collides with itself.
  const context = vm.createContext(fresh ? {...sandbox} : sandbox);
  // A browser's global object answers to `self`, and the vendored sealed-box library asks for it by that name
  // (UMD wrappers do). The fake browser did not have one, which is the fake's gap and not the page's, so it gets
  // one: `self` is the global, as it is in a window.
  vm.runInContext('this.self = this;', context);
  vm.runInContext(source, context, {filename: 'ait.html'});
  return context;
}

const run = (context, code) => vm.runInContext(code, context);
// A check that needs a function the page does not have yet is a check that fails, not a harness that dies with
// a stack trace: "the page has no Ask for a picture" is the finding, and it should be printed like the rest.
const tryRun = async (context, code) => {
  try { return await run(context, code); }
  catch(e){ return {err: 'threw: ' + (e && e.message)}; }
};
const text = (p) => (files.get(p) || {}).text;

/* ---- the checks ------------------------------------------------------------------------ */

const results = [];
function check(name, fn){
  try { const why = fn(); results.push({name, ok: !why, why: why || ''}); }
  catch(e){ results.push({name, ok: false, why: 'threw: ' + (e && e.message)}); }
}

function reset(){
  files.clear(); failWrites.clear(); clashWrites.clear(); calls.length = 0; dispatches.length = 0; store.clear();
  tpl.sha = null; tpl.files.clear(); tpl.refs.clear();
  actions.runs.length = 0; actions.onPoll = null; actions.secrets = []; actions.secretsDenied = false;
  actions.secretPublicKey = null; actions.secretWrites.length = 0; actions.secretWriteDenied = false;
  actions.login = 'someone'; actions.userRepos = []; actions.notCircles = []; actions.denyUser = false;
  exchanges.length = 0; actions.installationsDenied = false;
  actions.missingWorkflows = []; actions.busy = {};
  for (const id of ['mmsg', 'chaptsmsg', 'main']) if (elements.has(id)) elements.delete(id);
}

async function main(){
  const ctx = loadPage();

  /* 1 — filing a conversation keeps the talk itself, in a chapter, before the window is emptied. */
  reset();
  seed('wake/members/Lumi/state/identity.md', '# Lumi');
  seed('wake/members/Lumi/state/journal.md', '# Journal\n');
  seed('wake/members/Lumi/state/state.md', '# State\n\nWakes so far: 3\nLast wake: yesterday\n');
  seed('wake/members/Lumi/state/voice.md', 'api: deepseek\nmodel: deepseek-flash\n');
  for (const f of ['place.md', 'open-items.md', 'memory.md', 'conversation.md']) seed('wake/members/Lumi/state/' + f, '# ' + f + '\n');

  const report = await run(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    S.keys = {deepseek: {key: 'k'}};
    S.owner = 'Sam';
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash', journal: ''}];
    S.chat.Lumi = [
      {role:'user', at:'2026-11-12 19:00 UTC', content:'What did you make today?'},
      {role:'assistant', at:'2026-11-12 19:01 UTC', content:'A paper boat. It floats.'},
      {role:'user', at:'2026-11-12 19:02 UTC', content:'Keep it in your journal.'},
    ];
    await fileConversation('Lumi');
    return {left: (S.chat.Lumi || []).length, said: (document.getElementById('mmsg').textContent || '')};
  })()`);

  const chapters = [...files.keys()].filter(p => /^wake\/members\/Lumi\/state\/talk\/\d{3}-.*\.md$/.test(p));
  const chapter = chapters.length ? text(chapters[0]) : '';
  const thread = text('wake/members/Lumi/state/conversation.md') || '';
  const journal = text('wake/members/Lumi/state/journal.md') || '';

  check('a filed conversation leaves a chapter, not just an entry', () => {
    if (chapters.length !== 1) return `expected one chapter file, found ${chapters.length}`;
    return '';
  });
  check('the chapter holds what was actually said, in order, whole', () => {
    const said = ['What did you make today?', 'A paper boat. It floats.', 'Keep it in your journal.'];
    let at = -1;
    for (const line of said){
      const i = chapter.indexOf(line);
      if (i < 0) return `the chapter is missing: ${line}`;
      if (i < at) return `out of order at: ${line}`;
      at = i;
    }
    return '';
  });
  check('the window is empty afterwards, and the conversation file says so', () => {
    if (report.left !== 0) return `the window still holds ${report.left} turn(s)`;
    if (/paper boat/.test(thread)) return 'the filed turns are still in conversation.md as well as the chapter';
    return '';
  });
  check('the member still writes its own entry into its journal', () => {
    if (!/attended session/.test(journal)) return 'no entry was written to journal.md';
    return '';
  });
  check('the person is told where the talk went', () => {
    if (!/chapter 1/.test(report.said)) return `the message said only: "${report.said}"`;
    return '';
  });

  /* 2 — a failure after the chapter and before the window is cleared costs nothing and duplicates nothing. */
  reset();
  seed('wake/members/Lumi/state/identity.md', '# Lumi');
  seed('wake/members/Lumi/state/journal.md', '# Journal\n');
  seed('wake/members/Lumi/state/state.md', '# State\n\nWakes so far: 3\nLast wake: yesterday\n');
  seed('wake/members/Lumi/state/voice.md', 'api: deepseek\nmodel: deepseek-flash\n');
  seed('wake/members/Lumi/state/conversation.md', '# Conversation — Lumi\n');
  failWrites.add('wake/members/Lumi/state/journal.md');

  const first = await run(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    S.keys = {deepseek: {key: 'k'}};
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash', journal: ''}];
    S.chat.Lumi = [
      {role:'user', at:'2026-11-12 19:00 UTC', content:'What did you make today?'},
      {role:'assistant', at:'2026-11-12 19:01 UTC', content:'A paper boat. It floats.'},
    ];
    await fileConversation('Lumi');
    return {left: (S.chat.Lumi || []).length, said: (document.getElementById('mmsg').innerHTML || '')};
  })()`);

  const chapterPaths = [...files.keys()].filter(p => /^wake\/members\/Lumi\/state\/talk\/\d{3}-.*\.md$/.test(p));
  const chapter1 = chapterPaths.length ? text(chapterPaths[0]) : '';

  check('a refused journal write does not empty the window', () => {
    if (first.left !== 2) return `the window was emptied anyway (${first.left} turn(s) left)`;
    return '';
  });
  check('an error the person can read, rather than a silent loss', () => {
    if (!/repository said no/.test(first.said)) return `the message said: "${first.said}"`;
    return '';
  });
  check('what did land before the failure is kept', () => {
    if (!/paper boat/.test(chapter1)) return 'the chapter does not hold the talk';
    return '';
  });

  await run(ctx, `(async () => {
    S.keys = {deepseek: {key: 'k'}};
    await fileConversation('Lumi');
  })()`);
  failWrites.clear();
  const again = await run(ctx, `(async () => {
    S.keys = {deepseek: {key: 'k'}};
    await fileConversation('Lumi');
    return {left: (S.chat.Lumi || []).length};
  })()`);
  const after = [...files.keys()].filter(p => /^wake\/members\/Lumi\/state\/talk\/\d{3}-.*\.md$/.test(p));
  const whole = after.length ? text(after[0]) : '';

  check('pressing again after the failure appends the entry, not a second copy of the talk', () => {
    const times = (whole.match(/A paper boat\. It floats\./g) || []).length;
    if (times !== 1) return `the talk appears ${times} time(s) in the chapter`;
    if (!/attended session/.test(text('wake/members/Lumi/state/journal.md'))) return 'the entry never landed on the retry';
    return '';
  });
  check('and after the retry the window is empty', () => {
    if (again.left !== 0) return `the window still holds ${again.left} turn(s)`;
    return '';
  });

  /* 3 — "woken." is a claim, and a green run is not a wake.

     Gwen pressed Wake now, the run finished with every step green, and her member wrote nothing: the clock had
     no key for its engine, printed the skip on stderr, and the page said *done*. The run's conclusion is not
     evidence that a member woke — the only evidence a browser can read is the member's own `output/` folder
     before and after. These checks are that folder. */
  const CLOCK = `      - name: Whose turn it is
        env:
          TRIBE_API_KEY_DEEPSEEK: \${{ secrets.TRIBE_API_KEY_DEEPSEEK }}
          TRIBE_API_KEY_GEMINI: \${{ secrets.TRIBE_API_KEY_GEMINI }}
          TRIBE_API_KEY_QWEN: \${{ secrets.TRIBE_API_KEY_QWEN }}
`;

  const seedMember = (engine, model) => {
    seed('wake/members/Lumi/state/identity.md', '# Lumi');
    seed('wake/members/Lumi/state/journal.md', '# Journal\n');
    seed('wake/members/Lumi/state/state.md', '# State\n\nWakes so far: 3\nLast wake: yesterday\n');
    seed('wake/members/Lumi/state/voice.md', `api: ${engine}\nmodel: ${model}\n`);
    for (const f of ['place.md', 'open-items.md', 'memory.md', 'conversation.md'])
      seed('wake/members/Lumi/state/' + f, '# ' + f + '\n');
    seed('wake/members/Lumi/output/raw-earlier.json', '{"earlier": true}');
  };
  const runObject = (id, event, name = 'clock') => ({id, name, event, status: 'completed', conclusion: 'success',
    html_url: `https://github.com/someone/tribe/actions/runs/${id}`, created_at: new Date().toISOString()});

  // 3a — the wake wrote nothing: the page says so, names the run, and names the engine the clock has no key for.
  reset();
  seedMember('openrouter', 'openai/gpt-oss-20b');
  seed('.github/workflows/clock.yml', CLOCK);
  actions.runs.push(runObject(42927174555, 'workflow_dispatch'));
  const wake1 = await run(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.keys = {}; S.owner = 'Sam';
    render = () => {};                    // the repaint is not what these checks are about
    S.members = [{name: 'Lumi', engine: 'openrouter', model: 'openai/gpt-oss-20b'}];
    await wakeNow('Lumi');
    return {html: document.getElementById('mmsg').innerHTML || '', said: document.getElementById('mmsg').textContent || ''};
  })()`);

  check('a wake that wrote nothing is not reported as done', () => {
    if (!/wrote no file this wake/.test(wake1.html)) return `the page said: "${wake1.said || wake1.html}"`;
    if (/done/.test(wake1.said)) return 'the page still says done';
    return '';
  });
  check('and it names the run, so the log is one press away', () => {
    if (!/42927174555/.test(wake1.html)) return `no run number in: "${wake1.html}"`;
    if (!/actions\/runs\/42927174555/.test(wake1.html)) return 'the run number is not a link to the run';
    return '';
  });
  check('and it names the engine the clock has no key for, when the page can prove it', () => {
    if (!/openrouter/.test(wake1.html)) return `the engine is not named in: "${wake1.html}"`;
    if (!/skipped before it was called/.test(wake1.html)) return 'the page does not say the member was skipped';
    return '';
  });

  // 3b — the wake did write: no false alarm, and the message names the file and the run.
  reset();
  seedMember('deepseek', 'deepseek-flash');
  seed('.github/workflows/clock.yml', CLOCK);
  actions.runs.push(runObject(43045320505, 'workflow_dispatch'));
  actions.onPoll = (m) => m.set('wake/members/Lumi/output/raw-2026-11-12T20-41-00Z.json', {text: '{}', sha: 'a-new-one'});
  const wake2 = await run(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.keys = {};
    render = () => {};
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash'}];
    await wakeNow('Lumi');
    return {text: document.getElementById('mmsg').textContent || '', html: document.getElementById('mmsg').innerHTML || ''};
  })()`);

  check('a wake that wrote a file is reported as written, with the file named', () => {
    if (!/raw-2026-11-12T20-41-00Z\.json/.test(wake2.text)) return `the page said: "${wake2.text}"`;
    if (!/43045320505/.test(wake2.text)) return 'the run is not named';
    return '';
  });
  check('and no claim of nothing written', () => {
    if (/wrote no file/.test(wake2.html)) return 'the page warns about a wake that did write';
    return '';
  });

  // 3c — a scheduled clock run in flight is not the run this press started. The clock runs on a timer too, so a
  // run that was already going was being adopted as the answer to the button — and its conclusion, and its
  // silence, reported as this member's.
  reset();
  seedMember('deepseek', 'deepseek-flash');
  seed('.github/workflows/clock.yml', CLOCK);
  actions.runs.push(runObject(41000000000, 'schedule'));          // newest first is how GitHub answers;
  actions.runs.push(runObject(43099999999, 'workflow_dispatch')); // the schedule is listed first on purpose
  const wake3 = await run(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.keys = {};
    render = () => {};
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash'}];
    await wakeNow('Lumi');
    return {html: document.getElementById('mmsg').innerHTML || '', text: document.getElementById('mmsg').textContent || ''};
  })()`);

  check('a scheduled run is not adopted as the run the button started', () => {
    if (/41000000000/.test(wake3.html)) return 'the page reported the scheduled run, not the dispatched one';
    if (!/43099999999/.test(wake3.html)) return `the dispatched run is not named in: "${wake3.html}"`;
    return '';
  });

  /* 4 — the person's seat: three numbers typed, one point played, and the member's engine the only model
     call in it. The form is the whole of the person's input, so the two ways it can lie are a movement the
     engine would clamp rather than play, and a green run with no point in the record at that press. */
  const POINT = `# a point on the person's seat — 2026-11-12T21:30:00Z

- **the person**: Sam, playing a movement they typed: \`FACE +6 POWER 62 AIM 12\`.
- **the member**: Lumi, whose own engine chooses its shots (deepseek / deepseek-flash).

## the point

   1.1  Sam      face +6 power  62 aim 12 [clean ] -> IN, 21ft past the net, 1ft west of centre
       the hands gave face +8.1, not +6
`;

  reset();
  seedMember('deepseek', 'deepseek-flash');
  seed('games/tennis/seasons/2026-spring/practice.json', '{}');
  actions.runs.push(runObject(43111111111, 'workflow_dispatch', 'season'));
  actions.onPoll = (m) => m.set('games/tennis/seasons/2026-spring/points/2026-11-12T21-30-00Z.md',
                                {text: POINT, sha: 'point-one'});
  const seat = await run(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Sam';
    render = () => {};
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash'}];
    const set = (id, v) => { document.getElementById(id).value = v; };
    set('yface', '6'); set('ypower', '62'); set('yaim', '12'); set('ypoints', '1');
    set('yname', 'Sam'); set('yvs', 'Lumi'); set('ysurface', 'auto'); set('yseason', '2026-spring');
    await playPoint();
    return {said: document.getElementById('ymsg').textContent || '',
            html: document.getElementById('yresult').innerHTML || ''};
  })()`);

  check('the typed movement is what the form sends, field by field', () => {
    const d = dispatches[dispatches.length - 1];
    if (!d) return 'the press dispatched nothing';
    if (d.workflow !== 'season.yml') return `it dispatched ${d.workflow}`;
    const want = {shot: 'FACE 6 POWER 62 AIM 12', person: 'Sam', players: 'Lumi', season: '2026-spring',
                  rallies: '1'};
    for (const [k, v] of Object.entries(want)){
      if (String(d.inputs[k] ?? '') !== v) return `${k} was ${JSON.stringify(d.inputs[k])}, not ${v}`;
    }
    return '';
  });
  check('and the point the run wrote is shown, in the run\'s own words', () => {
    if (!/21ft past the net/.test(seat.html)) return `the page showed: "${seat.html.slice(0, 200)}"`;
    if (!/the hands gave face \+8\.1/.test(seat.html))
      return 'the delivered angle is missing — the person cannot learn from their own shot';
    if (!/2026-11-12T21-30-00Z\.md/.test(seat.said)) return `the file is not named: "${seat.said}"`;
    return '';
  });

  // 4b — a green run that wrote no point. The same rule as the wake button: the conclusion is not the evidence.
  reset();
  seedMember('deepseek', 'deepseek-flash');
  seed('games/tennis/seasons/2026-spring/practice.json', '{}');
  actions.runs.push(runObject(43222222222, 'workflow_dispatch', 'season'));
  const seat2 = await run(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    render = () => {};
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash'}];
    const set = (id, v) => { document.getElementById(id).value = v; };
    set('yface', '6'); set('ypower', '62'); set('yaim', '12'); set('ypoints', '1');
    set('yname', 'Sam'); set('yvs', 'Lumi'); set('ysurface', 'auto'); set('yseason', '2026-spring');
    await playPoint();
    return {said: document.getElementById('ymsg').textContent || '',
            html: document.getElementById('yresult').innerHTML || ''};
  })()`);

  check('a run that wrote no point is not reported as a point played', () => {
    if (!/wrote no point file/.test(seat2.html)) return `the page said: "${seat2.html || seat2.said}"`;
    if (!/43222222222/.test(seat2.html)) return 'the run is not named, so the log is not one press away';
    return '';
  });
  check('and the folder a point would have appeared in is named', () => {
    if (!/games\/tennis\/seasons\/2026-spring\/points/.test(seat2.html))
      return `the page does not say where a point would have been: "${seat2.html}"`;
    return '';
  });

  // 4c — a movement outside the engine's range is refused before the press, and says the range.
  reset();
  seedMember('deepseek', 'deepseek-flash');
  const seat3 = await run(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    render = () => {};
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash'}];
    const set = (id, v) => { document.getElementById(id).value = v; };
    set('yface', '60'); set('ypower', '62'); set('yaim', '12'); set('ypoints', '1');
    set('yname', 'Sam'); set('yvs', 'Lumi'); set('ysurface', 'auto'); set('yseason', '2026-spring');
    await playPoint();
    return {html: document.getElementById('ymsg').innerHTML || ''};
  })()`);

  check('a shot the engine would clamp is refused before it is sent, naming the range', () => {
    if (dispatches.length) return `it was sent anyway (${dispatches.length} dispatch(es))`;
    if (!/face between -20 and 40/.test(seat3.html)) return `the message said: "${seat3.html}"`;
    return '';
  });

  /* 3 — a member's talk shows the talk with that member, and says what it is holding back. */
  reset();
  seed('wake/members/Hermes/state/identity.md', '# Hermes');
  seed('wake/members/Hermes/state/journal.md', '# Journal\n');
  seed('wake/members/Hermes/state/state.md', '# State\n\nWakes so far: 1\nLast wake: yesterday\n');
  seed('wake/members/Hermes/state/voice.md', 'api: deepseek\nmodel: deepseek-flash\n');
  for (const f of ['place.md', 'open-items.md', 'memory.md']) seed('wake/members/Hermes/state/' + f, '# ' + f + '\n');
  seed('wake/members/Hermes/state/conversation.md', [
    '# Conversation — Hermes',
    '',
    '## 2026-11-12 22:30 UTC — Lindsay',
    '',
    'a private question',
    '',
    '## 2026-11-12 22:31 UTC — Hermes',
    '',
    'a private answer',
    '',
    '## 2026-11-12 22:34 UTC — Dionysus [urgency 3, in "the-trojan-war"]',
    '',
    'a joke said in the room',
    '',
    '## 2026-11-12 22:34 UTC — Lindsay [in "the-trojan-war"]',
    '',
    'what the person said in the room',
    '',
    '## 2026-11-12 22:40 UTC — Lindsay',
    '',
    'and a private question afterwards',
    '',
  ].join('\n'));

  const view = await run(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    S.owner = 'Lindsay Ridgeway';
    S.members = ['Hermes', 'Dionysus', 'Aphrodite'].map(name => ({name, engine: 'deepseek', model: 'deepseek-flash'}));
    S.chat = {};
    await loadThread('Hermes');
    return {turns: S.chat.Hermes.length, shown: chatHTML('Hermes'), note: roomNoteHTML('Hermes'),
            thread: threadFor(S.chat.Hermes, 100000, 'Hermes')};
  })()`).catch(e => ({error: e.message}));

  check('a private talk is what it shows, and a room turn is not', () => {
    if (view.error) return 'the page could not be asked why: ' + view.error;
    if (!/a private answer/.test(view.shown)) return 'the private turns are missing from the talk';
    if (/a joke said in the room/.test(view.shown)) return "another member's sentence is still in the private talk";
    if (/what the person said in the room/.test(view.shown)) return "the person's own room turn is still in the private talk";
    return '';
  });
  check('the turns it did not show are still in its memory', () => {
    if (view.error) return 'the page could not be asked: ' + view.error;
    if (view.turns !== 5) return `the file was read as ${view.turns} turns instead of 5 — the room turns were dropped, not hidden`;
    return '';
  });
  check('and the page says how many, and which room, so the person can ask about it', () => {
    if (view.error) return 'the page could not be asked: ' + view.error;
    if (!/2 turns from .the trojan war./.test(view.note)) return `the note says: ${view.note}`;
    return '';
  });
  check('filtering does not renumber the bubbles a reply streams into', () => {
    if (view.error) return 'the page could not be asked: ' + view.error;
    // the fifth turn is the private one after the room; the reply to it is written at index 4
    if (!/data-i="4"/.test(view.shown)) return 'the turn after the room lost its own index — a reply would stream into the wrong bubble';
    if (/data-i="2"|data-i="3"/.test(view.shown)) return 'a hidden turn left its index behind on a visible bubble';
    if (!/and a private question afterwards/.test(view.shown)) return 'the private turn after the room is missing';
    return '';
  });

  check("another member's sentence is not handed to it as its own", () => {
    if (view.error) return 'the page could not be asked: ' + view.error;
    if (/You: a joke said in the room/.test(view.thread)) return "a room turn is in the prompt as the member's own words";
    if (!/Dionysus \(in "the-trojan-war"\): a joke said in the room/.test(view.thread)) return 'the room turn is not attributed in the prompt: ' + view.thread.slice(0, 300);
    if (!/You: a private answer/.test(view.thread)) return 'the member\'s own turn lost its "You:"';
    if (!/Lindsay: a private question/.test(view.thread)) return 'the person is not named by personLabel() in the prompt';
    return '';
  });

  /* 4 — the room's own file does not claim to be a room, and a member's file does. */
  reset();
  seed('wake/members/Hermes/state/identity.md', '# Hermes');
  seed('wake/members/Hermes/state/journal.md', '# Journal\n');
  seed('wake/members/Hermes/state/state.md', '# State\n\nWakes so far: 1\nLast wake: yesterday\n');
  seed('wake/members/Hermes/state/voice.md', 'api: deepseek\nmodel: deepseek-flash\n');
  for (const f of ['place.md', 'open-items.md', 'memory.md']) seed('wake/members/Hermes/state/' + f, '# ' + f + '\n');
  seed('wake/members/Hermes/state/conversation.md', '# Conversation — Hermes\n');
  seed('chats/the-trojan-war/talk.md', '# Talk — the trojan war\n');

  const written = await run(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    S.owner = 'Lindsay Ridgeway';
    S.members = [{name: 'Hermes', engine: 'deepseek', model: 'deepseek-flash'}];
    S.chat = {};
    CHAT.topic = 'The Trojan War'; CHAT.total = 0;
    const turns = [
      {role:'user', who:'Lindsay', at:'2026-11-12 22:34 UTC', content:'gentlemen, what is a hero?'},
      {role:'assistant', who:'Hermes', at:'2026-11-12 22:34 UTC', content:'a man who is remembered', mark:'urgency 4'},
    ];
    await chatPersist('the-trojan-war', turns, {Hermes: turns});
    return {shown: chatHTML('Hermes'), note: roomNoteHTML('Hermes'), turns: S.chat.Hermes.length};
  })()`).catch(e => ({error: e.message}));

  const roomFile = text('chats/the-trojan-war/talk.md') || '';
  const memberFile = text('wake/members/Hermes/state/conversation.md') || '';

  check("a member's memory of a room says which room it was", () => {
    if (!/in "the-trojan-war"/.test(memberFile)) return 'the member file has no room mark, so the page cannot tell them apart next time';
    return '';
  });
  check('the room itself is not marked as being in a room', () => {
    if (/in "the-trojan-war"/.test(roomFile)) return "the room's own file says it is in the room";
    if (!/urgency 4/.test(roomFile)) return "the room's file lost the member's urgency claim";
    return '';
  });
  check('after a room, the private talk is still a private talk', () => {
    if (written.error) return 'the page could not be asked: ' + written.error;
    if (written.turns !== 2) return `the member kept ${written.turns} turns instead of 2`;
    if (/a man who is remembered/.test(written.shown)) return 'the room turn is showing in the private talk';
    if (!/2 turns from .the trojan war./.test(written.note)) return `the note says: ${written.note}`;
    return '';
  });
  check('and reading the file back finds the room mark again', () => {
    if (written.error) return 'the page could not be asked: ' + written.error;
    return /in "the-trojan-war"/.test(memberFile) && /not shown here/.test(written.note) ? '' : 'the mark did not survive the round trip';
  });

  /* 5 — a file written before the mark existed is read against the rooms' own records. */
  reset();
  seed('wake/members/Hermes/state/identity.md', '# Hermes');
  seed('wake/members/Hermes/state/journal.md', '# Journal\n');
  seed('wake/members/Hermes/state/state.md', '# State\n\nWakes so far: 1\nLast wake: yesterday\n');
  seed('wake/members/Hermes/state/voice.md', 'api: deepseek\nmodel: deepseek-flash\n');
  for (const f of ['place.md', 'open-items.md', 'memory.md']) seed('wake/members/Hermes/state/' + f, '# ' + f + '\n');
  // what the founder's Aphrodite looked like on 2026-11-12: the room's turns with no mark of their own
  seed('wake/members/Hermes/state/conversation.md', [
    '# Conversation — Hermes', '',
    '## 2026-11-12 22:30 UTC — Lindsay', '', 'a private question', '',
    '## 2026-11-12 22:31 UTC — Hermes', '', 'a private answer', '',
    '## 2026-11-12 22:34 UTC — Lindsay', '', 'what he asked in the room', '',
    '## 2026-11-12 22:34 UTC — Hermes', '', 'what it answered in the room', '',
    '## 2026-11-12 22:34 UTC — Dionysus', '', 'what somebody else said in the room', '',
  ].join('\n'));
  seed('chats/the-trojan-war/chat.md', '# A chat — The Trojan War\n\nMembers: Hermes, Dionysus\nFloor: claim\n');
  seed('chats/the-trojan-war/talk.md', [
    '# Talk — the trojan war', '',
    '## 2026-11-12 22:34 UTC — Lindsay', '', 'what he asked in the room', '',
    '## 2026-11-12 22:34 UTC — Hermes', '', 'what it answered in the room', '',
    '## 2026-11-12 22:34 UTC — Dionysus [urgency 3]', '', 'what somebody else said in the room', '',
  ].join('\n'));

  const old = await run(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    S.owner = 'Lindsay Ridgeway';
    S.members = ['Hermes', 'Dionysus', 'Aphrodite'].map(name => ({name, engine: 'deepseek', model: 'deepseek-flash'}));
    S.chat = {}; S.chatRoomMatch = {}; roomTurnKeys.cache = null;
    await loadThread('Hermes');
    return {turns: S.chat.Hermes.length, shown: chatHTML('Hermes'), note: roomNoteHTML('Hermes')};
  })()`).catch(e => ({error: e.message}));

  check('an older file is read against the room that wrote it', () => {
    if (old.error) return 'the page could not be asked: ' + old.error;
    if (/what he asked in the room/.test(old.shown)) return "the person's own room question is in the private talk";
    if (/what it answered in the room/.test(old.shown)) return "the member's own room answer is in the private talk";
    if (/what somebody else said in the room/.test(old.shown)) return "another member's room turn is in the private talk";
    if (!/a private answer/.test(old.shown)) return 'the private talk was emptied along with the room';
    return '';
  });
  check('and it says where those turns were found, not just that they are missing', () => {
    if (!/3 turns from .the trojan war./.test(old.note)) return `the note says: ${old.note}`;
    if (!/found in the rooms. own records/.test(old.note)) return 'the note does not say how they were identified';
    return '';
  });

  /* 5 — pictures, §8: an engine that can paint, a picture committed with its credit line and the sentence it
     was asked with, and a plain refusal in front of the eight engines that cannot. The page cannot paint (the
     commit needs the runner's credential), so what it owes the person is the right ask, a refusal that names
     what would have worked, and a picture that is only called a picture when a file says so. */

  const CARD = 'Painted by gemini (gemini-3.1-flash-image) for Lumi, 2026-11-13 17:00 UTC — the harness made '
    + 'the call; a wake has no tools and cannot.\nThe sentence it was asked with: a watercolour of the harbour '
    + 'at night, one lamp, no lettering\n';

  reset();
  seedMember('gemini', 'gemini-3.8-flash');
  actions.runs.push(runObject(43500000001, 'workflow_dispatch', 'paint'));
  actions.onPoll = (m) => {
    m.set('plates/20261113T170000Z.png', {text: 'not really a png', sha: 'plate-image'});
    m.set('plates/20261113T170000Z.md', {text: CARD, sha: 'plate-card'});
  };
  const pic1 = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Sam';
    render = () => {};
    S.members = [{name: 'Lumi', engine: 'gemini', model: 'gemini-3.8-flash'}];
    document.getElementById('paintwork').value = '';
    document.getElementById('paintprompt').value = 'a watercolour of the harbour at night, one lamp, no lettering';
    await askForPicture('Lumi');
    return {said: document.getElementById('paintmsg').textContent || '',
            html: document.getElementById('paintresult').innerHTML || ''};
  })()`);

  check('the sentence typed is what the form sends, to the engine the member\'s voice names', () => {
    if (pic1.err) return pic1.err;
    const d = dispatches[dispatches.length - 1];
    if (!d) return 'the press dispatched nothing';
    if (d.workflow !== 'paint.yml') return `it dispatched ${d.workflow}`;
    if (String(d.inputs.member) !== 'Lumi') return `member was ${JSON.stringify(d.inputs.member)}`;
    if (String(d.inputs.prompt) !== 'a watercolour of the harbour at night, one lamp, no lettering')
      return `prompt was ${JSON.stringify(d.inputs.prompt)}`;
    if (String(d.inputs.work ?? '') !== '') return `work was ${JSON.stringify(d.inputs.work)}`;
    return '';
  });
  check('and the picture is shown with the credit line that names the machine', () => {
    if (pic1.err) return pic1.err;
    if (!/plates\/20261113T170000Z\.png/.test(pic1.said)) return `the file is not named: "${pic1.said}"`;
    if (!/Painted by gemini/.test(pic1.html)) return `the credit is not on the page: "${pic1.html.slice(0, 240)}"`;
    if (!/gemini-3\.1-flash-image/.test(pic1.html)) return 'the card does not name the model that drew';
    return '';
  });

  // 5a — the press that cannot work at all, because the workflow was never in the repository. Measured by Gwen
  // on 2026-11-13: all five test tribes returned `404 · Not Found` for paint.yml, which reads as "the page is
  // broken" when the truth is "the repository is older than this page" — the strongest form of the 422 the page
  // already translated. Both are one sentence now, and this is the case that was missed.
  // The function is called directly rather than through the card: what is under test is `dispatch()`'s
  // translation, and the card needs a rendered member view that has nothing to do with the sentence.
  reset();
  actions.missingWorkflows = ['paint.yml'];
  const d404 = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    try {
      await dispatch('paint.yml', {member: 'Lumi', prompt: 'a watercolour of the harbour', work: ''});
      return {said: '', threw: false};
    } catch(e){ return {said: e.message || '', threw: true}; }
  })()`);
  check('a press on a tribe whose repository has no such workflow says the repository is older, not 404', () => {
    if (d404.err) return d404.err;
    if (!d404.threw) return 'the dispatch was reported as accepted';
    if (/\b404\b/.test(d404.said)) return `the person is shown GitHub's word: "${d404.said}"`;
    if (!/paint\.yml/.test(d404.said)) return `the workflow is not named: "${d404.said}"`;
    if (!/installed before this button existed/.test(d404.said)) return `it does not say why: "${d404.said}"`;
    if (!/lab\/update_tribe\.py/.test(d404.said)) return `it does not say what to do: "${d404.said}"`;
    return '';
  });
  actions.missingWorkflows = [];

  // 5b — the sentence a private tribe was missing. Gwen's #22 as she corrected it herself: the degradation is
  // designed and stated in the code (a private repository's raw URL needs the token, so the picture is a link),
  // and the *silence* around it is the defect — on a private tribe, which is every tribe this product recommends,
  // a person concludes the page cannot show pictures at all. She reached that conclusion with the network log open.
  const picturePanel = async (priv) => {
    reset();
    seedMember('gemini', 'gemini-3.8-flash');
    return tryRun(ctx, `(async () => {
      S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.isPrivate = ${priv === null ? 'null' : priv};
      S.members = [{name: 'Lumi', engine: 'gemini', model: 'gemini-3.8-flash'}];
      await showPictures('Lumi');
      return {panel: (document.getElementById('pictures').innerHTML || '')};
    })()`);
  };

  const panelPrivate = await picturePanel(true);
  check('a private tribe says why its picture opens in the repository instead of on the page', () => {
    if (panelPrivate.err) return panelPrivate.err;
    if (!/private/i.test(panelPrivate.panel)) return 'the panel does not mention that the tribe is private';
    if (!/opens in the repository/i.test(panelPrivate.panel)) return 'it does not say where the picture goes';
    if (!/does not keep a copy/i.test(panelPrivate.panel)) return 'it does not say why the page does not render it';
    return '';
  });

  const panelPublic = await picturePanel(false);
  check('and a public tribe is not told a picture it will see plainly is somewhere else', () => {
    if (panelPublic.err) return panelPublic.err;
    if (/opens in the repository/i.test(panelPublic.panel)) return 'the private-tribe sentence appears on a public tribe';
    return '';
  });

  const panelUnknown = await picturePanel(null);
  check('and a page that was never told the visibility does not guess', () => {
    if (panelUnknown.err) return panelUnknown.err;
    if (/opens in the repository/i.test(panelUnknown.panel)) return 'the sentence appears without an answer from GitHub';
    return '';
  });

  // 5b — a green run that committed no picture. Same rule as the wake and the point: the conclusion is not the
  // evidence, and a picture nobody wrote is the easiest thing in the world to report as done.
  reset();
  seedMember('gemini', 'gemini-3.8-flash');
  actions.runs.push(runObject(43500000002, 'workflow_dispatch', 'paint'));
  const pic2 = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    render = () => {};
    S.members = [{name: 'Lumi', engine: 'gemini', model: 'gemini-3.8-flash'}];
    document.getElementById('paintwork').value = '';
    document.getElementById('paintprompt').value = 'a red cube';
    await askForPicture('Lumi');
    return {html: document.getElementById('paintresult').innerHTML || ''};
  })()`);

  check('a run that committed no picture is not reported as one', () => {
    if (pic2.err) return pic2.err;
    if (!/committed no picture/.test(pic2.html)) return `the page said: "${pic2.html}"`;
    if (!/43500000002/.test(pic2.html)) return 'the run is not named, so the log is not one press away';
    if (!/plates\//.test(pic2.html)) return 'the folder a picture would have appeared in is not named';
    return '';
  });

  // 5c — a member whose engine has no image model. Refused before anything is dispatched, in a sentence that
  // names the three that can: "no" without an address is the answer this project stopped accepting.
  reset();
  seedMember('deepseek', 'deepseek-flash');
  const pic3 = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    render = () => {};
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash'}];
    document.getElementById('paintprompt').value = 'a red cube';
    await askForPicture('Lumi');
    return {html: document.getElementById('paintmsg').innerHTML || ''};
  })()`);

  check('an engine with no image model is refused before anything is sent', () => {
    if (pic3.err) return pic3.err;
    if (dispatches.length) return `it was sent anyway (${dispatches.length} dispatch(es))`;
    if (!/no image model/.test(pic3.html)) return `the page said: "${pic3.html}"`;
    for (const can of ['OpenAI', 'Gemini', 'Qwen'])
      if (!pic3.html.includes(can)) return `the refusal does not name ${can}, which would have worked`;
    if (!/Nothing was sent/.test(pic3.html)) return 'the refusal does not say that nothing was sent';
    return '';
  });

  // 5d — a picture for a piece on the shelf: the sentence is the piece's own commission line, read from the
  // file and shown, not typed a second time. Two copies of one ask can disagree, and only one of them is the
  // one the member wrote.
  reset();
  seedMember('gemini', 'gemini-3.8-flash');
  seed('works/Lumi/20261101T090000Z-harbour.md',
    '---\ntitle: The Harbour\ncommission: a watercolour of the harbour at night, one lamp, no lettering\n---\n\n'
    + 'the harbour, written\n');
  actions.runs.push(runObject(43500000003, 'workflow_dispatch', 'paint'));
  actions.onPoll = (m) => {
    m.set('plates/20261101T090000Z-harbour.png', {text: 'not really a png', sha: 'plate-image-2'});
    m.set('plates/20261101T090000Z-harbour.md', {text: CARD, sha: 'plate-card-2'});
  };
  const pic4 = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    render = () => {};
    S.members = [{name: 'Lumi', engine: 'gemini', model: 'gemini-3.8-flash'}];
    await showPictures('Lumi');
    const sel = document.getElementById('paintwork');
    sel.value = '20261101T090000Z-harbour';
    await sel.onchange();
    const shown = document.getElementById('paintprompt').value;
    await askForPicture('Lumi');
    return {shown, said: document.getElementById('paintmsg').textContent || '',
            html: document.getElementById('paintresult').innerHTML || ''};
  })()`);

  check('a piece\'s commission line is the sentence, read from the piece itself', () => {
    if (pic4.err) return pic4.err;
    if (!/a watercolour of the harbour at night/.test(pic4.shown)) return `the box held: "${pic4.shown}"`;
    const d = dispatches[dispatches.length - 1];
    if (!d) return 'the press dispatched nothing';
    if (String(d.inputs.work) !== '20261101T090000Z-harbour') return `work was ${JSON.stringify(d.inputs.work)}`;
    if (String(d.inputs.prompt ?? '') !== '') return 'the sentence was sent a second time, so two copies can disagree';
    if (!/plates\/20261101T090000Z-harbour\.png/.test(pic4.said)) return `the plate is not named: "${pic4.said}"`;
    return '';
  });

  // 5e — a piece that asked for no picture. The page must not press: the workflow would refuse, and a person
  // who pressed and read "that piece carries no commission line" has been told after asking, not before.
  reset();
  seedMember('gemini', 'gemini-3.8-flash');
  seed('works/Lumi/20261102T090000Z-quiet.md', '---\ntitle: Quiet\n---\n\nno picture asked for\n');
  const pic5 = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    render = () => {};
    S.members = [{name: 'Lumi', engine: 'gemini', model: 'gemini-3.8-flash'}];
    await showPictures('Lumi');
    const sel = document.getElementById('paintwork');
    sel.value = '20261102T090000Z-quiet';
    await sel.onchange();
    return {html: document.getElementById('paintmsg').innerHTML || '',
            shut: !!document.getElementById('paintbtn').disabled};
  })()`);

  check('a piece with no commission line is refused before the press, and the button shuts', () => {
    if (pic5.err) return pic5.err;
    if (!pic5.shut) return 'the button is still pressable';
    if (!/no <code>commission:<\/code> line|carries no/.test(pic5.html)) return `the page said: "${pic5.html}"`;
    return '';
  });

  // 5f — the page holds a copy of who can paint, and a copy is a thing that drifts. This check is the only
  // reason the copy is allowed to exist: it reads `lab/paint.py` and fails when the two tables disagree, so a
  // fourth engine (or a painter that loses its image model) cannot leave the page offering a button that
  // cannot work, or refusing a member who could have painted.
  check('the page\'s table of painters is lab/paint.py\'s table, not a memory of it', () => {
    const py = fs.readFileSync(path.join(HERE, '..', 'lab', 'paint.py'), 'utf8');
    const block = (py.match(/PAINTERS = \{([\s\S]*?)\n\}/) || [])[1] || '';
    const there = new Set([...block.matchAll(/^\s*"([a-z0-9]+)"\s*:/gm)].map(m => m[1]));
    const here = new Set(Object.keys(run(ctx, 'PAINTERS')));
    if (!there.size) return 'paint.py\'s PAINTERS table could not be read — the check has gone blind';
    for (const e of there) if (!here.has(e)) return `paint.py paints with ${e} and the page does not offer it`;
    for (const e of here) if (!there.has(e)) return `the page offers ${e}, which paint.py cannot paint with`;
    // The extension too: the page names the file before the runner writes it, and Gemini answers a jpeg.
    const mine = run(ctx, 'PAINTERS');
    for (const m of block.matchAll(/"([a-z0-9]+)"\s*:\s*\{[^}]*"ext"\s*:\s*"(\.[a-z]+)"/g)){
      const [_, engine, ext] = m;
      if (mine[engine].ext !== ext)
        return `paint.py files ${engine} as ${ext} and the page says ${mine[engine].ext}`;
    }
    const noBlock = (py.match(/NO_PAINTER = \(([\s\S]*?)\n\)/) || [])[1] || '';
    const cannot = [...noBlock.matchAll(/"([a-z0-9]+)"/g)].map(m => m[1]);
    if (cannot.length !== 8) return `paint.py refuses ${cannot.length} engines; the manual says eight`;
    for (const e of cannot) if (here.has(e)) return `${e} is refused and offered at once`;
    return '';
  });

  /* 6 — the magazine, §9: one press assembles the open issue from the shelf and commits it. Two things the
     page used to do are tested against here. It assembled a magazine of its own (twelve files, newest first,
     no letter under the piece it answers) — the check for that is that the page fetches no work at all: the
     order is `magazine.py`'s, and a second copy of it is a second magazine. And it committed nothing, so the
     issue a person read was a tab. What it owes now is the file the run wrote, named, and an honest difference
     between "published" and "the shelf had not moved". */

  const ISSUE = '# The Workshop — issue 1 — workshop\n\n'
    + "*2 pieces, assembled from `works/` on 2026-11-13 by `magazine.py`. The pieces are the members'; the "
    + 'order is not.*\n\n## Contents\n\n- **The Harbour** — LUMI, piece, 21 words\n\n---\n\n'
    + '## The Harbour\n\n*LUMI — piece, 21 words*\n\nthe harbour, written\n\n'
    + '![The Harbour](../plates/harbour.jpg)\n\n*Plate: asked for by LUMI, made by a human.*\n';
  const seedShelf = () => seed('works/Lumi/20261113T090000Z-harbour.md',
    '---\ntitle: The Harbour\nform: piece\nissue: 1\n---\n\nthe harbour, written\n');

  reset();
  seedMember('deepseek', 'deepseek-flash');
  seedShelf();
  actions.runs.push(runObject(43600000001, 'workflow_dispatch', 'magazine'));
  actions.onPoll = (m) => {
    m.set('issues/01.md', {text: ISSUE, sha: 'issue-1'});
    m.set('issues/README.md', {text: '# The magazine\n', sha: 'index-1'});
  };
  const mag1 = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Sam';
    render = () => {};
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash'}];
    await viewMagazine(document.getElementById('main'));
    await buildIssue();
    return {said: document.getElementById('issuemsg').textContent || '',
            html: document.getElementById('issue').innerHTML || '',
            list: document.getElementById('issuelist').innerHTML || ''};
  })()`);

  check('the press sends the open issue to the assembler, not a shape of its own', () => {
    if (mag1.err) return mag1.err;
    const d = dispatches[dispatches.length - 1];
    if (!d) return 'the press dispatched nothing';
    if (d.workflow !== 'magazine.yml') return `it dispatched ${d.workflow}`;
    if (String(d.inputs.issue ?? '') !== '')
      return `the page chose issue ${JSON.stringify(d.inputs.issue)}; the open issue is the shelf's to say`;
    return '';
  });
  check('and the page assembles nothing itself — it reads no work', () => {
    if (mag1.err) return mag1.err;
    const read = calls.filter(c => /contents\/works\/[^/]+\/.*\.md$/.test(c));
    if (read.length) return `the page fetched a work to print it: ${read[0]}`;
    return '';
  });
  check('the issue on the page is the file the run committed, named', () => {
    if (mag1.err) return mag1.err;
    if (!/issues\/01\.md is in the record/.test(mag1.said)) return `the page said: "${mag1.said}"`;
    if (!/issues\/01\.md/.test(mag1.html)) return 'the file is not named beside the issue';
    if (!/the harbour, written/.test(mag1.html)) return 'the issue itself is not on the page';
    if (!/43600000001/.test(mag1.html)) return 'the run is not named, so its log is not one press away';
    if (!/01/.test(mag1.list)) return 'the new issue is not in the list of issues';
    return '';
  });
  // 6b — the picture the issue prints. `magazine.py` writes a plate from the issue's own folder
  // (`../plates/x.jpg`), which is right on GitHub and meaningless to a page; an issue that renders its
  // pictures as bracket text is not the magazine §9 promises to put in your hands.
  check('a plate in an issue is a picture on the page, resolved against the repository', () => {
    if (mag1.err) return mag1.err;
    if (!/src="https:\/\/github\.com\/someone\/tribe\/raw\/main\/plates\/harbour\.jpg"/.test(mag1.html))
      return `the plate was not resolved: ${(mag1.html.match(/!\[[^\]]*\]\([^)]*\)/) || ['missing'])[0]}`;
    if (!/alt="The Harbour"/.test(mag1.html)) return 'the picture lost its alt text';
    return '';
  });

  // 6c — a green run that published nothing. Same rule as the wake, the point and the picture: the conclusion
  // is not the evidence, and an issue nobody wrote is the easiest thing in the world to report as built.
  reset();
  seedMember('deepseek', 'deepseek-flash');
  seedShelf();
  actions.runs.push(runObject(43600000002, 'workflow_dispatch', 'magazine'));
  const mag2 = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    render = () => {};
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash'}];
    await viewMagazine(document.getElementById('main'));
    await buildIssue();
    return {html: document.getElementById('issue').innerHTML || ''};
  })()`);

  check('a run that committed no issue is not reported as one', () => {
    if (mag2.err) return mag2.err;
    if (!/still holds no issue/.test(mag2.html)) return `the page said: "${mag2.html}"`;
    if (!/43600000002/.test(mag2.html)) return 'the run is not named';
    if (!/issues\//.test(mag2.html)) return 'the folder an issue would have appeared in is not named';
    return '';
  });

  // 6d — a press that changes no byte. The magazine is derived from the shelf, so assembling the same shelf
  // twice gives the same file: that is the machinery working, not a failure — and it is not a publication
  // either. Both sentences are true; only one of them is about this press.
  reset();
  seedMember('deepseek', 'deepseek-flash');
  seedShelf();
  seed('issues/01.md', ISSUE);
  actions.runs.push(runObject(43600000003, 'workflow_dispatch', 'magazine'));
  const mag3 = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    render = () => {};
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash'}];
    await viewMagazine(document.getElementById('main'));
    await buildIssue();
    return {said: document.getElementById('issuemsg').textContent || '',
            html: document.getElementById('issue').innerHTML || ''};
  })()`);

  check('a press that adds no commit says so instead of claiming a publication', () => {
    if (mag3.err) return mag3.err;
    if (/is in the record/.test(mag3.said)) return `the page claimed a publication: "${mag3.said}"`;
    if (!/already on the shelf, byte for byte/.test(mag3.said)) return `the page said: "${mag3.said}"`;
    if (!/byte for byte/.test(mag3.html)) return 'the issue on the page is not labelled with what happened';
    if (!/the harbour, written/.test(mag3.html)) return 'and the issue that is already on the shelf is not shown';
    return '';
  });

  // 6e — a shelf with no works. The assembler would write a header and one true sentence saying nothing has
  // been filed; committing that publishes a nothing. Refused before the press, like the shot the court would
  // clamp — and the refusal says where a work goes, because "no" without an address is not an answer.
  reset();
  seedMember('deepseek', 'deepseek-flash');
  const mag4 = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    render = () => {};
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash'}];
    await viewMagazine(document.getElementById('main'));
    await buildIssue();
    return {html: document.getElementById('issuemsg').innerHTML || ''};
  })()`);

  check('an empty shelf is refused before anything is sent, with the place a work goes', () => {
    if (mag4.err) return mag4.err;
    if (dispatches.length) return `it was sent anyway (${dispatches.length} dispatch(es))`;
    if (!/shelf holds no works/.test(mag4.html)) return `the page said: "${mag4.html}"`;
    if (!/works\/&lt;member&gt;|works\/<member>/.test(mag4.html)) return 'the refusal does not say where a work goes';
    if (!/Nothing was sent/.test(mag4.html)) return 'the refusal does not say that nothing was sent';
    return '';
  });

  /* 6 — the two errors the founder's own presses produced, on 2026-11-13, on a tribe whose machinery is older
     than the page. Neither is a fault in the physics: one is the page asking a repository for a field it does
     not have, and the other is a run that ended in a word. Both were reported as codes. */
  reset();
  const older = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    // GitHub's actual refusal, as a repository one version behind this page answers it.
    const real = gh;
    gh = async () => { throw new Error('422 · Unexpected inputs provided: ["person", "shot"]'); };
    try { await dispatch('season.yml', {person: 'Lindsay', shot: 'FACE 6 POWER 62 AIM 12'}); }
    catch(e){ return {said: e.message}; }
    finally { gh = real; }
    return {said: 'it did not refuse'};
  })()`);

  check('a tribe older than the page is told so in words, not as 422', () => {
    if (older.err) return older.err;
    if (/^422/.test(older.said)) return 'the page still shows GitHub\'s code';
    if (!/season\.yml/.test(older.said)) return `the workflow is not named: "${older.said}"`;
    if (!/person/.test(older.said) || !/shot/.test(older.said))
      return `the fields the repository lacks are not named: "${older.said}"`;
    if (!/Nothing was sent/.test(older.said)) return 'it does not say that nothing happened';
    return '';
  });

  reset();
  seedMember('openrouter', 'deepseek-flash');
  seed('wake/members/Dionysus/state/voice.md', 'api: deepseek\nmodel: deepseek-flash\n');
  actions.runs.push({id: 43464439540, name: 'season', event: 'workflow_dispatch', status: 'completed',
    conclusion: 'failure', html_url: 'https://github.com/someone/tribe/actions/runs/43464439540',
    created_at: new Date().toISOString()});
  const failed = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    render = () => {};
    S.members = [{name: 'Aphrodite', engine: 'openrouter', model: 'x'}, {name: 'Dionysus', engine: 'deepseek', model: 'y'}];
    await viewPlay(document.getElementById('main'));
    document.getElementById('p1').value = 'Aphrodite';
    document.getElementById('p2').value = 'Dionysus';
    document.getElementById('season').value = '2026-spring';
    document.getElementById('rallies').value = '8';
    document.getElementById('surface').value = 'auto';
    await document.getElementById('go').onclick();
    return {html: document.getElementById('pmsg').innerHTML || ''};
  })()`);

  check('a season that ended in a word names the run, and the secret the repository is missing', () => {
    if (failed.err) return failed.err;
    if (!/43464439540/.test(failed.html)) return `the run is not named: "${failed.html}"`;
    if (!/actions\/runs\/43464439540/.test(failed.html)) return 'the run number is not a link to the run';
    // The repository here holds no secrets, so the page can prove why the run had nothing to think with — and it
    // must say which names, because "add a key" to a person holding eight is not an instruction.
    if (!/TRIBE_API_KEY_OPENROUTER/.test(failed.html)) return `the missing key is not named: "${failed.html}"`;
    if (!/TRIBE_API_KEY_DEEPSEEK/.test(failed.html)) return 'the second member\'s key is not named';
    if (!/Keys tab/.test(failed.html)) return 'the page does not say that the Keys tab is not the repository\'s copy';
    return '';
  });

  // 6b — and when the token cannot see the secret list, the page claims nothing: it falls back to the run's link.
  // A token without admin is an ordinary case, and a page that guessed would be inventing the reason a run failed.
  reset();
  seedMember('openrouter', 'deepseek-flash');
  seed('wake/members/Dionysus/state/voice.md', 'api: deepseek\nmodel: deepseek-flash\n');
  actions.secretsDenied = true;
  actions.runs.push({id: 43464439541, name: 'season', event: 'workflow_dispatch', status: 'completed',
    conclusion: 'failure', html_url: 'https://github.com/someone/tribe/actions/runs/43464439541',
    created_at: new Date().toISOString()});
  const denied = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    render = () => {};
    S.members = [{name: 'Aphrodite', engine: 'openrouter', model: 'x'}, {name: 'Dionysus', engine: 'deepseek', model: 'y'}];
    await viewPlay(document.getElementById('main'));
    document.getElementById('p1').value = 'Aphrodite';
    document.getElementById('p2').value = 'Dionysus';
    document.getElementById('season').value = '2026-spring';
    document.getElementById('rallies').value = '8';
    document.getElementById('surface').value = 'auto';
    await document.getElementById('go').onclick();
    return {html: document.getElementById('pmsg').innerHTML || ''};
  })()`);

  check('when the page cannot see the secrets it names no reason, only the run', () => {
    if (denied.err) return denied.err;
    if (!/43464439541/.test(denied.html)) return `the run is not named: "${denied.html}"`;
    if (/TRIBE_API_KEY/.test(denied.html)) return 'the page named a secret it could not see';
    if (!/its log says why/.test(denied.html)) return `the fallback is missing: "${denied.html}"`;
    return '';
  });

  /* 7 — adding a member, and the two paragraphs that are not the same for every member. The founder used it on
     2026-11-12 and found the hole: an identity that never lets a member be the figure it is seated as makes the
     model argue with its own prompt. He pasted the missing paragraph into three Greek gods by hand. The page now
     asks for what is known about the member, and this checks that the question exists, that skipping it sends
     nothing rather than a heading over nothing, and that the paste reaches the workflow exactly as typed. */
  reset();
  seed('wake/members/.gitkeep', '');
  actions.runs.push(runObject(43700000001, 'workflow_dispatch', 'new-member'));
  const made = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Sam'; S.members = [];
    S.keys = {gemini: {key: 'k'}};
    render = () => {};
    await addMember();
    document.getElementById('ans').value = 'Aphrodite'; adminAnswer();
    document.getElementById('ans').value = 'Goddess of love'; adminAnswer();
    const asked = document.getElementById('dlg').innerHTML || '';
    document.getElementById('ans').value = 'Aphrodite (The Anchor of Emotion and Charm)\\n\\n• heart of the group';
    adminAnswer();
    pickEngine('gemini'); pickPlace('workshop');
    const confirm = document.getElementById('dlg').innerHTML || '';
    await makeMember();
    return {asked, confirm};
  })()`);
  const madeSent = dispatches[dispatches.length - 1] || {};

  check('the form asks what the world already knows about the member', () => {
    if (made.err) return made.err;
    if (!/<textarea/.test(made.asked)) return `the seat question led to something with no box to paste into: ${made.asked.slice(0, 200)}`;
    if (!/someone new/.test(made.asked)) return 'it does not say what skipping means, so skipping looks like a mistake';
    if (!/knows/.test(made.confirm)) return 'the sheet read back before writing does not mention it';
    return '';
  });
  check('and the paste reaches the workflow as typed, under the member it is about', () => {
    if (made.err) return made.err;
    const d = madeSent;
    if (d.workflow !== 'new-member.yml') return `it dispatched ${d.workflow}`;
    if (String(d.inputs.about ?? '') !== 'Aphrodite (The Anchor of Emotion and Charm)\n\n• heart of the group')
      return `about was ${JSON.stringify(d.inputs.about)}`;
    if (String(d.inputs.seat) !== 'Goddess of love') return `seat was ${JSON.stringify(d.inputs.seat)}`;
    return '';
  });

  reset();
  seed('wake/members/.gitkeep', '');
  actions.runs.push(runObject(43700000002, 'workflow_dispatch', 'new-member'));
  const skipped = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Sam'; S.members = [];
    S.keys = {gemini: {key: 'k'}};
    render = () => {};
    await addMember();
    document.getElementById('ans').value = 'Ada'; adminAnswer();
    document.getElementById('ans').value = 'the archivist'; adminAnswer();
    adminSkipAbout();
    pickEngine('gemini'); pickPlace('workshop');
    const confirm = document.getElementById('dlg').innerHTML || '';
    await makeMember();
    return {confirm};
  })()`);
  const skippedSent = dispatches[dispatches.length - 1] || {};

  check('and skipping it sends nothing, not an empty heading', () => {
    if (skipped.err) return skipped.err;
    if (String((skippedSent.inputs || {}).about ?? '') !== '')
      return `about was ${JSON.stringify((skippedSent.inputs || {}).about)}`;
    if (!/nothing yet/.test(skipped.confirm)) return `the sheet does not say it is someone new: ${skipped.confirm.slice(-300)}`;
    return '';
  });

  // 7c — the tribe is older than the page. Every tribe installed from a template published before this question
  // has no `about` field, and GitHub refuses the whole dispatch rather than the field. Refusing to make the member
  // would turn one missing question into a tribe that cannot add members at all; dropping the paste silently is
  // the fault this project keeps finding. So it is made without it, and the page says so and says where to paste.
  reset();
  seed('wake/members/.gitkeep', '');
  actions.runs.push(runObject(43700000003, 'workflow_dispatch', 'new-member'));
  const olderTribe = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Sam'; S.members = [];
    S.keys = {gemini: {key: 'k'}};
    render = () => {};
    const real = gh; let first = true;
    gh = async (p, init) => {
      if (first && /dispatches$/.test(String(p))){ first = false;
        throw new Error('422 · Unexpected inputs provided: ["about"]'); }
      return real(p, init);
    };
    await addMember();
    document.getElementById('ans').value = 'Hermes'; adminAnswer();
    document.getElementById('ans').value = 'the messenger god'; adminAnswer();
    document.getElementById('ans').value = 'Hermes (The Ultimate Facilitator)\\n\\n• he bridges the gap';
    adminAnswer();
    pickEngine('gemini'); pickPlace('workshop');
    await makeMember();
    gh = real;
    return {said: document.getElementById('dmsg').innerHTML || ''};
  })()`);

  check('a tribe older than the question still gets its member, and is told what was not saved', () => {
    if (olderTribe.err) return olderTribe.err;
    // The refused dispatch never reaches the fake repository — a throw has no fetch behind it — so what can be
    // seen here is the retry: one dispatch, and it must not carry the field the workflow does not declare.
    if (dispatches.length !== 1) return `${dispatches.length} dispatch(es); the retry did not happen`;
    if ('about' in (dispatches[0].inputs || {})) return 'the retry still carried the field the repository refuses';
    if (String(dispatches[0].inputs.name) !== 'Hermes') return 'the retry is not the same member';
    if (!/was not saved/.test(olderTribe.said)) return `the page did not say the description was dropped: "${olderTribe.said}"`;
    if (!/Edit this/.test(olderTribe.said)) return 'it does not say where the text can still go';
    return '';
  });

  /* 8 — a public tribe says so; a private one says nothing; a page that was never told says nothing either.
     The owner's question, 2026-11-15: "can't they later make their repos public, possibly without realizing
     that they are exposing..." Nothing warned them, because nothing read the one field that answers it. */
  const connectTo = async (priv) => {
    reset();
    seed('wake/members/.gitkeep', '');
    repoMeta.private = priv;
    return tryRun(ctx, `(async () => {
      S.repo = ''; S.token = ''; S.isPrivate = null; S.keys = {}; S.members = [];
      location.hash = '#/connect';
      await viewConnect(document.getElementById('main'));
    await new Promise(r => setTimeout(r, 40));      // paintApp is started, not awaited, by the view
      document.getElementById('repo').value = 'someone/tribe';
      document.getElementById('token').value = 't';
      await document.getElementById('go').onclick();
      paintVisibility(true);          // render() is stubbed out by the checks above; this is the line it calls
      const n = document.getElementById('visnote');
      // the fake element keeps innerHTML and does not parse it, so the sentence is read from there
      return {isPrivate: S.isPrivate, note: (n.innerHTML || n.textContent || ''), hidden: n.hidden};
    })()`);
  };

  const inPublic = await connectTo(false);
  check('a public tribe is named as public, above every view', () => {
    if (inPublic.err) return inPublic.err;
    if (inPublic.isPrivate !== false) return `the page kept isPrivate=${JSON.stringify(inPublic.isPrivate)} after GitHub said the repository is public`;
    if (inPublic.hidden) return 'the notice stays hidden in a public tribe';
    if (!/public/i.test(inPublic.note)) return `the notice does not say public: "${inPublic.note.slice(0, 200)}"`;
    if (!/journal/i.test(inPublic.note)) return 'it does not say what becomes readable';
    return '';
  });

  const inPrivate = await connectTo(true);
  check('a private tribe is not accused of being public', () => {
    if (inPrivate.err) return inPrivate.err;
    if (inPrivate.isPrivate !== true) return `isPrivate=${JSON.stringify(inPrivate.isPrivate)}`;
    if (!inPrivate.hidden) return `a private tribe carries a warning: "${inPrivate.note.slice(0, 120)}"`;
    return '';
  });

  const inUnknown = await connectTo(undefined);
  check('a page that was never told says nothing, rather than guessing', () => {
    if (inUnknown.err) return inUnknown.err;
    if (inUnknown.isPrivate !== null) return `isPrivate=${JSON.stringify(inUnknown.isPrivate)} — an absent field is not a public repository`;
    if (!inUnknown.hidden) return `a warning appeared without an answer: "${inUnknown.note.slice(0, 120)}"`;
    return '';
  });
  repoMeta.private = true;

  /* 8 — worlds. The ground a member stands in: `soil/<world>/world.md` is quoted into every wake of every member
     standing there, and `name.md` is the title the magazine prints. It is the one part of a tribe that is neither
     code nor a member, and until 2026-11-15 the page could pick one and not write one — so the founder's most
     entertaining use (a cast with a setting) needed a terminal. Three checks: an edit lands, a create writes both
     files, and a name that is empty or taken writes nothing at all. */
  reset();
  seed('wake/members/.gitkeep', '');
  seed('soil/workshop/name.md', 'The Workshop\n');
  seed('soil/workshop/world.md', '# The soil\n\nA workshop at the end of a pier.\n');
  seed('soil/workshop/drops.md', '# Drops\n');
  const world1 = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    render = () => {};
    await viewWorld(document.getElementById('main'), 'workshop');
    // The fake document holds text rather than parsing HTML, so what the view *drew* is read from the markup;
    // what the person then types is the element's value, set here.
    const drew = document.getElementById('main').innerHTML || '';
    document.getElementById('wf-world.md').value = '# The soil\\n\\nA workshop above a chandlery, and a kettle.\\n';
    await saveWorldFile('workshop', 'world.md');
    return {drew, said: document.getElementById('wfmsg-world.md').innerHTML || ''};
  })()`);

  check('a world can be rewritten from the page, and the box is what was on disk', () => {
    if (world1.err) return world1.err;
    if (!/workshop at the end of a pier/.test(world1.drew)) return `the view drew "${world1.drew}"`;
    const now = (files.get('soil/workshop/world.md') || {}).text || '';
    if (!/a kettle/.test(now)) return `the file holds "${now}"`;
    if (!/saved/.test(world1.said)) return `the page said: "${world1.said}"`;
    return '';
  });

  reset();
  seed('wake/members/.gitkeep', '');
  seed('soil/workshop/name.md', 'The Workshop\n');
  seed('soil/workshop/world.md', '# The soil\n');
  const world2 = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    render = () => {};
    document.getElementById('wnew-title').value = "Jerry's Building";
    document.getElementById('wnew-slug').value = '';
    document.getElementById('wnew-world').value = 'Apartment 5A, West 81st Street, 1991.';
    await newWorld();
    return {hash: location.hash};
  })()`);

  check('a new world writes the folder name the magazine prints and the ground the members read', () => {
    if (world2.err) return world2.err;
    const name = (files.get('soil/jerrys-building/name.md') || {}).text || '';
    const world = (files.get('soil/jerrys-building/world.md') || {}).text || '';
    if (!/Jerry's Building/.test(name)) return `name.md holds "${name}"`;
    if (!/West 81st Street/.test(world)) return `world.md holds "${world}"`;
    if (world2.hash !== '#/w/jerrys-building') return `the page did not open it: ${world2.hash}`;
    return '';
  });

  reset();
  seed('wake/members/.gitkeep', '');
  seed('soil/workshop/name.md', 'The Workshop\n');
  const world3 = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    render = () => {};
    const say = () => document.getElementById('wnewmsg').innerHTML || '';
    document.getElementById('wnew-title').value = '';
    document.getElementById('wnew-slug').value = '';
    await newWorld();
    const nameless = say();
    document.getElementById('wnew-title').value = 'workshop';
    document.getElementById('wnew-world').value = 'something';
    await newWorld();
    return {nameless, taken: say()};
  })()`);

  check('a world with no name, or a name already taken, writes nothing', () => {
    if (world3.err) return world3.err;
    if (!/needs a name/.test(world3.nameless)) return `a nameless world said: "${world3.nameless}"`;
    if (!/already a world called workshop/.test(world3.taken)) return `a taken name said: "${world3.taken}"`;
    const wrote = [...files.keys()].filter(p => p.startsWith('soil/') && !p.startsWith('soil/workshop/'));
    if (wrote.length) return `it wrote ${wrote.join(', ')}`;
    return '';
  });

  /* item 7, 2026-11-15 — whose name goes on the person's turn.
     `turnsToText` and `threadText` filed any turn with no `who` under the literal `Lindsay`. In the founder's own
     tribe that is right by accident — he is Lindsay — and in anybody else's it puts a stranger's name on somebody
     else's questions, in the two files that claim to be what happened: the chapter, and the member's memory of the
     talk. `personLabel()` already existed and was already used in the prompt; the writers were never pointed at it. */
  reset();
  seed('wake/members/Lumi/state/identity.md', '# Lumi');
  seed('wake/members/Lumi/state/journal.md', '# Journal\n');
  seed('wake/members/Lumi/state/state.md', '# State\n\nWakes so far: 3\nLast wake: yesterday\n');
  seed('wake/members/Lumi/state/voice.md', 'api: deepseek\nmodel: deepseek-flash\n');
  seed('wake/members/Lumi/state/conversation.md', '# Conversation — Lumi\n');
  for (const f of ['place.md', 'open-items.md', 'memory.md']) seed('wake/members/Lumi/state/' + f, '# ' + f + '\n');

  const sams = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.keys = {deepseek: {key: 'k'}};
    S.owner = 'Sam Okonkwo';
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash', journal: ''}];
    S.chat.Lumi = [
      {role:'user', at:'2026-11-15 18:00 UTC', content:'is anyone there?'},
      {role:'assistant', at:'2026-11-15 18:01 UTC', content:'I am here.'},
    ];
    const thread = threadText('Lumi', S.chat.Lumi);
    await fileConversation('Lumi');
    return {thread};
  })()`);

  const samChapters = [...files.keys()].filter(p => /^wake\/members\/Lumi\/state\/talk\/\d{3}-.*\.md$/.test(p));
  const samChapter = samChapters.length ? text(samChapters[0]) : '';

  check("a chapter in somebody else's tribe is signed with that person's name", () => {
    if (sams.err) return sams.err;
    if (!/— Sam\n/.test(samChapter)) return `the person's turn is headed: ${(samChapter.match(/^## .*$/m) || ['nothing'])[0]}`;
    if (/Lindsay/.test(samChapter)) return "the founder's name is on a stranger's chapter";
    if (!/— Lumi\n/.test(samChapter)) return "the member's own turn lost its name";
    return '';
  });
  check('and so is the conversation file the member reads every wake', () => {
    if (sams.err) return sams.err;
    if (!/— Sam\n/.test(String(sams.thread))) return `the file says: ${(String(sams.thread).match(/^## .*$/m) || ['nothing'])[0]}`;
    if (/Lindsay/.test(String(sams.thread))) return "the founder's name is in a stranger's conversation file";
    if (!/— Lumi\n/.test(String(sams.thread))) return 'the member signed its own turn with something else';
    return '';
  });

  // What to do about the chapters already written. Nothing: they are not rewritten, and they do not need to be —
  // the reader never depended on the name. With the member list loaded, anyone who is not a member is the person,
  // so `— Lindsay` in somebody else's chapter still reads as that person's turn. The check is here because the
  // answer to "and the ones already written?" should be a test rather than a promise.
  const legacy = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Sam Okonkwo';
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash'}];
    const filed = parseTurns('# Talk — Lumi\\n\\n## 2026-11-12 22:30 UTC — Lindsay\\n\\nan old question\\n\\n'
      + '## 2026-11-12 22:31 UTC — Lumi\\n\\nan old answer\\n');
    S.members = [];   // a page whose member list has not loaded: the fallback is the only thing left to go on
    const bare = parseTurns('## 2026-11-12 22:30 UTC — Lindsay\\n\\nan old question\\n');
    S.owner = '';      // and a page that has never been told who the person is
    return {filed: filed.map(t => t.role), bare: bare.map(t => t.role), label: personLabel()};
  })()`);

  check("a chapter already signed `Lindsay` still reads as the person's turn", () => {
    if (legacy.err) return legacy.err;
    if (legacy.filed.join(',') !== 'user,assistant') return `with the member list loaded the roles are: ${legacy.filed}`;
    if (legacy.bare.join(',') !== 'user') return `with no member list the old heading reads as: ${legacy.bare}`;
    return '';
  });
  check('a page that does not know the person writes no name at all rather than the wrong one', () => {
    if (legacy.err) return legacy.err;
    if (legacy.label === 'Lindsay') return 'the founder\'s name is still the fallback';
    return '';
  });

  /* item 9, 2026-11-15 — what pressing Let them talk does, said before it is pressed.
     The founder could not work out the Rounds list or that button (his #3/#6, 2026-11-12). The panel explained the
     mechanic — "4 calls a round; it stops when nobody has anything the judge would choose" — to a person who wanted
     the effect, and everything that says what a round *is* sat in paragraphs below the control, which a person who
     pressed it had already scrolled past. Three facts now come before the button: a round is one question to
     everybody at once, they answer on their own without hearing each other, and one answer is said aloud while the
     rest are kept. The wording is the page's, not the manual's, because the page is where the press happens. */
  reset();
  seed('wake/members/Hermes/state/identity.md', '# Hermes');
  seed('wake/members/Hermes/state/journal.md', '# Journal\n');
  seed('wake/members/Hermes/state/state.md', '# State\n\nWakes so far: 1\n');
  seed('wake/members/Hermes/state/voice.md', 'api: deepseek\nmodel: deepseek-flash\n');
  for (const f of ['place.md', 'open-items.md', 'memory.md']) seed('wake/members/Hermes/state/' + f, '# ' + f + '\n');
  seed('wake/members/Dionysus/state/identity.md', '# Dionysus');
  seed('wake/members/Dionysus/state/journal.md', '# Journal\n');
  seed('wake/members/Dionysus/state/state.md', '# State\n\nWakes so far: 1\n');
  seed('wake/members/Dionysus/state/voice.md', 'api: deepseek\nmodel: deepseek-flash\n');
  for (const f of ['place.md', 'open-items.md', 'memory.md']) seed('wake/members/Dionysus/state/' + f, '# ' + f + '\n');
  seed('chats/the-trojan-war/chat.md', '# A chat — The Trojan War\n\nMembers: Hermes, Dionysus\nFloor: claim\n');
  seed('chats/the-trojan-war/talk.md', '# Talk — the trojan war\n\n## 2026-11-12 22:30 UTC — Lindsay\n\nwhat is a hero?\n');

  const claimRoom = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Lindsay Ridgeway';
    S.members = []; CHAT = {};
    await viewChat(document.getElementById('main'), 'the-trojan-war');
    return {html: document.getElementById('main').innerHTML};
  })()`);

  check('the round control says what a round is, above the button that starts one', () => {
    if (claimRoom.err) return claimRoom.err;
    const html = String(claimRoom.html);
    const says = html.indexOf('A round is one');
    const button = html.indexOf('startLoop(');
    if (says < 0) return 'the room view does not say what a round is';
    if (button < 0) return 'there is no button to compare against';
    if (!(says < button)) return 'the sentence is below the button, so it is read after the press';
    if (!/none of them hearing the others first/.test(html)) return 'it does not say that members answer without hearing each other';
    if (!/highest urgency is the one said aloud/.test(html)) return 'it does not say who is said aloud';
    if (!/kept in the file and not\s+said/.test(html)) return 'it does not say what happens to the answers that lose';
    return '';
  });

  check('and the caveat that keeps the claim honest survives the trim', () => {
    if (claimRoom.err) return claimRoom.err;
    if (!/claim, not a measurement/.test(String(claimRoom.html))) return 'the claim-is-not-a-measurement sentence is gone';
    return '';
  });

  reset();
  seed('wake/members/Hermes/state/identity.md', '# Hermes');
  seed('wake/members/Hermes/state/journal.md', '# Journal\n');
  seed('wake/members/Hermes/state/state.md', '# State\n\nWakes so far: 1\n');
  seed('wake/members/Hermes/state/voice.md', 'api: deepseek\nmodel: deepseek-flash\n');
  for (const f of ['place.md', 'open-items.md', 'memory.md']) seed('wake/members/Hermes/state/' + f, '# ' + f + '\n');
  seed('wake/members/Dionysus/state/identity.md', '# Dionysus');
  seed('wake/members/Dionysus/state/journal.md', '# Journal\n');
  seed('wake/members/Dionysus/state/state.md', '# State\n\nWakes so far: 1\n');
  seed('wake/members/Dionysus/state/voice.md', 'api: deepseek\nmodel: deepseek-flash\n');
  for (const f of ['place.md', 'open-items.md', 'memory.md']) seed('wake/members/Dionysus/state/' + f, '# ' + f + '\n');
  seed('chats/the-trojan-war/chat.md', '# A chat — The Trojan War\n\nMembers: Hermes, Dionysus\nFloor: judge\nJudge: gemini\nRepeat: 1\n');
  seed('chats/the-trojan-war/talk.md', '# Talk — the trojan war\n\n## 2026-11-12 22:30 UTC — Lindsay\n\nwhat is a hero?\n');

  const judgeRoom = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Lindsay Ridgeway';
    S.members = []; CHAT = {};
    await viewChat(document.getElementById('main'), 'the-trojan-war');
    return {html: document.getElementById('main').innerHTML};
  })()`);

  check('in a room where a judge decides, the same sentence names the judge instead', () => {
    if (judgeRoom.err) return judgeRoom.err;
    const html = String(judgeRoom.html);
    if (!/The judge then picks the one answer that is said aloud/.test(html)) return 'the judge variant of the sentence is missing';
    if (/highest urgency is the one said aloud/.test(html)) return 'it promises a claim vote in a room where the judge decides';
    if (!/kept in the file and not\s+said/.test(html)) return 'it does not say what happens to the answers the judge did not pick';
    return '';
  });

  /* the clock's key, 2026-11-15 — the page says when a member will never wake, instead of guessing 30 hours later.
     The founder's own evening: two keys on the Keys tab, "all the required keys are now provided", and a
     repository with none. The page's Keys tab holds this browser's copy; a scheduled run can only read the
     repository's. The page already knew how to read the repository's secret *names* (after a failed run) and how
     to read the engines the clock forwards — this is the same two facts, asked before anything fails. */
  const CLOCK_YML = ['.github/workflows/clock.yml', 'name: clock\njobs:\n  wake:\n    steps:\n'
    + ['deepseek','gemini','qwen','openai','groq','openrouter','cerebras','mistral','together','anthropic']
        .map(e => `      - run: echo\n        env:\n          TRIBE_API_KEY_${e.toUpperCase()}: \${{ secrets.TRIBE_API_KEY_${e.toUpperCase()} }}`)
        .join('\n') + '\n'];
  const plantMember = (name, api) => {
    seed(`wake/members/${name}/state/identity.md`, `# ${name}`);
    seed(`wake/members/${name}/state/journal.md`, '# Journal\n');
    seed(`wake/members/${name}/state/state.md`, '# State\n\nWakes so far: 2\nLast wake: 2026-11-15 12:00 UTC\n');
    seed(`wake/members/${name}/state/voice.md`, `api: ${api}\nmodel: someone's-model\n`);
    for (const f of ['place', 'open-items', 'memory']) seed(`wake/members/${name}/state/${f}.md`, '# ' + f + '\n');
  };

  reset();
  seed(CLOCK_YML[0], CLOCK_YML[1]);
  plantMember('Lumi', 'deepseek');
  plantMember('Wisp', 'local');
  const unarmed = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Sam';
    await viewToday(document.getElementById('main'));
    return document.getElementById('main').innerHTML;
  })()`);

  check('a member whose engine has no key in the repository is named, with the secret to add', () => {
    if (unarmed.err) return unarmed.err;
    const html = String(unarmed);
    if (!/will never wake on the clock/.test(html)) return 'the page says nothing about a clock that cannot wake anyone';
    if (!/TRIBE_API_KEY_DEEPSEEK/.test(html)) return 'it does not name the secret the repository is missing';
    if (!/Settings .* Secrets and variables .* Actions/s.test(html)) return 'it does not say where a repository secret goes';
    // Either it explains that the browser's copy is not where the runner looks, or — when this browser does hold a
    // key for that engine, which is the common case — it offers the press that puts it there. Both are the same
    // fact, and since 2026-11-19 the second one is the better answer to it.
    if (!/Keys tab holds this browser.s copy/.test(html) && !/Put my .* key in the repository/.test(html))
      return 'it neither explains why the browser copy is not enough nor offers to put it in the repository';
    if (!/https:\/\/github\.com\/someone\/tribe\/settings\/secrets\/actions\/new/.test(html))
      return 'it says where the secret goes but does not take the person there';
    if (!/Read again/.test(html)) return 'it does not say the notice is re-read rather than remembered';
    return '';
  });
  check('and weights on your own machine are told apart from a missing key', () => {
    if (unarmed.err) return unarmed.err;
    const html = String(unarmed);
    if (!/Wisp \(local\)/.test(html)) return 'the local member is not named';
    if (!/weights on your own machine/.test(html)) return 'a member on weights is given the missing-key sentence, which is not its problem';
    if (!/the clock runs on GitHub, which has none/.test(html)) return 'it does not say why a runner cannot reach weights';
    return '';
  });

  reset();
  seed(CLOCK_YML[0], CLOCK_YML[1]);
  plantMember('Lumi', 'deepseek');
  actions.secrets = ['TRIBE_API_KEY_DEEPSEEK'];
  const armedRoom = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Sam';
    await viewToday(document.getElementById('main'));
    return document.getElementById('main').innerHTML;
  })()`);

  check('a repository that holds the key is not accused of missing it', () => {
    if (armedRoom.err) return armedRoom.err;
    if (/will never wake on the clock/.test(String(armedRoom))) return 'the page warns about a clock that is armed';
    return '';
  });

  /* 2026-11-19 — the repository holds a secret *name*; the runner found no *value*. Three ways that happens (empty,
     an environment secret a repository-level run never sees, revoked at the vendor) and all three look identical from
     the names list: armed. The clock now writes what it found, and the page reads it, because the runner is the only
     place that knows. */
  const plantRecord = (engines, when = '2026-11-19T04:41:00Z') => seed('.ait/last-clock.json', JSON.stringify({
    schema: 'ait-clock/1', when, engines, turns: [{place: 'workshop', member: 'Lumi', why: 'fewest wakes'}],
    skipped: []}) + '\n');

  reset();
  seed(CLOCK_YML[0], CLOCK_YML[1]);
  plantMember('Lumi', 'deepseek');
  actions.secrets = ['TRIBE_API_KEY_DEEPSEEK'];
  plantRecord([]);
  const valueless = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Sam';
    await viewToday(document.getElementById('main'));
    return document.getElementById('main').innerHTML;
  })()`);

  check('a secret whose name is there and whose value is not is told apart from a missing one', () => {
    if (valueless.err) return valueless.err;
    const html = String(valueless);
    if (!/will not wake on the clock/.test(html)) return 'the page says nothing about an armed-looking clock that woke nobody';
    if (/will never wake on the clock/.test(html)) return 'it says the secret is missing, which is not the fact';
    if (!/TRIBE_API_KEY_DEEPSEEK/.test(html)) return 'it does not name the secret';
    if (!/environment/i.test(html)) return 'it does not name the likeliest cause';
    if (!/2026-11-19 04:41 UTC/.test(html)) return 'it does not say when the clock looked: ' + html.slice(0, 400);
    if (!/no key at all/.test(html)) return 'a run that found no keys at all is described as if it found some';
    if (!/secrets\/actions\/new/.test(html)) return 'it does not take the person to the page that fixes it';
    return '';
  });

  const todayView = `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Sam';
    await viewToday(document.getElementById('main'));
    return document.getElementById('main').innerHTML;
  })()`;

  reset();
  seed(CLOCK_YML[0], CLOCK_YML[1]);
  plantMember('Lumi', 'deepseek');
  actions.secrets = ['TRIBE_API_KEY_DEEPSEEK'];
  plantRecord(['deepseek']);
  const found = await tryRun(ctx, todayView);
  check('a key the runner did find is not reported as a fault', () => {
    if (found.err) return found.err;
    const html = String(found);
    if (/will not wake on the clock/.test(html)) return 'the page blames a clock that had the key and woke the member';
    if (/will never wake on the clock/.test(html)) return 'the page blames the secret list too';
    return '';
  });

  reset();
  seed(CLOCK_YML[0], CLOCK_YML[1]);
  plantMember('Lumi', 'deepseek');
  actions.secrets = ['TRIBE_API_KEY_DEEPSEEK'];
  const noRecord = await tryRun(ctx, todayView);
  check('a circle whose clock predates the record is told nothing, not told a guess', () => {
    if (noRecord.err) return noRecord.err;
    if (/will not wake on the clock/.test(String(noRecord))) return 'the page invented a record it never read';
    return '';
  });

  reset();
  seed(CLOCK_YML[0], CLOCK_YML[1]);
  plantMember('Lumi', 'deepseek');
  actions.secrets = ['TRIBE_API_KEY_DEEPSEEK'];
  plantRecord(['gemini']);
  const otherKey = await tryRun(ctx, todayView);
  check('a run that had a key for a different engine is not read as having this one', () => {
    if (otherKey.err) return otherKey.err;
    const html = String(otherKey);
    if (!/will not wake on the clock/.test(html)) return 'a run with a key for another engine is read as armed';
    if (!/keys for <code>gemini<\/code>/.test(html)) return 'it does not say which keys the run did have: ' + html.slice(0, 500);
    return '';
  });

  reset();
  seed(CLOCK_YML[0], CLOCK_YML[1]);
  plantMember('Lumi', 'deepseek');
  actions.secretsDenied = true;
  const blind = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Sam';
    await viewToday(document.getElementById('main'));
    return document.getElementById('main').innerHTML;
  })()`);

  check('a token that cannot see the secrets is told nothing rather than told a guess', () => {
    if (blind.err) return blind.err;
    if (/will never wake on the clock/.test(String(blind))) return 'the page accuses a repository it could not read';
    return '';
  });

  /* 2026-11-19 — which sign-in this is, after a round trip that changes hostname.

     The founder's own install produced a circle he could not enter: GitHub said
     `403 · You must authenticate with an access token authorized to a GitHub App in order to list installations`,
     because the exchange had been told "classic" about a flow that was the App's. The flag lived in sessionStorage,
     and sessionStorage belongs to one origin — while this app answers on two, and the OAuth callback returns to
     whichever GitHub has registered. So the flag now travels in `state`, which comes back in the URL.

     The harness has no sessionStorage at all, which is exactly the losing half of that round trip: a page that can
     only read the URL must still get this right. */
  reset();
  const askExchange = async (search) => {
    const was = location.search;
    location.search = search;
    exchanges.length = 0;
    loadPage(true);                              // boots the page the way a reload after GitHub does
    await new Promise(r => setTimeout(r, 60));
    location.search = was;
    return exchanges[0] || null;
  };

  const appReturn = await askExchange('?code=one&state=connect.a.7f2k');
  check('a return from the App\'s sign-in is exchanged as the App, with no memory in the browser', () => {
    if (!appReturn) return 'the page never exchanged the code';
    if (appReturn.app !== true) return 'the exchange was told app=' + JSON.stringify(appReturn.app);
    return '';
  });

  const classicReturn = await askExchange('?code=two&state=install.c.9d1x');
  check('and a return from the classic token sign-in is not handed to the App\'s credentials', () => {
    if (!classicReturn) return 'the page never exchanged the code';
    if (classicReturn.app !== false) return 'the exchange was told app=' + JSON.stringify(classicReturn.app);
    return '';
  });

  /* 2026-11-19 — a link to a circle survives the sign-in, and an empty circle keeps its update row.

     The founder followed `?circle=LindsayRidgeway/demo-ai-tribe`, was sent to the connect form because this browser
     had no token for it, pressed "Sign in with GitHub" — and came back into a *different*, brand-new circle whose
     name he had never typed. GitHub returns the browser to the address registered on the OAuth app and drops the
     query string, so the circle a link asked for has to ride in `state`, which does come back. The harness has no
     sessionStorage, which is exactly right: the request must survive that loss. */
  reset();
  const roundTrip = await tryRun(ctx, `(async () => {
    S.repo = ''; S.token = ''; S.circles = {}; S.app = '';
    WANT = 'LindsayRidgeway/demo-ai-tribe';
    const st = oauthState('connect', false);
    // what GitHub hands back: the state, and a new code — no query string, no sessionStorage
    const back = circleFromState(st);
    OAUTH = 'gho_fresh';
    const opened = await resumeWant(back);
    return {state: st, back, opened, repo: S.repo, branch: S.branch};
  })()`);
  check('the circle a link asked for rides in the sign-in state and is opened on the way back', () => {
    if (roundTrip.err) return roundTrip.err;
    if (roundTrip.back !== 'LindsayRidgeway/demo-ai-tribe')
      return 'the state does not carry the circle: ' + JSON.stringify(roundTrip.state) + ' -> ' + JSON.stringify(roundTrip.back);
    if (!roundTrip.opened) return 'the page did not open the circle it was asked for';
    if (roundTrip.repo !== 'LindsayRidgeway/demo-ai-tribe') return 'it opened ' + roundTrip.repo;
    return '';
  });
  const noCarry = await tryRun(ctx, `(async () => {
    // a link from before today, and a sign-in started from the connect form: no fourth field at all
    return ['connect.c.7f2k', 'install.a.9x', '', 'connect.c.7f2k.'].map(st => {
      try { return circleFromState(st); } catch(e){ return 'threw ' + e.message; }
    });
  })()`);
  check('and a state with nothing to carry opens nothing and breaks nothing', () => {
    if (noCarry.err) return noCarry.err;
    const bad = noCarry.filter(x => x !== '');
    if (bad.length) return 'a state with no circle produced ' + JSON.stringify(bad);
    return '';
  });

  reset();
  seed('wake/members/.gitkeep', '');
  const empty = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Sam';
    UPDATE = {state:'unknown', why:'this circle has no .ait/version.json'};
    UPDATE_NOTE = 'Could not check for updates: this circle has no .ait/version.json.';
    await viewToday(document.getElementById('main'));
    return document.getElementById('main').innerHTML;
  })()`);
  check('an empty circle still shows the update line and its button', () => {
    if (empty.err) return empty.err;
    const html = String(empty);
    if (!/Could not check for updates/.test(html)) return 'the update line is missing from an empty circle';
    if (!/See what an update would change/.test(html)) return 'no button: an empty circle is offered nothing';
    if (!/no members yet/.test(html)) return 'the empty state itself is gone, so this is testing nothing';
    return '';
  });

  /* The wall the founder hit: a classic token in a browser, and an App-only endpoint. The old page answered
     "GitHub would not answer: 403 - You must authenticate with an access token authorized to a GitHub App in order to
     list installations" and left the same button in place, so pressing it again was the only offered action and it
     could not work. What a person needs at that moment is the one control that replaces the token. */
  reset();
  actions.installationsDenied = true;
  const wall = await tryRun(ctx, `(async () => {
    S.app = 'gho_classic'; S.repo = ''; S.owner = 'Sam'; S.token = '';
    location.hash = '#/connect';
    await viewConnect(document.getElementById('main'));
    await new Promise(r => setTimeout(r, 40));      // paintApp is started, not awaited, by the view
    // A control the page *adds* is inserted as a child, and a child is not in innerHTML — the page's own
    // insertBefore, then, is what a check has to read. The harness records it as 'inserted'.
    const m = document.getElementById('appmsg') || {};
    return {said: m.textContent || '', html: document.getElementById('main').innerHTML,
            offered: (m.inserted || []).map(b => b.textContent || '')};
  })()`);
  check('a token that is not an App token is named, and the page offers the sign-in that replaces it', () => {
    if (wall.err) return wall.err;
    const said = String(wall.said || '');
    if (/You must authenticate with an access token authorized/.test(said))
      return 'it shows GitHub\'s own sentence, which describes the API and not the fix';
    if (!/not an App token/i.test(said)) return 'it does not say what is wrong with the token it holds: ' + said;
    if (!/Sign in with GitHub again/.test(String(wall.html) + ' ' + (wall.offered || []).join(' ')))
      return 'it does not offer a fresh sign-in';
    return '';
  });

  /* the verdict */
  let bad = 0;
  /* 22 — the sentence that survives the repaint. `render()` rebuilds the view, so a success written into the
     old DOM is written into an element that no longer exists; only the success paths call render(), because a
     failure returns before it — which is why an error stayed on the page and a success vanished two lines later.
     Gwen found it in a browser on 2026-11-13 (#21). The fake deletes the element on render here, which is the
     one thing `reset()` did that a per-check stub did not: model the rewrite. */
  reset();
  seed('wake/members/Lumi/state/identity.md', '# Lumi');
  seed('wake/members/Lumi/state/journal.md', '# Journal\n');
  seed('wake/members/Lumi/state/state.md', '# State\n\nWakes so far: 3\nLast wake: yesterday\n');
  seed('wake/members/Lumi/state/voice.md', 'api: deepseek\nmodel: deepseek-flash\n');
  for (const f of ['place.md', 'open-items.md', 'memory.md', 'conversation.md']) seed('wake/members/Lumi/state/' + f, '# ' + f + '\n');
  const survived = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    S.keys = {deepseek: {key: 'k'}};
    S.owner = 'Sam';
    S.members = [{name: 'Lumi', engine: 'deepseek', model: 'deepseek-flash', journal: ''}];
    S.chat.Lumi = [{role:'user', at:'2026-11-12 19:00 UTC', content:'Keep this.'},
                   {role:'assistant', at:'2026-11-12 19:01 UTC', content:'Kept.'}];
    // The rewrite, as the page experiences it: the view is rebuilt and the element starts empty. Written with the
    // page's own API on purpose - a stub that reached into the harness's element map threw inside the page and the
    // error surfaced as an empty message, which is the same symptom as the bug being tested.
    render = () => { const el = document.getElementById('mmsg'); if (el){ el.textContent = ''; el.innerHTML = ''; } applyFlash(); };
    let threw = '';
    try { await fileConversation('Lumi'); } catch(e){ threw = e.message; }
    render();     // and then one more repaint, which is what the page does as the press finishes
    return {said: (document.getElementById('mmsg').textContent || ''), threw,
            keys: (S.chat.Lumi || []).length};
  })()`);
  check('a success message outlives the repaint that follows it, not just the first one', () => {
    if (survived.err) return survived.err;
    if (process.env.AIT_DEBUG) return 'DEBUG ' + JSON.stringify(survived) + ' inMap=' + elements.has('mmsg') + ' mapText=' + JSON.stringify(((elements.get('mmsg')||{}).textContent)||'');
    if (!/filed/.test(survived.said)) return `the sentence is gone after render(): "${survived.said}"`;
    if (!/chapter/.test(survived.said)) return `it does not say where: "${survived.said}"`;
    return '';
  });


  /* 12 — the write, UPDATE.md step 3. What an update may touch is the template's manifest; whether it may replace a
     file is decided by comparing the tribe's copy against the commit it came from; a file somebody edited is left
     alone and said so; and `members.json`, which is a list derived from the shelf, is never written at all because
     the template's copy of it is empty. Every check here drives the page's own functions against the fake. */
  const HEAD = 'a'.repeat(40), OLD = 'b'.repeat(40);
  const WOLD = '# wake.py\n\nversion = 1\n', WNEW = '# wake.py\n\nversion = 2\n';
  const TOLD = '# tribe.py\n\ndef main(): return 0\n', TNEW = '# tribe.py\n\ndef main(): return 1\n';
  function seedUpdate(opts = {}){
    reset();
    tpl.sha = HEAD;
    seedTemplate('.tribe-manifest.json', JSON.stringify({schema: 'ait-manifest/1',
      files: ['wake/wake.py', 'tribe.py', 'USER-MANUAL.md', 'lab/paint.py']}));
    seedTemplate('wake/wake.py', WNEW);
    seedTemplate('tribe.py', opts.tribeUpstream || TOLD);
    seedTemplate('USER-MANUAL.md', '# manual v2\n');
    // a file the template ships and this circle has never had: an addition needs no proof of anything
    seedTemplate('lab/paint.py', '# paint.py\n');
    // what the tribe was given when it installed: the OLD template commit
    seedTemplate('wake/wake.py', WOLD, OLD);
    seedTemplate('tribe.py', TOLD, OLD);
    seedTemplate('USER-MANUAL.md', '# manual v1\n', OLD);
    // the tribe
    seed('wake/wake.py', WOLD);
    seed('tribe.py', opts.tribe || TOLD);
    seed('USER-MANUAL.md', '# manual v1\n');
    seed('members.json', '[{"name":"Lumi"}]\n');
    seed('wake/members/Lumi/state/journal.md', '# Journal\n\nI wrote a paper boat.\n');
    if (opts.version !== null)
      seed('.ait/version.json', JSON.stringify({schema:'ait-version/1', template:'LindsayRidgeway/ai-tribe-template',
        installed_from: OLD, updated_to: opts.version || null, updated_at: '2026-11-10T00:00:00Z'}) + '\n');
  }
  const settle = (code) => run(ctx, `(async () => { S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    ${code} })()`);

  // 12a — the plan, and what it refuses to include
  seedUpdate();
  const plan1 = await settle(`const p = await updatePlan();
    return {writes: p.writes.map(f => f.path), adds: p.adds.map(f => f.path), kept: p.kept, waiting: p.waiting,
            said: planSentence(p), provable: p.provable};`);
  check('an update names the files that changed and not the ones that did not', () => {
    if (plan1.err) return plan1.err;
    if (!plan1.writes.includes('wake/wake.py') || !plan1.writes.includes('USER-MANUAL.md'))
      return 'the changed files are not in the plan: ' + JSON.stringify(plan1.writes);
    if (plan1.writes.includes('tribe.py')) return 'a file with identical content was listed as changed';
    return '';
  });
  check('nothing on the plan is outside the template\'s manifest', () => {
    const outside = plan1.writes.filter(p => !['wake/wake.py', 'tribe.py', 'USER-MANUAL.md'].includes(p));
    if (outside.length) return 'the plan would write ' + outside.join(', ');
    if (plan1.writes.some(p => p === 'members.json')) return 'the plan would write members.json';
    return '';
  });

  // 12b — the write, and what it does to the record
  seedUpdate();
  const wrote1 = await settle(`let threw = ''; let r = {done:[], clash:[], p:{kept:[],waiting:[]}};
    try { r = await applyUpdate(); } catch(e){ threw = e.message; }
    return {threw, done: r.done, clash: r.clash, said: updateReport(r),
            wake: (await fileText('wake/wake.py')).text,
            members: (await fileText('members.json')).text,
            version: JSON.parse((await fileText('.ait/version.json')).text)};`);
  check('pressing update writes the manifest files and leaves the tribe\'s own list alone', () => {
    if (wrote1.err) return wrote1.err;
    if (process.env.AIT_DEBUG) return 'DEBUG ' + JSON.stringify(wrote1).slice(0,600);
    if (wrote1.wake !== WNEW) return 'wake/wake.py was not replaced with the template\'s copy';
    if (wrote1.members !== '[{"name":"Lumi"}]\n') return 'members.json was overwritten: ' + JSON.stringify(wrote1.members);
    if (text('wake/members/Lumi/state/journal.md') !== '# Journal\n\nI wrote a paper boat.\n')
      return 'a member\'s journal was touched';
    return '';
  });
  check('the version record says which template the tribe now runs, and keeps where it came from', () => {
    if (wrote1.err) return wrote1.err;
    if (wrote1.version.updated_to !== HEAD) return 'updated_to is ' + wrote1.version.updated_to;
    if (wrote1.version.installed_from !== OLD) return 'installed_from was rewritten to ' + wrote1.version.installed_from;
    return '';
  });
  const after1 = await settle(`const u = await updateCheck(); return {state: u.state, said: updateSentence(u)};`);
  check('after a successful write the page reports the tribe as current', () => {
    if (after1.err) return after1.err;
    if (after1.state !== 'current') return 'the state is ' + after1.state + ': ' + after1.said;
    return '';
  });

  // 12c — a file the owner edited is kept, and the rest still land
  seedUpdate({tribe: '# tribe.py\n\ndef main(): return 99   # mine\n'});
  const edited = await settle(`const p = await updatePlan();
    const r = await applyUpdate();
    return {kept: p.kept, done: r.done, said: updateReport(r), plan: planSentence(p),
            tribe: (await fileText('tribe.py')).text};`);
  check('a file somebody edited is left alone, and the update says which one', () => {
    if (edited.err) return edited.err;
    if (!edited.kept.includes('tribe.py')) return 'tribe.py was not recognised as differing: ' + JSON.stringify(edited.kept);
    if (edited.tribe.indexOf('mine') < 0) return 'the edited file was overwritten';
    if (!edited.done.includes('wake/wake.py')) return 'the update stopped at the first differing file';
    if (!/left alone/i.test(edited.said)) return 'the report does not say it was left alone: ' + edited.said;
    if (!/differ from the version this circle records/i.test(edited.said))
      return 'the report claims to know whether it was edited: ' + edited.said;
    if (!/lab\/update_tribe\.py/.test(edited.plan))
      return 'the plan does not say which tool replaces a file it will not decide about: ' + edited.plan;
    return '';
  });

  // 12d — the template that publishes no manifest cannot update anything
  reset();
  tpl.sha = HEAD;
  seed('wake/wake.py', WOLD);
  const nomani = await settle(`let why = ''; try { await applyUpdate(); } catch(e){ why = e.message; }
    return {why, calls: null};`);
  check('a template with no list of files updates nothing and says why', () => {
    if (nomani.err) return nomani.err;
    if (!/does not publish/i.test(nomani.why)) return 'the refusal does not name the reason: "' + nomani.why + '"';
    if (text('wake/wake.py') !== WOLD) return 'a file was written anyway';
    return '';
  });

  // 12e — a template that cannot be read is not "up to date"
  reset();
  seed('wake/wake.py', WOLD);
  const unreachable = await settle(`let why = ''; try { await updatePlan(); } catch(e){ why = e.message; }
    return {why};`);
  check('a template the page cannot read refuses the update in a sentence', () => {
    if (unreachable.err) return unreachable.err;
    if (!/could not be read/i.test(unreachable.why)) return 'the refusal says: "' + unreachable.why + '"';
    return '';
  });

  // 12f — no version record: files may be added, no file may be replaced
  seedUpdate({version: null});
  const nv = await settle(`const p = await updatePlan();
    return {writes: p.writes.map(f=>f.path), waiting: p.waiting, provable: p.provable, said: planSentence(p)};`);
  check('a tribe that does not record where it came from may gain files and lose none', () => {
    if (nv.err) return nv.err;
    if (nv.writes.length) return 'it would replace ' + nv.writes.join(', ') + ' without being able to prove anything';
    if (!nv.waiting.includes('wake/wake.py')) return 'the files it cannot judge are not named';
    return '';
  });

  // 12g — a file written by somebody else between the plan and the write
  seedUpdate();
  clashWrites.add('USER-MANUAL.md');
  const raced = await settle(`const r = await applyUpdate();
    const v = JSON.parse((await fileText('.ait/version.json')).text);
    const u = await updateCheck();
    return {done: r.done, clash: r.clash, stamped: r.stamped, said: updateReport(r),
            updated_to: v.updated_to, state: u.state};`);
  check('a file that changed between the plan and the write is not overwritten', () => {
    if (raced.err) return raced.err;
    if (!raced.clash.includes('USER-MANUAL.md')) return 'the 409 was not noticed: ' + JSON.stringify(raced.clash);
    if (raced.done.includes('USER-MANUAL.md')) return 'a clashing file was reported as written';
    if (!/changed while the page was reading/i.test(raced.said)) return 'the report does not say it: ' + raced.said;
    return '';
  });
  check('an update that could not finish does not claim the tribe is current', () => {
    if (raced.err) return raced.err;
    if (raced.stamped) return 'the record was stamped after a file was left behind';
    if (raced.updated_to === HEAD) return 'the record says the tribe runs the new template';
    if (raced.updated_to !== null) return 'the record was rewritten to ' + JSON.stringify(raced.updated_to);
    if (raced.state !== 'behind') return 'the next load would say ' + raced.state + ' and never offer the file again';
    if (!/offered again/i.test(raced.said)) return 'the report does not say the update will be offered again: ' + raced.said;
    return '';
  });

  // 12g-2 — a record the files contradict is not evidence, and the page says which tool is not fooled by it
  seedUpdate({tribe: '# tribe.py\n\n# rewritten by hand, or by a version this tribe never came from\n'});
  for (const [path, text] of [['wake/wake.py', '# wake.py\n\n# old, from a commit the record does not name\n'],
                              ['USER-MANUAL.md', '# manual, from somewhere else\n']]) seed(path, text);
  const liar = await settle(`const p = await updatePlan();
    return {writes: p.writes.map(f=>f.path), waiting: p.waiting, provable: p.provable,
            agree: p.agree, shared: p.shared, said: planSentence(p),
            r: updateReport(await applyUpdate())};`);
  check('a version record its own files contradict replaces nothing, and names the tool that does not use it', () => {
    if (liar.err) return liar.err;
    if (liar.provable) return 'the record was believed: ' + liar.agree + '/' + liar.shared + ' agree';
    if (liar.writes.length) return 'it would replace ' + liar.writes.join(', ') + ' on a record it cannot trust';
    if (liar.waiting.length !== 3) return 'the files it will not judge are not all named: ' + JSON.stringify(liar.waiting);
    if (!/lab\/update_tribe\.py/.test(liar.said)) return 'the sentence does not name the tool that compares contents: ' + liar.said;
    if (!/does not match its files/.test(liar.said)) return 'the sentence does not say why: ' + liar.said;
    return '';
  });

  // 12h — the button exists when there is something to update, and not otherwise
  const ui = await settle(`const a = (UPDATE = {state:'behind', sha:'${HEAD}'}) && updBlock();
    const u = (UPDATE = {state:'unknown', why:'this circle has no .ait/version.json'}) && updBlock();
    UPDATE = {state:'current', sha:'${HEAD}'};
    const b = updBlock();
    return {behind: /update/i.test(a) && /updmsg/.test(a), unknown: /update/i.test(u) && /updmsg/.test(u), current: b};`);
  check('the page offers an update unless the check says it is current', () => {
    if (ui.err) return ui.err;
    if (!ui.behind) return 'the behind state draws no button';
    if (!ui.unknown) return 'a circle with no version record is offered nothing — and that is the circle that most needs it';
    if (ui.current) return 'the current state still draws one: ' + ui.current;
    return '';
  });

  // the install path's stamp: retried, because a repository GitHub has just generated is not writable for a moment
  reset();
  tpl.sha = HEAD;
  seed('.tribe.py', '');
  actions.busy['.ait/version.json'] = 2;
  const fresh = await settle(`const ok = await stampFreshCircle();
    let v = null; try { v = JSON.parse((await fileText('.ait/version.json')).text); } catch(e){}
    return {ok, v, tries: 0};`);
  check('a circle the page has just installed is stamped even though the repository answers "empty" at first', () => {
    if (fresh.err) return fresh.err;
    if (!fresh.ok) return 'the stamp gave up';
    if (!fresh.v) return 'no .ait/version.json after a successful stamp';
    if (fresh.v.installed_from !== HEAD) return 'the stamp does not name the template: ' + JSON.stringify(fresh.v);
    return '';
  });

  // 12i — a circle with no record at all: the press adds what it can and writes the record it lacked
  seedUpdate({version: null});
  const stamped = await settle(`const r = await applyUpdate();
    const v = JSON.parse((await fileText('.ait/version.json')).text);
    const u = await updateCheck();
    return {done: r.done, said: updateReport(r), v, complete: r.complete,
            state: u.state, why: u.why, touched: u.touched};`);
  check('a press that leaves files behind records what it did and claims no version', () => {
    if (stamped.err) return stamped.err;
    if (!stamped.done.length) return 'nothing was written';
    if (stamped.complete) return 'a circle with files nobody could judge was called complete';
    if (stamped.v.updated_to !== null) return 'the record claims a version the press did not reach: ' + stamped.v.updated_to;
    if (!stamped.v.touched || stamped.v.touched.template !== HEAD) return 'it does not say what it touched: ' + JSON.stringify(stamped.v);
    if (stamped.state !== 'unknown') return 'a partial press was reported as ' + stamped.state;
    if (!/cannot tell whether it is current/.test(stamped.why || '')) return 'the line does not say what it cannot know: ' + stamped.why;
    if (!/lab\/update_tribe\.py/.test(stamped.why || '')) return 'it does not name the tool that compares the files: ' + stamped.why;
    return '';
  });
  // and a press that leaves nothing behind does claim the version — the same fixture as 12b, where every file that
  // differed is landed.
  seedUpdate();
  const wholePress = await settle(`const r = await applyUpdate();
    const v = JSON.parse((await fileText('.ait/version.json')).text);
    return {complete: r.complete, v, state: (await updateCheck()).state};`);
  check('a press with nothing left behind stamps the version it reached', () => {
    if (wholePress.err) return wholePress.err;
    if (!wholePress.complete) return 'a plan with nothing left behind was called partial';
    if (wholePress.v.updated_to !== HEAD) return 'the record does not name the version: ' + JSON.stringify(wholePress.v);
    if (wholePress.state !== 'current') return 'the check afterwards says ' + wholePress.state;
    return '';
  });

  // 12j — a circle whose files are already the template's, and which has no record. This is what a real install
  // produced on 2026-11-19: the machinery copied, the receipt not written. Every file matches, so there is nothing to
  // copy and `applyUpdate` used to return without writing anything — a circle that could never stop being "unchecked".
  seedUpdate({version: null});
  seed('wake/wake.py', WNEW); seed('tribe.py', TOLD);
  seed('USER-MANUAL.md', '# manual v2\n'); seed('lab/paint.py', '# paint.py\n');
  // The button appears on the second look, not the first: this page never writes before it has shown what it would
  // write, so the plan press comes first here exactly as it does in front of a person.
  const same = await settle(`const p = await updatePlan();
    const u = await updateCheck();
    UPD_PLAN = p;
    const row = (UPDATE = u) && updBlock();
    return {writes: p.writes.map(f => f.path), adds: p.adds.map(f => f.path), waiting: p.waiting,
            identical: p.identical, provable: p.provable, said: planSentence(p),
            sentence: updateSentence(u), why: u.why, row};`);
  check('a circle that already has the current files is offered the record, not told nothing', () => {
    if (same.err) return same.err;
    if (!same.identical) return 'the plan does not notice that every file already matches';
    if (same.writes.length || same.adds.length) return 'it wants to write files that already match';
    if (!/Record this version/.test(same.row)) return 'no press is offered: ' + same.row;
    if (!/none of them is replaced/.test(same.said)) return 'the plan does not say nothing will be replaced: ' + same.said;
    if (/predates the version record/.test(same.sentence))
      return 'it tells the owner of a circle made today that their circle predates the record: ' + same.sentence;
    if (!/no record of which template it came from/.test(same.sentence)) return 'the sentence does not say what is missing: ' + same.sentence;
    if (/Could not check for updates/.test(same.sentence)) return 'a circle with no record is reported as a failed check: ' + same.sentence;
    return '';
  });
  const recorded = await settle(`const r = await applyUpdate();
    const got = await fileText('.ait/version.json').catch(() => null);
    const u = await updateCheck();
    return {recorded: !!r.recorded, done: r.done, v: got ? JSON.parse(got.text) : null,
            state: u.state, said: updateReport(r)};`);
  check('pressing it writes the record, replaces nothing, and the circle is current afterwards', () => {
    if (recorded.err) return recorded.err;
    if (!recorded.recorded) return 'the press did not write a record';
    if (!recorded.v) return 'no record was written at all, so this circle can never be told it is current';
    if (recorded.done.length !== 1 || recorded.done[0] !== '.ait/version.json') return 'it wrote something else: ' + JSON.stringify(recorded.done);
    if (recorded.v.updated_to !== HEAD) return 'the record does not name the version it just verified: ' + JSON.stringify(recorded.v);
    if (recorded.v.installed_from !== null) return 'it invented an origin it does not know: ' + JSON.stringify(recorded.v.installed_from);
    if (recorded.v.confirmed !== 'by content') return 'the record does not say how it was known: ' + JSON.stringify(recorded.v);
    if (recorded.state !== 'current') return 'the check afterwards says ' + recorded.state;
    if (!/Nothing was replaced/.test(recorded.said)) return 'the report does not say nothing was replaced: ' + recorded.said;
    return '';
  });

  // 13 — the address the page gives itself
  const was = {host: location.host, search: location.search, hash: location.hash, pathname: location.pathname};
  location.pathname = '/';        // what production serves; the harness file name is not an address
  location.host = 'ai-tribe.netlify.app';
  location.search = '?circle=Sam/tribe&code=one&state=connect.a.7f2k';
  location.hash = '#/today';
  replaceCalls.length = 0;
  exchanges.length = 0;
  loadPage(true);
  await new Promise(r => setTimeout(r, 60));
  const hop = {calls: replaceCalls.slice(), exchanges: exchanges.slice()};
  check('a page opened at the address the rename retired moves to the real one, and keeps the circle and the return', () => {
    if (hop.calls.length !== 1) return 'the page did not move: ' + JSON.stringify(hop.calls);
    if (hop.calls[0] !== 'https://kythe.app/?circle=Sam/tribe&code=one&state=connect.a.7f2k#/today')
      return 'the move loses something: ' + hop.calls[0];
    if (hop.exchanges.length) return 'it read a repository or spent the sign-in code before leaving: ' + JSON.stringify(hop.exchanges);
    return '';
  });
  location.host = 'kythe.app';
  location.search = '';
  location.hash = '';
  replaceCalls.length = 0;
  loadPage(true);
  await new Promise(r => setTimeout(r, 60));
  const nohop = replaceCalls.slice();
  check('a page already at its real name does not move, and a preview deploy is not dragged anywhere', () => {
    if (nohop.length) return 'it moved from its own address: ' + JSON.stringify(nohop);
    location.host = 'deploy-preview-3--ai-tribe.netlify.app';
    replaceCalls.length = 0;
    loadPage(true);
    const preview = replaceCalls.slice();
    location.host = was.host; location.search = was.search; location.hash = was.hash;
    location.pathname = was.pathname;
    if (preview.length) return 'a preview deploy was sent to production: ' + JSON.stringify(preview);
    return '';
  });

  // 14 — the circle's own address, which the page only ever showed on the install screen
  reset();
  seed(CLOCK_YML[0], CLOCK_YML[1]);
  plantMember('Lumi', 'deepseek');
  clipboardWrites.length = 0;
  const addr = await tryRun(ctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.owner = 'Sam';
    await viewToday(document.getElementById('main'));
    const html = document.getElementById('main').innerHTML;
    copyAddress();
    await new Promise(r => setTimeout(r, 20));
    return {html, said: (document.getElementById('addrtold') || {}).textContent || ''};
  })()`);
  addr.copied = clipboardWrites.slice();
  check('a circle shows its own address, and it is the address that opens it', () => {
    if (addr.err) return addr.err;
    const html = String(addr.html || '');
    if (!/https:\/\/kythe\.app\/\?circle=someone\/tribe/.test(html))
      return 'the page never shows the circle address a link would use: ' + html.slice(0, 200);
    if (!/Copy/.test(html)) return 'there is no way to take it out of the page';
    if (addr.copied.length !== 1 || addr.copied[0] !== 'https://kythe.app/?circle=someone/tribe')
      return 'Copy did not put the address on the clipboard: ' + JSON.stringify(addr.copied);
    if (!/copied/.test(String(addr.said))) return 'it does not say that it copied: ' + addr.said;
    return '';
  });
  const addrEmpty = await tryRun(ctx, `(async () => {
    S.repo = 'someone/empty'; S.token = 't'; S.branch = 'main';
    await viewToday(document.getElementById('main'));
    return document.getElementById('main').innerHTML;
  })()`);
  check('an empty circle shows its address too, because that is the circle nobody has a link to yet', () => {
    if (addrEmpty.err) return addrEmpty.err;
    if (!/https:\/\/kythe\.app\/\?circle=someone\/empty/.test(String(addrEmpty)))
      return 'a freshly installed circle is the one whose address nobody has';
    return '';
  });

  // 15 — the clock's own account of its last run, which the page had no way of showing when it went right
  const clocked = await tryRun(ctx, `(async () => {
    const now = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
    const old = new Date(Date.now() - 40 * 3600e3).toISOString().replace(/\.\d+Z$/, 'Z');
    const ran = {schema: 'ait-clock/1', when: now, engines: ['deepseek'], turns: [{member: 'George', why: 'work'}], skipped: []};
    const empty = {schema: 'ait-clock/1', when: now, engines: [], turns: [], skipped: []};
    const blocked = {schema: 'ait-clock/1', when: now, engines: ['deepseek'], turns: [],
                     skipped: [{member: 'Lumi', engine: 'gemini'}]};
    const stale = {schema: 'ait-clock/1', when: old, engines: ['deepseek'], turns: [{member: 'George'}], skipped: []};
    // The founder's own circle wrote this one on 2026-11-19: a free wake, no key held, one turn taken. It is the shape
    // that produced "held , and took 1 turn" in the page, and no made-up fixture had it.
    const freeWake = {schema: 'ait-clock/1', when: now, engines: [], turns: [{place: 'workshop', member: 'George',
                      why: 'fewest wakes (0 in workshop)'}], skipped: []};
    return {ran: clockSentence(ran), empty: clockSentence(empty), blocked: clockSentence(blocked),
            stale: clockSentence(stale), none: clockSentence(null), free: clockSentence(freeWake)};
  })()`);
  check('the page says what the clock did, not only when it failed', () => {
    if (clocked.err) return clocked.err;
    if (!/took 1 turn/.test(clocked.ran) || !/George/.test(clocked.ran) || !/deepseek/.test(clocked.ran))
      return 'a run that woke somebody is not reported: ' + clocked.ran;
    if (!/found no engine key at all/.test(clocked.empty)) return 'a run with no keys is silent: ' + clocked.empty;
    if (!/Lumi/.test(clocked.blocked) || !/no key/.test(clocked.blocked))
      return 'a member the run could not reach is not named: ' + clocked.blocked;
    if (!/hours ago/.test(clocked.stale)) return 'a clock that stopped looks like a clock that is fine: ' + clocked.stale;
    if (clocked.none !== '') return 'with no record it invents one: ' + clocked.none;
    if (/held\s*,/.test(clocked.free)) return 'a wake with no key reads as a gap: ' + clocked.free;
    if (!/no engine key/.test(clocked.free) || !/no engine|costs nothing/.test(clocked.free))
      return 'a free wake is not explained: ' + clocked.free;
    return '';
  });
  /* 15e — the page that asks for a token has a token field on it.
     Two turns of "how do I supply my token" were spent looking at a page where the field was behind a link, and then
     behind a "we already hold one" rule. A field the instruction names must be on screen, in the same card as the
     button that needs it. */
  reset();
  const shape = await tryRun(ctx, `(async () => {
    S.repo = ''; S.token = ''; S.circles = {}; S.app = ''; S.members = [];
    location.hash = '#/connect';
    await viewConnect(document.getElementById('main'));
    const html = document.getElementById('main').innerHTML || '';
    const card = html.slice(html.indexOf('id="pastecard"'), html.indexOf('id="cstore"'));
    return {hasToken: /id="token"/.test(card), hasFind: /id="find"/.test(card),
            hasRepo: /id="repo"/.test(card), hidden: /id="pastecard"[^>]*hidden/.test(html),
            fieldHidden: document.getElementById('token').hidden === true};
  })()`);
  check('the card that asks for a token has the token field in it, on screen', () => {
    if (shape.err) return shape.err;
    if (!shape.hasToken) return 'no token field in the card that needs one';
    if (!shape.hasFind) return 'the search button is not in that card, so the field it needs is somewhere else';
    if (!shape.hasRepo) return 'the name field is not in that card';
    if (shape.hidden) return 'the whole card is hidden';
    if (shape.fieldHidden) return 'the field itself is hidden';
    return '';
  });

  /* 15a — the sentence that answers "that circle isn't in either of them". He asked it twice: once about the list,
     and again with a screenshot of the home page and the words "where is Find my circles, and what token". A page
     that shows a list must say what the list is a list of, and what to do about what it does not contain. */
  reset();
  actions.login = 'LambieLamberton';
  const says = await tryRun(ctx, `(async () => {
    S.repo = ''; S.token = ''; S.circles = {}; S.app = 'app-token'; S.members = [];
    location.hash = '#/connect';
    await viewConnect(document.getElementById('main'));
    await new Promise(r => setTimeout(r, 40));
    const main = document.getElementById('main').innerHTML || '';
    return {missing: /A circle missing from this list/.test(main),
            why: /never let into/.test(main),
            ways: /by name/.test(main) && /token/.test(main)};
  })()`);
  check('a list says what it is a list of, and what to do about a circle it does not contain', () => {
    if (says.err) return says.err;
    if (!says.missing) return 'nothing tells a person their circle may simply not be in this list';
    if (!says.why) return 'it does not say why a circle would be missing';
    if (!says.ways) return 'it does not say where to look for one';
    return '';
  });

  /* 15d — the eight-hour sign-in, and the box that takes a token.
     He pressed "Find my circles" a day after signing in and got `401 · Bad credentials` on a card that said "your
     token"; his question back was "How do I supply my token?" — the box that takes one was hidden behind a link two
     cards away. GitHub App sign-ins last eight hours, and nothing in the page knew that. */
  const expiredSearch = async (opts) => {
    reset();
    actions.login = 'someone';
    actions.denyUser = !!opts.denyUser;      // set after reset(), which clears the fake's flags
    return tryRun(ctx, `(async () => {
      S.repo = ''; S.token = ''; S.circles = {}; S.members = [];
      S.app = ${JSON.stringify(opts.token)}; S.appAt = Date.now() - ${JSON.stringify(opts.ageMs)};
      location.hash = '#/connect';
      await viewConnect(document.getElementById('main'));
      document.getElementById('token').value = '';
      await document.getElementById('find').onclick();
      const m = document.getElementById('findmsg');
      return {said: m.innerHTML || m.textContent,
              boxShown: document.getElementById('pastecard').hidden === false,
              appForgotten: !S.app};
    })()`);
  };
  const stale = await expiredSearch({token: 'gho_old', ageMs: 9 * 3600e3});
  check('a sign-in from yesterday is said to have expired, and never blamed on a token nobody gave', () => {
    if (stale.err) return stale.err;
    if (/Bad credentials|401/.test(stale.said)) return 'it shows a status code: ' + stale.said.slice(0, 160);
    if (!/expired/.test(stale.said) || !/eight hours/.test(stale.said)) return 'it does not say what happened: ' + stale.said.slice(0, 160);
    if (!stale.boxShown) return 'the box that takes a token is still hidden behind a link';
    if (!stale.appForgotten) return 'it kept a dead token and will fail the same way again';
    return '';
  });
  const signInRefused = await expiredSearch({token: 'gho_live', ageMs: 60e3, denyUser: true});
  actions.denyUser = false;
  check('a sign-in GitHub refuses is reported as an expired sign-in, not as an error', () => {
    if (signInRefused.err) return signInRefused.err;
    if (/Bad credentials|401/.test(signInRefused.said)) return 'it shows a status code: ' + signInRefused.said.slice(0, 160);
    if (!/expired/.test(signInRefused.said)) return 'it does not say the sign-in is the thing that expired: ' + signInRefused.said.slice(0, 160);
    if (!signInRefused.boxShown) return 'no token box is offered after the refusal';
    return '';
  });

  /* 15b — a circle the App was never installed on, found without being told its name.
     His words, 2026-11-19: "I have two GH accounts, and that circle doesn't seem to be in either of them." It was
     in neither list because the list was the App's installations, and his circle predates it. */
  reset();
  seed('.tribe-manifest.json', '{"schema":"ait-manifest/1"}');
  seed('members.json', '{"members":[]}');
  actions.login = 'LambieLamberton';
  actions.userRepos = [
    {full_name: 'LambieLamberton/test-circle-20261119-1223', private: true, default_branch: 'main'},
    {full_name: 'LambieLamberton/notes', private: false, default_branch: 'main'},
  ];
  actions.notCircles = ['LambieLamberton/notes'];
  const foundBySearch = await tryRun(ctx, `(async () => {
    S.repo = ''; S.token = ''; S.circles = {}; S.app = ''; S.members = [];
    location.hash = '#/connect';
    await viewConnect(document.getElementById('main'));
    const btn = document.getElementById('find');
    if (!btn) return {err: 'the connect page has no way to look for circles'};
    document.getElementById('token').value = 't';
    await btn.onclick();
    const said = document.getElementById('findmsg').innerHTML || document.getElementById('findmsg').textContent;
    const rows = document.getElementById('findlist').innerHTML || '';
    window.openScanned('LambieLamberton/test-circle-20261119-1223', 'main');
    return {said, rows, repo: S.repo, remembered: Object.keys(S.circles || {})};
  })()`);
  check('a circle the App was never installed on is found by looking, not by being told its name', () => {
    if (foundBySearch.err) return foundBySearch.err;
    if (!/test-circle-20261119-1223/.test(foundBySearch.rows)) return 'the search did not find it: ' + foundBySearch.rows.slice(0, 200);
    if (/LambieLamberton\/notes/.test(foundBySearch.rows)) return 'a repository that is not a circle is offered as one';
    if (!/@LambieLamberton/.test(foundBySearch.said)) return 'it does not say whose account was searched: ' + foundBySearch.said;
    if (foundBySearch.repo !== 'LambieLamberton/test-circle-20261119-1223') return 'pressing it did not open it: ' + foundBySearch.repo;
    if (!foundBySearch.remembered.includes('LambieLamberton/test-circle-20261119-1223'))
      return 'the circle was opened but not kept, so the next visit has to search again';
    return '';
  });

  /* 15c — the leftover query GitHub leaves behind, and the shell that was two shells. */
  reset();
  replaceCalls.length = 0; historyWrites.length = 0;
  const before = location.search, beforeHash = location.hash;
  location.search = '?iss=https%3A%2F%2Fgithub.com%2Flogin%2Foauth&install';
  location.hash = '';
  const hopped = loadPage(true);
  const bar = {search: location.search, hash: location.hash, writes: historyWrites.slice()};
  location.search = before; location.hash = beforeHash;
  check('the address GitHub hands back is put into words before anyone has to read it', () => {
    if (!bar.writes.length) return 'the page kept `?iss=…&install` in the address bar, which is what he sent me';
    if (/iss=|&install/.test(bar.writes[bar.writes.length - 1]))
      return 'it wrote the leftover back: ' + bar.writes[bar.writes.length - 1];
    return '';
  });
  const shell = await tryRun(hopped, `(async () => {
    location.hash = '#/install';
    await renderBody();
    const foot = document.getElementById('foot');
    return {footHidden: !!foot.hidden, hasChip: /id="preview"/.test(document.documentElement.innerHTML || '')};
  })()`);
  check('the install screen wears the same shell as every other page', () => {
    if (shell.err) return shell.err;
    if (shell.footHidden) return 'an unconnected page still hides the footer, so it looks like a different product';
    if (shell.hasChip) return 'the header still carries the version chip, so the mark is in two places';
    return '';
  });

  // 16 — the person's key goes into the repository, sealed, without leaving the page
  //
  // In a fresh load, and not in the shared context that every other check uses. A page's globals belong to its
  // document; this harness keeps one global across a hundred checks, and by the time these run the shared `nacl`
  // functions are no longer in the realm of the arrays the page hands them, so every call trips an
  // `instanceof Uint8Array` that says nothing about the shipped page — a browser never shares a global between two
  // documents. A second load is cheaper than a red that sends somebody looking in the wrong place.
  const sctx = loadPage(true);
  const kp = await tryRun(sctx, `(async () => {
    const k = nacl.box.keyPair();
    const b64 = (u8) => btoa(String.fromCharCode(...u8));
    return {pub: b64(k.publicKey), sec: Array.from(k.secretKey)};
  })()`);
  if (kp.err) throw new Error('the harness could not make a repository keypair: ' + kp.err);
  actions.secretPublicKey = kp.pub;
  actions.secretWrites.length = 0;
  const sealed = await tryRun(sctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    await putSecret('TRIBE_API_KEY_DEEPSEEK', 'sk-live-123456');
    return 'written';
  })()`);
  const posted = actions.secretWrites[0] || {name: '', body: {}};
  const opened = await tryRun(sctx, `(async () => {
    const raw = atob(${JSON.stringify(posted.body.encrypted_value || '')});
    const bytes = Uint8Array.from(raw, c => c.charCodeAt(0));
    const epk = bytes.subarray(0, 32);
    // The nonce is derived the way libsodium derives it, not chosen: crypto_generichash(epk || pk, 24). A harness that
    // opened with a zero nonce would agree with a page that sealed with a zero nonce, and both would be wrong in a way
    // GitHub cannot see — so the derivation here is the page's, and the page's own derivation is pinned to Python's
    // hashlib, below, which is the same algorithm libsodium uses.
    const repoPub = Uint8Array.from(atob(${JSON.stringify(kp.pub)}), c => c.charCodeAt(0));
    const nonce = blake2b((() => { const c = new Uint8Array(64); c.set(epk, 0); c.set(repoPub, 32); return c; })(), 24);
    // The third argument is the *ephemeral* key, not the repository's: a sealed box is opened from the sender's
    // keypair, which the message carries in its first 32 bytes. Passing the repository's own key there is what a
    // person would try first, and it fails as "cannot open". That is also why this harness is not the last word:
    // lab/seal-check.mjs hands the page's output to libsodium itself, which is the only thing that can say whether
    // the runner will be able to open it.
    const pt = nacl.box.open(bytes.subarray(32), nonce, epk, new Uint8Array(${JSON.stringify(kp.sec)}));
    const zero = nacl.box.open(bytes.subarray(32), new Uint8Array(24), epk, new Uint8Array(${JSON.stringify(kp.sec)}));
    return {pt: pt ? String.fromCharCode(...pt) : null, zeroOpens: !!zero};
  })()`);
  check('the key is sealed with the repository\'s own key, and what is sent cannot be read without it', () => {
    if (sealed.err) return sealed.err;
    if (opened.err) return opened.err;
    if (posted.name !== 'TRIBE_API_KEY_DEEPSEEK') return 'it wrote to the wrong secret: ' + posted.name;
    if (posted.body.key_id !== 'k1') return 'the write does not name the key it was sealed with: ' + JSON.stringify(posted.body.key_id);
    const asSent = String(posted.body.encrypted_value || '');
    if (!asSent || /sk-live/.test(asSent)) return 'the key went in the clear: ' + asSent.slice(0, 60);
    if (opened.pt !== 'sk-live-123456') return 'the repository key cannot open what was sent: ' + JSON.stringify(opened);
    if (opened.zeroOpens) return 'it opens with a zero nonce too, so the derived nonce is not being used';
    return '';
  });
  // The nonce derivation, pinned to an implementation that is not this page's: Python's hashlib.blake2b, which is
  // what libsodium's crypto_generichash computes. A page and a harness that agree with each other about a wrong
  // derivation would pass every round trip above and still write a secret no runner can open.
  const digests = await tryRun(sctx, `(async () => ({
    empty: Array.from(blake2b(new Uint8Array(0), 24)),
    abc:   Array.from(blake2b(new TextEncoder().encode('abc'), 24)),
    sixtyfour: Array.from(blake2b(new TextEncoder().encode('a'.repeat(64)), 24)),
    long:  Array.from(blake2b(new TextEncoder().encode('a'.repeat(300)), 32)),
    full:  Array.from(blake2b(new TextEncoder().encode('abc'), 64))
  }))()`);
  check('the nonce is derived with real BLAKE2b — checked against hashlib, not against itself', () => {
    if (digests.err) return digests.err;
    const want = {
      empty: 'ab3b5331a7135ed50d0f182d026e60abdb3646fd51bcf8a3',
      abc: '56a17e38cc371a46b12c32f18e0c61de2a84e9c2555b114e',
      sixtyfour: '2c91b27f14d18e8f22d8d3bbb1b8686efe440e8a7299abb2',
      long: '3c1292de00a518e36823f9ff908ac2da46be38718c018713403461df077e15f6',
      full: 'ba80a53f981c4d0d6a2797b69f12f6e94c212f14685ac4b74b12bb6fdbffa2d17d87c5392aab792dc252d5de4533cc9518d38aa8dbf1925ab92386edd4009923'
    };
    const toHex = (a) => a.map(x => x.toString(16).padStart(2, '0')).join('');
    for (const [k, v] of Object.entries(want)){
      if (!v) continue;
      const got = toHex(digests[k] || []);
      if (got !== v) return k + ' is ' + got + ', hashlib says ' + v;
    }
    if ((digests.abc || []).length !== 24) return 'the digest is not 24 bytes, and a nonce must be';
    if ((digests.full || []).length !== 64) return 'a 64-byte digest fails, so the length is being faked';
    return '';
  });
  const secondWrite = await tryRun(sctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main';
    await putSecret('TRIBE_API_KEY_DEEPSEEK', 'sk-live-123456');
    return 'written';
  })()`);
  const second = (actions.secretWrites[1] || {body: {}}).body.encrypted_value || '';
  check('two writes of the same key do not look alike, so the sealed value says nothing about the key', () => {
    if (secondWrite.err) return secondWrite.err;
    if (!second) return 'the second write did not happen';
    if (second === posted.body.encrypted_value) return 'the same ciphertext twice: the sealing is not really a sealed box';
    return '';
  });

  // and the sentence a person gets when the token may not write there
  actions.secretWriteDenied = true;
  const refused = await tryRun(sctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.keys = {deepseek: {key: 'sk-x'}};
    const ok = await keepKeyInRepository('deepseek', 'keymsg');
    return {ok, said: document.getElementById('keymsg').innerHTML};
  })()`);
  actions.secretWriteDenied = false;
  check('a key the token may not write is reported as a wall with the paste that still works', () => {
    if (refused.err) return refused.err;
    if (refused.ok) return 'it reported success after a 403';
    if (!/secrets page/.test(refused.said)) return 'it does not say where the paste goes: ' + refused.said;
    if (/is in the repository now/.test(refused.said)) return 'it claims the key is in the repository: ' + refused.said;
    return '';
  });
  actions.secretPublicKey = kp.pub;
  actions.secretWrites.length = 0;
  const kept = await tryRun(sctx, `(async () => {
    S.repo = 'someone/tribe'; S.token = 't'; S.branch = 'main'; S.keys = {deepseek: {key: 'sk-y'}};
    const ok = await keepKeyInRepository('deepseek', 'keymsg');
    return {ok, said: document.getElementById('keymsg').innerHTML};
  })()`);
  check('and when it may, one press puts the key where the clock reads it — with no trip to GitHub', () => {
    if (kept.err) return kept.err;
    if (!kept.ok) return 'the press failed: ' + kept.said;
    if (!/is in the repository now/.test(kept.said)) return 'it did not say so: ' + kept.said;
    if ((actions.secretWrites[0] || {}).name !== 'TRIBE_API_KEY_DEEPSEEK') return 'it wrote the wrong name';
    return '';
  });
  actions.secretPublicKey = null;

  for (const r of results){
    if (r.ok) console.log('PASS  ' + r.name);
    else { bad++; console.log('FAIL  ' + r.name + (r.why ? '\n        ' + r.why : '')); }
  }
  console.log(`\n${results.length - bad}/${results.length} checks passed`);
  if (bad) process.exitCode = 1;
}

await main();
