# -*- coding: utf-8 -*-
"""en_acceptance_check.py · 英文版 A 类验收一键跑（分册② §3.3 A1~A4）

把散命令收进一个入口：跑完输出《英文验收单》A 类段落，直接可粘（顺手性尺子：
让正确的动作成为最顺手的动作）。B 类人判、C 类中英对表不在本脚本范围。

用法：
    python en_acceptance_check.py README.en.md [--terms terms.json] [--dir 项目根]

    --terms  术语对照表 JSON：{"定译": ["禁用旧译", ...], ...}
             （分册② §3.1 表的机器可读形态；不传则只跑内置默认禁用词）
             B7b 修（早期修订）：值必须是字符串数组——字符串会被 extend 按字符拆成单字母
             （实测：整篇误报 c/r/o/n/e，验收单作废）；非数组值报错跳过该键并 FAIL；
             `_` 前缀键＝备注/元数据，跳过不进校验
             B7a 修（早期修订）：值支持 {"ban": [...], "allow_literals": [...]} 形态——
             allow_literals 字面量所在行豁免（实测：`zero connections` 是内部状态名，
             与红线旧译 no outbound connections 不是同一概念，纯 grep 逼人改正确正文）
    --dir    项目根（A2 查盘用，缺省=README 同目录）
    --selftest 自检（B2）：terms 三形态＋allow_literals 豁免＋锚点回归＋CJK 残留检测，不需要 src

早期修订：修（P1 组合修，多轮假绿实锤——三方独立复现）：A4 新增 **CJK 残留检测**
（[\u4e00-\u9fff]，围栏代码块与行内代码豁免，行含豁免字面量整行豁免——B7a 同款口径）：
此前"中文残留"只查固定短语，中文可整段注入英文版而闸放绿（46 处汉字、三项全 PASS 的假绿实案）。

早期修订：修（一轮复核打回＋早期修订 复核 R1/R3）：R3＝main 无 --terms 时 banned_add 未初始化崩溃
（UnboundLocalError，最常见调用路径一张验收单都出不了）——初始化补齐＋selftest 补 main() 端到端冒烟
（其余用例全在内存调纯函数、从不进 main，结构性测不到这条路径）。R1＝check_cjk 豁免扩到**资源目标路径**
（markdown ](…)/HTML src="…"/href="…"）——分册①的 assets/截图/ 是册子自定的中文目录名（W11 同源），
旧口径只认反引号，真·已发布件 6 处命中里 5 处是合法路径、干净件本身 FAIL（实测）。

内置默认禁用项：
    中文残留指引（see the Chinese README / 待补 / 形式对齐初稿）
    AI 腔特征（em dash 连发、as an AI、delve、三段式 It's not just X, it's Y）
    超前账残留（ TODO / TBD / placeholder）

退出码（统一口径）：0=全部 PASS；1=有 FAIL（判红，验收单照打）；2=用法或输入/环境错（文件不存在、术语表非 JSON 等，不甩 traceback）。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_BANNED = [
    "see the Chinese README", "待补", "形式对齐初稿", "TBD", "TODO", "placeholder",
    "as an AI", "delve", "It's not just", "it's not just",
]

# A1 用与整形器同一套 gh_slug（单一来源，不重写第二份算法）
def gh_slug(heading: str) -> str:
    out = []
    for ch in heading.strip().lower():
        if ch in (" ", "-", "\u00a0"):
            out.append("-")
            continue
        cat = __import__("unicodedata").category(ch)
        if cat[0] in ("L", "M", "N") or cat == "Pc":
            out.append(ch)
    return "".join(out)


# ---------- 检测核心（纯内存函数，早期修订——selftest 直接调用，不落任何文件） ----------

def check_anchors(text):
    """A1 核心：目录锚点全可点。返回配不上的页内链接列表。"""
    headings = [t for _, t in re.findall(r"^(#{1,3}) (.+)$", text, flags=re.M)]  # 审查修正：收 H1~H3，目录链到 H1 不再误报
    seen, slugs = {}, []
    for h in headings:
        b = gh_slug(h)
        n = seen.get(b, 0)
        seen[b] = n + 1
        slugs.append(b if n == 0 else f"{b}-{n}")
    valid = set(slugs)
    links = re.findall(r"\]\(#([^)]+)\)", text)
    return [l for l in links if l not in valid]


def parse_terms(table):
    """B7a/B7b 核心：术语表解析（内存 dict）→ (追加禁用对列表, 组描述, 格式是否出错)。"""
    banned_add = []      # (禁用词, allow_literals 列表)
    term_pairs = []
    format_bad = False
    for canonical, olds in table.items():
        if canonical.startswith("_"):
            continue   # B7b：_ 前缀键＝备注/元数据，跳过不进校验（实测同款）
        if isinstance(olds, str):
            print(f"[en_check] FAIL terms 格式：键「{canonical}」的值是字符串，应为字符串数组"
                  f"——已跳过该键（B7b：字符串会被 extend 按字符拆成单字母，验收单作废实案）",
                  file=sys.stderr)
            format_bad = True
            continue
        if isinstance(olds, dict):
            allows = [a for a in olds.get("allow_literals", []) if isinstance(a, str)]
            words = [w for w in olds.get("ban", []) if isinstance(w, str)]
            term_pairs.append((canonical, f"{len(words)} 组（allow_literals {allows}）"))
            for w in words:
                banned_add.append((w, allows))   # B7a：带豁免的禁用词
            continue
        if not isinstance(olds, list):
            print(f"[en_check] FAIL terms 格式：键「{canonical}」的值类型不支持（{type(olds).__name__}）"
                  f"——已跳过该键（B7b）", file=sys.stderr)
            format_bad = True
            continue
        term_pairs.append((canonical, f"{len(olds)} 组"))
        for w in olds:
            banned_add.append((w, []))
    return banned_add, term_pairs, format_bad


def check_banned(text, banned_pairs):
    """A3+A4 核心：行级扫描＋B7a 豁免（行内含 allow_literals 字面量则该行不算）。返回命中 dict。"""
    hits = {}
    for w, allows in banned_pairs:
        n = 0
        for line in text.splitlines():
            if w in line and not any(a in line for a in allows):
                n += 1
        if n:
            hits[w] = n
    return hits


# ---------- CJK 残留检测（早期修订 P1 组合修——机器层） ----------

DEFAULT_CJK_ALLOW = [
    "[中文]",          # 语言切换行锚文本（双语互认行，R3 双语互认同源）
    "Produced by",     # 署名行前缀（通用；署名主体由项目自定，见分册② §1 第 7 段）
]


def check_cjk(text, allow_literals):
    """A4 CJK 残留核心（早期修订 P1 修；早期修订 R1 扩豁免）：逐行检测汉字区间（\\u4e00-\\u9fff），
    返回命中 [(行号, 行截断)]。豁免：①围栏代码块（``` 整块）；②行内代码 `...`；
    ③资源目标路径——markdown 链接/图片 ](…) 与 HTML src="…"/href="…"（早期修订 R1：分册①的
    assets/截图/ 等中文目录名是册子自定的，引用形态不带反引号；只豁免路径本身，alt/caption
    等内容文本照查）；④行含豁免字面量则整行豁免（B7a 同款口径；
    allow_literals＝terms 豁免＋DEFAULT_CJK_ALLOW 预置）。"""
    hits = []
    in_fence = False
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        probe = re.sub(r"`[^`]*`", "", line)   # 行内代码整体豁免
        probe = re.sub(r"\]\([^)]*\)", "]()", probe)   # 早期修订 R1：markdown 链接/图片目标路径
        probe = re.sub(r'(?i)\b(src|href)\s*=\s*(?:"[^"]*"|\'[^\']*\')', r'\1=""', probe)   # 早期修订 R1：HTML src/href
        if not re.search(r"[\u4e00-\u9fff]", probe):
            continue
        if any(a in line for a in allow_literals):
            continue   # B7a 同款：行含豁免字面量，整行豁免
        hits.append((i, line.strip()[:90]))
    return hits


def run_python(args, runner=subprocess.run):
    """统一 -B 不写缓存；-I 被宿主拦截时显式降级，不把环境问题说成自检失败。"""
    base = [sys.executable, "-B", "-I", "-X", "utf8"]
    kwargs = dict(capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    try:
        return runner(base + [str(a) for a in args], **kwargs)
    except PermissionError:
        print("WARN 宿主禁止 -I 隔离参数：降级为 -B -X utf8 重跑", file=sys.stderr)
        return runner([sys.executable, "-B", "-X", "utf8"] + [str(a) for a in args], **kwargs)


def selftest():
    """B2/B7a/B7b 自检（早期修订）——纯内存，不落任何文件。"""
    results = []

    # ① B7a：allow_literals 行级豁免＋旧译照样逮住
    text = ("# Demo\n\n## Usage\n\nRun `demo`.\n\n"
            "Note: failure and zero connections are recorded separately (internal state).\n"
            "Legacy text with whitelist here.\n")
    table = {
        "_comment": "备注键应被跳过（B7b）",
        "trust list": {"ban": ["whitelist"], "allow_literals": []},
        "no outbound connections": {"ban": ["zero ports"],
                                    "allow_literals": ["zero connections"]},
    }
    banned_add, term_pairs, fmt_bad = parse_terms(table)
    hits = check_banned(text, [(w, []) for w in DEFAULT_BANNED] + banned_add)
    ok = (not fmt_bad and "whitelist" in hits
          and all("zero connections" not in k for k in hits))
    results.append(("B7a 豁免生效＋旧译逮住＋_键跳过", ok,
                    f"hits={hits}（期望只命中 whitelist；zero connections 行被豁免）"))

    # ② B7b：字符串值报格式错、不拆单字母
    banned_add2, _, fmt_bad2 = parse_terms({"ExampleApp": "exampleapp", "_note": "x"})
    letters = [w for w, _ in banned_add2 if len(w) == 1]
    ok2 = fmt_bad2 and not letters
    results.append(("B7b 字符串值报错不拆字", ok2,
                    f"format_bad={fmt_bad2}，单字母 {letters}（旧版会拆成 m/i/c/…整篇误报）"))

    # ③ A1 锚点回归：坏锚逮住、好锚放过
    bad = check_anchors("# D\n\n## A\n\n[x](#a)\n[y](#nope)\n")
    results.append(("A1 锚点回归", bad == ["nope"], f"bad={bad}"))

    # ④ CJK 残留检测（夹具＝册子产物形态——分册① 的 assets/截图/ 路径约定用
    #    markdown 图片/HTML 标签引用、不带反引号。旧夹具把路径写反引号里＝理想最小件，测不到 R1 缺口：
    #    三个新 selftest 用例全挑"能过的形态"、回归全绿而两层在真件上是死的——§五系统性教训）
    cjk_text = (
        "# Demo\n"
        "[中文](README.md) | [EN](README.en.md)\n\n"          # 语言锚行：豁免
        "## Overview\n\n"
        '<a href="assets/流程图/How_It_Works.svg">\n'          # HTML href 路径：豁免（R1）
        '  <img src="assets/流程图/How_It_Works.png" width="900" alt="how it works">\n'
        "</a>\n\n"
        "![screenshot](assets/截图/主界面.png)\n\n"            # markdown 图片路径：豁免（R1）
        "Or double-click `启动示例项目.bat`.\n\n"               # 行内代码：豁免
        "Produced by Example Team.\n\n"                        # 署名字面量：豁免
        "```bash\npip install 示例包名\n```\n\n"               # 围栏代码块：豁免
        "## 界面一览\n\n"                                      # 中文节标题：命中
        '<img src="a.png" alt="界面截图">\n'                   # alt 文本（内容非路径）：照查命中
    )
    cjk_hits = check_cjk(cjk_text, DEFAULT_CJK_ALLOW)
    ok4 = (len(cjk_hits) == 2 and "界面一览" in cjk_hits[0][1]
           and "界面截图" in cjk_hits[1][1])
    results.append(("CJK 残留检测：中文标题/alt 文本 FAIL＋资源路径等豁免不误报", ok4,
                    f"hits={[(h[0], h[1][:30]) for h in cjk_hits]}（语言锚/HTML+md 资源路径/行内代码/署名/代码块全豁免，仅标题与 alt 命中）"))

    # ⑤ main() 端到端冒烟：不带 --terms 的默认路径——干净件出单、中文残留件 FAIL、零 Traceback。
    with tempfile.TemporaryDirectory() as td:
        clean = Path(td) / "clean.md"
        clean.write_text("# Demo\n\n## Body\nAll good, see `assets/截图/主界面.png`.\n", encoding="utf-8")
        r1 = run_python([Path(__file__).resolve(), clean])
        dirty = Path(td) / "dirty.md"
        dirty.write_text("# Demo\n\n## 界面一览\n中文标题残留。\n", encoding="utf-8")
        r2 = run_python([Path(__file__).resolve(), dirty])
    ok5 = (r1.returncode == 0 and "Traceback" not in r1.stdout + r1.stderr
           and "英文验收单" in r1.stdout
           and r2.returncode == 1 and "Traceback" not in r2.stdout + r2.stderr
           and "FAIL" in r2.stdout and "CJK" in r2.stdout)
    results.append(("main() 无 --terms 端到端冒烟：默认路径出单不崩＋注入中文 FAIL", ok5,
                    f"clean exit={r1.returncode}，dirty exit={r2.returncode}"
                    + ("" if ok5 else f"；r2 stdout[:200]={r2.stdout[:200]!r} stderr[:200]={r2.stderr[:200]!r}")))

    # ⑥ 宿主禁止 -I：第一次显式拦截后，第二次去 -I、保留 -B，不重复原参数硬闯。
    calls = []
    def deny_isolated(cmd, **kwargs):
        calls.append(cmd)
        if "-I" in cmd:
            raise PermissionError("host denied -I")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    fallback = run_python(["--help"], runner=deny_isolated)
    ok6 = (len(calls) == 2 and "-I" in calls[0] and "-I" not in calls[1]
           and "-B" in calls[1] and fallback.returncode == 0)
    results.append(("run_python：-I 被禁时显式降级且保留 -B", ok6,
                    f"调用 {len(calls)} 次；第二次参数={calls[1][1:4] if len(calls) > 1 else calls}"))

    print("# en_acceptance_check.py --selftest（纯内存，无脚手架）")
    all_ok = True
    for name, ok, msg in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}  {msg}")
        all_ok = all_ok and ok
    print("selftest 结论：" + ("全过" if all_ok else "有 FAIL，见上"))
    return 0 if all_ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="英文版 A 类验收一键跑（A1~A4）早期修订")
    ap.add_argument("src", nargs="?", default=None)
    ap.add_argument("--terms", help="术语对照表 JSON（禁用旧译表）")
    ap.add_argument("--dir", help="项目根（缺省=README 同目录）")
    ap.add_argument("--selftest", action="store_true",
                    help="自检（B2/B7a/B7b）：纯内存，不需要 src")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.src:
        ap.error("缺少 README.en.md 路径（或用 --selftest / --help）")

    src = Path(args.src)
    # 统一口径：输入/环境错误统一 exit 2（不与"判红 exit 1"混用），只给一句人话
    if not src.is_file():
        print(f"ERROR 找不到输入文件：{src}（检查路径，或用 --help 看用法）", file=sys.stderr)
        return 2
    try:
        text = src.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        print(f"ERROR 读不了输入文件：{src}（{e.__class__.__name__}）", file=sys.stderr)
        return 2
    root = Path(args.dir) if args.dir else src.parent
    results = []

    # A1 目录锚点全可点（早期修订：抽纯函数 check_anchors，selftest 复用）
    bad_a1 = check_anchors(text)
    links = re.findall(r"\]\(#([^)]+)\)", text)
    results.append(("A1 目录锚点全可点", not bad_a1,
                    f"{len(links)} 个页内链接" + (f"，配不上 {bad_a1}" if bad_a1 else "")))

    # A2 本地链接/图片逐个查盘（审查修正：[x](路径 "标题") 形态只取路径，标题不进查盘）
    refs = re.findall(r"\]\((?!#|http)([^\s)\"]+)(?:\s+\"[^\"]*\")?\)", text) + \
           re.findall(r'<img[^>]+src="([^":]+)"', text)
    bad_a2 = []
    for r in {r.strip() for r in refs if not r.startswith(("http", "mailto:"))}:
        if not (root / r.split("#")[0]).exists():
            bad_a2.append(r)
    results.append(("A2 本地链接/图片全存在", not bad_a2,
                    f"查盘 {len(set(refs))} 个引用" + (f"，缺 {bad_a2}" if bad_a2 else "")))

    # A3+A4 禁用词/禁用旧译零命中（早期修订：抽纯函数 parse_terms＋check_banned，selftest 复用）
    banned_pairs = [(w, []) for w in DEFAULT_BANNED]
    banned_add, term_pairs, terms_format_bad = [], [], False   # 早期修订 R3 修：banned_add 须无条件初始化（45 号实锤：无 --terms 时下方循环遍历未赋值变量崩溃）
    if args.terms:
        try:
            table = json.loads(Path(args.terms).read_text(encoding="utf-8-sig"))
        except FileNotFoundError:
            print(f"ERROR 找不到术语表：{args.terms}", file=sys.stderr)
            return 2
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"ERROR 术语表读不了或不是合法 JSON：{args.terms}（{e.__class__.__name__}）", file=sys.stderr)
            return 2
        banned_add, term_pairs, terms_format_bad = parse_terms(table)
        banned_pairs.extend(banned_add)
    hits = check_banned(text, banned_pairs)
    # A4 CJK 残留检测（早期修订 P1 修——多轮假绿：中文可整段注入英文版而闸放绿）
    cjk_allows = list(DEFAULT_CJK_ALLOW)
    for _, allows in banned_add:
        cjk_allows.extend(allows)   # terms 豁免字面量并入（B7a 同款口径）
    cjk_hits = check_cjk(text, cjk_allows)
    results.append(("A3+A4 禁用词/禁用旧译/中文残留（CJK）零命中", not hits and not terms_format_bad and not cjk_hits,
                    f"内置 {len(DEFAULT_BANNED)} 条＋术语表 {len(term_pairs)} 组（组＝键数：数组/allow_literals 形态各计 1，_ 前缀备注键不计——W13 口径）"
                    + (f"，命中 {hits}" if hits else "，零命中")
                    + (f"；CJK 残留 {len(cjk_hits)} 处（首处 L{cjk_hits[0][0]}：{cjk_hits[0][1]}）" if cjk_hits else "；CJK 零残留")
                    + ("；terms 格式有错（见 stderr）" if terms_format_bad else "")))

    # 打验收单 A 类段落
    all_pass = all(ok for _, ok, _ in results)
    print("# 英文验收单 · A 类（机器跑）")
    print(f"对象：{src.name} @ {__import__('hashlib').sha256(src.read_bytes()).hexdigest()[:8].upper()}")
    for name, ok, ev in results:
        print(f"{name}  {'PASS' if ok else 'FAIL'}  证据：{ev}")
    print(f"\nA 类结论：{'全部 PASS' if all_pass else '有 FAIL——定点改，改完重跑本脚本'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
