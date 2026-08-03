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
        # Enumerate gives us the original list index to use for deletion/completion
        for i, task in enumerate(self.db["tasks"]):
            if task.due <= today:
                tasks_due.append((i, task))

        return tasks_due

    class Task():
        def __init__(self, data={}):
            today = datetime.now()
            self.complete = data.get("complete", False)
            self.title = data.get("title", "Undefined")
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