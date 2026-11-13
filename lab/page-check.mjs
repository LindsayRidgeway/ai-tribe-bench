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
const dispatches = [];            // every workflow_dispatch, with the inputs the page sent it
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
  if (/^\/repos\/[^/]+\/[^/]+\/actions\/workflows\/[^/]+\/dispatches$/.test(p)){
    // A dispatch answers with nothing but a 204, so the inputs are kept here: a form that fills the wrong
    // field is invisible from the page and from the run's conclusion, and only this can say it happened.
    let inputs = {};
    try { inputs = JSON.parse(init.body || '{}').inputs || {}; } catch(e){ inputs = {}; }
    dispatches.push({workflow: decodeURIComponent(p.split('/')[6] || ''), inputs});
    return jsonResponse(204, {});
  }
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
  files.clear(); failWrites.clear(); calls.length = 0; dispatches.length = 0; store.clear();
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
