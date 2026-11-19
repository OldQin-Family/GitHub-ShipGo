# -*- coding: utf-8 -*-
"""restyle_readme.py · 项目 README 版式整形器（通用版，只动版式不动正文）

用途：把 README.md 的呈现层整理成 GitHub/Gitee 落地页形态，正文一个字不改。
      文字改动先做完再套版式；脚本可重复执行（幂等）。

退出码（统一口径）：0=通过／1=判红（版式或正文校验不过）／2=用法或输入/环境错（文件不存在、config 非 JSON 等）。
用法：
    python restyle_readme.py README.md                    # 默认内置配置，打印到 stdout
    python restyle_readme.py README.md -c config.json -o README.new.md
    python restyle_readme.py README.md --check            # 校验正文未被改动且应有版式齐全；--check 与 -o 不能同用

config.json 字段（全部可选，缺省按内置默认）：
    icon        {"src","alt"}                  标题区图
    badges      ["...", ...]                   徽章条文案（禁带写死的数字）
    screenshots [{"src","alt","caption"}]      界面一览
    flow        {"png","svg","caption"}|null   整机流程图
    toc_insert_before "## 标题"                目录/截图区插入锚（缺失自动降级并明示）
    wall        {"start","end","summary"}|null 折叠墙
    avatar_dir  "assets/team/avatar-"          头像行（贡献者墙）通配标记
    site_line   {"url","name","text"?}|null     收尾网站行（text=前缀文案，缺省无前缀；显式配则按配置出）
    section_titles {"screenshots","flow","toc"} 章节标题表（B10 修，早期修订）：
                                                守卫/verify 按此配置识别章节，不认中文字面串
                                                ——本地化项目改这里即可，改标题不改脚本

三条硬纪律（继承第一代参考实现）：
    1. 原文每行（多重集）必须逐字出现在新版；例外仅四类：头像行只改 width、
       编号章节提级（### N. → ## N.）、纯空行压缩、锚点内部改写——全部写进 verify，无暗豁免；
       **反向同样校验（B10 修，早期修订）：新版不得多插标准节**（K-4 实案：已本地化文件再跑，
       中文三节重复注入、页内链接 1→10，旧 verify 只查"少"查不出"多"）；
    2. 锚点只报告不改写（自动改写锚点曾被实证造出死链）；
    3. 自报数不作数——验收须独立实现复算（github-slugger / 线上点击）。

v2 修复（N1~N4）：补 promote_numbered；流程图插整节之后；头像行级替换＋
任意宽度＋verify 落实宽度例外；verify 改多重集＋顺序感知，删除未授权的 norm_level 例外。
早期修订：修复（复核定级"本轮最严重"）：章节标题配置化（section_titles）＋守卫按配置
识别（不再认中文字面串）＋verify 双向校验（多插节也 FAIL）＋--selftest 自检
（含幂等连验两次——复核硬要求：对输出再完整跑一遍，二次与一次 diff 为零才算幂等）。
早期修订：修复（早期某轮实测 3/3 全撞＝V3-1 必修头一件）：extra_sections 按"预期/意外 ×
单节/重复"四格判（定口径）——管道配置注入的标准节记显式降级不判 FAIL，
首跑 exit 0（早期某轮 3/3 撞的"首跑必 exit 1"缺口堵上）；K-4 真重复与未配置节继续 FAIL；
selftest 补"首跑 exit 0"用例（补盲区：旧用例只查节注入没查首跑 exit 码）。
（docstring 重复段去重——平行查证 §5.3 逮出，stale 三类例外块已删。）
早期修订：修（一轮打回＋早期修订 复核 R2）：语言混杂警告的中文判定改用 en_check 的 check_cjk＋
DEFAULT_CJK_ALLOW（单一真源，不写第二份豁免表）——早期修订 版只自写三道豁免（代码块/语言切换行/
行内代码）、没有署名豁免，册子分册② §1 第 7 段强制的署名收尾使本警告在任何符合册子的
英文版上恒不触发（D/E 隔离实锤）；另按 R1 同口径豁免资源目标路径，判定改"命中行不过内容行
半数＝英文文档"（零星残留不掩盖文档主语言，真发布件夹残留也照样警告）。
"""
import argparse
import difflib
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

# M2 修（代码审查）：导入 en_acceptance_check 会写 scripts/__pycache__，让紧随的
# fingerprints_scan --check 判"净空违例"。脚本自身先关字节码写入（不依赖调用方记得加 -B）。
sys.dont_write_bytecode = True

# 早期修订 R2 修：CJK 判定单一真源在 en_check（check_cjk＋DEFAULT_CJK_ALLOW）。
# 显式挂本脚本目录——嵌码联检 selftest_4tools 全程 -I 跑脚本（-I 下脚本目录不自动进 sys.path，
# 裸 import 会炸）；en_check 缺席＝坏包，宁可 ImportError 摔响也不静默丢掉这层警告。
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
from en_acceptance_check import DEFAULT_CJK_ALLOW, check_cjk

# ---------- GitHub 锚点（复刻 github-slugger@2.0.0；验收不采信自报） ----------

def gh_slug(heading: str) -> str:
    out = []
    for ch in heading.strip().lower():
        if ch in (" ", "-", "\u00a0"):
            out.append("-")
            continue
        cat = unicodedata.category(ch)
        if cat[0] in ("L", "M", "N") or cat == "Pc":
            out.append(ch)
    return "".join(out)


def slug_map(headings):
    seen, out = {}, []
    for h in headings:
        base = gh_slug(h)
        n = seen.get(base, 0)
        seen[base] = n + 1
        out.append(base if n == 0 else f"{base}-{n}")
    return out


# ---------- 默认配置 ----------

DEFAULTS = {
    "icon": {"src": "icon.png", "alt": "project icon"},
    "badges": [],
    "screenshots": [],
    "flow": None,
    "toc_insert_before": None,
    "wall": None,
    "avatar_dir": "assets/team/avatar-",
    "avatar_width": 96,
    "site_line": None,
    # B10 修（早期修订）：章节标题配置化——守卫/verify 按此识别，不认中文字面串
    "section_titles": {"screenshots": "界面一览", "flow": "整机流程图", "toc": "本文目录"},
}


def deep_merge(base, over):
    """M7 修：嵌套字典逐键合并，局部 config（如只配 section_titles.toc）不再 KeyError。"""
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def sec(cfg, key):
    """取配置化章节标题（B10）：'## ' 前缀统一在这里拼；缺键回落内置默认（M7）。"""
    titles = cfg.get("section_titles") or {}
    return f"## {titles.get(key, DEFAULTS['section_titles'][key])}"


class Fail(Exception):
    pass


DEGRADATIONS = []  # 输入形态差异导致的显式降级（main 时打印，绝不静默）


def must_find(text, pattern, what):
    m = re.search(pattern, text, flags=re.M)
    if not m:
        raise Fail(f"锚文本缺失：{what}\n  正则：{pattern}\n  → 正文可能已被大改，请人工核对后再跑。")
    return m


def p_center(inner):
    return f'<p align="center">\n{inner}\n</p>'


# ---------- 变换步骤（每步幂等守卫＋锚点必中／显式降级） ----------

def step_header(text, cfg):
    if f'src="{cfg["icon"]["src"]}"' in text:
        return text
    header = (f'<p align="center"><img src="{cfg["icon"]["src"]}" width="96" '
              f'alt="{cfg["icon"]["alt"]}"></p>')
    badges = ""
    if cfg["badges"]:
        badges = ("<p align=\"center\">"
                  + " &nbsp;·&nbsp; ".join(f"<code>{b}</code>" for b in cfg["badges"])
                  + "</p>")
    m = re.search(r"^\[[^\]]{1,20}\]\(README(?:\.en)?\.md\)[^\n]*\n", text, flags=re.M)  # #35 双语互认（R3 修正：字符类关闭，复核）
    if m:  # 形态 A：已有语言行 → icon 排语言行前
        lang = text[m.start():m.end()].rstrip("\n")
        return (text[:m.start()] + header + "\n\n" + lang + "\n\n" + badges
                + "\n\n" + text[m.end():].lstrip("\n"))
    # 形态 B（显式降级）：无语言行 → icon＋徽章放文件顶
    DEGRADATIONS.append("无语言切换行：标题区放文件最顶（工作副本形态）")
    head = header + ("\n\n" + badges if badges else "")
    return head + "\n\n" + text.lstrip("\n")


def img_block(src, alt, caption, href=None):
    img = (f'<a href="{href}">\n  <img src="{src}" width="900" alt="{alt}">\n</a>'
           if href else f'<img src="{src}" width="900" alt="{alt}">')
    sub = f"<br>\n  <sub>{caption}</sub>" if caption else ""
    return p_center("  " + img + sub)


def step_screenshots(text, cfg):
    t = sec(cfg, "screenshots")   # B10：配置化标题，不再认中文字面串
    if t in text or not cfg["screenshots"]:
        return text
    blocks = [img_block(s["src"], s.get("alt", ""), s.get("caption", ""))
              for s in cfg["screenshots"]]
    section = t + "\n\n" + "\n\n".join(blocks) + "\n\n"
    m = _insert_anchor(text, cfg)
    return text[:m.start()] + section + text[m.start():]


def step_flow(text, cfg):
    f = cfg.get("flow")
    t_shot, t_flow = sec(cfg, "screenshots"), sec(cfg, "flow")
    if not f or t_flow in text:
        return text
    section = (t_flow + "\n\n"
               + img_block(f["png"], f.get("caption", "流程图"), f.get("caption", ""),
                           href=f.get("svg"))
               + "\n\n")
    # N2 修：插到「界面一览」整节之后（下一个二级标题之前），段序=截图→流程图
    # B10：查找标题也按配置（本地化后中文字面串找不到＝错插位置）
    m = re.search(rf"^{re.escape(t_shot)}\s*$", text, flags=re.M)
    if m:
        nxt = re.search(r"^## ", text[m.end():], flags=re.M)
        if nxt:
            cut = m.end() + nxt.start()
            return text[:cut] + section + text[cut:]
    # 无界面一览（降级）：插在目录/首个二级标题前
    m = _insert_anchor(text, cfg)
    return text[:m.start()] + section + text[m.start():]


def _insert_anchor(text, cfg):
    """目录/截图区插入点：配置锚优先，缺失显式降级到首个二级标题。"""
    anchor = cfg.get("toc_insert_before")
    if anchor:
        m = re.search(rf"^{re.escape(anchor)}\s*\n", text, flags=re.M)
        if m:
            return m
        DEGRADATIONS.append(f"配置锚 {anchor} 不存在：降级到首个二级标题前")
    return must_find(text, r"^## ", "插入锚（首个二级标题）")


def step_promote_numbered(text, cfg):
    """编号章节提级：### N. → ## N.、#### N.M → ### N.M（N1 修：补进管道，排 toc 前）。

    幂等由输入形态自然保证：提级后二次运行时 ### N. 已不存在，走 N/A 返回；
    守卫不检查 ## N. 是否存在（样例含 ## 0. 前置节时误判"已提级"的坑已踩）。
    """
    if not re.search(r"^### \d+\. ", text, flags=re.M):
        return text  # 无三级编号章节，N/A
    DEGRADATIONS.append("编号章节已提级：### N. → ## N.（版式七段第⑤段标准层级）")
    text = re.sub(r"^#### (\d+\.+\d+) ", r"### \1 ", text, flags=re.M)
    return re.sub(r"^### (\d+\. )", r"## \1", text, flags=re.M)


def step_toc(text, cfg):
    t = sec(cfg, "toc")   # B10：配置化标题
    if t in text:
        return text
    # 目录收 H2/H3（版式选择——H1 通常是文档标题不进目录）；锚点审计收 H1~H3（见 anchor_audit）。
    # 两处口径不同是有意的，不是 P2-3 只改了一半（审查修正 复核注）。
    pairs = [(lv, t2) for lv, t2 in re.findall(r"^(#{2,3}) (.+)$", text, flags=re.M)
             if t2.strip() not in ("目录", cfg["section_titles"]["toc"])]
    slugs = slug_map([t2 for _, t2 in pairs])
    lines = [t, ""]
    for (level, title), slug in zip(pairs, slugs):
        lines.append(f"{'  ' if level == '###' else ''}- [{title}](#{slug})")
    toc = "\n".join(lines) + "\n\n---\n\n"
    m = _insert_anchor(text, cfg)
    return text[:m.start()] + toc + text[m.start():]


def step_wall(text, cfg):
    w = cfg.get("wall")
    if not w or "<details>" in text:
        return text
    ms = must_find(text, w["start"], "折叠墙起点")
    me = must_find(text, w["end"], "折叠墙终点")
    wall = text[ms.start():me.end()]
    head = f"<details>\n<summary><b>{w.get('summary', '详见折叠区')}</b></summary>\n\n"
    return text[:ms.start()] + head + wall + "\n</details>\n" + text[me.end():]


def step_avatars(text, cfg):
    """N3 修：行级替换——只动含头像标记的行，认任意原宽度，统一到目标宽。"""
    marker = cfg["avatar_dir"]
    width = cfg.get("avatar_width", 96)
    out_lines = []
    changed = 0
    for line in text.splitlines():
        if marker in line and re.search(r"width\s*=\s*[\"']\d+[\"']", line):
            # 审查修正：单双引号都认，替换统一输出双引号
            new_line = re.sub(r"width\s*=\s*[\"']\d+[\"']", f'width="{width}"', line)
            if new_line != line:
                changed += 1
            out_lines.append(new_line)
        else:
            out_lines.append(line)
    if changed:
        DEGRADATIONS.append(f"头像行 {changed} 行宽度统一为 {width}px（行级替换，非头像行不动）")
    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")


def step_site_line(text, cfg):
    s = cfg.get("site_line")
    if not s:
        return text
    # 审查修正：守卫改认本函数生成的特征串——正文别处出现同名不致静默跳过收尾行
    # （静默不岗＝该干的活没干还没声）；幂等性由精确特征串保住。
    if f'<a href="{s["url"]}">{s["name"]}</a>' in text:
        return text
    # （④-2）：前缀文案曾硬编码中文——英文版配 site_line 必进中文、A4 必 FAIL。
    # 缺省改**无前缀**（中性）；需要前缀的项目在 config 里显式配 text（中/英按项目定）。
    prefix = s.get("text", "")
    line = f'<p align="center">{prefix}<a href="{s["url"]}">{s["name"]}</a></p>'
    return text.rstrip("\n") + "\n\n---\n\n" + line + "\n"


def step_anchor_audit(text, cfg):
    titles = [t for _, t in re.findall(r"^(#{1,3}) (.+)$", text, flags=re.M)]  # 审查修正 同款：收 H1~H3
    valid = set(slug_map(titles))
    links = re.findall(r"\]\(#([^)]+)\)", text)
    report = {"checked": len(links),
              "unresolved": sorted({l for l in links if l not in valid})}
    return text, report


def step_blank_runs(text, cfg):
    return re.sub(r"\n{4,}", "\n\n\n", text)


STEPS = [step_header, step_promote_numbered, step_screenshots, step_flow, step_toc,
         step_wall, step_avatars, step_site_line, step_anchor_audit, step_blank_runs]

# ---------- 正文完整性校验（多重集＋顺序感知，无暗豁免） ----------

def _normalize(line, avatar_marker):
    """锚点抹平＋头像宽度抹平——这两类是册子授权的版式变化。
    审查修正 半修补：归一化口径与 step_avatars 的替换口径同步（单双引号都抹平），
    否则单引号头像行改写后会被 verify 误判"正文被删改"。"""
    s = re.sub(r"\]\(#[^)]*\)", "](#X)", line)
    if avatar_marker in s:
        s = re.sub(r"""width\s*=\s*["']\d+["']""", 'width="X"', s)
    return s


def verify(original, restyled, avatar_marker):
    """返回（被删改的原文行清单, 多重集差额, 顺序违例数）。

    口径：原文每个非空行（按锚点/头像宽度归一后）在"多重集计数"与"相对顺序"上
    都必须存活于新版；否则逐行列出。编号章节提级只动 `#` 数量——
    归一时同时抹平标题级前缀（N4 修：该例外显式写进本函数与分册白名单）。
    """
    def norm(line):
        s = _normalize(line, avatar_marker)
        return re.sub(r"^#+\s*", "", s) if re.match(r"^#+\s", s) else s

    old_seq = [norm(l) for l in original.splitlines() if l.strip()]
    new_seq = [norm(l) for l in restyled.splitlines() if l.strip()]

    dropped_multiset = []
    c_new = Counter(new_seq)
    for line, cnt in Counter(old_seq).items():
        if c_new[line] < cnt:
            dropped_multiset.extend([line] * (cnt - c_new[line]))

    # 顺序感知：原文行序列必须是新版行序列的子序列（保序存活）
    it = iter(new_seq)
    order_violation = 0
    if not all(any(candidate == keep for keep in it) for candidate in old_seq):
        order_violation = 1

    dropped_lines = []
    if dropped_multiset or order_violation:
        sm = difflib.SequenceMatcher(a=old_seq, b=new_seq, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag in ("delete", "replace"):
                dropped_lines.extend(old_seq[i1:i2])

    return dropped_lines, dropped_multiset, order_violation


def injected_expected(cfg):
    """本管道配置要注入的标准节（V3-1）：toc 无条件注入；screenshots/flow 按 config 注入。"""
    expected = ["toc"]
    if cfg.get("screenshots"):
        expected.append("screenshots")
    if cfg.get("flow"):
        expected.append("flow")
    return expected


def extra_sections(original, restyled, cfg):
    """多插节检测——verify 的反向半边。V3-1 修（早期修订，定口径）按"预期/意外 × 单节/重复"四格判：

    1. 标准节 n_new > 1 → FAIL（K-4 真重复注入，必须继续逮住，不能改没了）；
    2. n_new=1、n_old=0，且该节**本就在管道配置的注入清单内**（cfg 开了 toc/screenshots/flow）
       → 属预期注入，记显式降级声明、**不判 FAIL**（早期某轮实测 3/3 撞：首跑必 exit 1 的缺口已堵）；
    3. 管道没配置要注入的节出现 → FAIL。

    返回 (fails, notices)：fails 进退出码；notices 由调用方并入 DEGRADATIONS 显式声明。
    """
    titles = cfg.get("section_titles", DEFAULTS["section_titles"])
    expected = set(injected_expected(cfg))
    fails, notices = [], []
    for key, title in titles.items():
        pat = rf"^## {re.escape(title)}\s*$"
        n_new = len(re.findall(pat, restyled, flags=re.M))
        n_old = len(re.findall(pat, original, flags=re.M))
        if n_new > 1:
            fails.append(f"{title}：新版出现 {n_new} 次（重复注入——K-4 实案，必逮）")
        elif n_new == 1 and n_old == 0:
            if key in expected:
                notices.append(f"{title}：管道注入（预期语义，首跑正常）")
            else:
                fails.append(f"{title}：原文无此节、新版多插，且管道未配置注入此节")
    return fails, notices


def missing_expected_sections(text, cfg):
    """--check 的正向版式校验：配置要求的标准节必须已在被检文件里。

    校验对象是原始输入而不是 restyle 后的输出——否则管道刚注入的节会反向
    证明原文件已整形，未整形文件就会继续假绿。
    """
    heads = {t.strip() for _h, t in re.findall(r"^(#{1,3}) (.+)$", text, flags=re.M)}
    titles = cfg["section_titles"]
    # toc 与 injected_expected 同口径：管道无条件生成；toc_insert_before=None
    # 只是自动选锚的合法默认，不代表目录变成可选。
    expected = [("toc", titles["toc"])]
    for key in ("screenshots", "flow"):
        if cfg.get(key):
            expected.append((key, titles[key]))
    missing = [title for key, title in expected if title not in heads]
    icon = cfg.get("icon") or {}
    if icon.get("src") and icon["src"] not in text:
        missing.append("icon")
    return missing


def validate_config(cfg):
    """配置结构人话校验；返回错误文案或 None。只查本管道实际消费的键。"""
    for key in ("badges", "screenshots"):
        if not isinstance(cfg.get(key), list):
            return f"{key} 必须是数组"
    if any(not isinstance(b, str) for b in cfg["badges"]):
        return "badges 数组元素必须是字符串"
    for key in ("icon", "wall", "flow", "site_line", "section_titles"):
        if cfg.get(key) is not None and not isinstance(cfg.get(key), dict):
            return f"{key} 必须是对象"
    for key in ("avatar_dir", "toc_insert_before"):
        if cfg.get(key) is not None and not isinstance(cfg.get(key), str):
            return f"{key} 必须是字符串或 null"
    if not isinstance(cfg.get("avatar_width"), int):
        return "avatar_width 必须是整数"
    for key in ("icon", "flow"):
        for sub, val in (cfg.get(key) or {}).items():
            if not isinstance(val, str):
                return f"{key}.{sub} 必须是字符串"
    for i, shot in enumerate(cfg["screenshots"]):
        if not isinstance(shot, dict) or not isinstance(shot.get("src"), str) or not shot["src"]:
            return f"screenshots[{i}] 必须是对象，且 src 必须是非空字符串"
        for sub in ("alt", "caption"):
            if sub in shot and not isinstance(shot[sub], str):
                return f"screenshots[{i}].{sub} 必须是字符串"
    for key in ("section_titles",):
        for sub, val in (cfg.get(key) or {}).items():
            if not isinstance(val, str) or not val.strip():
                return f"{key}.{sub} 必须是非空字符串"
    return None


# ---------- selftest（B2/B10，早期修订） ----------

def selftest():
    """自检（早期修订）：首跑 exit 语义（V3-1 补盲区，硬要求）＋幂等连验＋K-4 重复注入
    ＋未配置节 FAIL＋双语互认＋守卫配置化。全过打印 PASS 返回 0。不需要输入文件。"""
    results = []
    base_cfg = dict(DEFAULTS)
    base_cfg["screenshots"] = [{"src": "shot.png", "alt": "s", "caption": "c"}]

    sample = """# Demo
[中文](README.md) | [EN](README.en.md)

## 0. 前置
正文行一。

### 1. 用法
跑一下。

## 收尾
完。
"""
    # ① 首跑 exit 语义（V3-1 新增）：干净 README 首跑应 exit 0——预期注入记降级、不判 FAIL
    DEGRADATIONS.clear()
    once, rep = restyle(sample, base_cfg)
    dropped, multiset, order = verify(sample, once, base_cfg["avatar_dir"])
    fails1, notices1 = extra_sections(sample, once, base_cfg)
    bad_first = bool(dropped) or bool(multiset) or order or bool(fails1)
    results.append(("首跑 exit 0（预期注入不报错——V3-1 补盲区）", not bad_first,
                    f"fails={fails1}，notices={len(notices1)} 条降级声明（早期某轮 3/3 撞的缺口）"))

    # ② 幂等连验：对输出再完整跑一遍，二次与一次 diff 为零
    DEGRADATIONS.clear()
    twice, _ = restyle(once, base_cfg)
    results.append(("幂等连验：二跑 diff=0", twice == once,
                    "对输出再完整跑一遍，二次应与一次逐字符一致"))

    # ③ K-4 真重复注入必须继续 FAIL（四格判第 1 格，不能改没了）
    poisoned = once.replace(sec(base_cfg, "screenshots"),
                            sec(base_cfg, "screenshots") + "\n\n<sub>旧截图</sub>\n\n"
                            + sec(base_cfg, "screenshots"), 1)
    fails_k4, _ = extra_sections(sample, poisoned, base_cfg)
    results.append(("重复注入 FAIL（K-4 必逮）", len(fails_k4) >= 1,
                    f"检出 {fails_k4}（精确同名节出现 2 次）"))

    # ④ 未配置注入的节出现 → FAIL（四格判第 3 格）
    bare_cfg = dict(DEFAULTS)   # screenshots/flow 均未配置
    manual = sample.replace("## 0. 前置",
                            sec(bare_cfg, "screenshots") + "\n\n<div>手动塞的节</div>\n\n## 0. 前置", 1)
    fails_manual, _ = extra_sections(sample, manual, bare_cfg)
    results.append(("未配置注入的节 FAIL", len(fails_manual) >= 1,
                    f"检出 {fails_manual}（管道没配置 screenshots 却出现该节）"))

    # ⑤ 双语互认（R3 回归）：英文样例不误报降级
    en_sample = "# Demo\n[中文](README.md) | [EN](README.en.md)\n\n## Body\nline.\n"
    DEGRADATIONS.clear()
    restyle(en_sample, dict(DEFAULTS))
    deg = [d for d in DEGRADATIONS if "无语言切换行" in d]
    results.append(("双语互认（R3 回归）：英文行不误报降级", not deg,
                    "英文样例不应触发'无语言切换行'降级"))

    # ⑥ 守卫配置化（B10 回归）：本地化标题后守卫仍生效（不重复注入）
    en_cfg = dict(DEFAULTS)
    en_cfg["section_titles"] = {"screenshots": "Screenshots", "flow": "Flow", "toc": "Contents"}
    en_cfg["screenshots"] = [{"src": "shot.png", "alt": "s", "caption": "c"}]
    en_src = "# Demo\n[中文](README.md) | [EN](README.en.md)\n\n## Body\nline.\n"
    en_once, _ = restyle(en_src, en_cfg)   # 第一次：注入 ## Screenshots
    DEGRADATIONS.clear()
    en_twice, _ = restyle(en_once, en_cfg)  # 第二次：守卫按配置标题识别，不再注入
    n = len(re.findall(r"^## Screenshots\s*$", en_twice, flags=re.M))
    results.append(("守卫配置化（B10 回归）：本地化标题不重复注入", n == 1,
                    f"'## Screenshots' 出现 {n} 次（期望 1，二跑守卫生效）"))

    # ⑦ 语言混杂警告（早期修订 P1 组合修；早期修订 R2 后夹具＝册子产物形态——署名收尾/资源路径/零星残留，
    #    不再自造"理想最小件"：早期修订 三个新用例全挑能过的形态、真件上两层是死的，§五教训）
    def _deg_lang():
        return [d for d in DEGRADATIONS if "语言混杂" in d]

    DEGRADATIONS.clear()
    restyle(en_src, dict(DEFAULTS))   # en_src 无汉字＋DEFAULTS 标题中文 → 应触发警告
    deg_lang = _deg_lang()
    results.append(("语言混杂警告：英文文档＋中文注入值→显式降级", len(deg_lang) >= 1,
                    f"警告={deg_lang[:1]}"))

    # ⑦b 册子形态（§1 第 7 段强制署名收尾）：早期修订 版警告恒不触发（R2 D/E 隔离实锤），修后须触发
    DEGRADATIONS.clear()
    restyle(en_src + "Produced by Example Team.\n", dict(DEFAULTS))
    deg_lang = _deg_lang()
    results.append(("语言混杂警告：带册子署名收尾仍触发（R2 修）", len(deg_lang) >= 1,
                    f"{len(deg_lang)} 条（署名行走 DEFAULT_CJK_ALLOW 豁免，不掩盖英文主语言）"))

    # ⑦c 零星残留不掩盖主语言：英文文档夹残留（真发布件朋友席形态）＋资源路径 → 仍触发
    en_res = (en_src
              + "Produced by Example Team.\n\n"
              + '<p align="center">Contributor A　Contributor B　Contributor C</p>\n\n'
              + '<img src="assets/截图/主界面.png" width="900" alt="screenshot">\n\n')
    DEGRADATIONS.clear()
    restyle(en_res, dict(DEFAULTS))
    deg_lang = _deg_lang()
    results.append(("语言混杂警告：零星残留＋资源路径不掩盖英文主语言（R1/R2 修）", len(deg_lang) >= 1,
                    f"{len(deg_lang)} 条（1 行残留 / 7 行内容，未过半）"))

    # ⑦d 中文文档＋中文注入值 → 不警告（本地化件无混杂问题）
    DEGRADATIONS.clear()
    restyle(sample, dict(DEFAULTS))
    results.append(("语言混杂警告：中文文档不误报", len(_deg_lang()) == 0,
                    f"{len(_deg_lang())} 条（命中行过半＝文档本身中文）"))

    # ⑦e config 全英文（en_cfg 形态＝分册② §4 治因正解）→ 不警告
    DEGRADATIONS.clear()
    restyle(en_src, dict(en_cfg))
    results.append(("语言混杂警告：英文 config 不误报", len(_deg_lang()) == 0,
                    f"{len(_deg_lang())} 条"))

    # ⑦f config 注入值仅含署名字面量 → 不警告（DEFAULT_CJK_ALLOW 单一真源豁免，config 侧同源）
    sig_cfg = dict(en_cfg)   # 基座＝英文标题表；中文只剩署名字面量本身
    sig_cfg["screenshots"] = [{"src": "a.png", "alt": "shot", "caption": "Produced by Example Team"}]
    DEGRADATIONS.clear()
    restyle(en_src, sig_cfg)
    results.append(("语言混杂警告：config 仅署名字面量不误报", len(_deg_lang()) == 0,
                    f"{len(_deg_lang())} 条"))
    DEGRADATIONS.clear()

    # ⑧ site_line 前缀可配（④-2：硬编码中文曾使英文版配 site_line 必进 CJK）
    _sl_en = dict(en_cfg)   # 基座＝英文标题表（DEFAULTS 中文标题注入英文稿＝④-2 同族雷）
    _sl_en["site_line"] = {"url": "https://example.com/tools", "name": "More tools",
                           "text": "More from this maintainer:"}
    _out_sl, _rep_sl = restyle(en_src, _sl_en)
    # 断言口径：en_src 自带语言切换行"[中文](README.md)"（#35 合法 CJK 豁免形态），故不断言"零 CJK"，
    # 断言"site_line 前缀不含任何硬编码中文＋英文前缀已在"。
    results.append(("site_line：英文 text 键→前缀不再是中文硬编码（④-2 修）",
                    ("More from this maintainer:" in _out_sl)
                    and re.search(r"[\u4e00-\u9fff][^<\n]*<a href=\"https://example\.com/tools\"", _out_sl) is None,
                    "查正文"))
    _sl_def = dict(DEFAULTS)
    _sl_def["site_line"] = {"url": "https://example.com/tools", "name": "更多小工具"}
    _out_sl2, _rep_sl2 = restyle("# 标题\n\n## 一\n\n中文正文。\n", _sl_def)
    results.append(("site_line：缺省 text→无前缀（中性，中英稿都不夹带）",
                    ('<a href="https://example.com/tools">更多小工具</a>' in _out_sl2)
                    and re.search(r"[\u4e00-\u9fff][^<>\n]*：\s*<a href", _out_sl2) is None, "查正文"))
    # 审查修正 负测：单引号宽度头像行——step_avatars 改写（单双都认）＋verify 归一化同步，整链不误判
    _av_body = "# Demo\n\n" + '<img src="assets/team/avatar-x.png" width=\'120\'>\n'
    _av_cfg = {"avatar_dir": "assets/team/"}
    _av_styled = step_avatars(_av_body, _av_cfg)
    _av_verify = verify(_av_body, _av_styled, _av_cfg["avatar_dir"])
    results.append(("头像宽度：单引号行改写后 verify 不误判（审查修正 半修补）",
                    _av_verify[0] == [], f"被删改行 {_av_verify[0]}"))

    # ⑨ --check 正向版式校验：未整形原文必须缺项，一次输出必须齐全。
    _check_cfg = dict(DEFAULTS)  # toc_insert_before=None 是合法默认，但目录仍是必检标准节
    _check_cfg["screenshots"] = [{"src": "shot.png", "alt": "s", "caption": "c"}]
    _raw_missing = missing_expected_sections(sample, _check_cfg)
    _styled, _ = restyle(sample, _check_cfg)
    _styled_missing = missing_expected_sections(_styled, _check_cfg)
    results.append(("--check 正向版式：未整形判红、一次输出可过",
                    "本文目录" in _raw_missing and "界面一览" in _raw_missing and not _styled_missing,
                    f"原文缺 {_raw_missing} / 输出缺 {_styled_missing}"))

    # ⑩ config 结构错误必须被人话拦下，不落到 AttributeError/KeyError。
    _bad_cfgs = ({"section_titles": "oops"}, {"screenshots": [{"alt": "x"}]},
                 {"badges": "oops"}, {"icon": "oops"}, {"avatar_dir": 1}, {"flow": "oops"})
    _config_errors = [validate_config(deep_merge(DEFAULTS, c)) for c in _bad_cfgs]
    results.append(("config 六类结构错误均给中文输入错误", all(_config_errors),
                    f"{len([e for e in _config_errors if e])}/{len(_bad_cfgs)} 命中；合法默认={validate_config(dict(DEFAULTS))}"))

    print("# restyle_readme.py --selftest")
    all_ok = True
    for name, ok, msg in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}  {msg}")
        all_ok = all_ok and ok
    print("selftest 结论：" + ("全过" if all_ok else "有 FAIL，见上"))
    return 0 if all_ok else 1


def _lang_mismatch_warning(original, cfg):
    """工具层语言混杂警告（早期修订 P1 组合修；早期修订 R2 修——复核：早期修订 版无署名/路径豁免，
    册子分册② §1 第 7 段强制的署名收尾使本警告在任何符合册子的英文版上恒不触发）。
    中文判定复用 en_check 的 check_cjk＋DEFAULT_CJK_ALLOW（单一真源，与机器层同一张豁免表）：
    文档零命中、或命中行不过内容行半数（零星残留不掩盖文档主语言）＝英文文档；config 注入值
    （内容字段：section_titles/icon alt/screenshots caption+alt/flow caption/wall summary/
    site_line name/badges；路径字段不查）经同一闸判出汉字 → 显式降级警告（非阻断）。
    治因配套判据：英文版美化须另备英文 config（分册② §4）。"""
    hits = check_cjk(original, DEFAULT_CJK_ALLOW)
    if hits:
        content_lines = sum(1 for l in re.sub(r"```.*?```", "", original, flags=re.S).splitlines()
                            if l.strip())
        if len(hits) > content_lines / 2:
            return   # 命中行过半＝文档本身就是中文（本地化件），无混杂问题
    titles = cfg.get("section_titles", DEFAULTS["section_titles"])
    texts = list(titles.values())
    texts.append(str(cfg.get("icon", {}).get("alt", "")))
    for s in cfg.get("screenshots", []):
        texts.append(str(s.get("caption", "")))
        texts.append(str(s.get("alt", "")))
    flow = cfg.get("flow")
    if flow:
        texts.append(str(flow.get("caption", "")))
    wall = cfg.get("wall")
    if wall:
        texts.append(str(wall.get("summary", "")))
    site = cfg.get("site_line")
    if site:
        texts.append(str(site.get("name", "")))
    texts.extend(str(b) for b in cfg.get("badges", []))
    probe = "\n".join(t for t in texts if t)
    if check_cjk(probe, DEFAULT_CJK_ALLOW):   # config 侧同一闸：署名/语言锚等预置豁免同源生效
        DEGRADATIONS.append(
            "语言混杂警告：文档主体不含汉字但 config 注入值（section_titles/caption/alt/badges 等）含汉字——"
            "中文将进对外门面；英文版美化须另备英文 config（分册② §4），en_check A4 亦会拦 CJK 残留")


# ---------- main ----------

def restyle(text, cfg):
    crlf = "\r\n" in text
    if crlf:
        text = text.replace("\r\n", "\n")
    _lang_mismatch_warning(text, cfg)
    report = {"checked": 0, "unresolved": []}
    for fn in STEPS:
        if fn is step_anchor_audit:
            text, report = fn(text, cfg)
        else:
            text = fn(text, cfg)
    text = text.rstrip("\n") + "\n"
    return (text.replace("\n", "\r\n") if crlf else text), report


def main() -> int:
    ap = argparse.ArgumentParser(description="项目 README 版式整形（只动版式不动正文）")
    ap.add_argument("src", nargs="?", default=None)
    ap.add_argument("-o", "--out")
    ap.add_argument("-c", "--config", help="变量表 JSON（缺省内置默认）")
    ap.add_argument("--check", action="store_true",
                    help="只校验：正文未被改动、无多插节，且配置要求的标准版式已存在")
    ap.add_argument("--idempotent", action="store_true",
                    help="幂等连验（④-3，实测反馈）：对一次输出再完整跑一遍，二次 diff≠0 即 FAIL——"
                         "'再跑一遍 diff 必须为 0'从执行者要记得变成脚本自己判")
    ap.add_argument("--selftest", action="store_true",
                    help="自检：幂等连验＋多插节检测＋双语互认＋守卫配置化（不需要 src）")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.src:
        ap.error("缺少输入文件参数（或用 --selftest / --help）")

    if args.check and args.out:
        ap.error("--check 与 -o 不能同用：--check 只校验不写文件，-o 会被静默忽略（M1）")

    cfg = dict(DEFAULTS)
    if args.config:
        # 统一口径：输入/环境错误统一 exit 2，不甩 traceback
        try:
            loaded = json.loads(Path(args.config).read_text(encoding="utf-8-sig"))
            if not isinstance(loaded, dict):
                print("ERROR config 顶层必须是对象（{...}），不能是数组/字符串/数字", file=sys.stderr)
                return 2
            cfg = deep_merge(DEFAULTS, loaded)
        except FileNotFoundError:
            print(f"ERROR 找不到配置文件：{args.config}", file=sys.stderr)
            return 2
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"ERROR 配置读不了或不是合法 JSON：{args.config}（{e.__class__.__name__}）", file=sys.stderr)
            return 2
    config_error = validate_config(cfg)
    if config_error:
        print(f"ERROR config 格式错误：{config_error}", file=sys.stderr)
        return 2

    # M6 修：read_bytes 保原始换行（read_text 会把 CRLF 归一成 LF，令 crlf 分支成死代码）
    src_path = Path(args.src)
    if not src_path.is_file():
        print(f"ERROR 找不到输入文件：{src_path}（检查路径，或用 --help 看用法）", file=sys.stderr)
        return 2
    try:
        raw = src_path.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        print(f"ERROR 读不了输入文件：{src_path}（{e.__class__.__name__}）", file=sys.stderr)
        return 2
    global DEGRADATIONS
    DEGRADATIONS = []
    try:
        new, report = restyle(raw, cfg)
    except Fail as e:
        print(f"[restyle] 中止：{e}", file=sys.stderr)
        return 2

    dropped_lines, dropped_multiset, order_violation = verify(raw, new, cfg["avatar_dir"])
    layout_missing = missing_expected_sections(raw, cfg) if args.check else []
    if layout_missing:
        print(f"[restyle] --check 正向版式校验：缺 {len(layout_missing)} 项（未整形/标准节被删）："
              + "、".join(layout_missing), file=sys.stderr)
    injected_fails, injected_notices = extra_sections(raw, new, cfg)   # V3-1 四格判
    for s in injected_notices:   # 预期注入→显式降级声明（不判 FAIL）
        DEGRADATIONS.append(f"标准节注入（预期语义）：{s}")
    if DEGRADATIONS:
        print(f"[restyle] 显式降级 {len(DEGRADATIONS)} 项（输入形态差异/预期注入，非静默）：", file=sys.stderr)
        for d in DEGRADATIONS:
            print(f"   ↓ {d}", file=sys.stderr)
    print(f"[restyle] 逐字校验：被删改的原文行 {len(dropped_lines)}（应为 0）；"
          f"多重集差额 {len(dropped_multiset)}；顺序违例 {order_violation}", file=sys.stderr)
    for d in dropped_lines[:10]:
        print("   !", d[:90], file=sys.stderr)
    print(f"[restyle] 多插节校验（V3-1 四格判）：FAIL {len(injected_fails)}（应为 0；"
          f"预期注入已记降级，重复注入/未配置节才 FAIL）", file=sys.stderr)
    for s in injected_fails:
        print("   ! 多插：", s, file=sys.stderr)
    print(f"[restyle] 锚点审计：{report['checked']} 个页内链接，配不上 {len(report['unresolved'])} 个"
          f"（只报告不改写；验收须独立实现复算）", file=sys.stderr)
    for u in report["unresolved"]:
        print(f"   ! 配不上：{u}", file=sys.stderr)

    bad = (bool(dropped_lines) or bool(dropped_multiset) or order_violation
           or bool(injected_fails) or bool(layout_missing))
    if args.idempotent:
        new2, _r2 = restyle(new, cfg)
        same = (new2 == new)
        print(f"[restyle] 幂等连验：二次输出与一次输出"
              f"{'逐字节相同（幂等成立）' if same else '存在差异（幂等 FAIL）'}", file=sys.stderr)
        bad = bad or not same
    if args.check:
        return 1 if bad else 0

    if args.out:
        Path(args.out).write_text(new, encoding="utf-8", newline="")
        print(f"[restyle] 已写出 {args.out}（{len(new)} 字符，sha256 "
              f"{hashlib.sha256(new.encode('utf-8')).hexdigest()[:16]}）", file=sys.stderr)
    else:
        sys.stdout.write(new)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
