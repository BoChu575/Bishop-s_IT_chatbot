import streamlit as st
import html
import re
import time
import os
import csv
from groq import Groq

# --- Page setup ---
st.set_page_config(
    page_title="Bishop's IT Support", 
    page_icon="💻"
)

st.title("💬 Bishop's University IT Support")
st.markdown("Enter your question here...")

# --- API Key handling (completely secure) ---
api_key = ""

try:
    if hasattr(st, 'secrets') and "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    # No fallback key for security
    api_key = ""

# --- Sidebar with helpful information ---
with st.sidebar:
    st.header("🔗 Quick Help")
    st.markdown("""
    **Need immediate help?**
    
    📞 **Call IT Helpdesk:**  
    819-822-9600 ext. 2273
    
    📍 **Visit in person:**  
    Library Learning Commons, 1st Floor
    
    🎫 **Submit a ticket:**  
    [octopus.ubishops.ca](https://octopus.ubishops.ca/)
    """)
    
    st.header("📚 Quick Links")
    st.markdown("""
    - [🎓 Moodle Login](https://moodle.ubishops.ca/)
    - [🔑 Reset Password](https://passwordreset.microsoftonline.com/)
    - [📋 Support Tickets](https://octopus.ubishops.ca/)
    """)
    
    st.header("💡 Common Issues")
    st.info("""
    **Wi-Fi Problems?**  
    Connect to: **WIZABU**
    
    **Can't access Moodle?**  
    Try password reset first
    
    **Email issues?**  
    Use the password reset link
    """)
    
    st.markdown("---")
    
    # Move footer content to sidebar
    st.markdown("""
    💻 **Bishop's University IT Support Chatbot**
    
    For urgent issues or complex problems, contact IT Helpdesk directly
    
    📞 819-822-9600 ext. 2273  
    📍 Library Learning Commons, 1st Floor
    """)

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
            writer.writerow(["timestamp", "question", "answer", "feedback"])
        writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), question, answer, feedback or ""])

# --- Feedback callback ---
def feedback(key, value):
    st.session_state[key] = value
    idx = int(key.split("_")[1])
    if idx < len(st.session_state.messages):
        question = st.session_state.messages[idx - 1]["content"]
        answer = st.session_state.messages[idx]["content"]
        logs_save(question, answer, feedback=value)

# --- Initialize messages ---
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": system_prompt}]

# --- Show message history ---
for idx, msg in enumerate(st.session_state.messages[1:], start=1):
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(msg["content"])
            
            feedback_key = f"feedback_{idx}"
            feedback_value = st.session_state.get(feedback_key)
            
            col1, col2, col3 = st.columns([1, 1, 6])
            with col1:
                st.button("👍", key=feedback_key+"_up", on_click=feedback,
                          args=[feedback_key, "up"], disabled=feedback_value is not None,
                          help="This answer was helpful")
            with col2:
                st.button("👎", key=feedback_key+"_down", on_click=feedback,
                          args=[feedback_key, "down"], disabled=feedback_value is not None,
                          help="This answer needs improvement")
            
            if feedback_value == "up":
                st.success("Thanks for your feedback! 👍")
            elif feedback_value == "down":
                st.warning("Thanks for the feedback! We'll keep improving. 👎")

# --- Input & Response ---
if prompt := st.chat_input("Ask your IT question here... (e.g., 'Can't connect to Wi-Fi', 'Forgot Moodle password')"):
    if not api_key:
        st.error("🔧 The IT support chatbot is temporarily unavailable for maintenance.")
        st.info("""
        **Please contact IT support directly:**
        
        📞 **Call:** 819-822-9600 ext. 2273  
        📍 **Visit:** Library Learning Commons, 1st Floor  
        🎫 **Submit ticket:** [octopus.ubishops.ca](https://octopus.ubishops.ca/)
        """)
        st.stop()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    try:
        start_time = time.time()
        
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Looking up the best solution for you..."):
                client = Groq(api_key=api_key)
                response = client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=st.session_state.messages,
                    temperature=0.7,
                    max_tokens=1000
                )
            
            end_time = time.time()
            reply = response.choices[0].message.content
            
            st.session_state.messages.append({"role": "assistant", "content": reply})
            
            linked_reply = links(reply)
            st.markdown(linked_reply, unsafe_allow_html=True)
            
            st.caption(f"⏱️ Response time: {end_time - start_time:.1f}s")

            feedback_key = f"feedback_{len(st.session_state.messages)-1}"
            feedback_value = st.session_state.get(feedback_key)
            
            col1, col2, col3 = st.columns([1, 1, 6])
            with col1:
                st.button("👍", key=feedback_key+"_up", on_click=feedback,
                          args=[feedback_key, "up"], disabled=feedback_value is not None,
                          help="This answer was helpful")
            with col2:
                st.button("👎", key=feedback_key+"_down", on_click=feedback,
                          args=[feedback_key, "down"], disabled=feedback_value is not None,
                          help="This answer needs improvement")
            
            if feedback_value == "up":
                st.success("Thanks for your feedback! 👍")
            elif feedback_value == "down":
                st.warning("Thanks for the feedback! We'll keep improving. 👎")

    except Exception as e:
        with st.chat_message("assistant", avatar="🤖"):
            st.error("🔧 I'm having some technical difficulties right now. Please try again, or contact IT support directly if the issue persists.")
            
            st.info("""
            **Need immediate help?**
            
            📞 **Call:** 819-822-9600 ext. 2273  
            📍 **Visit:** Library Learning Commons, 1st Floor  
            🎫 **Submit ticket:** [octopus.ubishops.ca](https://octopus.ubishops.ca/)
            """)

# End of main content - no footer needed since it's moved to sidebar
