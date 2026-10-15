"""Public chat front end. Talks to the internal API (fai-api); holds no model credentials.

Safeguards: passcode gate, per-session question limit, input length limit.
"""
import hmac
import os
import uuid

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://fai-api")          # in-cluster service name
PASSCODE = os.getenv("APP_PASSCODE", "")
MAX_QUESTIONS = int(os.getenv("MAX_QUESTIONS", "20"))      # per browser session
MAX_CHARS = int(os.getenv("MAX_CHARS", "500"))
WELCOME = ("Welcome to the agentic chat on lending and KYC policy. "
           "Ask me about exposure limits, covenant reporting, approvals or sanctions screening. "
           "Do you have any questions today?")

st.set_page_config(page_title="Policy assistant", page_icon="💬")
st.title("Policy assistant")

# ---- passcode gate -------------------------------------------------------
if not PASSCODE:
    st.error("This app is not configured (no passcode set). Refusing to run.")
    st.stop()
if not st.session_state.get("ok"):
    code = st.text_input("Passcode", type="password")
    if code:
        if hmac.compare_digest(code.encode(), PASSCODE.encode()):
            st.session_state.ok = True
            st.rerun()
        else:
            st.error("Wrong passcode.")
    st.stop()

# ---- session state -------------------------------------------------------
st.session_state.setdefault("thread", str(uuid.uuid4()))
st.session_state.setdefault("asked", 0)
st.session_state.setdefault("history", [{"role": "assistant", "content": WELCOME}])

mode = st.sidebar.radio("Mode", ["Plain RAG (grounded)", "Agent (tools)"])
st.sidebar.caption(f"Questions used: {st.session_state.asked}/{MAX_QUESTIONS}")
st.sidebar.caption("Answers come only from the sample policy documents. Not advice.")

for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

q = st.chat_input("Ask a question")
if q:
    q = q.strip()[:MAX_CHARS]
    with st.chat_message("user"):
        st.markdown(q)
    st.session_state.history.append({"role": "user", "content": q})

    if st.session_state.asked >= MAX_QUESTIONS:
        reply = "You have reached the question limit for this session."
    else:
        st.session_state.asked += 1
        path = "/rag" if mode.startswith("Plain") else "/chat"
        try:
            r = requests.post(API_URL + path, json={"question": q, "thread_id": st.session_state.thread}, timeout=90)
            r.raise_for_status()
            d = r.json()
            reply = d.get("answer", "(no answer)")
            extra = d.get("sources") or d.get("tools_used")
            if extra:
                reply += f"\n\n*Sources/tools: {', '.join(map(str, extra))}*"
        except Exception as e:  # never show internals to the public
            reply = "Sorry, the service had a problem. Please try again in a moment."
            print("api error:", repr(e), flush=True)
    with st.chat_message("assistant"):
        st.markdown(reply)
    st.session_state.history.append({"role": "assistant", "content": reply})
