/* Turns the ?code= GitHub hands back into an access token.
 *
 * This is the whole reason AIT needs a server at all: the exchange requires the client secret, and a
 * page cannot keep a secret. Nothing else about an owner's tribe passes through here — no member, no
 * repository, no key, no usage. It takes one code and gives back one token, and it logs neither.
 *
 * The client id below is public on purpose; it is in the page as well. The secret lives in the site's
 * environment as GH_CLIENT_SECRET and is never sent anywhere but github.com.
 */
const CLIENT_ID = 'Ov23liKyiakrCEg8jTn9';

const CORS = {
  'access-control-allow-origin': '*',
  'access-control-allow-headers': 'content-type',
  'access-control-allow-methods': 'POST, OPTIONS',
};

const reply = (status, body) => ({
  statusCode: status,
  headers: { ...CORS, 'cache-control': 'no-store', 'content-type': 'application/json' },
  body: JSON.stringify(body),
});

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') return { statusCode: 204, headers: CORS, body: '' };
  if (event.httpMethod !== 'POST') return reply(405, { error: 'POST only' });

  let code = '';
  try { code = String(JSON.parse(event.body || '{}').code || '').trim(); } catch (e) { /* fall through */ }
  // A GitHub code is short and alphanumeric. Anything else is not a code, and must not be forwarded,
  // or this function becomes a proxy for arbitrary requests to github.com.
  if (!/^[A-Za-z0-9]{8,64}$/.test(code)) return reply(400, { error: 'that is not a code' });

  const secret = process.env.GH_CLIENT_SECRET;
  if (!secret) return reply(500, { error: 'GH_CLIENT_SECRET is not set on this site' });

  let data = {};
  try {
    const r = await fetch('https://github.com/login/oauth/access_token', {
      method: 'POST',
      headers: { 'content-type': 'application/json', accept: 'application/json' },
      body: JSON.stringify({ client_id: CLIENT_ID, client_secret: secret, code }),
    });
    data = await r.json();
  } catch (e) {
    return reply(502, { error: 'could not reach github', detail: String(e.message || e) });
  }

  if (!data.access_token) {
    return reply(400, { error: data.error || 'github did not return a token', detail: data.error_description || '' });
  }
  return reply(200, { access_token: data.access_token, scope: data.scope || '' });
};
