#!/usr/bin/env python3
"""
Task Tracker CLI

A simple command-line task tracker that stores tasks in a JSON file
in the current directory. Uses only the Python standard library.

Usage:
    python task_cli.py add "Task description"
    python task_cli.py update <id> "New description"
    python task_cli.py delete <id>
    python task_cli.py mark-in-progress <id>
    python task_cli.py mark-done <id>
    python task_cli.py list
    python task_cli.py list done
    python task_cli.py list todo
    python task_cli.py list in-progress
"""

import json
import os
import sys
from datetime import datetime, timezone

TASKS_FILE = "tasks.json"

VALID_STATUSES = ("todo", "in-progress", "done")


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def load_tasks():
    """Load tasks from the JSON file. Create the file if it doesn't exist.
    Handles a missing, empty, or corrupted file gracefully.
    """
    if not os.path.exists(TASKS_FILE):
        save_tasks([])
        return []

    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            if not isinstance(data, list):
                raise ValueError("Tasks file does not contain a list of tasks.")
            return data
    except json.JSONDecodeError:
        print(f"Error: '{TASKS_FILE}' is not valid JSON. "
              "Please fix or remove the file and try again.")
        sys.exit(1)
    except OSError as e:
        print(f"Error reading '{TASKS_FILE}': {e}")
        sys.exit(1)


def save_tasks(tasks):
    """Write the list of tasks to the JSON file."""
    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)
    except OSError as e:
        print(f"Error writing '{TASKS_FILE}': {e}")
        sys.exit(1)


def next_id(tasks):
    """Return the next available integer id."""
    if not tasks:
        return 1
    return max(task["id"] for task in tasks) + 1


def now_iso():
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def find_task(tasks, task_id):
    """Return the task dict with the given id, or None."""
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


def parse_id(raw_id):
    """Convert a CLI argument to an integer id, exiting with a clear
    error message if it isn't a valid integer."""
    try:
        return int(raw_id)
    except ValueError:
        print(f"Error: '{raw_id}' is not a valid task id (expected a number).")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_add(args):
    if len(args) != 1:
        print("Usage: task_cli.py add \"Task description\"")
        sys.exit(1)

    description = args[0].strip()
    if not description:
        print("Error: Task description cannot be empty.")
        sys.exit(1)

    tasks = load_tasks()
    task_id = next_id(tasks)
    timestamp = now_iso()

    task = {
        "id": task_id,
        "description": description,
        "status": "todo",
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"Task added successfully (ID: {task_id})")


def cmd_update(args):
    if len(args) != 2:
        print("Usage: task_cli.py update <id> \"New description\"")
        sys.exit(1)

    task_id = parse_id(args[0])
    new_description = args[1].strip()
    if not new_description:
        print("Error: Task description cannot be empty.")
        sys.exit(1)

    tasks = load_tasks()
    task = find_task(tasks, task_id)
    if task is None:
        print(f"Error: No task found with ID {task_id}.")
        sys.exit(1)

    task["description"] = new_description
    task["updatedAt"] = now_iso()
    save_tasks(tasks)
    print(f"Task {task_id} updated successfully.")


def cmd_delete(args):
    if len(args) != 1:
        print("Usage: task_cli.py delete <id>")
        sys.exit(1)

    task_id = parse_id(args[0])
    tasks = load_tasks()
    task = find_task(tasks, task_id)
    if task is None:
        print(f"Error: No task found with ID {task_id}.")
        sys.exit(1)

    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    print(f"Task {task_id} deleted successfully.")


def _mark_status(args, status, command_name):
    if len(args) != 1:
        print(f"Usage: task_cli.py {command_name} <id>")
        sys.exit(1)

    task_id = parse_id(args[0])
    tasks = load_tasks()
    task = find_task(tasks, task_id)
    if task is None:
        print(f"Error: No task found with ID {task_id}.")
        sys.exit(1)

    task["status"] = status
    task["updatedAt"] = now_iso()
    save_tasks(tasks)
    print(f"Task {task_id} marked as {status}.")


def cmd_mark_in_progress(args):
    _mark_status(args, "in-progress", "mark-in-progress")


def cmd_mark_done(args):
    _mark_status(args, "done", "mark-done")


def _print_tasks(tasks):
    if not tasks:
        print("No tasks found.")
        return

    for task in sorted(tasks, key=lambda t: t["id"]):
        print(
            f"[{task['id']}] ({task['status']}) {task['description']}\n"
            f"    created: {task['createdAt']}  updated: {task['updatedAt']}"
        )


def cmd_list(args):
    if len(args) > 1:
        print("Usage: task_cli.py list [done|todo|in-progress]")
        sys.exit(1)

    tasks = load_tasks()

    if len(args) == 0:
        _print_tasks(tasks)
        return

    status_filter = args[0]
    if status_filter not in VALID_STATUSES:
        print(f"Error: '{status_filter}' is not a valid status. "
              f"Choose from: {', '.join(VALID_STATUSES)}.")
        sys.exit(1)

    filtered = [t for t in tasks if t["status"] == status_filter]
    _print_tasks(filtered)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

COMMANDS = {
    "add": cmd_add,
    "update": cmd_update,
    "delete": cmd_delete,
    "mark-in-progress": cmd_mark_in_progress,
    "mark-done": cmd_mark_done,
    "list": cmd_list,
}


def print_usage():
    print(__doc__)


def main():
    argv = sys.argv[1:]

    if not argv:
        print_usage()
        sys.exit(1)

    command, rest = argv[0], argv[1:]

    handler = COMMANDS.get(command)
    if handler is None:
        print(f"Error: Unknown command '{command}'.")
        print_usage()
        sys.exit(1)

    handler(rest)


if __name__ == "__main__":
    main()
