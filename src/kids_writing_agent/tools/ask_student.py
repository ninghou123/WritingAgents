# tools/ask_student.py
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

class AskArgs(BaseModel):
    question: str = Field(..., description="Prompt to show the student")

class AskStudentTool(BaseTool):
    name: str  = "ask_student"
    description: str  = "Ask the student a question and return the exact answer."
    args_schema: Type[BaseModel] = AskArgs

    def _run(self, question: str) -> str:           # noqa: D401
        return input(f"\n👩‍🏫 {question}\n🧑‍🎓 > ")
