#!/usr/bin/env python
import sys
import os
import warnings

from datetime import datetime

from kids_writing_agent.crew import KidsWritingAgent

os.environ["OTEL_SDK_DISABLED"] = "true"
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

from crewai.flow.flow import Flow, start, listen, router
from kids_writing_agent.state import EssayState
from kids_writing_agent.agents import (profile_manager, conversation_guide,
                    outline_planner, reviewer,
                    improvement_coach, progress_analyst)

class EssayCoachFlow(Flow[EssayState]):

    # STEP 1 – topic & requirements come from UI
    @start()
    def intake(self):
        self.state.topic = input("📝 Topic?  ")
        self.state.requirements = input("📋 Any special requirements?  ")
        return self.state.topic

    # STEP 2 – fetch profile
    @listen(intake)
    def fetch_profile(self, topic):
        # Hard-coded profile for PoC
        self.state.profile = {
            "age": 8, "grade": 3, "skill_level": "beginner",
            "weak_areas": ["organization", "comma splices"],
        }
        return self.state.profile

    # STEP 3 – chat to gather ideas
    @listen(fetch_profile)
    def collect_ideas(self, _profile):
        q1 = f"We're writing about **{self.state.topic}**. What are your main ideas?"
        ideas = conversation_guide.run(q1)
        self.state.ideas = [i.strip("-• ") for i in ideas.split("\n") if i.strip()]
        return self.state.ideas

    # STEP 4 – draft outline
    @listen(collect_ideas)
    def create_outline(self, ideas):
        outline_prompt = (
            "Create a numbered outline with a hint for each paragraph.\n"
            f"Ideas: {ideas}\nStudent profile: {self.state.profile}"
        )
        outline_txt = outline_planner.run(outline_prompt)
        self.state.outline = [l.strip() for l in outline_txt.split("\n") if l.strip()]
        return self.state.outline

    # STEP 5 – deliver outline & collect draft
    @listen(create_outline)
    def collect_draft(self, outline):
        print("\nHere’s your outline:")
        for l in outline: print(l)
        print("Write your essay below. Type END on its own line when done.")
        lines = []
        while True:
            line = input("✏️  ")
            if line.strip().upper() == "END":
                break
            lines.append(line)
        self.state.draft = "\n".join(lines)
        return self.state.draft

    # STEP 6 – review and route
    @router(collect_draft)
    def review(self, draft):
        review_json = reviewer.run(
            f"Requirements: {self.state.requirements}\n\n{draft}"
        )
        self.state.review_json = review_json
        self.state.passes = review_json.get("passed", False)
        return "good" if self.state.passes else "revise"

    # ---- success path
    @listen("good")
    def praise(self):
        msg = progress_analyst.run(
            f"Essay accepted. Compare to history and praise improvement."
        )
        print("\n✅  Essay accepted!\n" + msg)
        return "done"

    # ---- revision path
    @listen("revise")
    def feedback(self):
        issues = self.state.review_json["issues"]
        fb = improvement_coach.run(
            f"These issues were found: {issues}. Give improvement advice."
        )
        print("\n🔍 Feedback:\n" + fb)
        # student revises
        print("Rewrite and type END when finished.")
        lines = []
        while True:
            line = input("✏️  ")
            if line.strip().upper() == "END":
                break
            lines.append(line)
        self.state.draft = "\n".join(lines)
        return self.state.draft   # feeds back into router

flow = EssayCoachFlow() 

def run():                       
    """
    Kick off the writing-coach Flow.
    Called automatically by `crewai run`.
    """
    flow.kickoff()

if __name__ == "__main__":
    EssayCoachFlow().kickoff()
