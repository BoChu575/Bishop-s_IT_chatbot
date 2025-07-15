import streamlit as st
import html
import re
import time
import os
import csv
from groq import Groq

# --- Page setup ---
st.set_page_config(page_title="C2 Chatbot", page_icon="💻")
st.title("💬 IT Support Chatbot")
st.markdown("Ask your basic IT questions here (Wi-Fi, Moodle, email, etc).")

# --- API Key input ---
default_key = ""
try:
    if hasattr(st, 'secrets') and "GROQ_API_KEY" in st.secrets:
        default_key = st.secrets["GROQ_API_KEY"]
except Exception:
    default_key = ""

api_key = st.text_input(
    "🔑 API Key",
    type="password",
    value=default_key,
    help="Enter your Groq API key. This will be auto-filled if configured in deployment."
)

# --- System prompt ---
system_prompt = """
You are an IT support assistant for Bishop's University. Help students with simple tech issues like Wi-Fi, Moodle, email, etc.

Use these facts when needed:
- Wi-Fi name: WIZABU
- Moodle login: https://moodle.ubishops.ca/
- Password reset: https://passwordreset.microsoftonline.com/
- Ticket system: https://octopus.ubishops.ca/
- ITS Helpdesk: The ITS Helpdesk is located on the 1st floor of the Library Learning Commons.
- Phone: 819-822-9600 ext. 2273

If the problem cannot be solved directly, kindly suggest submitting a support ticket or calling the IT Helpdesk. 
Keep answers friendly, simple but specific to Bishop's University students.
"""

# --- Utility: make links clickable ---
def links(text):
    url_pattern = r"(https?://[^\s]+)"
    return re.sub(url_pattern, r"<a href='\1' target='_blank'>\1</a>", text)

# --- Utility: save to CSV ---
def logs_save(question, answer, feedback=None):
    folder = "logs"
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, "chat_logs.csv")
    file_exists = os.path.isfile(filepath)

    with open(filepath, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["question", "answer", "feedback"])
        writer.writerow([question, answer, feedback or ""])

# --- Feedback callback ---
def feedback(key, value):
    st.session_state[key] = value
    idx = int(key.split("_")[1])
    if idx < len(st.session_state.messages):
        question = st.session_state.messages[idx - 1]["content"]
        answer = st.session_state.messages[idx]["content"]
        logs_save(question, answer, feedback=value)

# --- Init messages ---
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": system_prompt}]

# --- Show message history ---
for idx, msg in enumerate(st.session_state.messages[1:], start=1):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            feedback_key = f"feedback_{idx}"
            feedback_value = st.session_state.get(feedback_key)
            col1, col2 = st.columns([1, 1])
            with col1:
                st.button("👍", key=feedback_key+"_up", on_click=feedback,
                          args=[feedback_key, "up"], disabled=feedback_value is not None)
            with col2:
                st.button("👎", key=feedback_key+"_down", on_click=feedback,
                          args=[feedback_key, "down"], disabled=feedback_value is not None)
            if feedback_value == "up":
                st.success("Thanks for your feedback! 👍")
            elif feedback_value == "down":
                st.warning("Sorry to hear that! We'll improve. 👎")

# --- Input & Response ---
if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    if api_key:
        try:
            start_time = time.time()
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=st.session_state.messages
            )
            end_time = time.time()

            reply = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})

            linked_reply = links(reply).replace("\n", "<br>")

            with st.chat_message("assistant"):
                st.markdown(
                    f"<div style='font-size: 20px; line-height: 1.6;'>{linked_reply}</div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<p style='font-size: 14px; color: gray;'>⏱️ Response time: {end_time - start_time:.2f} seconds</p>",
                    unsafe_allow_html=True
                )

                feedback_key = f"feedback_{len(st.session_state.messages)-1}"
                feedback_value = st.session_state.get(feedback_key)
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.button("👍", key=feedback_key+"_up", on_click=feedback,
                              args=[feedback_key, "up"], disabled=feedback_value is not None)
                with col2:
                    st.button("👎", key=feedback_key+"_down", on_click=feedback,
                              args=[feedback_key, "down"], disabled=feedback_value is not None)
                if feedback_value == "up":
                    st.success("Thanks for your feedback! 👍")
                elif feedback_value == "down":
                    st.warning("Sorry to hear that! We'll improve. 👎")

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter your API key.")
