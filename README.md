# 个人主页

这是一个可直接部署到 GitHub Pages 的静态个人主页模板，包含头像、姓名、邮箱、联系电话、个人经历、研究方向和项目成果等内容，并通过 Google Translate 支持多语言自动翻译。

## 修改个人信息

打开 `index.html`，修改中文内容即可。页面以简体中文为唯一维护源，访客可以通过右上角的语言选择器自动翻译为繁体中文、English、日本語、한국어、Français、Deutsch、Español、Русский、العربية、Português 和 Italiano 等常用语言。

建议重点修改下面这些内容：

- `你的姓名`
- `你的学校 / 学院`
- `your.email@example.com`
- `+86 138 0000 0000`
- `中国 · 你的城市`
- 教育经历、科研经历、项目成果、研究方向

如果要换成真实头像，把图片放到 `assets` 文件夹中，例如 `assets/avatar.jpg`，然后把 `index.html` 中的 `assets/avatar.svg` 改成你的图片路径。

## 自动翻译说明

页面使用 Google Translate 网页组件实现自动翻译，不需要在代码中填写 API Key。后续你只需要维护中文正文，其他语言会根据当前页面内容自动生成。

语言选择器默认显示 `中文简体`，每个语言选项使用对应语言自己的文字显示。

如果访问者所在网络无法加载 Google Translate，页面仍会正常显示中文原文。

## 论文雷达

主页包含一个“论文雷达”模块，会读取 `data/papers.json` 并展示 Google Scholar 近 3 年同时满足成对关键词关系的 Transactions 期刊论文。论文资源库来源为 Google Scholar。

关键词含义：

- `ISAC`：Integrated Sensing and Communication，通感一体化。
- `UAV`：Unmanned Aerial Vehicle，无人机。
- `MA`：Movable Antenna，可移动天线。

检索关系为“且”的关系，而不是“或”的关系：

- `UAV AND ISAC`
- `MA AND ISAC`
- `MA AND UAV`

自动更新逻辑位于：

- `.github/workflows/update-papers.yml`：每天北京时间约 04:00 自动运行，也可以在 GitHub Actions 手动运行。
- `scripts/fetch_papers.py`：从 Google Scholar 获取论文数据；自动任务通过 SerpApi Google Scholar API 作为访问方式。
- `scripts/paper_config.json`：配置概念关键词、成对检索关系、Transactions 期刊白名单和 SCI/JCR Q1-Q3 标注。

由于 SCI/JCR 分区完整数据通常不是开放 API，本项目采用本地白名单控制“三区及以上”条件，即 `Q1`、`Q2`、`Q3`。后续如果要增加或删除 Transactions 期刊，修改 `scripts/paper_config.json` 即可。

Google Scholar 自动抓取需要在 GitHub 仓库中配置 `SERPAPI_KEY`。这里的 SerpApi 只是访问 Google Scholar 的接口服务，论文资源库仍然来源于 Google Scholar：

1. 注册并获取 SerpApi API Key。
2. 打开 GitHub 仓库 `Settings` -> `Secrets and variables` -> `Actions`。
3. 新建仓库密钥 `SERPAPI_KEY`，值填写你的 SerpApi API Key。
4. 打开 `Actions`，手动运行一次 `Update paper radar`。

推送脚本、配置或工作流文件后，`Update paper radar` 也会自动运行一次，方便立即测试。

如果 GitHub Actions 无法自动提交更新，请在仓库中打开 `Settings` -> `Actions` -> `General`，把 `Workflow permissions` 改为 `Read and write permissions`。

## 发布到 GitHub Pages

方式一：发布为个人主页，访问地址通常是：

`https://你的GitHub用户名.github.io`

1. 在 GitHub 新建仓库，仓库名必须是 `你的GitHub用户名.github.io`。
2. 把本文件夹中的所有文件上传到该仓库。
3. 进入仓库的 `Settings` -> `Pages`。
4. 在 `Build and deployment` 中选择 `Deploy from a branch`。
5. 分支选择 `main`，目录选择 `/root`，保存。

方式二：发布为普通项目主页，访问地址通常是：

`https://你的GitHub用户名.github.io/仓库名/`

1. 在 GitHub 新建任意仓库，例如 `personal-homepage`。
2. 上传本文件夹中的所有文件。
3. 进入仓库的 `Settings` -> `Pages`。
4. 分支选择 `main`，目录选择 `/root`，保存。

## 使用命令上传

如果你已经安装并登录 Git，可以在 `personal-homepage` 文件夹中运行：

```powershell
git init
git add .
git commit -m "Create personal homepage"
git branch -M main
git remote add origin https://github.com/你的GitHub用户名/你的仓库名.git
git push -u origin main
```

上传后，在 GitHub 仓库的 `Settings` -> `Pages` 开启 GitHub Pages 即可。
