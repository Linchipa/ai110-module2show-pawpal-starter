"""
Automated test suite for PawPal+ system logic.
Run: python -m pytest
"""

import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def basic_owner():
    owner = Owner("Jordan")
    dog = Pet("Mochi", "dog")
    cat = Pet("Luna", "cat")
    dog.add_task(Task("Evening walk", "18:00", 30, priority="high", frequency="daily"))
    dog.add_task(Task("Morning walk", "07:00", 20, priority="high", frequency="daily"))
    dog.add_task(Task("Vet visit",    "14:00", 60, priority="high", frequency="once"))
    cat.add_task(Task("Breakfast",    "08:00", 10, priority="high", frequency="daily"))
    cat.add_task(Task("Playtime",     "08:00", 15, priority="low",  frequency="daily"))  # conflict
    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


@pytest.fixture
def scheduler(basic_owner):
    return Scheduler(basic_owner)


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    """mark_complete() must flip completed to True."""
    task = Task("Walk", "09:00", 20)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_mark_complete_once_returns_none():
    """One-time tasks should return None (no follow-up)."""
    task = Task("Vet", "14:00", 60, frequency="once")
    result = task.mark_complete()
    assert result is None


def test_mark_complete_daily_creates_next_task():
    """Daily tasks should return a new Task due tomorrow."""
    today = date.today()
    task = Task("Walk", "07:00", 20, frequency="daily", due_date=today)
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False


def test_mark_complete_weekly_creates_next_task():
    """Weekly tasks should return a new Task due in 7 days."""
    today = date.today()
    task = Task("Grooming", "11:00", 20, frequency="weekly", due_date=today)
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

def test_add_task_increases_count():
    """add_task() must increase the pet's task list by 1."""
    pet = Pet("Mochi", "dog")
    before = len(pet.tasks)
    pet.add_task(Task("Walk", "07:00", 20))
    assert len(pet.tasks) == before + 1


def test_remove_task_decreases_count():
    """remove_task() must decrease the pet's task list by 1."""
    pet = Pet("Mochi", "dog")
    task = Task("Walk", "07:00", 20)
    pet.add_task(task)
    pet.remove_task(task)
    assert task not in pet.tasks


# ---------------------------------------------------------------------------
# Scheduler: sorting
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order(scheduler):
    """Tasks must come back in HH:MM ascending order."""
    sorted_pairs = scheduler.sort_by_time()
    times = [t.time for _, t in sorted_pairs]
    assert times == sorted(times)


def test_sort_by_time_same_time_high_priority_first(scheduler):
    """When two tasks share the same time, high priority comes first."""
    # Luna's 08:00 tasks: Breakfast (high) and Playtime (low)
    sorted_pairs = scheduler.sort_by_time()
    at_0800 = [(p, t) for p, t in sorted_pairs if t.time == "08:00"]
    assert at_0800[0][1].priority == "high"


# ---------------------------------------------------------------------------
# Scheduler: filtering
# ---------------------------------------------------------------------------

def test_filter_by_pet_name(scheduler):
    """filter_tasks(pet_name='Mochi') returns only Mochi's tasks."""
    results = scheduler.filter_tasks(pet_name="Mochi")
    assert all(p.name == "Mochi" for p, _ in results)


def test_filter_by_completion_status(scheduler, basic_owner):
    """filter_tasks(completed=True) returns only completed tasks."""
    mochi = basic_owner.pets[0]
    task = mochi.tasks[0]
    task.completed = True
    results = scheduler.filter_tasks(completed=True)
    assert len(results) == 1
    assert results[0][1].completed is True


def test_filter_by_priority(scheduler):
    """filter_tasks(priority='high') returns only high-priority tasks."""
    results = scheduler.filter_tasks(priority="high")
    assert all(t.priority == "high" for _, t in results)


# ---------------------------------------------------------------------------
# Scheduler: conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_finds_same_time(scheduler):
    """Conflict detection must flag Luna's two 08:00 tasks."""
    warnings = scheduler.detect_conflicts()
    assert len(warnings) >= 1
    assert any("Luna" in w for w in warnings)


def test_detect_conflicts_no_false_positives():
    """No warnings when every task has a unique time slot per pet."""
    owner = Owner("Alex")
    dog = Pet("Rex", "dog")
    dog.add_task(Task("Walk",    "07:00", 20))
    dog.add_task(Task("Feeding", "08:00", 10))
    dog.add_task(Task("Meds",    "09:00", 5))
    owner.add_pet(dog)
    scheduler = Scheduler(owner)
    assert scheduler.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Scheduler: recurring task via mark_task_complete
# ---------------------------------------------------------------------------

def test_recurring_task_adds_to_pet(basic_owner):
    """mark_task_complete on a daily task must add the next occurrence to the pet."""
    scheduler = Scheduler(basic_owner)
    mochi = basic_owner.pets[0]
    daily_task = next(t for t in mochi.tasks if t.frequency == "daily")
    count_before = len(mochi.tasks)
    scheduler.mark_task_complete(mochi, daily_task)
    assert len(mochi.tasks) == count_before + 1
    assert mochi.tasks[-1].due_date == daily_task.due_date + timedelta(days=1)


def test_once_task_does_not_add_followup(basic_owner):
    """mark_task_complete on a 'once' task must NOT add a follow-up."""
    scheduler = Scheduler(basic_owner)
    mochi = basic_owner.pets[0]
    once_task = next(t for t in mochi.tasks if t.frequency == "once")
    count_before = len(mochi.tasks)
    scheduler.mark_task_complete(mochi, once_task)
    assert len(mochi.tasks) == count_before


# ---------------------------------------------------------------------------
# Scheduler: edge cases
# ---------------------------------------------------------------------------

def test_owner_with_no_pets():
    """Scheduler handles an owner with no pets gracefully."""
    owner = Owner("Empty")
    scheduler = Scheduler(owner)
    assert scheduler.get_all_tasks() == []
    assert scheduler.detect_conflicts() == []
    assert scheduler.generate_schedule() == []


def test_pet_with_no_tasks():
    """Scheduler handles a pet with no tasks."""
    owner = Owner("Alex")
    owner.add_pet(Pet("Buddy", "dog"))
    scheduler = Scheduler(owner)
    assert scheduler.get_all_tasks() == []
