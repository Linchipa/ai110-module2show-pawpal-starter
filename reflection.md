# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I designed four classes:

- **Task** (dataclass) — holds a single care activity: `title`, `time` (HH:MM string), `duration_minutes`, `priority`, `frequency`, `completed`, and `due_date`. Its only behavior is `mark_complete()`, which flips the status and returns a new Task if the frequency is recurring.
- **Pet** (dataclass) — stores `name`, `species`, and a list of `Task` objects. Responsible for managing its own task list via `add_task()` and `remove_task()`.
- **Owner** — holds a name and a list of `Pet` objects. Provides `add_pet()` and `get_all_tasks()`, which flattens all pet-task pairs into a single list for the Scheduler to consume.
- **Scheduler** — the "brain." It receives an `Owner` and provides all algorithmic operations: sorting, filtering, conflict detection, recurring-task automation, and daily schedule generation.

I chose Python dataclasses for `Task` and `Pet` because they eliminate boilerplate `__init__` code while keeping the class readable. `Owner` and `Scheduler` use regular classes because they have non-trivial initialization logic.

**b. Design changes**

Originally I considered putting `sort_by_time()` directly on `Owner`, but that would have mixed data-holding responsibilities with algorithmic ones. Moving all scheduling intelligence into `Scheduler` kept each class focused on a single responsibility. I also added a secondary sort key (priority) to `sort_by_time()` after discovering that two tasks at `08:00` needed a deterministic ordering.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers:
1. **Time** — tasks are sorted by `HH:MM` so the owner sees their day in order.
2. **Priority** — when two tasks share the same time, `high` comes before `medium` before `low`.
3. **Due date** — `generate_schedule()` only shows tasks whose `due_date` is today or earlier.
4. **Completion status** — completed tasks are hidden from the active schedule.

Time was chosen as the primary sort key because a pet owner thinks in terms of their clock, not abstract priority scores.

**b. Tradeoffs**

The conflict detector only flags exact time matches (e.g., two tasks both at `08:00`). It does not check for overlapping durations (e.g., a 60-minute task at `08:00` overlapping a task at `08:30`). This is a deliberate simplification: implementing overlap detection requires converting times to minutes-since-midnight and checking interval intersections, which adds complexity that may not matter for most home pet-care scenarios. A pet owner is more likely to care about double-booking an exact slot than about precise interval overlap.

---

## 3. AI Collaboration

**a. How you used AI**

AI (Claude Code) was used throughout the project:
- **Design phase** — brainstormed which class should own which responsibility (e.g., should `sort_by_time` live on `Owner` or `Scheduler`?).
- **Implementation** — scaffolded the dataclass structures and the `mark_complete()` recurring-task logic using `timedelta`.
- **Testing** — generated a comprehensive pytest suite covering happy paths and edge cases.
- **UI integration** — designed the `st.session_state` pattern so the `Owner` object persists across Streamlit reruns.

The most helpful prompts were specific and structural: "How should the Scheduler retrieve all tasks from the Owner's pets?" rather than "write me a scheduler."

**b. Judgment and verification**

An early AI suggestion placed the recurring-task creation logic entirely inside `Scheduler.mark_task_complete()`. I modified this: the decision of what the next task looks like belongs to `Task` (it knows its own frequency and due date), while `Scheduler` is responsible for where to put the resulting task. This separation keeps `Task` self-contained and testable in isolation — confirmed by the fact that `test_mark_complete_daily_creates_next_task` tests `Task` directly without needing a `Scheduler`.

---

## 4. Testing and Verification

**a. What you tested**

- Task completion status change (`mark_complete()` flips `completed`)
- Recurring task creation: daily (+1 day), weekly (+7 days), once (no follow-up)
- `add_task()` increases pet task count; `remove_task()` decreases it
- `sort_by_time()` returns tasks in HH:MM ascending order
- Same-time tasks ordered by priority (high before low)
- `filter_tasks()` by pet name, completion status, and priority
- Conflict detection finds duplicate slots; no false positives on unique slots
- `mark_task_complete()` on a daily task adds a new task to the pet
- `mark_task_complete()` on a one-time task does not add a follow-up
- Edge cases: owner with no pets, pet with no tasks

**b. Confidence**

**5/5 stars** — All 17 tests pass. Edge cases I would test next:
- Tasks with `due_date` in the future (should not appear in today's schedule)
- Multiple conflicts for the same pet (more than two tasks at the same time)
- Large task lists to check sorting performance

---

## 5. Reflection

**a. What went well**

The CLI-first workflow was the most valuable discipline. By verifying `main.py` output before touching `app.py`, I caught the time-format sorting edge case (same-time, different-priority tasks) early, where it was easy to fix in one place rather than debugging through the UI.

**b. What you would improve**

The conflict detector currently only checks exact time matches. Given more time I would implement interval-overlap detection and add data persistence (saving pets and tasks to a `data.json` file so the schedule survives a Streamlit restart).

**c. Key takeaway**

The most important lesson was that AI is best used as a collaborator on structure, not a generator of complete solutions. When I asked AI specific, architectural questions ("where should the recurrence logic live?") the conversation produced a cleaner, more testable design. The human architect's job is to ask the right questions and evaluate the answers critically.
