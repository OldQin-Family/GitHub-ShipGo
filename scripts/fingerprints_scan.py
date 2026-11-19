# -*- coding: utf-8 -*-
"""fingerprints_scan.py v3 —— 扫描/校验双模式；两模式输出互相接头；zip 专节自动化。

口径：排除 .git node_modules dist .venv venv _历史；
      __pycache__ 目录与 *.pyc/*.pyo 不排除——升格为"净空违例"点名（W5-a，某轮返工：
      原先留在 EXCLUDE_DIRS 使特判不可达，G16 场景静默 exit 0）；
      排除文件 Thumbs.db desktop.ini .DS_Store。
安全：盘上路径一律 os.walk 自产；表内路径只做解析后的精确登记，不拿子串冒充登记。

v3 新增（#20/#26/#30 修）：
  · scan 遇 .zip 自动生成「分发 zip 专节」：zip 本体行＋CRC 行＋zip 内件行
    （arc 名带 zip: 前缀、SHA256 全值）——zip 内件从此由探针自动登记，
    人不再手写（手写 zip 内件与根件同名撞车的坑结构性消失）；
  · check 识别 zip: 前缀行：从 zip 内读取该件复算，不经盘上路径；
  · 报告口径区分「表行条目」（含对照扩展行与 zip: 行）与「盘点实物件」，
    并附口径说明（68 vs 67 误读的修法）。
"""
import hashlib
import os
import re
import sys
import zipfile

EXCLUDE_DIRS = {".git", "node_modules", "dist", ".venv", "venv", "_历史"}  # W5-a（四格夹具）: __pycache__ 移出——否则 L39 特判不可达死代码（G16 未闭合）
EXCLUDE_FILES = {"thumbs.db", "desktop.ini", ".ds_store"}
SELF = "FINGERPRINTS.md"   # 自身不入表（自指哈希不可能成立），默认豁免漏登记检查


def normalize(rel):
    return rel.replace("\\", "/")


def iter_inventory(root):
    """盘点索引。W5 修（早期修订）：__pycache__/*.pyc 不再静默排除——单独收集为"净空违例"
    （早期某轮 G16 实锤：运行期长出 __pycache__ 曾被误判 PASS，习惯推断不是判据，
    只能数出来）。返回 (inventory, violations)。"""
    root_abs = os.path.abspath(root)
    inventory = {}
    violations = []
    for dirpath, dirnames, filenames in os.walk(root_abs):
        if "__pycache__" in os.path.basename(dirpath):
            violations.append(normalize(os.path.relpath(dirpath, root_abs)) + "/（__pycache__ 目录）")
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for f in filenames:
            if f.lower().endswith((".pyc", ".pyo")):
                violations.append(normalize(os.path.relpath(os.path.join(dirpath, f), root_abs)) + "（字节码残留）")
                continue
            if f.lower() in EXCLUDE_FILES:
                continue
            full = os.path.join(dirpath, f)
            inventory[normalize(os.path.relpath(full, root_abs))] = full
    return inventory, violations


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _open_zip(path):
    """打开 zip；损坏/不可读＝输入环境错：一句人话＋返回 None（审查修正：
    退出码三态承诺“2＝用法或输入环境错，不甩 traceback”）。调用方见 None 即中止。"""
    try:
        return zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as e:
        print(f"ERROR zip 无法读取：{path}（{e.__class__.__name__}）——重下或删掉后重跑",
              file=sys.stderr)
        return None


def zip_section_lines(zip_path):
    """对一个 zip 生成专节行：本体行＋CRC 行＋zip 内件行（zip: 前缀＋全值哈希）。"""
    z = _open_zip(zip_path)
    if z is None:
        return None
    lines = []
    with z:
        crc_bad = z.testzip()
        crc_text = "CRC 全验 PASS" if crc_bad is None else f"CRC FAIL（{crc_bad}）"
        names = [n for n in z.namelist() if not n.endswith("/")]
        # 注释行放表格流之外（本段首行）——真机实测反馈：`# ↑` 插在表格中间会打断 markdown 表，
        # zip: 行变成无表头表格（"整段可粘"与"渲染可用"之间有缝）。
        lines.append(f"# 分发 zip 专节（探针自动生成）：内件 {len(names)} 件，{crc_text}，"
                     f"内件 arc 名带 zip: 前缀、SHA256 全值；下表为本体行＋内件行")
        lines.append(f"| `{os.path.basename(zip_path)}` | {os.path.getsize(zip_path):,} | "
                     f"`{sha256(zip_path).upper()}` |")
        for info in sorted(z.infolist(), key=lambda i: i.filename):
            if info.filename.endswith("/"):
                continue
            data = z.read(info.filename)
            lines.append(f"| `zip:{info.filename}` | {len(data):,} | "
                         f"`{sha256_bytes(data).upper()}` |")
    return lines


def scan_print(root):
    inv, _viol = iter_inventory(root)
    rows = [(rel, os.path.getsize(full), sha256(full)) for rel, full in sorted(inv.items())]
    print("| 文件 | 字节 | SHA256（前 16） |")
    print("|---|---|---|")
    zips = [rel for rel, _, _ in rows if rel.lower().endswith(".zip")]
    _pending_hdr = False  # zip 专节打断了主表：下一个普通件行前要补表头（真机实测反馈）
    for rel, size, digest in rows:
        if rel == SELF:
            continue
        if rel in zips:
            # zip 本体行由专节生成（含全值哈希），不再打严格行——避免同名行（同名撞车坑）
            # 真机实测反馈：专节注释行插在表格中间＝lazy continuation 把表吞成纯文本。
            # v3.0.1 小深复核定版顺序：**注释 → 空行 → 表头 → 分隔 → 数据行**（v1/v2/v3 三版
            # 都把注释留在表头之后，表照样被注释打断——"表数对"是代理指标，
            # 语义判据＝行必须在表里：每表 tbody ≥1 行、渲染无 <p>| 管行）。
            print("")
            sec = zip_section_lines(inv[rel])
            if sec is None:
                return 2
            print(sec[0])  # 注释行先出（在表头之前，不进表格流）
            print("")  # 空行断开注释与表
            print("| 文件 | 字节 | SHA256（前 16） |")
            print("|---|---|---|")
            for line in sec[1:]:
                print(line)
            print("")
            _pending_hdr = True  # 若后面还有普通件行，先补表头再打行；没有则不悬空表头
            continue
        if _pending_hdr:
            print("| 文件 | 字节 | SHA256（前 16） |")
            print("|---|---|---|")
            _pending_hdr = False
        print(f"| `{rel}` | {size:,} | `{digest[:16].upper()}` |")
    n_files = len(rows) - (1 if SELF in inv else 0)
    n_zip = len(zips)
    print(f"\n# 实物件 {n_files} 件（FINGERPRINTS.md 自身不入表；含分发 zip {n_zip} 个，"
          f"其 zip: 内件为虚拟行不计实物）")


def check(root):
    # 统一口径：根不存在属用法/环境错 → exit 2（缺 FINGERPRINTS 仍是判红 exit 1）
    if not os.path.isdir(root):
        print(f"ERROR 找不到目录：{root}（检查路径，或用 --help 看用法）", file=sys.stderr)
        return 2
    inv, viol = iter_inventory(root)
    # W5：净空违例先点名（__pycache__/*.pyc 静默排除的时代结束——它们现在是 FAIL 证据）
    for v in viol:
        print(f"FAIL 净空违例  {v}")
    if viol:
        print("（W5：以上为运行期残留，清理后重跑；发布目录不该有它们——分册③ 第 15 项判据）")
    if SELF not in inv:
        print("FAIL: 找不到 FINGERPRINTS.md")
        return 1
    text = open(inv[SELF], encoding="utf-8").read()
    # 表头结构自检：--check 只验数值对得上，验不了表能不能渲染——分隔行必须独占一行
    header_bad = 0
    for i, ln in enumerate(text.splitlines(), 1):
        s = ln.strip()
        if s.startswith("|---") and re.fullmatch(r"\|(?:[-: ]+\|)+", s) is None:
            print(f"FAIL 表头粘行  FINGERPRINTS.md:L{i} 分隔行未独占一行（渲染会坏）")
            header_bad += 1
    # 表前起块自检：Markdown 表格必须从块首开始——紧跟引用块/段落行会被并成纯文本（渲染坏）。
    # 与"分隔行独占一行"是两个形态：前者表还在、只是行坏；后者整表被吞、肉眼却像没问题。
    lines_all = text.splitlines()
    for i, ln in enumerate(lines_all):
        if re.fullmatch(r"\|(?:[-: ]+\|)+", ln.strip()):
            if i >= 2 and lines_all[i - 2].strip() != "":
                print(f"FAIL 表头未起块  FINGERPRINTS.md:L{i + 1} 表格前缺空行（表会并进上一段，渲染坏）")
                header_bad += 1
    entries = []          # (rel, size, digest, is_zip_arc)
    for m in re.finditer(r"`([^`]+)`\s*\|\s*([\d,]+)\s*\|\s*`([0-9A-Fa-f]{8,64})`", text):
        rel = normalize(m.group(1))
        if rel.startswith("zip:"):
            entries.append((rel, int(m.group(2).replace(",", "")), m.group(3).upper(), True))
        else:
            entries.append((rel, int(m.group(2).replace(",", "")), m.group(3).upper(), False))
    if not entries:
        print("FAIL: FINGERPRINTS.md 里没解析到表行")
        return 1

    ok = bad = missing = 0
    declared = set()
    # 审查修正：zip 名单预开缓存（with 正确关闭句柄，替换生成器内裸开＋死变量）；
    # 损坏 zip＝输入环境错 → 一句人话 + 中止 exit 2。
    zip_names = {}
    for r, full in sorted(inv.items()):
        if not r.lower().endswith(".zip"):
            continue
        z = _open_zip(full)
        if z is None:
            return 2
        with z:
            zip_names[r] = z.namelist()
    for rel, size, digest, is_arc in entries:
        declared.add(rel)
        if is_arc:
            arc = rel[4:]
            zrel = next((r for r in inv if r.lower().endswith(".zip")
                         and arc in zip_names.get(r, [])), None)
            # R1 修：全路径 inv[r]（相对路径在非目标 cwd 下崩，实跑逮出）
            if zrel is None:
                print(f"FAIL 缺件  {rel}（zip 内无此 arc 名，或目录中无对应 zip）")
                missing += 1
                continue
            z = _open_zip(inv[zrel])
            if z is None:
                return 2
            with z:
                data = z.read(arc)
            real, rsize = sha256_bytes(data), len(data)
            if real.upper().startswith(digest) and rsize == size:
                ok += 1
            else:
                print(f"FAIL 出入  {rel}  表:{digest}/{size:,}B  实算:{real[:len(digest)]}/{rsize:,}B")
                bad += 1
            continue
        if rel not in inv:
            print(f"FAIL 缺件  {rel}")
            missing += 1
            continue
        full = inv[rel]  # 路径取自盘点索引；表内字符串只做比对，从不拼读取路径
        real, rsize = sha256(full), os.path.getsize(full)
        if real.upper().startswith(digest) and rsize == size:
            ok += 1
        else:
            print(f"FAIL 出入  {rel}  表:{digest}/{size:,}B  实算:{real[:len(digest)]}/{rsize:,}B")
            bad += 1

    # CRC 复验：目录内每个 zip 全验一次
    crc_fail = []
    for r, full in sorted(inv.items()):
        if r.lower().endswith(".zip"):
            z = _open_zip(full)
            if z is None:
                return 2
            with z:
                badmember = z.testzip()
            if badmember is not None:
                crc_fail.append(f"{r}:{badmember}")
    if crc_fail:
        print("FAIL CRC  " + "；".join(crc_fail))

    # 反向对拍：实物必须各有自己的精确表行。路径只被说明文字提到不算登记。
    leak = 0
    for rel in sorted(inv):
        if rel == SELF or rel in declared:
            continue
        print(f"FAIL 漏登记  {rel}（各有精确表行才算登记；子串命中不算）")
        leak += 1

    # M3 修（代码审查）：zip 内件反向对拍——表里没有的 arc 一律 FAIL。
    # 只更新 zip 本体行、不登记新增内件时，旧版会报"表盘一致"（ghost.txt 实案）。
    declared_arcs = {rel[4:] for rel, _s, _d, is_arc in entries if is_arc}
    unreg = 0
    for r, full in sorted(inv.items()):
        if not r.lower().endswith(".zip"):
            continue
        z = _open_zip(full)
        if z is None:
            return 2
        with z:
            for arc in z.namelist():
                if arc.endswith("/"):
                    continue
                if arc not in declared_arcs:
                    print(f"FAIL 漏登记  zip:{r}!{arc}（zip 内有、表内无）")
                    unreg += 1

    counted = len(inv) - (1 if SELF in inv else 0)
    declared_physical = {rel for rel, _s, _d, is_arc in entries if not is_arc}
    count_mismatch = len(declared_physical) != counted
    if count_mismatch:
        print(f"FAIL 总件数  表内实物行 {len(declared_physical)} / 盘点实物 {counted}（不计 zip: 内件）")

    print(f"\n复算表行 {len(entries)} 项：PASS {ok} / 出入 {bad} / 缺件 {missing}"
          f"（表行含对照扩展行与 zip: 内件行，可多于实物件数——口径说明，非误读）")
    print(f"反向对拍：漏登记 {leak} 件；zip 内件漏登记 {unreg} 件；"
          f"总件数 {'一致' if not count_mismatch else '不一致'}；盘点实物 {counted} 件（zip: 行为虚拟行不计）")
    clean = (bad == 0 and missing == 0 and leak == 0 and unreg == 0 and header_bad == 0
             and not crc_fail and not viol and not count_mismatch)
    print("结论：" + ("表盘一致" if clean else "有出入，见上"))
    return 0 if clean else 1


if __name__ == "__main__":
    # X4 修（早期修订）：argparse 接管参数——v3 及之前错误输入（--help/拼错路径）被当目录参数
    # 静默吐空表 exit 0，错误伪装成功比报错危险（独立复现实锤）。
    # B2/B3 的 --selftest 不在本脚本实现：部分宿主平台对探测类脚本写入零容忍（env_probe 五次被拦同款），
    # 自检段见分册③ §2.1「四脚本自检段」（md 内嵌代码块，复制即跑）。
    import argparse
    ap = argparse.ArgumentParser(
        prog="fingerprints_scan.py",
        description="发布目录指纹扫描/校验（早期修订）——scan 出表可粘、check 对盘复算")
    ap.add_argument("dir", nargs="?", default=None, help="发布目录路径")
    ap.add_argument("--check", action="store_true",
                    help="校验模式：FINGERPRINTS.md 对盘复算（哈希全长＋zip CRC＋反向对拍）")
    args = ap.parse_args()
    if not args.dir:
        ap.error("缺少发布目录参数")
    # X4 补刀（早期件残留）：scan 模式给不存在的目录，os.walk 不报错走空→静默吐空表 exit 0
    # ——错误输入伪装成成功的空结果（X4 实锤情形之一）。scan/check 两模式统一拦。
    if not os.path.isdir(os.path.abspath(args.dir)):
        ap.error(f"发布目录不存在：{args.dir}")
    sys.exit(check(os.path.abspath(args.dir)) if args.check
             else (scan_print(os.path.abspath(args.dir)) or 0))
