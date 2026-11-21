// DSH 后端半边：注册 /dsh-shipgo 面板与健康检查。
// 面板只记录检查进度，不执行脚本、不读取本地文件、不代发版。

export const name = 'dsh-shipgo';
export const inject = ['webServer'];

const PAGE_HTML = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ShipGo 发版检查单</title>
  <style>
    :root {
      --bg: #f4f6fa;
      --card: #ffffff;
      --ink: #172033;
      --muted: #6b7688;
      --line: #e4e9f1;
      --accent: #2f6fed;
      --accent-soft: #eaf0ff;
      --ok: #15803d;
      --ok-soft: #e9f7ee;
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; background: var(--bg); color: var(--ink); }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; line-height: 1.55; }
    .page { max-width: 860px; margin: 0 auto; padding: 28px 22px 48px; }
    .top { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; }
    .kicker { margin: 0 0 4px; color: var(--accent); font-size: 12px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
    h1 { margin: 0; font-size: 26px; letter-spacing: -.02em; }
    .sub { margin: 7px 0 0; color: var(--muted); font-size: 14px; }
    .pill { display: inline-block; flex: none; padding: 6px 10px; border-radius: 999px; font-size: 12px; white-space: nowrap; }
    .pill.muted { background: #eef1f6; color: var(--muted); }
    .pill.ok { background: var(--ok-soft); color: var(--ok); }
    .progress-card { margin-top: 20px; padding: 16px 18px; border: 1px solid var(--line); border-radius: 14px; background: var(--card); display: flex; align-items: center; gap: 14px; }
    .progress-card strong { font-size: 18px; }
    .progress-card span { color: var(--muted); font-size: 13px; }
    .bar { flex: 1; height: 9px; border-radius: 999px; background: #e8edf5; overflow: hidden; }
    .bar span { display: block; width: 0; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #2f6fed, #5b91ff); transition: width .2s ease; }
    button { font: inherit; cursor: pointer; border: 1px solid var(--line); background: #fff; color: var(--ink); border-radius: 9px; padding: 7px 12px; }
    button:hover { border-color: #c8d3e5; background: #f8faff; }
    .cmd { margin-top: 14px; display: flex; align-items: center; gap: 10px; padding: 11px 13px; border: 1px dashed #cbd6e8; border-radius: 11px; background: #fbfcff; }
    .cmd code { flex: 1; min-width: 0; overflow-wrap: anywhere; font-size: 12.5px; color: #334155; }
    .cmd button { flex: none; }
    .stage { margin-top: 24px; }
    .stage h2 { display: flex; align-items: baseline; gap: 9px; margin: 0 0 9px; font-size: 16px; }
    .stage h2 small { color: var(--muted); font-size: 12px; font-weight: 400; }
    .badge { display: inline-flex; align-items: center; justify-content: center; min-width: 24px; height: 24px; padding: 0 6px; border-radius: 7px; background: var(--accent-soft); color: var(--accent); font-size: 12px; font-weight: 700; }
    .list { border: 1px solid var(--line); border-radius: 12px; background: var(--card); overflow: hidden; }
    label.item { display: grid; grid-template-columns: 22px 1fr; gap: 10px; align-items: start; padding: 13px 15px; border-top: 1px solid var(--line); }
    label.item:first-child { border-top: 0; }
    label.item:hover { background: #fafcff; }
    label.item input { width: 17px; height: 17px; margin: 3px 0 0; accent-color: var(--accent); }
    label.item .txt { font-size: 14px; }
    label.item .txt small { display: block; margin-top: 3px; color: var(--muted); font-size: 12px; line-height: 1.45; }
    label.item.done .txt { color: #526079; }
    .foot { margin-top: 26px; padding-top: 18px; border-top: 1px solid var(--line); color: var(--muted); font-size: 13px; }
    .foot p { margin: 0 0 9px; }
    .links { display: flex; flex-wrap: wrap; gap: 14px; }
    .links a { color: var(--accent); text-decoration: none; }
    .links a:hover { text-decoration: underline; }
    @media (max-width: 620px) {
      .top { display: block; }
      .pill { margin-top: 10px; }
      .progress-card { flex-wrap: wrap; }
      .bar { flex-basis: 100%; order: 3; }
    }
  </style>
</head>
<body>
<div class="page">
  <div class="top">
    <div>
      <p class="kicker">GitHub-ShipGo · DSH 插件</p>
      <h1>发版检查单</h1>
      <p class="sub">按 ShipGo 的三站式流程逐项确认。进度只保存在本机浏览器，不上传、不写盘。</p>
    </div>
    <span id="health" class="pill muted">正在检测插件…</span>
  </div>

  <div class="progress-card">
    <div><strong id="count">0 / 16</strong> <span>项已确认</span></div>
    <div class="bar"><span id="bar"></span></div>
    <button id="reset" type="button">重置</button>
  </div>

  <div class="cmd">
    <code id="cmd-text">python -B -I -X utf8 scripts/fingerprints_scan.py . --check</code>
    <button id="copy" type="button">复制</button>
  </div>

  <section class="stage">
    <h2><span class="badge">0</span> 环境预检 <small>阻断式，不过不开工</small></h2>
    <div class="list">
      <label class="item"><input type="checkbox" data-id="pre-1"><span class="txt">四支脚本 <small>--selftest</small> 全 exit 0<small>en / restyle / checklist / text_quality；探针不走 --selftest。</small></span></label>
      <label class="item"><input type="checkbox" data-id="pre-2"><span class="txt">四工具联检全 PASS<small>按分册③ §2.1 的代码块实跑，结论留在文字里。</small></span></label>
      <label class="item"><input type="checkbox" data-id="pre-3"><span class="txt">指纹探针结论为「表盘一致」<small><code>fingerprints_scan.py . --check</code></small></span></label>
      <label class="item"><input type="checkbox" data-id="pre-4"><span class="txt">包版本已从 SKILL.md frontmatter 读取并自报</span></label>
    </div>
  </section>

  <section class="stage">
    <h2><span class="badge">1</span> 站一 · 发布约定 <small>问卷定约定</small></h2>
    <div class="list">
      <label class="item"><input type="checkbox" data-id="q-1"><span class="txt">固定尾句逐字出现，问数 ≤ 9，必答 3 全在</span></label>
      <label class="item"><input type="checkbox" data-id="q-2"><span class="txt">《发布约定.md》已落盘，字段齐</span></label>
    </div>
  </section>

  <section class="stage">
    <h2><span class="badge">2</span> 自动段 · 4.5–9 <small>做发布件</small></h2>
    <div class="list">
      <label class="item"><input type="checkbox" data-id="auto-1"><span class="txt">文书件已落盘<small>README 中/英、LICENSE、NOTICE、SKILL.md、llms.txt 等按项目形态齐备。</small></span></label>
      <label class="item"><input type="checkbox" data-id="auto-2"><span class="txt">README 美化、英文验收、AI 四件套已过闸</span></label>
      <label class="item"><input type="checkbox" data-id="auto-3"><span class="txt">收口 15 项逐项 PASS</span></label>
    </div>
  </section>

  <section class="stage">
    <h2><span class="badge">3</span> 站二 · 核对 <small>两问制与清理</small></h2>
    <div class="list">
      <label class="item"><input type="checkbox" data-id="review-1"><span class="txt">两问制原句出现，用户确认有记录</span></label>
      <label class="item"><input type="checkbox" data-id="review-2"><span class="txt">第三问件数＝实际多出件数，一件一行</span></label>
      <label class="item"><input type="checkbox" data-id="review-3"><span class="txt">清理清单逐件列单</span></label>
    </div>
  </section>

  <section class="stage">
    <h2><span class="badge">4</span> 收尾 · 封包 <small>哈希落账</small></h2>
    <div class="list">
      <label class="item"><input type="checkbox" data-id="pack-1"><span class="txt">封包哈希已落账，账与实算一致，件数自报</span></label>
      <label class="item"><input type="checkbox" data-id="pack-2"><span class="txt">分发 zip 已重打并验 CRC<small>skill / 仓库克隆类项目按规则登记 N/A 立牌，不拿散文说明代替。</small></span></label>
    </div>
  </section>

  <section class="stage">
    <h2><span class="badge">5</span> 站三 · 交付 <small>只前置不介入</small></h2>
    <div class="list">
      <label class="item"><input type="checkbox" data-id="deliver-1"><span class="txt">结束报告四段齐<small>做了啥 / 缺啥 / 咋补 / 等拍板。</small></span></label>
      <label class="item"><input type="checkbox" data-id="deliver-2"><span class="txt">只前置不介入的边界声明在<small>发不发、何时发、发到哪个账号，由使用者决定。</small></span></label>
    </div>
  </section>

  <div class="foot">
    <p>本面板只记录检查进度，不执行脚本、不读取本地文件、不代发版；发布决定仍由你做出。</p>
    <div class="links">
      <a href="https://github.com/OldQin-Family/GitHub-ShipGo" target="_blank" rel="noreferrer">GitHub-ShipGo 仓库</a>
      <a href="https://github.com/OldQin-Family/GitHub-ShipGo/blob/main/SKILL.md" target="_blank" rel="noreferrer">SKILL.md</a>
      <a href="https://github.com/OldQin-Family/GitHub-ShipGo/tree/main/references" target="_blank" rel="noreferrer">参考分册</a>
    </div>
  </div>
</div>

<script>
(function () {
  var KEY = 'dsh-shipgo-checklist-v1';
  var boxes = Array.prototype.slice.call(document.querySelectorAll('input[data-id]'));
  var countEl = document.getElementById('count');
  var barEl = document.getElementById('bar');
  var state = {};
  try { state = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { state = {}; }

  function update() {
    var done = 0;
    boxes.forEach(function (box) {
      var on = !!state[box.getAttribute('data-id')];
      box.checked = on;
      var label = box.closest('label');
      if (label) label.classList.toggle('done', on);
      if (on) done += 1;
    });
    countEl.textContent = done + ' / ' + boxes.length;
    barEl.style.width = (boxes.length ? (done / boxes.length * 100) : 0) + '%';
  }

  boxes.forEach(function (box) {
    box.addEventListener('change', function () {
      state[box.getAttribute('data-id')] = box.checked;
      try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
      update();
    });
  });

  document.getElementById('reset').addEventListener('click', function () {
    state = {};
    try { localStorage.removeItem(KEY); } catch (e) {}
    update();
  });

  document.getElementById('copy').addEventListener('click', function () {
    var text = document.getElementById('cmd-text').textContent;
    var btn = this;
    var ok = function () {
      btn.textContent = '已复制';
      setTimeout(function () { btn.textContent = '复制'; }, 1500);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(ok).catch(function () { btn.textContent = '复制失败'; });
    } else {
      btn.textContent = '请手动复制';
    }
  });

  fetch('/dsh-shipgo/health', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (j) {
      var el = document.getElementById('health');
      if (j && j.ok) {
        el.textContent = '插件已加载 · v' + j.version;
        el.className = 'pill ok';
      } else {
        el.textContent = '独立预览 · 未连接 DSH';
        el.className = 'pill muted';
      }
    })
    .catch(function () {
      var el = document.getElementById('health');
      el.textContent = '独立预览 · 未连接 DSH';
      el.className = 'pill muted';
    });

  update();
})();
</script>
</body>
</html>`;

function rejectUnadmitted(ctx, req, res) {
  const connection = ctx.get('connection');
  if (typeof connection?.requestRejection !== 'function') {
    res.writeHead(503, {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff',
    });
    res.end(JSON.stringify({ error: 'DSH connection authentication service is unavailable.' }));
    return true;
  }

  let status;
  try {
    status = connection.requestRejection(req);
  } catch (_) {
    status = 503;
  }

  if (status === undefined) return false;
  if (!Number.isInteger(status)) status = 503;
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff',
  });
  res.end(JSON.stringify({
    error: status === 401
      ? 'DSH login required.'
      : 'Request from an untrusted or cross-site origin was refused.',
  }));
  return true;
}

export function apply(ctx) {
  const webServer = ctx.get('webServer');
  if (!webServer) return;

  const disposePage = webServer.register({
    kind: 'exact',
    path: '/dsh-shipgo',
    handler(req, res) {
      if (rejectUnadmitted(ctx, req, res)) return;
      res.writeHead(200, {
        'content-type': 'text/html; charset=utf-8',
        'cache-control': 'no-store',
        'x-content-type-options': 'nosniff',
      });
      res.end(PAGE_HTML);
    },
  });

  const disposeHealth = webServer.register({
    kind: 'exact',
    path: '/dsh-shipgo/health',
    handler(req, res) {
      if (rejectUnadmitted(ctx, req, res)) return;
      res.writeHead(200, {
        'content-type': 'application/json; charset=utf-8',
        'cache-control': 'no-store',
        'x-content-type-options': 'nosniff',
      });
      res.end(JSON.stringify({ ok: true, plugin: 'dsh-shipgo', version: '0.1.1' }));
    },
  });

  return () => {
    try { disposePage(); } catch (_) {}
    try { disposeHealth(); } catch (_) {}
  };
}
