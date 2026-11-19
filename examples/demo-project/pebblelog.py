# -*- coding: utf-8 -*-
"""PebbleLog —— 一个虚构的命令行笔记小工具（示例用，非真实产品）。

演示 GitHub-ShipGo 发布流程的台架：只往本地一个文件追加一行笔记。
只用 Python 标准库，不联网。
"""
import argparse
import os
import sys

DEFAULT_LOG = os.path.join(os.path.expanduser("~"), "pebblelog.txt")


def add_note(text, path=DEFAULT_LOG):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(text.rstrip("\n") + "\n")
    return path


def read_notes(path=DEFAULT_LOG):
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [ln.rstrip("\n") for ln in fh if ln.strip()]


def main():
    ap = argparse.ArgumentParser(prog="pebblelog", description="本地单行笔记小工具（示例）")
    ap.add_argument("text", nargs="?", help="要记下的一句话；省略则列出已有笔记")
    ap.add_argument("--file", default=DEFAULT_LOG, help="笔记文件路径")
    args = ap.parse_args()
    if args.text:
        p = add_note(args.text, args.file)
        print(f"已记下 → {p}")
    else:
        for ln in read_notes(args.file):
            print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main())
