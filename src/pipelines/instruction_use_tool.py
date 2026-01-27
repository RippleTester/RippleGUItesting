import json

from src.pipelines.placeholder import Placeholder

from src.utils.gpt_util import GPTUtil
from typing import Optional, List, Literal
from pydantic import BaseModel


class UIInstructionSchema(BaseModel):
    ACTION: str
    SCROLL_DIRECTION: str
    ELEMENT_NAME: Optional[str]
    coordinates: Optional[List[int]]
    KEYS: Optional[List[str]]
    INPUT_TEXT: Optional[str]

class StepUIInstruction(BaseModel):
    STEP: str
    UI_INSTRUCTIONS: List[UIInstructionSchema]

class InstructionUseToolOutput(BaseModel):
    chain_of_thoughts: str
    steps: list[StepUIInstruction]


class InstructionReuseTool:
    """
    LLM component that derives reusable StepUIInstructions
    from scenario + common step seeds + execution memory.
    """

    @staticmethod
    def get_reusable_instructions(test_scenario, execution_memory=None,
                                  # common_step_instructions=None,
                                  previous_response_id=None,
                                  output_format=InstructionUseToolOutput, model=GPTUtil.GPT5_2, reasoning='medium'):
        system_instructions = GPTUtil.get_instructions(prompt_folder=Placeholder.EXECUTOR, system_prompt=f'{Placeholder.INSTRUCTION_REUSE_TOOL}')

        # if common_step_instructions is None:
        #     common_step_instructions = FileUtil.load_json(Path(PROMPT_DIR, Placeholder.EXECUTOR, f"{Placeholder.UBUNTU_COMMON_STEP_INSTRUCTIONS}.json"))
        text_input = {
            Placeholder.SCENARIO: test_scenario,
            # Placeholder.COMMON_STEP_INSTRUCTIONS: common_step_instructions,
        }

        # if executor_messages:
        text_input[Placeholder.EXECUTION_MEMORY] = execution_memory

        text_input = GPTUtil.get_text_input(text_input)
        user_input = json.dumps(text_input, ensure_ascii=False, indent=2)

        (response, cost), duration_mins = GPTUtil.parse_response(user_input, output_format=output_format,
                                                                 previous_response_id=previous_response_id,
                                                                 system_instructions=system_instructions,
                                                                 model=model, reasoning=reasoning)
        outputs = GPTUtil.get_response_outputs(response)
        if outputs:
            output = outputs[0]
            output[Placeholder.COST] = cost
            output[Placeholder.DURATION_MINS] = duration_mins
        # print(json.dumps(output, indent=2))
        else:
            output = None
        return output, response.id


