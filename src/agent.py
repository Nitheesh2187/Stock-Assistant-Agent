import os
import asyncio
import time
from groq import RateLimitError
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq
from src.utils import run_async_task, run_in_loop
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
            }
        )
        
        # Get tools from MCP client
        required_tools = [ "get_stock_quote", "get_stock_fundamentals", "get_stock_news", "get_stock_analysis", "firecrawl_scrape"]
        self.tools = asyncio.run(self.client.get_tools())

        self.selected_tools = []
        for tool in self.tools:
            if tool.name in required_tools:
                self.selected_tools.append(tool)
        
        # Initialize LLM
        self.llm = ChatGroq(
            model_name="qwen/qwen3-32b",
            temperature=0.2
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
            tools=self.selected_tools,
            prompt=prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.selected_tools,
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
        return [tool.name for tool in self.selected_tools]
    
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

agent= StockAssistanceAgent()

async def main():
    # Make sure to set your GROQ_API_KEY in your .env file   
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

    answer = await agent.chat("What is the news of Infosys?")
    print(str(answer))
    
    
    # Test portfolio calculation
    holdings = {"AAPL": 100, "GOOGL": 50, "MSFT": 75}
    prices = {"AAPL": 150.0, "GOOGL": 2500.0, "MSFT": 300.0}

# Example usage
if __name__ == "__main__":
    asyncio.run(main())    
