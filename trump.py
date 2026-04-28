from flask import Flask, request, jsonify, render_template_string, session
import requests
import os
from supabase import create_client

app = Flask(__name__)
app.secret_key = "trump2024secretkey"

# API keys
API_KEY = os.environ.get("GROQ_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Connect to Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are Donald Trump. You speak exactly like him — using words like 'tremendous', 'huge', 'believe me', 'nobody knows more than me', 'bigly', 'the best'. You brag constantly but are actually helpful."
}

def load_conversation(session_id):
    try:
        result = supabase.table("conversations")\
            .select("role, content")\
            .eq("session_id", session_id)\
            .order("id")\
            .execute()
        
        if result.data:
            return [{"role": r["role"], "content": r["content"]} for r in result.data]
        else:
            return [SYSTEM_PROMPT]
    except:
        return [SYSTEM_PROMPT]

def save_message(session_id, role, content):
    try:
        # Clean special characters before saving
        clean_content = content.encode('utf-8', 'ignore').decode('utf-8')
        supabase.table("conversations").insert({
            "session_id": session_id,
            "role": role,
            "content": clean_content
        }).execute()
    except Exception as e:
        print(f"Save error: {e}")
        
def ask_ai(conversation_history):
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": conversation_history
            }
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"We have a problem, a huge problem. The best people are looking at it. (Error: {str(e)})"

@app.route("/")
def home():
    if "session_id" not in session:
        session["session_id"] = os.urandom(16).hex()
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Trump AI</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; max-width: 600px; margin: 0 auto; padding: 20px; background: #001f3f; color: white; }
        h1 { color: #ff0000; text-align: center; }
        h2 { color: #ffd700; text-align: center; font-size: 14px; }
        #chat { height: 400px; overflow-y: auto; border: 2px solid #ff0000; padding: 10px; border-radius: 10px; margin-bottom: 10px; background: #002f5f; }
        .user { color: #ffd700; margin: 10px 0; }
        .ai { color: #ffffff; margin: 10px 0; }
        .flag { text-align: center; font-size: 30px; margin: 10px; }
        .controls { display: flex; gap: 10px; margin-bottom: 10px; }
        input { flex-grow: 1; padding: 10px; border-radius: 5px; border: 2px solid #ff0000; background: #001f3f; color: white; }
        button { padding: 10px 15px; background: #ff0000; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        #voiceBtn { width: 100%; padding: 10px; background: #ffd700; color: black; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>
    <div class="flag">🇺🇸</div>
    <h1>🍊 Trump AI 🍊</h1>
    <h2>Make Conversations Great Again!</h2>
    <div id="chat"></div>
    <div class="controls">
        <input type="text" id="message" placeholder="Ask Trump anything...">
        <button onclick="sendMessage()">SEND</button>
    </div>
    <button id="voiceBtn" onclick="startVoice()">🎤 SPEAK TO TRUMP</button>

    <script>
        window.onload = async function() {
            const response = await fetch("/history");
            const data = await response.json();
            const chat = document.getElementById("chat");
            data.messages.forEach(msg => {
                if (msg.role === "user") {
                    chat.innerHTML += `<p class="user">You: ${msg.content}</p>`;
                } else if (msg.role === "assistant") {
                    chat.innerHTML += `<p class="ai">🍊 Trump: ${msg.content}</p>`;
                }
            });
            chat.scrollTop = chat.scrollHeight;
        }

        function startVoice() {
            const recognition = new webkitSpeechRecognition();
            recognition.lang = 'en-US';
            recognition.onresult = function(event) {
                const text = event.results[0][0].transcript;
                document.getElementById('message').value = text;
                document.getElementById('voiceBtn').innerText = '🎤 SPEAK TO TRUMP';
                sendMessage();
            };
            recognition.onerror = function() {
                document.getElementById('voiceBtn').innerText = '🎤 SPEAK TO TRUMP';
            };
            recognition.start();
            document.getElementById('voiceBtn').innerText = '🔴 Listening...';
        }

    
        async function sendMessage() {
            const input = document.getElementById("message");
            const chat = document.getElementById("chat");
            const message = input.value.trim();
            if (!message) return;
            chat.innerHTML += `<p class="user">You: ${message}</p>`;
            input.value = "";
            const response = await fetch("/chat", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({message: message})
            });
            const data = await response.json();
            chat.innerHTML += `<p class="ai">🍊 Trump: ${data.response}</p>`;
            chat.scrollTop = chat.scrollHeight;
        }

        document.getElementById("message").addEventListener("keypress", function(e) {
            if (e.key === "Enter") sendMessage();
        });
    </script>
</body>
</html>
    ''')

@app.route("/history")
def history():
    session_id = session.get("session_id", "default")
    conversation = load_conversation(session_id)
    messages = [m for m in conversation if m["role"] != "system"]
    return jsonify({"messages": messages})

@app.route("/chat", methods=["POST"])
def chat():
    session_id = session.get("session_id", "default")
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"response": "That's a weak question. Try again."})

    conversation = load_conversation(session_id)
    save_message(session_id, "user", user_input)
    conversation.append({"role": "user", "content": user_input})
    response_text = ask_ai(conversation)
    save_message(session_id, "assistant", response_text)

    return jsonify({"response": response_text})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
