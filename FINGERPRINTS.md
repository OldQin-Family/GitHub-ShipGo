# GitHub-ShipGo 全包账

> **状态：已封死（LOCKED）· 2026-11-19（v3.0.4 二次巡检整改验收后）** —— 本账与包内全部文件逐件对拍一致；此后再改任何件都须解封并重扫。
> **口径**：SHA256 前 16 位大写；**全包登记**——除本账自身外的全部文件，一件不落。
> 分发 zip 存在时，其 `zip:` 内件为虚拟行，不计入实物件数。
> **维护规矩**：任何文件改动后重跑探针，只更新受影响行，再跑 `--check` 至"表盘一致"；本账自身不入表。
> **重算命令**：`python -B -I -X utf8 scripts/fingerprints_scan.py .`（出表）／`python -B -I -X utf8 scripts/fingerprints_scan.py . --check`（对表）
> **退出码**：0 通过／1 判红／2 用法或输入环境错。
> **包版本**：见 `SKILL.md` frontmatter（当前 3.0.4）。
> **本次重出**：v3.0.4 外眼复核整改后依本 skill ⓪→⑦ 全流程重扫 —— ⓪ 预检四脚本 selftest＋四工具联检、⑤ 检查器与文书口径修订、⑦ 本表按当前实物重算。历史截图与历史快照保持原样。

| 文件 | 字节 | SHA256（前 16） |
|---|---|---|
| `.gitattributes` | 167 | `3F8697F27C75D555` |
| `.gitignore` | 51 | `A2A71CEDAEA56F60` |
| `ACKNOWLEDGEMENTS.md` | 1,077 | `339EEDC2CB6D2380` |
| `CHANGELOG.md` | 10,778 | `B480B6418095B66E` |
| `LICENSE` | 1,075 | `87B9C2221BE7749C` |
| `NOTICE.en.md` | 2,276 | `8D52F710237F63B5` |
| `NOTICE.md` | 1,846 | `6807D9DABFE65697` |
| `README.en.md` | 15,743 | `7CE59502F083299C` |
| `README.md` | 15,689 | `130AA7EFE6F580E8` |
| `SKILL.md` | 10,890 | `A9C3BDC1BC88C162` |
| `assets/brand/bell-black-128.png` | 3,141 | `D3ACB651D3D4CCA9` |
| `assets/brand/bell-black-48.png` | 1,195 | `AB92EF13AFD3B4D8` |
| `assets/brand/bell-black-512.png` | 13,751 | `7AFF6A9D46155FDD` |
| `assets/brand/bell-gray-128.png` | 3,245 | `1D91718681C058CC` |
| `assets/brand/bell-gray-48.png` | 1,193 | `35E3578A40AA99EB` |
| `assets/brand/bell-gray-512.png` | 14,108 | `4DC35F7EC76F19BD` |
| `assets/brand/bell-white-128.png` | 3,287 | `C6D372FEFFD2CBF6` |
| `assets/brand/bell-white-48.png` | 1,214 | `2193EBA41DB35AB8` |
| `assets/brand/bell-white-512.png` | 14,558 | `21FD90BBFCF326BE` |
| `assets/brand/bell.svg` | 1,580 | `18EC31976EDBB052` |
| `assets/brand/icon-shipgo.svg` | 831 | `75BAC4D7C7EFFB03` |
| `assets/team/avatar-ashu.png` | 404,750 | `6991E2730D8A5F7D` |
| `assets/team/avatar-azi.png` | 450,855 | `09E4C85FB34AF76D` |
| `assets/team/avatar-daa.png` | 480,997 | `42CE7798ACAC3EA4` |
| `assets/team/avatar-daniu.png` | 424,143 | `ACCBF839FFD63C20` |
| `assets/team/avatar-laodou.png` | 440,813 | `8DA0FAC1DC6D51D2` |
| `assets/team/avatar-laohuojie.png` | 15,237 | `CF9D0922955533F3` |
| `assets/team/avatar-laoqin.png` | 413,944 | `9486A71ACC0E5B3E` |
| `assets/team/avatar-neko.png` | 598,216 | `FFDC7C219F856D87` |
| `assets/team/avatar-pro.png` | 476,518 | `7C30CAFD71353AF9` |
| `assets/team/avatar-turbo.png` | 417,620 | `030A4D2034A3C1CE` |
| `assets/team/avatar-xiaoa.png` | 384,312 | `B32EEA394A523019` |
| `assets/team/avatar-xiaoniu.png` | 492,048 | `C6A8DF9A02E90879` |
| `assets/team/avatar-xiaoshen.png` | 411,902 | `65A3FF74C5207D06` |
| `assets/team/avatar-xiaoshu.png` | 14,594 | `C786FFC299F59D88` |
| `assets/team/avatar-zhuazong.png` | 15,701 | `742C9DD5482A190A` |
| `assets/team/名单.md` | 1,844 | `A01F61E5FBE56C0C` |
| `assets/截图/1-开篇引导.png` | 296,557 | `706C13841A8BFAFC` |
| `assets/截图/2-问卷站素材约定.png` | 287,591 | `B62CBC9CA2A8B28A` |
| `assets/截图/3-交付清单.png` | 318,530 | `076D7F02FD217CDF` |
| `assets/截图/4-交付报告与边界.png` | 379,572 | `48388519B0A28D37` |
| `assets/截图/5-流程图_中文.png` | 321,463 | `30FC79B56BB65A7C` |
| `assets/截图/6-流程图_英文.png` | 271,738 | `2791A17A81ADCC9F` |
| `config.json` | 283 | `55288CC0D0AD3E70` |
| `docs/收口检查单.md` | 6,701 | `89ED5F35B3CE9CC3` |
| `docs/英文验收单.md` | 3,895 | `A0EDE1A830AA8715` |
| `examples/demo-project/README.md` | 490 | `9B7A85F2A391C10D` |
| `examples/demo-project/pebblelog.py` | 1,260 | `06939416C3487294` |
| `examples/demo-project/test_pebblelog.py` | 654 | `772EAC74AC11BAD1` |
| `examples/端到端成品示例.md` | 6,376 | `DD2E244C5A01898B` |
| `icon.png` | 3,141 | `D3ACB651D3D4CCA9` |
| `index.html` | 1,872 | `4999FF6BF36DA041` |
| `llms.txt` | 4,636 | `5D70B35C679C6A5E` |
| `references/FAQ常见问题.md` | 8,357 | `C89E37119BE742BD` |
| `references/分册①_定名查重与素材清单.md` | 11,156 | `7AA27234DFD0847C` |
| `references/分册②_README规整与美化.md` | 16,485 | `2C596B004A1436CB` |
| `references/分册②附_美化模板.md` | 10,528 | `364BB8F6BBF7346B` |
| `references/分册③_收口检查与指纹.md` | 63,942 | `B832545592DD09C1` |
| `references/分册③附_判据追溯与历史判例.md` | 9,114 | `0B81CF0E81F45A83` |
| `references/分册④_三站式交互手册.md` | 19,528 | `5812E6AD95BD006C` |
| `scripts/checklist_check.py` | 14,934 | `A70556B184B78508` |
| `scripts/en_acceptance_check.py` | 19,099 | `1BD2BB2F441ECF22` |
| `scripts/fingerprints_scan.py` | 15,403 | `D454DA7B62FEF244` |
| `scripts/restyle_readme.py` | 40,350 | `BC5DC9AB70D265C9` |
| `scripts/text_quality_check.py` | 14,574 | `62932D3565BDE901` |
| `site.json` | 6,042 | `B4C30396A4C40B55` |
| `terms.json` | 733 | `A3543A2705C09527` |
| `使用说明.md` | 2,740 | `115199D916DF54BE` |
| `隐私与合规说明.md` | 975 | `AC38E8E7F247969E` |

# 实物件 69 件（FINGERPRINTS.md 自身不入表；含分发 zip 0 个，其 zip: 内件为虚拟行不计实物）

## 条件件 N/A 立牌

> 只有本专节内的精确件名参与清单豁免；本说明与其他章节的散文不生效。必选件不可在此豁免。

- **`启动<项目>.bat`**：N/A（本包为 Python 检查器与文档合集，无 Windows 启动器）。
- **`tests/`**：N/A（无独立产品测试目录；以四脚本 selftest＋四工具联检＋负测回归补位）。
- **`packages/<渠道>-<name>/`**：N/A（本包按 skill／仓库克隆方式交付，无渠道插件包）。
- **分发 zip**：N/A（skill／仓库克隆类交付，按分册③第 12 项结构化 N/A；若改作应用类分发则必须补 zip）。
- **`assets/流程图/`**：N/A（流程图 PNG 已随 `assets/截图/` 留档，无独立流程图目录）。
- **流程图 SVG 源**：N/A（现有流程图为历史 PNG 实测留档，无可核验 SVG 源；按分册②保留 PNG，不伪造源文件）。

## 挂起项登记位

- 无（本轮无挂起；后续如有，逐件写明事项／原因／下一步／责任人）。

## 素材与署名立牌

- **`icon.png`**：取自标准素材库 `brand/bell-black-128.png`（sha16 `D3ACB651D3D4CCA9`），标题区按 `width=96` 显示；三色×三规格＋`bell.svg` 随 `assets/brand/` 全带（10 件）。
- **头像墙**：`assets/team/` 15 张头像＋`名单.md`（16 件）。标准素材库原件与已安装 skill 副本两份素材库逐字节同源；包内 **brand 10＋team 16＝26 件，26/26 与原件逐字节全一致**（收口单 10a）。
- **名册文案**：逐字照抄家里网站 `site.json` / `family.html`（15 人＋好友席 6 位），按 #19 照抄判据；**英文家人墙按分册② §1 第 6 条口径意译**（人名拼音／岗位意译／同一套头像），好友席同口径转拼音。
- **家里网站链接**：README 结尾一行 `https://c2fnbmhd.qwenwork.host/`（「老秦家的本地小工具」），仅文档指路；本包脚本不联网、不产生请求（`llms.txt` 已同步口径）。
- **收尾署名**：「老秦 Family」（OldQin Family）作品，按版式七段第 7 段。

> 本表由探针出表生成，非手拼；FINGERPRINTS.md 自身不入表。
