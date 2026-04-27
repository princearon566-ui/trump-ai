from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

API_KEY = os.environ.get("GROQ_API_KEY")

conversation = [
    {
        "role": "system", 
        "content": "You are Donald Trump. You speak exactly like him — using words like 'tremendous', 'huge', 'believe me', 'nobody knows more than me', 'bigly', 'the best'. You brag constantly but are actually helpful. Every answer relates back to how great you are."
    }
]

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
        .controls { display: flex; gap: 10px; }
        input { flex-grow: 1; padding: 10px; border-radius: 5px; border: 2px solid #ff0000; background: #001f3f; color: white; }
        button { width: 20%; padding: 10px; background: #ff0000; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        #voiceBtn { width: 100%; margin-top: 10px; padding: 10px; background: #ffd700; color: black; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
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
        <button id="voiceBtn" onclick="startVoice()">🎤 SPEAK</button>
    </div>

<script>
    // 1. Voice input function
    function startVoice() {
    alert("Button works!");  // add this first line
    const recognition = new webkitSpeechRecognition();
        const recognition = new webkitSpeechRecognition();
        recognition.lang = 'en-US';
        
        recognition.onresult = function(event) {
            const text = event.results[0][0].transcript;
            document.getElementById('message').value = text;
            sendMessage();
        };
        
        recognition.start();
        document.getElementById('voiceBtn').innerText = '🔴 Listening...';
    }

    // 2. Trump speaks back!
    function speak(text) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.8;
        utterance.pitch = 0.7;
        utterance.volume = 1;
        const voices = window.speechSynthesis.getVoices();
        const americanVoice = voices.find(v => v.lang === "en-US");
        if (americanVoice) utterance.voice = americanVoice;
        window.speechSynthesis.speak(utterance);
    }

    // 3. Send message function
    async function sendMessage() {
        ...
    }
</script>
</body>
</html>
    ''')

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"response": "That's a weak question. Try again."})
        
    conversation.append({"role": "user", "content": user_input})
    response_text = ask_ai(conversation)
    conversation.append({"role": "assistant", "content": response_text})
    
    return jsonify({"response": response_text})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
  
