import os
import gradio as gr
from src.rag_engine import load_index, get_query_engine, setup_models
from src.language_handler import translate_to_english, translate_response
from dotenv import load_dotenv

load_dotenv()

# ── INITIALIZATION ──────────────────────────────────────────────────
print("Booting Kadel Lab Assistant (ChatGPT Minimal UI)...")

try:
    index = load_index()
    query_engine = get_query_engine(index)
except Exception as e:
    print(f"Error initializing RAG: {e}")
    query_engine = None

def get_provider_status():
    provider = os.getenv("LLM_PROVIDER", "ollama")
    model = os.getenv(f"{provider.upper()}_MODEL", "unknown")
    return f"Active: {provider} ({model})"

def get_doc_count():
    folder = "knowledge_base"
    if not os.path.exists(folder): return 0
    return len([f for f in os.listdir(folder) if f.endswith(('.pdf', '.txt', '.docx'))])

# ── CHAT LOGIC ───────────────────────

LANG_MAP = {"English": "en", "Hindi": "hi", "Hinglish": "hi"}

def chat_stream(message, history, manual_lang):
    if not message.strip():
        yield "", history
        return
        
    try:
        # Step 1: Append User Message
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": "<span class='typing-dot'></span><span class='typing-dot'></span><span class='typing-dot'></span>"})
        yield "", history
        
        user_lang = LANG_MAP.get(manual_lang, "en")
        
        english_query = message
        if user_lang != 'en':
            english_query = translate_to_english(message, user_lang)

        # Step 3: Predictive RAG Search with System Guardrails
        system_prompt = "You are Kadel Lab Assistant, an AI helper for Kadel Lab Training Centre. Always respond in English only, regardless of what language the user writes in. Do not switch to any other language unless the user explicitly selects a different language from settings. Keep responses concise, helpful, and friendly."
        
        full_query = f"{system_prompt}\n\nUser Query: {english_query}"
        streaming_response = query_engine.query(full_query)
        
        full_response = ""
        for text in streaming_response.response_gen:
            full_response += text
            history[-1]["content"] = full_response
            yield "", history
            
        # Step 4: Finalize & Format
        if user_lang != 'en':
            history[-1]["content"] = full_response + " <span class='typing-dot'></span><span class='typing-dot'></span><span class='typing-dot'></span>"
            yield "", history
            final_answer = translate_response(full_response, user_lang)
            history[-1]["content"] = final_answer
            yield "", history
            
    except Exception as e:
        history.append({"role": "assistant", "content": f"An error occurred: {str(e)}"})
        yield "", history

def change_provider(new_provider):
    global query_engine
    try:
        # Re-setup models with the new provider
        setup_models(new_provider.lower())
        # Refresh query engine to use the new LLM
        query_engine = get_query_engine(index)
        # Update env for consistency (optional)
        os.environ["LLM_PROVIDER"] = new_provider.lower()
        return f"Provider switched to: {new_provider}"
    except Exception as e:
        return f"Failed to switch: {str(e)}"

def sync_knowledge():
    global index, query_engine
    try:
        from src.rag_engine import build_index
        index = build_index()
        query_engine = get_query_engine(index)
        return f"Database Refreshed ({get_doc_count()} docs)"
    except Exception as e:
        return f"Sync failed: {str(e)}"

# ── CHATGPT MINIMAL STYLING ──────────────────────────────────────────

chatgpt_css = """
@import url('https://fonts.googleapis.com/css2?family=Söhne:wght@400;500;600&family=ui-sans-serif&family=system-ui&family=JetBrains+Mono&display=swap');

body {
    background-color: #212121 !important;
    font-family: 'Söhne', ui-sans-serif, system-ui, sans-serif !important;
    color: #ececec !important;
    margin: 0; padding: 0;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: #424242;
    border-radius: 3px;
}

.gradio-container {
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* Header */
.top-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background-color: #212121;
    border-bottom: 1px solid #2f2f2f;
    position: sticky;
    top: 0;
    z-index: 100;
}

.settings-col {
    display: flex;
    align-items: center;
    gap: 12px;
}

#settings-accordion {
    background: transparent !important;
    border: 1px solid #2f2f2f !important;
    border-radius: 8px;
    padding: 4px;
}

/* Chat Area */
#chat-container {
    max-width: 760px !important;
    margin: 0 auto !important;
    padding: 24px !important;
    flex-grow: 1;
}

#chatbot {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

.message-wrap {
    animation: fadeInSlideUp 0.3s ease forwards;
}

@keyframes fadeInSlideUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* User Message */
.user {
    background: #2f2f2f !important;
    color: #ececec !important;
    border-radius: 20px !important; 
    padding: 10px 16px !important;
    border: none !important;
    font-size: 16px;
    line-height: 1.5;
}

/* Bot Message */
.bot {
    background: transparent !important;
    color: #ececec !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 8px 0 !important;
    box-shadow: none !important;
    font-size: 16px;
    line-height: 1.75;
}

/* Timestamps & Copy button */
.bot .time, .user .time, .timestamp {
    display: none !important;
}
.bot:hover .timestamp, .user:hover .timestamp {
    display: none !important; 
}
.md-copy {
    opacity: 0;
    transition: opacity 0.2s;
}
.bot:hover .md-copy {
    opacity: 1;
}

/* Code */
.bot pre, .bot code {
    font-family: 'JetBrains Mono', monospace !important;
    background: #1e1e1e !important;
    border: 1px solid #2f2f2f;
    border-radius: 6px;
}

/* Input Bar */
#input-wrapper {
    max-width: 760px;
    margin: 0 auto;
    padding: 0 24px 24px 24px;
    position: relative;
}

#input-section {
    background: #2f2f2f;
    border-radius: 24px;
    padding: 4px 12px;
    border: 1px solid transparent;
    transition: all 0.2s;
}

#input-section:focus-within {
    box-shadow: 0 0 15px rgba(255, 255, 255, 0.05);
}

#input-section textarea {
    background: transparent !important;
    border: none !important;
    color: #ececec !important;
    box-shadow: none !important;
    font-size: 16px;
    line-height: 1.5;
    padding: 12px 8px !important;
    resize: none !important;
}

#input-section textarea:focus {
    box-shadow: none !important;
    border: none !important;
}

.send-btn {
    background: #ececec !important;
    color: #212121 !important;
    width: 32px;
    height: 32px;
    border-radius: 8px !important;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 !important;
    cursor: pointer;
    border: none !important;
    transition: opacity 0.2s;
}
.send-btn:hover {
    opacity: 0.8;
}

/* Quick Chips */
#quick-chips {
    margin: 40px auto;
    max-width: 600px;
}

.chip-card {
    background: #2f2f2f !important;
    border: 1px solid #424242 !important;
    border-radius: 12px !important;
    color: #ececec !important;
    padding: 16px !important;
    font-size: 14px !important;
    text-align: left !important;
    transition: all 0.2s !important;
    display: flex;
    justify-content: center;
    align-items: center;
}
.chip-card:hover {
    background: #3f3f3f !important;
}

/* Footer */
.footer-text {
    text-align: center;
    font-size: 12px;
    color: #666;
    margin-top: 12px;
}

/* Typing indicator */
.typing-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    background: #888;
    border-radius: 50%;
    margin-right: 4px;
    animation: typing 1.4s infinite ease-in-out both;
}
.typing-dot:nth-child(1) { animation-delay: -0.32s; }
.typing-dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes typing {
    0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
    40% { transform: scale(1); opacity: 1; }
}

/* Overriding gradio avatars sizes for bot */
.avatar-image {
    border-radius: 50% !important;
    background: white !important;
}
"""

def launch_ui():
    # Pass CSS inside Blocks for Gradio 4.x/5.x compatibility in latest versions
    with gr.Blocks(title="Kadel Lab Assistant", theme=gr.themes.Default(), css=chatgpt_css) as demo:
        
        # ── HEADER ──
        with gr.Row(elem_classes="top-nav"):
            gr.HTML("""
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 32px; height: 32px; background: #ececec; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #212121; font-weight: bold; font-size: 14px;">
                        KL
                    </div>
                    <span style="font-weight: 600; font-size: 16px; color: #ececec;">Kadel Lab Assistant</span>
                </div>
            """)
            with gr.Column(elem_classes="settings-col", min_width=250):
                with gr.Row():
                    gr.HTML('<span style="color: #888; font-size: 14px; display: flex; align-items: center; padding-top: 12px; margin-right: 8px;">KL-2.1</span>')
                    with gr.Accordion("⚙️ Settings", open=False, elem_id="settings-accordion"):
                        manual_lang = gr.Dropdown(choices=["English", "Hindi", "Hinglish"], value="English", label="Language")
                        provider_dropdown = gr.Dropdown(
                            choices=["Ollama", "Groq", "Gemini"], 
                            value=os.getenv("LLM_PROVIDER", "ollama").capitalize(), 
                            label="LLM Provider"
                        )
                        sync_btn = gr.Button("Sync Vectors", variant="secondary", size="sm")
                        status_text = gr.Markdown(f"_{get_doc_count()} docs_")
                        provider_text = gr.HTML(f'<div id="provider-status" style="font-size: 11px; color: #666; margin-top: 8px;">{get_provider_status()}</div>')

        # ── CHAT AREA ──
        with gr.Column(elem_id="chat-container"):
            
            # Conditionally shown action chips
            with gr.Column(elem_id="quick-chips") as quick_chips:
                with gr.Row():
                    q1 = gr.Button("📚 View Courses", elem_classes="chip-card")
                    q2 = gr.Button("📅 Training Schedules", elem_classes="chip-card")
                with gr.Row():
                    q3 = gr.Button("💰 Fee Structure", elem_classes="chip-card")
                    q4 = gr.Button("🎓 Certifications", elem_classes="chip-card")

            chatbot = gr.Chatbot(
                height=600,
                show_label=False,
                elem_id="chatbot",
                avatar_images=(None, "https://cdn-icons-png.flaticon.com/512/2813/2813137.png")
            )

        # ── INPUT AREA ──
        with gr.Column(elem_id="input-wrapper"):
            with gr.Row(elem_id="input-section", variant="compact"):
                with gr.Column(scale=9, min_width=250):
                    msg = gr.Textbox(
                        placeholder="Ask Kadel Lab Assistant...",
                        show_label=False,
                        container=False,
                        lines=1,
                        max_lines=6
                    )
                with gr.Column(scale=1, min_width=40):
                    send_btn = gr.Button("↑", elem_classes="send-btn")
                
            gr.HTML('<div class="footer-text">Kadel Lab Assistant can make mistakes. Verify important info.</div>')

        # ── LOGIC BINDINGS ──
        
        # Toast language change
        def notify_lang(lang):
            gr.Info(f"Language set to {lang}")
        manual_lang.change(notify_lang, inputs=[manual_lang], outputs=[])
        
        # Provider change handling
        def update_provider_ui(provider):
            msg = change_provider(provider)
            gr.Info(msg)
            return f'<div id="provider-status" style="font-size: 11px; color: #666; margin-top: 8px;">Active: {provider.lower()}</div>'

        provider_dropdown.change(update_provider_ui, inputs=[provider_dropdown], outputs=[provider_text])
        
        # Hide chips and process message
        def hide_chips_ui():
            return gr.update(visible=False)

        # Submit Flow
        msg.submit(hide_chips_ui, None, quick_chips).then(chat_stream, [msg, chatbot, manual_lang], [msg, chatbot])
        send_btn.click(hide_chips_ui, None, quick_chips).then(chat_stream, [msg, chatbot, manual_lang], [msg, chatbot])
        
        sync_btn.click(sync_knowledge, None, status_text)
        
        # Quick Chips Flow
        def direct_chip_submit(query):
            return query, gr.update(visible=False)
            
        q1.click(lambda: direct_chip_submit("What courses are currently available?"), None, [msg, quick_chips]).then(
            chat_stream, [msg, chatbot, manual_lang], [msg, chatbot])
        q2.click(lambda: direct_chip_submit("Show me the upcoming training schedules."), None, [msg, quick_chips]).then(
            chat_stream, [msg, chatbot, manual_lang], [msg, chatbot])
        q3.click(lambda: direct_chip_submit("What is the fee structure for available courses?"), None, [msg, quick_chips]).then(
            chat_stream, [msg, chatbot, manual_lang], [msg, chatbot])
        q4.click(lambda: direct_chip_submit("What certifications do you offer?"), None, [msg, quick_chips]).then(
            chat_stream, [msg, chatbot, manual_lang], [msg, chatbot])

    return demo

if __name__ == "__main__":
    demo = launch_ui()
    # Note: gradio handles theme overrides, but using simple gr.themes.Default removes unwanted global overrides.
    demo.launch(share=True)
