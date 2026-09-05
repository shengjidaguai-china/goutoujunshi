# ChatLab聊天记录分析适配

## 定位

ChatLab负责导入、检索、统计和返回带编号的聊天证据；狗头军师负责情绪承接、事实／推测拆分、关系判断与行动建议。适配不赋予狗头军师直接读取或导出微信、QQ等应用数据库的能力。

上游契约可能变化，运行前以 `chatlab manifest` 为准：

- [ChatLab外部Agent说明](https://github.com/ChatLab/ChatLab/blob/main/docs/cn/ai/external-agent.md)
- [chatlab-analyze-cn](https://github.com/ChatLab/ChatLab/blob/main/skills/chatlab-analyze-cn/SKILL.md)
- [chatlab-import-cn](https://github.com/ChatLab/ChatLab/blob/main/skills/chatlab-import-cn/SKILL.md)

## 先锁定说话人

分析前建立并显示固定映射，例如“用户＝member 17／右侧蓝色，对象A＝member 42／左侧白色”。没有确认前不解释关系：

- ChatLab或导出文件优先使用 sender／member ID、账号和会话元数据；绝不根据左右位置、语气、性别或“谁更像用户”判断。左右和颜色会随应用、导出方式与截图者变化。
- 截图或元数据缺失时，只问一个最小问题，请用户确认哪一侧或哪个昵称是自己；一年记录、跨平台记录再抽 2–3 条带时间与短摘录的锚点核对，冲突时暂停分析。
- 跨文件、跨年份和分块查询沿用同一映射；只有格式或账号改变时才重新确认，不能因内容、称谓或代词静默翻转。

## 已经导入ChatLab

先检查当前命令契约和候选会话：

```bash
chatlab --help
chatlab manifest
chatlab sessions list --format json
```

存在多个会话、同名成员或“me”身份不明时让用户消歧。先使用最窄的专用查询，并限定对象和时间：

```bash
chatlab messages between --member me --member <member> --session <session-id> --last 90d --format agent
chatlab messages search "<keyword>" --session <session-id> --format agent
chatlab messages context --id <message-id> --session <session-id> --window 10 --format agent
```

结果不足时再查统计或上下文，最后才使用只读SQL。不得使用 `--raw`、修改数据库、泄露完整聊天或为了“更全面”无边界翻页。

## 用户提供已导出文件

先确认一个准确的绝对路径；存在多个候选文件时不猜。ChatLab CLI未安装时只给官方安装方式，不擅自安装。

先只读预览：

```bash
chatlab import "/absolute/path/to/chat-export.json" --dry-run --json
```

向用户报告识别格式、目标会话、新增与重复消息数，不引用消息正文。用户已经明确要求导入且预览结果安全时，可使用相同路径正式导入；若用户只要求预览则停止。格式无法识别时查看 `chatlab formats`，不要假装支持。

ChatLab只能处理用户已经取得的导出文件。用户说“帮我导出微信聊天”时，明确说明当前适配只能分析已导出的文件，不调用第三方解密工具、不绕过应用权限。

## 关系趋势与K线

[Relationship Candlestick Lab](https://github.com/ZhenyuanPAN822/relationship-candlestick-lab) 可作为可选探索层。只吸收按时间聚合、关键转折、事件归因和代表性消息编号；K线价格、MACD、RSI、KDJ、均值回归和固定基线不是经过验证的关系测量，不能据此判断爱意、忠诚或分手概率，也不能写入稳定档案。用户想看趋势时优先展示可解释的主动频率、回复间隔、邀约兑现、冲突与修复事件，并显式标注模型评分的主观性。

## 回答与记忆边界

回答开头说明实际查询的会话和时间范围。引用 `[#1021]` 等证据编号，分开写：

1. 可观察事实：主动次数、兑现、时间间隔、明确原话。
2. 合理解释：可能的关系含义和其他解释。
3. 关键未知：线下互动、没有说出口的意图、应用外事件。
4. 建议：低成本验证动作、观察窗口和停止条件。

原始聊天、长摘要和统计表不进入长期记忆。首次同意后，也只允许把关键事件的简短摘要、日期和证据编号写入 `event`；由ChatLab或模型得出的性格与意图只能写入 `hypothesis`，不能升级为对象事实。
