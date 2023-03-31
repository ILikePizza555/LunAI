import heapq
from collections import defaultdict
from dataclasses import dataclass, field
from discord import TextChannel
from enum import Enum
from functools import lru_cache
from openai import ChatCompletion
from tiktoken import get_encoding, Encoding
from typing import NamedTuple, Iterable

class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

@dataclass(order=True, frozen=True)
class Message:
    """Dataclass to store metadata and content for messages between us and the chat completion model"""
    # The priority of the message
    priority: int
    # The "index" of the message. Newer messages have higher numbers. Should be an incrementing integer.
    index: int
    # The role of the message. Gets sent to the API
    role: MessageRole = field(compare=False, hash=True)
    # The message itself. Gets sent to the API
    content: str = field(compare=False, hash=True)

    def api_serialize(self):
        """Converts this object into a dict that can be passed to the OpenAI API."""
        return {
            "role": self.role.value,
            "content": self.content
        }
    
    @staticmethod
    @lru_cache
    def calculate_tokens(message, encoding: str | Encoding = "cl100k_base") -> int:
        if type(encoding) is str:
            encoding = get_encoding(encoding)
        
        return len(encoding.encode(message.content))


class ContextWindow:
    """Manages messages to form a context window that can be passed to the model."""

    def __init__(self, max_tokens: int, encoding: str | Encoding = "cl100k_base"):
        self._queue: list[Message] = []
        self._token_count = 0
        self._incrementor = 0
        self.encoding = encoding
        self.max_tokens = max_tokens

    @property
    def empty(self) -> bool:
        return len(self._queue) == 0

    @property
    def messages(self):
        """Returns an iterator of messages in lowest priority, lowest index order."""
        return iter(self._queue)
    
    @property
    def chat_order(self):
        """Returns messages in highest priority, lowest index order."""
        return sorted(self._queue, key=lambda a: (a.priority * -1, a.index))
    
    @property
    def token_count(self) -> int:
        return self._token_count
    
    @property
    def incrementor(self) -> int:
        """Get the value of incrementor, then increase it by 1."""
        rv = self._incrementor
        self._incrementor += 1
        return rv
    
    def drain_tokens(self):
        """Pops items from the window until the token count is under max_tokens"""
        rv = []

        while self._token_count > self.max_tokens:
            m = heapq.heappop(self._queue)
            m_tokens = Message.calculate_tokens(m, self.encoding)
            
            self._token_count -= m_tokens
            rv.append(m_tokens)
        
        return rv
    
    def insert_message(self, message: Message) -> list[Message]:
        """
        Inserts a message into the window. Automatically calls drain_tokens.
        Note that **lower** `priority` and `index` values are **higher** priority. 
        """
        token_count = Message.calculate_tokens(message, self.encoding)
        self._token_count += token_count
        
        heapq.heappush(self._queue, message)
        return self.drain_tokens()
    
    def insert_new_message(self, role: MessageRole, content: str, priority = 0, index = None) -> list[Message]:
        """
        Creates a new `Message` and inserts it into the window.
        Note that **lower** `priority` and `index` values are **higher** priority.
        """
        return self.insert_message(Message(
            priority,
            self.incrementor if index is None else index,
            role,
            content
        ))
    
    def clear(self):
        self._queue.clear()


class CompletionRespose(NamedTuple):
    """A standard type for responses from models"""
    content: str
    statistics: dict[str, int]


class ChatCompletionAPI:
    """Defines a standard interface for the OpenAI ChatCompletion API"""

    def __init__(self, **kwargs) -> None:
        self.api_args = kwargs
    
    async def get_completion(self, messages: Iterable[Message]) -> CompletionRespose:
        response = await ChatCompletion.acreate(
            **self.api_args,
            messages = [m.api_serialize() for m in messages]
        )

        return CompletionRespose(
            response["choices"][0]["message"]["content"],
            response["usage"]
        )


class Foxtail:
    """
    An instance of the abstract idea of an "intelligence" or connection to a model.

    In practice this class just holds the prompt and context windows for a model, and defines
    and API to simplify communicating across the API. Of course, there being an API in the first
    places is merely an implementation detail.

    I chose the name Foxtail because I spent like an hour trying to come up with a name and
    I just settled for the first thing I saw which was a scarf with a fox on it.
    """
    PROMPT_PRIORITY = 100

    def __init__(self, prompt: str, api, context_window_size = 2900) -> None:
        self._api = api

        def context_window_factory():
            rv = ContextWindow(context_window_size)
            rv.insert_new_message(MessageRole.SYSTEM, prompt, Foxtail.PROMPT_PRIORITY)
            return rv
        self._channel_context_windows = defaultdict(context_window_factory)
    
    @property
    def context_windows(self) -> defaultdict[TextChannel, ContextWindow]:
        return self._channel_context_windows

    def clear_channel_context(self, channel: TextChannel):
        self._channel_context_windows[channel].clear()

    async def send_window(self, channel: TextChannel, add_response = True) -> CompletionRespose:
        """
        Sends the window to the api for a resonse and returns it.
        If `add_response` is True (default) then the response is added to the context window.
        If the window is empty or does not exist then an error is raised.
        """
        if channel not in self._channel_context_windows:
            raise LookupError(f"No context window for channel {channel.id} exists.")

        context_window = self._channel_context_windows[channel]
        if context_window.empty:
            raise ValueError(f"Channel {channel.id}'s context window is empty.")
        response: CompletionRespose = await self._api.get_completion(context_window.chat_order)

        if add_response:
            context_window.insert_new_message(MessageRole.ASSISTANT, response.content)
        
        return response
    
    async def add_and_send_new_message(self, 
                                 channel: TextChannel,
                                 role: MessageRole, 
                                 content: str,
                                 priority = 0,
                                 index = None,
                                 add_response = True) -> CompletionRespose:
        """
        Creates a new user message and adds it to the context window. 
        Then, sends that context window to the api and returns the response.
        """
        context_window = self._channel_context_windows[channel]
        context_window.insert_new_message(role, content, priority, index)
        return await self.send_window(channel, add_response)