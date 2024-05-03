from flask import Flask, request, jsonify, render_template, session  
from assistant import Assistant  
  
app = Flask(__name__)  
app.secret_key = 'khalil_secret'
  
# Instantiate the Assistant class  
assistant = Assistant()  
  
@app.route('/')  
def index():  
    # Render the chat interface  
    return render_template('index.html')  

@app.route('/create_thread', methods=['POST'])  
def create_thread():  
    thread_id = assistant.create_thread()  
    session['thread_id'] = thread_id  # Store the thread ID in the user's session  
    return jsonify({'thread_id': thread_id})  
  
@app.route('/message', methods=['POST'])  
def message():  
    content = request.json['message']  
    thread_id = session.get('thread_id')  # Retrieve the thread ID from the user's session  
    if not thread_id:  
        return jsonify({'error': 'No thread ID found. Please create a new thread.'}), 400  
    response = assistant.process_message(thread_id, content)  
    return jsonify({'response': response})  
  
if __name__ == '__main__':  
    #app.run(debug=True)  
    pass

