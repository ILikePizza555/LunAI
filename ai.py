from enum import Enum
from collections import deque
from dataclasses import dataclass, field
from functools import lru_cache
from tiktoken import get_encoding, Encoding
from typing import Union

class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

# dataclass will only generate hash if both eq and frozen are true
# Message is "logically" frozen. So we set unsafe_hash here to force the generation of __hash__()
@dataclass(order=True, unsafe_hash=True)
class Message:
    """Dataclass to store metadata and content for messages between us and the chat completion model"""
    # The priority of the message
    priority: int
    # The "index" of the message. Newer messages have higher numbers. Should be an incrementing integer.
    index: int
    # The role of the message. Gets sent to the API
    role: MessageRole = field(compare=False)
    # The message itself. Gets sent to the API
    content: str = field(compare=False)

    def api_serialize(self):
        """Converts this object into a dict that can be passed to the OpenAI API."""
        return {
            "role": self.role.value,
            "content": self.content
        }
    
@lru_cache
def calculate_message_tokens(message: Message, encoding: Union[str, Encoding] = "cl100k_base") -> int:
    if type(encoding) is str:
        encoding = get_encoding(encoding)
    
    return len(encoding.encode(message.content))


class ModelContextWindow:
    """Manages messages to form a context window that can be passed to the model."""

    def __init__(self, max_tokens: int, encoding: Union[str, Encoding] = "cl100k_base"):
        self._queue = deque()
        self._token_count = 0
        self.encoding = encoding
        self.max_tokens = max_tokens

    @property
    def message_iterator(self):
        """Returns an iterator of messages in order."""
        return iter(self._queue)
    
    @property
    def token_count(self) -> int:
        return self._token_count
    
    def drain_tokens(self):
        """Pops items from the window until the token count is under max_tokens"""
        rv = []

        while self._token_count > self.max_tokens:
            m = self._queue.popleft()
            m_tokens = calculate_message_tokens(m, self.encoding)
            
            self._token_count -= m_tokens
            rv.append(m_tokens)
        
        return rv
    
    def insert_message(self, message: Message) -> list[Message]:
        """Inserts a message into the window. Automatically calls drain_tokens"""
        token_count = calculate_message_tokens(message, self.encoding)
        self._token_count += token_count

        self._queue.append(message)
        return self.drain_tokens()
    
    def insert_new_message(self, role: MessageRole, content: str, priority = 0, index = None) -> list[Message]:
        """Creates a new `Message` and inserts it into the window."""
        return self.insert_message(Message(
            priority,
            len(self._queue) if index is not None else index,
            role,
            content
        ))
    
    def clear(self):
        self._queue.clear()