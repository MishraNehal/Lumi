from collections import deque


class SimpleChatMemory:
    """
    Stores last N turns of conversation.
    Each turn = (user question, assistant answer).
    """

    def __init__(self, max_turns: int = 5):
        self.history = deque(maxlen=max_turns)

    def add(self, question: str, answer: str):
        self.history.append((question.strip(), answer.strip()))

    def get_last_turn(self) -> str:
        """Return only the last 1 turn — used to avoid topic pollution."""
        if not self.history:
            return ""
        q, a = list(self.history)[-1]
        return f"User: {q}\nAssistant: {a}"

    def get_full_history(self) -> str:
        """Return all stored turns as a formatted string."""
        if not self.history:
            return "No previous conversation."
        lines = []
        for q, a in self.history:
            lines.append(f"User: {q}")
            lines.append(f"Assistant: {a}")
        return "\n".join(lines)

    def get_history_list(self) -> list[dict]:
        """Return history as list of dicts for frontend display."""
        result = []
        for q, a in self.history:
            result.append({"role": "user", "content": q})
            result.append({"role": "assistant", "content": a})
        return result

    def clear(self):
        self.history.clear()

    def is_empty(self) -> bool:
        return len(self.history) == 0