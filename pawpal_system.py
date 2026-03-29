"""
PawPal+ System Logic Layer
Core classes: Task, Pet, Owner, Scheduler
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """Represents a single pet care activity."""

    title: str
    time: str                          # "HH:MM" format
    duration_minutes: int
    priority: str = "medium"           # "low", "medium", "high"
    frequency: str = "once"            # "once", "daily", "weekly"
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def mark_complete(self):
        """Mark this task complete and schedule the next occurrence for recurring tasks."""
        self.completed = True
        if self.frequency == "daily":
            return Task(
                title=self.title,
                time=self.time,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(days=1),
            )
        if self.frequency == "weekly":
            return Task(
                title=self.title,
                time=self.time,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(weeks=1),
            )
        return None  # "once" — no follow-up task

    def __str__(self):
        status = "x" if self.completed else " "
        return (
            f"[{status}] {self.time} | {self.title} "
            f"({self.duration_minutes} min, {self.priority}, {self.frequency})"
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a pet owned by an Owner."""

    name: str
    species: str
    tasks: list = field(default_factory=list)

    def add_task(self, task: Task):
        """Add a Task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task: Task):
        """Remove a Task from this pet's task list."""
        if task in self.tasks:
            self.tasks.remove(task)

    def __str__(self):
        return f"{self.name} ({self.species})"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Manages one or more pets and provides access to all their tasks."""

    def __init__(self, name: str):
        """Initialize an Owner with a name and an empty pet list."""
        self.name = name
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet):
        """Add a Pet to this owner's roster."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (Pet, Task) pair across all pets."""
        pairs = []
        for pet in self.pets:
            for task in pet.tasks:
                pairs.append((pet, task))
        return pairs

    def __str__(self):
        return f"Owner: {self.name} ({len(self.pets)} pet(s))"


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class Scheduler:
    """Retrieves, organizes, and manages tasks across all of an owner's pets."""

    def __init__(self, owner: Owner):
        """Initialize with an Owner whose pets and tasks will be managed."""
        self.owner = owner

    # --- retrieval ----------------------------------------------------------

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all (Pet, Task) pairs from the owner."""
        return self.owner.get_all_tasks()

    # --- sorting ------------------------------------------------------------

    def sort_by_time(self, pairs: Optional[list] = None) -> list[tuple[Pet, Task]]:
        """Return tasks sorted by time (HH:MM) then by priority."""
        if pairs is None:
            pairs = self.get_all_tasks()
        return sorted(
            pairs,
            key=lambda pt: (pt[1].time, PRIORITY_ORDER.get(pt[1].priority, 1)),
        )

    # --- filtering ----------------------------------------------------------

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        priority: Optional[str] = None,
    ) -> list[tuple[Pet, Task]]:
        """Filter tasks by pet name, completion status, and/or priority."""
        results = self.get_all_tasks()
        if pet_name is not None:
            results = [(p, t) for p, t in results if p.name.lower() == pet_name.lower()]
        if completed is not None:
            results = [(p, t) for p, t in results if t.completed == completed]
        if priority is not None:
            results = [(p, t) for p, t in results if t.priority == priority]
        return results

    # --- conflict detection -------------------------------------------------

    def detect_conflicts(self) -> list[str]:
        """
        Return a list of warning strings when two tasks for the same pet
        share the same time slot.
        """
        warnings = []
        for pet in self.owner.pets:
            seen: dict[str, str] = {}  # time -> first task title
            for task in pet.tasks:
                if task.time in seen:
                    warnings.append(
                        f"[!] Conflict for {pet.name}: '{seen[task.time]}' and "
                        f"'{task.title}' both scheduled at {task.time}"
                    )
                else:
                    seen[task.time] = task.title
        return warnings

    # --- recurring task completion ------------------------------------------

    def mark_task_complete(self, pet: Pet, task: Task):
        """
        Mark a task complete. If it recurs, add the next occurrence to the pet.
        """
        next_task = task.mark_complete()
        if next_task is not None:
            pet.add_task(next_task)

    # --- schedule generation ------------------------------------------------

    def generate_schedule(self) -> list[tuple[Pet, Task]]:
        """
        Build today's schedule: sort by time, then by priority.
        Only includes tasks due today or earlier that are not yet complete.
        """
        today = date.today()
        pending = [
            (p, t)
            for p, t in self.get_all_tasks()
            if not t.completed and t.due_date <= today
        ]
        return self.sort_by_time(pending)
