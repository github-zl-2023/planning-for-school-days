# planning-for-school-days

A simple, kid-friendly desktop planner for keeping track of school tasks.

## How to run

1. Make sure you have Python 3 installed.
2. From this folder, run:

```bash
python3 planner.py
```

The app stores tasks in a local `tasks.json` file. If it doesn't exist yet, the app will create it for you.

## Notes

- Pick a due date from the calendar or type `YYYY-MM-DD`, then enter time as `HH:MM`.
- Use the sidebar filters to switch between Today / This Week / All / Done.
- Pick a category (School/Home/Activities) when adding or editing a task.
- Reminders are checked every 30 seconds.
- The app tries to send a system notification if possible. If not, it will show an in-app popup reminder.
- Keyboard shortcuts: press **Enter** to save in the dialog, **Delete** to remove the selected task.
