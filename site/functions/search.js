/* One search, no key, for a member who needs an address it does not know.
 *
 * Why this exists: the fetch function can read a page but cannot find one. A member asked to look
 * something up had only two moves — guess an address, or explain that it could not. That is a harness
 * limit talking, not a limit of the mind using it.
 *
 * How: Bing's RSS form returns the ten results a search page would show, as a 5 KB document. No key,
 * no API account, nothing to sign up for, and nothing to break in six months but the shape of an
 * <item>. If it does break, the member is told the search failed, which is honest.
 *
 * What this holds: nothing. No key, no tribe, no per-person state, no history of what was searched.
 */
const MAX_Q = 200;
const TIMEOUT_MS = 10_000;
const UA = 'AIT/1 (a member of a household looking something up; +https://ai-tribe.netlify.app)';

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

const plain = (s) => String(s || '')
  .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1')
  .replace(/<[^>]+>/g, '')
  .replace(/&nbsp;/g, ' ').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&')
  .replace(/\s+/g, ' ').trim();

const field = (item, tag) => {
  const m = item.match(new RegExp('<' + tag + '>([\\s\\S]*?)</' + tag + '>'));
  return m ? plain(m[1]) : '';
};

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') return { statusCode: 204, headers: { 'access-control-allow-origin': '*' }, body: '' };
  const q = ((event.queryStringParameters && event.queryStringParameters.q) || '').trim();
  if (!q) return json(400, { error: 'give a search as ?q=' });
  if (q.length > MAX_Q) return json(400, { error: 'that search is too long' });

  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), TIMEOUT_MS);
  try {
    const url = 'https://www.bing.com/search?format=rss&count=10&q=' + encodeURIComponent(q);
    const r = await fetch(url, {
      signal: ctl.signal,
      headers: { 'user-agent': UA, accept: 'application/rss+xml, application/xml;q=0.9, text/xml;q=0.8' },
    });
    if (!r.ok) return json(502, { error: 'the search engine answered ' + r.status });
    const xml = await r.text();
    const results = [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)]
      .slice(0, 10)
      .map(m => ({ title: field(m[1], 'title'), url: field(m[1], 'link'), text: field(m[1], 'description') }))
      .filter(x => /^https?:\/\//i.test(x.url));
    if (!results.length) return json(502, { error: 'the search engine returned nothing readable' });

    // The text a member reads: numbered, an address it can FETCH, and one line of why it might matter.
    const text = results.map((x, i) => `${i + 1}. ${x.title}\n   ${x.url}\n   ${x.text}`.slice(0, 700)).join('\n\n');
    return json(200, { query: q, results, text }, true);
  } catch (e) {
    const why = e.name === 'AbortError' ? 'the search engine did not answer in time' : String(e.message || e);
    return json(502, { error: why });
  } finally {
    clearTimeout(timer);
  }
};
