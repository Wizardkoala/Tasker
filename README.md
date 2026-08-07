# Tasker

Tasker is a simple Flask-based task manager for organizing tasks by category, priority, and due date.

## Features

- Add tasks with a title, description, category, priority, and due date
- Mark tasks as complete
- Delete tasks
- View tasks grouped by category
- Highlight a selection of top-priority pending tasks

## Project Structure

- `web.py` – Flask routes and app setup
- `tasks.py` – task storage and task model logic
- `templates/index.html` – dashboard UI
- `static/css/style.css` – styling for the app

## Running the App

1. Activate the virtual environment:
   ```bash
   source bin/activate
   ```
2. Start the Flask app:
   ```bash
   python web.py
   ```
3. Open the app in your browser at:
   ```text
   http://127.0.0.1:5000/
   ```

## Upcoming Features

- Completion history and completion dates
- Better task filtering and sorting
- Drag-and-drop task organization
- Persistent reminders and notifications
- Dark mode UI
- Search and tag-based task organization
- All the issues marked ```development``` on Github
