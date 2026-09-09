"""
Streamlit frontend for Mental Health Companion.
Provides interactive chat interface with emotion visualization.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, List, Any, Optional
import time

# Page configuration
st.set_page_config(
    page_title="Mental Health Companion",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
import os

API_URL = st.sidebar.text_input(
    "API URL",
    value=os.getenv("API_URL", "http://localhost:8000"),
    help="URL of the FastAPI backend",
)

UNCERTAIN_WARNING = (
    "I couldn't clearly detect a specific emotional state. "
    "As an AI designed for emotional support, I cannot provide medical advice. "
    "If you are experiencing physical symptoms, please consult a professional."
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "emotion_history" not in st.session_state:
    st.session_state.emotion_history = []
if "session_start" not in st.session_state:
    st.session_state.session_start = datetime.now()
if "journal_entries" not in st.session_state:
    st.session_state.journal_entries = []
if "mood_logs" not in st.session_state:
    st.session_state.mood_logs = []
if "jwt_token" not in st.session_state:
    st.session_state.jwt_token = None
if "current_user" not in st.session_state:
    st.session_state.current_user = None


def check_api_health() -> bool:
    """Check if API is available."""
    try:
        response = requests.get(f"{API_URL}/healthcheck", timeout=2)
        return response.status_code == 200 and response.json().get('model_loaded', False)
    except Exception:
        return False


def _auth_headers() -> Dict[str, str]:
    token = st.session_state.get("jwt_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def api_signup(email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
    try:
        resp = requests.post(
            f"{API_URL}/api/auth/signup",
            json={"email": email, "password": password, "full_name": full_name},
            timeout=60,
        )
        if resp.status_code >= 400:
            return {"ok": False, "error": resp.json().get("detail", "Signup failed")}
        return {"ok": True, "data": resp.json()}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": str(e)}


def api_login(email: str, password: str) -> Dict[str, Any]:
    try:
        resp = requests.post(
            f"{API_URL}/api/auth/login",
            json={"email": email, "password": password},
            timeout=60,
        )
        if resp.status_code >= 400:
            # FastAPI uses `detail` for errors
            detail = None
            try:
                detail = resp.json().get("detail")
            except Exception:
                detail = None
            return {"ok": False, "error": detail or "Login failed"}
        return {"ok": True, "data": resp.json()}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": str(e)}


def api_me() -> Dict[str, Any]:
    try:
        resp = requests.get(
            f"{API_URL}/api/auth/me",
            headers=_auth_headers(),
            timeout=60,
        )
        if resp.status_code >= 400:
            return {"ok": False, "error": "Not authenticated"}
        return {"ok": True, "data": resp.json()}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": str(e)}


def render_auth_gate() -> bool:
    """
    Returns True if authenticated and dashboard can render.
    Otherwise renders login/signup UI and returns False.
    """
    # Validate stored token once per run
    if st.session_state.get("jwt_token") and not st.session_state.get("current_user"):
        me = api_me()
        if me.get("ok"):
            st.session_state.current_user = me["data"]
        else:
            st.session_state.jwt_token = None
            st.session_state.current_user = None

    if st.session_state.get("jwt_token") and st.session_state.get("current_user"):
        return True

    st.markdown(
        """
        <div class="soft-card">
          <h2 style="margin:0; color:#4f46e5;">Welcome</h2>
          <p style="margin:0.25rem 0 0; color:#475569;">
            Please sign up or log in to continue to your dashboard.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, signup_tab = st.tabs(["Log in", "Sign up"])

    with login_tab:
        st.subheader("Log in")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log in", type="primary"):
            result = api_login(email=email.strip(), password=password)
            if result.get("ok"):
                token = result["data"].get("access_token")
                st.session_state.jwt_token = token
                me = api_me()
                if me.get("ok"):
                    st.session_state.current_user = me["data"]
                st.success("Logged in successfully.")
                st.rerun()
            else:
                st.error(result.get("error", "Login failed"))

    with signup_tab:
        st.subheader("Sign up")
        full_name = st.text_input("Full name (optional)", key="signup_full_name")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password (min 6 chars)", type="password", key="signup_password")
        if st.button("Create account", type="primary"):
            result = api_signup(
                email=email.strip(),
                password=password,
                full_name=full_name.strip() if full_name else None,
            )
            if result.get("ok"):
                st.success("Account created. Please log in.")
            else:
                st.error(result.get("error", "Signup failed"))

    st.info("Tip: Make sure the backend is running at the API URL shown in the sidebar.")
    return False


def predict_emotion(text: str) -> Dict:
    """Send prediction request to API."""
    try:
        response = requests.post(
            f"{API_URL}/predict",
            json={"text": text},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {e}")
        return None


def chat_with_therapist(
    message: str, history: Optional[List[Dict[str, Any]]] = None
) -> Dict:
    """
    Call the richer /api/chat endpoint if available,
    otherwise gracefully fall back to /predict.
    """
    try:
        # Try new chat endpoint
        payload: Dict[str, Any] = {"message": message}
        if history:
            payload["history"] = [{"role": m["role"], "content": m["content"]} for m in history]

        resp = requests.post(f"{API_URL}/api/chat", json=payload, timeout=8)
        if resp.status_code == 404:
            # Backend not yet upgraded – fall back to simple prediction
            basic = predict_emotion(message)
            if not basic:
                return {}
            return {
                "status": "success",
                "state": "confident",
                "emotion": basic["emotion"],
                "confidence_score": basic["confidence"],
                "probabilities": basic["probabilities"],
                "cbt_techniques": [],
                "recommendation": basic["recommendation"],
                "reply": (
                    f"I understand you're feeling {basic['emotion'].capitalize()}. "
                    f"{basic['explanation']} {basic['recommendation']}"
                ),
                "timestamp": basic.get("timestamp", datetime.now().isoformat()),
            }

        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "success":
            return {}
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to chat API: {e}")
        return {}


def get_emotion_color(emotion: str) -> str:
    """Get color for emotion visualization."""
    colors = {
        'joy': '#FFD700',
        'sadness': '#4169E1',
        'anger': '#FF4500',
        'fear': '#9370DB',
        'disgust': '#8B4513',
        'surprise': '#FF69B4',
        'stress': '#fb923c',
    }
    return colors.get(emotion.lower(), '#808080')


def display_sidebar():
    """Display sidebar with information and controls."""
    st.sidebar.title("💚 Mental Health Companion")
    st.sidebar.markdown("---")
    
    # API status
    api_healthy = check_api_health()
    if api_healthy:
        st.sidebar.success("✅ API Connected")
    else:
        st.sidebar.error("❌ API Not Available")
        st.sidebar.info("Please ensure the FastAPI backend is running.")
    
    st.sidebar.markdown("---")
    
    # Session info
    st.sidebar.subheader("Session Info")
    session_duration = datetime.now() - st.session_state.session_start
    st.sidebar.write(f"Duration: {str(session_duration).split('.')[0]}")
    st.sidebar.write(f"Messages: {len(st.session_state.messages)}")
    
    # Clear session
    if st.sidebar.button("Clear Session", type="secondary"):
        st.session_state.messages = []
        st.session_state.emotion_history = []
        st.session_state.session_start = datetime.now()
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # About
    st.sidebar.subheader("About")
    st.sidebar.info(
        "This AI companion uses DistilBERT to recognize emotions and provide "
        "evidence-based recommendations. It's designed to support, not replace, "
        "professional mental health care."
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("⚠️ Not a substitute for professional help")


def log_mood_api(mood: str, emoji: Optional[str], note: Optional[str]):
    """Send mood log to backend (best-effort)."""
    user = st.session_state.get("current_user") or {}
    payload = {
        "user_id": user.get("id"),
        "mood": mood,
        "emoji": emoji,
        "note": note,
    }
    try:
        requests.post(f"{API_URL}/api/mood-log", json=payload, timeout=5)
    except requests.exceptions.RequestException:
        # Silent fail – UI still tracks mood in session state.
        pass


def fetch_mood_logs_api(period: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch mood logs for the current user from the backend."""
    user = st.session_state.get("current_user") or {}
    params: Dict[str, Any] = {"limit": 500}
    if user.get("id"):
        params["user_id"] = user["id"]
    if period:
        params["period"] = period
    try:
        resp = requests.get(f"{API_URL}/api/mood-log", params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items") or []
        # Normalize datetimes for plotting
        for it in items:
            if isinstance(it.get("created_at"), str):
                it["created_at"] = it["created_at"]
        return items
    except requests.exceptions.RequestException:
        return []


def fetch_personalized_recommendations_api(timeframe_days: int = 30) -> Dict[str, Any]:
    """Fetch personalized recommendations for the current user."""
    user = st.session_state.get("current_user") or {}
    user_id = user.get("id")
    if not user_id:
        return {}
    try:
        resp = requests.get(
            f"{API_URL}/api/recommendations/personalized",
            params={"user_id": user_id, "timeframe_days": timeframe_days},
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException:
        return {}


def analyze_journal_api(content: str) -> Dict:
    """Submit journal entry for analysis."""
    try:
        resp = requests.post(
            f"{API_URL}/api/journal",
            json={"content": content},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error analyzing journal entry: {e}")
        return {}


def get_emotion_analytics_api() -> Dict:
    """Fetch aggregated emotion analytics for dashboard."""
    try:
        resp = requests.get(f"{API_URL}/api/emotion-analysis", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException:
        return {}


def display_emotion_chart():
    """Display emotion distribution chart."""
    if not st.session_state.emotion_history:
        return
    
    df = pd.DataFrame(st.session_state.emotion_history)
    
    # Emotion distribution pie chart
    emotion_counts = df['emotion'].value_counts()
    
    fig_pie = px.pie(
        values=emotion_counts.values,
        names=emotion_counts.index,
        title="Emotion Distribution",
        color=emotion_counts.index,
        color_discrete_map={emotion: get_emotion_color(emotion) for emotion in emotion_counts.index}
    )
    fig_pie.update_layout(showlegend=True, height=300)
    
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Emotion timeline
    if len(df) > 1:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        fig_line = go.Figure()
        
        for emotion in df['emotion'].unique():
            emotion_df = df[df['emotion'] == emotion]
            fig_line.add_trace(go.Scatter(
                x=emotion_df['timestamp'],
                y=emotion_df['confidence'],
                mode='lines+markers',
                name=emotion,
                line=dict(color=get_emotion_color(emotion), width=2),
                marker=dict(size=8)
            ))
        
        fig_line.update_layout(
            title="Emotion Confidence Over Time",
            xaxis_title="Time",
            yaxis_title="Confidence",
            height=300,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_line, use_container_width=True)


def render_breathing_module():
    """Guided breathing and relaxation module."""
    st.subheader("🫁 Guided Breathing & Relaxation")
    st.markdown(
        "Use these short, structured exercises to help your body and mind slow down. "
        "These are general wellness tools and not a replacement for medical care."
    )

    col_a, col_b = st.columns(2)

    with col_a:
        pattern = st.selectbox(
            "Choose a breathing pattern",
            [
                "Box Breathing (4-4-4-4)",
                "4-7-8 Relaxation",
                "Calm Counting (5-5)",
            ],
        )
        duration_min = st.slider("Session length (minutes)", 1, 10, 3)

        if st.button("Start Breathing Session"):
            total_seconds = duration_min * 60
            step = 0
            start = time.time()
            placeholder = st.empty()

            st.info(
                "Follow the instructions on screen. "
                "You can stop anytime if you feel uncomfortable."
            )

            while time.time() - start < total_seconds:
                if pattern == "Box Breathing (4-4-4-4)":
                    phases = [("Inhale", 4), ("Hold", 4), ("Exhale", 4), ("Hold", 4)]
                elif pattern == "4-7-8 Relaxation":
                    phases = [("Inhale", 4), ("Hold", 7), ("Exhale", 8)]
                else:
                    phases = [("Inhale", 5), ("Exhale", 5)]

                phase_name, seconds = phases[step % len(phases)]
                for remaining in range(seconds, 0, -1):
                    placeholder.markdown(
                        f"<div style='text-align:center; font-size:2rem;'>"
                        f"<strong>{phase_name}</strong><br/>{remaining}s"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    time.sleep(1)

                step += 1

            placeholder.empty()
            st.success("Breathing session complete. Notice how your body feels now.")

    with col_b:
        st.markdown("### Visual Breathing Cue")
        st.markdown(
            """
            <style>
            .breathing-circle {
                width: 160px;
                height: 160px;
                border-radius: 50%;
                margin: 2rem auto;
                background: radial-gradient(circle at 30% 30%, #a5b4fc, #4f46e5);
                animation: breathe 8s ease-in-out infinite;
                box-shadow: 0 0 40px rgba(79, 70, 229, 0.5);
            }
            @keyframes breathe {
                0% { transform: scale(0.85); opacity: 0.7; }
                50% { transform: scale(1.1); opacity: 1; }
                100% { transform: scale(0.85); opacity: 0.7; }
            }
            </style>
            <div class="breathing-circle"></div>
            <p style="text-align:center; color:#555;">
            Match your breath to the circle: breathe in as it expands, out as it contracts.
            </p>
            """,
            unsafe_allow_html=True,
        )


def render_medical_assistance_panel(symptom_support: Optional[Dict[str, Any]]):
    """Medical Assistance Panel embedded in chat responses."""
    if not symptom_support:
        return

    st.markdown("#### 🏥 Medical Assistance Panel")

    cols = st.columns(3)

    with cols[0]:
        st.markdown("**Detected Condition(s)**")
        for cond in symptom_support.get("detected_conditions", []):
            st.markdown(f"- **{cond['name']}** ({cond['likelihood']})")
            st.caption(cond["explanation"])

    with cols[1]:
        st.markdown("**Coping / First-Aid Techniques**")
        for technique in symptom_support.get("coping_techniques", []):
            with st.expander(technique["title"]):
                for step in technique["steps"]:
                    st.markdown(f"- {step}")

    with cols[2]:
        st.markdown("**Nearby Support & Emergency Contacts**")
        for loc in symptom_support.get("nearby_support", []):
            st.markdown(
                f"**{loc['name']}** ({loc['type'].title()})  \n"
                f"{loc['address']}  \n"
                f"{loc.get('contact_number', 'Contact: N/A')}  \n"
                f"{loc.get('distance_km', '?')} km away (approx.)"
            )
            st.markdown("---")

        st.markdown("**Emergency Contacts**")
        for ec in symptom_support.get("emergency_contacts", []):
            st.markdown(f"- **{ec['name']}**: {ec['number']}")
            if ec.get("description"):
                st.caption(ec["description"])

    st.warning(symptom_support.get("disclaimer", ""), icon="⚠️")


def main():
    """Main application."""
    # Custom CSS
    st.markdown(
        """
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #4f46e5;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .soft-card {
            background: linear-gradient(135deg, #f5f3ff, #eff6ff);
            border-radius: 1rem;
            padding: 1.25rem 1.5rem;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.06);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header
    st.markdown(
        '<h1 class="main-header">💚 AI-Powered Mental Health Companion</h1>',
        unsafe_allow_html=True,
    )

    # Auth gate (login/signup before dashboard loads)
    if not render_auth_gate():
        return

    # Sidebar
    display_sidebar()
    user = st.session_state.get("current_user")
    if user:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Account")
        st.sidebar.write(user.get("email", ""))
        if user.get("full_name"):
            st.sidebar.caption(user.get("full_name"))
        if st.sidebar.button("Log out"):
            st.session_state.jwt_token = None
            st.session_state.current_user = None
            st.rerun()

    # Check API health
    if not check_api_health():
        st.warning(
            "⚠️ The API backend is not available. Please start the FastAPI server:\n\n"
            "```bash\nuvicorn src.api.main:app --host 0.0.0.0 --port 8000\n```"
        )
        return

    # Load mood history from backend once after login (no UI change).
    if st.session_state.get("current_user") and not st.session_state.get(
        "_mood_logs_loaded"
    ):
        st.session_state.mood_logs = fetch_mood_logs_api(period=None) or []
        st.session_state._mood_logs_loaded = True

    chat_tab, analytics_tab, journal_tab, wellness_tab = st.tabs(
        ["💬 Chat Therapist", "📊 Mood Dashboard", "📓 Journal", "🧘 Wellness"]
    )

    with chat_tab:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Conversational Support")

            # Display chat history
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

                    if message["role"] == "assistant":
                        emotion_data = message.get("emotion_data")
                        if emotion_data:
                            state = (emotion_data.get("state") or "").lower()
                            is_uncertain = state == "uncertain"
                            if not is_uncertain:
                                emotion = emotion_data.get("emotion", "unknown")
                                confidence = emotion_data.get("confidence_score", 0)
                                color = get_emotion_color(emotion)
                                st.markdown(
                                    f"<div style='background-color: {color}20; padding: 0.5rem; "
                                    f"border-radius: 0.5rem; margin-top: 0.5rem;'>"
                                    f"<strong>Detected Emotion:</strong> {emotion.capitalize()} "
                                    f"(Confidence: {confidence:.1%})</div>",
                                    unsafe_allow_html=True,
                                )
                                st.metric("Model Confidence", f"{confidence:.1%}")
                                st.progress(float(confidence))
                                if emotion_data.get("recommendation"):
                                    st.info(f"💡 **Suggestion:** {emotion_data['recommendation']}")

                        symptom_support = message.get("symptom_support")
                        if symptom_support and (emotion_data or {}).get("state") != "uncertain":
                            render_medical_assistance_panel(symptom_support)

            user_input = st.chat_input("Share how you're feeling today...")

            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})

                with st.chat_message("user"):
                    st.write(user_input)

                with st.chat_message("assistant"):
                    with st.spinner("Listening carefully and analyzing your message..."):
                        result = chat_with_therapist(
                            user_input,
                            history=st.session_state.messages,
                        )

                    if result:
                        # Track emotion history
                        is_uncertain = (result.get("state") or "").lower() == "uncertain"
                        if not is_uncertain:
                            st.session_state.emotion_history.append(
                                {
                                    "emotion": result.get("emotion", "unknown"),
                                    "confidence": result.get("confidence_score", 0),
                                    "timestamp": result.get("timestamp", datetime.utcnow().isoformat()),
                                }
                            )

                        response_text = result.get("message") if is_uncertain else result.get("reply", "")
                        st.write(response_text)

                        # CBT techniques
                        techniques = result.get("cbt_techniques") or []
                        if techniques and not is_uncertain:
                            with st.expander("View CBT-based coping ideas"):
                                for t in techniques:
                                    st.markdown(f"- {t}")

                        # Crisis message & emergency banner
                        if result.get("crisis_detected"):
                            st.error(
                                result.get(
                                    "crisis_message",
                                    "There may be signs of crisis in this message. "
                                    "Please consider reaching out for immediate human support.",
                                )
                            )

                        # Medical assistance panel
                        if result.get("symptom_support") and not is_uncertain:
                            render_medical_assistance_panel(result["symptom_support"])

                        if not is_uncertain:
                            confidence_score = float(result.get("confidence_score", 0))
                            st.metric("Model Confidence", f"{confidence_score:.1%}")
                            st.progress(confidence_score)
                            with st.expander("View emotion probabilities"):
                                prob_df = pd.DataFrame(
                                    list((result.get("probabilities") or {}).items()),
                                    columns=["Emotion", "Probability"],
                                )
                                prob_df = prob_df.sort_values("Probability", ascending=False)
                                prob_df["Probability"] = prob_df["Probability"].apply(
                                    lambda x: f"{x:.1%}"
                                )
                                st.dataframe(prob_df, use_container_width=True, hide_index=True)

                        # Persist assistant message
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": response_text,
                                "emotion_data": result,
                                "symptom_support": result.get("symptom_support") if not is_uncertain else None,
                            }
                        )
                    else:
                        st.error(
                            "Sorry, I couldn't process your message right now. Please try again."
                        )

        with col2:
            st.subheader("Quick Mood Check-In")
            mood_choice = st.slider(
                "Overall mood right now",
                min_value=1,
                max_value=5,
                value=3,
                format="%d",
                help="1 = very low, 5 = very high",
            )
            emoji_map = {1: "😞", 2: "😔", 3: "😐", 4: "🙂", 5: "😄"}
            selected_emoji = emoji_map[mood_choice]
            st.markdown(f"**Mood emoji:** {selected_emoji}")

            note = st.text_input("Optional note about your mood")

            if st.button("Log Mood"):
                mood_label_map = {
                    1: "very_low",
                    2: "low",
                    3: "neutral",
                    4: "high",
                    5: "very_high",
                }
                entry = {
                    "mood": mood_label_map[mood_choice],
                    "emoji": selected_emoji,
                    "note": note,
                    "created_at": datetime.utcnow().isoformat(),
                }
                st.session_state.mood_logs.append(entry)
                log_mood_api(entry["mood"], entry["emoji"], entry["note"])
                st.success("Mood logged for your personal dashboard.")

    with analytics_tab:
        st.subheader("Mood & Emotion Analytics")

        if not st.session_state.emotion_history and not st.session_state.mood_logs:
            st.info("Start a conversation or log your mood to see analytics here.")
        else:
            col_a, col_b = st.columns([2, 1])

            with col_a:
                if st.session_state.emotion_history:
                    st.markdown("#### Emotion Trends")
                    display_emotion_chart()

            with col_b:
                st.markdown("#### Mood Check-Ins")
                range_choice = st.selectbox(
                    "History range",
                    ["All", "Weekly", "Monthly"],
                    index=0,
                    key="mood_range_choice",
                )
                period = None
                if range_choice == "Weekly":
                    period = "week"
                elif range_choice == "Monthly":
                    period = "month"
                if st.button("Refresh mood history"):
                    st.session_state.mood_logs = fetch_mood_logs_api(period=period) or []

                if st.session_state.mood_logs:
                    df_mood = pd.DataFrame(st.session_state.mood_logs)
                    df_mood["created_at"] = pd.to_datetime(df_mood["created_at"])
                    df_mood = df_mood.sort_values("created_at")

                    mood_score_map = {
                        "very_low": 1,
                        "low": 2,
                        "neutral": 3,
                        "high": 4,
                        "very_high": 5,
                    }
                    df_mood["score"] = df_mood["mood"].map(mood_score_map)

                    fig = px.line(
                        df_mood,
                        x="created_at",
                        y="score",
                        markers=True,
                        title="Mood Over Time",
                    )
                    fig.update_yaxes(
                        tickvals=[1, 2, 3, 4, 5],
                        ticktext=["Very Low", "Low", "Neutral", "High", "Very High"],
                    )
                    st.plotly_chart(fig, use_container_width=True)

                analytics = get_emotion_analytics_api()
                if analytics:
                    st.markdown("#### Weekly Insights")
                    notes = analytics.get("notes") or []
                    if notes:
                        for n in notes:
                            st.markdown(f"- {n}")
                    else:
                        st.caption(
                            "As more entries are added, this panel will highlight emotional patterns for you."
                        )

                recs_payload = fetch_personalized_recommendations_api(timeframe_days=30)
                recs = recs_payload.get("recommendations") if recs_payload else None
                if recs:
                    st.markdown("#### Personalized Suggestions")
                    for r in recs:
                        title = r.get("title", "Suggestion")
                        desc = r.get("description", "")
                        actions = r.get("actions") or []
                        severity = (r.get("severity") or "info").lower()

                        if severity == "warning":
                            st.warning(f"**{title}**\n\n{desc}")
                        else:
                            st.info(f"**{title}**\n\n{desc}")

                        if actions:
                            with st.expander("Action steps"):
                                for a in actions:
                                    st.markdown(f"- {a}")

    with journal_tab:
        st.subheader("Private Mental Health Journal")
        st.markdown(
            "Use this space to write freely about your experiences. "
            "Entries in this demo are stored only in this session. "
            "In production, they should be encrypted and protected."
        )

        journal_text = st.text_area(
            "Today's entry",
            height=200,
            placeholder="Write about your day, feelings, or anything on your mind...",
        )

        if st.button("Save & Analyze Entry") and journal_text.strip():
            entry = {
                "content": journal_text,
                "created_at": datetime.utcnow().isoformat(),
            }
            st.session_state.journal_entries.append(entry)
            with st.spinner("Analyzing patterns in this entry..."):
                insight = analyze_journal_api(journal_text)

            st.success("Entry saved for this session.")

            if insight:
                st.markdown("#### Emotional Summary")
                st.write(insight.get("summary", ""))

                patterns = insight.get("patterns") or []
                if patterns:
                    st.markdown("#### Noticed Patterns")
                    for p in patterns:
                        st.markdown(f"- {p}")

        if st.session_state.journal_entries:
            st.markdown("#### Recent Entries (Session Only)")
            for e in reversed(st.session_state.journal_entries[-5:]):
                with st.expander(e["created_at"]):
                    st.write(e["content"])

    with wellness_tab:
        render_breathing_module()

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "This tool is for informational purposes only and is not a substitute for professional mental health care. "
        "If you're experiencing a mental health crisis, please contact a mental health professional or emergency services."
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

