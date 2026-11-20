# 86 五笔打字练习

基于 Vue 2 的本地网页练习工具，支持导入文本、显示当前字符的五笔编码提示，以及统计输入速度和正确率。

## 本地运行

需要 Node.js 和 npm。克隆项目后执行：

```bash
npm ci
npm run serve
```

打开终端显示的本地地址。可通过“选择文本文件”导入 `.txt`、`.md` 或 `.text` 文件，点击练习区域后使用输入法打字。

## 生产构建

```bash
npm run build
```

静态构建结果位于 `dist/`，依赖与构建产物不提交到仓库。

## 主要文件

- `src/components/TypingTrainer.vue`：练习界面与输入逻辑。
- `public/wubi86.json`：页面加载的五笔码表。
- `wubi/better-wubi.dict`：原始词典。
- `wubi/better_wubi_to_json.py`：词典转换脚本，在 `wubi/` 目录运行后生成 JSON 文件。

当前为个人练习版本，编码提示与统计结果供练习参考。
