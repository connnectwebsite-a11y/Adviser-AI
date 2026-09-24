class AdviserMemory:
    def __init__(self):
        self.memories = []


    def add(self, memory):
        memory = str(memory).strip()

        if (
            memory
            and memory not in self.memories
        ):
            self.memories.append(memory)


    def get(self):
        return list(self.memories)


    def as_text(self):
        if not self.memories:
            return "No saved user memories."

        return "\n".join(
            f"- {memory}"
            for memory in self.memories
        )


    def clear(self):
        self.memories = []


    def replace(
        self,
        old_memory,
        new_memory
    ):
        old_memory = str(old_memory).strip()
        new_memory = str(new_memory).strip()

        try:
            index = self.memories.index(
                old_memory
            )

        except ValueError:
            if new_memory:
                self.add(new_memory)
            return

        if new_memory:
            self.memories[index] = new_memory
        else:
            self.memories.pop(index)


    def remove(self, memory):
        memory = str(memory).strip()

        try:
            self.memories.remove(memory)
            return True

        except ValueError:
            return False
