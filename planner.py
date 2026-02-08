import calendar
import json
import os
import uuid
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox

TASKS_FILE = "tasks.json"
DATE_FORMAT = "%Y-%m-%d %H:%M"
REMIND_OPTIONS = [0, 5, 10, 15, 30, 60]
CATEGORIES = ["School", "Home", "Activities"]
CATEGORY_COLORS = {
    "School": "#4A90E2",
    "Home": "#50B27D",
    "Activities": "#F5A623",
}


class PlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kid Planner")
        self.root.geometry("1100x700")
        self.root.configure(bg="#F6F7FB")
        self.root.minsize(980, 640)

        self.font_title = ("Helvetica", 20, "bold")
        self.font_large = ("Helvetica", 14, "bold")
        self.font_body = ("Helvetica", 12)
        self.font_button = ("Helvetica", 12, "bold")

        self.tasks = []
        self.selected_task_id = None
        self.active_filter = "Today"
        self.active_category = "All"

        self.load_tasks()

        self.build_ui()
        self.refresh_task_list()
        self.schedule_reminder_check()

        self.root.bind("<Delete>", lambda event: self.delete_task())

    def build_ui(self):
        main_frame = tk.Frame(self.root, bg="#F6F7FB")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        sidebar = tk.Frame(main_frame, bg="#2D2F6F", width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 16))
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="Kid Planner",
            bg="#2D2F6F",
            fg="white",
            font=("Helvetica", 18, "bold"),
        ).pack(pady=(20, 12), padx=12, anchor=tk.W)

        tk.Label(
            sidebar,
            text="FILTERS",
            bg="#2D2F6F",
            fg="#B8B9E0",
            font=("Helvetica", 10, "bold"),
        ).pack(pady=(12, 6), padx=12, anchor=tk.W)

        for label in ["Today", "This Week", "All", "Done"]:
            self.create_sidebar_button(sidebar, label, self.set_filter)

        tk.Label(
            sidebar,
            text="CATEGORIES",
            bg="#2D2F6F",
            fg="#B8B9E0",
            font=("Helvetica", 10, "bold"),
        ).pack(pady=(20, 6), padx=12, anchor=tk.W)

        for category in CATEGORIES:
            self.create_sidebar_button(sidebar, category, self.set_category)

        content = tk.Frame(main_frame, bg="#F6F7FB")
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        header = tk.Frame(content, bg="#F6F7FB")
        header.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            header,
            text="Hello! Let's plan your day",
            bg="#F6F7FB",
            fg="#2E2E4F",
            font=self.font_title,
        ).pack(side=tk.LEFT)

        add_button = tk.Button(
            header,
            text="➕ Add Task",
            font=("Helvetica", 14, "bold"),
            bg="#FF7A59",
            fg="white",
            activebackground="#FF9A7A",
            padx=18,
            pady=8,
            relief=tk.FLAT,
            command=self.open_add_dialog,
        )
        add_button.pack(side=tk.RIGHT)

        top_section = tk.Frame(content, bg="#F6F7FB")
        top_section.pack(fill=tk.X, pady=(0, 16))

        tk.Label(
            top_section,
            text="Top 3 Today",
            bg="#F6F7FB",
            fg="#2E2E4F",
            font=self.font_large,
        ).pack(anchor=tk.W, pady=(0, 8))

        self.top_cards_frame = tk.Frame(top_section, bg="#F6F7FB")
        self.top_cards_frame.pack(fill=tk.X)

        list_header = tk.Frame(content, bg="#F6F7FB")
        list_header.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            list_header,
            text="Your Tasks",
            bg="#F6F7FB",
            fg="#2E2E4F",
            font=self.font_large,
        ).pack(side=tk.LEFT)

        actions = tk.Frame(list_header, bg="#F6F7FB")
        actions.pack(side=tk.RIGHT)

        tk.Button(
            actions,
            text="✏️ Edit",
            font=self.font_button,
            bg="#FFFFFF",
            fg="#2E2E4F",
            relief=tk.FLAT,
            command=self.open_edit_dialog,
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            actions,
            text="✅ Done",
            font=self.font_button,
            bg="#FFFFFF",
            fg="#2E2E4F",
            relief=tk.FLAT,
            command=self.mark_done,
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            actions,
            text="🗑 Delete",
            font=self.font_button,
            bg="#FFFFFF",
            fg="#2E2E4F",
            relief=tk.FLAT,
            command=self.delete_task,
        ).pack(side=tk.LEFT, padx=4)

        list_container = tk.Frame(content, bg="#F6F7FB")
        list_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(list_container, bg="#F6F7FB", highlightthickness=0)
        scrollbar = tk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.cards_frame = tk.Frame(self.canvas, bg="#F6F7FB")

        self.cards_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_sidebar_button(self, parent, label, callback):
        btn = tk.Button(
            parent,
            text=label,
            font=("Helvetica", 12, "bold"),
            bg="#3E4190",
            fg="white",
            activebackground="#5255A6",
            relief=tk.FLAT,
            command=lambda value=label: callback(value),
            padx=12,
            pady=8,
        )
        btn.pack(fill=tk.X, padx=12, pady=4)

    def load_tasks(self):
        if not os.path.exists(TASKS_FILE):
            self.tasks = []
            self.save_tasks()
            return
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as file:
                self.tasks = json.load(file)
            for task in self.tasks:
                task.setdefault("status", "Open")
                task.setdefault("category", "School")
                task.setdefault("notified", False)
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

    def set_filter(self, label):
        self.active_filter = label
        self.refresh_task_list()

    def set_category(self, label):
        self.active_category = label if self.active_category != label else "All"
        self.refresh_task_list()

    def get_filtered_tasks(self):
        now = datetime.now()
        today = now.date()
        week_end = today + timedelta(days=7)

        def in_filter(task):
            status = task.get("status")
            due = self.parse_datetime(task.get("due"))

            if self.active_filter == "Done":
                return status == "Done"
            if status == "Done":
                return False
            if self.active_filter == "All":
                return True
            if not due:
                return False
            if self.active_filter == "Today":
                return due.date() == today
            if self.active_filter == "This Week":
                return today <= due.date() <= week_end
            return True

        def in_category(task):
            if self.active_category == "All":
                return True
            return task.get("category") == self.active_category

        filtered = [task for task in self.tasks if in_filter(task) and in_category(task)]

        def sort_key(task):
            status_order = 0 if task.get("status") == "Open" else 1
            due = self.parse_datetime(task.get("due")) or datetime.max
            return (status_order, due)

        return sorted(filtered, key=sort_key)

    def refresh_task_list(self):
        for widget in self.top_cards_frame.winfo_children():
            widget.destroy()
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        top_tasks = self.get_top_today_tasks()
        if not top_tasks:
            self.create_empty_card(self.top_cards_frame, "No tasks due today yet!")
        else:
            for task in top_tasks:
                self.create_task_card(self.top_cards_frame, task, compact=True)

        tasks = self.get_filtered_tasks()
        if not tasks:
            self.create_empty_card(self.cards_frame, "No tasks to show. Add one!")
        else:
            for task in tasks:
                self.create_task_card(self.cards_frame, task)

    def get_top_today_tasks(self):
        today = datetime.now().date()
        open_tasks = [
            task
            for task in self.tasks
            if task.get("status") == "Open"
            and (self.parse_datetime(task.get("due")) or datetime.max).date() == today
        ]
        open_tasks.sort(key=lambda t: self.parse_datetime(t.get("due")) or datetime.max)
        return open_tasks[:3]

    def create_empty_card(self, parent, text):
        card = tk.Frame(parent, bg="#FFFFFF", bd=0, relief=tk.FLAT)
        card.pack(fill=tk.X, pady=8)
        tk.Label(
            card,
            text=text,
            bg="#FFFFFF",
            fg="#7A7B9A",
            font=self.font_body,
            padx=16,
            pady=16,
        ).pack(anchor=tk.W)

    def create_task_card(self, parent, task, compact=False):
        shadow = tk.Frame(parent, bg="#E2E3EC")
        shadow.pack(fill=tk.X, pady=8, padx=6)

        card = tk.Frame(
            shadow,
            bg="#FFFFFF",
            highlightthickness=2,
            highlightbackground="#FFFFFF",
            padx=16,
            pady=12 if compact else 16,
        )
        card.pack(fill=tk.X)

        if self.selected_task_id == task.get("id"):
            card.configure(highlightbackground="#7B6CFF")

        card.bind("<Button-1>", lambda event, t=task: self.select_task(t))

        header = tk.Frame(card, bg="#FFFFFF")
        header.pack(fill=tk.X)

        title = tk.Label(
            header,
            text=task.get("name"),
            bg="#FFFFFF",
            fg="#2E2E4F",
            font=self.font_large,
        )
        title.pack(side=tk.LEFT, anchor=tk.W)
        title.bind("<Button-1>", lambda event, t=task: self.select_task(t))

        status = task.get("status", "Open")
        status_color = "#A6E3A1" if status == "Done" else "#FFD3B6"
        status_text = "Done" if status == "Done" else "Open"
        status_label = tk.Label(
            header,
            text=status_text,
            bg=status_color,
            fg="#2E2E4F",
            font=("Helvetica", 10, "bold"),
            padx=10,
            pady=4,
        )
        status_label.pack(side=tk.RIGHT)

        meta = tk.Frame(card, bg="#FFFFFF")
        meta.pack(fill=tk.X, pady=(8, 0))

        due_label = tk.Label(
            meta,
            text=f"Due: {task.get('due')}",
            bg="#FFFFFF",
            fg="#6A6B89",
            font=self.font_body,
        )
        due_label.pack(side=tk.LEFT)

        category = task.get("category", "School")
        tag_color = CATEGORY_COLORS.get(category, "#4A90E2")
        category_label = tk.Label(
            meta,
            text=category,
            bg=tag_color,
            fg="white",
            font=("Helvetica", 10, "bold"),
            padx=10,
            pady=4,
        )
        category_label.pack(side=tk.RIGHT)

    def select_task(self, task):
        self.selected_task_id = task.get("id")
        self.refresh_task_list()

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
                        "category": data["category"],
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
        self.selected_task_id = None
        self.save_tasks()
        self.refresh_task_list()

    def get_selected_task(self):
        if not self.selected_task_id:
            return None
        for task in self.tasks:
            if task["id"] == self.selected_task_id:
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
        self.window.geometry("480x420")
        self.window.configure(bg="#F6F7FB")
        self.window.transient(parent)
        self.window.grab_set()

        font_label = ("Helvetica", 11, "bold")
        font_entry = ("Helvetica", 12)

        self.container = tk.Frame(self.window, bg="#F6F7FB")
        self.container.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        tk.Label(
            self.container,
            text="Task Name",
            font=font_label,
            bg="#F6F7FB",
            fg="#2E2E4F",
        ).pack(anchor=tk.W, pady=(0, 4))
        self.entry_name = tk.Entry(self.container, font=font_entry)
        self.entry_name.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            self.container,
            text="Category",
            font=font_label,
            bg="#F6F7FB",
            fg="#2E2E4F",
        ).pack(anchor=tk.W, pady=(0, 4))
        self.category_var = tk.StringVar()
        category_menu = ttk.Combobox(
            self.container,
            textvariable=self.category_var,
            values=CATEGORIES,
            state="readonly",
            font=font_entry,
        )
        category_menu.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            self.container,
            text="Due Date",
            font=font_label,
            bg="#F6F7FB",
            fg="#2E2E4F",
        ).pack(anchor=tk.W, pady=(0, 4))
        date_frame = tk.Frame(self.container, bg="#F6F7FB")
        date_frame.pack(fill=tk.X, pady=(0, 10))
        self.entry_date = tk.Entry(date_frame, font=font_entry)
        self.entry_date.pack(side=tk.LEFT, fill=tk.X, expand=True)
        btn_calendar = tk.Button(
            date_frame,
            text="📅 Pick",
            font=font_entry,
            bg="#FFFFFF",
            relief=tk.FLAT,
            command=self.open_calendar,
        )
        btn_calendar.pack(side=tk.LEFT, padx=6)

        tk.Label(
            self.container,
            text="Due Time (HH:MM)",
            font=font_label,
            bg="#F6F7FB",
            fg="#2E2E4F",
        ).pack(anchor=tk.W, pady=(0, 4))
        self.entry_time = tk.Entry(self.container, font=font_entry)
        self.entry_time.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            self.container,
            text="Remind minutes before",
            font=font_label,
            bg="#F6F7FB",
            fg="#2E2E4F",
        ).pack(anchor=tk.W, pady=(0, 4))
        self.remind_var = tk.StringVar()
        remind_menu = ttk.Combobox(
            self.container,
            textvariable=self.remind_var,
            values=[str(option) for option in REMIND_OPTIONS],
            state="readonly",
            font=font_entry,
        )
        remind_menu.pack(fill=tk.X, pady=(0, 16))

        tk.Label(
            self.container,
            text="Example: 2024-12-05 at 15:30",
            font=("Helvetica", 10),
            bg="#F6F7FB",
            fg="#7A7B9A",
        ).pack(anchor=tk.W, pady=(0, 12))

        btn_frame = tk.Frame(self.container, bg="#F6F7FB")
        btn_frame.pack(pady=6)

        btn_save = tk.Button(
            btn_frame,
            text="Save",
            font=("Helvetica", 12, "bold"),
            width=10,
            bg="#7B6CFF",
            fg="white",
            relief=tk.FLAT,
            command=self.save,
        )
        btn_save.pack(side=tk.LEFT, padx=6)

        btn_cancel = tk.Button(
            btn_frame,
            text="Cancel",
            font=("Helvetica", 12, "bold"),
            width=10,
            bg="#FFFFFF",
            relief=tk.FLAT,
            command=self.window.destroy,
        )
        btn_cancel.pack(side=tk.LEFT, padx=6)

        self.window.bind("<Return>", lambda event: self.save())

        if task:
            self.entry_name.insert(0, task.get("name", ""))
            due_value = task.get("due", "")
            if due_value:
                try:
                    parsed_due = datetime.strptime(due_value, DATE_FORMAT)
                    self.entry_date.insert(0, parsed_due.strftime("%Y-%m-%d"))
                    self.entry_time.insert(0, parsed_due.strftime("%H:%M"))
                except ValueError:
                    self.entry_date.insert(0, due_value)
            self.remind_var.set(str(task.get("remind", REMIND_OPTIONS[0])))
            self.category_var.set(task.get("category", CATEGORIES[0]))
        else:
            self.remind_var.set(str(REMIND_OPTIONS[1]))
            self.category_var.set(CATEGORIES[0])

    def save(self):
        name = self.entry_name.get().strip()
        due_date = self.entry_date.get().strip()
        due_time = self.entry_time.get().strip()
        remind = self.remind_var.get()
        category = self.category_var.get()

        if not name:
            messagebox.showerror("Missing name", "Please enter a task name.")
            return

        try:
            datetime.strptime(f"{due_date} {due_time}", DATE_FORMAT)
        except ValueError:
            messagebox.showerror(
                "Date format",
                "Please use date YYYY-MM-DD and time HH:MM (24-hour).",
            )
            return

        if remind not in [str(option) for option in REMIND_OPTIONS]:
            messagebox.showerror(
                "Remind minutes", "Please choose a reminder time from the list."
            )
            return

        if category not in CATEGORIES:
            messagebox.showerror("Category", "Please choose a category.")
            return

        data = {
            "id": self.task["id"] if self.task else None,
            "name": name,
            "due": f"{due_date} {due_time}",
            "remind": int(remind),
            "category": category,
        }
        self.on_save(data)
        self.window.destroy()

    def open_calendar(self):
        CalendarPopup(self.window, self.entry_date)


class CalendarPopup:
    def __init__(self, parent, entry_widget):
        self.entry_widget = entry_widget
        self.window = tk.Toplevel(parent)
        self.window.title("Pick a date")
        self.window.geometry("340x340")
        self.window.configure(bg="#F6F7FB")
        self.window.transient(parent)
        self.window.grab_set()

        self.current_date = datetime.now().date()
        self.display_year = self.current_date.year
        self.display_month = self.current_date.month

        header = tk.Frame(self.window, bg="#F6F7FB")
        header.pack(pady=8)

        btn_prev = tk.Button(
            header, text="<", width=3, command=self.prev_month, relief=tk.FLAT
        )
        btn_prev.pack(side=tk.LEFT, padx=4)

        self.label_month = tk.Label(
            header, font=("Helvetica", 12, "bold"), bg="#F6F7FB"
        )
        self.label_month.pack(side=tk.LEFT, padx=8)

        btn_next = tk.Button(
            header, text=">", width=3, command=self.next_month, relief=tk.FLAT
        )
        btn_next.pack(side=tk.LEFT, padx=4)

        self.calendar_frame = tk.Frame(self.window, bg="#F6F7FB")
        self.calendar_frame.pack(pady=8)

        self.draw_calendar()

    def draw_calendar(self):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        month_name = datetime(self.display_year, self.display_month, 1).strftime(
            "%B %Y"
        )
        self.label_month.config(text=month_name)

        days_header = tk.Frame(self.calendar_frame, bg="#F6F7FB")
        days_header.pack()
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            tk.Label(days_header, text=day, width=4, bg="#F6F7FB").pack(side=tk.LEFT)

        weeks = calendar.monthcalendar(self.display_year, self.display_month)
        for week in weeks:
            row = tk.Frame(self.calendar_frame, bg="#F6F7FB")
            row.pack()
            for day in week:
                if day == 0:
                    tk.Label(row, text="", width=4, bg="#F6F7FB").pack(side=tk.LEFT)
                else:
                    btn = tk.Button(
                        row,
                        text=str(day),
                        width=4,
                        relief=tk.FLAT,
                        bg="#FFFFFF",
                        command=lambda d=day: self.select_date(d),
                    )
                    btn.pack(side=tk.LEFT, padx=1, pady=1)

    def select_date(self, day):
        selected = datetime(self.display_year, self.display_month, day).strftime(
            "%Y-%m-%d"
        )
        self.entry_widget.delete(0, tk.END)
        self.entry_widget.insert(0, selected)
        self.window.destroy()

    def prev_month(self):
        if self.display_month == 1:
            self.display_month = 12
            self.display_year -= 1
        else:
            self.display_month -= 1
        self.draw_calendar()

    def next_month(self):
        if self.display_month == 12:
            self.display_month = 1
            self.display_year += 1
        else:
            self.display_month += 1
        self.draw_calendar()


if __name__ == "__main__":
    root = tk.Tk()
    app = PlannerApp(root)
    root.mainloop()
