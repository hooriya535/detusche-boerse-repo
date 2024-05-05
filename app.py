from flask import Flask, request, jsonify, render_template, session  
from assistant import Assistant  
import logging
import sys

# Configure logging to output to the console and set the level to DEBUG  
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s') 
  
app = Flask(__name__)  
app.secret_key = 'khalil_secret'
  
# Instantiate the Assistant class  
assistant = Assistant()  
  
@app.route('/')  
def index():  
    app.logger.debug('Index page visited')
    # Render the chat interface  
    return render_template('index.html')  

@app.route('/create_thread', methods=['POST'])  
def create_thread():  
    try:  
        thread_id = assistant.create_thread()  
        session['thread_id'] = thread_id  
        logging.info(f'Thread created with ID: {thread_id}')  
        return jsonify({'thread_id': thread_id})  
    except Exception as e:  
        logging.error(f'Error creating thread: {e}')  
        return jsonify({'error': str(e)}), 500   
  
@app.route('/message', methods=['POST'])  
def message():  
    try:  
        content = request.json['message']  
        thread_id = session.get('thread_id')  
        if not thread_id:  
            logging.warning('No thread ID found. Message without thread.')  
            return jsonify({'error': 'No thread ID found. Please create a new thread.'}), 400  
        response = assistant.process_message(thread_id, content)  
        logging.info(f'Message processed for thread_id {thread_id}')  
        return jsonify({'response': response})  
    except Exception as e:  
        logging.error(f'Error processing message for thread_id {thread_id}: {e}')  
        return jsonify({'error': str(e)}), 500  
  
if __name__ == '__main__':  
    logging.info('Starting the application...')  
    app.run(debug=True)  
    #pass

