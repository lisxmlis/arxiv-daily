# arXiv Daily

自动获取 [arXiv](https://arxiv.org) 当天（或近几日）最新论文，并按主题分类与关键词筛选。

**云端固定地址（部署后）：** `https://<你的应用名>.streamlit.app`

## 功能

- 按学科主题（cs.LG、cs.AI、quant-ph 等）拉取新论文
- 支持自定义分类代码
- 关键词筛选（命中任一 / 全部命中）
- 可调目标日期与回溯天数
- 导出 Markdown / CSV / JSON

## 云端部署（固定链接，推荐）

使用 [Streamlit Community Cloud](https://share.streamlit.io/) 免费托管，电脑关机也能访问。

1. 把本仓库推送到 GitHub
2. 打开 https://share.streamlit.io/ → 用 GitHub 登录
3. **New app** → 选择本仓库
4. Main file path 填：`app.py`
5. Deploy 后得到固定链接：`https://xxxx.streamlit.app`

之后每次推送 `main` 分支，云端会自动更新。

## 本机运行

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Windows 也可双击 `run.bat`（仅本机）。临时公网隧道见 `run_remote.bat`（链接不固定，不如云端部署）。

## 使用说明

1. 左侧选择主题分类（或填写自定义代码，如 `cs.CV`）
2. 可选填关键词，逗号分隔，例如：`transformer, attention, LLM`
3. 选择目标日期；结果少时可增大「回溯天数」
4. 点击「获取论文」

## 数据源

| 模式 | 说明 |
|------|------|
| 自动 | 优先 RSS，结果少时用官方 API 补充 |
| 仅 RSS | 更快 |
| 仅 API | 更全，稍慢 |

> arXiv 按美国东部时间发布；工作日傍晚左右更新新帖。
