from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OtherChatParameters(BaseModel):
    stop_sequences: Optional[List[str]]
    temperature: Optional[float] = Field(0.2, ge=0, le=1)
    top_p: Optional[float]
    top_k: Optional[int]
    metadata: Optional[Dict[str, Any]]
    stream: Optional[bool] = Field(True)
