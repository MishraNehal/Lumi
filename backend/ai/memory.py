class SimpleChatMemory:
    def __init__(self):
        self.history = []

    def add(self, question: str, answer: str):
        self.history.append({
            "question": question,
            "answer": answer
        })

    def get_last_turn(self) -> str:
        """
        Only return last Q&A.
        Prevents topic pollution.
        """
        if not self.history:
            return ""
        last = self.history[-1]
        return f"User: {last['question']}\nAssistant: {last['answer']}"
