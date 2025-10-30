# app.py
import streamlit as st
import pandas as pd
import datetime
import io
import contextlib
import sqlite3
import bcrypt
import smtplib
import threading
import time
from email.mime.text import MIMEText
from config import generate_ai_response  # must exist and return text for prompts

# -------------------------
# App config
# -------------------------
st.set_page_config(page_title="EduMentor AI", page_icon="🎓", layout="wide")

# -------------------------
# Email (Gmail SMTP) config
# -------------------------
# Replace these with your sending Gmail and App Password (create App Password in Google account)
SENDER_EMAIL = "your_email@gmail.com"
SENDER_APP_PASSWORD = "your_app_password"

# -------------------------
# Helper: send email (no Streamlit UI calls inside thread)
# -------------------------
def _send_email_direct(to_email: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)

# -------------------------
# Reminder background checker (runs once)
# -------------------------
def start_reminder_thread():
    """Start a single background daemon thread that checks reminders in session_state."""
    if st.session_state.get("_reminder_thread_started"):
        return

    def checker():
        while True:
            try:
                reminders = st.session_state.get("reminders_by_user", {})
                now_str = datetime.datetime.now().strftime("%H:%M")
                for user_email, user_reminders in list(reminders.items()):
                    # iterate copy because we may modify list
                    for rem in list(user_reminders):
                        if rem.get("sent"):
                            continue
                        # rem['time'] stored as "HH:MM"
                        if rem.get("time") == now_str:
                            ok, err = _send_email_direct(user_email, "EduMentor Study Reminder", rem.get("msg", "Time to study!"))
                            rem["sent"] = True
                            if not ok:
                                rem["last_error"] = err
                time.sleep(20)
            except Exception:
                time.sleep(20)

    th = threading.Thread(target=checker, daemon=True)
    th.start()
    st.session_state["_reminder_thread_started"] = True


# -------------------------
# Users (bcrypt + CSV)
# -------------------------
USERS_CSV = "users.csv"

def load_users():
    try:
        return pd.read_csv(USERS_CSV)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["email", "password"])
        df.to_csv(USERS_CSV, index=False)
        return df

def save_user(email: str, password_plain: str):
    df = load_users()
    hashed = bcrypt.hashpw(password_plain.encode(), bcrypt.gensalt()).decode()
    df = pd.concat([df, pd.DataFrame({"email": [email], "password": [hashed]})], ignore_index=True)
    df.to_csv(USERS_CSV, index=False)

def verify_user(email: str, password_plain: str) -> bool:
    df = load_users()
    user = df[df["email"] == email]
    if user.empty:
        return False
    hashed = user.iloc[0]["password"]
    return bcrypt.checkpw(password_plain.encode(), hashed.encode())

# -------------------------
# Session state defaults
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "page_ready" not in st.session_state:
    st.session_state.page_ready = False
if "login_time" not in st.session_state:
    st.session_state.login_time = None
if "reminders_by_user" not in st.session_state:
    # dict: {email: [ {time: "HH:MM", msg: "...", sent: False} ] }
    st.session_state.reminders_by_user = {}
if "show_login" not in st.session_state:
    st.session_state.show_login = False

# start background reminder checker
start_reminder_thread()

# -------------------------
# Front splash page (logo)
# -------------------------
def front_page():
    logo_path = "assets/logo.png"
    try:
        st.image(logo_path, use_container_width=True)
    except Exception:
        st.title("🎓 EduMentor AI")

    st.markdown(
        """
        <div style='text-align:center; margin-top:10px;'>
            <h2>EduMentor AI</h2>
            <p style='color: #666;'>Your AI-powered study companion — plan, practice and prepare smarter.</p>
            <p>Built by <b>Ajai Raaj</b></p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("🚀 Get Started"):
        st.session_state.show_login = True
        # safe rerun
        st.rerun()

# -------------------------
# Login / Signup UI
# -------------------------
def login_signup_ui():
    st.header("🔐 Login / Sign Up")
    choice = st.radio("Select:", ["Login", "Sign Up"], index=0)

    email = st.text_input("Email", key="auth_email")
    password = st.text_input("Password", type="password", key="auth_password")

    if choice == "Sign Up":
        if st.button("Create Account"):
            if not email or not password:
                st.warning("Please enter email and password.")
            else:
                users_df = load_users()
                if email in users_df["email"].values:
                    st.warning("Email already registered. Please log in.")
                else:
                    save_user(email, password)
                    st.success("Account created! Please log in.")
    else:
        if st.button("Login"):
            if verify_user(email, password):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.login_time = time.time()
                st.success("✅ Login successful")
                st.session_state.page_ready = False
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Invalid credentials.")

# -------------------------
# Study planner UI
# -------------------------
def study_planner_ui():
    st.header("📅 Study Planner")
    name = st.text_input("Your name", key="planner_name")
    goal = st.text_input("Goal (e.g., Crack Data Science Interviews)", key="planner_goal")
    duration = st.number_input("Duration (weeks)", min_value=1, max_value=52, value=4, key="planner_duration")
    hours = st.number_input("Hours / day", min_value=1, max_value=12, value=2, key="planner_hours")
    focus = st.text_area("Focus areas (comma separated)", placeholder="Python, SQL, ML", key="planner_focus")

    if st.button("Generate Study Plan"):
        if not name or not goal or not focus.strip():
            st.warning("Please fill all fields.")
        else:
            topics = [t.strip() for t in focus.split(",") if t.strip()]
            total_days = duration * 7
            days_per_topic = max(1, total_days // len(topics))
            rows = []
            for i, topic in enumerate(topics, 1):
                start_day = (i - 1) * days_per_topic + 1
                end_day = min(start_day + days_per_topic - 1, total_days)
                rows.append({"Topic": topic, "Days": f"Day {start_day} - Day {end_day}", "Hours/Day": hours})
            df = pd.DataFrame(rows)
            st.success(f"Study plan generated for {name}")
            st.dataframe(df, use_container_width=True)
            # save per-user
            user_file = f"study_plan_{st.session_state.user_email}.csv"
            df.to_csv(user_file, index=False)
            st.info(f"Saved plan to {user_file}")

# -------------------------
# Interview questions UI (AI)
# -------------------------
def interview_questions_ui():
    st.header("🎯 AI-generated Interview Questions")
    topic = st.text_input("Enter any topic (any topic you want)", key="iq_topic")
    if st.button("Explain"):
        if not topic.strip():
            st.warning("Enter a topic.")
        else:
            with st.spinner("cooking concept"):
                prompt = f""""
                    first explain the concept of the given words or question's concept in 300 words in crisp and with the real world example then do these things , if user wants the image of it please find 
                    the related topic's image from the internet and provide some article or suggested course link for the user's related question.
🧩 1. Interview Question

Write a realistic, interviewer-style question on the given topic.

💡 2. Simple Explanation

Explain the concept in clear, beginner-friendly language that builds intuition. Avoid jargon unless necessary, and if used, define it.

🔍 3. Intuitive Understanding

Explain why the concept exists, what problem it solves, and how it fits into the broader ML/NLP/DSA context.
Use short relatable analogies or real-world examples to make it intuitive.

🧮 4. Mathematical or Algorithmic Explanation

If the concept involves math or algorithmic reasoning, include:

Relevant formulas or pseudocode, clearly explained

Step-by-step breakdown of how it works internally

Key parameters, assumptions, or variations

💻 5. Code Example (in Python)

If the topic involves implementation, include a concise, well-commented Python code snippet.

Ensure it’s clean and easy to follow.

Include small example input/output to demonstrate functionality.

If the topic is theoretical (no coding), skip or show how it might be used in code.

🧠 6. Real-World Analogy / Use Case

Connect the concept to a practical real-world scenario (e.g., predicting words in NLP, optimizing routes, fraud detection, etc.).
This helps visualize how the concept is used in production.

⚙️ 7. Applications / Interview Insights

Include:

Where this concept is commonly used (industry or ML pipelines)

Possible follow-up questions or common interview traps

suggest the user with the related youtube video that is related to the user's input question and if you can means run the video at the live webpage and you can share the link for the reference or youtube video related to the user input concept 

🏁 8. In One Line (Summary)

End with a short one-liner that neatly sums up the entire concept.

The explanation style should be professional yet simple, like how a senior ML engineer or interviewer would explain a concept during an interview.
Each section should build on the previous one, maintaining flow and clarity.
Always include real-world intuition + short code + clean mathematical connection.
                    : {topic}"""
                ai_text = generate_ai_response(prompt)
                st.markdown(f"### Questions on **{topic}**")
                st.markdown(ai_text)

# -------------------------
# Code practice UI (basic)
# -------------------------
def code_practice_ui():
    st.header("💻 Code Practice")
    lang = st.selectbox("Language", ["Python", "SQL"])
    code = st.text_area("Write code here", height=250, key="practice_code")
    if st.button("Run Code"):
        if not code.strip():
            st.warning("Write some code first.")
        else:
            if lang == "Python":
                with io.StringIO() as buf, contextlib.redirect_stdout(buf):
                    try:
                        exec(code, {})
                        out = buf.getvalue()
                        st.code(out or "✅ Ran successfully", language="python")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:  # SQL (sqlite in-memory)
                try:
                    conn = sqlite3.connect(":memory:")
                    cursor = conn.cursor()
                    cursor.executescript(code)
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    st.info(f"Tables: {tables}")
                    conn.close()
                except Exception as e:
                    st.error(f"SQL Error: {e}")

# -------------------------
# Reminder UI (schedules email)
# -------------------------
def reminder_ui():
    st.header("⏰ Reminders (emails + on-screen)")
    st.write("Set a daily reminder time (24-hr). Email will be sent at that time (app must be running).")

    time_sel = st.time_input("Reminder time (HH:MM)", key="rem_time")
    msg = st.text_input("Message / topic", key="rem_msg")

    if st.button("Add Reminder"):
        user = st.session_state.user_email
        if not user:
            st.error("No logged-in user.")
            return
        tstr = time_sel.strftime("%H:%M")
        reminders = st.session_state.reminders_by_user.get(user, [])
        reminders.append({"time": tstr, "msg": msg, "sent": False})
        st.session_state.reminders_by_user[user] = reminders
        st.success(f"Reminder set at {tstr} — we'll email you at that time.")
        st.info(f"Reminder scheduled: {tstr} — {msg}")

    user = st.session_state.user_email
    user_rem = st.session_state.reminders_by_user.get(user, [])
    if user_rem:
        st.write("Your reminders:")
        for r in user_rem:
            st.write(f"- {r['time']} — {r['msg']} (sent: {r.get('sent', False)})")
    else:
        st.info("No reminders set yet.")

# -------------------------
# 30-minute rest alert
# -------------------------
def check_rest_alert():
    if st.session_state.login_time is None:
        return
    elapsed = time.time() - st.session_state.login_time
    if elapsed >= 1800:  # 30 minutes
        # show modal-like block for 30 seconds
        with st.expander("⏳ You've been active for 30 minutes — take 10 minutes rest", expanded=True):
            st.write("Please step away for 10 minutes to rest your eyes and mind.")
            st.write("This message will close in 30 seconds.")
            time.sleep(30)
        # reset timer
        st.session_state.login_time = time.time()
        st.rerun()

# -------------------------
# App navigation
# -------------------------
def dashboard():
    st.sidebar.title("Navigation")
    choice = st.sidebar.radio("Go to", ["Study Planner", "Interview Questions", "Code Practice", "Reminders", "Logout"])

    if choice == "Study Planner":
        study_planner_ui()
    elif choice == "Interview Questions":
        interview_questions_ui()
    elif choice == "Code Practice":
        code_practice_ui()
    elif choice == "Reminders":
        reminder_ui()
    elif choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.page_ready = False
        st.rerun()

    # check rest alert each dashboard load
    check_rest_alert()

# -------------------------
# Main entry & routing
# -------------------------
if not st.session_state.show_login and not st.session_state.logged_in:
    front_page()
elif not st.session_state.logged_in:
    login_signup_ui()
else:
    # logged in
    if not st.session_state.page_ready:
        st.success("✅ Login successful.")
        if st.button("Next ➡️"):
            st.session_state.page_ready = True
            # set login time (start session timer)
            st.session_state.login_time = time.time()
            st.rerun()
    else:
        dashboard()

# -------------------------
# Footer
# -------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align:center;'>🚀 Built with ❤️ by <b>Ajai Raaj</b></div>",
    unsafe_allow_html=True
)



