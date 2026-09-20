from agent.llm_agent import LLMAgent


def print_state(agent):
    state = agent.state.to_dict()

    print("\n[Agent State]")
    print(f"current_poi  : {state['current_poi']}")
    print(f"visited_pois : {state['visited_pois']}")
    print(f"status       : {state['status']}")


def main():
    print("=== AgentOS LLM Agent ===")
    print("输入 quit 退出\n")

    agent = LLMAgent()

    while True:
        user_input = input("User > ")

        if user_input.lower() == "quit":
            print("Agent > 再见")
            break

        result = agent.handle(user_input)

        print(f"\nAgent > {result}")

        # 显示 Agent 当前内部状态
        print_state(agent)

        print()


if __name__ == "__main__":
    main()