// DSH 前端半边：在「设置 → 插件」里加一个 ShipGo 检查单 tab。
// id 必须逐字等于 npm 包名，否则 DSH 报 "loaded without registering"。

window.__ModuleLoader__.load({
  id: "dsh-shipgo",
  factory: require => {
    var module = { exports: {} };
    var exports = module.exports;
    let react = require("react");

    const Panel = () => {
      const h = react.createElement;
      return h("iframe", {
        src: "/dsh-shipgo",
        style: { width: "100%", height: "75vh", border: "0" },
        title: "ShipGo",
      });
    };

    const apply = ctx => {
      const slots = ctx.get("slots");
      if (!slots) return;
      slots.inject("settings.plugins.tab", () =>
        slots.register(
          {
            name: "settings.plugins.tab",
            key: "shipgo",
            id: "shipgo",
            order: 1004,
          },
          Panel
        )
      );
    };

    exports.apply = apply;
    return exports;
  },
});
