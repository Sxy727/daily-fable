# CLAUDE.md — 每日寓言项目指引

## 项目简介

「每日寓言」是一款运行在手机上的知识软件（PWA 手机网页）：每天由 AI（DeepSeek）生成一篇寓言式文章，围绕一个研究生水平的概念——先讲故事，故事快结束时才揭示概念，最后解释概念与隐喻。目标用户是不懂代码的用户，页面简约精致，显示当天日期，支持回看历史文章。

## 标准文档路径

每次开发前，先阅读以下文档了解项目全貌：

| 文档 | 路径 | 内容 |
|------|------|------|
| 开发需求 | [docs/requirements.md](docs/requirements.md) | 用户需求、功能清单、非功能需求、约束条件 |
| 技术规范 | [docs/tech-spec.md](docs/tech-spec.md) | 总体架构、技术栈、目录结构、数据格式、API 流程 |
| 设计规范 | [docs/design-spec.md](docs/design-spec.md) | 设计理念、配色、字体、排版、页面结构 |
| 执行步骤 | [docs/execution-steps.md](docs/execution-steps.md) | 分阶段任务清单、完成标准、进度状态 |

## 工作原则

1. **小步推进**：一次只完成一个模块（一个文件或一个功能），确认无误后再推进下一步
2. **先文档后代码**：开发时对照标准文档执行；需求变化先更新文档再改代码
3. **每个阶段完成后**：
   - 更新 [docs/execution-steps.md](docs/execution-steps.md) 中对应任务的状态
   - 在 [devlog/](devlog/) 目录下创建/更新当日日志
4. **不要过度设计**：满足需求即可，不增加额外功能
5. **非技术用户视角**：代码注释用中文，交付说明用通俗语言，每个阶段结束给用户验收

## 开发日志（每天自动记录）

每次开发会话结束时，在 `devlog/YYYY-MM-DD.md` 中创建/更新当日日志（格式见 [devlog/README.md](devlog/README.md)）：

```markdown
# 开发日志 — YYYY-MM-DD

## 已完成
- 事项 1
- 事项 2

## 待办
- 事项 A
- 事项 B

## 遇到的问题
- 问题描述及解决方案

## 下次计划
- 下一步要做什么
```

## 当前进度

参考 [docs/execution-steps.md](docs/execution-steps.md) 中各阶段状态标记。

## 技术栈速查

- 展示端：HTML / CSS / JavaScript（纯静态，无框架）
- 内容端：GitHub Actions 定时任务 + DeepSeek API
- 部署：静态托管（阶段 3 确定）
