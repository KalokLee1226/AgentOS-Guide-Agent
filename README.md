# AgentOS Guide Agent

面向展厅导览机器人的轻量级 AgentOS 原型。项目通过大语言模型的 Tool Calling 能力理解自然语言指令、选择工具并执行导览任务，使用 Robot Adapter 隔离 Agent 逻辑与机器人平台。

**当前版本：v0.3（新增 DGX Spark 本地部署验证）**

> 当前已在 NVIDIA DGX Spark 上部署 Qwen3-30B-A3B-Instruct-2507-FP8，并成功验证 `navigate_to → query_knowledge → speak` 的完整 **MockRobot** 工具调用流程。真实机器人 SDK、ROS2 导航和 Isaac Sim/仿真联调尚未完成。

## 1. 已实现功能

- OpenAI-compatible 大模型接口，支持云端和本地模型切换
- LLM Tool Calling 和多步骤任务执行
- Agent State 状态管理、短期对话记忆
- 导航 `navigate_to`、知识查询 `query_knowledge`、播报 `speak`
- RobotAdapter 接口及 MockRobot 后端
- FastAPI HTTP 接口
- NVIDIA DGX Spark 上的 Qwen3-30B FP8 + vLLM 本地推理部署与验证

## 2. 架构与工作流程

```text
User / API
    │
    ▼
LLMAgent（规划、短期记忆、AgentState）
    │ OpenAI-compatible Chat Completions
    ├──────────► Cloud LLM
    └──────────► Local vLLM → Qwen3-30B（DGX Spark）
    │
    ▼ Tool Calling
Toolkit
    ├── navigate_to(poi_id) ──► RobotAdapter → MockRobot
    ├── query_knowledge(poi_id) → 本地展品知识
    └── speak(text) ──────────► RobotAdapter → MockRobot
```

例：输入“带我去展品1并做介绍”，Agent 可依次调用导航、查询和播报工具，并更新当前展品位置与访问记录。

**说明：** 现在的导航与播报为 Mock 执行，并不代表机器人已真实移动或播放声音。

## 3. 项目结构

```text
agentos_demo/
├── agent/
│   ├── llm_agent.py        # LLM 客户端、工具调用、多轮记忆
│   ├── prompt.py           # 系统提示词
│   ├── state.py            # Agent 状态
│   ├── toolkit.py          # 工具注册与分发
│   └── rule_agent.py
├── robot/
│   ├── base.py             # RobotAdapter 抽象接口
│   ├── factory.py          # Robot 后端选择
│   └── mock_robot.py       # 模拟机器人
├── tools/
│   ├── navigation.py
│   ├── knowledge.py
│   └── speech.py
├── tests/
├── examples/
├── main.py                # 命令行交互入口
├── api_server.py          # FastAPI 入口
├── requirements.txt
├── .env.example
└── README.md
```

`robot/factory.py` 支持 `ROBOT_BACKEND=mock`。`tienkung` 为预留目标，仓库当前版本尚未提供可运行的 `robot/tienkung_robot.py`，请勿直接切换。

## 4. 快速开始：AgentOS

要求：Python 3.11/3.12、可访问的 OpenAI-compatible LLM 服务。

```bash
cd ~/projects/agentos_demo  # 按实际仓库路径调整
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

创建本机配置文件 `.env`（不要提交密钥）：

```dotenv
LLM_BASE_URL=http://127.0.0.1:8001/v1
LLM_API_KEY=local
LLM_MODEL=Qwen3-30B
ROBOT_BACKEND=mock
```

启动命令行 Agent：

```bash
source .venv/bin/activate
python main.py
```

输入 `带我去展品1并做介绍` 测试；输入 `quit` 退出。

> 如果 Shell 中已设置了同名环境变量，它们可能优先于 `.env` 生效。可在运行前检查环境变量，或按需显式传入 `LLM_BASE_URL=... LLM_MODEL=... ROBOT_BACKEND=mock python main.py`。

### 云端模型切换

更改 `.env` 中的 `LLM_BASE_URL`、`LLM_MODEL` 及 `LLM_API_KEY`（或 `DASHSCOPE_API_KEY`）即可，无需修改 `llm_agent.py`。云端密钥不要写进 README、提交到 GitHub 或发到公开日志。

## 5. DGX Spark 本地模型部署（已验证）

以下步骤记录本项目 **2026-10-12** 在实验室 DGX Spark 上验证成功的配置，其他机器/驱动组合需要重新确认兼容性。

| 项目 | 已验证配置 |
| --- | --- |
| 设备 | NVIDIA DGX Spark / GB10 / ARM64 |
| 系统 Python | 3.12.3 |
| NVIDIA 驱动 | 580.178.04 |
| 推理镜像 | `nvcr.io/nvidia/vllm:26.02-py3` |
| vLLM | 0.15.1（该镜像内） |
| 模型 | `Qwen/Qwen3-30B-A3B-Instruct-2507-FP8` |
| 模型来源 | ModelScope |
| 端口 | Spark 本机 `127.0.0.1:8001` |
| 容器名称 | `agentos-qwen30b` |
| 最大上下文 | 8192 |
| 工具解析器 | `hermes` |

### 5.1 前置检查

```bash
uname -m
nvidia-smi
docker --version
docker info --format '{{json .Runtimes}}'
df -h ~
```

需确认主机能正常使用 Docker NVIDIA runtime，且磁盘、统一内存充足。**不要为了部署 AgentOS 升级共享主机驱动或停止其他项目容器。**

### 5.2 拉取 vLLM 镜像

```bash
docker pull --platform linux/arm64 nvcr.io/nvidia/vllm:26.02-py3
```

可用以下命令确认 GPU 能被容器内的 PyTorch 识别：

```bash
docker run --rm --gpus all --entrypoint python3 \
  nvcr.io/nvidia/vllm:26.02-py3 \
  -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

### 5.3 从 ModelScope 下载模型

如果不能直接访问 Hugging Face，可使用 ModelScope。创建独立的下载虚拟环境：

```bash
mkdir -p ~/models
python3 -m venv ~/models/.download-venv
source ~/models/.download-venv/bin/activate
python -m pip install modelscope -i https://pypi.tuna.tsinghua.edu.cn/simple
```

下载到固定路径：

```python
from modelscope import snapshot_download

snapshot_download(
    model_id="Qwen/Qwen3-30B-A3B-Instruct-2507-FP8",
    local_dir="/home/nvidia/models/Qwen3-30B-A3B-Instruct-2507-FP8",
)
```

可以保存为临时下载脚本后运行。大文件建议在 `tmux` 会话中下载，以减少 SSH 断连影响。完成后检查模型配置及多个 `.safetensors` 权重分片：

```bash
du -sh ~/models/Qwen3-30B-A3B-Instruct-2507-FP8
ls -lh ~/models/Qwen3-30B-A3B-Instruct-2507-FP8
```

### 5.4 首次创建 vLLM 容器

下面是**已成功验证**的容器命令，必须保留自动工具调用配置。首次创建执行一次即可；再次使用请看第 6 节。

```bash
docker run -d \
  --name agentos-qwen30b \
  --gpus all \
  --ipc=host \
  -p 127.0.0.1:8001:8000 \
  -v /home/nvidia/models/Qwen3-30B-A3B-Instruct-2507-FP8:/models/qwen:ro \
  --entrypoint vllm \
  nvcr.io/nvidia/vllm:26.02-py3 \
  serve /models/qwen \
  --served-model-name Qwen3-30B \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype auto \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.65 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

- `--entrypoint vllm`：显式指定命令入口，避免重复 `vllm serve` 参数解析。
- `--enable-auto-tool-choice` + `--tool-call-parser hermes`：允许 Agent 使用 `tool_choice="auto"`。
- 仅向 Spark 本机开放 `8001`，避免直接将无认证的推理接口暴露到局域网。
- `--gpu-memory-utilization 0.65` 是 vLLM 的内存预算配置，并不等于整个系统最多用 65% 内存。
- 首次加载 FP8/MoE 权重可能耗时数分钟，容器显示 `Up` 不代表模型已经就绪。

验证：

```bash
docker logs -f --tail 50 agentos-qwen30b
# 看到 Application startup complete. 后按 Ctrl+C 退出日志查看
curl -f http://127.0.0.1:8001/health
curl -sS http://127.0.0.1:8001/v1/models
```

## 6. 日常启动与停止（推荐收藏）

适用于**模型权重和容器都已经部署好**的 Spark，不需要再次下载模型，也不需要再次执行 `docker run`。

### 6.1 每次使用时

```bash
# 1. SSH 登录 Spark
# 2. 查看已有容器
docker ps -a --filter name=agentos-qwen30b

# 3. 若容器未运行，启动现有容器
docker start agentos-qwen30b

# 4. 等待服务初始化完成
docker logs --tail 30 agentos-qwen30b
curl -f http://127.0.0.1:8001/health

# 5. 启动 AgentOS
cd ~/projects/agentos_demo
source .venv/bin/activate
python main.py
```

如果健康检查暂时失败，等待模型加载，不要重复执行 `docker run`。必要时查看 `docker logs -f agentos-qwen30b`。

### 6.2 结束使用时

在 AgentOS 交互界面输入：

```text
quit
```

这只会退出 AgentOS，不会停止后台 vLLM 服务。在**确认无人共用当前模型服务**后，若确实需要释放内存，可以执行：

```bash
docker stop agentos-qwen30b
```

SSH 断连通常不影响已使用 `-d` 启动的容器；容器是否持续运行应以 `docker ps` 为准。

## 7. 工具调用验证结果

2026-10-12，在 Spark 本地模型和 MockRobot 下，输入：

```text
带我去展品1并做介绍
```

观察到模型自主触发并成功执行：

```text
navigate_to({"poi_id": "exhibit_1"})
query_knowledge({"poi_id": "exhibit_1"})
speak({"text": "..."})
```

三项工具均返回 `success: True`，最终状态包括：

```text
current_poi  : exhibit_1
visited_pois : ['exhibit_1']
status       : idle
```

这证明了**单次测试下**的自然语言指令 → 本地 LLM 工具调用 → MockRobot 执行 → 状态更新闭环；尚不构成复杂任务可靠性、真实导航或物理语音播报的验证。

## 8. FastAPI（可选）

```bash
cd ~/projects/agentos_demo
source .venv/bin/activate
python -m uvicorn api_server:app --host 127.0.0.1 --port 8000
```

本机 API 文档：`http://127.0.0.1:8000/docs`。

主要接口：`POST /v1/chat`、`POST /v1/voice/transcripts`、`GET /v1/sessions/{session_id}/state`。

注意区分：AgentOS FastAPI 使用 `8000`（本机示例），vLLM 映射使用 Spark 本机 `8001`。如需远程访问，请优先使用 SSH 端口转发和适当的访问控制。

## 9. 常见问题

| 现象 | 优先检查 |
| --- | --- |
| `Connection refused` / 连接重置 | `docker ps`、`docker logs`；模型可能尚未完成加载 |
| `400: "auto" tool choice requires...` | vLLM 必须使用 `--enable-auto-tool-choice --tool-call-parser hermes` 启动 |
| `No LLM API key configured` | 检查 `.env`、`LLM_BASE_URL` 和环境变量优先级 |
| `load_dotenv()` 在 `python - <<'PY'` 中报 `AssertionError` | 在临时脚本中明确使用 `load_dotenv(".env", override=True)`；正常 `main.py` 不一定受此影响 |
| SSH 断开 | 重新连接后检查容器；不需要再次下载模型 |
| 内存占用高 | Spark 为 CPU/GPU 统一内存架构；结合 `free -h` 的 `available`、`nvidia-smi` 和实际工作负载判断 |
| Github/Hugging Face 超时 | 使用可达镜像源、ModelScope 或离线传输，不要擅自更改共享服务器的全局代理 |

## 10. 本地开发与 Spark 同步

开发以本地 WSL Git 工作区为准，推送到 GitHub；Spark 目前因 GitHub 访问超时，使用 MobaXterm SFTP 或 `rsync` 同步必要的代码和 README。

同步时**不要覆盖** Spark 的 `.env`、`.venv`、模型目录或 Docker 数据。Spark 当前的项目源码位于 `~/projects/agentos_demo`，是通过源码压缩包部署的，不含完整 Git 历史，因此不能直接在该目录使用 `git pull`。

## 11. 后续计划

- 多轮导览任务、错误恢复及 Tool Calling 可靠性测试
- 记录本地推理延迟、内存占用和模型对比数据
- 完善 RobotAdapter，接入天工机器人 SDK / ROS2
- 在可用的仿真环境中验证 Agent 与机器人执行链路
- 结合语音识别、真实播报、导航与视觉模块

---

**用途说明：** 本项目目前用于课程实践、研究与原型验证。真实机器人动作和仿真接口仍需独立测试；请勿将 Mock 成功结果视为真实机器人安全验证。
