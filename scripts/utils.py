from dataclasses import dataclass
from datetime import datetime


@dataclass
class News:
    data: datetime
    fonte: str
    materia: str
    link: str


@dataclass
class Article:
    title: str
    url: str
