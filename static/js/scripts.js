// script.js  
  
function sendMessage() {  
    const input = document.getElementById('chat-input');  
    const message = input.value.trim();  
    if(message === '') return; // Don't send empty messages  
  
    input.value = ''; // Clear the input after sending  
  
    const chatWindow = document.getElementById('chat-window');  
    const currentTime = new Date().toLocaleTimeString();  
  
    // Append user's message  
    chatWindow.innerHTML += `<div class="chat-message user-message"><span class="message-content">${message}</span><span class="message-time">${currentTime}</span></div>`;  
  
    // Show typing indicator  
    document.getElementById('typing-indicator').style.display = 'block';  
  
    // Scroll to the bottom of the chat window  
    chatWindow.scrollTop = chatWindow.scrollHeight;  
  
    // Send the message to the backend  
    fetch('/message', {  
        method: 'POST',  
        headers: {  
            'Content-Type': 'application/json',  
        },  
        body: JSON.stringify({ message: message }),  
    })  
    .then(response => response.json())  
    .then(data => {  
        // Hide typing indicator  
        document.getElementById('typing-indicator').style.display = 'none';  
  
        // Append bot's response  
        chatWindow.innerHTML += `<div class="chat-message bot-message"><span class="message-content">${data.response}</span><span class="message-time">${new Date().toLocaleTimeString()}</span></div>`;  
  
        // Scroll to the bottom of the chat window  
        chatWindow.scrollTop = chatWindow.scrollHeight;  
    })  
    .catch(error => {  
        console.error('Error:', error);  
        // Hide typing indicator in case of error as well  
        document.getElementById('typing-indicator').style.display = 'none';  
    });  
}  
  
function createThread() {  
    fetch('/create_thread', {  
        method: 'POST',  
    })  
    .then(response => response.json())  
    .then(data => {  
        if(data.thread_id) {  
            // Show temporary success message  
            const messageDiv = document.getElementById('thread-status-message');  
            messageDiv.textContent = 'New thread created successfully.';  
            messageDiv.style.display = 'block';  
              
            // Enable the send button  
            document.getElementById('send-button').disabled = false;  
  
            // Hide the message after 3 seconds  
            setTimeout(() => {  
                messageDiv.style.display = 'none';  
            }, 3000);  
        } else {  
            // Handle thread creation failure  
            // You can also display an error message in a similar way  
        }  
    })  
    .catch(error => {  
        console.error('Error:', error);  
        // Handle error scenario  
        // Display an error message if needed  
    });  
}  
  
// Remember to remove the inline 'onclick' in your HTML and use the event listener approach as shown previously  
document.querySelector('.create-thread-btn').addEventListener('click', createThread);  
