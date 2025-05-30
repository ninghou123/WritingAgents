"""
essay_coach_poc.py  –  end-to-end K-12 writing-coach demo
--------------------------------------------------------
Works with crewai >= 0.46.  Requires an OPENAI_API_KEY.
"""

from __future__ import annotations
import json, re, textwrap
from typing import Dict, List, Any

from crewai.agent import Agent
from crewai.flow.flow import Flow, start, listen, router
from crewai.tools import BaseTool

# ------------------------------------------------------------------
# 0-bis.  Grade-to-writing expectations (tweak as needed)
# ------------------------------------------------------------------
GRADE_GUIDE = {
    1: {"paras": 2, "min_words": 40,  "max_words": 700},
    2: {"paras": 3, "min_words": 60,  "max_words": 1000},
    3: {"paras": 3, "min_words": 80,  "max_words": 1500},   # Reading Rockets, Reddit teacher
    4: {"paras": 4, "min_words": 120, "max_words": 2000},
    5: {"paras": 4, "min_words": 150, "max_words": 3000},
    6: {"paras": 5, "min_words": 200, "max_words": 4000},
}

# ──────────────────────────────────────────────────────
# 1.  Custom tool that actually talks to the child
# ──────────────────────────────────────────────────────
class AskStudentTool(BaseTool):
    name: str = "ask_student"
    description: str = "Prompt the student and capture the reply"

    def _run(self, question: str) -> str:
        return input(f"\n👩‍🏫 {question}\n🧑‍🎓 > ").strip()

    # quality-of-life wrapper so we can call tool.run()
    def run(self, *, question: str) -> str:
        return self._run(question)

# ──────────────────────────────────────────────────────
# 2.  All agents from your YAML (prompts kept verbatim)
# ──────────────────────────────────────────────────────
profile_manager = Agent(
    role="Profile Manager",
    goal='Provide user profile data for downstream tasks. When the user asks for AGE and GRADE, reply with exact JSON: {"age":<int>,"grade":<int>} and nothing else.',
    backstory=textwrap.dedent("""
        User profile data for user "demo_user":
        {
          "age": 8, "grade": 3, "skill_level": "beginner",
          "weak_areas": ["organization","comma splices"],
          "history":[
            {"date":"2023-09-01","topic":"My Favorite Animal","score":85,
             "comments":"Good effort, but needs better structure."},
            {"date":"2023-09-15","topic":"A Day at the Zoo","score":90,
             "comments":"Great use of descriptive language!"}
          ]
        }
    """).strip(),
    verbose=True,
)


conversation_guide = Agent(
    role="Conversation Guide",
    goal="Help the student craft an essay by guiding the conversation and gathering information",
    backstory="""
        You are a friendly, encouraging K-12 writing coach.
        You use light, friendly Socratic questions to study the topic
        and keep the learner engaged.
        You always ask one clear question at a time.""",
    tools=[AskStudentTool()],
    verbose=True,
)

outline_planner = Agent(
    role="Outline Planner",
    goal="Turn early ideas into a usable outline + hints",
    backstory="Veteran writing tutor who organises information clearly.",
    verbose=True,
)

reviewer = Agent(
    role="Writing Reviewer",
    goal="Score the draft for grammar, structure, and requirement fulfilment",
    backstory="Exacting English teacher with a fair but firm rubric.",
    verbose=True,
)

improvement_coach = Agent(
    role="Improvement Coach",
    goal="Give actionable, motivating feedback when the draft misses the mark",
    backstory="Encouraging but precise.",
    verbose=True,
)

progress_analyst = Agent(
    role="Progress Analyst",
    goal="Spot and celebrate concrete improvements over time",
    backstory="Compares current work to the student's history to show growth.",
    verbose=True,
)

# ──────────────────────────────────────────────────────
# 3.  Flow implementation  (dict state keeps it simple)
# ──────────────────────────────────────────────────────
class EssayCoachFlow(Flow[dict]):

    # ---------- phase 1 : get topic & profile ----------
    @start()
    def intake(self) -> dict:
        topic = input("📝 Topic?  ").strip()
        req   = input("📋 Special requirements? (press Enter for none)  ").strip()

        # --- ask ONLY for age & grade ---
        age_grade_output = profile_manager.kickoff(
            'Give only the age and grade for "demo_user" '
            'in JSON: {"age":<int>,"grade":<int>}'
        )
        age_grade = json.loads(age_grade_output.raw.strip())
        print(f"\n👤 Profile: {age_grade}")
        grade = int(age_grade["grade"])
        guide = GRADE_GUIDE.get(grade, GRADE_GUIDE[3])

        # --- if you still want the full profile, do it AFTER you know grade ---
        full_profile_output = profile_manager.kickoff(
            'Return the COMPLETE JSON profile for "demo_user". '
            'No markdown, no commentary.'
        )
        full_profile = json.loads(full_profile_output.raw.strip())

        return {
            "topic": topic,
            "req": req,
            "profile": full_profile,
            "grade": grade,
            "age": int(age_grade["age"]),
            "guide": guide,
        }

    # ---------- phase 2 : collect ideas with Socratic chat ----------
    @listen(intake)
    def brainstorm(self, data):
        """
        • Uses conversation_guide (LLM) to craft ONE next question at a time.
        • Presents that question to the student via AskStudentTool.
        • Stores each Q-A pair.
        • The loop stops when the agent signals [DONE] and returns a tidy
        bullet list of ideas in data["ideas"].
        """
        qa_history: list[dict[str, str]] = []
        ask_tool = AskStudentTool()

        while True:
            # Build a prompt for the guide agent that includes context so far.
            guide_prompt = (
                f"You are helping the student (grade {data['grade']}, age {data['age']}) "
                f"prepare an essay on **{data['topic']}**.\n"
                "Strict rule: Ask about ONLY what the student has already said or what "
                "is common knowledge about the topic. If you suggest a new angle, make "
                "it explicit with: 'Some people also ____. Do you think so?' "
                "Never claim the student 'mentioned' something unless the exact words "
                "appear in the transcript you see."
                f"Student profile:\n{json.dumps(data['profile'])}\n\n"
                "Conversation so far:\n" +
                "\n".join(f"Q: {p['q']}\nA: {p['a']}" for p in qa_history) +
                "\n\nAsk ONE open question that will elicit details, feelings, "
                "examples, or reasons.\n"
                f"When you believe you have at least {data['guide']['paras']} rich ideas "
                "for the body paragraphs, answer EXACTLY in this format:\n"
                "[DONE]\n• idea 1\n• idea 2\n• idea 3 ..."
                "Make sure the ideas loyally reflect the student's input.\n"
            )

            agent_reply = conversation_guide.kickoff(guide_prompt).raw.strip()

            # If the agent says it's done, parse bullet list and break.
            if agent_reply.startswith("[DONE]"):
                bullets = [
                    line.lstrip("•").strip()
                    for line in agent_reply.splitlines()[1:]
                    if line.strip()
                ]
                data["ideas"] = bullets
                return data

            # Otherwise ask the student and store the answer.
            # Quick sanity check for false attributions:
            if ("you mentioned" in agent_reply.lower()
                and not any("you mentioned" in qa["q"].lower() for qa in qa_history)
                and agent_reply.lower().split("you mentioned")[1].strip().split()[0]   # first word after phrase
                    not in qa_history[-1]["a"].lower()):
                agent_reply = ("I might be mistaken, but " + agent_reply)

            # Otherwise ask the student and store the answer.
            student_answer = ask_tool.run(question=agent_reply)
            qa_history.append({"q": agent_reply, "a": student_answer})

    # ---------- phase 3 : draft outline ----------
    @listen(brainstorm)
    def outline(self, data):
        numbered = "\n".join(f"{i+1}. {idea}" for i, idea in enumerate(data["ideas"]))
        outline_prompt = (
            f"Create a numbered outline for a grade-{data['grade']} student. "
            f"Limit the whole essay to about {data['guide']['max_words']} words. "
            "Use an intro, one body paragraph per idea, and a conclusion. "
            "Give each paragraph a kid-friendly hint (≤15 words).\n\n"
            f"Ideas:\n{numbered}"
        )
        outline_text = outline_planner.kickoff(outline_prompt).raw
        print("\n📑 Outline\n" + outline_text)
        data["outline"] = outline_text
        return data

    # ---------- phase 4 : student writes ----------
    @listen(outline)
    def collect_draft(self, data):
        print("\nPlease write your essay now. Finish with a blank line.")
        lines: List[str] = []
        while True:
            line = input()
            if not line.strip(): break
            lines.append(line)
        data["draft"] = "\n".join(lines)
        return data

    # ---------- phase 5 : review ----------
    @listen(collect_draft)
    def review(self, data):
        topic = data["topic"]
        min_words  = data["guide"]["min_words"]
        max_words  = data["guide"]["max_words"]
        review_prompt = (
            f"Evaluate the draft for a grade-{data['grade']} writer "
            f"Topic: {topic}\n"
            f"Expected length: {min_words}-{max_words} words.\n"
            f"Score for grammar, clarity, structure, and topic compliance."
            "Score 0-100 and return JSON {{'score':int,'passed':bool,'issues':[]}}.\n\n"
            + data["draft"]
        )
        review_json = reviewer.kickoff(review_prompt).raw
        data["assessment"] = json.loads(re.search(r"\{.*\}", review_json, re.S).group())
        return data

    # ---------- router ----------
    @router(review)
    def branch(self, data):
        return "good" if data["assessment"]["passed"] else "revise"

    # ---------- phase 6 : improvements loop ----------
    @listen("revise")
    def coach(self, data):
        issues = "\n".join(f"• {iss}" for iss in data["assessment"]["issues"])
        feedback = improvement_coach.kickoff(
            f"The draft has these issues:\n{issues}\nGive encouraging, concrete advice."
        ).raw
        print("\n🔍 Feedback\n" + feedback)
        print("\nPlease revise your essay (blank line to finish).")
        new_lines: List[str] = []
        while True:
            ln = input()
            if not ln.strip(): break
            new_lines.append(ln)
        data["draft"] = "\n".join(new_lines)
        return data  # cycles back to review step

    # ---------- phase 7 : celebrate ----------
    @listen("good")
    def praise(self, data):
        last_score = data["profile"]["history"][-1]["score"]
        new_score  = data["assessment"]["score"]
        delta      = new_score - last_score
        praise = progress_analyst.kickoff(
            f"Old best: {last_score}, new score: {new_score}. "
            f"Congratulate and highlight the +{delta} improvement."
        ).raw
        print("\n🎉 " + praise)
        return "done"

# ──────────────────────────────────────────────────────
if __name__ == "__main__":
    flow = EssayCoachFlow()
    flow.plot("essay_flow")   # generates essay_flow.html without warnings
    flow.kickoff()
