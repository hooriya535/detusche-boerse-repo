import os  
import time
from openai import AzureOpenAI  
from dotenv import load_dotenv
from functions import *  
import logging 
from flask import current_app  

logger = logging.getLogger(__name__)
 
# Load the .env file  
load_dotenv()  
  
class Assistant: 
     
    def __init__(self):  
        # Retrieve the environment variables  
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")  
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")  
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION")  
        self.model_name = os.getenv("AZURE_OPENAI_MODEL_NAME")  
  
        # Ensure the variables are set  
        if not self.api_key or not self.azure_endpoint or not self.api_version or not self.model_name:  
            raise ValueError("Error loading env variables from .env file.")  
  
        # Initialize the Azure OpenAI client  
        self.client = AzureOpenAI(  
            api_key=self.api_key,  
            api_version=self.api_version,  
            azure_endpoint=self.azure_endpoint  
        )  

        # Create an assistant  
        with open("assistant_tools/system_prompt.txt",'r') as system_prompt_file:
            self.system_prompt = system_prompt_file.read()

        with open("assistant_tools/assistant_tools.json",'r') as assistant_tools_file:
            self.tools = json.load(assistant_tools_file)["tools"]
  
        self.assistant = self.client.beta.assistants.create(  
            instructions=self.system_prompt,  
            model=self.model_name, 
            tools=self.tools  
        )  
        
        logger.info("Assistant class initialized.") 
    
    def create_thread(self):  
        try:  
            thread = self.client.beta.threads.create()  
            logger.info(f"Assistant is Creating Thread with ID: {thread.id}")  
            return thread.id  
        except Exception as e:  
            logger.error(f"Assitant Failed to create thread: {e}")  
            raise
    
    def call_functions(self, run):  
        logger.info("Function Calling")  
        required_actions = run.required_action.submit_tool_outputs.model_dump()  
        logger.info(f"Required actions: {required_actions}")  
        tool_outputs = []  
  
        for action in required_actions["tool_calls"]:  
            func_name = action["function"]["name"]  
            arguments = json.loads(action["function"]["arguments"])  
  
            try:  
                if func_name == "search_etfs":  
                    output = search_etfs(arguments["query"],arguments.get("entries",10),arguments.get("sort",'{"shareClassVolume": "desc"}'))  
                    tool_outputs.append({"tool_call_id": action["id"], "output": output})  
                    logger.info(f"Function {func_name} called with arguments {arguments}. Output: {output}")  
                else:  
                    logger.error(f"Unknown function: {func_name}")  
                    raise ValueError(f"Unknown function: {func_name}")  
            except Exception as e:  
                logger.exception(f"Error calling function {func_name} with arguments {arguments}: {e}", exc_info=True)  
                raise  
  
        logger.info("Submitting outputs back to the Assistant...")  
        self.client.beta.threads.runs.submit_tool_outputs(  
            thread_id=run.thread_id,  
            run_id=run.id,  
            tool_outputs=tool_outputs  
        )  
        logger.info("Outputs submitted successfully.") 
    
    def format_messages(self, messages) -> list:  
        formatted_messages = []  
        found_last_user_message = False  
    
        # Convert messages cursor to a list and reverse it  
        messages_list = list(messages)  
        messages_list.reverse()  
       # print("******")
        #print(messages_list)
    
        for message in messages:  
            if message.role == "user":  
                 return formatted_messages[::-1] 
            # If we've found the last user message, start formatting the assistant messages  
            for content_item in message.content:  
                if content_item.type == "text":  
                    formatted_messages.append({  
                        'type': 'text',  
                        'content': content_item.text.value  
                    })  
                elif content_item.type == "image_file":  
                    # Ensure the assistant_outputs directory exists  
                    output_dir = './assistant_outputs'  
                    os.makedirs(output_dir, exist_ok=True)  
                    
                    # Process and save the image file  
                    image_file_id = content_item.image_file.file_id  
                    image_data = self.client.files.content(image_file_id)  
                    image_data_bytes = image_data.read()  
                    image_path = os.path.join(output_dir, f"image_{image_file_id}.png")  
                    with open(image_path, "wb") as file:  
                        file.write(image_data_bytes)  
                        print(f"Image {image_file_id} saved as {image_path}")  
                    base_url = current_app.config['BASE_URL'] 
                    image_url = f"{base_url}/assistant_outputs/image_{image_file_id}.png"  
                    formatted_messages.append({  
                        'type': 'image',  
                        'content': image_url  
                    })  
    # Since we iterated in reverse, we need to reverse the formatted_messages list  
    # to maintain the chronological order for rendering.  
        return formatted_messages[::-1]  

        
    def process_message(self, thread_id, content: str):  
        logger.info(f"Received message for processing: '{content}' in thread ID: {thread_id}")  
        try:  
            # Add a user question to the thread  
            self.client.beta.threads.messages.create(  
                thread_id=thread_id,  
                role="user",  
                content=content 
            )  
  
            # Start the processing run  
            run = self.client.beta.threads.runs.create(  
                thread_id=thread_id,  
                assistant_id=self.assistant.id,  
            )  
  
            logger.info("Processing...")  
            while True:  
                time.sleep(1)  # Avoid busy-waiting  
                run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)  
                if run.status == "completed":  
                    messages = self.client.beta.threads.messages.list(thread_id=thread_id)  
                    response = self.format_messages(messages)  
                    logger.info(f"Completed processing message for thread ID: {thread_id}. Response: {response}")  
                    return response  
                elif run.status in ["failed", "expired", "cancelled"]:  
                    logger.error(f"Run status {run.status} for thread ID: {thread_id}.")  
                    return f"Run failed with status: {run.status}"  
                elif run.status == "requires_action":  
                    logger.info("Run requires action. Calling functions.")  
                    self.call_functions(run)  
                else:  
                    logger.debug(f"Run status {run.status} for thread ID: {thread_id}. Waiting for completion...")  
                    time.sleep(5)  # Wait before checking the status again  
        except Exception as e:  
            logger.exception(f"An error occurred while processing message for thread ID: {thread_id}: {e}", exc_info=True)  
            raise  
