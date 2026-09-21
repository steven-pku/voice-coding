# Voice Coding

[English](README.md) · [Skill](SKILL.md) · [验证记录](VALIDATION.md)

利用 Codex 现有 Voice 功能，在一个主控任务中管理多个编码任务：说出要做什么，询问进度，检查结果，再结束工作。

**v0.1.1 公开预览版。** 仓库提供操作流程和轻量本地台账；语音与任务能力由 Codex 提供。[离线 CI](https://github.com/steven-pku/voice-coding/actions/workflows/check.yml)覆盖 macOS、Linux 和 Python 3.10／3.13。实际 Voice 使用前，请阅读[验证记录与限制](VALIDATION.md)。

## 开始使用

需要具备相应任务工具及 Voice 入口的 Codex；可选的本地辅助工具需要 Python 3.10+。Voice 是否可用取决于功能开放情况。Voice 是持续语音对话，dictation 是把语音转成文字输入。参见 [OpenAI Voice 指南](https://learn.chatgpt.com/docs/features/voice)。

先在仓库根目录运行本地演示：

```sh
python3 scripts/demo.py
```

演示在临时目录中使用合成任务，不调用模型或网络，不创建或运行 Codex 任务。

阅读[安装脚本](scripts/install.py)，再安装到目标项目：

```sh
python3 scripts/install.py --project /path/to/target-project
```

将路径替换为你的项目目录。脚本把 Skill 及配套文件复制到项目内的 `.agents/skills/voice-coding/`，目标已存在时拒绝覆盖，不安装到全局。

在该项目中新建一个 **Codex 任务**，明确调用 `$voice-coding`，确认该任务能发现 Skill 后再使用。复制成功不等于加载成功。Voice 可用时，在这个任务中开启语音。

## 第一次对话

> 使用 $voice-coding。你负责这个项目的主控。新建两个任务：一个审查文档，一个审查测试，都只读。把发现汇总到这里，不发布任何内容。

接着说：

> 看一下这两个任务，告诉我哪些需要处理，哪些已经可以检查。

主控记录原生工具返回的任务 ID 和主机，读取最新状态，再汇总结果。需要写入相同路径的工作按顺序执行。暂停、创建结果不确定、核验与结束的完整示例见[合成会话](examples/voice-session.md)。

## 本地辅助工具

可选的 Python 标准库工具记录任务指针、预定写入范围、状态观察和主控核验回执。它不调用模型、不联网、不执行任务。

在仓库根目录运行：

```sh
python3 scripts/voice_coding.py init /path/to/local/board.json --controller-id my-controller --host local
python3 scripts/voice_coding.py status /path/to/local/board.json
python3 scripts/voice_coding.py check /path/to/local/board.json
```

`my-controller` 和 `local` 只是示意值，请替换为当前环境提供的精确任务 ID 与主机。请替换成本地私人台账路径，并将台账排除在版本控制之外。安装后，目标项目内也有 `.agents/skills/voice-coding/scripts/voice_coding.py`。登记、绑定、观察和核验命令见 `--help` 与 [SKILL.md](SKILL.md)。除 `init` 外，所有修改命令都需要当前 `--revision N`，避免旧状态覆盖新修改。

## 使用边界

- 语音不会扩大权限。本流程要求发布、付费、凭据修改或破坏性操作取得明确文字授权，宽泛目标不能替代该授权。
- 执行任务报告完成，只代表一次状态观察。主控还需检查产物、单独记录核验，并在处理完未决事项后关闭任务。
- 台账中的暂停只阻止本流程继续派发工作，**不能终止**原生任务或进程。当前工具不支持停止时，主控应明确说明，并引导你使用原生界面。
- 写入范围均指辅助工具所在机器的本地路径，所有记录都会保守比较，不按任务主机分开；本版不建模远程文件系统。检查不是沙箱，也不能锁住其他程序。暂停中的任务仍保留写入范围。明确取消的任务只有在确认未创建或已经停止执行后，才可释放本地预留范围；工具本身不停止进程。仅大小写不同的路径按重叠处理。
- 原生工具随运行环境而异。本项目不承诺通用跨运行时控制，不提供后台守护进程，也不会自动恢复暂停任务。详见[原生工具对照](references/native-tools.md)。

[安全说明](SECURITY.md) · [贡献指南](CONTRIBUTING.md) · [更新记录](CHANGELOG.md) · [MIT 许可](LICENSE)
