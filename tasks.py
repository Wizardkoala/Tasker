from datetime import datetime, timedelta
import pickle
import os

class Tasks():
    def __init__(self, db_path="./tasks.pkl"):
        self.db_path = db_path
        if os.path.exists(self.db_path):
            with open(self.db_path, 'rb') as f: # Changed to 'rb' for pickle
                self.db = pickle.load(f)
        else:
            self.db = {"tasks": []}

        self._update_tasks()
        self.save()

    def save(self):
        """Added a save method to write changes back to the pickle file."""
        with open(self.db_path, 'wb') as f: # Changed to 'wb' for pickle
            pickle.dump(self.db, f)

    def remove_completed(self):
        for task in self.db["tasks"]:
            if task.complete:
                self.db["tasks"].remove(task)

        self.save()

    def get_due(self):
        tasks_due = []
        today = datetime.now() 

        for i, task in enumerate(self.db["tasks"]):
            if task.due <= today:
                tasks_due.append((i, task))

        return tasks_due

    def _update_tasks(self):
        updated = []
        for task in self.db["tasks"]:
            properties = dir(task)
            data = {}

            # Remove all the python added properties
            for prop in properties:
                if prop.startswith("__"):
                    continue

                data[prop] = task[prop]

            updated.append(task)

        self.db["task"] = updated
            

    class Task():
        version = 0.1

        def __init__(self, data={}):
            today = datetime.now()
            self.complete = data.get("complete", False)
            self.title = data.get("title", "Undefined")
            self.repeat = data.get("repeat", {"value": 0, "interval": "day"})
            self.desc = data.get("description", "No Description")
            self.category = data.get("category", "No Category")
            self.priority = int(data.get("priority", 3))
            
            # Allow HTML date inputs to be parsed into datetime objects
            due_raw = data.get("due", today)
            if isinstance(due_raw, str) and due_raw:
                try:
                    self.due = datetime.strptime(due_raw, '%Y-%m-%d')
                except ValueError:
                    self.due = today + timedelta(days=30)
            elif isinstance(due_raw, datetime):
                self.due = due_raw
            else:
                self.due = today + timedelta(days=30)

            completed_raw = data.get("completed", today)
            if isinstance(completed_raw, str) and completed_raw:
                try:
                    self.completed = datetime.strptime(completed_raw, '%Y-%m-%d')
                except ValueError:
                    self.completed = today + timedelta(days=30)
            elif isinstance(completed_raw, datetime):
                self.completed = completed_raw
            else:
                self.completed = today + timedelta(days=30)


if __name__ == "__main__":
    t = Tasks()

    print(dir(t.db["tasks"][0]))