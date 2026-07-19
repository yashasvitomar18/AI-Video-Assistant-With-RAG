import streamlit as st
import streamlit.components.v1 as components
import time
from dotenv import load_dotenv
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Theme State ────────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "light"  # soft pink by default

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

IS_DARK = st.session_state.theme == "dark"

# ─── Theme Tokens ───────────────────────────────────────────────────────────────
if IS_DARK:
    # Monochrome dark mode — black canvas, white ink, a whisper of pink for life
    TOKENS = {
        "bg":            "#080808",
        "bg-2":          "#0f0f0f",
        "bg-3":          "#141414",
        "surface":       "#121212",
        "surface-2":     "#1a1a1a",
        "surface-3":     "#1f1f1f",
        "border":        "#2b2b2b",
        "accent":        "#f472b6",
        "accent-glow":   "#f9a8d4",
        "accent-2":      "#ffffff",
        "text":          "#f4f4f5",
        "text-muted":    "#93939c",
        "success":       "#34d399",
        "warning":       "#fbbf24",
        "danger":        "#f87171",
        "btn-start":     "#f472b6",
        "btn-end":       "#be185d",
        "grid-rgba":     "rgba(244, 114, 182, 0.035)",
    }
else:
    # Pale, professional blush — restrained, portfolio-ready
    TOKENS = {
        "bg":            "#fdf3f6",
        "bg-2":          "#faeaf0",
        "bg-3":          "#f7e1e9",
        "surface":       "#ffffff",
        "surface-2":     "#fbeef3",
        "surface-3":     "#f5e3ea",
        "border":        "#eed7de",
        "accent":        "#9d174d",
        "accent-glow":   "#b5306a",
        "accent-2":      "#701a3f",
        "text":          "#241a1f",
        "text-muted":    "#7d6570",
        "success":       "#0d9488",
        "warning":       "#b45309",
        "danger":        "#be123c",
        "btn-start":     "#9d174d",
        "btn-end":       "#701a3f",
        "grid-rgba":     "rgba(157, 23, 77, 0.035)",
    }

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Fraunces:opsz,wght@9..144,500;9..144,600&family=JetBrains+Mono:wght@300;400;500&display=swap');

/* ── Root Variables ── */
:root {{
    --bg: {TOKENS['bg']};
    --bg-2: {TOKENS['bg-2']};
    --bg-3: {TOKENS['bg-3']};
    --surface: {TOKENS['surface']};
    --surface-2: {TOKENS['surface-2']};
    --surface-3: {TOKENS['surface-3']};
    --border: {TOKENS['border']};
    --accent: {TOKENS['accent']};
    --accent-glow: {TOKENS['accent-glow']};
    --accent-2: {TOKENS['accent-2']};
    --text: {TOKENS['text']};
    --text-muted: {TOKENS['text-muted']};
    --success: {TOKENS['success']};
    --warning: {TOKENS['warning']};
    --danger: {TOKENS['danger']};
    --btn-start: {TOKENS['btn-start']};
    --btn-end: {TOKENS['btn-end']};
}}

/* ── Global Reset ── */
html, body, [class*="css"] {{
    font-family: 'JetBrains Mono', monospace;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}}

.stApp {{
    background: linear-gradient(150deg, var(--bg) 0%, var(--bg-2) 45%, var(--bg-3) 100%) !important;
    transition: background 0.4s ease;
}}

/* Wavy white line pattern across the background */
.stApp::before {{
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='420' height='180' viewBox='0 0 420 180'><path d='M0 40 Q 52.5 0 105 40 T 210 40 T 315 40 T 420 40' stroke='white' stroke-width='2.5' fill='none' opacity='0.55'/><path d='M0 100 Q 52.5 60 105 100 T 210 100 T 315 100 T 420 100' stroke='white' stroke-width='2' fill='none' opacity='0.4'/><path d='M0 150 Q 52.5 118 105 150 T 210 150 T 315 150 T 420 150' stroke='white' stroke-width='1.5' fill='none' opacity='0.3'/></svg>");
    background-repeat: repeat;
    background-size: 420px 180px;
    opacity: {"0.06" if IS_DARK else "0.5"};
    pointer-events: none;
    z-index: 0;
}}

/* Soft glow blobs for a smooth, airy feel */
.stApp::after {{
    content: '';
    position: fixed;
    top: -10%; right: -10%;
    width: 45vw; height: 45vw;
    background: radial-gradient(circle, var(--accent-glow) 0%, transparent 70%);
    opacity: {"0.04" if IS_DARK else "0.05"};
    filter: blur(70px);
    pointer-events: none;
    z-index: 0;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}}

[data-testid="stSidebar"] * {{
    color: var(--text) !important;
}}

/* ── Headings ── */
h1, h2, h3, h4, h5, h6 {{
    font-family: 'Syne', sans-serif !important;
    color: var(--text) !important;
}}

/* ── Hero Title ── */
.hero-wrap {{
    display: flex;
    align-items: center;
    gap: 16px;
}}

.hero-icon {{
    width: 54px;
    height: 54px;
    border-radius: 14px;
    background: linear-gradient(135deg, #f9a8d4, var(--accent), var(--accent-2));
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 4px 14px rgba(157,23,77,0.28);
}}

.hero-icon svg {{
    width: 26px;
    height: 26px;
}}

.hero-title {{
    font-family: 'Fraunces', serif;
    font-size: clamp(1.9rem, 4.2vw, 2.9rem);
    font-weight: 600;
    letter-spacing: -0.01em;
    line-height: 1.1;
    margin: 0;
    background: linear-gradient(100deg, #f9a8d4 0%, var(--accent-glow) 40%, var(--accent) 70%, var(--accent-2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.hero-badge {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    margin-top: 8px;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    background: linear-gradient(120deg, rgba(157,23,77,0.14), rgba(244,114,182,0.14));
    color: var(--accent-2);
    border: 1px solid rgba(157,23,77,0.22);
}}

.hero-sub {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-muted);
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-top: 0.35rem;
}}

.hero-rule {{
    height: 1px;
    margin-top: 1.4rem;
    background: var(--border);
}}

/* ── Cards ── */
.card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 10px {"rgba(0,0,0,0.3)" if IS_DARK else "rgba(157,23,77,0.05)"};
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}}

.card:hover {{
    border-color: var(--accent);
    box-shadow: 0 4px 16px {"rgba(157,23,77,0.12)" if IS_DARK else "rgba(157,23,77,0.09)"};
}}

.card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: var(--accent);
}}

.card-title {{
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}

.card-content {{
    font-size: 0.875rem;
    line-height: 1.7;
    color: var(--text);
}}

/* ── Accent Badge ── */
.badge {{
    display: inline-block;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}}

.badge-purple {{ background: rgba(236,72,153,0.16); color: var(--accent-2); border: 1px solid rgba(236,72,153,0.3); }}
.badge-cyan   {{ background: rgba(219,39,119,0.12); color: var(--accent);    border: 1px solid rgba(219,39,119,0.28); }}
.badge-green  {{ background: rgba(16,185,129,0.14); color: var(--success);   border: 1px solid rgba(16,185,129,0.28); }}

/* ── Input & Selects ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {{
    background: var(--surface-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}}

.stTextInput > div > div > input:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(236,72,153,0.2) !important;
}}

.stSelectbox > div > div:hover {{
    border-color: var(--accent-glow) !important;
}}

/* ── Buttons — solid, confident, restrained ── */
.stButton > button {{
    background: var(--btn-start) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.04em !important;
    padding: 0.6rem 1.5rem !important;
    transition: background 0.2s ease, box-shadow 0.2s ease !important;
    text-transform: uppercase !important;
    box-shadow: 0 3px 10px rgba(157,23,77,0.22) !important;
}}

.stButton > button:hover {{
    background: var(--btn-end) !important;
    box-shadow: 0 5px 16px rgba(157,23,77,0.32) !important;
}}

.stButton > button:active {{
    box-shadow: 0 1px 4px rgba(157,23,77,0.3) !important;
}}

/* Secondary button */
.stButton > button[kind="secondary"] {{
    background: var(--surface-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    box-shadow: none !important;
}}

.stButton > button[kind="secondary"]:hover {{
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    box-shadow: 0 6px 18px rgba(236,72,153,0.18) !important;
}}

/* ── Progress / Status ── */
.status-bar {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: var(--surface-2);
    border-radius: 14px;
    margin: 0.4rem 0;
    border: 1px solid var(--border);
    font-size: 0.8rem;
}}

.status-dot {{
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}}

.dot-active   {{ background: var(--accent-glow); box-shadow: 0 0 8px var(--accent-glow); animation: pulse 1.5s infinite; }}
.dot-done     {{ background: var(--success); }}
.dot-pending  {{ background: var(--border); }}

@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50%       {{ opacity: 0.4; }}
}}

/* ── Chat ── */
.chat-container {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1.25rem;
    max-height: 420px;
    overflow-y: auto;
    margin-bottom: 1rem;
}}

.chat-msg {{
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}}

.chat-label {{
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}}

.chat-bubble {{
    display: inline-block;
    padding: 0.65rem 1.05rem;
    border-radius: 16px;
    font-size: 0.85rem;
    line-height: 1.6;
    max-width: 90%;
}}

.user-label  {{ color: var(--accent-2); }}
.bot-label   {{ color: var(--accent); }}

.user-bubble {{ background: rgba(236,72,153,0.14); border: 1px solid rgba(236,72,153,0.25); align-self: flex-end; }}
.bot-bubble  {{ background: rgba(219,39,119,0.08);  border: 1px solid rgba(219,39,119,0.18); align-self: flex-start; }}

/* ── Divider ── */
hr {{
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}}

/* ── Transcript box ── */
.transcript-box {{
    background: var(--surface-3);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.25rem;
    font-size: 0.82rem;
    line-height: 1.8;
    max-height: 300px;
    overflow-y: auto;
    color: var(--text-muted);
    white-space: pre-wrap;
    word-break: break-word;
}}

/* ── Stale Streamlit elements ── */
.stProgress > div > div > div {{ background: var(--accent) !important; }}
.stSpinner > div {{ border-top-color: var(--accent) !important; }}
[data-testid="stMarkdownContainer"] p {{ color: var(--text) !important; }}
label {{ color: var(--text-muted) !important; font-size: 0.8rem !important; }}

/* scrollbar */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--accent); }}
</style>
""", unsafe_allow_html=True)

# ─── Scroll-to-Top Button (appears once user scrolls down) ──────────────────────
components.html(f"""
<script>
(function() {{
    const doc = window.parent.document;
    let btn = doc.getElementById('scrollTopBtn');
    if (!btn) {{
        btn = doc.createElement('button');
        btn.id = 'scrollTopBtn';
        btn.innerHTML = '↑';
        btn.title = 'Back to top';
        Object.assign(btn.style, {{
            position: 'fixed',
            bottom: '28px',
            right: '28px',
            width: '46px',
            height: '46px',
            borderRadius: '999px',
            border: 'none',
            background: '{TOKENS['btn-start']}',
            color: '#fff',
            fontSize: '19px',
            fontWeight: '600',
            cursor: 'pointer',
            boxShadow: '0 4px 14px rgba(157,23,77,0.3)',
            opacity: '0',
            transform: 'translateY(12px)',
            pointerEvents: 'none',
            transition: 'opacity 0.25s ease, transform 0.25s ease',
            zIndex: 999999,
        }});
        btn.onmouseenter = () => btn.style.transform = 'translateY(0px) scale(1.08)';
        btn.onmouseleave = () => btn.style.transform = 'translateY(0px) scale(1)';
        btn.onclick = () => {{
            const mainEl = doc.querySelector('section.main');
            if (mainEl) mainEl.scrollTo({{ top: 0, behavior: 'smooth' }});
            window.parent.scrollTo({{ top: 0, behavior: 'smooth' }});
        }};
        doc.body.appendChild(btn);
    }}

    const mainEl = doc.querySelector('section.main');
    const target = mainEl || window.parent;

    function handleScroll() {{
        const scrollY = mainEl ? mainEl.scrollTop : window.parent.scrollY;
        if (scrollY > 240) {{
            btn.style.opacity = '1';
            btn.style.pointerEvents = 'auto';
            btn.style.transform = 'translateY(0px)';
        }} else {{
            btn.style.opacity = '0';
            btn.style.pointerEvents = 'none';
            btn.style.transform = 'translateY(12px)';
        }}
    }}

    target.removeEventListener('scroll', handleScroll);
    target.addEventListener('scroll', handleScroll);
    handleScroll();
}})();
</script>
""", height=0, width=0)

# ─── Session State Init ──────────────────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Helpers ────────────────────────────────────────────────────────────────────
def step_status(steps: dict, key: str) -> str:
    s = steps.get(key, "pending")
    if s == "active":  return "dot-active"
    if s == "done":    return "dot-done"
    return "dot-pending"

def render_step_bar(label: str, key: str, icon: str):
    css = step_status(st.session_state.pipeline_steps, key)
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-dot {css}"></div>
        <span>{icon} {label}</span>
    </div>""", unsafe_allow_html=True)

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    top_l, top_r = st.columns([4, 1])
    with top_l:
        st.markdown('<div class="hero-title" style="font-size:1.6rem">🎬 AI<br>Video</div>', unsafe_allow_html=True)
    with top_r:
        st.button("🌙" if not IS_DARK else "☀️", key="theme_toggle_btn", on_click=toggle_theme,
                   help="Switch to dark mode" if not IS_DARK else "Switch to light mode")

    st.markdown('<div class="hero-sub">AI Video Assistant Translator</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<span class="badge badge-purple">Input</span>', unsafe_allow_html=True)
    source = st.text_input("YouTube URL or File Path", placeholder="https://youtube.com/watch?v=... or /path/to/file.mp4")

    language = st.selectbox(
        "Language",
        ["english", "hinglish"],
        index=0,
        format_func=lambda x: x.capitalize(),
    )

    run_btn = st.button("⚡  Analyse", use_container_width=True)

    if st.session_state.pipeline_done:
        st.markdown("---")
        st.markdown('<span class="badge badge-green">Pipeline Status</span>', unsafe_allow_html=True)
        for step, icon, label in [
            ("audio",      "🔊", "Audio Processing"),
            ("transcript", "📝", "Transcription"),
            ("title",      "🏷️", "Title Generation"),
            ("summary",    "📋", "Summarisation"),
            ("extract",    "🔍", "Extraction"),
            ("rag",        "🧠", "RAG Engine"),
        ]:
            render_step_bar(label, step, icon)

# ─── Main Area ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <div class="hero-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="6" width="14" height="12" rx="2"></rect>
            <path d="M16 10.5l5-3v9l-5-3"></path>
        </svg>
    </div>
    <div>
        <div class="hero-title">AI Video Assistant</div>
        <div class="hero-sub">Transcribe · Summarise · Chat with your meetings</div>
        <div><span class="hero-badge">🎙️ Video Transcriber</span></div>
    </div>
</div>
<div class="hero-rule"></div>
""", unsafe_allow_html=True)

# ── Run Pipeline ────────────────────────────────────────────────────────────────
if run_btn:
    if not source.strip():
        st.error("Please enter a YouTube URL or file path.")
    else:
        st.session_state.pipeline_done = False
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pipeline_steps = {}

        progress_placeholder = st.empty()

        def update_step(key, state):
            st.session_state.pipeline_steps[key] = state

        try:
            with progress_placeholder.container():
                st.info("⚙️ Pipeline running — see sidebar for live status…")

            update_step("audio", "active")
            chunks = process_input(source)
            update_step("audio", "done")

            update_step("transcript", "active")
            transcript = transcribe_all(chunks, language)
            update_step("transcript", "done")

            update_step("title", "active")
            title = generate_title(transcript)
            update_step("title", "done")

            update_step("summary", "active")
            summary = summarize(transcript)
            update_step("summary", "done")

            update_step("extract", "active")
            action_items  = extract_action_items(transcript)
            decisions     = extract_key_decisions(transcript)
            questions     = extract_questions(transcript)
            update_step("extract", "done")

            update_step("rag", "active")
            rag_chain = build_rag_chain(transcript)
            update_step("rag", "done")

            st.session_state.result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "rag_chain": rag_chain,
            }
            st.session_state.pipeline_done = True
            progress_placeholder.success("✅ Analysis complete!")
            time.sleep(0.5)
            progress_placeholder.empty()
            st.rerun()

        except Exception as e:
            for k in ["audio","transcript","title","summary","extract","rag"]:
                if st.session_state.pipeline_steps.get(k) == "active":
                    st.session_state.pipeline_steps[k] = "pending"
            progress_placeholder.error(f"❌ Error: {e}")

# ── Results ──────────────────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result

    # Title banner
    st.markdown(f"""
    <div class="card">
        <div class="card-title">📌 Session Title</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:700;color:var(--text)">
            {r['title']}
        </div>
    </div>""", unsafe_allow_html=True)

    # Top row: summary + transcript
    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">📋 Summary</div>
            <div class="card-content">{r['summary']}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        with st.expander("📝 Full Transcript", expanded=False):
            st.markdown(f'<div class="transcript-box">{r["transcript"]}</div>', unsafe_allow_html=True)

    # Second row: action items | decisions | questions
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">✅ Action Items</div>
            <div class="card-content">{r['action_items']}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">🔑 Key Decisions</div>
            <div class="card-content">{r['key_decisions']}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">❓ Open Questions</div>
            <div class="card-content">{r['open_questions']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── RAG Chat ──────────────────────────────────────────────────────────────
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.2rem;font-weight:700;margin-bottom:1rem">💬 Chat with your Meeting</div>', unsafe_allow_html=True)

    # Chat history display
    if st.session_state.chat_history:
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-end">
                    <span class="chat-label user-label">You</span>
                    <div class="chat-bubble user-bubble">{msg['content']}</div>
                </div>"""
            else:
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-start">
                    <span class="chat-label bot-label">🤖 Assistant</span>
                    <div class="chat-bubble bot-bubble">{msg['content']}</div>
                </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2rem">
            <div style="font-size:2rem;margin-bottom:0.5rem">💬</div>
            <div style="color:var(--text-muted);font-size:0.85rem">Ask anything about your meeting transcript</div>
        </div>""", unsafe_allow_html=True)

    # Chat input
    chat_col1, chat_col2 = st.columns([5, 1], gap="small")
    with chat_col1:
        user_input = st.text_input("Your question", placeholder="What were the main decisions made?", label_visibility="collapsed")
    with chat_col2:
        send_btn = st.button("Send →", use_container_width=True)

    if send_btn and user_input.strip():
        with st.spinner("Thinking…"):
            answer = ask_question(r["rag_chain"], user_input.strip())
        st.session_state.chat_history.append({"role": "user",      "content": user_input.strip()})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

else:
    # Empty state
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:5rem 2rem;text-align:center">
        <div style="font-size:4rem;margin-bottom:1rem">🎬</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:700;color:var(--text);margin-bottom:0.5rem">
            Ready to Analyse
        </div>
        <div style="color:var(--text-muted);font-size:0.85rem;max-width:380px;line-height:1.7">
            Paste a YouTube URL or local file path in the sidebar, choose your language, and hit <strong>Analyse</strong> to get started.
        </div>
        <div style="margin-top:2rem;display:flex;gap:1rem;flex-wrap:wrap;justify-content:center">
            <span class="badge badge-purple">Transcription</span>
            <span class="badge badge-cyan">Summarisation</span>
            <span class="badge badge-green">RAG Chat</span>
        </div>
    </div>""", unsafe_allow_html=True)