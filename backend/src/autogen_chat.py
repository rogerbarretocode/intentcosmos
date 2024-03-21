import autogen
from user_proxy_webagent import UserProxyWebAgent
import asyncio
from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent

from websocket_proxy import WebSocketProxy


config_list = [
    {
        "model": "gpt-3.5-turbo",
    }
]
llm_config_assistant = {
    "model":"gpt-3.5-turbo",
    "temperature": 0,
    "config_list": config_list,
        "functions": [
        {
            "name": "search_db",
            "description": "Search database for order status",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "integer",
                        "description": "Order number",
                    },
                    "customer_number": {
                        "type": "string",
                        "description": "Customer number",
                    }
                },
                "required": ["order_number","customer_number"],
            },
        },
    ],
}
llm_config_proxy = {
    "model":"gpt-3.5-turbo-0613",
    "temperature": 0,
    "config_list": config_list,
}


#############################################################################################
# this is where you put your Autogen logic, here I have a simple 2 agents with a function call
class AutogenChat():
    def __init__(self, chat_id: str, websocket: WebSocketProxy):
        self.websocket: WebSocketProxy = websocket
        self.chat_id = chat_id
        self.client_sent_queue = asyncio.Queue()
        self.client_receive_queue = asyncio.Queue()

       

        self.intent_agent = GPTAssistantAgent(name="intent_agent",
                        instructions = """
                                    you are intent_agent. you possess knowledge of all psychology models in the world . 

                                    INSTRUCTIONS:
                                    1 .You will welcome the user 
                                    2. you will ask user_proxy for schwartz value and input string and time 
                                    3. you will generate 10 more strings related to input string based on the schwartz value  with cosine similarity of 1-3 sigma which a user would usually search on youtube
                                    4. Based on the time you will generate different strings that suit the mood of the user_proxy at that time . use your psychology knowledge for this .
                                    5. STRICTLY Dont mention the schwartz value in any form  in the generated string. 
                                    6. Generate the strings on topics that fall in the same category as input string . The generated string need not have words of the input string but should match the theme and category.
                                    

                                        
                                        """,
                                        llm_config = llm_config_proxy)






        #create a UserProxyAgent instance named "user_proxy"
        self.user_proxy = UserProxyWebAgent(
            name="user_proxy",
            human_input_mode="ALWAYS",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config={
                "work_dir": "coding",
                "use_docker": False, 
                },
            # Please set use_docker=True if docker is available to run the generated code. Using docker is safer than running the generated code directly.
            system_message ="""Tell whatever you want to intent_agent when prompted"""

        )








        # add the queues to communicate 
        self.user_proxy.set_queues(self.client_sent_queue, self.client_receive_queue)

    async def start(self, message):
        await self.user_proxy.a_initiate_chat(
            self.intent_agent,
            clear_history=True,
            message=message
        )

    #MOCH Function call 
    def search_db(self, order_number=None, customer_number=None):
        return "Order status: delivered TERMINATE"

