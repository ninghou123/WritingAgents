from crewai import Agent
from kids_writing_agent.tools.ask_student import AskStudentTool

profile_manager = Agent(
    role="Profile Manager",
    goal="Provide user profile data for downstream tasks",
    backstory="Pre-loads demo_user profile from DB",
    verbose=True, allow_delegation=False,
)

conversation_guide = Agent(
    role="Conversation Guide",
    goal="Ask Socratic questions to gather essay specs",
    backstory="Friendly K-12 coach", verbose=True,
    tools=[AskStudentTool()], allow_delegation=False,
)

outline_planner = Agent(
    role="Outline Planner",
    goal="Turn ideas into a crystal-clear outline",
    backstory="Veteran tutor", verbose=True,
)

reviewer = Agent(
    role="Writing Reviewer",
    goal="Score the draft with a strict rubric",
    backstory="Exacting English teacher", verbose=True,
)

improvement_coach = Agent(
    role="Improvement Coach",
    goal="Give targeted feedback to reach 80+ score",
    backstory="Encouraging mentor", verbose=True,
    tools=[AskStudentTool()],
)

progress_analyst = Agent(
    role="Progress Analyst",
    goal="Spot and celebrate concrete improvements",
    backstory="Tracks growth across submissions",
    verbose=True,
)
