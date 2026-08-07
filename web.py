import datetime

from flask import Flask, render_template, request, redirect, url_for
from tasks import Tasks

version = "ALPHA 0.0.1"

app = Flask(__name__)
task_manager = Tasks()

## TODO: Make it so it doest scroll on every update

@app.route('/')
def index():
    # Get the limit from the URL, defaulting to 5
    limit = request.args.get('limit', 5, type=int)
    
    # Grab all tasks with their original indices
    all_tasks = list(enumerate(task_manager.db["tasks"]))
    
    # --- Top Half: Highlighted Priority Tasks ---
    # Filter only incomplete tasks for the top highlight
    pending_tasks = [(i, t) for i, t in all_tasks if not t.complete]
    
    cat_groups = {}
    for i, t in pending_tasks:
        if t.category not in cat_groups:
            cat_groups[t.category] = []
        cat_groups[t.category].append((i, t))
        
    # Sort within each category by priority (assuming 1 is the highest priority)
    for cat in cat_groups:
        cat_groups[cat].sort(key=lambda x: x[1].priority)
        
    top_tasks = []
    pointers = {cat: 0 for cat in cat_groups}
    active_cats = list(cat_groups.keys())
    
    # Round-robin selection: pick #1 from each category, then #2, etc.
    while len(top_tasks) < limit and active_cats:
        for cat in list(active_cats):
            idx = pointers[cat]
            if idx < len(cat_groups[cat]):
                top_tasks.append(cat_groups[cat][idx])
                pointers[cat] += 1
                if len(top_tasks) >= limit:
                    break
            else:
                active_cats.remove(cat)

    # --- Bottom Half: All Tasks in Columns ---
    all_categorized_tasks = {}
    for i, t in all_tasks:
        if t.category not in all_categorized_tasks:
            all_categorized_tasks[t.category] = []
        all_categorized_tasks[t.category].append((i, t))
        
    return render_template(
        'index.html', 
        top_tasks=top_tasks, 
        all_categorized_tasks=all_categorized_tasks,
        limit=limit
    )


@app.route('/add', methods=['POST'])
def add_task():
    data = {
        "title": request.form.get("title"),
        "description": request.form.get("description"),
        "category": request.form.get("category") or "Uncategorized",
        "priority": request.form.get("priority"),
        "due": request.form.get("due")
    }
    
    new_task = task_manager.Task(data)
    task_manager.db["tasks"].append(new_task)
    task_manager.save()
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    if 0 <= task_id < len(task_manager.db["tasks"]):
        task_manager.db["tasks"][task_id].complete = True
        task_manager.db["tasks"][task_id].completed = datetime.datetime.today()
        task_manager.save()
    return redirect(request.referrer or url_for('index'))

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 0 <= task_id < len(task_manager.db["tasks"]):
        task_manager.db["tasks"].pop(task_id)
        task_manager.save()
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)