// ============================================================================
//  KIAN V2Ray — Subscription Gist Proxy (Cloudflare Worker)
//  ---------------------------------------------------------------------------
//  سرور کاربر به این Worker POST می‌زند؛ Worker با توکن خصوصیِ Gist (که فقط در
//  env-secret خودش است) برای هر کاربر یک secret gist می‌سازد/آپدیت/حذف می‌کند و
//  لینک‌های HTTPS را برمی‌گرداند. توکن Gist هرگز روی سرور کاربر یا در ریپو نیست.
//
//  env:
//    GIST_TOKEN  (secret)  — توکن گیت‌هاب با scope=gist
//    KV          (binding) — namespace برای نگاشت install_id:subtoken → gist_id
//
//  Endpoints:
//    GET  /                → سلامت
//    POST /sync            → body: { install_id, items: { "<subtoken>": "<base64 content>" } }
//                            خروجی: { ok, urls: { "<subtoken>": "<https url>" } }
//    POST /delete          → body: { install_id }  → همهٔ گیست‌های آن نصب پاک می‌شوند
//  امنیت: install_id یک رشتهٔ تصادفی است که فقط سرور کاربر می‌داند؛ هر نصب فقط
//         به گیست‌های خودش دسترسی دارد (کلید KV با install_id پیشوند می‌شود).
// ============================================================================

const GH = "https://api.github.com";
const UA = "kian-sub-worker/1.0";

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}

async function gh(method, path, token, body) {
  const res = await fetch(GH + path, {
    method,
    headers: {
      "Authorization": "token " + token,
      "Accept": "application/vnd.github+json",
      "User-Agent": UA,
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = {};
  const txt = await res.text();
  if (txt) { try { data = JSON.parse(txt); } catch { data = { raw: txt }; } }
  return { status: res.status, data };
}

function validId(s) { return typeof s === "string" && /^[A-Za-z0-9_-]{8,128}$/.test(s); }
function validTok(s) { return typeof s === "string" && /^[A-Za-z0-9_-]{8,64}$/.test(s); }

async function getLogin(token) {
  const r = await gh("GET", "/user", token);
  return r.status === 200 ? (r.data.login || "") : "";
}

function stableUrl(login, gid) {
  return `https://gist.githubusercontent.com/${login}/${gid}/raw/sub.txt`;
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return json({ ok: true });
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/") {
      return json({ ok: true, service: "kian-sub-worker", ts: Date.now() });
    }

    if (request.method === "POST" && url.pathname === "/sync") {
      let body;
      try { body = await request.json(); } catch { return json({ ok: false, error: "bad json" }, 400); }
      const installId = body.install_id;
      const items = body.items || {};
      if (!validId(installId)) return json({ ok: false, error: "bad install_id" }, 400);
      const token = env.GIST_TOKEN;
      if (!token) return json({ ok: false, error: "server token missing" }, 500);

      const login = await getLogin(token);
      if (!login) return json({ ok: false, error: "gist auth failed" }, 502);

      const urls = {};
      const seen = [];
      for (const [subtok, content] of Object.entries(items)) {
        if (!validTok(subtok) || typeof content !== "string") continue;
        seen.push(subtok);
        const kvKey = `${installId}:${subtok}`;
        let gid = await env.KV.get(kvKey);
        let ok = false;
        if (gid) {
          const r = await gh("PATCH", `/gists/${gid}`, token, { files: { "sub.txt": { content } } });
          ok = r.status === 200 || r.status === 201;
        }
        if (!ok) {
          const r = await gh("POST", "/gists", token, {
            description: "kian-v2ray sub", public: false,
            files: { "sub.txt": { content } },
          });
          if (r.status === 200 || r.status === 201) {
            const newGid = r.data.id;
            // race-condition guard: یک درخواست همزمان دیگر شاید قبلاً نوشته باشد.
            // اگر KV الان مقدار دیگری دارد، gist تازه‌ساخته را حذف کن و از winner استفاده کن.
            const winner = await env.KV.get(kvKey);
            if (winner && winner !== newGid) {
              await gh("DELETE", `/gists/${newGid}`, token);
              gid = winner;
              // محتوا را روی winner ست کن تا مطمئن باشیم محتوای کاربر آنجاست
              await gh("PATCH", `/gists/${gid}`, token, { files: { "sub.txt": { content } } });
            } else {
              gid = newGid;
              await env.KV.put(kvKey, gid);
            }
            ok = true;
          }
        }
        if (ok && gid) urls[subtok] = stableUrl(login, gid);
      }

      // حذف گیست‌هایی که دیگر در items نیستند (کاربر حذف‌شده)
      const idxKey = `${installId}::index`;
      let prevList = [];
      try { prevList = JSON.parse((await env.KV.get(idxKey)) || "[]"); } catch { prevList = []; }
      for (const oldTok of prevList) {
        if (seen.includes(oldTok)) continue;
        const kvKey = `${installId}:${oldTok}`;
        const gid = await env.KV.get(kvKey);
        if (gid) {
          await gh("DELETE", `/gists/${gid}`, token);
          await env.KV.delete(kvKey);
        }
      }
      await env.KV.put(idxKey, JSON.stringify(seen));

      return json({ ok: true, urls });
    }

    if (request.method === "POST" && url.pathname === "/delete") {
      let body;
      try { body = await request.json(); } catch { return json({ ok: false, error: "bad json" }, 400); }
      const installId = body.install_id;
      if (!validId(installId)) return json({ ok: false, error: "bad install_id" }, 400);
      const token = env.GIST_TOKEN;
      const idxKey = `${installId}::index`;
      let list = [];
      try { list = JSON.parse((await env.KV.get(idxKey)) || "[]"); } catch { list = []; }
      let n = 0;
      for (const tok of list) {
        const kvKey = `${installId}:${tok}`;
        const gid = await env.KV.get(kvKey);
        if (gid) { await gh("DELETE", `/gists/${gid}`, token); await env.KV.delete(kvKey); n++; }
      }
      await env.KV.delete(idxKey);
      return json({ ok: true, deleted: n });
    }

    return json({ ok: false, error: "not found" }, 404);
  },
};
