import datetime
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import google.generativeai as genai
from threading import Lock
from datetime import timedelta
from flask import Flask, request, render_template, make_response
from src.security.secure_uuid4 import secure_uuid4
from src.security.mask_sensitive_data import mask_sensitive_data
from src.ChatSession import ChatSession

chat_sessions_lock = Lock()

# -------------------------------------------------DOTENV------------------------------------------------------

GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
MAX_CHAT_COUNT = os.getenv("MAX_CHAT_COUNT")
LOG_PATH = os.getenv("LOG_PATH")
LOG_ROTATE_BACKUP_COUNT = os.getenv("LOG_ROTATE_BACKUP_COUNT")

assert GOOGLE_AI_API_KEY, "GOOGLE_AI_API_KEY is not set."
assert MAX_CHAT_COUNT, "MAX_CHAT_COUNT is not set."

assert MAX_CHAT_COUNT.isdigit(), "MAX_CHAT_COUNT must be a string of digits."

assert (
    int(MAX_CHAT_COUNT) % 2 == 0
), "MAX_CHAT_COUNT must be an even number. It records the user's message and the model's response."

MAX_CHAT_COUNT = int(MAX_CHAT_COUNT)

assert (
    LOG_ROTATE_BACKUP_COUNT.isdigit()
), "LOG_ROTATE_BACKUP_COUNT must be a string of digits."

LOG_ROTATE_BACKUP_COUNT = int(LOG_ROTATE_BACKUP_COUNT)

# ---------------------------------------------Summary-------------------------------------------------

print("------------------ENV-------------------")
print(f"GOOGLE_AI_API_KEY: {mask_sensitive_data(GOOGLE_AI_API_KEY)}")
print(f"MAX_CHAT_COUNT: {MAX_CHAT_COUNT}")
print(f"LOG_PATH: {LOG_PATH}")
print(f"LOG_ROTATE_BACKUP_COUNT: {LOG_ROTATE_BACKUP_COUNT}")

# ---------------------------------------------Logging-------------------------------------------------

# This is the logger used by waitress
logger = logging.getLogger("waitress")


logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    u"[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

stdout_handler = TimedRotatingFileHandler(
    os.path.join(LOG_PATH, "webapp-debug.log"),
    when="midnight",
    backupCount=LOG_ROTATE_BACKUP_COUNT,
    encoding="utf-8"
)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)

stderr_handler = TimedRotatingFileHandler(
    os.path.join(LOG_PATH, "webapp-error.log"),
    when="midnight",
    backupCount=LOG_ROTATE_BACKUP_COUNT,
    encoding="utf-8"
)
stderr_handler.setLevel(logging.ERROR)
stderr_handler.setFormatter(formatter)

# Write application log to stdout and stderr
logger.addHandler(stdout_handler)
logger.addHandler(stderr_handler)

# Also log traffic logs to stdout and stderr
trans_logger = logging.getLogger("wsgi")
trans_logger.addHandler(stdout_handler)
trans_logger.addHandler(stderr_handler)

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
        # logger.debug(f"New chat session for user: {mask_sensitive_data(user_token)}")
        chat_session = chat_sessions[user_token]
    else:
        # logger.debug(f"Found existing session for user: {mask_sensitive_data(user_token)}")
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
            content_from_user = chat.history[-2]
            content_from_model = chat.history[-1]

            # For debugging
            # logger.debug(f"prompt_object_from_user: {response_content_from_user}")
            # logger.debug(f"prompt_object_from_model: {response_content_from_model}")

            # Calculate the length of the text in the message part of the Content object
            text_length_sum_from_user = sum(
                len(part.text) for part in content_from_user.parts
            )
            text_length_sum_from_model = sum(
                len(part.text) for part in content_from_model.parts
            )

            # Produce a masked message of the same length for the message of the user and the model
            masked_message_from_user = text_length_sum_from_user * "*"
            masked_message_from_model = text_length_sum_from_model * "*"

            logger.debug(
                f"Storing chat history for user: {mask_sensitive_data(user_token)}, {masked_message_from_user}, {masked_message_from_model}"
            )
            chat_session.store_message(content_from_user, content_from_model)
            chat_session.prune_chat_log(MAX_CHAT_COUNT)
        return chat_response.text


# ---------------------------------------------Message History-------------------------------------------------
chat_sessions = {}

# ---------------------------------------------Flask web server---------------------------------------------

app = Flask(__name__)
if os.getenv("FLASK_ENV") != "production":
    logger.info("-----------Development mode-------------")
    logger.info("index.html, main.js and main.css will be served.")

    # Enable Flask debugging
    logging.basicConfig(level=logging.DEBUG)

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
        logger.debug(f"New user_token: {mask_sensitive_data(user_token)}")
    return user_token


def refresh_user_token(response, user_token):
    # Refresh user_token. Store it for 7 days
    response.set_cookie(
        "user_token",
        user_token,
        max_age=timedelta(days=7).total_seconds(),
        samesite="None",
        secure=True,
    )


last_cleanup_timestamp = datetime.datetime.now()


@app.before_request
def cleanup_chat_sessions():
    global last_cleanup_timestamp

    # Check if an hour has passed since the last cleanup
    if datetime.datetime.now() - last_cleanup_timestamp < timedelta(hours=1):
        return

    # Prune chat_sessions dictionary
    cleanup_count = 0
    logger.debug(f"Cleanup chat_sessions: {len(chat_sessions)} keys in store.")
    with chat_sessions_lock:
        for user_token, chat_session in list(chat_sessions.items()):
            if chat_session.last_updated < datetime.datetime.now() - timedelta(days=7):
                logger.debug(f"Removing user_token: {mask_sensitive_data(user_token)}")
                del chat_sessions[user_token]
                cleanup_count += 1

    # Update the last cleanup timestamp
    last_cleanup_timestamp = datetime.datetime.now()
    logger.info(
        f"Last cleanup finished at {last_cleanup_timestamp}, {cleanup_count} keys removed."
    )


@app.route("/api/ask-gemini", methods=["POST"])
def process_user_message_and_return_reply():
    user_token = get_user_token()
    logger.debug(f"Access from user: {mask_sensitive_data(user_token)}")

    message = request.form.get("message")
    if message is None:
        return "No message provided"

    # For debugging
    # logger.debug(f"Received query: {mask_sensitive_data(message)}")

    reply = send_message_and_get_reply(user_token, message)

    # For debugging
    # logger.debug(f"Reply from model: {mask_sensitive_data(reply)}")

    response = make_response(reply)

    # Refresh user_token on each api request
    refresh_user_token(response, user_token)

    return response


@app.route("/api/reset", methods=["GET"])
def reset_user_token():
    user_token = get_user_token()
    history_reset_reply = (
        f"🤖 History Reset for user: {mask_sensitive_data(user_token)}"
    )

    if user_token in chat_sessions:
        del chat_sessions[user_token]

    logger.debug(history_reset_reply)
    response = make_response(history_reset_reply)

    # Refresh user_token on each api request
    refresh_user_token(response, user_token)

    return response


# ---------------------------------------------Main-------------------------------------------------

if __name__ == "__main__":
    app.run()


def create_app():
    return app
