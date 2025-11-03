"""
RAG Agent with Planning and Tool Use
Uses LangGraph for agent orchestration
"""

from typing import List, Dict, Any, Optional, TypedDict, Annotated
import json
import re
from loguru import logger
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.nim_clients.llm_client import NIMClient
from src.agent.tools import get_tools_description


class AgentState(TypedDict):
    """State for the agent"""
    messages: List[Dict[str, str]]
    plan: Optional[str]
    current_step: int
    max_steps: int
    tools_output: List[str]
    final_answer: Optional[str]


class RAGAgent:
    """Agentic RAG system with planning and tool use"""

    def __init__(
        self,
        llm_client: NIMClient,
        tools: List[Any],
        max_iterations: int = 10,
    ):
        """
        Initialize RAG agent

        Args:
            llm_client: NIM LLM client
            tools: List of tools available to the agent
            max_iterations: Maximum number of planning/execution iterations
        """
        self.llm_client = llm_client
        self.tools = {tool.name: tool for tool in tools}
        self.max_iterations = max_iterations

        # System prompt for the agent
        self.system_prompt = """You are a helpful AI assistant with access to tools.

Your task is to help answer user questions by:
1. Planning the steps needed to answer the question
2. Using available tools when needed
3. Synthesizing information from tool outputs
4. Providing clear, accurate answers with source citations when applicable

When using tools:
- Use the retrieval tool to search the knowledge base for relevant information
- Always cite sources when using retrieved information
- Use calculator for mathematical operations

Format tool calls as: TOOL[tool_name](input)
For example: TOOL[retrieval](machine learning concepts)
"""

        logger.info(f"Initialized RAG Agent with {len(tools)} tools")

    async def plan(self, query: str, context: List[str] = None) -> str:
        """
        Create a plan for answering the query

        Args:
            query: User query
            context: Optional context from previous steps

        Returns:
            Plan as a string
        """
        tools_desc = get_tools_description(self.tools.values())

        planning_prompt = f"""Given the user question and available tools, create a step-by-step plan to answer the question.

{tools_desc}

User Question: {query}

{"Context from previous steps: " + str(context) if context else ""}

Create a numbered plan (2-4 steps) for how to answer this question. If tools are needed, specify which tool to use in each step."""

        response = await self.llm_client.generate_with_system(
            system_prompt="You are a planning assistant. Create clear, actionable plans.",
            user_message=planning_prompt,
            temperature=0.3,
        )

        logger.info(f"Generated plan: {response}")
        return response

    async def execute_tool_call(self, tool_call_text: str) -> str:
        """
        Parse and execute a tool call

        Args:
            tool_call_text: Text containing tool call (e.g., "TOOL[retrieval](query)")

        Returns:
            Tool output
        """
        # Parse tool call
        pattern = r'TOOL\[(\w+)\]\((.+?)\)'
        match = re.search(pattern, tool_call_text)

        if not match:
            return "Invalid tool call format"

        tool_name = match.group(1)
        tool_input = match.group(2)

        if tool_name not in self.tools:
            return f"Unknown tool: {tool_name}"

        # Execute tool
        tool = self.tools[tool_name]
        result = await tool.run(tool_input)

        logger.info(f"Executed {tool_name} with input: {tool_input}")
        return result

    async def reason_and_act(
        self,
        query: str,
        plan: str,
        tools_output: List[str],
    ) -> Dict[str, Any]:
        """
        Reason about the next action based on plan and previous outputs

        Args:
            query: User query
            plan: Current plan
            tools_output: Outputs from previously executed tools

        Returns:
            Dict with 'action' (tool_call or answer) and 'content'
        """
        tools_desc = get_tools_description(self.tools.values())

        context = "\n".join([f"Tool Output {i+1}: {output}" for i, output in enumerate(tools_output)])

        reasoning_prompt = f"""Given the plan and any tool outputs, decide the next action.

Plan:
{plan}

{tools_desc}

User Question: {query}

{"Previous Tool Outputs:\n" + context if context else "No tool outputs yet."}

Decide the next action:
1. If you need to use a tool, respond with: TOOL[tool_name](input)
2. If you have enough information to answer, respond with: ANSWER: [your final answer]

Your response:"""

        response = await self.llm_client.generate_with_system(
            system_prompt=self.system_prompt,
            user_message=reasoning_prompt,
            temperature=0.5,
        )

        # Parse response
        if response.startswith("ANSWER:"):
            return {
                'action': 'answer',
                'content': response.replace("ANSWER:", "").strip()
            }
        elif "TOOL[" in response:
            return {
                'action': 'tool_call',
                'content': response
            }
        else:
            # Default to answering if unclear
            return {
                'action': 'answer',
                'content': response
            }

    async def run(self, query: str) -> Dict[str, Any]:
        """
        Run the agent on a query

        Args:
            query: User query

        Returns:
            Dict with 'answer', 'plan', 'tool_outputs', and 'reasoning_steps'
        """
        logger.info(f"Agent processing query: {query}")

        # Step 1: Plan
        plan = await self.plan(query)

        # Step 2: Execute iteratively
        tools_output = []
        reasoning_steps = []

        for iteration in range(self.max_iterations):
            logger.info(f"Iteration {iteration + 1}/{self.max_iterations}")

            # Reason about next action
            decision = await self.reason_and_act(query, plan, tools_output)
            reasoning_steps.append(decision)

            if decision['action'] == 'answer':
                # Got final answer
                final_answer = decision['content']
                logger.info("Agent reached final answer")
                break
            elif decision['action'] == 'tool_call':
                # Execute tool
                tool_output = await self.execute_tool_call(decision['content'])
                tools_output.append(tool_output)
            else:
                logger.warning(f"Unknown action: {decision['action']}")
                break
        else:
            # Max iterations reached
            final_answer = "I couldn't complete the task within the maximum number of steps. Please try rephrasing your question."

        return {
            'answer': final_answer,
            'plan': plan,
            'tool_outputs': tools_output,
            'reasoning_steps': reasoning_steps,
        }

    async def run_simple(self, query: str) -> str:
        """
        Run the agent and return just the answer

        Args:
            query: User query

        Returns:
            Answer string
        """
        result = await self.run(query)
        return result['answer']
