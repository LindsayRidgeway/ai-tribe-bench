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
const calls = [];                 // every request, for the failure messages to be specific
const actions = { runs: [], onPoll: null };   // what the Actions API answers, and what a run does while it runs

function shaOf(text, n = 0){
  return crypto.createHash('sha1').update(text + ':' + n).digest('hex');
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
  if (/^\/repos\/[^/]+\/[^/]+\/actions\/workflows\/[^/]+\/dispatches$/.test(p))
    return jsonResponse(204, {});
  if (/^\/repos\/[^/]+\/[^/]+\/actions\/runs$/.test(p)){
    // A run does its work between the dispatch and the poll: the callback stands in for the runner.
    if (actions.onPoll){ const once = actions.onPoll; actions.onPoll = null; once(files); }
    return jsonResponse(200, {workflow_runs: actions.runs.slice()});
  }

  const m = p.match(/^\/repos\/([^/]+)\/([^/]+)(?:\/contents\/?(.*))?$/);
  if (!m) return jsonResponse(404, {message: 'Not Found'});
  const rest = m[3] || '';
  if (!rest) return jsonResponse(200, {full_name: m[1] + '/' + m[2], default_branch: 'main'});

  if (method === 'GET'){
    if (files.has(rest)) return jsonResponse(200, {content: Buffer.from(files.get(rest).text).toString('base64'),
                                                  sha: files.get(rest).sha, path: rest});
    const dir = listing(rest);
    if (dir.length) return jsonResponse(200, dir);
    return jsonResponse(404, {message: 'Not Found'});
  }

  if (method === 'PUT'){
    if (failWrites.has(rest)) return jsonResponse(500, {message: 'the repository said no'});
    const body = JSON.parse(init.body || '{}');
    const text = Buffer.from(String(body.content || ''), 'base64').toString('utf8');
    const prev = files.get(rest);
    if (body.sha && prev && body.sha !== prev.sha) return jsonResponse(409, {message: 'sha does not match'});
    if (body.sha && !prev) return jsonResponse(409, {message: 'sha does not match'});
    files.set(rest, {text, sha: shaOf(text, files.size + 1)});
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
    dataset: {}, style: {}, files: [], href: '', download: '',
    classList: {add(){}, remove(){}, toggle(){}, contains(){ return false; }},
    appendChild(){}, removeChild(){}, remove(){}, click(){}, focus(){}, blur(){},
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

const location = {hash: '', search: '', pathname: '/ait.html', href: 'http://localhost/ait.html',
                  replaceState(){}, assign(){}};

const sandbox = {
  console, document, localStorage, location, fetch: null, setInterval, clearInterval,
  // The page waits three seconds between polls of the run list. A harness that waited would spend its life asleep,
  // and the wait is not what is being tested — the answer is.
  setTimeout: (fn) => setTimeout(fn, 0), clearTimeout,
  TextEncoder, TextDecoder, URL, URLSearchParams, Blob: class {}, atob, btoa, structuredClone,
  crypto: {randomUUID: () => crypto.randomUUID()},
  alert(){}, confirm(){ return true; }, prompt(){ return ''; },
  navigator: {userAgent: 'node', clipboard: {writeText: async () => {}}},
  history: {replaceState(){}, pushState(){}},
  addEventListener(){}, removeEventListener(){}, matchMedia: () => ({matches: false, addEventListener(){}}),
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.fetch = async (url, init = {}) => {
  const u = String(url);
  if (u.startsWith('https://api.github.com')) return githubFetch(u, init);
  if (/\/chat\/completions$/.test(u)) return sseResponse(MEMBER_ENTRY);
  return jsonResponse(404, {message: 'this harness does not answer ' + u});
};

/* ---- run the page ---------------------------------------------------------------------- */

export function loadPage(){
  const html = fs.readFileSync(PAGE, 'utf8');
  const m = html.match(/<script>([\s\S]*?)<\/script>/);
  if (!m) throw new Error('ait.html has no script — did the page move?');
  const context = vm.createContext(sandbox);
  vm.runInContext(m[1], context, {filename: 'ait.html'});
  return context;
}

const run = (context, code) => vm.runInContext(code, context);
const text = (p) => (files.get(p) || {}).text;

/* ---- the checks ------------------------------------------------------------------------ */

const results = [];
function check(name, fn){
  try { const why = fn(); results.push({name, ok: !why, why: why || ''}); }
  catch(e){ results.push({name, ok: false, why: 'threw: ' + (e && e.message)}); }
}

function reset(){
  files.clear(); failWrites.clear(); calls.length = 0; store.clear();
  actions.runs.length = 0; actions.onPoll = null;
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
  const runObject = (id, event) => ({id, name: 'clock', event, status: 'completed', conclusion: 'success',
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

  /* the verdict */
  let bad = 0;
  for (const r of results){
    if (r.ok) console.log('PASS  ' + r.name);
    else { bad++; console.log('FAIL  ' + r.name + (r.why ? '\n        ' + r.why : '')); }
  }
  console.log(`\n${results.length - bad}/${results.length} checks passed`);
  if (bad) process.exitCode = 1;
}

await main();
