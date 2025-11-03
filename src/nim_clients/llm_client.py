"""
NVIDIA NIM LLM Client for llama-3.1-nemotron-nano-8B-v1
Uses OpenAI-compatible API
"""

from typing import List, Dict, Optional, AsyncIterator
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
import os


class NIMClient:
    """Client for NVIDIA NIM LLM inference"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """
        Initialize NIM client

        Args:
            api_key: NVIDIA API key
            base_url: NIM inference endpoint URL
            model: Model name (default: llama-3.1-nemotron-nano-8b-instruct)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        self.api_key = api_key or os.getenv("NIM_API_KEY")
        self.base_url = base_url or os.getenv("NIM_INFERENCE_URL", "https://integrate.api.nvidia.com/v1")
        self.model = model or os.getenv("NIM_MODEL", "llama-3.1-nemotron-nano-8b-instruct")
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not self.api_key:
            raise ValueError("NIM_API_KEY must be provided or set in environment")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        logger.info(f"Initialized NIM client with model: {self.model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> str:
        """
        Generate completion from messages

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            stream: Whether to stream the response

        Returns:
            Generated text response
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=stream,
            )

            if stream:
                return response

            content = response.choices[0].message.content
            logger.debug(f"Generated response: {content[:100]}...")
            return content

        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """
        Generate streaming completion from messages

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max_tokens

        Yields:
            Chunks of generated text
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Error in streaming completion: {e}")
            raise

    async def generate_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate completion with system and user messages

        Args:
            system_prompt: System prompt
            user_message: User message
            temperature: Override default temperature
            max_tokens: Override default max_tokens

        Returns:
            Generated text response
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return await self.generate(messages, temperature, max_tokens)
