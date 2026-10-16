// Kobra – Git-Proxy fuer Cloudflare Workers (kostenlos).
// Browser duerfen nicht direkt mit GitHub-Git sprechen (CORS). Dieser Worker
// leitet ausschliesslich Git-Anfragen an github.com/gitlab.com/codeberg.org
// weiter und ergaenzt die noetigen CORS-Kopfzeilen.
//
// Optional: Unter Settings -> Variables die Variable ALLOWED_ORIGINS setzen,
// z. B. "https://deinname.github.io", damit nur deine Kobra-Seite den Proxy nutzt.

const ALLOW_HEADERS = [
  'accept', 'accept-encoding', 'accept-language', 'authorization', 'cache-control', 'content-type',
  'git-protocol', 'pragma', 'range', 'user-agent', 'x-authorization', 'x-http-method-override', 'x-requested-with',
];
const EXPOSE_HEADERS = [
  'accept-ranges', 'age', 'cache-control', 'content-length', 'content-language', 'content-type', 'date', 'etag',
  'expires', 'last-modified', 'location', 'pragma', 'server', 'vary', 'x-github-request-id', 'x-redirected-url',
];
const HOSTS = ['github.com', 'gitlab.com', 'codeberg.org', 'bitbucket.org'];

function cors(origin) {
  return {
    'Access-Control-Allow-Origin': origin || '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': ALLOW_HEADERS.join(', '),
    'Access-Control-Expose-Headers': EXPOSE_HEADERS.join(', '),
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin',
  };
}

function isGitRequest(method, target) {
  const p = target.pathname;
  const q = target.search;
  if (method === 'GET' && /\/info\/refs$/.test(p) && /service=git-(upload|receive)-pack/.test(q)) return true;
  if (method === 'POST' && /\/git-(upload|receive)-pack$/.test(p)) return true;
  return false;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get('Origin') || '';
    const allowed = String(env?.ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
    if (allowed.length && origin && !allowed.includes(origin)) {
      return new Response('Diese Seite darf den Proxy nicht benutzen.', { status: 403 });
    }
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(origin) });
    if (url.pathname === '/' || url.pathname === '') {
      return new Response('Kobra Git-Proxy läuft.', { headers: { 'content-type': 'text/plain; charset=utf-8', ...cors(origin) } });
    }

    let target;
    try { target = new URL(`https://${url.pathname.slice(1)}${url.search}`); }
    catch (e) { return new Response('Ungültige Adresse', { status: 400, headers: cors(origin) }); }
    if (!HOSTS.includes(target.hostname) || !isGitRequest(request.method, target)) {
      return new Response('Nur Git-Anfragen an GitHub, GitLab, Codeberg oder Bitbucket sind erlaubt.', { status: 403, headers: cors(origin) });
    }

    const headers = new Headers();
    for (const name of ALLOW_HEADERS) {
      const v = request.headers.get(name);
      if (v) headers.set(name, v);
    }
    if (!/^git\//.test(headers.get('user-agent') || '')) headers.set('user-agent', 'git/kobra-proxy');

    const upstream = await fetch(target.toString(), {
      method: request.method,
      headers,
      body: request.method === 'POST' ? request.body : undefined,
      redirect: 'follow',
    });

    const out = new Headers(cors(origin));
    for (const name of EXPOSE_HEADERS) {
      const v = upstream.headers.get(name);
      if (v) out.set(name, v);
    }
    if (upstream.redirected) out.set('x-redirected-url', upstream.url);
    return new Response(upstream.body, { status: upstream.status, statusText: upstream.statusText, headers: out });
  },
};
