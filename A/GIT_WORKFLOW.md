# 三人私有仓库合作方法

2026-10-23建立。仓库根目录为 `D:\mathorcup`，A题是唯一执行题目。远端创建/分支保护的真实状态见文末，不把建议配置当成已启用。

## 1. 使用最简单的分支流程

`main`保存队友可使用的版本。一项任务从最新main开短期分支，做完推送并发Pull Request（PR），由另一队员看改动与证据，合并后下一任务重新开分支。不设置长期develop、每人永久分支或三份论文主稿。

| 角色 | 分支示例 | 主要负责 | 另一人复核 |
|---|---|---|---|
| 甲：题意/文献/论文 | `docs/sensory-map` | 数据语义、证据表、论文分节 | 乙查方法/数字，丙查工件 |
| 乙：Python/建模 | `feat/q1-ridge`、`fix/group-split` | 数据处理、Q1/Q2、切分 | 丙复跑，甲解释核对 |
| 丙：工程/agent/复现 | `chore/reproduce`、`feat/q3-generator` | 环境、流水线、Q3实现、日志 | 乙复跑，甲审结论 |
| agent独立任务 | `codex/<task>` | 仅分配范围，报告证据和限制 | 对应人类责任人及另一队员 |

每人每天集中同步一次，声明今天改哪些文件。共同的映射表/切分/方法论由指定一人合并，不同时编辑。二进制Word只由甲整合；其他人改Markdown分节或提交意见。详细所有权见 [roles/CONTRACTS.md](roles/CONTRACTS.md)。

## 2. 每台机器首次加入

仓库所有者先在GitHub确认Private，再邀请另外两人的真实GitHub账号为协作者；不要分享账号、token或SSH私钥。账号尚未提供时不创建虚假的CODEOWNERS规则。每名队员使用自己的身份和登录。

以下为PowerShell示例；仓库地址已填真实值，用户名、邮箱和任务名需换成自己的。不要嵌入token。已有本地仓库的人无需再次clone。

```powershell
git clone https://github.com/Ferrystd/mathorcup.git mathorcup
Set-Location mathorcup
git config --local user.name "自己的姓名或GitHub名"
git config --local user.email "自己的GitHub邮箱或noreply邮箱"
git config --local pull.ff only
git config --local fetch.prune true
git config --local push.default simple
```

初始化机器沿用已配置的Git作者身份；没有修改全局身份。上面三项协作配置在初始化机器已设置，但`.git/config`不随clone传播，所以队友需各自执行。本机Git直连GitHub失败，已用现有本地代理完成推送，并在本仓库设置`http.https://github.com/.proxy=http://127.0.0.1:7897`；它依赖本机代理继续运行，其他机器不要照抄。团队仓库没有开源授权声明；上游研究快照保留各自MIT许可，官方材料保留来源，不擅自将整库标成MIT。

## 3. 每个任务的日常命令

以下从仓库根执行，示例任务名需换成自己的。执行切换前确认工作区干净；有未提交改动就先完成本任务提交，或改用新worktree，不自动stash队友改动。

```powershell
git status --short
git switch main
git pull --ff-only
git switch -c feat/q1-ridge
```

修改后：

```powershell
git diff --stat
git diff
git add -- A/src/q1 A/configs/q1.yaml
git diff --cached
git diff --cached --check
git commit -m "feat(q1): add grouped ridge baseline"
git push -u origin feat/q1-ridge
```

`A/src/q1`和配置文件是未来实现示例，目前不存在；只替换为本次真实改动的路径。不要盲用`git add .`，也不要用`git add -f`绕过忽略规则。首次push后，GitHub网页或已配置的`gh pr create --base main --head <任务分支>`创建PR，按仓库模板填写实际验证。调用工具创建PR后应附到相应Codex聊天。

PR保持一件事：一个基线/一个错误修复/一个论文节。草稿PR可以提前同步，但不能将未运行模型写成已验证。代码改动附真实运行和指标；仅文档修改只需内容与链接核查，当前没有已实现的测试套件或CI，不虚构绿色测试。

## 4. 审查、合并与冲突

至少另一名队员看diff及证据；模型实现者不能是唯一验收人。默认协调者丙负责点击合并；如果PR由丙编写，则由甲或乙审查后合并。GitHub已限定Squash merge，一项任务变为main上一条清晰提交；只有本次初始化引导阶段直接建立main，后续工作走PR。

需要同步main时，在自己的任务分支、干净工作区执行：

```powershell
git fetch origin
git merge origin/main
```

冲突出现后停止新增功能；与冲突文件负责人确认最终内容，保留有意改动，去掉冲突标记，验证后只暂存解决的文件并commit。不要整体选ours/theirs覆盖别人的工作，不对共享分支rebase或force push。若决定放弃这次合并，可在确认没有其他进程写入后用`git merge --abort`返回合并前状态；先看status，不能代替备份。

合并后队友回main并`git pull --ff-only`。已推送并被别人使用的错误用新修复提交或`git revert <完整提交SHA>`，不用改历史。`pull --ff-only`提示分叉时停下检查`git log --oneline --graph --all -15`，由协调者确定保留方案，不改成强制覆盖。分支删除是单独清理动作，只在确认PR合并、没有唯一提交/未提交改动后按团队约定处理。

## 5. 同一电脑多个agent

不同电脑各自clone即可。同一目录多agent会共享文件、index和当前分支；即使口头说“各做各的”，切分支也会影响其他agent。独立任务可用独立worktree，依赖任务按上游提交完成后顺序开始。

示例（尚未为未来任务执行）：

```powershell
git fetch origin
git worktree add .worktrees/q2 -b codex/q2-graph origin/main
git worktree list
```

`.worktrees/`已忽略，每个任务拥有一个分支和目录。派发时传入该worktree的绝对路径、可写文件、基线SHA和复核人。主工作区不要在子agent运行中stash/merge。worktree不共享未跟踪的正式数据，每个worktree需配置各自数据位置和哈希；不要复制数据入Git。尚未开始需要并行写入的研究任务，所以本轮没有预建空任务分支或worktree。

## 6. 什么进入Git，什么另存

| 纳入Git | 留本地或队内受控共享存储 |
|---|---|
| 代码、依赖锁文件、配置、切分ID（许可允许）、规范、论文源 | `A/data/raw/`官方附件和`A/data/processed/`大数据 |
| `A/data/manifest.csv`等来源/哈希/取得步骤，审计摘要 | `A/runs/`完整运行、模型权重、输出大表 |
| `A/results/`内经复核的小型指标表、图表源数据和论文必要图片 | `A/models/`、`A/outputs/`、论文build/exports、最终提交包 |
| `A/logs/ai/`内脱敏使用记录、决定与关键交互摘要 | `A/logs/ai/raw/`原始对话、`A/logs/private/`个人信息 |
| 官方题面/空模板、来源许可证和研究快照 | 已签名承诺书、账号/凭据、`.env`、虚拟环境、缓存 |

原始数据忽略不等于可以丢失。由乙管理数据原件，丙维护另一份队内备份；通过受控共享盘交接，Git登记可取得位置（无密码链接）、SHA-256、权限、版本与负责人。完整实验工件同样由运行者保存并共享；克隆者按manifest补齐后才能复现。未选定共享位置时明确待配置，不写“已备份”。

小型结果建议单文件≤1MiB，图可按可读性例外；这只是管理约定，当前没有自动大小门禁。不全局忽略所有CSV/JSON/PNG/PDF，因为配置、切分和官方材料需要跟踪。`.gitignore`只影响未跟踪文件，不能消除已提交秘密；误提交时先停止推送，若已泄露则轮换凭据并由协调者处理历史。私有仓库不是秘密保险箱。

每次实验先提交代码与配置，记录**完整commit SHA**、dirty状态、数据/配置/切分哈希、环境和run_id。若临时dirty运行，保存diff/未跟踪实现的快照并标探索；正式验收必须能回到完整干净提交复跑。Squash会改变main上的SHA，保留实际运行SHA，在合并后复跑关键结果并记录新SHA；不要只记录可能过期的分支名。

## 7. 远端与main保护

仓库创建时必须显式选Private，推送前核对`gh repo view --json nameWithOwner,isPrivate,url`。新增队员必须知道真实账号和访问范围；本轮尚未邀请未知账号。

推荐main规则：要求PR、至少1名非作者批准、新提交后重审、解决讨论、禁止强推和删除。只在已有可运行检查后才要求对应status check；当前没有CI，不设置不存在的检查。保护在私有仓库上依GitHub套餐而定，不能假设Free一定支持；若不支持，保留私有性并按上述流程人工执行，不为了保护规则改成公开或擅自升级付费套餐。

2026-10-23已核验状态：

- 私有远端：[Ferrystd/mathorcup](https://github.com/Ferrystd/mathorcup)，`isPrivate=true`；origin已连接，main初始提交已实际推送并建立追踪。
- main保护API已成功设置：1人批准、新提交撤销旧批准、解决讨论、禁止强推/删除；未要求不存在的CI检查。
- 合并仅允许Squash；自动删分支关闭，避免未检查就删除。
- 管理员暂保留GitHub默认绕过权限（`enforce_admins=false`）；这不代表允许日常绕过团队PR约定。当前所有者可完成初始化收尾；邀请队友后由另一人审查，不把技术可绕过视为自审通过。
- 尚未邀请队友：需要两人的真实GitHub账号。没有创建虚假CODEOWNERS或已完成邀请的声明。

## 8. 赛前冻结

10月30日16:00内部冻结前，把最终代码、论文源、配置、脱敏AI说明和小型结果合入main，另一队员按对应提交干净复跑。确认后可给该提交建立带说明的`submission-20261030`标签，记录正式上传文件的SHA-256、对应commit及回执位置。标签现在不创建，因为实验、论文和实际提交尚未完成；标签也不代表比赛平台已提交。

## 依据

已于2026-10-23实际阅读 [GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow)、[protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)、[gitignore](https://git-scm.com/docs/gitignore)。本文件对三人分工、文件大小、数据交接和实验SHA的规定是项目约定，不是GitHub官方强制规则。
