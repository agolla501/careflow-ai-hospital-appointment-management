
import os
import sqlite3

from datetime import datetime, timedelta, time
from pathlib import Path

import streamlit as st

from dotenv import load_dotenv
from google import genai


# --------------------------------------------
# 1. APPLICATION CONFIGURATION
# --------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "appointments.db"

load_dotenv(BASE_DIR / ".env")

AI_AVAILABLE = bool(os.getenv("GEMINI_API_KEY"))

st.set_page_config(
    page_title="CareFlow AI",
    page_icon="🏥",
    layout="wide"
)


# --------------------------------------------
# 2. CREATE THE APPOINTMENT DATABASE
# --------------------------------------------

def initialize_database():

    conn = sqlite3.connect(DB_PATH)

    try:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_alias TEXT NOT NULL,
                department TEXT NOT NULL,
                appointment_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending'
            )
        """)

        conn.commit()

    finally:

        conn.close()


# --------------------------------------------
# 3. SAVE A NEW APPOINTMENT
# --------------------------------------------

def add_appointment(
    patient_alias,
    department,
    appointment_at,
    status="Pending"
):

    conn = sqlite3.connect(DB_PATH)

    try:

        conn.execute(
            """
            INSERT INTO appointments
            (patient_alias, department, appointment_at, status)
            VALUES (?, ?, ?, ?)
            """,
            (
                patient_alias,
                department,
                appointment_at.isoformat(timespec="minutes"),
                status
            )
        )

        conn.commit()

    finally:

        conn.close()


# --------------------------------------------
# 4. RETRIEVE SAVED APPOINTMENTS
# --------------------------------------------

def get_appointments():

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    try:

        rows = conn.execute(
            """
            SELECT *
            FROM appointments
            ORDER BY appointment_at ASC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:

        conn.close()


# --------------------------------------------
# 5. UPDATE APPOINTMENT CONFIRMATION STATUS
# --------------------------------------------

def update_appointment_status(appointment_id, new_status):

    conn = sqlite3.connect(DB_PATH)

    try:

        conn.execute(
            """
            UPDATE appointments
            SET status = ?
            WHERE id = ?
            """,
            (new_status, appointment_id)
        )

        conn.commit()

    finally:

        conn.close()


# --------------------------------------------
# 6. CHECK IF AN APPOINTMENT NEEDS ATTENTION
# --------------------------------------------

def check_appointment(appointment):

    status = appointment["status"]

    appointment_time = datetime.fromisoformat(
        appointment["appointment_at"]
    )

    current_time = datetime.now()

    if status == "Cancelled":
        return "Cancelled"

    if status == "Confirmed":
        return "Confirmed"

    time_remaining = appointment_time - current_time

    if time_remaining <= timedelta(0):
        return "Past due - review required"

    if time_remaining <= timedelta(hours=24):
        return "Needs confirmation"

    return "Upcoming"


# --------------------------------------------
# 7. CREATE A REMINDER DRAFT
# --------------------------------------------

def generate_reminder(appointment):

    appointment_time = datetime.fromisoformat(
        appointment["appointment_at"]
    )

    formatted_time = appointment_time.strftime(
        "%B %d, %Y at %I:%M %p"
    )

    department = appointment["department"]

    # If Gemini is not configured, use a normal template.
    if not AI_AVAILABLE:

        return (
            "Hello,\n\n"
            "This is a reminder of your upcoming "
            f"{department} appointment scheduled for "
            f"{formatted_time}.\n\n"
            "Please contact the scheduling team "
            "to confirm or request a change.\n\n"
            "Thank you."
        )

    # Gemini AI client
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY")
    )

    prompt = f"""
You write short, professional appointment reminder drafts
for a fictional hospital scheduling demonstration.

Use only the supplied appointment details.

Department: {department}
Appointment date and local time: {formatted_time}

Rules:
- Do not invent phone numbers, addresses, medical information,
  or hospital policies.
- Do not claim the appointment is already confirmed.
- Do not include patient names or identifiers.
- Do not provide medical advice.
- Politely ask the recipient to contact the scheduling team
  to confirm or request a change.
- Keep the reminder concise and professional.

Return only the reminder message.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return response.text



# --------------------------------------------
# 8. ADD FICTIONAL APPOINTMENTS FOR TESTING
# --------------------------------------------

def create_demo_appointments():

    now = datetime.now()

    add_appointment(
        "Demo Patient A",
        "General Consultation",
        now + timedelta(hours=8),
        "Pending"
    )

    add_appointment(
        "Demo Patient B",
        "Dental",
        now + timedelta(hours=20),
        "Confirmed"
    )

    add_appointment(
        "Demo Patient C",
        "Physiotherapy",
        now + timedelta(hours=72),
        "Pending"
    )


# --------------------------------------------
# 9. START THE APPLICATION
# --------------------------------------------

initialize_database()

st.title("🏥 CareFlow AI")

st.subheader(
    "AI-Powered Hospital Appointment Management"
)

st.caption(
    "Independent educational demonstration. "
    "Use fictional appointment data only. "
    "Not connected to a real hospital."
)

if AI_AVAILABLE:

    st.success(
        "AI mode is enabled. "
        "Reminder drafts will use the OpenAI API."
    )

else:

    st.info(
        "Template mode is enabled. "
        "Add an OpenAI API key to your .env file "
        "to enable AI-generated reminder drafts."
    )


# --------------------------------------------
# 10. CREATE SAMPLE DATA
# --------------------------------------------

if not get_appointments():

    st.write(
        "Your appointment database is empty."
    )

    if st.button("Load three fictional appointments"):

        create_demo_appointments()

        st.rerun()


# --------------------------------------------
# 11. APPOINTMENT REGISTRATION FORM
# --------------------------------------------

st.header("Register a New Appointment")

with st.form("appointment_form"):

    patient_alias = st.text_input(
        "Patient alias",
        placeholder="Example: Demo Patient D"
    )

    department = st.selectbox(
        "Department",
        [
            "General Consultation",
            "Dental",
            "Physiotherapy"
        ]
    )

    appointment_date = st.date_input(
        "Appointment date",
        value=(
            datetime.now() + timedelta(days=1)
        ).date()
    )

    appointment_clock = st.time_input(
        "Appointment time",
        value=time(10, 0)
    )

    submitted = st.form_submit_button(
        "Save Appointment"
    )

    if submitted:

        appointment_datetime = datetime.combine(
            appointment_date,
            appointment_clock
        )

        if not patient_alias.strip():

            st.error(
                "Please enter a fictional patient alias."
            )

        elif appointment_datetime <= datetime.now():

            st.error(
                "Please choose a future appointment."
            )

        else:

            add_appointment(
                patient_alias.strip(),
                department,
                appointment_datetime
            )

            st.success(
                "Appointment saved successfully."
            )


# --------------------------------------------
# 12. LOAD APPOINTMENTS
# --------------------------------------------

appointments = get_appointments()

if not appointments:

    st.info(
        "Add an appointment or load the sample data "
        "to view the dashboard."
    )

    st.stop()


# --------------------------------------------
# 13. CALCULATE DASHBOARD METRICS
# --------------------------------------------

total_appointments = len(appointments)

needs_confirmation = sum(
    check_appointment(a) == "Needs confirmation"
    for a in appointments
)

confirmed_appointments = sum(
    a["status"] == "Confirmed"
    for a in appointments
)

past_due_appointments = sum(
    check_appointment(a) == "Past due - review required"
    for a in appointments
)


# --------------------------------------------
# 14. DISPLAY THE DASHBOARD
# --------------------------------------------

st.header("Appointment Dashboard")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Appointments",
    total_appointments
)

col2.metric(
    "Need Confirmation",
    needs_confirmation
)

col3.metric(
    "Confirmed",
    confirmed_appointments
)

col4.metric(
    "Past Due",
    past_due_appointments
)

dashboard_rows = []

for appointment in appointments:

    appointment_time = datetime.fromisoformat(
        appointment["appointment_at"]
    )

    dashboard_rows.append({
        "ID": appointment["id"],
        "Patient": appointment["patient_alias"],
        "Department": appointment["department"],
        "Appointment": appointment_time.strftime(
            "%Y-%m-%d %I:%M %p"
        ),
        "Confirmation": appointment["status"],
        "Follow-up Status": check_appointment(
            appointment
        )
    })

st.dataframe(
    dashboard_rows,
    hide_index=True,
    use_container_width=True
)

st.caption(
    "All appointment times use your computer's "
    "local timezone."
)

if st.button("Refresh Appointment Dashboard"):

    st.rerun()


# --------------------------------------------
# 15. REVIEW INDIVIDUAL APPOINTMENTS
# --------------------------------------------

st.header("Appointment Review & AI Reminders")

for appointment in appointments:

    appointment_id = appointment["id"]

    follow_up_status = check_appointment(
        appointment
    )

    with st.expander(
        f"Appointment {appointment_id} - "
        f"{appointment['patient_alias']} - "
        f"{follow_up_status}"
    ):

        appointment_time = datetime.fromisoformat(
            appointment["appointment_at"]
        )

        st.write(
            "Department:",
            appointment["department"]
        )

        st.write(
            "Appointment:",
            appointment_time.strftime(
                "%B %d, %Y at %I:%M %p"
            )
        )

        st.write(
            "Current status:",
            appointment["status"]
        )

        st.write(
            "Follow-up:",
            follow_up_status
        )

        # Allow staff to update appointment status.

        new_status = st.selectbox(
            "Update confirmation status",
            [
                "Pending",
                "Confirmed",
                "Cancelled"
            ],
            index=[
                "Pending",
                "Confirmed",
                "Cancelled"
            ].index(appointment["status"]),
            key=f"status_{appointment_id}"
        )

        if st.button(
            "Save Status",
            key=f"save_{appointment_id}"
        ):

            update_appointment_status(
                appointment_id,
                new_status
            )

            st.rerun()

        # Only generate a reminder when confirmation
        # is pending and the appointment is approaching.

        if follow_up_status == "Needs confirmation":

            st.warning(
                "This appointment requires "
                "confirmation follow-up."
            )

            draft_key = f"draft_{appointment_id}"

            if st.button(
                "Generate Reminder Draft",
                key=f"generate_{appointment_id}"
            ):

                try:

                    st.session_state[draft_key] = (
                        generate_reminder(appointment)
                    )

                except Exception as error:


                    st.error(
                        "AI reminder generation is temporarily unavailable. "
                        "Please verify the API configuration and try again."
                   )

                    st.caption(str(error))

            if draft_key in st.session_state:

                st.text_area(
                    "Reminder draft - staff review only",
                    key=draft_key,
                    height=160
                )

                st.caption(
                    "This is a draft. "
                    "No message has been sent."
                )

        elif follow_up_status == "Past due - review required":

            st.error(
                "The appointment time has passed. "
                "Staff should review the appointment "
                "rather than generate an upcoming reminder."
            )


# --------------------------------------------
# 16. APPLICATION FOOTER
# --------------------------------------------

st.divider()

st.caption(
    "CareFlow AI | Independent AI Engineering "
    "Portfolio Project | Synthetic Data Only"
)