from typing import List

from pydantic import BaseModel


class Position(BaseModel):
    line: int  # 0-based
    character: int  # 0-based


class Range(BaseModel):
    start: Position
    end: Position


class Location(BaseModel):
    abspath: str
    range: Range


class SymbolNode(BaseModel):
    name: str
    kind: str
    range: Range
    children: List["SymbolNode"]
