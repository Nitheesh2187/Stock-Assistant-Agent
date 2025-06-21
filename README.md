# Stock Assistance Agent

A powerful AI-powered stock market assistant built with LangChain, Streamlit, and Model Context Protocol (MCP) servers. This intelligent agent provides comprehensive stock analysis, real-time quotes, fundamental data, market news, and web scraping capabilities to help you make informed investment decisions.

## 🚀 Features

- **Real-time Stock Quotes**: Get current stock prices and trading data
- **Fundamental Analysis**: Access P/E ratios, revenue growth, debt levels, and key financial metrics
- **Market News**: Stay updated with latest earnings, announcements, and market-moving news
- **Comprehensive Stock Analysis**: Combined analysis of price, fundamentals, and news
- **Web Scraping**: Extract data from financial websites using Firecrawl
- **Interactive Chat Interface**: Streamlit-based conversational UI
- **Memory Management**: Maintains conversation context for better interactions

## 🛠️ Architecture

This project leverages two MCP (Model Context Protocol) servers:

1. **Custom Stock MCP Server**: A specialized server for stock market data
   - Repository: [Stock Analysis MCP Server](https://github.com/Nitheesh2187/Stock-Analysis-MCP-Server.git)
   - Provides tools: `get_stock_quote`, `get_stock_fundamentals`, `get_stock_news`, `get_stock_analysis`
   - Powered by Alpha Vantage API for comprehensive financial data

2. **Firecrawl MCP Server**: Web scraping capabilities
   - Tool: `firecrawl_scrape`
   - Enables extraction of data from financial websites and news sources

## 📋 Prerequisites

- Python 3.8+
- Node.js (for Firecrawl MCP server)
- Docker and Docker Compose (for containerized deployment)

## 🔑 Required API Keys

You'll need to obtain the following API keys:

1. **ALPHAVANTAGE_API_KEY**: 
   - Get from [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
   - Free tier available, premium plans for higher request limits

2. **FIRECRAWL_API_KEY**: 
   - Get from [Firecrawl](https://firecrawl.dev/)
   - Used for web scraping capabilities

3. **GROQ_API_KEY**: 
   - Get from [Groq](https://console.groq.com/keys)
   - Powers the conversational AI using Qwen3-32B model

## 🚀 Installation & Setup

### Option 1: Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Nitheesh2187/Stock-Assistant-Agent.git
   cd stock-assistance-agent
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install the custom Stock MCP Server**
   ```bash
   pip install git+https://github.com/Nitheesh2187/Stock-Analysis-MCP-Server.git
   ```
   
   > **Note**: For detailed information about the Stock MCP Server, including its features, configuration options, and API documentation, please refer to the [Stock Analysis MCP Server repository](https://github.com/Nitheesh2187/Stock-Analysis-MCP-Server.git).

4. **Install Firecrawl MCP Server**
   ```bash
   npm install -g firecrawl-mcp
   ```

5. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   ALPHAVANTAGE_API_KEY=your_alphavantage_api_key_here
   FIRECRAWL_API_KEY=your_firecrawl_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

   The application will be available at `http://localhost:8501`

### Option 2: Docker Deployment

1. **Clone the repository**
   ```bash
   git clone https://github.com/Nitheesh2187/Stock-Assistant-Agent.git
   cd stock-assistance-agent
   ```

2. **Set up environment variables**
   
   Create a `.env` file in the project root with your API keys:
   ```env
   ALPHAVANTAGE_API_KEY=your_alphavantage_api_key_here
   FIRECRAWL_API_KEY=your_firecrawl_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

   Or

   Add the API keys in the docker compose file:
   ```env
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
      - ALPHAVANTAGE_API_KEY=${ALPHAVANTAGE_API_KEY}
    ```

3. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

   The application will be available at `http://localhost:8501`

4. **Run in detached mode (optional)**
   ```bash
   docker-compose up -d
   ```

5. **Stop the application**
   ```bash
   docker-compose down
   ```

## 🎯 Usage Examples

Once the application is running, you can interact with the Stock Assistant through the web interface:

### Indian Stock Market Examples:
- "What is the current price of Reliance Industries?"
- "Show me the fundamentals for TCS (TCS.NS)"
- "Get the latest news about Infosys stock"
- "Perform a comprehensive analysis of HDFC Bank (HDFCBANK.NS)"
- "What are the P/E ratios for IT sector stocks like Wipro and Tech Mahindra?"
- "Analyze State Bank of India (SBIN.NS) financials"
- "Show me Tata Motors stock performance and news"
- "Compare fundamentals of ICICI Bank vs HDFC Bank"
- "Get current price and analysis for Bharti Airtel"
- "What's the latest news on Adani Group stocks?"

### Global Market Examples:
- "What is the current price of Apple stock?"
- "Show me the fundamentals for Microsoft (MSFT)"
- "Get the latest news about Tesla"
- "Perform a comprehensive analysis of Google stock"
- "What are the P/E ratios for FAANG stocks?"

## 🏗️ Project Structure

```
stock-assistance-agent/
├── src/
│   ├── agent.py          # Main agent class
│   ├── style.css         # Streamlit styling
│   └── utils.py          # Utility functions (if any)
├── app.py                # Streamlit web application
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yaml   # Docker Compose configuration
├── .env.example         # Environment variables template
└── README.md           # This file
```

## 🔧 Configuration

### MCP Server Configuration

The agent is configured to use two MCP servers:

```python
{
    "stock_tools": {
        "command": "python",
        "args": ["-m", "stock_mcp.server"],
        "transport": "stdio"
    },
    "firecrawl-mcp": {
        "command": "npx",
        "args": ["-y", "firecrawl-mcp"],
        "env": {
            "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY")
        },
        "transport": "stdio"
    }
}
```

### Available Tools

- `get_stock_quote`: Real-time stock price data
- `get_stock_fundamentals`: Financial metrics and ratios
- `get_stock_news`: Latest market news and announcements
- `get_stock_analysis`: Comprehensive stock analysis
- `firecrawl_scrape`: Web scraping for additional data

## 🐛 Troubleshooting

### Common Issues:

1. **MCP Server Connection Failed**
   - Ensure all API keys are correctly set in `.env`
   - Verify the Stock MCP Server is properly installed
   - Check that Node.js is installed for Firecrawl MCP

2. **Rate Limit Errors**
   - The agent includes exponential backoff for rate limiting
   - Consider upgrading API plans for higher limits

3. **Docker Issues**
   - Ensure Docker and Docker Compose are installed
   - Check that ports 8501 is available
   - Verify `.env` file is in the correct location

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


## 🔗 Related Resources

- [Stock Analysis MCP Server](https://github.com/Nitheesh2187/Stock-Analysis-MCP-Server.git) - Custom MCP server for stock data
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Alpha Vantage API](https://www.alphavantage.co/documentation/)
- [Firecrawl Documentation](https://docs.firecrawl.dev/)
- [Groq Documentation](https://console.groq.com/docs)