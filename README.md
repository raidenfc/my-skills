# my-skills

个人 Agent skills 源码仓库。

## 目录结构

- 仓库根目录下放各个 skill（每个 skill 目录必须包含 `SKILL.md`）
- `scripts/sync-to-agents.sh`：将本地 skills 同步到 `~/.agents/skills`
- `INDEX.md`：已管理 skills 的索引清单

## 工作流

1. 在本仓库根目录创建或更新你的 skills。
2. 提交并推送到 GitHub。
3. 运行同步脚本，将 skills 安装/更新到 `~/.agents/skills`。

## 快速开始

```bash
cd /Users/mac/Documents/code/my-skills
git init
git branch -M main
git add .
git commit -m "chore: initialize my-skills repo"
```

```bash
bash scripts/sync-to-agents.sh
```
