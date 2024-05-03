import os  
import time
from openai import AzureOpenAI  
from dotenv import load_dotenv
from functions import *   
  
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
    
    def create_thread(self):  
        # Create a thread and return the thread ID  
        thread = self.client.beta.threads.create()  
        return thread.id 
    
    def call_functions(self, run) -> None:  
        print("Function Calling")  
        required_actions = run.required_action.submit_tool_outputs.model_dump()  
        print(required_actions)  
        tool_outputs = []  

        for action in required_actions["tool_calls"]:  
            func_name = action["function"]["name"]  
            arguments = json.loads(action["function"]["arguments"])  

            if func_name == "search_etfs":  
                output = search_etfs(arguments["query"])  
                tool_outputs.append({"tool_call_id": action["id"], "output": output})  
            else:  
                raise ValueError(f"Unknown function: {func_name}")  

        print("Submitting outputs back to the Assistant...")  
        self.client.beta.threads.runs.submit_tool_outputs(thread_id=run.thread_id, run_id=run.id, tool_outputs=tool_outputs) 
  
    
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
    
    def process_message(self, thread_id, content: str) -> None:  
        # Add a user question to the thread  
        self.client.beta.threads.messages.create(  
            thread_id= thread_id, 
            role="user",  
            content=content  # Replace this with your prompt  
        )  
  
        run = self.client.beta.threads.runs.create(  
            thread_id= thread_id, 
            assistant_id=self.assistant.id,  
        )  
  
        print("Processing...")  
        while True:  
            time.sleep(1)  
            run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)  
            if run.status == "completed":  
                messages = self.client.beta.threads.messages.list(thread_id=thread_id)  
                return self.format_messages(messages)  
            if run.status in ["failed", "expired", "cancelled"]:  
                # Handle failed, expired, and cancelled statuses  
                break  
            if run.status == "requires_action":  
                self.call_functions(run)  
            else:  
                time.sleep(5)  
