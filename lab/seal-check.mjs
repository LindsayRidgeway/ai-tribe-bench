/* seal-check.mjs — the page seals a secret, and libsodium itself opens it.

   Why this is separate from page-check.mjs. `page-check` can prove that the page's sealed value round-trips through
   the harness's *own copy* of tweetnacl, and that its BLAKE2b matches Python's hashlib. Neither proves the thing that
   matters: that the runner GitHub starts can decrypt what a person's browser sent. It cannot, because a page and a
   harness that agree about a wrong nonce, or a wrong key, agree perfectly. The only authority on a libsodium sealed
   box is libsodium, so this script hands the page's output to it.

   What it does. Loads the real `ait.html` in a fake browser (as page-check does), makes a keypair, seals a known
   string with `sealForRepository`, and then calls the system libsodium's `crypto_box_seal_open` — the same call the
   runner makes — through Python's ctypes. Prints the plaintext, and exits non-zero if libsodium could not open it.

   This is how the zero-nonce bug that was in the first draft of the seal would have been caught: that version
   round-tripped inside this repository, and no version could ever have been opened by GitHub.

   Run: node lab/seal-check.mjs
   Needs: a libsodium shared library (brew: `brew install libsodium`; mac arm64 path used by default).
*/
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const PAGE = path.join(HERE, '..', 'ait.html');
const PLAINTEXT = 'sk-live-123456';

// Just enough browser for the page to load: it runs its own boot code at the end of the script, and that code wires
// up elements it will never find here. Everything it asks for exists and does nothing.
const noop = () => {};
const element = () => ({
  innerHTML: '', textContent: '', value: '', style: {}, dataset: {}, children: [], firstChild: null, parentNode: null,
  classList: {add: noop, remove: noop, toggle: noop, contains: () => false},
  appendChild: noop, addEventListener: noop, removeEventListener: noop, focus: noop, click: noop,
  setAttribute: noop, remove: noop, querySelector: () => null, querySelectorAll: () => [], closest: () => null,
});
const document = {
  getElementById: () => element(), querySelector: () => null, querySelectorAll: () => [],
  createElement: () => element(), addEventListener: noop, removeEventListener: noop, cookie: '',
  body: {appendChild: noop, addEventListener: noop}, head: {appendChild: noop}, documentElement: {setAttribute: noop},
};
const store = new Map();
const sandbox = {
  console, document, TextEncoder, TextDecoder, atob, btoa, URL, URLSearchParams,
  localStorage: {getItem: (k) => (store.has(k) ? store.get(k) : null), setItem: (k, v) => store.set(k, String(v)),
                  removeItem: (k) => store.delete(k), clear: () => store.clear()},
  location: {hash: '', search: '', pathname: '/ait.html', href: 'http://localhost/ait.html', host: 'kythe.app',
             replace: noop, replaceState: noop, assign: noop},
  crypto: {getRandomValues: (u8) => globalThis.crypto.getRandomValues(u8)},
  navigator: {userAgent: 'node'}, history: {replaceState: noop, pushState: noop},
  setTimeout: (fn) => setTimeout(fn, 0), clearTimeout, setInterval: () => 0, clearInterval: noop,
  addEventListener: noop, removeEventListener: noop,
  fetch: async () => ({ok: true, status: 200, json: async () => ({}), text: async () => ''}),
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
const context = vm.createContext(sandbox);
vm.runInContext('this.self = this;', context);
const blocks = [...fs.readFileSync(PAGE, 'utf8').matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
vm.runInContext(blocks.join('\n;\n'), context, {filename: 'ait.html'});

const made = await vm.runInContext(`(() => {
  const k = nacl.box.keyPair();
  const b64 = (u8) => btoa(String.fromCharCode(...u8));
  return {pub: b64(k.publicKey), sec: b64(k.secretKey), sealed: sealForRepository(${JSON.stringify(PLAINTEXT)}, k.publicKey)};
})()`, context);

const open = `
import ctypes, json, base64, sys
d = json.load(sys.stdin)
candidates = ['libsodium.dylib', '/opt/homebrew/lib/libsodium.dylib', '/usr/local/lib/libsodium.dylib', 'libsodium.so.23', 'libsodium.so']
lib = None
for c in candidates:
    try:
        lib = ctypes.CDLL(c); break
    except OSError:
        continue
if lib is None:
    print('NO-LIBSODIUM'); sys.exit(0)
lib.sodium_init()
pub = base64.b64decode(d['pub']); sec = base64.b64decode(d['sec']); sealed = base64.b64decode(d['sealed'])
m = ctypes.create_string_buffer(len(sealed))
rc = lib.crypto_box_seal_open(m, sealed, ctypes.c_ulonglong(len(sealed)), pub, sec)
if rc != 0:
    print('CANNOT-OPEN'); sys.exit(1)
print(m.raw[:len(${JSON.stringify(PLAINTEXT)})].decode())
`;

let verdict = '';
try {
  verdict = execFileSync('python3', ['-c', open], {input: JSON.stringify(made), encoding: 'utf8'}).trim();
} catch (e) {
  verdict = 'CANNOT-OPEN';
  if (e.stderr) process.stderr.write(String(e.stderr));
}
if (verdict === 'NO-LIBSODIUM'){
  console.log('SKIPPED  no libsodium on this machine, so nothing was verified. Install it and run again — this check');
  console.log('         is the only one that can tell a real sealed box from one this repository likes.');
  process.exit(0);
}
if (verdict !== PLAINTEXT){
  console.log('FAIL  libsodium could not open the page\'s sealed box, so no runner could: ' + verdict);
  process.exit(1);
}
console.log('PASS  libsodium opened the page\'s sealed box: the runner will read this secret, and the page never had');
console.log('      to send the key anywhere to put it there.');
