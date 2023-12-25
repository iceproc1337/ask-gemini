import os
import google.generativeai as genai
from flask import Flask, request, render_template, Response


def mask_sensitive_data(data):
    return "*" * (len(data) - 4) + data[-4:]


GOOGLE_GENERATIVE_LANGUAGE_API_KEY = os.getenv("GOOGLE_GENERATIVE_LANGUAGE_API_KEY")
MAX_HISTORY = int(os.getenv("MAX_HISTORY"))

print(
    f"GOOGLE_GENERATIVE_LANGUAGE_API_KEY: {mask_sensitive_data(GOOGLE_GENERATIVE_LANGUAGE_API_KEY)}"
)
print(f"MAX_HISTORY: {MAX_HISTORY}")

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


def generate_response_with_text(message_text):
    prompt_parts = [message_text]
    print("Got textPrompt: " + message_text)
    response = text_model.generate_content(prompt_parts, stream=True)
    if response._error:
        return "❌" + str(response._error)
    
    for chunk in response:
        yield(chunk.text)

# ---------------------------------------------Flask web server---------------------------------------------

app = Flask(__name__)


@app.route("/", methods=["GET"])
def serve_index():
    return render_template("index.html")


@app.route("/ask-gemini", methods=["POST"])
def ask_gemini():
    query = request.form.get("query")
    # Process the query here
    print(f"Received query: {query}")
    response = generate_response_with_text(query)
    return Response(response, mimetype='text/plain')

if __name__ == "__main__":
    app.run()
