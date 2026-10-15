import requests
import streamlit as st

API= "http://localhost:8000"

st.title("Agentic Chat on Covenants and Lending Policy")
mode = st.radio("Mode", ["Agent (use tools)", "Plain RAG"], horizontal=True)

WELCOME = ("Welcome to the agentic chat on covenants and lending policy. "
           "What questions do you have today?")
if "history" not in st.session_state:
    st.session_state.history = [("assistant", WELCOME)]



for role, text in st.session_state.history:
    st.chat_message(role).write(text)

if q := st.chat_input("Ask a question"):
    st.session_state.history.append(("user", q))
    st.chat_message("user").write(q)
    path = "/chat" if mode.startswith("Agent") else "/rag"
    r = requests.post(API + path, json={"question": q, "thread_id": "ui"}, timeout=180)
    if r.ok:
        d = r.json()
        extra = f"\n\n_Tools: {d.get('tools_used')}_" if "tools_used" in d else f"\n\n_Sources: {d.get('sources')}_"
        ans = d["answer"] + extra
    else:
        ans = f"Error {r.status_code}: {r.text[:300]}"
    st.session_state.history.append(("assistant", ans))
    st.chat_message("assistant").write(ans)