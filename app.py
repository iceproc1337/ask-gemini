import secrets
from datetime import timedelta
import os
from uuid import UUID
import google.generativeai as genai
from flask import Flask, request, render_template, make_response


def mask_sensitive_data(data):
    return "*" * (len(data) - 4) + data[-4:]


def secure_uuid4():
    return UUID(int=secrets.randbelow(1 << 128))


GOOGLE_GENERATIVE_LANGUAGE_API_KEY = os.getenv("GOOGLE_GENERATIVE_LANGUAGE_API_KEY")
MAX_HISTORY = int(os.getenv("MAX_HISTORY"))

assert MAX_HISTORY % 2 == 0, "MAX_HISTORY must be an even number. It records the user's message and the model's response."

print("------------------ENV-------------------")
print(
    f"GOOGLE_GENERATIVE_LANGUAGE_API_KEY: {mask_sensitive_data(GOOGLE_GENERATIVE_LANGUAGE_API_KEY)}"
)
print(f"MAX_HISTORY: {MAX_HISTORY}")
print("----------------------------------------")

# ---------------------------------------------AI Configuration-------------------------------------------------

# Configure the generative AI model
genai.configure(api_key=GOOGLE_GENERATIVE_LANGUAGE_API_KEY)
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
image_model = genai.GenerativeModel(
    model_name="gemini-pro-vision",
    generation_config=image_generation_config,
    safety_settings=safety_settings,
)

# ---------------------------------------------AI Generation History-------------------------------------------------


def send_user_query(user_id, query):
    chat_history = message_history.get(user_id, [])
    chat = text_model.start_chat(history=chat_history)
    chat_response = chat.send_message(query)

    if chat_response._error:
        return "❌" + str(chat_response._error)
    else:
        if MAX_HISTORY > 0:
            # If history is enabled, stores "part" objects of the chat history of both user and the model.
            update_message_history(user_id, chat.history[-2], chat.history[-1])
        return chat_response.text


# ---------------------------------------------Message History-------------------------------------------------
message_history = {}


def update_message_history(user_id, user_message, model_message):
    # Check if user_id already exists in the dictionary
    if user_id in message_history:
        # Append the new message to the user's message list
        message_history[user_id].extend([user_message, model_message])
        # If there are more than MAX_HISTORY messages, remove the oldest ones
        if len(message_history[user_id]) > MAX_HISTORY:
            num_messages_to_remove = len(message_history[user_id]) - MAX_HISTORY
            message_history[user_id] = message_history[user_id][num_messages_to_remove:]
    else:
        # If the user_id does not exist, create a new entry with the message
        message_history[user_id] = [user_message, model_message]


# ---------------------------------------------Flask web server---------------------------------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"  # replace with your secret key

if os.getenv("FLASK_ENV") != "production":
    print("-----------Development mode-------------")
    print("index.html, main.js and main.css will be served by Flask.")
    print("----------------------------------------")

    # Serve the index.html file, main.js and the main.css file if it is not production.
    # For development, we use the Flask web server to serve the static files.
    # For production, we use a CDN to serve the static files.
    @app.route("/", methods=["GET"])
    def serve_index():
        return render_template("index.html")

    @app.route("/main.js", methods=["GET"])
    def serve_index_js():
        response = make_response(render_template("main.js"))
        response.headers["Content-Type"] = "application/javascript"
        return response

    @app.route("/main.css", methods=["GET"])
    def serve_index_css():
        response = make_response(render_template("main.css"))
        response.headers["Content-Type"] = "text/css"
        return response


@app.route("/ask-gemini", methods=["POST"])
def ask_gemini():
    token = request.cookies.get("token")
    if not token:
        # No token for this user, generate a new one. Use a cryptographically secure random UUID4.
        token = str(secure_uuid4())

    query = request.form.get("query")
    # Process the query here
    print(f"Received query: {query}")

    response = make_response(send_user_query(token, query))
    # Refresh token. Store it for 30 days
    response.set_cookie("token", token, max_age=timedelta(days=30).total_seconds())

    return response


if __name__ == "__main__":
    app.run()
