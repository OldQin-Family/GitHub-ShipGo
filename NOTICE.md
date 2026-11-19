# NOTICE · GitHub-ShipGo

> 本件按「借鉴的／原创实现／LICENSE」三块结构写。版本：3.0.4。

## 一、借鉴的

- **公开技术事实**：Markdown 表格与文档结构、SHA-256 校验和、zip/CRC 校验、Python 标准库 argparse／hashlib／zipfile 的用法——均为公开技术事实，不构成版权客体。
- **参考项目**：开发期阅读过公开的 skill / README 编写与上架资料（资料清单见 [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md)）。**只借思路与流程结构，未包含其任何代码、图片或文案**。
- **可选依赖**：**无第三方运行时依赖**。五支脚本只使用 Python 标准库；`scripts/restyle_readme.py` 从同包 `scripts/en_acceptance_check.py` 引入豁免表，属本包自有代码。因此不存在需要捆绑的可选依赖，其许可义务不触发。

## 二、原创实现

- 三站式发布流程（问卷 → 自动段 → 核对交付）与四张交互模板；
- 发布构成清单、口径三律、收口 15 项检查单、全包指纹账的判据体系；
- `scripts/` 下五支脚本：清单核查、英文验收、README 版式整形、指纹扫描与对表、文字质量检查；
- 四脚本 selftest＋四工具联检，以及指纹探针与手册嵌码的双源同步校验（改一边忘另一边会判红）；
- 安全设计原则：脚本不联网、不读取凭据、不在交付目录原地写盘；预检与验证要求在副本运行，运行期残留不入包。

## 三、LICENSE

本包采用 **MIT**，见 [LICENSE](LICENSE)。

- **本侧义务**：保留版权声明与许可全文；
- **反向义务**：下游再分发时同样保留本 LICENSE 与 NOTICE 中的署名信息；
- 不随包捆绑任何第三方代码，故无第三方许可需要随附。

---

英文版见 [NOTICE.en.md](NOTICE.en.md)。
