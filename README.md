# AgentOS Guide Agent

一个面向展厅导览机器人的轻量级 AgentOS 原型。

当前版本基于大模型 Tool Calling 实现任务规划，并通过统一工具接口完成导航、知识查询和语音播报。

项目目前已支持：

- 云端大模型 API
- 本地 OpenAI-compatible 大模型服务
- 多步骤 Tool Calling
- Agent 状态管理
- 短期对话记忆
- FastAPI 会话化接口

当前机器人能力仍主要使用 Mock Tool 模拟，后续计划逐步接入天工机器人、ROS2、导航模块、语音模块、视觉模块以及真实知识库。

---

## 当前版本

**v0.3**

目前已经完成：

- Cloud LLM 接入
- Local LLM 接入
- OpenAI-compatible LLM Backend
- Qwen3-14B 本地部署
- vLLM 本地推理服务
- LLM Tool Calling
- 多步骤任务执行
- Agent State 状态管理
- Short-term Memory 短期记忆
- 滑动窗口对话上下文
- Navigation Mock Tool
- Knowledge Mock Tool
- Speech Mock Tool
- FastAPI HTTP 服务
- Agent 状态查询接口
- 英文 System Prompt 与英文 Tool Schema
- 面向文本、语音和机器人客户端的会话化 API
- 可选的外部 TTS HTTP Adapter
- 本地模型 `<think>...</think>` 内容清理
- 云端 / 本地模型环境变量切换

---

## 项目目标

本项目计划构建一个面向人形机器人展厅导览场景的 AgentOS。

Agent 负责理解用户自然语言指令，并根据任务动态决定调用不同机器人能力。

例如用户输入：

```text
带我去展品3，然后介绍一下
```

Agent 的执行流程：

```text
User
  ↓
LLMAgent
  ↓
navigate_to("exhibit_3")
  ↓
query_knowledge("exhibit_3")
  ↓
speak(...)
  ↓
Task Finished
```

Agent 主要负责高层语义任务规划，不直接控制机器人底层运动。

未来真实系统中：

```text
Agent
  ↓
Tool Interface
  ↓
Navigation / Speech / Vision / Knowledge
  ↓
ROS2 / HTTP / Robot SDK
  ↓
TienKung Robot
```

---

## 系统架构

当前系统架构：

```text
User / Frontend / Robot
          ↓
        HTTP
          ↓
    FastAPI Server
          ↓
       LLMAgent
     ┌────┴────┐
     ↓         ↓
 AgentState   LLM Model
     ↓
 Tool Registry
  ┌──┼──────┐
  ↓  ↓      ↓
 Nav KB   Speech
  ↓
Mock Tools
  ↓
Future ROS2 / Robot Modules
```

当前 LLM Backend 支持两种模式：

### Cloud Mode

```text
AgentOS
  ↓
OpenAI-compatible Client
  ↓
Cloud LLM API
```

### Local Mode

```text
AgentOS
  ↓
OpenAI-compatible Client
  ↓
127.0.0.1:8000/v1
  ↓
vLLM
  ↓
Local Qwen3-14B
  ↓
NVIDIA GPU
```

---

## 项目结构

```text
agentos_demo/
│
├── agent/
│   ├── __init__.py
│   ├── llm_agent.py
│   ├── prompt.py
│   ├── rule_agent.py
│   ├── state.py
│   └── toolkit.py
│
├── tools/
│   ├── __init__.py
│   ├── navigation.py
│   ├── knowledge.py
│   └── speech.py
│
├── examples/
│   └── voice_client.py
│
├── tests/
│
├── api_server.py
├── main.py
├── test_qwen.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 核心模块

### LLMAgent

`agent/llm_agent.py`

负责：

- 接收用户自然语言输入
- 调用大模型进行任务决策
- 执行 Tool Calling
- 将 Tool Result 返回给模型
- 完成多步骤任务循环
- 管理短期对话上下文
- 结合 AgentState 处理连续任务
- 支持云端和本地 OpenAI-compatible LLM
- 清理部分本地模型返回的 `<think>...</think>` 内容

LLM Backend 可通过环境变量切换，而无需修改 Agent 主体逻辑。

### AgentState

`agent/state.py`

用于保存机器人的结构化状态。

当前包含：

- `current_poi`
- `visited_pois`
- `status`

例如：

```text
current_poi  : exhibit_3
visited_pois : ['exhibit_1', 'exhibit_3']
status       : idle
```

因此 Agent 可以理解：

- “介绍一下这里”
- “我刚才参观了哪些展品？”

这类依赖上下文的信息。

### Toolkit

`agent/toolkit.py`

负责统一管理 Agent 可以使用的工具。

当前包括：

- `navigate_to`
- `query_knowledge`
- `speak`

LLM 不需要知道工具内部具体如何实现，只需要知道 Tool 的名称、描述和参数格式。

Toolkit 会将模型生成的 Tool Call 转发给对应 Handler。

后续 Mock Tool 可以替换为真实机器人接口，而 Agent 主体基本不需要修改。

---

## 当前 Tools

### navigate_to

用于导航到指定展品。

示例：

```text
navigate_to("exhibit_3")
```

当前为 Mock 实现。

未来计划接入：

- Nav2
- ROS2
- TienKung SDK

### query_knowledge

用于查询展品介绍信息。

示例：

```text
query_knowledge("exhibit_3")
```

当前使用本地 Python 数据模拟知识库。

未来计划替换为：

- Exhibition Knowledge Base
- RAG
- Vector Database

### speak

用于将文本交给语音模块播报。

示例：

```text
speak("这里是具身智能展区")
```

当前支持：

- 终端 Mock 输出
- API 响应中的 `speech` 数组
- 可选外部 TTS HTTP Adapter

未来计划进一步接入真实语音模块。

---

## Memory 设计

当前 Agent 采用两层记忆结构。

### Structured State

通过 `AgentState` 保存：

- `current_poi`
- `visited_pois`
- `status`

### Short-term Memory

使用 `messages` 保存最近几轮对话。

为了避免上下文无限增长，目前采用滑动窗口，只保留最近部分历史消息。

```text
AgentState
   ↓
长期结构化状态

messages
   ↓
短期对话上下文
```

这样可以实现：

- 机器人知道自己在哪里
- 机器人知道刚才做过什么
- 用户可以使用“这里”“刚才那个”等自然表达
- 上下文不会无限增长

---

## FastAPI 服务

当前 Agent 已经封装为 FastAPI 服务。

启动：

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

启动后访问：

```text
http://localhost:8000
```

Swagger API：

```text
http://localhost:8000/docs
```

---

## API 接口

新接入请优先使用 `/v1/*`。

每个用户或机器人应保存服务返回的 `session_id`，并在后续请求中重复传入，避免不同用户共享对话记忆。

原有 `/chat` 和 `/state` 仍保留兼容。

### POST /v1/chat

供前端、机器人控制端或其他业务模块调用。

示例：

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"带我去展品3，然后介绍一下","source":"robot"}'
```

第一次请求可省略 `session_id`。

响应示例：

```json
{
  "session_id": "624e905e-7ceb-45ba-8c1d-8122af96ef21",
  "reply": "已经完成讲解。",
  "speech": [
    "这里是具身智能展区……"
  ],
  "tool_calls": [
    {
      "name": "navigate_to",
      "arguments": {
        "poi_id": "exhibit_3"
      },
      "result": {
        "success": true,
        "poi_id": "exhibit_3",
        "status": "arrived"
      }
    }
  ],
  "state": {
    "current_poi": "exhibit_3",
    "visited_pois": [
      "exhibit_3"
    ],
    "status": "idle"
  }
}
```

后续对话把响应中的 `session_id` 原样传回：

```json
{
  "message": "再介绍一下这里",
  "session_id": "624e905e-7ceb-45ba-8c1d-8122af96ef21",
  "source": "text"
}
```

### POST /v1/voice/transcripts

语音模块完成 ASR 后，将最终识别文本传给 Agent：

```bash
curl -X POST http://localhost:8000/v1/voice/transcripts \
  -H "Content-Type: application/json" \
  -d '{"transcript":"带我去展品3，然后介绍一下"}'
```

语音模块可以读取响应中的 `speech` 数组并逐条交给 TTS。

可参考：

```text
examples/voice_client.py
```

另一种接法是由 Agent 主动推送 TTS。

在 `.env` 中配置：

```dotenv
SPEECH_SERVICE_URL=http://127.0.0.1:9000/tts
SPEECH_SERVICE_TIMEOUT=10
```

此时 `speak` 工具会向该地址发送：

```json
{
  "text": "需要播报的文本"
}
```

### GET /v1/sessions/{session_id}/state

读取指定会话的机器人状态。

### DELETE /v1/sessions/{session_id}

结束会话并释放该会话的短期记忆。

### GET /

检查 Agent 服务是否运行。

示例：

```json
{
  "service": "AgentOS Guide Agent",
  "status": "running"
}
```

### GET /state

获取当前 Agent 状态。

示例：

```json
{
  "current_poi": "exhibit_3",
  "visited_pois": [
    "exhibit_3"
  ],
  "status": "idle"
}
```

### POST /chat

兼容旧版接口。

请求示例：

```json
{
  "message": "带我去展品3，然后介绍一下"
}
```

Agent 可能自动执行：

```text
navigate_to
     ↓
query_knowledge
     ↓
   speak
```

---

## 环境配置

推荐开发环境：

- Ubuntu 22.04 / 24.04
- WSL2
- Python 3.10+
- VSCode

创建虚拟环境：

```bash
python3 -m venv .venv
```

如果系统缺少 `python3-venv`，也可以使用：

```bash
python3 -m pip install --user virtualenv
python3 -m virtualenv .venv
```

激活：

```bash
source .venv/bin/activate
```

安装项目依赖：

```bash
pip install -r requirements.txt
```

---

## LLM 配置

项目通过 OpenAI-compatible Client 调用大模型。

因此可以通过环境变量在云端和本地模型之间切换。

推荐复制：

```bash
cp .env.example .env
```

然后根据实际环境修改 `.env`。

### 云端 LLM

例如使用 Qwen 云端服务：

```dotenv
DASHSCOPE_API_KEY=your_api_key
LLM_MODEL=qwen3.8-omni-flash
LLM_BASE_URL=https://maas.qianwenaiapi.com/compatible-mode/v1
```

此模式需要有效的云端 API Key。

---

## Local LLM Deployment

当前已经在 RTX 5880 工作站上完成本地模型部署验证。

测试环境：

- GPU: NVIDIA RTX 5880 Ada Generation
- VRAM: 48 GB
- Model: Qwen3-14B
- Inference Framework: vLLM
- API Protocol: OpenAI-compatible API
- Local API: `http://127.0.0.1:8000/v1`

### 模型目录

测试模型路径：

```text
/mnt/models/Qwen3-14B
```

实际部署时可根据服务器环境修改。

### 启动 vLLM

首先进入本地推理环境：

```bash
source ~/agentos/llm_env/bin/activate
```

由于当前测试环境未安装系统级 `nvcc`，启动前关闭 FlashInfer sampler：

```bash
export VLLM_USE_FLASHINFER_SAMPLER=0
```

启动本地模型服务：

```bash
vllm serve /mnt/models/Qwen3-14B \
  --host 127.0.0.1 \
  --port 8000 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

看到：

```text
Application startup complete.
```

说明 vLLM 服务已经启动。

### 检查本地模型服务

查看模型：

```bash
curl http://127.0.0.1:8000/v1/models
```

测试聊天：

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Qwen3-14B",
    "messages": [
      {
        "role": "user",
        "content": "你好，请简单介绍一下你自己。"
      }
    ]
  }'
```

### AgentOS 使用本地模型

在 `.env` 中配置：

```dotenv
LLM_API_KEY=local
LLM_MODEL=/mnt/models/Qwen3-14B
LLM_BASE_URL=http://127.0.0.1:8000/v1
```

本地 OpenAI-compatible 服务通常不需要真实 API Key。

`LLM_API_KEY=local` 仅作为 OpenAI Client 的占位值。

此时 Agent 调用链路为：

```text
AgentOS
  ↓
OpenAI-compatible Client
  ↓
http://127.0.0.1:8000/v1
  ↓
vLLM
  ↓
Qwen3-14B
  ↓
RTX 5880
```

无需修改 Agent 主体代码。

---

## 本地模型 Tool Calling

Qwen3-14B + vLLM 已完成 Tool Calling 验证。

当前本地模型能够正确生成：

```text
navigate_to
query_knowledge
speak
```

等工具调用。

测试任务：

```text
带我去展品1，并做介绍
```

实际执行流程：

```text
navigate_to("exhibit_1")
        ↓
query_knowledge("exhibit_1")
        ↓
speak(...)
        ↓
Task Finished
```

本地模型最终回答中的 `<think>...</think>` 内容会在 Agent 层进行清理，不直接展示给用户。

---

## API Key 配置

如果使用云端模型，需要配置对应的真实 API Key。

例如：

```dotenv
DASHSCOPE_API_KEY=YOUR_API_KEY
```

如果使用本地 OpenAI-compatible 模型，则可以配置：

```dotenv
LLM_API_KEY=local
```

`.env` 已加入 `.gitignore`。

不要将真实 API Key 上传到 GitHub。

---

## 运行方式

### 终端模式

激活 Agent 环境：

```bash
source .venv/bin/activate
```

运行：

```bash
python main.py
```

示例：

```text
User > 带我去展品1，并做介绍
```

### FastAPI 模式

运行：

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

然后访问：

```text
http://localhost:8000/docs
```

即可通过 HTTP 调用 Agent。

注意：

如果本地 vLLM 已占用 `8000` 端口，则 FastAPI 服务应使用其他端口，例如：

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8080
```

---

## 当前开发状态

```text
v0.3
│
├── LLM Agent                     ✅
├── Cloud Qwen API                ✅
├── Local OpenAI-compatible LLM   ✅
├── Qwen3-14B Local Deployment    ✅
├── vLLM Inference Service        ✅
├── Tool Calling                  ✅
├── Local Tool Calling            ✅
├── Multi-step Task               ✅
├── Agent State                   ✅
├── Short-term Memory             ✅
├── Sliding Window Memory         ✅
├── Navigation Mock Tool          ✅
├── Knowledge Mock Tool           ✅
├── Speech Mock Tool              ✅
├── FastAPI Service               ✅
├── Session API                   ✅
├── Voice Transcript API          ✅
├── Optional TTS Adapter          ✅
│
├── Tool Adapter                  ⏳
├── Real Navigation               ⏳
├── ROS2 Integration              ⏳
├── ASR Integration               ⏳
├── Real TTS Integration          ⏳
├── Vision Integration            ⏳
├── Knowledge Base / RAG          ⏳
└── TienKung Integration          ⏳
```

---

## 下一阶段

下一阶段计划重点完成：

1. 增加 Tool Adapter / Client 层
2. 将 Mock Tool 与真实模块接口解耦
3. 对接真实导航模块
4. 设计 ROS2 / HTTP Tool Interface
5. 接入 ASR、TTS 和 Vision 模块
6. 接入真实机器人导航状态和执行结果
7. 构建展厅知识库 / RAG
8. 测试 Agent 与天工机器人整体联动
9. 优化本地模型服务的后台运行和自动启动方式
10. 根据实际性能需求评估其他本地模型

最终目标：

```text
User
  ↓
ASR
  ↓
AgentOS
  ↓
Local / Cloud LLM
  ↓
Tool Calling
  ↓
ROS2 / Robot API
  ↓
Navigation / Speech / Vision
  ↓
TienKung Humanoid Robot
```

---

## Reference

Agent 架构设计过程中参考了 RPent：

https://github.com/RLinf/RPent

主要参考其 Planner、Agent Loop、Toolkit 和 Tool Handler 等设计思想，并针对展厅导览机器人场景进行了简化实现。

---

## Status

当前项目处于原型开发阶段。

目前已经完成从：

```text
Natural Language
      ↓
LLM Planning
      ↓
Tool Calling
      ↓
Robot Capability
```

这一核心 AgentOS 工作流的验证。

同时已完成：

```text
AgentOS
   ↓
Local OpenAI-compatible API
   ↓
vLLM
   ↓
Qwen3-14B
   ↓
RTX 5880
```

这一完整本地大模型推理链路的部署与验证。

下一阶段将重点从 Mock Tool 逐步过渡到真实机器人模块。
