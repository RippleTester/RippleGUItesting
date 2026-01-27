import json

from src.pipelines.generation_tool import Step
from src.pipelines.placeholder import Placeholder
from src.types.bug import Bug
from src.utils.gpt_util import GPTUtil
from src.utils.llm_util import LLMUtil
from pydantic import BaseModel


class Scenario(BaseModel):
    summary: str
    steps: list[Step]


class Scenarios(BaseModel):
    scenarios: list[Scenario]

class ClassifyOutcome(BaseModel):
    include_scenario: bool


class ScenarioExtractor:
    def __init__(self):
        pass

    @staticmethod
    def get_input_from_bug_dict(bug):
        if isinstance(bug, Bug):
            # summary = bug.summary
            description = bug.description.text
        else:
            # summary = bug["summary"]
            description = bug["description"]
        # input_content = {
        #     # "summary": summary,
        #     "description": description,
        # }
        # return str(input_content)
        return description

    @staticmethod
    def extract_scenarios(bug,
                          # output_format=Scenarios,
                          output_format=ClassifyOutcome,
                          prompt_folder=Placeholder.CONSTRUCTOR, system_prompt=Placeholder.SYSTEM,
                          model=GPTUtil.GPT5_NANO, reasoning='low'):
        if isinstance(bug, Bug):
            bug_id = bug.id
            summary = bug.summary
        else:
            bug_id = bug["id"]
            summary = bug["summary"]
        system_instructions = LLMUtil.get_instructions(prompt_folder, system_prompt)
        input_content = ScenarioExtractor.get_input_from_bug_dict(bug)
        # print(json.dumps(input_content, indent=2))
        if input_content.strip():
            (response, cost), duration_mins = GPTUtil.parse_response(input_content, output_format=output_format, system_instructions=system_instructions,
                                    model=model, reasoning=reasoning)
        else:
            response, cost = None, None
        output = {
            Placeholder.BUG_ID: bug_id,
            Placeholder.SUMMARY: summary,
            Placeholder.COST: cost,
            Placeholder.DURATION_MINS: duration_mins,
        }
        if response:
            response_output = json.loads(response.output_text)
            output = output | response_output
        return output

    @staticmethod
    def extract_scenarios_by_gpt_oss_20b(bug,
                          # output_format=Scenarios,
                          output_format=ClassifyOutcome,
                          prompt_folder=Placeholder.CONSTRUCTOR, system_prompt=Placeholder.SYSTEM,
                          model=GPTUtil.GPT5_NANO, reasoning='low'):
        if isinstance(bug, Bug):
            bug_id = bug.id
            summary = bug.summary
        else:
            bug_id = bug["id"]
            summary = bug["summary"]
        system_instructions = LLMUtil.get_instructions(prompt_folder, system_prompt)
        input_content = ScenarioExtractor.get_input_from_bug_dict(bug)
        # print(json.dumps(input_content, indent=2))
        if input_content.strip():
            response = GPTUtil.client_gpt_oss_20b.chat.completions.create(
                model="gpt-oss:20b",
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": input_content}
                ],
                # reasoning={"effort": 'low'},
            )
            cost = None
        else:
            response, cost = None, None
        output = {
            Placeholder.BUG_ID: bug_id,
            Placeholder.SUMMARY: summary,
            Placeholder.COST: cost,
        }
        if response:
            # print(f"{bug_id}: {response.choices[0].message.content}")
            response_output = {
                "include_scenario": response.choices[0].message.content
            }
            # response_output = json.loads(response.choices[0].message.content)
            output = output | response_output
        return output




