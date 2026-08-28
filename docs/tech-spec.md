# 技术规范 — 每日寓言

> 版本：v1.0　创建：2026-08-28

## 1. 总体架构

采用「静态生成 + 静态托管」架构：定时任务每天生成一篇文章存入仓库，手机网页直接读取展示。无服务器、无数据库，成本最低、最稳定。

```
┌────────────────┐  每天定时   ┌─────────────────┐
│ GitHub Actions │ ─────────> │ DeepSeek API     │
│ （定时任务）    │  调用生成   │ （AI 写文章）     │
└───────┬────────┘            └─────────────────┘
        │ 文章写入仓库
        ▼
┌────────────────┐  手机访问   ┌─────────────────┐
│ content/ 目录   │ ─────────> │ app/ 静态网页    │
│ （文章数据）    │  读取渲染   │ （PWA 页面）     │
└────────────────┘            └─────────────────┘
```

## 2. 技术栈

| 部分 | 技术 | 说明 |
|------|------|------|
| 展示端 | HTML + CSS + JavaScript | 纯静态单页，无框架，零依赖 |
| 内容生成 | Python 脚本 + GitHub Actions | 定时任务调用 DeepSeek API |
| 数据存储 | Markdown + JSON 文件 | 存于仓库 content/ 目录 |
| 托管 | 静态托管（阶段 3 选定） | 候选：Cloudflare Pages / GitHub Pages / Vercel |

## 3. 目录结构

```
d:\知识软件\
├─ CLAUDE.md                # 项目指引
├─ docs\                    # 标准文档
├─ devlog\                  # 开发日志
├─ index.html               # 手机网页单页应用（阶段 1，部署根目录）
├─ sw.js                    # Service Worker：离线缓存（阶段 3）
├─ manifest.webmanifest     # PWA 配置（阶段 3）
├─ icon-*.png               # PWA 图标（阶段 3）
├─ content\                 # 文章数据（阶段 2）
│  ├─ index.json            # 全部文章索引
│  └─ YYYY-MM-DD.md         # 每日文章
├─ scripts\                 # 生成脚本（阶段 2）
│  ├─ generate.py           # 调用 DeepSeek 生成当日文章
│  └─ make_icon.py          # 一次性图标生成脚本（阶段 3）
└─ .github\workflows\       # 定时任务（阶段 2）
   └─ daily.yml
```

> 说明：网页文件放在仓库根目录（而非 app/ 子目录），是因为 GitHub Pages 从根目录发布，这样页面才能直接读取同级的 content/ 文章数据。

## 4. 数据格式

### 4.1 文章文件 `content/YYYY-MM-DD.md`

```markdown
---
date: 2026-08-28
field: 物理学
concept: 熵
---
（正文：故事 / 概念揭示 / 概念解释 / 隐喻对应）
```

### 4.2 索引文件 `content/index.json`

```json
[
  { "date": "2026-08-28", "field": "物理学", "concept": "熵", "title": "故事标题" }
]
```
按日期倒序排列。网页加载此文件渲染历史列表。

## 5. DeepSeek 接入（阶段 2 执行）

### 5.1 注册与密钥（用户操作，一次性，约 10 分钟）
1. 打开 https://platform.deepseek.com 注册账号（支持微信/支付宝充值）
2. 在「API Keys」页面创建密钥（形如 `sk-xxxxxxxx`）
3. 充值 10 元即可覆盖数年的每日一篇成本

### 5.2 调用方式
- 接口兼容 OpenAI 格式：`POST https://api.deepseek.com/chat/completions`
- 推荐模型：`deepseek-chat`
- 密钥通过 GitHub Secrets 传入（变量名 `DEEPSEEK_API_KEY`），永不写入代码或仓库

### 5.3 生成脚本逻辑（scripts/generate.py）
1. 确定日期：默认今天，可用命令行参数指定（`python scripts/generate.py YYYY-MM-DD`，用于补跑某天）
2. 从领域池随机选一个领域（避免与近 7 天重复）
3. 组装提示词 = 原始提示词 + 今日领域
4. 调用 API 获取文章
5. 校验内容完整性（四段式齐全）→ 写入 content/YYYY-MM-DD.md
6. 更新 content/index.json
7. git commit + push

## 6. GitHub 准备（阶段 2 执行）

### 6.1 注册账号（用户操作，一次性，约 5 分钟）
1. 打开 https://github.com/signup 注册：邮箱 → 密码 → 用户名 → 邮箱验证码
2. 记好用户名（推送代码时要用）

### 6.2 创建仓库
1. 登录后点右上角头像 → Your repositories → New repository
2. Repository name 填 `daily-fable`，选 Public，其余保持默认，不要勾选 README
3. 创建完成后由 Claude 在本地执行 git push 完成关联

### 6.3 配置密钥
1. 进入仓库 → Settings → Secrets and variables → Actions → New repository secret
2. Name 填 `DEEPSEEK_API_KEY`，Secret 粘贴 DeepSeek 平台的 API 密钥（sk- 开头）
3. 密钥只存在 GitHub 加密配置中，不会出现在代码和运行日志里

## 7. GitHub Actions 定时任务（阶段 2 执行）

- 触发：`schedule` 每天 00:30（北京时间）自动运行；另支持手动触发兜底
- 密钥：`DEEPSEEK_API_KEY` 存仓库 Secrets，不进入代码
- 容错：生成失败时重试；失败不影响已部署的历史内容，次日任务继续运行

## 8. 安全要点

1. API 密钥只存 GitHub Secrets，不出现在任何前端代码中
2. 前端只读公开内容，无任何写入接口
3. 仓库可公开（文章内容本身就是要公开阅读的）

## 9. 成本估算

| 项目 | 成本 |
|------|------|
| DeepSeek 文章生成 | 约 0.005–0.05 元/天（每月 1 元以内） |
| GitHub Actions | 免费额度内（每天一次，远低于限额） |
| 静态托管 | 免费方案 |
