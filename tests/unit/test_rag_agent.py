"""
Unit tests for RAG Agent
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agent.rag_agent import RAGAgent


@pytest.fixture
def mock_llm_client():
    """Mock LLM client"""
    client = AsyncMock()
    client.generate = AsyncMock(return_value="Test response")
    client.generate_with_system = AsyncMock(return_value="Test plan")
    return client


@pytest.fixture
def mock_tools():
    """Mock tools"""
    tool1 = Mock()
    tool1.name = "retrieval"
    tool1.description = "Search the knowledge base"
    tool1.run = AsyncMock(return_value="Retrieved: test data")

    tool2 = Mock()
    tool2.name = "calculator"
    tool2.description = "Calculate expressions"
    tool2.run = AsyncMock(return_value="Result: 42")

    return [tool1, tool2]


class TestRAGAgent:
    """Tests for RAG Agent"""

    def test_init(self, mock_llm_client, mock_tools):
        """Test agent initialization"""
        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools,
            max_iterations=5
        )

        assert agent.llm_client == mock_llm_client
        assert len(agent.tools) == 2
        assert "retrieval" in agent.tools
        assert "calculator" in agent.tools
        assert agent.max_iterations == 5

    @pytest.mark.asyncio
    async def test_plan(self, mock_llm_client, mock_tools):
        """Test planning functionality"""
        mock_llm_client.generate_with_system = AsyncMock(
            return_value="1. Search knowledge base\n2. Analyze results\n3. Formulate answer"
        )

        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools
        )

        plan = await agent.plan("What is machine learning?")

        assert "Search knowledge base" in plan
        mock_llm_client.generate_with_system.assert_called_once()
        call_args = mock_llm_client.generate_with_system.call_args
        assert "planning" in call_args.kwargs['system_prompt'].lower()

    @pytest.mark.asyncio
    async def test_plan_with_context(self, mock_llm_client, mock_tools):
        """Test planning with context"""
        mock_llm_client.generate_with_system = AsyncMock(return_value="Updated plan")

        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools
        )

        context = ["Previous result 1", "Previous result 2"]
        plan = await agent.plan("Follow-up question", context)

        assert plan == "Updated plan"
        call_args = mock_llm_client.generate_with_system.call_args
        assert "Previous result 1" in call_args.kwargs['user_message']

    @pytest.mark.asyncio
    async def test_execute_tool_call_valid(self, mock_llm_client, mock_tools):
        """Test executing a valid tool call"""
        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools
        )

        result = await agent.execute_tool_call("TOOL[retrieval](machine learning)")

        assert result == "Retrieved: test data"
        mock_tools[0].run.assert_called_once_with("machine learning")

    @pytest.mark.asyncio
    async def test_execute_tool_call_invalid_format(self, mock_llm_client, mock_tools):
        """Test executing tool call with invalid format"""
        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools
        )

        result = await agent.execute_tool_call("Invalid format")

        assert "Invalid tool call format" in result

    @pytest.mark.asyncio
    async def test_execute_tool_call_unknown_tool(self, mock_llm_client, mock_tools):
        """Test executing tool call with unknown tool"""
        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools
        )

        result = await agent.execute_tool_call("TOOL[unknown_tool](input)")

        assert "Unknown tool" in result

    @pytest.mark.asyncio
    async def test_reason_and_act_answer(self, mock_llm_client, mock_tools):
        """Test reasoning that leads to answer"""
        mock_llm_client.generate_with_system = AsyncMock(
            return_value="ANSWER: Machine learning is a subset of AI"
        )

        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools
        )

        decision = await agent.reason_and_act(
            query="What is ML?",
            plan="Check knowledge base",
            tools_output=["ML is AI subset"]
        )

        assert decision['action'] == 'answer'
        assert "Machine learning is a subset of AI" in decision['content']

    @pytest.mark.asyncio
    async def test_reason_and_act_tool_call(self, mock_llm_client, mock_tools):
        """Test reasoning that leads to tool call"""
        mock_llm_client.generate_with_system = AsyncMock(
            return_value="TOOL[retrieval](neural networks)"
        )

        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools
        )

        decision = await agent.reason_and_act(
            query="What are neural networks?",
            plan="Search for info",
            tools_output=[]
        )

        assert decision['action'] == 'tool_call'
        assert "TOOL[retrieval]" in decision['content']

    @pytest.mark.asyncio
    async def test_reason_and_act_unclear_response(self, mock_llm_client, mock_tools):
        """Test reasoning with unclear response defaults to answer"""
        mock_llm_client.generate_with_system = AsyncMock(
            return_value="Some unclear response"
        )

        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools
        )

        decision = await agent.reason_and_act(
            query="Test query",
            plan="Test plan",
            tools_output=[]
        )

        assert decision['action'] == 'answer'
        assert decision['content'] == "Some unclear response"

    @pytest.mark.asyncio
    async def test_run_with_immediate_answer(self, mock_llm_client, mock_tools):
        """Test agent run that immediately produces answer"""
        mock_llm_client.generate_with_system = AsyncMock(
            side_effect=[
                "1. Answer directly",  # Plan
                "ANSWER: The answer is 42"  # Reasoning
            ]
        )

        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools,
            max_iterations=10
        )

        result = await agent.run("What is the answer?")

        assert result['answer'] == "The answer is 42"
        assert result['plan'] == "1. Answer directly"
        assert len(result['tool_outputs']) == 0
        assert len(result['reasoning_steps']) == 1

    @pytest.mark.asyncio
    async def test_run_with_tool_execution(self, mock_llm_client, mock_tools):
        """Test agent run that uses tools"""
        mock_llm_client.generate_with_system = AsyncMock(
            side_effect=[
                "1. Search knowledge base\n2. Answer question",  # Plan
                "TOOL[retrieval](test query)",  # First reasoning
                "ANSWER: Based on retrieved data, the answer is X"  # Second reasoning
            ]
        )

        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools,
            max_iterations=10
        )

        result = await agent.run("Test question")

        assert "Based on retrieved data" in result['answer']
        assert len(result['tool_outputs']) == 1
        assert result['tool_outputs'][0] == "Retrieved: test data"
        assert len(result['reasoning_steps']) == 2

    @pytest.mark.asyncio
    async def test_run_max_iterations_reached(self, mock_llm_client, mock_tools):
        """Test agent hitting max iterations"""
        # Always request tool calls, never answer
        mock_llm_client.generate_with_system = AsyncMock(
            side_effect=[
                "Keep searching",  # Plan
                "TOOL[retrieval](query1)",
                "TOOL[retrieval](query2)",
                "TOOL[retrieval](query3)",
            ]
        )

        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools,
            max_iterations=3
        )

        result = await agent.run("Test question")

        assert "couldn't complete the task" in result['answer']
        assert len(result['tool_outputs']) == 3
        assert len(result['reasoning_steps']) == 3

    @pytest.mark.asyncio
    async def test_run_simple(self, mock_llm_client, mock_tools):
        """Test run_simple method"""
        mock_llm_client.generate_with_system = AsyncMock(
            side_effect=[
                "Plan",
                "ANSWER: Simple answer"
            ]
        )

        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools
        )

        answer = await agent.run_simple("Test query")

        assert answer == "Simple answer"

    @pytest.mark.asyncio
    async def test_run_multiple_tool_calls(self, mock_llm_client, mock_tools):
        """Test agent making multiple tool calls"""
        mock_llm_client.generate_with_system = AsyncMock(
            side_effect=[
                "1. Retrieve data\n2. Calculate\n3. Answer",  # Plan
                "TOOL[retrieval](data)",  # First tool
                "TOOL[calculator](2 + 2)",  # Second tool
                "ANSWER: Combined result"  # Final answer
            ]
        )

        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools
        )

        result = await agent.run("Complex question")

        assert len(result['tool_outputs']) == 2
        assert result['tool_outputs'][0] == "Retrieved: test data"
        assert result['tool_outputs'][1] == "Result: 42"
        assert result['answer'] == "Combined result"

    @pytest.mark.asyncio
    async def test_run_with_unknown_action(self, mock_llm_client, mock_tools):
        """Test agent handling unknown action"""
        mock_llm_client.generate_with_system = AsyncMock(
            side_effect=[
                "Plan",
                "UNKNOWN_ACTION: something"  # This will be treated as answer
            ]
        )

        agent = RAGAgent(
            llm_client=mock_llm_client,
            tools=mock_tools
        )

        result = await agent.run("Test")

        # Should treat unknown format as answer
        assert "something" in result['answer']
