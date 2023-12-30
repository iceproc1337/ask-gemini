import datetime
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import string
import google.generativeai as genai
from threading import Lock
from datetime import timedelta
from flask import Flask, request, make_response, send_from_directory
from src.security.mask_sensitive_data import mask_sensitive_data
from src.ChatSession import ChatSession
from werkzeug.exceptions import HTTPException
from google.generativeai.types import StopCandidateException
from PIL import Image

chat_sessions_lock = Lock()

# -------------------------------------------------DOTENV------------------------------------------------------

GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
MAX_CHAT_COUNT = os.getenv("MAX_CHAT_COUNT")
LOG_PATH = os.getenv("LOG_PATH")
LOG_ROTATE_BACKUP_COUNT = os.getenv("LOG_ROTATE_BACKUP_COUNT")

HARM_CATEGORY_HARASSMENT_THRESHOLD = os.getenv("HARM_CATEGORY_HARASSMENT_THRESHOLD")
HARM_CATEGORY_HATE_SPEECH_THRESHOLD = os.getenv("HARM_CATEGORY_HATE_SPEECH_THRESHOLD")
HARM_CATEGORY_SEXUALLY_EXPLICIT_THRESHOLD = os.getenv(
    "HARM_CATEGORY_SEXUALLY_EXPLICIT_THRESHOLD"
)
HARM_CATEGORY_DANGEROUS_CONTENT_THRESHOLD = os.getenv(
    "HARM_CATEGORY_DANGEROUS_CONTENT_THRESHOLD"
)


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

print(f"HARM_CATEGORY_HARASSMENT_THRESHOLD: {HARM_CATEGORY_HARASSMENT_THRESHOLD}")
print(f"HARM_CATEGORY_HATE_SPEECH_THRESHOLD: {HARM_CATEGORY_HATE_SPEECH_THRESHOLD}")
print(
    f"HARM_CATEGORY_SEXUALLY_EXPLICIT_THRESHOLD: {HARM_CATEGORY_SEXUALLY_EXPLICIT_THRESHOLD}"
)
print(
    f"HARM_CATEGORY_DANGEROUS_CONTENT_THRESHOLD: {HARM_CATEGORY_DANGEROUS_CONTENT_THRESHOLD}"
)


# ---------------------------------------------Logging-------------------------------------------------

# This is the logger used by waitress
logger = logging.getLogger("waitress")


logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

stdout_handler = TimedRotatingFileHandler(
    os.path.join(LOG_PATH, "webapp-debug.log"),
    when="midnight",
    backupCount=LOG_ROTATE_BACKUP_COUNT,
    encoding="utf-8",
)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)

stderr_handler = TimedRotatingFileHandler(
    os.path.join(LOG_PATH, "webapp-error.log"),
    when="midnight",
    backupCount=LOG_ROTATE_BACKUP_COUNT,
    encoding="utf-8",
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
image_generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 512,
}
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": HARM_CATEGORY_HARASSMENT_THRESHOLD,
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": HARM_CATEGORY_HATE_SPEECH_THRESHOLD,
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": HARM_CATEGORY_SEXUALLY_EXPLICIT_THRESHOLD,
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": HARM_CATEGORY_DANGEROUS_CONTENT_THRESHOLD,
    },
]

text_model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=text_generation_config,
    safety_settings=safety_settings,
)

image_model = genai.GenerativeModel(
    model_name="gemini-pro-vision",
    generation_config=image_generation_config,
    safety_settings=safety_settings,
)


# ---------------------------------------------AI Generation History-------------------------------------------------


def send_message_and_get_reply(user_token, message, image=None):
    if user_token in chat_sessions:
        # logger.debug(f"New chat session for user: {mask_sensitive_data(user_token)}")
        chat_session = chat_sessions[user_token]
    else:
        # logger.debug(f"Found existing session for user: {mask_sensitive_data(user_token)}")
        chat_session = ChatSession(user_token)
        chat_sessions[user_token] = chat_session

    chat_log = chat_session.get_chat_log()

    if image is None:
        chat = text_model.start_chat(history=chat_log)
    else:
        chat = image_model.start_chat(history=[]) # 400 Multiturn chat is not enabled for models/gemini-pro-vision

    try:
        if image is None:
            chat_response = chat.send_message(message)
        else:
            image_pil = Image.open(image.stream)
            chat_response = chat.send_message([message, image_pil])
    except StopCandidateException as e:
        # Try to return the error message from the API
        try:
            exception_message = ""
            for i in range(len(e.args[0].content.parts)):
                exception_message += e.args[0].content.parts[i].text
                if i < len(e.args[0].content.parts) - 1:
                    exception_message += "\n"
            logger.error(exception_message)
            return exception_message
        except Exception as e:
            logger.error(e)
            return str(e)
    except Exception as e:
        # For debugging
        # logger.error(e)
        # print("-----")
        # print(dir(e.args[0]))
        # print("-----")
        # print(e.args[0])
        # print("-----")

        # Log whatever error message we can get
        logger.error(e)
        return str(e)

    # 400 Multiturn chat is not enabled for models/gemini-pro-vision
    if image is None and MAX_CHAT_COUNT > 0:
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

app = Flask(__name__, template_folder="client/dist")
if os.getenv("FLASK_ENV") != "production":
    logger.info("-----------Development mode-------------")
    logger.info("index.html, main.js and main.css will be served.")

    # Enable Flask debugging
    logging.basicConfig(level=logging.DEBUG)

    # Serve static assets from the "client/dist" folder for all routes "/"
    @app.route("/", methods=["GET"])
    def serve_static_assets():
        return send_from_directory("client/dist", "index.html")

    @app.route("/<path:path>", methods=["GET"])
    def serve_static_files(path):
        return send_from_directory("client/dist", path)


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


def is_token_valid(token):
    if not token:
        print("No token provided")
        return False

    if len(token) != 32:
        print("Invalid token length")
        return False

    if not all(c in string.hexdigits for c in token):
        print("Invalid token format")
        return False

    return True


@app.route("/api/ask-gemini", methods=["POST"])
def process_user_message_and_return_reply():
    user_token = request.form.get("token")

    if not is_token_valid(user_token):
        return "Invalid token"

    logger.debug(f"Access from user: {mask_sensitive_data(user_token)}")

    message = request.form.get("message")
    if message is None:
        return "No message provided"

    image = request.files.get("image")  # Get the image from request.files

    # For debugging
    # logger.debug(f"Received query: {mask_sensitive_data(message)}")

    reply = send_message_and_get_reply(user_token, message, image)

    # For debugging
    # logger.debug(f"Reply from model: {mask_sensitive_data(reply)}")

    response = make_response(reply)

    return response


@app.route("/api/reset", methods=["POST"])
def reset_user_token():
    user_token = request.form.get("token")
    print(f"Resetting user_token: {mask_sensitive_data(user_token)}")

    if not is_token_valid(user_token):
        return "Invalid token"

    history_reset_reply = (
        f"🤖 History Reset for user: {mask_sensitive_data(user_token)}"
    )

    if user_token in chat_sessions:
        del chat_sessions[user_token]

    logger.debug(history_reset_reply)
    response = make_response(history_reset_reply)

    return response


@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e

    # now you're handling non-HTTP exceptions only
    logger.error(e)

    if hasattr(e, "message") and hasattr(e, "code"):
        return str(e.message), e.code
    else:
        return str(e), 500


# ---------------------------------------------Main-------------------------------------------------

if __name__ == "__main__":
    app.run()


def create_app():
    return app
