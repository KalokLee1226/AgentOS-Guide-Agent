# AgentOS Guide Agent

一个面向展厅导览机器人的轻量级 AgentOS 原型。

当前版本基于大模型 Tool Calling 实现任务规划，并通过统一工具接口完成导航、知识查询和语音播报。项目目前使用 Mock 工具模拟机器人模块，后续计划接入天工机器人、ROS2、导航模块、语音模块、视觉模块以及本地大模型推理服务。

---

## 当前版本

**v0.1**

目前已经完成：

- Qwen 大模型接入
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

---

## 项目目标

本项目计划构建一个面向人形机器人展厅导览场景的 AgentOS。

Agent 负责理解用户自然语言指令，并根据任务动态决定调用不同机器人能力。

例如用户输入：

    带我去展品3，然后介绍一下

Agent 的执行流程为：

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

Agent 主要负责高层语义任务规划，不直接控制机器人底层运动。

未来真实系统中：

    Agent
      ↓
    Tool Interface
      ↓
    Navigation / Speech / Vision / Knowledge
      ↓
    ROS2 / HTTP / Robot SDK
      ↓
    TienKung Robot

---

## 系统架构

当前系统架构：

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
    Nav  KB   Speech
      ↓
    Mock Tools
      ↓
    Future ROS2 / Robot Modules

---

## 项目结构

    agentos_demo/
    │
    ├── agent/
    │   ├── __init__.py
    │   ├── llm_agent.py
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
    ├── api_server.py
    ├── main.py
    ├── test_qwen.py
    ├── .gitignore
    └── README.md

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

### AgentState

`agent/state.py`

用于保存机器人的结构化状态。

当前包含：

- `current_poi`
- `visited_pois`
- `status`

例如：

    current_poi  : exhibit_3
    visited_pois : ['exhibit_1', 'exhibit_3']
    status       : idle

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

LLM 不需要知道工具内部具体如何实现，只需要知道 Tool 的名称、描述和参数格式，然后由 Toolkit 将模型的 Tool Call 转发给对应 Handler。

后续 Mock Tool 可以替换为真实机器人接口，而 Agent 主体基本不需要修改。

---

## 当前 Tools

### navigate_to

用于导航到指定展品。

示例：

    navigate_to("exhibit_3")

当前为 Mock 实现。

未来计划接入：

- Nav2
- ROS2
- TienKung SDK

### query_knowledge

用于查询展品介绍信息。

示例：

    query_knowledge("exhibit_3")

当前使用本地 Python 数据模拟知识库。

未来计划替换为：

- Exhibition Knowledge Base
- RAG
- Vector Database

### speak

用于将文本交给语音模块播报。

示例：

    speak("这里是具身智能展区")

当前仅在终端打印文本。

未来计划接入真实 TTS 模块。

---

## Memory 设计

当前 Agent 采用两层记忆结构：

### Structured State

通过 `AgentState` 保存：

- `current_poi`
- `visited_pois`
- `status`

### Short-term Memory

使用 `messages` 保存最近几轮对话。

为了避免上下文不断增长，目前采用滑动窗口，只保留最近部分历史消息。

    AgentState
       ↓
    长期结构化状态

    messages
       ↓
    短期对话上下文

这样可以实现：

- 机器人知道自己在哪里
- 机器人知道刚才做过什么
- 用户可以使用“这里”“刚才那个”等自然表达
- 上下文不会无限增长

---

## FastAPI 服务

当前 Agent 已经封装为 FastAPI 服务。

启动：

    uvicorn api_server:app --host 0.0.0.0 --port 8000

启动后访问：

    http://localhost:8000

Swagger API 页面：

    http://localhost:8000/docs

---

## API 接口

### GET /

检查 Agent 服务是否运行。

示例返回：

    {
      "service": "AgentOS Guide Agent",
      "status": "running"
    }

### GET /state

获取当前 Agent 状态。

示例：

    {
      "current_poi": "exhibit_3",
      "visited_pois": [
        "exhibit_3"
      ],
      "status": "idle"
    }

### POST /chat

向 Agent 发送自然语言任务。

请求示例：

    {
      "message": "带我去展品3，然后介绍一下"
    }

Agent 可能自动执行：

    navigate_to
         ↓
    query_knowledge
         ↓
       speak

---

## 环境配置

推荐环境：

- Ubuntu 24.04 / WSL2
- Python 3.12

创建虚拟环境：

    python3 -m venv .venv

激活：

    source .venv/bin/activate

安装依赖：

    pip install openai python-dotenv fastapi uvicorn

如果 PyPI 网络访问不稳定，可以使用清华镜像：

    pip install openai python-dotenv fastapi uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple

---

## API Key 配置

在项目根目录创建 `.env`：

    DASHSCOPE_API_KEY=YOUR_API_KEY

`.env` 已加入 `.gitignore`。

不要将真实 API Key 上传到 GitHub。

---

## 运行方式

### 终端模式

激活虚拟环境：

    source .venv/bin/activate

运行：

    python main.py

### FastAPI 模式

运行：

    uvicorn api_server:app --host 0.0.0.0 --port 8000

然后访问：

    http://localhost:8000/docs

即可通过 HTTP 调用 Agent。

---

## 当前开发状态

    v0.1
    │
    ├── LLM Agent                 ✅
    ├── Qwen API                  ✅
    ├── Tool Calling              ✅
    ├── Multi-step Task           ✅
    ├── Agent State               ✅
    ├── Short-term Memory         ✅
    ├── Sliding Window Memory     ✅
    ├── Navigation Mock Tool      ✅
    ├── Knowledge Mock Tool       ✅
    ├── Speech Mock Tool          ✅
    ├── FastAPI Service           ✅
    │
    ├── Tool Adapter              ⏳
    ├── Real Navigation           ⏳
    ├── ROS2 Integration          ⏳
    ├── ASR Integration           ⏳
    ├── TTS Integration           ⏳
    ├── Vision Integration        ⏳
    ├── Knowledge Base / RAG      ⏳
    ├── Local LLM Deployment      ⏳
    └── TienKung Integration      ⏳

---

## 下一阶段

下一阶段计划重点完成：

1. 增加 Tool Adapter / Client 层
2. 将 Mock Tool 与真实模块接口解耦
3. 对接真实导航模块
4. 设计 ROS2 / HTTP Tool Interface
5. 接入 ASR、TTS、Vision 等机器人模块
6. 在 RTX 5880 / DGX Spark 上部署本地模型
7. 将云端模型接口替换为本地 OpenAI-compatible API
8. 接入真实天工机器人

最终目标：

    User
      ↓
    ASR
      ↓
    AgentOS
      ↓
    LLM
      ↓
    Tool Calling
      ↓
    ROS2 / Robot API
      ↓
    TienKung Humanoid Robot

---

## Reference

Agent 架构设计过程中参考了 RPent：

https://github.com/RLinf/RPent

主要参考其 Planner、Agent Loop、Toolkit 和 Tool Handler 等设计思想，并针对展厅导览机器人场景进行了简化实现。

---

## Status

当前项目处于早期原型阶段。

现阶段重点验证：

    Natural Language
          ↓
    LLM Planning
          ↓
    Tool Calling
          ↓
    Robot Capability

这一核心 AgentOS 工作流。
