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
        "completed": task.completed.strftime('%b %d, %Y'),
        "repeat": task.repeat,
        "subtasks": [
            {"id": i, "title": sub.title, "complete": sub.complete}
            for i, sub in enumerate(task.subtasks)
        ],
    }


def _get_top_tasks(limit):
    all_tasks = list(enumerate(task_manager.db["tasks"]))
    pending = [(i, t) for i, t in all_tasks if not t.complete]

    cat_groups = {}
    for i, t in pending:
        cat_groups.setdefault(t.category, []).append((i, t))
    for cat in cat_groups:
        cat_groups[cat].sort(key=lambda x: x[1].priority)

    top, pointers = [], {cat: 0 for cat in cat_groups}
    active = list(cat_groups.keys())
    while len(top) < limit and active:
        for cat in list(active):
            idx = pointers[cat]
            if idx < len(cat_groups[cat]):
                top.append(cat_groups[cat][idx])
                pointers[cat] += 1
                if len(top) >= limit:
                    break
            else:
                active.remove(cat)
    return top


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
        return jsonify({"ok": True, "deleted_id": task_id})
    return jsonify({"ok": False}), 404

if __name__ == '__main__':
    app.run(debug=True)