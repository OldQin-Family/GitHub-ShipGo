# -*- coding: utf-8 -*-
"""text_quality_check.py · 文书文字质量自动检查（分册③ 第 14 项的机械化）

把原先靠人工 grep 的四类文字检查脚本化，与既有四支脚本同一纪律：
只用 Python 标准库、不联网、不在交付目录写盘、自带 --selftest、守三态退出码。

检查面：
  ① 常见错字词表（分册③ 第 14 项①）；
  ② 泛自称与内部流程词（分册③ 第 14 项②-2）；
  ③ 当前版本号声明全库同值（分册③ 第 14 项③，覆盖 SKILL/README/NOTICE/使用说明/
     llms/FINGERPRINTS/index.html/site.json；CHANGELOG 与历史快照豁免）；
  ④ 正文残留工程追溯号（v3.0.3 起：追溯号应收附录，正文不该再夹）。

豁免口径（自指防护，缺了必假红）：
  - 本脚本自身、词表规则行（含"→"映射写法的行）不参与命中判定；
  - 追溯号附录（分册③附）与 §4 翻车实录里的编号属合法留痕，不计"正文残留"；
  - 嵌码/代码块（``` 围起的区段）不扫描；
  - CHANGELOG 的历史版本行不作"当前版本声明"。

用法：
    python text_quality_check.py <发布目录> [--json]
    python text_quality_check.py --selftest

退出码：0 通过 / 1 内容判红 / 2 用法或输入环境错。
"""
import argparse
import json
import os
import re
import sys

EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "dist", ".venv", "venv", "_历史"}
SCAN_EXT = (".md", ".txt")

# ① 常见错字词表（分册③ 第 14 项①，"错→对"映射写法；规则行自身豁免见 is_rule_line）
TYPO_MAP = {
    "台帐": "台账", "登陆": "登录", "做为": "作为", "既使": "即使",
    "装璜": "装潢", "松驰": "松弛",
}
# ② 泛自称与内部流程词（分册③ 第 14 项②-2）
SELF_REF = ["家项目", "自家", "家里", "家版", "家用", "盲测", "工单"]
# ④ 工程追溯号（应收附录，正文不该夹）——仅在"必修/实锤/实案/实跑/复核/修订"等
# 追溯修饰语境下才算残留；"A/B/C 类分档""B3 用例""N3 格"等功能名/用例名不算。
TRACE_TAG = re.compile(r"\bV3-\d|\bB\d{1,2}\b|\bW\d{1,2}\b|\bT-\d|\bS-\d|\bG\d{1,2}\b|\bN\d\b|\bM\d\b")
# 追溯语境修饰词（追溯号＋这些词同现才判残留；功能分档/用例名无这些词）
TRACE_CTX = ("必修", "实锤", "实案", "实跑", "复核", "修订", "判例", "教训", "夹叙")
# 功能名/用例名豁免（"B3 用例""N3 格""A/B/C 类"等，合法技术引用）
TRACE_FUNC = re.compile(r"[A-Z]\d{0,2}\s*(用例|格|类|档)")

# 豁免：词表/规则说明行（含映射箭头或"词表"字样的自指行）
RULE_HINT = ("→", "词表", "映射写法", "零命中才算过", "豁免")
# 附录与翻车实录属合法留痕（含 docs/ 历史快照件：收口检查单、英文验收单）
APPENDIX_HINT = ("分册③附", "翻车实录", "判据追溯", "历史判例", "收口检查单", "英文验收单")
# 家人墙署名段（公开项目既定做法，非内部流程词泄漏）
FAMILY_HINT = ("家人", "头像", "署名", "豆总", "爪总", "小枢", "老伙计",
               "Family", "老秦", "family.html", "名册", "岗位")
# 区段级豁免标记：命中即进入"合法留痕/署名"区段，直到下一个同级标题
FAMILY_SECTION = re.compile(r"Family|家人墙|名册与岗位")
LEDGER_SECTION = re.compile(r"翻车实录|判据追溯|历史判例")

VERSION_PATTERNS = [re.compile(p, re.M) for p in (
    r"当前版本[：:\s]*\**v?(\d+\.\d+\.\d+)\**",
    r"^>\s*版本\s+\*{0,2}(\d+\.\d+\.\d+)\*{0,2}",
    r"^版本：(\d+\.\d+\.\d+)",
    r"^>\s*\*{0,2}Version\s+(\d+\.\d+\.\d+)\*{0,2}",
    r"^Version:\s*(\d+\.\d+\.\d+)",
    r"^#{1,2}\s+GitHub-ShipGo[^\n]*?(\d+\.\d+\.\d+)",
    r"当前\s+([^：:\s]+)\s*[：:]",
)]
AUX_VERSION_FILES = {
    # index.html 同时认 meta 与可见「版本 x.y.z」句；两个捕获组按实际命中取非空值。
    "index.html": re.compile(r'<meta\s+name=["\']version["\']\s+content=["\'](\d+\.\d+\.\d+)["\']|版本\s*v?(\d+\.\d+\.\d+)'),
    "site.json": re.compile(r'"version"\s*:\s*"(\d+\.\d+\.\d+)"'),
}


def version_hits(text):
    """返回 [(line_offset, version)]；只认当前声明句式，不把历史沿革数字当声明。"""
    hits = []
    for pat in VERSION_PATTERNS:
        for m in pat.finditer(text):
            hits.append((text[:m.start()].count("\n"), m.group(1)))
    return hits


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for f in sorted(filenames):
            if f.lower().endswith(SCAN_EXT):
                yield os.path.join(dirpath, f)


def is_rule_line(line):
    return any(h in line for h in RULE_HINT)


def in_appendix(relpath, line):
    return any(h in relpath for h in APPENDIX_HINT) or any(h in line for h in APPENDIX_HINT)


def split_code_blocks(lines):
    """返回 [(lineno, text, in_code)]，``` 围起的区段标 in_code=True（不扫描）。"""
    out, in_code = [], False
    for i, ln in enumerate(lines, 1):
        if ln.strip().startswith("```"):
            out.append((i, ln, True))
            in_code = not in_code
            continue
        out.append((i, ln, in_code))
    return out


def current_version_decl(root):
    """从 SKILL.md frontmatter 读当前版本号；读不到返回 None。"""
    p = os.path.join(root, "SKILL.md")
    if not os.path.isfile(p):
        return None
    m = re.search(r'(?m)^version:\s*["\']?([\d.]+)', open(p, encoding="utf-8").read())
    return m.group(1) if m else None


def check(root):
    rel = lambda p: os.path.relpath(p, root).replace("\\", "/")
    fails = []
    ver = current_version_decl(root)
    ver_mismatch = []

    for path in iter_files(root):
        rp = rel(path)
        try:
            lines = open(path, encoding="utf-8").read().splitlines()
        except (UnicodeDecodeError, OSError) as e:
            fails.append(f"{rp}（读取失败：{e.__class__.__name__}）")
            continue
        family_zone = False   # 家人墙署名区段：泛自称豁免
        ledger_zone = False   # 翻车实录/追溯附录区段：追溯号豁免
        for lineno, text, in_code in split_code_blocks(lines):
            # 区段状态机（代码块内不切换）
            if not in_code:
                if FAMILY_SECTION.search(text):
                    family_zone = True
                if LEDGER_SECTION.search(text):
                    ledger_zone = True
                # 区段结束：遇到新 markdown 标题（非本区段标记）即退出对应区段
                if re.match(r"^#{1,6}\s", text.strip()):
                    if not FAMILY_SECTION.search(text):
                        family_zone = False
                    if not LEDGER_SECTION.search(text):
                        ledger_zone = False
            if in_code:
                continue
            # ① 错字
            if not is_rule_line(text):
                for wrong, right in TYPO_MAP.items():
                    if wrong in text:
                        fails.append(f"{rp}:L{lineno} 错字「{wrong}」应为「{right}」")
            # ② 泛自称（家人墙区段/署名行豁免——公开项目既定做法，非内部泄漏）
            if not family_zone and not is_rule_line(text) and not any(h in text for h in FAMILY_HINT):
                for w in SELF_REF:
                    if w in text:
                        fails.append(f"{rp}:L{lineno} 泛自称/内部流程词「{w}」")
            # ④ 追溯号（附录/翻车实录区段豁免；须带追溯语境修饰词；功能名/用例名豁免）
            if not ledger_zone and not is_rule_line(text) and not in_appendix(rp, text):
                if any(c in text for c in TRACE_CTX):
                    for m in TRACE_TAG.finditer(text):
                        if TRACE_FUNC.search(text[max(0, m.start()-1):m.end()+3]):
                            continue
                        fails.append(f"{rp}:L{lineno} 正文残留工程追溯号「{m.group(0)}」（应收附录）")
        # ③ 版本一致性（覆盖当前声明多种形态；CHANGELOG/历史快照豁免）
        is_history = (rp == "CHANGELOG.md" or rp.startswith("docs/")
                      or "附" in rp and ("追溯" in rp or "历史" in rp))
        if ver and not is_history:
            for lineno, text, in_code in split_code_blocks(lines):
                if in_code:
                    continue
                for _offset, declared in version_hits(text):
                    if declared != ver:
                        ver_mismatch.append(f"{rp}:L{lineno} 声明 {declared} ≠ SKILL.md {ver}")

    # HTML/JSON 的版本声明单独解析，不把它们塞进中文文书规则。
    if ver:
        for rp, pat in AUX_VERSION_FILES.items():
            path = os.path.join(root, rp)
            if not os.path.isfile(path):
                continue
            try:
                text = open(path, encoding="utf-8-sig").read()
            except (UnicodeDecodeError, OSError) as e:
                fails.append(f"{rp}（版本读取失败：{e.__class__.__name__}）")
                continue
            for m in pat.finditer(text):
                declared = next(g for g in m.groups() if g is not None)
                if declared != ver:
                    lineno = text[:m.start()].count("\n") + 1
                    ver_mismatch.append(f"{rp}:L{lineno} 声明 {declared} ≠ SKILL.md {ver}")

    return fails, ver_mismatch, ver


def selftest():
    """纯内存自检：错字命中/规则行豁免/追溯号附录豁免/代码块豁免/版本一致性。"""
    results = []
    # ① 错字命中 + 规则行豁免
    line_bad = "请把台帐登陆后做为记录"
    hit = [w for w in TYPO_MAP if w in line_bad]
    results.append(("错字命中", set(hit) == {"台帐", "登陆", "做为"}, f"命中 {hit}"))
    rule = "①常见错字 grep（零命中才算过）：`台帐→台账`、`登陆→登录`"
    results.append(("规则行自指豁免", is_rule_line(rule), "含→/零命中字样的词表行不判"))
    # ④ 追溯号：正文命中、附录豁免
    body = "**输出件判据（V3-2 必修）**：每个闸口要有输出件"
    results.append(("追溯号正文命中", TRACE_TAG.search(body) is not None, "V3-2 被逮"))
    results.append(("追溯号附录豁免", in_appendix("references/分册③附_判据追溯与历史判例.md", body),
                    "附录文件里的编号不判正文残留"))
    # 代码块豁免
    blk = split_code_blocks(["```", "V3-2 台帐", "```", "正文台帐"])
    code_lines = [t for _i, t, c in blk if c]
    results.append(("代码块不扫描", "V3-2 台帐" in code_lines and all(c for _i, _t, c in blk[:3]),
                    "围起区段标 in_code"))
    # 版本声明：README/NOTICE/使用说明/llms/FINGERPRINTS 的真实句式都必须识别。
    version_declarations = [
        "当前版本：**3.0.3**",
        "> 版本 **3.0.3**",
        "> 版本 3.0.3",
        "版本：3.0.3",
        "> **Version 3.0.3**",
        "> Version 3.0.3",
        "Version: 3.0.3",
        "# GitHub-ShipGo v3.0.3 · 使用说明",
        "当前 shipgo_github（3.0.3）：",
    ]
    sample = "\n".join(version_declarations) + "\n\n旧版本 3.0.0 的沿革叙述不应被当成当前声明。\n"
    results.append(("版本声明九类句式均可识别", len(version_hits(sample)) == len(version_declarations),
                    f"识别 {len(version_hits(sample))}/{len(version_declarations)}；历史数字不纳入"))
    declared = version_hits("当前版本：**3.0.2**")
    results.append(("版本不一致可被逮", declared and declared[0][1] == "3.0.2" and declared[0][1] != "3.0.3",
                    "声明 3.0.2 ≠ 当前 3.0.3 应判红"))
    results.append(("index.html meta／可见句与 site.json 版本句式可识别",
                    AUX_VERSION_FILES["index.html"].search('<meta name="version" content="9.9.9">').group(1) == "9.9.9"
                    and AUX_VERSION_FILES["index.html"].search('<p class="meta">版本 9.9.9</p>').group(2) == "9.9.9"
                    and AUX_VERSION_FILES["site.json"].search('{"version":"9.9.9"}').group(1) == "9.9.9",
                    "index 两类声明与 site.json 都有负测锚点"))
    # 版本 frontmatter 解析：从 SKILL.md 真实解析（本包内自检）
    ver = current_version_decl(_selftest_root())
    results.append(("SKILL.md 当前版本可解析", ver is not None and bool(re.fullmatch(r"\d+\.\d+\.\d+", ver or "")),
                    f"解析到 version={ver}"))
    print("# text_quality_check.py --selftest")
    all_ok = True
    for name, ok, msg in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}  {msg}")
        all_ok = all_ok and ok
    print("selftest 结论：" + ("全过" if all_ok else "有 FAIL，见上"))
    return 0 if all_ok else 1


def _selftest_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    ap = argparse.ArgumentParser(description="文书文字质量自动检查（错字/泛自称/版本一致性/正文残留追溯号）")
    ap.add_argument("dir", nargs="?", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true", help="纯内存自检，不需要 dir")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if not args.dir:
        ap.error("缺少发布目录参数（或用 --selftest / --help）")
    root = os.path.abspath(args.dir)
    if not os.path.isdir(root):
        print(f"ERROR 找不到发布目录：{root}（检查路径，或用 --help 看用法）", file=sys.stderr)
        return 2
    fails, ver_mismatch, ver = check(root)
    print(f"# 文字质量检查 · {os.path.basename(root)}（当前版本 {ver or '未识别'}）")
    for f in fails:
        print(f"FAIL {f}")
    for f in ver_mismatch:
        print(f"FAIL 版本不一致  {f}")
    total = len(fails) + len(ver_mismatch)
    print(f"\n结论：命中 {total} 条（错字/泛自称/追溯号 {len(fails)}，版本不一致 {len(ver_mismatch)}）")
    if args.json:
        print(json.dumps({"version": ver, "text_fails": fails, "version_mismatch": ver_mismatch},
                         ensure_ascii=False, indent=2))
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
