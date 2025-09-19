import os
import time
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE_URL = os.getenv(
    "BASE_URL",
    "https://gemini-backend-clone-assignment-6s5j.onrender.com"
)

st.set_page_config(page_title="Gemini Backend Frontend", page_icon="✨", layout="wide")


POLL_INTERVAL_SEC = 0.5     
POLL_ATTEMPTS_SEND = 80     
POLL_ATTEMPTS_REFRESH = 60   


if "base_url" not in st.session_state:
    st.session_state.base_url = DEFAULT_BASE_URL
if "token" not in st.session_state:
    st.session_state.token = ""
if "mobile" not in st.session_state:
    st.session_state.mobile = ""
if "chatrooms" not in st.session_state:
    st.session_state.chatrooms = []
if "selected_chatroom_id" not in st.session_state:
    st.session_state.selected_chatroom_id = None
if "_last_otp" not in st.session_state:
    st.session_state._last_otp = ""

if "waiting_reply" not in st.session_state:
    st.session_state.waiting_reply = False

if "pending_user_msg_id" not in st.session_state:
    st.session_state.pending_user_msg_id = 0

if "msg_input" not in st.session_state:
    st.session_state.msg_input = ""

if "clear_input_next_run" not in st.session_state:
    st.session_state.clear_input_next_run = False


def _headers(require_auth: bool = False):
    h = {"Content-Type": "application/json"}
    if require_auth and st.session_state.token:
        h["Authorization"] = f"Bearer {st.session_state.token}"
    return h


def api(method: str, path: str, json=None, params=None, require_auth=False, timeout=25):
    url = st.session_state.base_url.rstrip("/") + path
    try:
        resp = requests.request(
            method, url, headers=_headers(require_auth), json=json, params=params, timeout=timeout
        )
        ct = resp.headers.get("content-type", "")
        data = resp.json() if ct.startswith("application/json") else {"raw": resp.text}
        if not resp.ok:
            return None, f"{resp.status_code} {data}"
        return data, None
    except Exception as e:
        return None, str(e)


def refresh_chatrooms():
    data, err = api("GET", "/chatroom", require_auth=True)
    if err:
        st.error(err)
        return
    st.session_state.chatrooms = (data.get("data") or {}).get("chatrooms", [])


def poll_for_reply(chatroom_id: int, after_msg_id: int, attempts: int, status_ph=None) -> bool:
    """Poll chatroom detail until an assistant message with id > after_msg_id appears."""
    for i in range(attempts):
        if status_ph and i % 4 == 0:  # update UI every ~2s
            status_ph.info("Waiting for assistant reply…")
        time.sleep(POLL_INTERVAL_SEC)
        d2, e2 = api("GET", f"/chatroom/{chatroom_id}", require_auth=True)
        if e2:
            continue
        msgs2 = ((d2.get("data") or {}).get("chatroom") or {}).get("messages", [])
        newer_assist = [
            m for m in msgs2
            if (m.get("role") or "").lower() != "user" and int(m.get("id") or 0) > int(after_msg_id or 0)
        ]
        if newer_assist:
            return True
    return False


# ---------------- Sidebar ----------------
st.sidebar.header("Settings")
st.sidebar.text_input("Backend Base URL", key="base_url", help="e.g., http://localhost:8010")
if st.sidebar.button("Ping API", key="btn_ping_api"):
    data, err = api("GET", "/")
    if err:
        st.sidebar.error(err)
    else:
        st.sidebar.success("API reachable")
        st.sidebar.json(data)

st.sidebar.header("Auth")
with st.sidebar.form("form_send_otp"):
    st.text_input("Mobile", key="mobile", placeholder="9876543210")
    send_clicked = st.form_submit_button("Send OTP")
    if send_clicked:
        if not st.session_state.mobile.strip():
            st.sidebar.error("Enter a mobile number first.")
        else:
            data, err = api("POST", "/auth/send-otp", json={"mobile": st.session_state.mobile})
            if err:
                st.sidebar.error(err)
            else:
                otp = (data.get("data") or {}).get("otp", "")
                st.session_state._last_otp = otp
                st.sidebar.success(f"OTP (mock): {otp}")

with st.sidebar.form("form_verify_otp", clear_on_submit=False):
    otp_input = st.text_input("OTP", key="otp_input", value=st.session_state._last_otp)
    verify_clicked = st.form_submit_button("Verify OTP")
    if verify_clicked:
        if not st.session_state.mobile.strip():
            st.sidebar.error("Enter a mobile number first.")
        elif not otp_input.strip():
            st.sidebar.error("Enter the OTP.")
        else:
            payload = {"mobile": st.session_state.mobile, "otp": otp_input}
            data, err = api("POST", "/auth/verify-otp", json=payload)
            if err:
                st.sidebar.error(err)
            else:
                st.session_state.token = data.get("access_token", "")
                if st.session_state.token:
                    st.sidebar.success("Logged in!")
                    st.rerun()
                else:
                    st.sidebar.error("No token received")

if st.session_state.token:
    if st.sidebar.button("Logout", key="btn_logout"):
        st.session_state.token = ""
        st.session_state.selected_chatroom_id = None
        st.session_state.waiting_reply = False
        st.session_state.pending_user_msg_id = 0
        st.session_state.clear_input_next_run = True
        st.sidebar.success("Logged out")
        st.rerun()

if st.session_state.token:
    data, err = api("GET", "/user/me", require_auth=True)
    if not err and data:
        user = (data.get("data") or {}).get("user", {})
        st.sidebar.caption(f"User: **{user.get('mobile','?')}** | Tier: **{user.get('tier','?')}**")

    st.sidebar.header("Subscription")
    c1, c2 = st.sidebar.columns(2)
    with c1:
        if st.button("Check Status", key="btn_check_status"):
            data, err = api("GET", "/subscription/status", require_auth=True)
            st.sidebar.success(f"{data.get('tier')} ({data.get('status')})") if not err else st.sidebar.error(err)
    with c2:
        if st.button("Go Pro → Checkout", key="btn_checkout"):
            data, err = api("POST", "/subscribe/pro", require_auth=True)
            if err:
                st.sidebar.error(err)
            else:
                url = (data.get("data") or {}).get("checkout_url")
                if url:
                    st.sidebar.markdown(f"[Open Stripe Checkout]({url})", unsafe_allow_html=True)
                else:
                    st.sidebar.error("No checkout_url returned")


st.title("Gemini Backend — Streamlit Frontend")

st.header("Chatrooms")
if not st.session_state.token:
    st.info("Login to manage chatrooms.")
else:
    with st.expander("Create chatroom", expanded=False):
        title = st.text_input("Title", key="new_room_title", placeholder="My Room")
        if st.button("Create", key="btn_create_chatroom"):
            payload = {"title": title or "Untitled"}
            data, err = api("POST", "/chatroom", json=payload, require_auth=True)
            if err:
                st.error(err)
            else:
                st.success("Chatroom created")
                st.session_state.chatrooms = []

left, right = st.columns([1, 2])

with left:
    if st.session_state.token:
        if not st.session_state.chatrooms:
            refresh_chatrooms()
        st.subheader("Your Rooms")
        for r in st.session_state.chatrooms:
            rid = r.get("id")
            label = f"{rid} — {r.get('title')}"
            if st.button(label, key=f"btn_room_{rid}"):
                st.session_state.selected_chatroom_id = rid
                st.session_state.pending_user_msg_id = 0
                st.session_state.waiting_reply = False
                st.session_state.clear_input_next_run = True
                st.rerun()

with right:
    rid = st.session_state.selected_chatroom_id
    if st.session_state.token and rid:
        st.subheader(f"Room #{rid}")
        detail, err = api("GET", f"/chatroom/{rid}", require_auth=True)
        if err:
            st.error(err)
        else:
            chat = (detail.get("data") or {}).get("chatroom", {})
            msgs = chat.get("messages", [])


            if st.session_state.clear_input_next_run:
                st.session_state.msg_input = ""
                st.session_state.clear_input_next_run = False


            for m in msgs:
                role = (m.get("role") or "assistant").lower()
                content = (m.get("content") or "").strip()
                if role == "user":
                    st.chat_message("user").write(content)
                else:
                    st.chat_message("assistant").write(content)

 
            status_ph = st.empty()

  
            with st.form("form_send_message"):
                prompt = st.text_input("Your message", key="msg_input")
                send_clicked = st.form_submit_button("Send")

 
            if send_clicked and prompt.strip():
                if st.session_state.waiting_reply:
                    status_ph.info("Still processing the previous message…")
                else:
                    st.session_state.waiting_reply = True
                    payload = {"content": prompt.strip()}
                    resp, err = api("POST", f"/chatroom/{rid}/message", json=payload, require_auth=True)
                    if err:
                        status_ph.error(err)
                        st.session_state.waiting_reply = False
                    else:
                        user_msg_id = int(((resp.get("data") or {}).get("message_id")) or 0)
                        st.session_state.pending_user_msg_id = user_msg_id
                        status_ph.success("Queued! Waiting for assistant reply…")

                        got = poll_for_reply(rid, user_msg_id, attempts=POLL_ATTEMPTS_SEND, status_ph=status_ph)
                        st.session_state.waiting_reply = False
                        if got:
                        
                            st.session_state.pending_user_msg_id = 0
                            st.session_state.clear_input_next_run = True
                            st.rerun()
                        else:
                            status_ph.info("Still processing… click Refresh to keep waiting.")

            if st.button("Refresh", key="btn_refresh_room"):
                if st.session_state.pending_user_msg_id:
                    status_ph.info("Checking for the pending assistant reply…")
                    got = poll_for_reply(
                        rid,
                        st.session_state.pending_user_msg_id,
                        attempts=POLL_ATTEMPTS_REFRESH,
                        status_ph=status_ph,
                    )
                    if got:
                        st.session_state.pending_user_msg_id = 0
                        st.session_state.clear_input_next_run = True
                        st.rerun()
                    else:
                        status_ph.info("Still processing… try again shortly.")
                else:
                    st.rerun()
    else:
        st.info("Select a chatroom to view and chat.")
