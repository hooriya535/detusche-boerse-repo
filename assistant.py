import os  
import time
from openai import AzureOpenAI  
from dotenv import load_dotenv
from functions import *  
import logging 


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
        self.system_prompt = """
        You are a financial AI assistant specialized in handling queries related to securities like stocks, ETFs, and bonds. Your role is to interpret and extract key identifiers such as names, ISINs (International Securities Identification Number), or WKNs (Wertpapierkennnummer) from user queries.
        - If a query does not include a clear identifier for a security, you should attempt to infer the necessary information using relevant context from the query. If you are unable to confidently extract or infer the required identifier, prompt the user to provide this information explicitly.
        - Once an identifier is extracted, utilize the `search_etfs` function to retrieve detailed information about Exchange-Traded Funds (ETFs) based on the extracted identifier, which can be the ETF's name, ticker symbol, or ISIN.
        - Clearly inform the user when you are making an inference about the identifier to ensure transparency.
        - Your responses should be strictly based on the information retrieved from the `search_etfs` function. If no relevant information is found or the query cannot be answered with the available data, respond with "I don't know." Do not fabricate or guess answers.
        """ 
        
        self.tools = [  
            {  
                "type": "function",  
                "function": {  
                    "name": "search_etfs",  
                    "description": "Retrieve detailed information about Exchange-Traded Funds (ETFs) based on a search query.",  
                    "parameters": {  
                        "type": "object",  
                        "properties": {  
                            "query": {  
                                "type": "string",  
                                "description": "The search query used to find ETFs, which can include the ETF's name, ticker symbol, or ISIN."  
                            }  
                        },  
                        "required": ["query"]  
                    }  
                }  
            }  
        ] 
  
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
                    output = search_etfs(arguments["query"])  
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
  
    
    def format_messages(self, messages) -> str:          
        last_assistant_message = ""  # To store the last assistant message  
        messages_list = []

        for message in messages:
            messages_list.append(message)
        
        # Loop through all messages  
        for message in reversed(messages_list):  
            if message.role == "assistant":  
                # Construct the message string for the assistant's message  
                message_content = " ".join(item.text.value for item in message.content)  
                last_assistant_message = f"Assistant: {message_content}\n"  
    
        return last_assistant_message.strip()  # Return only the last assistant message  
    
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
