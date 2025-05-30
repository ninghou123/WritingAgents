from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
import litellm

# litellm._turn_on_debug()

class AskStudentTool(BaseTool):
    name: str = "ask_student"
    description: str = "Prompt the student and capture the answer."
    def _run(self, question: str):
        return input(f"\n👩‍🏫 {question}\n🧑‍🎓 > ")

teacher = Agent(
    role="Writing teacher",
    goal="Help the student craft a essay",
    backstory=(
        "You are a friendly, encouraging K-12 writing coach. "
        "You always ask one clear question at a time."
    ),
    tools=[AskStudentTool()],
    max_rpm=60, 
    verbose=False,
)

t1 = Task(
    agent=teacher,
    description=(
        "Ask the student what their favourite sport is and *why* they like it. "
        "Store the response as `animal_reason`."
    ),
    expected_output="{animal_reason}"
)

t2 = Task(
    agent=teacher,
    context=[t1],
    description=(
        "From the student's reason, extract **three distinct points** "
        "and propose an essay outline: intro, one paragraph per point, conclusion."
    ),
    expected_output="A markdown outline with four sections."
)

crew = Crew(
    agents=[teacher],
    tasks=[t1, t2],
    process=Process.sequential
)
result = crew.kickoff()
print(result)
