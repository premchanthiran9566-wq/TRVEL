import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import (
    MAX_HISTORY_MESSAGES,
    MAX_MESSAGE_LENGTH,
    MAX_OUTPUT_TOKENS,
    MODEL_NAME,
    REFUSAL_MESSAGE,
    SYSTEM_PROMPT,
    TEMPERATURE,
)

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

generation_config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    temperature=TEMPERATURE,
    max_output_tokens=MAX_OUTPUT_TOKENS,
)


def build_contents(messages):
    contents = []
    for message in messages[-MAX_HISTORY_MESSAGES:]:
        role = "model" if message.get("role") == "assistant" else "user"
        text = str(message.get("content", "")).strip()[:MAX_MESSAGE_LENGTH]
        if text:
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    return contents


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages")

    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "Please enter a message."}), 400

    contents = build_contents(messages)
    if not contents or contents[-1].role != "user":
        return jsonify({"error": "Please enter a message."}), 400

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=generation_config,
        )
        reply = (response.text or "").strip() or REFUSAL_MESSAGE
        return jsonify({"reply": reply})
    except Exception:
        app.logger.exception("Gemini request failed")
        return jsonify({"error": "Something went wrong. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True)
