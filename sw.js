// 服务工作者：让页面离线也能打开（PWA 的一部分）
// 策略：网络优先——先请求最新内容，请求失败时回退到缓存。
const CACHE = "daily-fable-v2";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    fetch(e.request)
      .then((resp) => {
        // 请求成功：写入缓存供离线使用
        const copy = resp.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        return resp;
      })
      .catch(() =>
        // 请求失败（离线）：回退缓存，最终回退页面本身
        caches.match(e.request).then((hit) => hit || caches.match("index.html"))
      )
  );
});
