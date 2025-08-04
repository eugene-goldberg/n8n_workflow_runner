"""Main entry point for running the agent."""

import asyncio
import logging
from typing import Optional

import click

from src.agents.main_agent import AgentRunner
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.app.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--query', '-q', help='Query to process')
@click.option('--interactive', '-i', is_flag=True, help='Run in interactive mode')
@click.option('--thread-id', '-t', help='Thread ID for conversation continuity')
def main(query: Optional[str], interactive: bool, thread_id: Optional[str]):
    """Run the LangGraph Agentic RAG agent."""
    
    # Validate settings
    try:
        settings.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    # Run the agent
    asyncio.run(run_agent(query, interactive, thread_id))


async def run_agent(query: Optional[str], interactive: bool, thread_id: Optional[str]):
    """Run the agent asynchronously."""
    
    agent = AgentRunner()
    
    if query:
        # Single query mode
        logger.info(f"Processing query: {query}")
        
        if thread_id:
            result = await agent.continue_conversation(query, thread_id)
        else:
            result = await agent.run(query)
        
        print(f"\nAnswer: {result['answer']}")
        print(f"\nMetadata: {result['metadata']}")
        print(f"Thread ID: {result['thread_id']} (use this to continue the conversation)")
    
    elif interactive:
        # Interactive mode
        print("🤖 LangGraph Agentic RAG - Interactive Mode")
        print("Type 'exit' to quit, 'new' to start a new conversation")
        print("-" * 50)
        
        current_thread_id = None
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() == 'exit':
                    break
                elif user_input.lower() == 'new':
                    current_thread_id = None
                    print("Starting new conversation...")
                    continue
                elif not user_input:
                    continue
                
                # Process the query
                if current_thread_id:
                    result = await agent.continue_conversation(user_input, current_thread_id)
                else:
                    result = await agent.run(user_input)
                    current_thread_id = result['thread_id']
                
                print(f"\nAssistant: {result['answer']}")
                
                # Show metadata in debug mode
                if settings.app.log_level == "DEBUG":
                    print(f"\n[Debug] Route: {result['metadata'].get('route')}")
                    print(f"[Debug] Tools: {result['metadata'].get('tools_used')}")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"\nError: {e}")
    
    else:
        print("Please provide a query with -q or use interactive mode with -i")


if __name__ == "__main__":
    main()