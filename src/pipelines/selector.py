import json

from src.pipelines.generation_tool import GenerationTool
from src.pipelines.placeholder import Placeholder
from src.utils.gpt_util import GPTUtil
from src.utils.llm_util import LLMUtil
from pydantic import BaseModel


class SelectorOutput(BaseModel):
    chain_of_thoughts: str
    suitable_for_test: bool


class Selector:
    def __init__(self):
        pass

    @staticmethod
    def select_pull_for_testing(pull, with_relevant_scenarios, reponame,
                          output_format=SelectorOutput,
                          prompt_folder=Placeholder.SELECTOR, system_prompt=Placeholder.SYSTEM,
                          model=GPTUtil.GPT5_2, reasoning='medium'):
        commits = pull.commits
        input_content = GenerationTool.get_input_from_commits(commits, with_change_desc=True, with_change_intent=True,
                                                              # with_file_content,
                                                              with_relevant_scenarios=with_relevant_scenarios,
                                                              # with_cochange_file_content,
                                                              reponame=reponame
                                                              )
        if isinstance(input_content, (dict, list)):
            input_content = json.dumps(input_content, ensure_ascii=False, indent=2)

        system_instructions = LLMUtil.get_instructions(prompt_folder, system_prompt)
        duration_mins = None
        if input_content.strip():
            (response, cost), duration_mins = GPTUtil.parse_response(input_content, output_format=output_format, system_instructions=system_instructions,
                                    model=model, reasoning=reasoning)
        else:
            response, cost = None, None
        output = {
            Placeholder.BUG_ID: pull.id,
            Placeholder.COST: cost,
            Placeholder.DURATION_MINS: duration_mins,
        }
        if response:
            response_output = json.loads(response.output_text)
            output = output | response_output
        return output

