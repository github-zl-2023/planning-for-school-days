import json
import os
import uuid
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox

TASKS_FILE = "tasks.json"
DATE_FORMAT = "%Y-%m-%d %H:%M"
REMIND_OPTIONS = [0, 5, 10, 15, 30, 60]


class PlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Desktop Planner")
        self.root.geometry("900x500")
        self.root.configure(padx=16, pady=16)

        self.font_large = ("Helvetica", 14)
        self.font_button = ("Helvetica", 13, "bold")

        self.tasks = []
        self.load_tasks()

        self.build_ui()
        self.refresh_task_list()
        self.schedule_reminder_check()

    def build_ui(self):
        header = tk.Label(
            self.root,
            text="My Planner",
            font=("Helvetica", 20, "bold"),
        )
        header.pack(pady=(0, 12))

        columns = ("due", "name", "status")
        self.tree = ttk.Treeview(
            self.root,
            columns=columns,
            show="headings",
            height=12,
        )
        self.tree.heading("due", text="Due Time")
        self.tree.heading("name", text="Task Name")
        self.tree.heading("status", text="Status")
        self.tree.column("due", width=200, anchor=tk.W)
        self.tree.column("name", width=420, anchor=tk.W)
        self.tree.column("status", width=120, anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        style = ttk.Style(self.root)
        style.configure("Treeview", font=self.font_large, rowheight=28)
        style.configure("Treeview.Heading", font=self.font_large)

        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X)

        btn_add = tk.Button(
            button_frame,
            text="Add Task",
            font=self.font_button,
            width=12,
            command=self.open_add_dialog,
        )
        btn_add.pack(side=tk.LEFT, padx=4, pady=4)

        btn_edit = tk.Button(
            button_frame,
            text="Edit",
            font=self.font_button,
            width=10,
            command=self.open_edit_dialog,
        )
        btn_edit.pack(side=tk.LEFT, padx=4, pady=4)

        btn_done = tk.Button(
            button_frame,
            text="Mark Done",
            font=self.font_button,
            width=12,
            command=self.mark_done,
        )
        btn_done.pack(side=tk.LEFT, padx=4, pady=4)

        btn_delete = tk.Button(
            button_frame,
            text="Delete",
            font=self.font_button,
            width=10,
            command=self.delete_task,
        )
        btn_delete.pack(side=tk.LEFT, padx=4, pady=4)

    def load_tasks(self):
        if not os.path.exists(TASKS_FILE):
            self.tasks = []
            self.save_tasks()
            return
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as file:
                self.tasks = json.load(file)
        except (json.JSONDecodeError, OSError):
            messagebox.showwarning(
                "Tasks file issue",
                "We couldn't read tasks.json, so we're starting fresh.",
            )
            self.tasks = []
            self.save_tasks()

    def save_tasks(self):
        with open(TASKS_FILE, "w", encoding="utf-8") as file:
            json.dump(self.tasks, file, indent=2)

    def refresh_task_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        def sort_key(task):
            status_order = 0 if task.get("status") == "Open" else 1
            due = self.parse_datetime(task.get("due")) or datetime.max
            return (status_order, due)

        for task in sorted(self.tasks, key=sort_key):
            self.tree.insert(
                "",
                tk.END,
                iid=task["id"],
                values=(task.get("due"), task.get("name"), task.get("status")),
            )

    def open_add_dialog(self):
        TaskDialog(self.root, title="Add Task", on_save=self.add_task)

    def open_edit_dialog(self):
        task = self.get_selected_task()
        if not task:
            messagebox.showinfo("Choose a task", "Please select a task to edit.")
            return
        TaskDialog(self.root, title="Edit Task", task=task, on_save=self.edit_task)

    def add_task(self, data):
        data["id"] = str(uuid.uuid4())
        data["status"] = "Open"
        data["notified"] = False
        self.tasks.append(data)
        self.save_tasks()
        self.refresh_task_list()

    def edit_task(self, data):
        for task in self.tasks:
            if task["id"] == data["id"]:
                task.update(
                    {
                        "name": data["name"],
                        "due": data["due"],
                        "remind": data["remind"],
                        "notified": False,
                    }
                )
                break
        self.save_tasks()
        self.refresh_task_list()

    def mark_done(self):
        task = self.get_selected_task()
        if not task:
            messagebox.showinfo("Choose a task", "Please select a task to mark done.")
            return
        task["status"] = "Done"
        self.save_tasks()
        self.refresh_task_list()

    def delete_task(self):
        task = self.get_selected_task()
        if not task:
            messagebox.showinfo("Choose a task", "Please select a task to delete.")
            return
        confirm = messagebox.askyesno(
            "Delete task", "Are you sure you want to delete this task?"
        )
        if not confirm:
            return
        self.tasks = [t for t in self.tasks if t["id"] != task["id"]]
        self.save_tasks()
        self.refresh_task_list()

    def get_selected_task(self):
        selection = self.tree.selection()
        if not selection:
            return None
        task_id = selection[0]
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None

    def parse_datetime(self, value):
        if not value:
            return None
        try:
            return datetime.strptime(value, DATE_FORMAT)
        except ValueError:
            return None

    def schedule_reminder_check(self):
        self.check_reminders()
        self.root.after(30000, self.schedule_reminder_check)

    def check_reminders(self):
        now = datetime.now()
        updated = False
        for task in self.tasks:
            if task.get("status") != "Open" or task.get("notified"):
                continue
            due = self.parse_datetime(task.get("due"))
            if not due:
                continue
            remind_minutes = int(task.get("remind", 0))
            remind_time = due - timedelta(minutes=remind_minutes)
            if now >= remind_time:
                self.send_reminder(task)
                task["notified"] = True
                updated = True
        if updated:
            self.save_tasks()
            self.refresh_task_list()

    def send_reminder(self, task):
        title = "Planner Reminder"
        message = f"{task.get('name')} is due at {task.get('due')}"
        try:
            from plyer import notification

            notification.notify(
                title=title,
                message=message,
                timeout=10,
            )
        except Exception:
            messagebox.showinfo(title, message)


class TaskDialog:
    def __init__(self, parent, title, on_save, task=None):
        self.parent = parent
        self.on_save = on_save
        self.task = task

        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("450x260")
        self.window.transient(parent)
        self.window.grab_set()

        font_label = ("Helvetica", 12, "bold")
        font_entry = ("Helvetica", 12)

        tk.Label(self.window, text="Task Name", font=font_label).pack(anchor=tk.W, pady=4)
        self.entry_name = tk.Entry(self.window, font=font_entry)
        self.entry_name.pack(fill=tk.X, pady=2)

        tk.Label(self.window, text="Due (YYYY-MM-DD HH:MM)", font=font_label).pack(
            anchor=tk.W, pady=4
        )
        self.entry_due = tk.Entry(self.window, font=font_entry)
        self.entry_due.pack(fill=tk.X, pady=2)

        tk.Label(self.window, text="Remind minutes before", font=font_label).pack(
            anchor=tk.W, pady=4
        )
        self.remind_var = tk.StringVar()
        remind_menu = ttk.Combobox(
            self.window,
            textvariable=self.remind_var,
            values=[str(option) for option in REMIND_OPTIONS],
            state="readonly",
            font=font_entry,
        )
        remind_menu.pack(fill=tk.X, pady=2)

        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=12)

        btn_save = tk.Button(
            btn_frame,
            text="Save",
            font=("Helvetica", 12, "bold"),
            width=10,
            command=self.save,
        )
        btn_save.pack(side=tk.LEFT, padx=6)

        btn_cancel = tk.Button(
            btn_frame,
            text="Cancel",
            font=("Helvetica", 12, "bold"),
            width=10,
            command=self.window.destroy,
        )
        btn_cancel.pack(side=tk.LEFT, padx=6)

        if task:
            self.entry_name.insert(0, task.get("name", ""))
            self.entry_due.insert(0, task.get("due", ""))
            self.remind_var.set(str(task.get("remind", REMIND_OPTIONS[0])))
        else:
            self.remind_var.set(str(REMIND_OPTIONS[1]))

    def save(self):
        name = self.entry_name.get().strip()
        due = self.entry_due.get().strip()
        remind = self.remind_var.get()

        if not name:
            messagebox.showerror("Missing name", "Please enter a task name.")
            return

        try:
            datetime.strptime(due, DATE_FORMAT)
        except ValueError:
            messagebox.showerror(
                "Date format", "Please use the format YYYY-MM-DD HH:MM."
            )
            return

        if remind not in [str(option) for option in REMIND_OPTIONS]:
            messagebox.showerror(
                "Remind minutes", "Please choose a reminder time from the list."
            )
            return

        data = {
            "id": self.task["id"] if self.task else None,
            "name": name,
            "due": due,
            "remind": int(remind),
        }
        self.on_save(data)
        self.window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PlannerApp(root)
    root.mainloop()
