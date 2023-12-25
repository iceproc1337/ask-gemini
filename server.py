from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/', methods=['GET'])
def serve_index():
    return render_template('index.html')

@app.route('/ask-gemini', methods=['POST'])
def ask_gemini():
    query = request.form.get('query')
    # Process the query here
    return 'Received query: ' + query

if __name__ == '__main__':
    app.run()
