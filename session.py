from knowledge import KnowledgeEngine
from memory import AdviserMemory


class AdviserSession:
    def __init__(self):
        self.knowledge = KnowledgeEngine()

        self.conversation = []

        self.memory = AdviserMemory()

        self.adviser_mind = """
The user has not added any knowledge yet.
""".strip()

        self.has_knowledge = False


    def learn(
        self,
        chunks,
        adviser_mind
    ):
        self.knowledge.build(chunks)

        self.adviser_mind = str(
            adviser_mind
        ).strip()

        self.has_knowledge = True

        # New knowledge starts a fresh
        # conversational context.
        self.conversation = []


    def search(
        self,
        message,
        top_k=4
    ):
        if not self.has_knowledge:
            return []

        return self.knowledge.search(
            message,
            top_k=top_k
        )


    def clear_conversation(self):
        self.conversation = []
