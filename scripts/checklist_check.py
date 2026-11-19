# -*- coding: utf-8 -*-
"""checklist_check.py · 必选/条件件存在性自动核查（分册③ 第 2 项的机械化，#27）

来源：一次实测反馈（"人工 ls 逮 5 缺件"→自动化）＋顺手性尺子
（机器能干的活压给机器）。

用法：
    python checklist_check.py <发布目录> [--list 清单.md] [--json]

    --list  分册①样式的清单 md（含 `件名` 与 必选/条件/建议 的表格）。
            缺省解析本 skill 的 references/分册①（旧布局 分册/ 仍兼容）。
    --json  追加机器可读输出。

判读口径：
    必选  → 必须存在，缺 = FAIL；
    条件  → 存在则过；缺 = WARN（须在 FINGERPRINTS/CHANGELOG 有 N/A 说明）；
    建议  → 缺 = INFO（可接受）；
    特例  → FINGERPRINTS.md 豁免（第⑦步生成）；无反引号件名的行 → 人工核清单。
"""
import argparse
import json
import os
import re
import sys

EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "dist", ".venv", "venv", "_历史"}
SELF = "FINGERPRINTS.md"
# B11 修（早期修订）：语义映射（清单描述行 → 盘上判定规则）——从精确键改子串匹配＋扩充
# "本体代码对外净化检查"这类描述行旧版解析不到落人工核（三个执行者独立复现）
# 本体代码扩展名白名单（审查修正）：对外版面向任意语言的项目，只认 .py 会把
# Node/Go/Rust 等齐装满员的项目冤判成“必选缺”。判据是“有源码即有本体”，
# 白名单覆盖常见源码扩展名；清单条目描述同步见分册①“本体代码”行。
CODE_EXT = (
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".rs",
    ".java", ".kt", ".swift", ".c", ".cc", ".cpp", ".h", ".hpp", ".cs",
    ".rb", ".php", ".sh", ".ps1", ".psm1", ".lua", ".dart", ".vue",
)
SEMANTIC = [
    ("分发 zip", lambda rels: any(r.lower().endswith(".zip") for r in rels)),
    ("本体代码", lambda rels: any(r.lower().endswith(CODE_EXT) for r in rels)),
]


def semantic_lookup(name):
    for key, fn in SEMANTIC:
        if key in name:
            return fn
    return None


def parse_list(md_path):
    """从分册①样式 md 里解析清单表：返回 [(件名, 级别, 原行)]。解析不了的行进人工核。"""
    text = open(md_path, encoding="utf-8").read()
    items, manual = [], []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|") or "---" in s:
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        names = [n.strip() for n in re.findall(r"`([^`]+)`", cells[0])]
        level = None
        for key in ("必选", "条件", "建议"):
            if len(cells) > 1 and key in cells[1]:  # 审查修正：三元嵌套改直读
                level = key
                break
        if level is None and len(cells) > 1:
            for key in ("必选", "条件", "建议"):
                if key in s:
                    level = key
                    break
        if not names or level is None:
            if "必选" in s or "条件" in s or "建议" in s:
                manual.append(s[:80])
            continue
        # M4 修：一格写两件（`NOTICE.md` / `NOTICE.en.md`）时全部入清单，任一缺即红
        for name in names:
            items.append((name, level, s[:80]))
    return items, manual


NA_HEADING = re.compile(r"^#{2,3}\s+条件件 N/A 立牌\s*$")
NA_LINE = re.compile(
    r"^\s*[-*]\s+(?:\*\*)?`?([^`：:*]+?)`?(?:\*\*)?\s*[：:]\s*"
    r"N/A\s*[（(]\s*([^）)]+?)\s*[）)]")


def _na_key(name):
    """立牌键与清单件名各自规范化后精确匹配；不做包含/子串豁免。"""
    key = name.strip().strip("`").replace("**", "").strip()
    return key if key == "分发 zip" else key.rstrip("/")


def parse_na_notes_text(text):
    """只认 FINGERPRINTS.md 的「条件件 N/A 立牌」专节；返回 件名→来源行号。"""
    notes, in_section = {}, False
    for lineno, line in enumerate(text.splitlines(), 1):
        if NA_HEADING.match(line):
            in_section = True
            continue
        if in_section and re.match(r"^#{1,3}\s+", line):
            break
        if not in_section:
            continue
        m = NA_LINE.match(line)
        if m and m.group(2).strip():
            notes[_na_key(m.group(1))] = f"FINGERPRINTS.md:L{lineno}"
    return notes


def load_na_notes(root):
    fp = os.path.join(root, SELF)
    if not os.path.isfile(fp):
        return {}
    with open(fp, "r", encoding="utf-8", errors="replace") as f:
        return parse_na_notes_text(f.read())


def na_allowed(name, level):
    """N/A 仅适用于条件件与分发 zip；必选件一律不得豁免。"""
    return level == "条件" or name == "分发 zip"


def selftest():
    """B2/B11 自检——解析本 skill 分册①（只读，不落任何文件）＋语义匹配逻辑。"""
    results = []
    here = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.dirname(here)
    cands = (os.path.join(skill_root, "references", "分册①_定名查重与素材清单.md"),
             os.path.join(skill_root, "分册", "分册①_定名查重与素材清单.md"))
    booklet = next((c for c in cands if os.path.isfile(c)), None)
    if booklet:
        items, manual = parse_list(booklet)
        levels = {lv for _, lv, _ in items}
        ok = len(items) > 0 and "必选" in levels
        results.append(("B11 分册①解析", ok,
                        f"条目 {len(items)}（人工核 {len(manual)}），级别 {sorted(levels)}"))
    else:
        # 缺件＝FAIL：不许"未找到就跳过"。跳过式 PASS 会让新目录布局下的 selftest 空转仍全绿（假绿）。
        results.append(("B11 分册①解析", False,
                        "未找到分册①（references/ 与 分册/ 都试过）：references/分册①_定名查重与素材清单.md、"
                        "分册/分册①_定名查重与素材清单.md"))

    fn_zip = semantic_lookup("分发 zip")
    ok_zip = fn_zip is not None and fn_zip({"dist.zip", "a.txt"})
    results.append(("B11 语义匹配：分发 zip", ok_zip, "子串匹配＋zip 存在判定"))
    fn_code = semantic_lookup("本体代码对外净化检查")
    ok_code = fn_code is not None and fn_code({"ExampleApp.py"})
    results.append(("B11 语义匹配：本体代码描述行", ok_code,
                    "旧版落人工核的描述行，现在自动判常见源码扩展名"))
    ok_multi = fn_code is not None and fn_code({"app.js", "main.go", "lib.rs", "README.md"})
    results.append(("B11 语义匹配：非 Python 源码也命中（审查修正 负测）", ok_multi,
                    "js/go/rs 项目不再冤判本体代码缺"))

    sample = """## 条件件 N/A 立牌
- **`tests/`**：N/A（纯库项目无独立测试目录）
- **分发 zip**：N/A（skill 包随整包克隆分发）
- **`packages/<渠道>-<name>/`**：N/A（本次无渠道分包）

## 其他章节
- **NOTICE.md**：N/A（越区，不得读取）
"""
    notes = parse_na_notes_text(sample)
    ok_na = (notes.get(_na_key("tests/"), "").startswith("FINGERPRINTS.md:L")
             and _na_key("packages/<渠道>-<name>/") in notes
             and _na_key("NOTICE.md") not in notes
             and _na_key("tests2/单元测试.py") not in notes)
    results.append(("B11 N/A 专节解析与精确匹配", ok_na,
                    "只认专节；目录名不串豁免；越区/无名 N/A 不生效"))
    ok_scope = (na_allowed("tests/", "条件") and na_allowed("分发 zip", "必选")
                and not na_allowed("NOTICE.md", "必选") and not na_allowed("tests/", "建议"))
    results.append(("B11 N/A 适用范围", ok_scope,
                    "仅条件件与分发 zip；必选/建议不豁免"))

    print("# checklist_check.py --selftest")
    all_ok = True
    for name, ok, msg in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}  {msg}")
        all_ok = all_ok and ok
    print("selftest 结论：" + ("全过" if all_ok else "有 FAIL，见上"))
    return 0 if all_ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="必选/条件件存在性自动核查（早期修订）")
    ap.add_argument("dir", nargs="?", default=None)
    ap.add_argument("--list", help="清单 md 路径（缺省自动找分册①）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--stage", choices=("pre", "final"), default="final",
                    help="核查阶段（V3-3 修，早期修订）：pre＝⑥过闸前（分发 zip 未打、"
                         "FINGERPRINTS.md 未生成，属'待生成'，打独立字样不判）；"
                         "final＝默认＝出货态（FINGERPRINTS.md 缺＝FAIL；zip/条件件缺失须在同一账的"
                         "「条件件 N/A 立牌」专节逐件精确登记，否则 FAIL）")
    ap.add_argument("--selftest", action="store_true",
                    help="自检（B2/B11）：解析分册①＋语义匹配，不需要 dir")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.dir:
        ap.error("缺少发布目录参数（或用 --selftest / --help）")

    root = os.path.abspath(args.dir)
    # 统一口径：输入/环境错误 exit 2（目录不存在时 os.walk 会静默给空清单，误判成"全缺"）
    if not os.path.isdir(root):
        print(f"ERROR 找不到发布目录：{root}（检查路径，或用 --help 看用法）", file=sys.stderr)
        return 2
    inv = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for f in filenames:
            inv.add(os.path.relpath(os.path.join(dirpath, f), root).replace("\\", "/"))

    list_path = args.list
    if not list_path:
        # 自动找：本脚本随 skill 走 → 用 __file__ 推导本 skill 分册①
        # 布局两种都试：新布局 "references/"（对外版）／旧布局 "分册/"（兼容）
        here = os.path.dirname(os.path.abspath(__file__))
        skill_root = os.path.dirname(here)
        for cand in (os.path.join(skill_root, "references", "分册①_定名查重与素材清单.md"),
                     os.path.join(skill_root, "分册", "分册①_定名查重与素材清单.md")):
            if os.path.isfile(cand):
                list_path = cand
                break
        if not list_path:
            print("FAIL: 未找到分册①清单（references/ 与 分册/ 都试过），"
                  "请用 --list 指定")
            return 2

    items, manual = parse_list(list_path)
    if not items:
        print("FAIL: 清单里没解析到条目（表格格式见分册① §1）")
        return 2

    fail, warn, info, pending, na = [], [], [], [], []
    na_notes = load_na_notes(root) if args.stage == "final" else {}

    def exists_on_disk(name):
        """清单件名 → 盘上存在判定：完整路径 / 目录尾斜杠 / 占位符 glob / 语义映射。"""
        import fnmatch
        if name == SELF:
            return True
        fn = semantic_lookup(name)
        if fn is not None:
            return fn(inv)
        # 占位符 <x> → 通配 *
        pat = re.sub(r"<[^>]+>", "*", name)
        if name.endswith("/"):
            d = name.rstrip("/")
            return any(r == d or r.startswith(d + "/") for r in inv) or                    any(fnmatch.fnmatch(r, pat + "/*") or fnmatch.fnmatch(r + "/", pat)
                       for r in inv)
        if "<" in name:  # 占位符文件名（如 启动<项目>.bat）
            return any(fnmatch.fnmatch(r, pat) for r in inv)
        if name in inv:
            return True
        # 目录型（清单写目录名不带尾斜杠）
        return any(r == name or r.startswith(name + "/") for r in inv)

    for name, level, _ in items:
        if name == SELF:
            # 不许静默（委托人 11-13 拍）：账在＝通过；账缺分两态——
            # 引导态（--stage pre，⑥ 过闸前）：打独立字样，不计 PASS/FAIL；
            # 出货态（final，默认）：账是整包的命根子，缺＝坏包＝FAIL。
            if name in inv:
                continue
            if args.stage == "pre":
                pending.append(name)
            else:
                fail.append(f"{name}（必选·出货态缺账＝坏包）")
            continue
        if exists_on_disk(name):
            continue
        row = f"{name}（{level}）"
        if args.stage == "final" and na_allowed(name, level):
            source = na_notes.get(_na_key(name))
            if source:
                na.append(f"{name}（{level}）〔{source}〕")
                continue
            if level == "条件":
                fail.append(row + "（缺且无有效 N/A 立牌）")
                continue
        if level == "必选":
            # pre 阶段分发 zip 未打＝待生成；final 缺 zip 且无有效 N/A 立牌＝FAIL。
            if args.stage == "pre" and "分发 zip" in name:
                warn.append(row + "〔pre 阶段：分发 zip 待生成（⑥其余项过闸后打）〕")
            else:
                fail.append(row)
        elif level == "条件":
            warn.append(row + "〔pre 阶段：final 前须补有效 N/A 立牌〕")
        else:
            info.append(row)

    print(f"# 必选/条件件存在性核查 · {os.path.basename(root)}")
    print(f"# 清单条目 {len(items)}（人工核 {len(manual)}）｜盘点实物 {len(inv)} 件")
    for r in fail:
        print(f"FAIL {'条件缺' if '（条件）' in r else '必选缺'}  {r}")
    # M5 修：解析不了的行不许只打一行"?"——没查＝没绿，按 FAIL 计并进退出码
    for m_ in manual:
        print(f"FAIL 未解析  {m_[:60]}")
    for r in warn:
        print(f"WARN 条件缺  {r}（须有 N/A 说明）")
    for r in info:
        print(f"INFO 建议缺  {r}（可接受）")
    for r in pending:
        print(f"----  {r}  未生成（账尚未创建）——不计 PASS/FAIL（pre 阶段；出货态缺失＝FAIL）")
    for r in na:
        print(f"---- N/A 立牌  {r}")
    print(f"\n结论：必选/条件失败 {len(fail)} / 未解析 {len(manual)} / "
          f"N/A 立牌 {len(na)} / pre 条件待立牌 {len(warn)} / 建议缺 {len(info)}")
    if args.json:
        print(json.dumps({"fail": fail, "unparsed": manual, "warn": warn, "info": info,
                          "pending": pending, "na": na, "manual": manual}, ensure_ascii=False, indent=2))
    return 0 if (not fail and not manual) else 1


if __name__ == "__main__":
    sys.exit(main())  # 审查修正：函数内重复 import json 已删（顶部已导入）
