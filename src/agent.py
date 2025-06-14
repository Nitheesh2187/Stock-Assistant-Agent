import os
import asyncio
import time
from groq import RateLimitError
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv

class StockAssistanceAgent:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        self.llm = None
        self.tools = None
        self.memory = None
        self.agent_executor = None
        self.max_retries = 1
        
        # Initialize MCP client with math and weather servers
        print("API KEY: ",os.getenv("FIRECRAWL_API_KEY"))
        self.client = MultiServerMCPClient(
            {
                "stock_tools": {
                    "command": "uv",
                    # Make sure to update to the full absolute path to your math_server.py file
                    "args": [
                        "--directory",
                        "/home/nitheesh/Desktop/Stock_MCP",
                        "run",
                        "main.py"                
                    ],
                    "transport" : "stdio"
                },
                "firecrawl-mcp": {
                    "command": "npx",
                    "args": ["-y", "firecrawl-mcp"],
                    "env": {
                        "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY")
                    },
                    "transport" : "stdio"
                    }
                # "weather": {
                #     # make sure you start your weather server on port 8000
                #     "url": "http://localhost:8000/mcp",
                #     "transport": "streamable_http",
                # }
            }
        )
        
        # Get tools from MCP client
        self.tools = asyncio.run(self.client.get_tools())
        
        # Initialize LLM
        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.7
        )
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Setup the agent
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup the agent with tools and prompt template"""
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful stock market assistant with access to mathematical calculations and weather data.
            
            You can help with:
            - Stock market analysis and calculations
            - Financial computations
            - Weather-related market impacts
            - General investment guidance
            
            Use the available tools when needed for calculations or weather data.
            Be helpful, accurate, and provide clear explanations for your reasoning."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create the agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    async def chat(self, message: str) -> str:
        """
        Process a user message and return the agent's response
        
        Args:
            message (str): User's input message
            
        Returns:
            str: Agent's response
        """
        for attempt in range(self.max_retries):
            try:
                response = await self.agent_executor.ainvoke({
                                "input": message,
                                "chat_history": self.memory.chat_memory.messages
                            })
                return response["output"]  # Exit the loop if the request is successful
            
            except RateLimitError as e:
                if attempt >= self.max_retries - 1:
                    # print(f"Max retries reached.  Error: {e}")
                    return {"error": e}

                sleep_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limit exceeded. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            except Exception as e:
                # print(f"An unexpected error occurred: {e}")
                return {"error": e}
    
    def get_available_tools(self) -> list:
        """
        Get list of available tools
        
        Returns:
            list: List of available tool names
        """
        return [tool.name for tool in self.tools]
    
    def clear_memory(self):
        """Clear the conversation memory"""
        self.memory.clear()
    
    def get_conversation_history(self) -> list:
        """
        Get the current conversation history
        
        Returns:
            list: List of messages in the conversation
        """
        return self.memory.chat_memory.messages
    
    def clean_up(self):
        try:
            # Close MCP client connections
            if hasattr(self.client, 'close'):
                self.client.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    # def __enter__(self):
    #     """Context manager entry"""
    #     return self
    
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     """Context manager exit - cleanup resources"""
    #     try:
    #         # Close MCP client connections
    #         if hasattr(self.client, 'close'):
    #             self.client.close()
    #     except Exception as e:
    #         print(f"Error during cleanup: {e}")

# Example usage
if __name__ == "__main__":
    # Make sure to set your GROQ_API_KEY in your .env file   
    agent= StockAssistanceAgent()
    print("Stock Assistant Agent initialized!")
    print(f"Available tools: {agent.get_available_tools()}")
    
    # Example interactions
    print("\n" + "="*50)
    print("Example conversation:")
    
    # async def run_chat():
    #     print("\n" + "="*50)
    #     print("Example conversation:")

    #     response1 = await agent.chat("What is the price of Infosys?")
    #     print(f"Agent: {response1}")

    answer = asyncio.run(agent.chat("What is the price of Infosys?"))
    print(answer)
    
    
    # Test portfolio calculation
    holdings = {"AAPL": 100, "GOOGL": 50, "MSFT": 75}
    prices = {"AAPL": 150.0, "GOOGL": 2500.0, "MSFT": 300.0}
