"""
PawPal+ Streamlit UI
Connects to the backend logic in pawpal_system.py.
"""

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ---------------------------------------------------------------------------
# Session state — persists Owner across reruns
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

# ---------------------------------------------------------------------------
# Sidebar — Owner setup
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🐾 PawPal+")
    st.subheader("Owner Setup")

    owner_name = st.text_input("Owner name", value="Jordan", key="owner_name_input")
    if st.button("Set / Update Owner"):
        if st.session_state.owner is None:
            st.session_state.owner = Owner(owner_name)
        else:
            st.session_state.owner.name = owner_name
        st.success(f"Owner set to {owner_name}")

    if st.session_state.owner is None:
        st.info("Enter your name and click 'Set / Update Owner' to begin.")
        st.stop()

    st.divider()

    # --- Add Pet ---
    st.subheader("Add a Pet")
    pet_name = st.text_input("Pet name", key="new_pet_name")
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"], key="new_species")
    if st.button("Add Pet"):
        if pet_name.strip():
            existing = [p.name.lower() for p in st.session_state.owner.pets]
            if pet_name.strip().lower() in existing:
                st.warning(f"{pet_name} is already in your roster.")
            else:
                st.session_state.owner.add_pet(Pet(pet_name.strip(), species))
                st.success(f"Added {pet_name}!")
        else:
            st.warning("Please enter a pet name.")

    # --- Pet list summary ---
    if st.session_state.owner.pets:
        st.divider()
        st.subheader("Your Pets")
        for pet in st.session_state.owner.pets:
            st.write(f"- **{pet.name}** ({pet.species}), {len(pet.tasks)} task(s)")

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
owner = st.session_state.owner
scheduler = Scheduler(owner)

st.title(f"PawPal+ — {owner.name}'s Dashboard")

tabs = st.tabs(["Today's Schedule", "Add Task", "Complete Tasks", "Filter & Search"])

# ===========================================================================
# TAB 1 — Today's Schedule
# ===========================================================================
with tabs[0]:
    st.subheader("Today's Schedule")

    if not owner.pets:
        st.info("Add a pet from the sidebar to get started.")
    else:
        # Conflict warnings
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            for w in conflicts:
                st.warning(w)

        schedule = scheduler.generate_schedule()

        if not schedule:
            st.info("No pending tasks for today. All done or nothing added yet!")
        else:
            rows = []
            for pet, task in schedule:
                rows.append({
                    "Time": task.time,
                    "Pet": pet.name,
                    "Task": task.title,
                    "Duration (min)": task.duration_minutes,
                    "Priority": task.priority.capitalize(),
                    "Frequency": task.frequency.capitalize(),
                })
            st.table(rows)

        # All tasks (including completed)
        with st.expander("Show all tasks (including completed)"):
            all_pairs = scheduler.sort_by_time()
            if not all_pairs:
                st.write("No tasks added yet.")
            for pet, task in all_pairs:
                status_label = "Done" if task.completed else "Pending"
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{task.time}** | {pet.name} — {task.title} ({task.priority}, {task.frequency})")
                col2.write(status_label)

# ===========================================================================
# TAB 2 — Add Task
# ===========================================================================
with tabs[1]:
    st.subheader("Add a Task")

    if not owner.pets:
        st.info("Add a pet first using the sidebar.")
    else:
        pet_names = [p.name for p in owner.pets]

        with st.form("add_task_form"):
            col1, col2 = st.columns(2)
            with col1:
                selected_pet = st.selectbox("Pet", pet_names)
                task_title = st.text_input("Task title", placeholder="e.g. Morning walk")
                task_time = st.text_input("Time (HH:MM)", value="08:00")
            with col2:
                duration = st.number_input("Duration (minutes)", min_value=1, max_value=480, value=20)
                priority = st.selectbox("Priority", ["high", "medium", "low"])
                frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])

            submitted = st.form_submit_button("Add Task")

        if submitted:
            if not task_title.strip():
                st.error("Task title cannot be empty.")
            else:
                # Validate time format
                try:
                    h, m = task_time.split(":")
                    assert 0 <= int(h) <= 23 and 0 <= int(m) <= 59
                    time_valid = True
                except Exception:
                    time_valid = False

                if not time_valid:
                    st.error("Please enter a valid time in HH:MM format (e.g. 07:30).")
                else:
                    pet = next(p for p in owner.pets if p.name == selected_pet)
                    pet.add_task(Task(
                        title=task_title.strip(),
                        time=task_time,
                        duration_minutes=int(duration),
                        priority=priority,
                        frequency=frequency,
                    ))
                    st.success(f"Added '{task_title}' for {selected_pet} at {task_time}!")
                    st.rerun()

# ===========================================================================
# TAB 3 — Complete Tasks
# ===========================================================================
with tabs[2]:
    st.subheader("Mark Tasks Complete")

    pending_pairs = scheduler.filter_tasks(completed=False)

    if not pending_pairs:
        st.success("All tasks are complete! Nothing left to do.")
    else:
        for i, (pet, task) in enumerate(scheduler.sort_by_time(pending_pairs)):
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{task.time}** | **{pet.name}** — {task.title} ({task.priority}, {task.frequency})")
            if col2.button("Done", key=f"complete_{i}_{task.title}_{pet.name}"):
                scheduler.mark_task_complete(pet, task)
                if task.frequency in ("daily", "weekly"):
                    st.success(f"'{task.title}' complete! Next occurrence scheduled.")
                else:
                    st.success(f"'{task.title}' complete!")
                st.rerun()

# ===========================================================================
# TAB 4 — Filter & Search
# ===========================================================================
with tabs[3]:
    st.subheader("Filter & Search Tasks")

    if not owner.pets:
        st.info("Add a pet first.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_pet = st.selectbox("Filter by pet", ["All"] + [p.name for p in owner.pets])
        with col2:
            filter_status = st.selectbox("Filter by status", ["All", "Pending", "Completed"])
        with col3:
            filter_priority = st.selectbox("Filter by priority", ["All", "high", "medium", "low"])

        pet_arg = None if filter_pet == "All" else filter_pet
        status_arg = None if filter_status == "All" else (filter_status == "Completed")
        priority_arg = None if filter_priority == "All" else filter_priority

        results = scheduler.filter_tasks(
            pet_name=pet_arg,
            completed=status_arg,
            priority=priority_arg,
        )
        results = scheduler.sort_by_time(results)

        if not results:
            st.info("No tasks match your filters.")
        else:
            rows = []
            for pet, task in results:
                rows.append({
                    "Time": task.time,
                    "Pet": pet.name,
                    "Task": task.title,
                    "Duration (min)": task.duration_minutes,
                    "Priority": task.priority.capitalize(),
                    "Frequency": task.frequency.capitalize(),
                    "Status": "Done" if task.completed else "Pending",
                })
            st.table(rows)
            st.caption(f"{len(results)} task(s) found.")
