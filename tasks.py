import json
import os

TASKS_FILE = "tasks.json"


class Task:
    def __init__(self, title, done=False):
        self.title = title
        self.done = done

    def to_dict(self):
        return {"title": self.title, "done": self.done}

    @classmethod
    def from_dict(cls, data):
        return cls(title=data["title"], done=data.get("done", False))

    def __repr__(self):
        status = "[x]" if self.done else "[ ]"
        return f"{status} {self.title}"


def save_tasks(tasks, filename=TASKS_FILE):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([t.to_dict() for t in tasks], f, indent=2)
    except OSError as e:
        print(f"Error saving tasks: {e}")


def load_tasks(filename=TASKS_FILE):
    try:
        if not os.path.exists(filename):
            return []
        with open(filename, "r", encoding="utf-8") as f:
            return [Task.from_dict(d) for d in json.load(f)]
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error loading tasks: {e}")
        return []


if __name__ == "__main__":
    tasks = [
        Task("Buy groceries"),
        Task("Finish report", done=True),
        Task("Call mom"),
    ]
    save_tasks(tasks)
    loaded = load_tasks()
    for task in loaded:
        print(task)
