from flask import Flask, request, jsonify, render_template_string, session
import requests
import os
import sqlite3
import json

app = Flask(__name__)
app.secret_key = "trump2024secretkey"

API_KEY = os.environ.get("GROQ_API_KEY")

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are Donald Trump. You speak exactly like him — using words like 'tremendous', 'huge', 'believe me', 'nobody knows more than me', 'bigly', 'the best'. You brag constantly but are actually helpful."
}

# Setup database
def init_db():
    db = sqlite3.connect("conversations.db")
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            content TEXT
        )
    """)
    db.commit()
    db.close()

# Load conversation from database
def load_conversation(session_id):
    db = sqlite3.connect("conversations.db")
    cursor = db.cursor()
    cursor.execute("""
        SELECT role, content FROM conversations
        WHERE session_id = ?
        ORDER BY id
    """, (session_id,))
    rows = cursor.fetchall()
    db.close()

    if rows:
        return [{"role": row[0], "content": row[1]} for row in rows]
    else:
        return [SYSTEM_PROMPT]

# Save message to database
def save_message(session_id, role, content):
    db = sqlite3.connect("conversations.db")
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO conversations (session_id, role, content)
        VALUES (?, ?, ?)
    """, (session_id, role, content))
    db.commit()
    db.close()

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
        return f"We have a problem, a huge problem. (Error: {str(e)})"

@app.route("/")
def home():
    # Give each user a unique session ID
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

    <script>
        // Load previous messages when page opens
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
            speak(data.response);
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
    # Filter out system message
    messages = [m for m in conversation if m["role"] != "system"]
    return jsonify({"messages": messages})

@app.route("/chat", methods=["POST"])
def chat():
    session_id = session.get("session_id", "default")
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"response": "That's a weak question. Try again."})

    # Load conversation from database
    conversation = load_conversation(session_id)

    # Save user message
    save_message(session_id, "user", user_input)
    conversation.append({"role": "user", "content": user_input})

    # Get AI response
    response_text = ask_ai(conversation)

    # Save AI response
    save_message(session_id, "assistant", response_text)

    return jsonify({"response": response_text})

# Initialize database when app starts
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
