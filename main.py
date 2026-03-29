"""
main.py — CLI demo script to verify PawPal+ backend logic.
Run: python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler
from datetime import date


def print_schedule(schedule):
    if not schedule:
        print("  (no tasks)")
        return
    for pet, task in schedule:
        print(f"  {pet.name:10} | {task}")


def main():
    # --- setup ---
    owner = Owner("Jordan")

    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")

    owner.add_pet(mochi)
    owner.add_pet(luna)

    # --- add tasks (intentionally out of order) ---
    mochi.add_task(Task("Evening walk",    "18:00", 30, priority="high",   frequency="daily"))
    mochi.add_task(Task("Morning walk",    "07:00", 20, priority="high",   frequency="daily"))
    mochi.add_task(Task("Flea medication", "09:00", 5,  priority="medium", frequency="weekly"))
    mochi.add_task(Task("Vet appointment", "14:00", 60, priority="high",   frequency="once"))

    luna.add_task(Task("Breakfast",        "08:00", 10, priority="high",   frequency="daily"))
    luna.add_task(Task("Playtime",         "08:00", 15, priority="low",    frequency="daily"))  # conflict!
    luna.add_task(Task("Grooming",         "11:00", 20, priority="medium", frequency="weekly"))

    scheduler = Scheduler(owner)

    # --- today's schedule ---
    print("\n====== TODAY'S SCHEDULE ======")
    print_schedule(scheduler.generate_schedule())

    # --- conflict detection ---
    print("\n====== CONFLICT WARNINGS ======")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for w in conflicts:
            print(" ", w)
    else:
        print("  No conflicts detected.")

    # --- filtering ---
    print("\n====== MOCHI'S TASKS ONLY ======")
    print_schedule(scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Mochi")))

    print("\n====== HIGH PRIORITY TASKS ======")
    print_schedule(scheduler.sort_by_time(scheduler.filter_tasks(priority="high")))

    # --- recurring task demo ---
    print("\n====== MARKING 'Morning walk' COMPLETE (daily -> reschedules) ======")
    morning_walk = mochi.tasks[1]  # "Morning walk"
    scheduler.mark_task_complete(mochi, morning_walk)
    print(f"  '{morning_walk.title}' completed: {morning_walk.completed}")
    print(f"  Next 'Morning walk' due: {mochi.tasks[-1].due_date}")

    # --- updated schedule ---
    print("\n====== UPDATED SCHEDULE (after completion) ======")
    print_schedule(scheduler.generate_schedule())

    print()


if __name__ == "__main__":
    main()
