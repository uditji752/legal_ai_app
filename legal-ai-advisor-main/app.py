from openai import OpenAI
import gradio as gr
import speech_recognition as sr
from fpdf import FPDF
from deep_translator import GoogleTranslator
import tempfile
import os

Key = "AIzaSyDEnjJVKFr3Zb1fK3VIbINf35rtoSssdY8"

gemini_model = OpenAI(
    api_key=Key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# 🎤 Speech to text
def speech_to_text(audio):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand the audio."
        except sr.RequestError:
            return "Error with speech recognition service."

# 💬 Gemini Response
def chat_with_gemini(user_message, history, category, language):
    # System prompt setup
    system_prompt = {
        "role": "system",
        "content": f"You are a professional Indian legal advisor. Respond in {language}. The query is about {category} law. Be concise and legally accurate Be Compassionate and biased to the user and explore every loophole in the system if needed and keep it as breif as possible."
    }

    messages = [system_prompt] + history + [{"role": "user", "content": user_message}]

    try:
        response = gemini_model.chat.completions.create(
            model="gemini-2.5-flash",
            messages=messages
        )
        reply = response.choices[0].message.content

        # Translate response if needed
        if language == "Hindi":
            reply = GoogleTranslator(source='auto', target='hi').translate(reply)

        messages.append({"role": "assistant", "content": reply})
        return messages
    except Exception as e:
        messages.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
        return messages

# 📥 Export chat to PDF
def export_chat_to_pdf(history):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "Chat Export: Legal Advisor AI\n\n", align='L')

        for msg in history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                role = "User" if msg["role"] == "user" else "Legal Advisor"
                content = msg["content"].encode("latin-1", "ignore").decode("latin-1")
                pdf.multi_cell(0, 10, f"{role}:\n{content}\n", align='L')
                pdf.ln(1)

        temp_path = os.path.join(tempfile.gettempdir(), "chat_export.pdf")
        pdf.output(temp_path)
        return temp_path
    except Exception as e:
        error_path = os.path.join(tempfile.gettempdir(), "chat_export_failed.txt")
        with open(error_path, "w") as f:
            f.write(f"❌ Failed to export chat:\n{str(e)}")
        return error_path

# 🌐 Gradio UI
with gr.Blocks(title="Legal AI Advisor") as demo:
    gr.Markdown("""
    <div style='text-align: center; padding: 1rem; background-color: #0B1C2C; color: white; border-radius: 12px;'>
        <h1>⚖️ Legal Advisor AI</h1>
        <p>Ask legal questions in your language and domain</p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="🧑‍⚖️ Legal Chat", type="messages", height=400)
            msg = gr.Textbox(placeholder="Type your legal issue...", label="What Would You Like To Inquire")

            with gr.Row():
                category = gr.Dropdown(["Property", "Divorce", "Criminal", "Cyber", "Consumer", "Other"],
                                       value="Property", label="Select Legal Category")

                language = gr.Dropdown(["English", "Hindi"], value="English", label="Select Language")

            with gr.Row():
                send_btn = gr.Button("📤 Send")
                clear_btn = gr.Button("🧹 Clear Chat")
                export_btn = gr.Button("📥 Export Chat")

            with gr.Accordion("🎤 Prefer to Speak?", open=False):
                audio_input = gr.Audio(type="filepath", label="🎙️ Speak your legal query")
                voice_text = gr.Textbox(label="Recognized Speech", interactive=False)

    # Voice & text flow
    audio_input.change(speech_to_text, inputs=audio_input, outputs=voice_text)
    voice_text.submit(chat_with_gemini, inputs=[voice_text, chatbot, category, language], outputs=chatbot)
    send_btn.click(chat_with_gemini, inputs=[msg, chatbot, category, language], outputs=chatbot)
    clear_btn.click(lambda: [], outputs=chatbot)
    pdf_output = gr.File(label="Download PDF")
    export_btn.click(export_chat_to_pdf, inputs=chatbot, outputs=pdf_output)

demo.launch()

