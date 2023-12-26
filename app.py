import datetime
import os
import google.generativeai as genai
from datetime import timedelta
from flask import Flask, request, render_template, make_response
from src.security.secure_uuid4 import secure_uuid4
from src.security.mask_sensitive_data import mask_sensitive_data
from src.ChatSession import ChatSession

# -------------------------------------------------DOTENV------------------------------------------------------

GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
MAX_CHAT_COUNT = os.getenv("MAX_CHAT_COUNT")

assert GOOGLE_AI_API_KEY, "GOOGLE_AI_API_KEY is not set."
assert MAX_CHAT_COUNT, "MAX_CHAT_COUNT is not set."

assert (
    MAX_CHAT_COUNT.isdigit()
), "MAX_CHAT_COUNT must be a string which contains only characters of 0 - 9."

assert (
    int(MAX_CHAT_COUNT) % 2 == 0
), "MAX_CHAT_COUNT must be an even number. It records the user's message and the model's response."

MAX_CHAT_COUNT = int(MAX_CHAT_COUNT)

print("------------------ENV-------------------")
print(f"GOOGLE_AI_API_KEY: {mask_sensitive_data(GOOGLE_AI_API_KEY)}")
print(f"MAX_CHAT_COUNT: {MAX_CHAT_COUNT}")
print("----------------------------------------")

# ---------------------------------------------AI Configuration-------------------------------------------------

# Configure the generative AI model
genai.configure(api_key=GOOGLE_AI_API_KEY)
text_generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 512,
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]
text_model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=text_generation_config,
    safety_settings=safety_settings,
)

# ---------------------------------------------AI Generation History-------------------------------------------------


def send_message_and_get_reply(user_token, message):
    if user_token in chat_sessions:
        chat_session = chat_sessions[user_token]
    else:
        chat_session = ChatSession(user_token)
        chat_sessions[user_token] = chat_session

    chat_log = chat_session.get_chat_log()
    chat = text_model.start_chat(history=chat_log)
    chat_response = chat.send_message(message)

    if chat_response._error:
        return "❌" + str(chat_response._error)
    else:
        if MAX_CHAT_COUNT > 0:
            # If history is enabled, stores "part" objects of the chat history of both user and the model.
            chat_session.store_message(chat.history[-2], chat.history[-1])
            chat_session.prune_chat_log(MAX_CHAT_COUNT)
        return chat_response.text


# ---------------------------------------------Message History-------------------------------------------------
chat_sessions = {}

# ---------------------------------------------Flask web server---------------------------------------------

app = Flask(__name__)
if os.getenv("FLASK_ENV") != "production":
    print("-----------Development mode-------------")
    print("index.html, main.js and main.css will be served by Flask.")
    print("----------------------------------------")

    # Serve the index.html file, main.js and the main.css file if it is not production.
    # For development, we use the Flask web server to serve the static files.
    # For production, we use a CDN to serve the static files.
    @app.route("/", methods=["GET"])
    def serve_index_html():
        return render_template("index.html")

    @app.route("/main.js", methods=["GET"])
    def serve_main_js():
        response = make_response(render_template("main.js"))
        response.headers["Content-Type"] = "application/javascript"
        return response

    @app.route("/main.css", methods=["GET"])
    def serve_main_css():
        response = make_response(render_template("main.css"))
        response.headers["Content-Type"] = "text/css"
        return response


def get_user_token():
    user_token = request.cookies.get("user_token")
    if not user_token:
        # No token for this user, generate a new one. Use a cryptographically secure random UUID4.
        user_token = str(secure_uuid4())
    return user_token


def refresh_user_token(response, user_token):
    # Refresh user_token. Store it for 7 days
    response.set_cookie(
        "user_token", user_token, max_age=timedelta(days=7).total_seconds()
    )


@app.before_request
def cleanup_chat_sessions():
    # Prune chat_sessions dictionary
    for user_token, chat_session in list(chat_sessions.items()):
        if chat_session.last_updated < datetime.datetime.now() - timedelta(days=7):
            del chat_sessions[user_token]


@app.route("/api/ask-gemini", methods=["POST"])
def process_user_message_and_return_reply():
    user_token = get_user_token()

    message = request.form.get("message")
    if message is None:
        return "No message provided"

    # Process the query here
    print(f"Received query: {message}")
    reply = send_message_and_get_reply(user_token, message)
    print(f"Reply from model: {reply}")
    response = make_response(reply)

    refresh_user_token(response, user_token)
    return response


@app.route("/api/reset", methods=["GET"])
def reset_user_token():
    user_token = get_user_token()

    if user_token in chat_sessions:
        del chat_sessions[user_token]

    response = make_response(
        "🤖 History Reset for user: " + mask_sensitive_data(user_token)
    )
    refresh_user_token(response, user_token)
    return response


if __name__ == "__main__":
    app.run()


def create_app():
    return app
