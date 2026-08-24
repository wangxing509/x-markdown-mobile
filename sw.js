/* Service Worker：离线缓存核心应用外壳，支持自动刷新数据缓存
 *
 * v2 变更：
 *  - 缓存版本提升到 xmd-v2 / xmd-data-v2，安装后自动清除旧缓存（xmd-v1/…），
 *    避免手机端一直沿用旧应用外壳（旧外壳用单文件 articles/<id>.json 读文章，
 *    与新数据目录 c*.json 不兼容，导致知识库列表能见、点进正文却 404/空白）。
 *  - HTML/导航请求改为「网络优先、缓存兜底」，保证每次部署后手机端能拿到最新
 *    index.html（其引用的 JS/CSS 带内容哈希），从而加载最新的应用代码。
 */
const CACHE = 'xmd-v2'
const DATA_CACHE = 'xmd-data-v2'

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
  // 只处理同源请求
  if (url.origin !== self.location.origin) return

  // 数据请求：网络优先，回退缓存（实现“刷新”语义）
  if (url.pathname.includes('/data/')) {
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          if (res.ok) {
            const clone = res.clone()
            caches.open(DATA_CACHE).then((c) => c.put(e.request, clone))
          }
          return res
        })
        .catch(() => caches.match(e.request).then((m) => m || Response.error()))
    )
    return
  }

  // HTML / 导航请求：网络优先，缓存兜底（保证拿到最新应用外壳）
  if (e.request.mode === 'navigate' || url.pathname.endsWith('.html')) {
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          if (res.ok) {
            const clone = res.clone()
            caches.open(CACHE).then((c) => c.put(e.request, clone))
          }
          return res
        })
        .catch(() => caches.match(e.request).then((m) => m || Response.error()))
    )
    return
  }

  // 其余静态资源（带内容哈希的 JS/CSS/图片等）：缓存优先，网络回填
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
