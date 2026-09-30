# AgentOS Guide Agent

一个面向展厅导览机器人的轻量级 AgentOS 原型。

项目基于大模型 Tool Calling 实现任务规划，通过统一工具接口完成导航、知识查询和语音播报，并逐步与真实机器人 SDK、ROS2、导航系统和多模态感知模块进行集成。

当前项目主要面向天工 2.0 人形机器人导览场景。

---

## 当前版本

**v0.3**

当前版本已经完成 Agent 基础能力以及 Robot Adapter 初步重构。

目前已实现：

- Qwen 大模型接入
- LLM Tool Calling
- 多步骤任务执行
- Agent State 状态管理
- Short-term Memory 短期记忆
- FastAPI HTTP 接口
- 导航工具 `navigate_to`
- 知识查询工具 `query_knowledge`
- 语音播报工具 `speak`
- RobotAdapter 统一机器人接口
- MockRobot 模拟机器人后端
- 本地 LLM / 云端 LLM 配置切换

目前真实天工机器人 SDK 后端尚未正式接入，现阶段默认使用 MockRobot 进行功能验证。

---

## 项目目标

项目目标是构建一个面向展厅导览场景的机器人 Agent，使机器人能够根据用户的自然语言指令自主完成：

1. 理解用户需求
2. 规划执行步骤
3. 前往指定展品
4. 查询展品知识
5. 完成语音讲解
6. 管理机器人状态与会话状态
7. 后续结合视觉、语音、导航与真实机器人 SDK

例如：

用户输入：

```text
带我去展品1并做介绍
```

Agent 会自动规划并执行：

```text
navigate_to(exhibit_1)
        ↓
query_knowledge(exhibit_1)
        ↓
speak(...)
```

---

## 当前系统架构

```text
User
  │
  ▼
LLM Agent
  │
  ├── navigate_to()
  ├── query_knowledge()
  └── speak()
  │
  ▼
Tool Layer
  │
  ├── Navigation
  ├── Knowledge
  └── Speech
  │
  ▼
Robot Adapter
  │
  ├── MockRobot
  └── TienKungRobot      (planned)
  │
  ▼
ROS2 / Robot SDK
  │
  ▼
TienKung Robot
```

Robot Adapter 的作用是隔离 Agent 与具体机器人平台。

上层 Agent 不需要关心当前连接的是 Mock、仿真环境还是真实机器人。

---

## Robot Backend

当前机器人后端通过环境变量进行配置。

### Mock 模式

```env
ROBOT_BACKEND=mock
```

这是目前默认使用的模式。

在没有真实机器人或 ROS2 环境的情况下，也可以正常运行完整 Agent 流程。

当前支持：

```text
navigate_to
speak
stop
get_status
```

后续将增加：

```env
ROBOT_BACKEND=tienkung
```

用于接入天工 2.0 ROS2 SDK。

---

## LLM 配置

项目支持本地 LLM 和云端 LLM 两种运行方式。

### 本地模型

配置文件：

```text
.env.local
```

主要用于实验室服务器或本地 vLLM 部署。

示例：

```env
LLM_API_KEY=local
LLM_MODEL=/path/to/model
LLM_BASE_URL=http://127.0.0.1:8000/v1

ROBOT_BACKEND=mock
```

### 云端模型

配置文件：

```text
.env.cloud
```

示例：

```env
DASHSCOPE_API_KEY=YOUR_API_KEY
LLM_MODEL=YOUR_MODEL
LLM_BASE_URL=YOUR_BASE_URL

ROBOT_BACKEND=mock
```

运行前可将对应配置复制为：

```bash
cp .env.cloud .env
```

或者：

```bash
cp .env.local .env
```

---

## 项目结构

```text
AgentOS-Guide-Agent/
│
├── agent/
│   ├── llm_agent.py
│   ├── prompt.py
│   ├── state.py
│   └── toolkit.py
│
├── robot/
│   ├── __init__.py
│   ├── base.py
│   ├── factory.py
│   └── mock_robot.py
│
├── tools/
│   ├── navigation.py
│   ├── knowledge.py
│   └── speech.py
│
├── api_server.py
├── main.py
│
├── .env.local
├── .env.cloud
├── .env.example
│
└── README.md
```

---

## Robot Adapter

当前版本新增 RobotAdapter 层。

RobotAdapter 定义统一的机器人能力接口：

```python
navigate_to()
speak()
stop()
get_status()
```

Agent 的 Tool 不再直接实现机器人控制逻辑，而是调用统一的 Robot Adapter。

例如：

```text
navigate_to
    ↓
RobotAdapter
    ↓
MockRobot
```

未来接入真实机器人后：

```text
navigate_to
    ↓
Navigation System
    ↓
TienKungRobot
    ↓
ROS2 / SDK
```

这样可以避免 Agent 层与具体机器人 SDK 强耦合。

---

## 当前运行流程

运行：

```bash
source .venv/bin/activate
python main.py
```

示例：

```text
User > 带我去展品1并做介绍
```

执行过程：

```text
[LLM] Tool Call -> navigate_to

[MockRobot] 正在前往 exhibit_1 ...
[MockRobot] 已到达 exhibit_1

[LLM] Tool Call -> query_knowledge

[Knowledge] 正在查询 exhibit_1 的信息 ...

[LLM] Tool Call -> speak

[MockRobot] 播报：...
```

说明当前：

```text
LLM
 ↓
Tool Calling
 ↓
RobotAdapter
 ↓
MockRobot
```

链路已经能够正常运行。

---

## FastAPI

启动 API：

```bash
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

当前主要接口包括：

```text
POST /v1/chat
POST /v1/voice/transcripts
GET /v1/sessions/{session_id}/state
```

FastAPI 接口用于后续接入：

- 语音模块
- 视觉模块
- Web 前端
- 机器人控制系统
- 其他 AgentOS 模块

---

## 天工 2.0 SDK 接入计划

项目后续将逐步接入天工 2.0 ROS2 SDK。

计划新增：

```text
robot/
    tienkung_robot.py
```

用于封装真实机器人能力。

计划优先接入：

```text
speak
    ↓
天工语音接口

get_status
    ↓
机器人状态接口

set_velocity / stop
    ↓
运动控制接口
```

高层导航不会直接由 LLM 控制机器人关节，而是通过导航系统完成：

```text
Agent
 ↓
navigate_to(poi)
 ↓
Navigation System
 ↓
Localization / Planning
 ↓
Robot Motion
 ↓
TienKung SDK
```

---

## 后续计划

### v0.4

- 新增 TienKungRobot
- 接入天工 ROS2 SDK
- 优先完成真实语音接口
- 增加机器人状态读取
- 完善 Robot Adapter

### v0.5

- 接入导航模块
- 支持 POI 与真实坐标映射
- 接入雷达 / 定位信息
- 支持仿真环境测试

### 后续

- 接入机器人真实导航
- 接入视觉模块
- 接入语音识别
- 多模态融合
- 完整展厅导览任务
- 真机部署与测试

---

## Development Status

当前阶段：

```text
Agent Demo            ✅
LLM Tool Calling      ✅
FastAPI               ✅
Agent State           ✅
Mock Robot            ✅
Robot Adapter         ✅
Cloud LLM             ✅
Local LLM             ✅

TienKung SDK           🚧
ROS2 Integration       🚧
Simulation             🚧
Navigation             🚧
Vision Integration     🚧
Real Robot Test        🚧
```

---

## License

This project is currently used for research and educational purposes.
