import autogen
from user_proxy_webagent import UserProxyWebAgent
from groupchatweb import GroupChatManagerWeb
import asyncio

config_list = [
    {
        "model": "gpt-3.5-turbo",
    }
]
llm_config_assistant = {
    "model":"gpt-3.5-turbo",
    "temperature": 0,
    "config_list": config_list,
}
llm_config_proxy = {
    "model":"gpt-3.5-turbo-0613",
    "temperature": 0,
    "config_list": config_list,
}


#############################################################################################
# this is where you put your Autogen logic, here I have a simple 2 agents with a function call
class AutogenChat():
    def __init__(self, chat_id=None, websocket=None):
        self.websocket = websocket
        self.chat_id = chat_id
        self.client_sent_queue = asyncio.Queue()
        self.client_receive_queue = asyncio.Queue()

        self.ticket_allocation_agent = autogen.AssistantAgent(
            name="ticket_allocation_agent",
            llm_config=llm_config_assistant,
            max_consecutive_auto_reply=5,
            system_message="""  You are ticket_allocation_agent. you are the primary interface of spades labour hire. you will serve as the quinessential knowledge expert navigating users to the required flow . 
                                    you will act according to the instructions given below 

                                    INSTRUCTIONS:

                                    1. Welcome the user.Be very brief
                                    2. Ask the user if he a existing or new,  worker or client . 
                                    3. if he says existing proceeed with logging him in using his client/worker id, provide him with www.spades.com
                                    4. if he says he is a client ,ask him if he  wants to check labour hire rates or login.
                                    5. if he says he is a new worker, pass him to sales_onboarding_agent """
                                
                                
        )
        self.sales_onboarding_agent = autogen.AssistantAgent(
            name="sales_onboarding_agent",
            llm_config=llm_config_assistant,
            max_consecutive_auto_reply=5,
            system_message="""You are sales_onboarding_agent. You will onboard new workers onto spades labour hire
                                    you will act according to the instructions given below. reply in brief always.

                                    INSTRUCTIONS:
                                    1. Run a qualification check by asking the user if he currently resides in austrailia and if he has full time work rights in austrailia.
                                    3. If worker doesnt pass the qualification check , tell the user that he cant sign up with spades and terminate the chat.
                                    4. If worker passes the qualification check but he isnt ready to sign up , present resources to him to sign up at later stage
                                    5. If worker passes the qualification check and is ready to sign up , ask him whether he will like to sign up via chat or a form 
                                    6- if he chooses to fill form provide him this link,you can fill out [THIS FORM](https://airtable.com/appghOQDixD5tAfsw/shria02o78WzHtETH).
                                    6- if he chooses chat - ask the following questions:
                                      a) Signup process will take around 5 minutes, all questions need to be answered.
                                      b) please give your FULL NAME.[First Name and Last Name]
                                      c) Please give your VALID Phone Number. If the phone number is not of Australia. ask to provide valid phone number.
                                      d) Please give your Email Id.
                                      e) Kindly give me your location.
                                      f) please tell me your gender "Male", "Female", "Other".
                                      g)Inform worker basic details are saved, i will now ask you skills 
                                      h) Select skills [joiner, plumber .....]

                                         
                                     

                                        

                                    """ )
        


        

        self.allocation_agent = autogen.AssistantAgent(name="allocation_agent",
            llm_config=llm_config_assistant,
            max_consecutive_auto_reply=5,
            system_message = """
                                    You are allocation_agent. you will match workers with client projects with high precision considering factors such as skill level , location and availability 
                                    you will act according to the instructions given below 

                                    INSTRUCTIONS:

                                    
                                
                                

                                    
                                    """
                                    )


        self.book_keeping_agent = autogen.AssistantAgent(name="book_keeping_agent",
            llm_config=llm_config_assistant,
            max_consecutive_auto_reply=5,
            system_message = """
                                    You are book_keeping_agent. you will automate financial transactions , payroll and reporting thereby maintaining accurate and real time financial records. 
                                    you will act according to the instructions given below 

                                    INSTRUCTIONS:

                                    
                                
                                

                                    
                                    """
                                    )




        self.management_agent =autogen.AssistantAgent(name="management_agent",
            llm_config=llm_config_assistant,
            max_consecutive_auto_reply=5,
            system_message = """
                                    You are management_agent. you will oversee and refine operational workflows  ensuring high level coordination and  decision making efficiency. 
                                    you will act according to the instructions given below 

                                    INSTRUCTIONS:

                                

                                    
                                    """)

        self.user_proxy = UserProxyWebAgent( 
            name="user_proxy",
            human_input_mode="ALWAYS", 
            system_message="""Tell whatever you want to ticket_allocation_agent when prompted""",
            max_consecutive_auto_reply=5,
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config=False,)

        # add the queues to communicate 
        self.user_proxy.set_queues(self.client_sent_queue, self.client_receive_queue)

        self.groupchat = autogen.GroupChat(agents=[self.user_proxy, self.allocation_agent, self.ticket_allocation_agent,self.book_keeping_agent,self.management_agent,self.sales_onboarding_agent], messages=[], max_round=20)
        self.manager = GroupChatManagerWeb(groupchat=self.groupchat, 
            llm_config=llm_config_assistant,
            human_input_mode="ALWAYS" )     

    async def start(self, message):
        await self.user_proxy.a_initiate_chat(
            self.manager,
            clear_history=True,
            message=message
        )


