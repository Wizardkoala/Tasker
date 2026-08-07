from datetime import datetime, timedelta
import pickle
import os

class Tasks():
    def __init__(self, db_path="./tasks.pkl"):
        self.db_path = db_path
        if os.path.exists(self.db_path):
            with open(self.db_path, 'rb') as f: # Changed to 'rb' for pickle
                self.db = pickle.load(f)
                self._update_tasks()
        else:
            self.db = {"tasks": []}

        
        self.save()

    def save(self):
        """Added a save method to write changes back to the pickle file."""
        with open(self.db_path, 'wb') as f: # Changed to 'wb' for pickle
            pickle.dump(self.db, f)

    def remove_completed(self):
        self.db["tasks"] = [t for t in self.db["tasks"] if not t.complete]
        self.save()

    def _advance_due(self, task):
        """Advance a recurring task's due date by its repeat interval."""
        value = task.repeat.get("value", 0)
        interval = task.repeat.get("interval", "day")
        if interval == "day":
            task.due += timedelta(days=value)
        elif interval == "week":
            task.due += timedelta(weeks=value)
        elif interval == "month":
            task.due += timedelta(days=value * 30)

    def toggle_task(self, task_id):
        """Toggle a task's completion. Handles recurring tasks and subtasks."""
        task = self.db["tasks"][task_id]
        if task.complete:
            task.complete = False
            for sub in task.subtasks:
                sub.complete = False
        else:
            if task.repeat.get("value", 0) > 0:
                # Recurring: advance due date instead of marking complete
                self._advance_due(task)
                for sub in task.subtasks:
                    sub.complete = False
            else:
                task.complete = True
                task.completed = datetime.now()
                for sub in task.subtasks:
                    sub.complete = True
                    sub.completed = datetime.now()
        self.save()

    def toggle_subtask(self, task_id, sub_idx):
        """Toggle a subtask. Auto-completes parent when all subtasks are done."""
        task = self.db["tasks"][task_id]
        sub = task.subtasks[sub_idx]
        sub.complete = not sub.complete
        if sub.complete:
            sub.completed = datetime.now()

        if task.subtasks and all(s.complete for s in task.subtasks):
            if task.repeat.get("value", 0) > 0:
                self._advance_due(task)
                for s in task.subtasks:
                    s.complete = False
            else:
                task.complete = True
                task.completed = datetime.now()
        elif not sub.complete and task.complete:
            # Unchecking a subtask uncompletes the parent
            task.complete = False

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

                data[prop] = getattr(task, prop)

            updated.append(self.Task(data))

        self.db["tasks"] = updated
            

    class Task():
        version = 0.2

        def __init__(self, data={}):
            today = datetime.now()
            self.complete = data.get("complete", False)
            self.title = data.get("title", "Undefined")
            self.repeat = data.get("repeat", {"value": 0, "interval": "day"})
            # Support both "desc" (stored attr) and "description" (form input)
            self.desc = data.get("desc", data.get("description", "No Description"))
            self.category = data.get("category", "No Category")
            self.priority = int(data.get("priority", 3))

            subtasks_raw = data.get("subtasks", [])
            self.subtasks = [
                s if hasattr(s, 'title') else self.__class__(s)
                for s in subtasks_raw
            ]
            
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

        @property
        def due_status(self):
            if self.complete:
                return "complete"
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            due = self.due.replace(hour=0, minute=0, second=0, microsecond=0)
            delta = (due - today).days
            if delta < 0:
                return "overdue"
            elif delta == 0:
                return "today"
            elif delta <= 3:
                return "soon"
            elif delta <= 7:
                return "upcoming"
            else:
                return "fine"


if __name__ == "__main__":
    t = Tasks()

    print(dir(t.db["tasks"][0]))