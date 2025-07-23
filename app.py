from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
import os

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Your FixHeros Assistant ID
ASSISTANT_ID = "asst_UR21ZKHOLtoIWkOaiQFhs4pt"

# Health check route
@app.route("/")
def home():
    return "FixHeros Assistant Running!"

# AI Assistant Message Handler
@app.route("/ask", methods=["POST"])
def ask():
    try:
        user_input = request.json.get("message", "")
        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        # Create thread
        thread = client.beta.threads.create()

        # Add user message
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

        # Run assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # Wait for run to complete
        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break

        # Get assistant reply
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        reply = messages.data[0].content[0].text.value

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Web chat interface
@app.route("/chat")
def chat():
    return render_template("chat.html")

# Start the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
