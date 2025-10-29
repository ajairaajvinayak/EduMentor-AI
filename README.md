🎓 EduMentor AI

Your AI-Powered Study Companion — Plan, Practice & Prepare Smarter

🚀 Overview

EduMentor AI is an intelligent study assistant built using Streamlit and Gemini AI (Google Generative AI).
It helps students plan their study schedule, generate AI-based interview questions, practice coding, and stay focused with reminders and rest alerts.

This project includes a secure login/signup system, Gmail-based reminder emails, and AI-powered learning tools, all in one interactive app.

🌟 Features
🧠 AI-Powered Learning

Automatically generates interview questions for any topic using Gemini AI.

Helps learners practice technical topics interactively.

🗓 Study Planner

Create personalized study schedules based on goals, duration, and daily hours.

Saves your study plans automatically.

💻 Code Practice

Practice programming directly inside the app.

Supports Python and SQL execution.

🔔 Smart Reminders

Set reminders that send email notifications via Gmail SMTP.

Keeps track of reminder status (sent / pending).

⏰ Focus Mode

After 30 minutes of continuous use, a gentle alert prompts the user to take a 10-minute rest.

🔐 User Authentication

Secure signup & login using bcrypt hashing.

Stores user details safely in users.csv.

💌 Email Integration

Uses Gmail SMTP for sending study reminders automatically.

🖼 Custom UI

Clean and modern Streamlit interface.

Custom EduMentor AI logo with credits to Ajai Raaj.

🧩 Tech Stack
Category	Technology
Frontend	Streamlit
Backend	Python
AI Model	Gemini 2.5 Flash (Google Generative AI)
Database	SQLite + CSV
Email	Gmail SMTP
Security	bcrypt Password Hashing
⚙️ Installation
1️⃣ Clone the Repository
git clone https://github.com/your-username/EduMentor-AI.git
cd EduMentor-AI

2️⃣ Create a Virtual Environment
python -m venv venv
source venv/bin/activate   # for Linux/Mac
venv\Scripts\activate      # for Windows

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Add Your Credentials

Open config.py and replace with your Gemini API key.

Update these in app.py:

SENDER_EMAIL = "your_email@gmail.com"
SENDER_APP_PASSWORD = "your_app_password"


(Use a Gmail App Password — not your actual Gmail password.)

5️⃣ Run the App
streamlit run app.py

🧠 Folder Structure
EduMentor-AI/
│
├── app.py                # Main Streamlit App
├── config.py             # Gemini AI Configuration
├── assets/
│   └── logo.png          # App Logo
├── users.csv             # User data (auto-created)
├── study_plan_<user>.csv # Individual user plans (auto-saved)
├── requirements.txt      # Dependencies
└── README.md             # Project documentation

📧 Email Reminder Setup

Enable 2-Step Verification in your Gmail account.

Create an App Password for “Mail”.

Paste that password in the SENDER_APP_PASSWORD field inside app.py.

🛡️ Security

Passwords are hashed using bcrypt.

Emails are sent securely using SSL (Port 465).

No sensitive data is stored in plain text.

💡 Future Enhancements

Add multi-language support (Java, C++, MySQL, Jupyter).

Add performance tracking and progress visualization.

Integrate AI-based doubt solving via chat.

Mobile-friendly UI for on-the-go learners.

🙌 Credits

Developed with ❤️ by Ajai Raaj
Built using Streamlit and Gemini AI

📜 License

This project is licensed under the MIT License — free to use and modify with attribution.
