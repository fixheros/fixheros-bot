from flask import Flask, request, jsonify, Response, render_template
from flask_cors import CORS
from openai import OpenAI
from twilio.twiml.messaging_response import MessagingResponse
import os
import time

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Your FixHeros Assistant ID (from OpenAI)
ASSISTANT_ID = "asst_UR21ZKHOLtoIWkOaiQFhs4pt"

# Health check
@app.route("/")
def home():
    return "FixHeros Assistant Running!"

# Web chat route
@app.route("/chat")
def chat():
    return render_template("chat.html")

# API route for AI conversation (Web interface)
@app.route("/ask", methods=["POST"])
def ask():
    try:
        user_input = request.json.get("message", "")
        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        # Create a new thread for each message (or use persistent thread per user)
        thread = client.beta.threads.create()

        # Add message
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

        # Wait for completion
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            if run_status.status == "completed":
                break
            time.sleep(1)

        # Get reply
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        reply = messages.data[0].content[0].text.value

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# WhatsApp bot route (via Twilio)
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get('Body', '').strip()
    sender = request.form.get('From', '')

    if not incoming_msg:
        twilio_resp = MessagingResponse()
        twilio_resp.message("Sorry, I didn’t get that.")
        return Response(str(twilio_resp), mimetype="application/xml")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are FixHeros, a helpful assistant for home maintenance and repair services."},
                {"role": "user", "content": incoming_msg}
            ]
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        reply = "⚠️ Sorry, something went wrong. Please try again later."

    twilio_resp = MessagingResponse()
    twilio_resp.message(reply)
    return Response(str(twilio_resp), mimetype="application/xml")

# Start server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
