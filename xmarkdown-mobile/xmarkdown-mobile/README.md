# X-markdown 手机端（GitHub Pages PWA）

基于桌面端 X-markdown 的核心功能，构建的**手机端 PWA**，通过 **GitHub Pages 一键部署**。

## 功能

- **每日精选**：浏览桌面端聚合的每日 AI 精选列表，支持领域 / 语言 / 分类筛选
- **Markdown 阅读**：5 种阅读主题（极简白 / 科技蓝 / 杂志灰 / 经典红 / 墨绿），支持原文 / 译文切换与编辑
- **知识库**：浏览、搜索、阅读收藏的文章（含译文标注）
- **自动 / 手动刷新**：下拉刷新 + 定时自动探测 + 手动刷新按钮，桌面端内容更替后手机端同步更新
- **PWA 离线**：Service Worker 缓存，安装到手机主屏幕

## 架构

```
桌面端 X-markdown (Electron + React + Python 后端)
        │
        │  tools/export_site.py  (读取 SQLite → 导出 JSON/MD)
        ▼
xmarkdown-mobile/public/data/  (index.json, kb.json, articles/*.json)
        │
        │  npm run build
        ▼
dist/  ──► GitHub Actions ──► GitHub Pages
```

因为 **GitHub Pages 只能托管静态文件**，手机端无法直接调用桌面端的 Python 后端，因此采用
「导出静态数据 + 静态 PWA」方案。桌面端新增「同步手机端」按钮，一键完成导出、构建、部署。

## 一键部署（桌面端）

1. 在 GitHub 创建仓库，安装并登录 [gh CLI](https://cli.github.com/)，或配置好 git 凭据。
2. 在项目根目录运行：
   ```
   node scripts/sync.mjs --repo 你的用户名/仓库名 --push
   ```
   或双击 `sync-to-mobile.bat`。
3. 脚本会：
   - 导出桌面端数据到 `public/data/`
   - 提交并推送到 `main` 分支
   - 触发 `.github/workflows/deploy.yml` → GitHub Actions 自动构建并部署到 Pages
4. 等待 1-3 分钟，访问 `https://<用户名>.github.io/<仓库名>/`。

> 提示：首次部署若未自动开启 Actions，需在仓库 Settings → Pages 中选择
> "GitHub Actions" 作为部署来源。

## 本地开发手机端

```bash
cd xmarkdown-mobile
npm install
npm run dev          # 本地开发（http://localhost:5173）
npm run build        # 构建到 dist/
```

数据导出：

```bash
python tools/export_site.py   # 从 backend/data/xmarkdown.db 导出数据到 public/data/
```

## 手动刷新逻辑

- **下拉刷新**：在列表页下拉即可重新拉取最新数据
- **自动刷新**：每 60 秒探测一次数据是否更新；应用回到前台立即探测
- **手动刷新**：右上角「刷新」按钮

数据是否更新由 `index.json` 的 `generatedAt` 时间戳判断，桌面端同步后该时间戳变化，手机端自动感知。
