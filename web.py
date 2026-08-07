from flask import Flask, render_template, request, jsonify
from tasks import Tasks

version = "ALPHA 0.0.1"

app = Flask(__name__)
task_manager = Tasks()

def task_to_dict(idx, task):
    return {
        "id": idx,
        "title": task.title,
        "desc": task.desc,
        "category": task.category,
        "priority": task.priority,
        "complete": task.complete,
        "due": task.due.strftime('%b %d, %Y'),
        "due_iso": task.due.strftime('%Y-%m-%d'),
        "completed": task.completed.strftime('%b %d, %Y'),
        "repeat": task.repeat,
        "due_status": task.due_status,
        "subtasks": [
            {"id": i, "title": sub.title, "complete": sub.complete}
            for i, sub in enumerate(task.subtasks)
        ],
    }


def _get_all_categorized():
    result = {}
    for i, t in enumerate(task_manager.db["tasks"]):
        result.setdefault(t.category, []).append(task_to_dict(i, t))
    return result


def _get_top_tasks(limit):
    all_tasks = list(enumerate(task_manager.db["tasks"]))
    pending = [(i, t) for i, t in all_tasks if not t.complete]

    urgency_rank = {"overdue": 0, "today": 1, "soon": 2, "upcoming": 3, "fine": 4}

    # Group by category; sort each category's tasks by (urgency, priority)
    # so that overdue comes before today, today before soon, etc.
    cat_groups = {}
    for i, t in pending:
        cat_groups.setdefault(t.category, []).append((i, t))
    for cat in cat_groups:
        cat_groups[cat].sort(
            key=lambda x: (urgency_rank.get(x[1].due_status, 5), x[1].priority)
        )

    selected, selected_ids = [], set()
    cats = sorted(cat_groups.keys())  # stable ordering across calls

    def pick_pass(urgent_only):
        """
        Round-robin across categories.
        urgent_only=True  → only pick overdue/today tasks this pass.
        urgent_only=False → pick any unselected task.
        Two passes ensures urgent items always appear before non-urgent ones,
        while the round-robin keeps the selection spread across categories.
        """
        any_picked = True
        pointers = {cat: 0 for cat in cats}
        while len(selected) < limit and any_picked:
            any_picked = False
            for cat in cats:
                if len(selected) >= limit:
                    return
                ptr = pointers[cat]
                tasks = cat_groups[cat]
                while ptr < len(tasks):
                    i, t = tasks[ptr]
                    ptr += 1
                    if i in selected_ids:
                        continue
                    if urgent_only and t.due_status not in ("overdue", "today"):
                        # Tasks are sorted by urgency; nothing more urgent remains
                        # in this category — restore pointer and stop for this cat.
                        pointers[cat] = ptr - 1
                        break
                    selected.append((i, t))
                    selected_ids.add(i)
                    pointers[cat] = ptr
                    any_picked = True
                    break
                else:
                    pointers[cat] = ptr

    pick_pass(urgent_only=True)   # fill with overdue/today first, spread across cats
    pick_pass(urgent_only=False)  # fill remaining slots with any task, still round-robin
    return selected



@app.route('/api/top')
def api_top():
    limit = request.args.get('limit', 5, type=int)
    top = _get_top_tasks(limit)
    return jsonify([task_to_dict(i, t) for i, t in top])


@app.route('/')
def index():
    limit = request.args.get('limit', 5, type=int)
    all_tasks = list(enumerate(task_manager.db["tasks"]))

    all_categorized_tasks = {}
    for i, t in all_tasks:
        all_categorized_tasks.setdefault(t.category, []).append((i, t))

    return render_template(
        'index.html',
        top_tasks=_get_top_tasks(limit),
        all_categorized_tasks=all_categorized_tasks,
        limit=limit
    )


@app.route('/edit/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    if 0 <= task_id < len(task_manager.db["tasks"]):
        old = task_manager.db["tasks"][task_id]
        data = {
            "title":       request.form.get("title", old.title),
            "description": request.form.get("description", old.desc),
            "category":    request.form.get("category", old.category),
            "priority":    request.form.get("priority", old.priority),
            "due":         request.form.get("due") or old.due.strftime('%Y-%m-%d'),
            "repeat": {
                "value":    int(request.form.get("repeat_value", 0) or 0),
                "interval": request.form.get("repeat_interval", "day")
            },
            "complete":  old.complete,
            "completed": old.completed,
            "subtasks":  old.subtasks,
        }
        task = task_manager.Task(data)
        task_manager.db["tasks"][task_id] = task
        task_manager.save()
        return jsonify({"ok": True, "task": task_to_dict(task_id, task)})
    return jsonify({"ok": False}), 404


@app.route('/add', methods=['POST'])
def add_task():
    repeat_value = int(request.form.get("repeat_value", 0) or 0)
    data = {
        "title": request.form.get("title"),
        "description": request.form.get("description"),
        "category": request.form.get("category") or "Uncategorized",
        "priority": request.form.get("priority"),
        "due": request.form.get("due"),
        "repeat": {
            "value": repeat_value,
            "interval": request.form.get("repeat_interval", "day")
        }
    }
    
    new_task = task_manager.Task(data)
    task_manager.db["tasks"].append(new_task)
    task_manager.save()
    new_id = len(task_manager.db["tasks"]) - 1
    return jsonify({"ok": True, "task": task_to_dict(new_id, new_task)})

@app.route('/toggle/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    if 0 <= task_id < len(task_manager.db["tasks"]):
        task_manager.toggle_task(task_id)
        task = task_manager.db["tasks"][task_id]
        return jsonify({"ok": True, "task": task_to_dict(task_id, task)})
    return jsonify({"ok": False}), 404

@app.route('/toggle/<int:task_id>/sub/<int:sub_idx>', methods=['POST'])
def toggle_subtask(task_id, sub_idx):
    if 0 <= task_id < len(task_manager.db["tasks"]):
        task = task_manager.db["tasks"][task_id]
        if 0 <= sub_idx < len(task.subtasks):
            task_manager.toggle_subtask(task_id, sub_idx)
            return jsonify({"ok": True, "task": task_to_dict(task_id, task)})
    return jsonify({"ok": False}), 404

@app.route('/add_subtask/<int:task_id>', methods=['POST'])
def add_subtask(task_id):
    if 0 <= task_id < len(task_manager.db["tasks"]):
        parent = task_manager.db["tasks"][task_id]
        data = {
            "title": request.form.get("title"),
            "due": request.form.get("due"),
            "category": parent.category,
        }
        parent.subtasks.append(task_manager.Task(data))
        task_manager.save()
        return jsonify({"ok": True, "task": task_to_dict(task_id, parent)})
    return jsonify({"ok": False}), 404

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 0 <= task_id < len(task_manager.db["tasks"]):
        task_manager.db["tasks"].pop(task_id)
        task_manager.save()
        return jsonify({"ok": True, "all_tasks": _get_all_categorized()})
    return jsonify({"ok": False}), 404


@app.route('/clear_completed', methods=['POST'])
def clear_completed():
    task_manager.remove_completed()
    limit = request.args.get('limit', 5, type=int)
    top = _get_top_tasks(limit)
    return jsonify({
        "ok": True,
        "all_tasks": _get_all_categorized(),
        "top_tasks": [task_to_dict(i, t) for i, t in top]
    })

if __name__ == '__main__':
    app.run(debug=True, host="10.0.0.164", port=80)