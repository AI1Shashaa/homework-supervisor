/**
 * 作业监督助手 Service Worker
 * 支持离线缓存，脱离电脑独立使用
 */

const CACHE_NAME = 'homework-supervisor-v1';

/** 需要缓存的资源列表 */
const ASSETS_TO_CACHE = [
  '/homework-supervisor.html',
  '/manifest.json'
];

/** 需要网络缓存的 CDN 资源（域名匹配） */
const CDN_CACHE_PATTERN = /^https:\/\/cdn\.jsdelivr\.net/;

/**
 * 安装事件：预缓存核心资源
 */
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

/**
 * 激活事件：清理旧缓存
 */
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) => {
      return Promise.all(
        names.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

/**
 * 请求拦截策略：
 * - 核心资源：优先缓存，离线可用
 * - CDN 资源：缓存优先，网络回退
 * - 其他请求：网络优先
 */
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // 核心资源：缓存优先
  if (ASSETS_TO_CACHE.includes(url.pathname)) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request).then((response) => {
          return caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, response.clone());
            return response;
          });
        });
      })
    );
    return;
  }

  // CDN 资源：缓存优先（face-api 模型等）
  if (CDN_CACHE_PATTERN.test(url.origin)) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request).then((response) => {
          if (response.ok) {
            return caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, response.clone());
              return response;
            });
          }
          return response;
        });
      }).catch(() => new Response('离线模式，资源不可用', { status: 503 }))
    );
    return;
  }

  // 其他请求：网络优先
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});
