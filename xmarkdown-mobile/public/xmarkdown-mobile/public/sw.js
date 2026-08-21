/* Service Worker：离线缓存核心应用外壳，支持自动刷新数据缓存 */
const CACHE = 'xmd-v1'
const DATA_CACHE = 'xmd-data-v1'

self.addEventListener('install', (e) => {
  self.skipWaiting()
})

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE && k !== DATA_CACHE).map((k) => caches.delete(k)))
    )
  )
  self.clients.claim()
})

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url)
  // 数据请求：网络优先，回退缓存（实现“刷新”语义）
  if (url.pathname.includes('/data/')) {
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          const clone = res.clone()
          caches.open(DATA_CACHE).then((c) => c.put(e.request, clone))
          return res
        })
        .catch(() => caches.match(e.request).then((m) => m || Response.error()))
    )
    return
  }
  // 应用外壳：缓存优先，网络回填
  e.respondWith(
    caches.match(e.request).then((cached) => {
      const network = fetch(e.request)
        .then((res) => {
          if (res.ok) {
            const clone = res.clone()
            caches.open(CACHE).then((c) => c.put(e.request, clone))
          }
          return res
        })
        .catch(() => cached)
      return cached || network
    })
  )
})
