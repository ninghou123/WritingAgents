# src/latest_ai_development/crew.py
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from crewai_tools import SerperDevTool
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from src.kids_writing_agent.tools.profile_loader import ProfileLoader
from crewai_tools import FileReadTool


@CrewBase
class KidsWritingAgent():
  """LatestAiDevelopment crew"""

  agents: List[BaseAgent]
  tasks: List[Task]


  @before_kickoff
  def before_kickoff_function(self, inputs):
    print(f"Before kickoff function with inputs: {inputs}")
    return inputs # You can return the inputs or modify them as needed

  @after_kickoff
  def after_kickoff_function(self, result):
    print(f"After kickoff function with result: {result}")
    return result # You can return the result or modify it as needed
  
  ##################
  # Agents
  ##################
  @agent
  def profile_manager(self) -> Agent:
    return Agent(
      config=self.agents_config['profile_manager'], # type: ignore[index]
      verbose=True,
      tools=[FileReadTool(file_path='../../data/profiles.json')]
    )
  
  @agent
  def conversation_guide(self) -> Agent:
    return Agent(
      config=self.agents_config['conversation_guide'], # type: ignore[index]
      verbose=True
    )
  
  @agent
  def outline_planner(self) -> Agent:
    return Agent(
      config=self.agents_config['outline_planner'], # type: ignore[index]
      verbose=True
    )
  
  @agent
  def reviewer(self) -> Agent:
    return Agent(
      config=self.agents_config['reviewer'], # type: ignore[index]
      verbose=True
    )
  
  @agent
  def manager(self) -> Agent:
    return Agent(
      config=self.agents_config['manager'], # type: ignore[index]
      verbose=True
    )
  
  @agent
  def improvement_coach(self) -> Agent:
    return Agent(
      config=self.agents_config['improvement_coach'], # type: ignore[index]
      verbose=True
    )
  
  @agent
  def progress_analyst(self) -> Agent:
    return Agent(
      config=self.agents_config['progress_analyst'], # type: ignore[index]
      verbose=True
    )
  
  ##################
  # Tasks
  ##################
  @task
  def fetch_profile(self) -> Task:
    return Task(
      config=self.tasks_config['fetch_profile'], # type: ignore[index]
      tools=[FileReadTool(file_path='../../data/profiles.json')]
    )
  
  @task
  def collect_writing_specs(self) -> Task:
    return Task(
      config=self.tasks_config['collect_writing_specs'], # type: ignore[index]
    )
  
  @task
  def draft_outline(self) -> Task:
    return Task(
      config=self.tasks_config['draft_outline'], # type: ignore[index]
    )
  
  @task
  def deliver_outline(self) -> Task:
    return Task(
      config=self.tasks_config['deliver_outline'], # type: ignore[index]
    )
  
  @task
  def evaluate_draft(self) -> Task:
    return Task(
      config=self.tasks_config['evaluate_draft'], # type: ignore[index]
    )
  
  @task
  def coach_improvements(self) -> Task:
    return Task(
      config=self.tasks_config['coach_improvements'], # type: ignore[index]
    )
  
  @task
  def appraise_progress(self) -> Task:
    return Task(
      config=self.tasks_config['appraise_progress'], # type: ignore[index]
    )

  @crew
  def crew(self) -> Crew:
    """Creates the LatestAiDevelopment crew"""
    return Crew(
      agents=[self.profile_manager(), 
              self.conversation_guide(),
              self.outline_planner(),
              self.reviewer(),
              self.improvement_coach(),
              self.progress_analyst()], # Automatically created by the @agent decorator
      tasks=self.tasks, # Automatically created by the @task decorator
      manager_agent=self.manager(),
      process=Process.hierarchical,
      # process=Process.sequential,
      verbose=True,
    )