# 长期记忆与关系档案

## 目标

在用户首次明确同意后，跨任务复用精简的用户、对象和关系信息。记忆服务于减少重复解释，不是完整聊天仓库，也不是对人格的永久判决。

## 首次同意

先运行：

```bash
python3 scripts/memory_store.py status
```

尚未启用时，用一句话询问：

> 是否允许狗头军师在本机保存精简关系档案？同意后会自动更新，每次提示变更，可随时查看、暂停、撤销或删除。

只有用户明确同意后才能运行：

```bash
python3 scripts/memory_store.py enable --confirm
```

拒绝后本次任务不再追问。宿主无文件权限、脚本不可用或命令失败时，只沿用当前任务上下文并说明没有持久化。

## 五类记忆

| scope | 内容 | 合格来源 |
| --- | --- | --- |
| `user` | 用户的 MBTI、主观综合评分、稳定目标、偏好、边界和沟通习惯 | 用户明确陈述 |
| `object` | 对象姓名或称呼、MBTI、用户主观评分及用户明确提供的稳定事实 | 用户明确陈述或转述 |
| `relationship` | 当前阶段、双方共识、现实约束和下一步目标 | 用户明确陈述或转述 |
| `event` | 带时间的关键转折、兑现、邀约、冲突与修复 | 用户叙述；ChatLab或工具只能到此层 |
| `hypothesis` | 性格、依恋、意图等可被纠正的暂定解释 | 用户观察或模型推断，必须带置信度和证据 |

用户提供的姓名、昵称或代号都可直接保存为 `display_label`，召回和回复优先沿用。为控制记忆体积，整份聊天、截图和导出文件继续留在原文件或ChatLab；长期记忆只保存字段和不超过200字的关键事件摘要。

MBTI和主观评分在首次建档时主动询问；用户说不知道即可留空。MBTI按用户明确提供或对对象的转述保存；主观评分保存为0–100并注明是用户评价。只按用户给出的评分定义解释；没有定义时称为“主观综合评分”，不得改称意愿、心动、条件或投入分数。评分变化时更新同一字段，不累积每次分数；MBTI被用户纠正时覆盖旧值。

## 自动更新

同意后，每轮先判断是否出现会影响未来建议的高价值变化。没有变化就不写。把当前状态写成 `user`、`object` 或 `relationship` 的字段更新；把一次性转折写成 `event`；把读心或人格解释写成 `hypothesis`。同一对象、同一日期、同一事件字段视为同一事件的后续更新；字段使用稳定类型，如 `planned_activity`、`conflict`、`repair`，不要为同一件事另造字段。

示例：

```bash
python3 scripts/memory_store.py apply --json '{"scope":"relationship","subject_id":"obj-a","field":"stage","value":"双方已确认进入排他约会","source_type":"user_report","source_ref":"turn:当前任务","occurred_at":"2026-08-02","confidence":"high"}'
```

首次同意后，可把已经明确给出的建档信息分字段写入：用户使用 `scope=user`、字段 `mbti`／`subjective_score`；对象使用 `scope=object`、字段 `display_label`／`mbti`／`subjective_score`。未知项不写入。评分只接受用户本人给出的数字，模型不得代填。

每次成功写入后，在回答末尾用一行说明：

> 记忆更新：对象A的关系阶段更新为“排他约会”。撤销：告诉我“撤销刚才的记忆”。

不得显示数据库路径、内部JSON或无关旧档案。自动更新不等于自动相信：对象人格、爱意、忠诚和未来意图不得升级为稳定事实。

## 读取与按需披露

只读取当前对象需要的压缩上下文：

```bash
python3 scripts/memory_store.py context --subject-id obj-a --max-chars 4000
```

默认最多加载用户稳定档案、当前对象快照、少量假设和最近8个关键事件。不要把所有对象或完整历史注入当前回答，不要把召回到的记忆再次当成新信息写回。

## 用户控制

- 查看：`show`，可加 `--subject-id obj-a`。
- 撤销最近更新：`undo`；若回答中保留了操作编号，可用 `undo --op-id ...`。
- 暂停／恢复：`pause`、`resume`。
- 忘记对象：先确认准确代号，再运行 `forget-object obj-a --confirm`；这是硬删除并清除撤销历史。
- 撤回同意但保留现有资料：`revoke --confirm`。
- 撤回并删除：`revoke --delete --confirm`。
- 清空全部：用户明确确认后运行 `clear --confirm`。

脚本将单条内容限制为200字、总记忆限制为200条、每个对象事件20条、假设5条，并只保留最近20次可撤销操作。达到上限时先合并或删除低价值事件，不扩容规避限制。

## 设计来源

- [OpenClaw memory](https://github.com/openclaw/openclaw/blob/main/docs/concepts/memory.md)：吸收核心档案与可检索事件分层、明文可审阅和按需召回。
- [claude-mem](https://github.com/thedotmack/claude-mem)：吸收渐进披露、先返回压缩索引和证据编号，不把全部历史塞入上下文。
- [Napkin skill](https://github.com/blader/napkin)：吸收持续整理、合并重复、删除低价值内容和分类封顶。
- [Cyrene-Agent](https://github.com/Playa-0v0/Cyrene-Agent) 与 [ZifaMem](https://github.com/zifacorp/zifamem)：吸收明确事实／模型推断分离、证据、置信度、冲突和替代状态。
- [Mem0](https://github.com/mem0ai/mem0) 与 [Letta](https://github.com/letta-ai/letta)：只吸收多层记忆与核心／归档思路；本Skill不引入常驻服务、云端依赖或无界ADD-only累积。
