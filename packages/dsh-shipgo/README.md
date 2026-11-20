# dsh-shipgo

ShipGo 的 DSH 插件壳：在「设置 → 插件」里提供一个发版检查单面板。插件可选，不影响 GitHub-ShipGo 本体。

## 它做什么

- 按 ShipGo 的三站式流程列出发布前闸门：环境预检、发布约定、自动段、站二核对、封包、站三交付。
- 勾选进度保存在**当前浏览器**的 localStorage，不上传、不写盘。
- 面板里有预检命令的复制按钮，以及仓库、SKILL.md、参考文档的链接。

## 它不做什么

- 不执行任何脚本，不读取本地文件。
- 不代开仓、不代上传、不代发版；发布决定仍由使用者做出。
- 不替代 ShipGo 本体：三站式问答、文书生成、指纹账仍在 GitHub-ShipGo skill 里。

## 入口

- 路由：`/dsh-shipgo`
- 健康检查：`/dsh-shipgo/health`
- 设置页 tab：ShipGo

## 包结构

```
packages/dsh-shipgo/
├── package.json          # dsh.bundle 指向 cordis.patch.yml
├── cordis.patch.yml      # 插入 shipgo 插件
├── lib/index.mjs         # webServer 路由
├── lib/client.js         # 设置页 tab
└── README.md
```

## 安装

由 DSH 插件市场或 `dsh plugin add` 从本仓库子包安装。插件本身没有 npm 依赖，也不需要构建。

## 许可

MIT，沿用仓库根 LICENSE。
