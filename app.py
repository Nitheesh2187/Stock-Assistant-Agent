import os
import streamlit as st
from src.agent import StockAssistanceAgent
import nest_asyncio
import asyncio
from dotenv import load_dotenv
import time

nest_asyncio.apply()
load_dotenv()

# Streamlit App Configuration
st.set_page_config(
    page_title="Stock Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Claude-like CSS styling
with open("src/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = None
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_initialized" not in st.session_state:
    st.session_state.agent_initialized = False
if "is_thinking" not in st.session_state:
    st.session_state.is_thinking = False

# Auto-initialize agent
if not st.session_state.agent_initialized:
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            with st.spinner("Initializing Stock Assistant..."):
                st.session_state.agent = StockAssistanceAgent()
                st.session_state.agent_initialized = True
        except Exception as e:
            st.error(f"Failed to initialize agent: {str(e)}")

# Status indicator
status_class = "status-ready" if st.session_state.agent_initialized else "status-error"
status_text = "🟢 Ready" if st.session_state.agent_initialized else "🔴 Not Ready"
st.markdown(f'<div class="status-indicator {status_class}">{status_text}</div>', unsafe_allow_html=True)

# Header
st.markdown("""
<div class="app-header">
    <div class="app-title">📈 Stock Assistant</div>
    <div class="app-subtitle">Your intelligent financial companion powered by AI</div>
</div>
""", unsafe_allow_html=True)

# Welcome message and suggestions (only when no conversation)
if not st.session_state.messages and st.session_state.agent_initialized:
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0; color: #718096;">
        Hi! I'm your Stock Assistant. I can help you with financial decisions, market analysis, 
        stock analysis, and much more. What would you like to explore today?
    </div>
    """, unsafe_allow_html=True)
    
    # Suggestion cards
    suggestions = [
    {
        "title": "📈 Stock Price Analysis",
        "text": "Get current stock prices, price history, and technical chart analysis"
    },
    {
        "title": "🔍 Company Fundamentals",
        "text": "Analyze P/E ratios, revenue growth, debt levels, and key financial metrics"
    },
    {
        "title": "📰 Latest Stock News",
        "text": "Stay updated with recent earnings, announcements, and market-moving news"
    },
    {
        "title": "📊 Complete Stock Analysis",
        "text": "Get comprehensive analysis combining price, fundamentals, and latest news"
    },
    {
        "title": "🏢 Indian Market Focus",
        "text": "Specialized analysis for NSE and BSE listed companies"
    },
    {
        "title": "💡 Investment Research",
        "text": "Get detailed financial data for informed investment decisions"
    }
]
    
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(f"{suggestion['title']}", key=f"suggestion_{i}", use_container_width=True):
                question_map = {
                    "📈 Stock Price Analysis": "Show me the current price and trading data for RELIANCE stock",
                    "🔍 Company Fundamentals": "What are the key financial metrics and fundamentals for TCS.NS?",
                    "📰 Latest Stock News": "Get me the latest news about Infosys stock and recent developments",
                    "📊 Complete Stock Analysis": "Perform a comprehensive analysis of HDFCBANK.NS including price, fundamentals, and news",
                    "🏢 Indian Market Focus": "Analyze WIPRO.NS with focus on Indian market performance and sector comparison",
                    "💡 Investment Research": "Help me research Tata Motors for investment - show financials, ratios, and recent news"
                }
                user_input = question_map[suggestion['title']]
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.is_thinking = True
                st.rerun()

# Chat history
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="message message-user">
                <div class="message-content">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        elif message["role"] == "error":
            st.markdown(f"""
            <div class="message message-error">
                <div class="message-content">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="message message-assistant">
                <div class="message-content">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Thinking indicator
    if st.session_state.is_thinking:
        st.markdown("""
        <div class="typing-indicator">
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
            <span style="margin-left: 0.75rem; color: #718096;">Thinking...</span>
        </div>
        """, unsafe_allow_html=True)

# Process pending message
if st.session_state.is_thinking and st.session_state.agent_initialized:

    last_user_message = st.session_state.messages[-1]["content"]
    response = asyncio.run(st.session_state.agent.chat(last_user_message))
    if type(response) == dict and "error" in response:
        error_msg = f"I apologize, but I encountered an error: {str(response['error'].message)}"
        st.session_state.messages.append({"role": "error", "content": error_msg})
    else:
        st.session_state.messages.append({"role": "assistant", "content": response})

    st.session_state.is_thinking = False
    st.rerun()

# Chat input (fixed at bottom)
st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)  # Spacer for fixed input

# Input area
if st.session_state.agent_initialized:
    user_input = st.chat_input(
        "Ask me anything about stocks, finance, or market analysis...",
        disabled=st.session_state.is_thinking,
        key="main_input"
    )
    
    if user_input and not st.session_state.is_thinking:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.is_thinking = True
        st.rerun()

# Error state with proper red styling
if not st.session_state.agent_initialized:
    st.markdown("""
    <div class="error-container">
        <div class="error-title">⚠️ Setup Required</div>
        <div class="error-message">Please ensure your GROQ_API_KEY is set in your .env file and restart the application.</div>
        <div class="error-details">Make sure your MCP servers (math and weather) are also running.</div>
    </div>
    """, unsafe_allow_html=True)

# Quick actions (floating when chatting)
if st.session_state.messages and st.session_state.agent_initialized:
    pass

with st.sidebar:
    st.markdown("### 🚀 Quick Actions")
    
    if st.button("📊 Market Trends", use_container_width=True):
        st.session_state.messages.append({
            "role": "user", 
            "content": "What are the current trends I should watch in the market?"
        })
        st.session_state.is_thinking = True
        st.rerun()
    
    if st.button("💡 Investment Tips", use_container_width=True):
        st.session_state.messages.append({
            "role": "user", 
            "content": "Give me some practical investment tips for beginners"
        })
        st.session_state.is_thinking = True
        st.rerun()
    
    
    st.markdown("---")

    # Available tools display
    if st.session_state.agent_initialized and st.session_state.agent:
        st.markdown("### 🛠️ Available Tools")
        tools = st.session_state.agent.get_available_tools()
        if tools:
            for tool in tools:
                st.markdown(f'<span class="tool-item">{tool}</span>', unsafe_allow_html=True)
            
            # st.markdown("""
            #     </div>
            # </div>
            # """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        if st.session_state.agent:
            st.session_state.agent.clear_memory()
        st.rerun()

# Cleanup function
@st.cache_resource
def get_cleanup_function():
    def cleanup():
        if st.session_state.get("agent"):
            st.session_state.agent.clean_up()
    return cleanup

cleanup_fn = get_cleanup_function()