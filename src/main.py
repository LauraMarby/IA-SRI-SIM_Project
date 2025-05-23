from agents.user_agent import UserAgent
from agents.coordinator_agent import CoordinatorAgent

if __name__ == "__main__":
    user_agent = UserAgent()
    coordinator = CoordinatorAgent()

    user_input = user_agent.get_input()
    coordinator.handle_query(user_input)
