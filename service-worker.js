/* Manager Online — Service Worker (GitHub Pages)
   Troque a versão abaixo a cada publicação para forçar atualização do cache. */
const VERSAO = 'manager-online-v1';
const CACHE_APP = VERSAO + '-app';
const CACHE_IMG = VERSAO + '-img';
const PAGINA = 'Manager_v2_0_Fase0_Online_Identidade_Real.html';
const PRE = ['./', PAGINA, 'index.html', 'manifest.json', 'firebase-config.js',
  'icons/icon-192.png', 'icons/icon-512.png', 'icons/icon-maskable-512.png',
  'icons/apple-touch-icon.png', 'icons/favicon-32.png'];
const HOSTS_IMG = ['flagcdn.com', 'upload.wikimedia.org', 'thumb.wikimedia.org'];
const MAX_IMG = 500;

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const c = await caches.open(CACHE_APP);
    await Promise.allSettled(PRE.map(u => c.add(new Request(u, { cache: 'reload' }))));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const ks = await caches.keys();
    await Promise.all(ks.filter(k => !k.startsWith(VERSAO)).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

async function limita(cache) {
  const ks = await cache.keys();
  if (ks.length > MAX_IMG) await Promise.all(ks.slice(0, ks.length - MAX_IMG).map(k => cache.delete(k)));
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Firebase, SDK e qualquer outro domínio: não mexe (sempre rede)
  if (url.origin !== location.origin) {
    if (!HOSTS_IMG.includes(url.hostname) || req.destination !== 'image') return;
    e.respondWith((async () => {
      const c = await caches.open(CACHE_IMG);
      const hit = await c.match(req.url);
      if (hit) return hit;
      try { // CORS para não gravar resposta "opaca" (que ocupa muito espaço)
        const r = await fetch(req.url, { mode: 'cors', credentials: 'omit' });
        if (r.ok) { c.put(req.url, r.clone()); limita(c); }
        return r;
      } catch (err) { return fetch(req); }
    })());
    return;
  }

  // Página/HTML: rede primeiro (pega atualizações), cache se estiver offline
  if (req.mode === 'navigate' || url.pathname.endsWith('.html') || url.pathname.endsWith('/')) {
    e.respondWith((async () => {
      const c = await caches.open(CACHE_APP);
      try {
        const r = await fetch(req);
        if (r.ok) c.put(url.pathname.endsWith('/') ? './' : req, r.clone());
        return r;
      } catch (err) {
        return (await c.match(req, { ignoreSearch: true })) || (await c.match(PAGINA)) || (await c.match('./')) || Response.error();
      }
    })());
    return;
  }

  // Arquivos estáticos do próprio site (ícones, manifest, escudos): cache + atualização em segundo plano
  e.respondWith((async () => {
    const c = await caches.open(CACHE_APP);
    const hit = await c.match(req);
    const rede = fetch(req).then(r => { if (r.ok) c.put(req, r.clone()); return r }).catch(() => null);
    return hit || (await rede) || Response.error();
  })());
});

self.addEventListener('message', e => { if (e.data === 'SKIP_WAITING') self.skipWaiting(); });
