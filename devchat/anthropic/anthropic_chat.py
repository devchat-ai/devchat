from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnthropicChatParameters(BaseModel, extra="ignore"):
    max_tokens_to_sample: int = Field(1024, ge=1)
    stop_sequences: Optional[List[str]]
    temperature: Optional[float] = Field(0.2, ge=0, le=1)
    top_p: Optional[float]
    top_k: Optional[int]
    metadata: Optional[Dict[str, Any]]
    stream: Optional[bool] = Field(True)
