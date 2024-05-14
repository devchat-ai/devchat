from typing import List

from pydantic import BaseModel

__all__ = ["Position", "Range", "Location", "SymbolNode", "LocationWithText"]


class Position(BaseModel):
    line: int  # 0-based
    character: int  # 0-based

    def __repr__(self):
        return f"Ln{self.line}:Col{self.character}"

    def __hash__(self):
        return hash(self.__repr__())


class Range(BaseModel):
    start: Position
    end: Position

    def __repr__(self):
        return f"{self.start} - {self.end}"

    def __hash__(self):
        return hash(self.__repr__())


class Location(BaseModel):
    abspath: str
    range: Range

    def __repr__(self):
        return f"{self.abspath}::{self.range}"

    def __hash__(self):
        return hash(self.__repr__())


class SymbolNode(BaseModel):
    name: str
    kind: str
    range: Range
    children: List["SymbolNode"]


class LocationWithText(BaseModel):
    abspath: str
    range: Range
    text: str

    def __repr__(self):
        return f"{self.abspath}::{self.range}::{self.text}"

    def __hash__(self):
        return hash(self.__repr__())
