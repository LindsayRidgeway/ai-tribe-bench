/* Fetch one public page for a member and hand back its text.
 *
 * Why this exists: a browser cannot read most of the web. Sites refuse cross-origin reads, and no
 * header on our side changes that. A member asking "what does this page say" needs something that
 * fetches from outside a browser — and it must be the smallest thing that does the job.
 *
 * What this holds: nothing. No key, no tribe, no storage, no memory between calls. It takes a URL,
 * fetches it, returns the text, and forgets. The engine key stays in the owner's browser where it
 * belongs, so this can never become a place where keys accumulate.
 *
 * What it refuses: anything that is not http(s), and anything that resolves to a private or link-local
 * address — otherwise the function could be used to read its own network, which is the classic way a
 * proxy becomes an intrusion. Two limits remain and are stated rather than hidden: it follows
 * redirects (a public URL may redirect into a private one), and DNS can be made to change between the
 * check and the fetch. For a page that reads public articles for a household, both are acceptable; for
 * a bank they would not be.
 */
const MAX_BYTES = 1_500_000;    // a modern article page is mostly scripts; cap high, then strip them
const TIMEOUT_MS = 12_000;

const PRIVATE = /^(localhost|127\.\d|0\.\d|10\.\d|169\.254\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|metadata\.|\[?::1\]?$)/i;

const json = (status, body, cache) => ({
  statusCode: status,
  headers: {
    'content-type': 'application/json',
    'access-control-allow-origin': '*',
    'cache-control': cache ? 'public, max-age=900' : 'no-store',
    ...(cache ? { 'netlify-cdn-cache-control': 'public, max-age=900' } : {}),
  },
  body: JSON.stringify(body),
});

exports.handler = async (event) => {
  const raw = (event.queryStringParameters && event.queryStringParameters.url) || '';
  let u;
  try { u = new URL(raw); } catch (e) { return json(400, { error: 'that is not a URL' }); }
  if (!/^https?:$/.test(u.protocol)) return json(400, { error: 'http and https only' });
  if (PRIVATE.test(u.hostname)) return json(400, { error: 'that address is not public' });

  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), TIMEOUT_MS);
  try {
    const r = await fetch(u.toString(), {
      redirect: 'follow',
      signal: ctl.signal,
      headers: {
        'user-agent': 'AIT/1 (a member of a household reading a page; +https://ai-tribe.netlify.app)',
        accept: 'text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5',
      },
    });
    const buf = await r.arrayBuffer();
    const type = r.headers.get('content-type') || '';
    // A PDF or an image is not something this harness can read, and handing a member its bytes wastes a
    // look-up and teaches it nothing. Say what it is instead, and let it choose a text page.
    if (type && !/text\/|json|xml|javascript/i.test(type)) {
      return json(415, {
        error: 'that address is ' + type.split(';')[0] + ', which this harness cannot read — it reads text and html only',
      });
    }
    const raw = new TextDecoder('utf-8').decode(buf.slice(0, MAX_BYTES));
    // Scripts and styles are most of the bytes on a modern page and none of the words. Cut them here,
    // before the response gets large, and without touching the markup the page actually says.
    const text = raw
      .replace(/<script[\s\S]*?<\/script>/gi, ' ')
      .replace(/<style[\s\S]*?<\/style>/gi, ' ')
      .replace(/<noscript[\s\S]*?<\/noscript>/gi, ' ')
      .replace(/<svg[\s\S]*?<\/svg>/gi, ' ');
    return json(200, {
      url: r.url,
      status: r.status,
      type: r.headers.get('content-type') || '',
      truncated: buf.byteLength > MAX_BYTES,
      text,
    }, r.ok);
  } catch (e) {
    const why = e.name === 'AbortError' ? 'the page took too long' : String(e.message || e);
    return json(502, { error: why });
  } finally {
    clearTimeout(timer);
  }
};
