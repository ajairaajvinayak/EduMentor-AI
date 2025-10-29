import streamlit as st
import pandas as pd
import datetime
import io
import contextlib
import subprocess
import tempfile
import sqlite3
import bcrypt
import smtplib
from email.mime.text import MIMEText
import time
from config import generate_ai_response

st.set_page_config(page_title="EduMentor AI", page_icon="🎓", layout="wide")

# ---------------- EMAIL CONFIG ----------------
SENDER_EMAIL = "your_email@gmail.com"       # ← replace with your Gmail
SENDER_PASSWORD = "your_app_password"       # ← use Gmail App Password

# ---------------- AUTH FUNCTIONS ----------------
def load_users():
    try:
        return pd.read_csv("users.csv")
    except FileNotFoundError:
        df = pd.DataFrame(columns=["email", "password"])
        df.to_csv("users.csv", index=False)
        return df

def save_user(email, password):
    df = load_users()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    df = pd.concat([df, pd.DataFrame({"email": [email], "password": [hashed]})])
    df.to_csv("users.csv", index=False)

def authenticate(email, password):
    df = load_users()
    user = df[df["email"] == email]
    if not user.empty:
        hashed = user.iloc[0]["password"]
        return bcrypt.checkpw(password.encode(), hashed.encode())
    return False

# ---------------- SESSION STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "page_ready" not in st.session_state:
    st.session_state.page_ready = False
if "login_time" not in st.session_state:
    st.session_state.login_time = None

# ---------------- EMAIL REMINDER FUNCTION ----------------
def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        server.quit()
        st.success(f"📩 Email sent to {to_email}")
    except Exception as e:
        st.error(f"❌ Email failed: {e}")

# ---------------- LOGIN / SIGNUP ----------------
def login_signup():
    st.title("🎓 EduMentor AI")
    st.subheader("Sign in or Create an Account")

    choice = st.radio("Select an option", ["🔐 Login", "🆕 Sign Up"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if choice == "🔐 Login":
        if st.button("Login"):
            if authenticate(email, password):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.login_time = time.time()
                st.success("✅ Login successful!")
                st.session_state.page_ready = False
                time.sleep(0.8)
                st.rerun()
            else:
                st.error("❌ Invalid email or password.")

    elif choice == "🆕 Sign Up":
        if st.button("Create Account"):
            if email and password:
                users = load_users()
                if email in users["email"].values:
                    st.warning("⚠️ Email already registered.")
                else:
                    save_user(email, password)
                    st.success("✅ Account created! Please log in.")
            else:
                st.warning("⚠️ Please fill both fields.")

# ---------------- STUDY PLANNER ----------------
def study_planner():
    st.header("📅 Generate Your Study Plan")

    name = st.text_input("👤 Your Name")
    goal = st.text_input("🎯 Your Goal")
    duration = st.number_input("📆 Duration (weeks)", min_value=1, max_value=52, value=4)
    hours_per_day = st.number_input("⏰ Study Hours per Day", min_value=1, max_value=12, value=3)
    focus_areas = st.text_area("📚 Focus Areas (comma-separated)", placeholder="Python, SQL, ML...")

    if st.button("Generate Plan"):
        if not name or not goal or not focus_areas:
            st.warning("⚠️ Please fill all fields.")
        else:
            topics = [t.strip() for t in focus_areas.split(",") if t.strip()]
            total_days = duration * 7
            days_per_topic = max(1, total_days // len(topics))
            plan = []
            for i, topic in enumerate(topics, 1):
                start_day = (i - 1) * days_per_topic + 1
                end_day = min(start_day + days_per_topic - 1, total_days)
                plan.append({
                    "Topic": topic,
                    "Days": f"Day {start_day} - Day {end_day}",
                    "Hours/Day": hours_per_day
                })
            df = pd.DataFrame(plan)
            st.success(f"✅ Study Plan for {name}")
            st.write(f"🎯 **Goal:** {goal}")
            st.dataframe(df, use_container_width=True)
            df.to_csv(f"study_plan_{st.session_state.user_email}.csv", index=False)

# ---------------- INTERVIEW QUESTIONS ----------------
def interview_questions():
    st.header("🎯 AI-Generated Interview Questions")
    topic = st.text_input("Enter any topic (e.g., Python, SQL, Cloud, ML)")

    if st.button("🤖 Generate Questions"):
        if not topic.strip():
            st.warning("⚠️ Please enter a topic.")
        else:
            with st.spinner("Generating AI questions..."):
                prompt = f"Generate 10 unique interview questions (basic to advanced) on {topic}"
                ai_response = generate_ai_response(prompt)
                st.subheader(f"💡 Interview Questions on {topic}")
                st.markdown(ai_response)

# ---------------- REMINDER SYSTEM ----------------
def reminder_system():
    st.header("⏰ Study Reminder")

    reminder_time = st.time_input("Set reminder time")
    message = st.text_input("Reminder message", placeholder="E.g., Take a break or start revision!")

    if st.button("Add Reminder"):
        reminders = st.session_state.get("reminders", [])
        reminders.append({"time": str(reminder_time), "msg": message})
        st.session_state["reminders"] = reminders
        st.success("✅ Reminder added!")

    st.write("### 🔔 Your Reminders:")
    reminders = st.session_state.get("reminders", [])
    for r in reminders:
        st.write(f"🕒 {r['time']} — {r['msg']}")

    now = datetime.datetime.now().strftime("%H:%M")
    for r in reminders:
        if r["time"] == now:
            st.warning(f"⏰ Reminder: {r['msg']}")
            send_email(st.session_state.user_email, "Study Reminder", r["msg"])

# ---------------- REST ALERT ----------------
def rest_alert():
    if st.session_state.login_time:
        elapsed = time.time() - st.session_state.login_time
        if elapsed >= 1800:  # 30 minutes
            st.warning("⚠️ You've been active for 30 minutes. Please take a 10-minute break!")
            st.info("🕓 Page will reset in 30 seconds...")
            time.sleep(30)
            st.session_state.login_time = time.time()
            st.rerun()

# ---------------- MAIN DASHBOARD ----------------
def dashboard():
    st.sidebar.title("📘 Navigation")
    page = st.sidebar.radio("Go to", [
        "📅 Study Planner",
        "🎯 Interview Questions (AI)",
        "⏰ Study Reminders"
    ])

    if page == "📅 Study Planner":
        study_planner()
    elif page == "🎯 Interview Questions (AI)":
        interview_questions()
    elif page == "⏰ Study Reminders":
        reminder_system()

    rest_alert()

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.page_ready = False
        st.rerun()

# ---------------- APP ROUTER ----------------
if not st.session_state.logged_in:
    login_signup()
else:
    if not st.session_state.page_ready:
        st.success("✅ Login successful! Click below to continue.")
        if st.button("Next ➡️"):
            st.session_state.page_ready = True
            st.rerun()
    else:
        dashboard()

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; padding-top: 10px; font-size: 15px;'>
        🚀 Built with ❤️ using <b>Streamlit</b> + <b>Gemini AI</b><br>
        👨‍💻 Credits: <b>Ajai Raaj</b>
    </div>
    """,
    unsafe_allow_html=True
)
