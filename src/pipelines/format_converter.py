import json
from pathlib import Path

from src.pipelines.placeholder import Placeholder
from src.utils.gpt_util import GPTUtil
from config import PROMPT_DIR


class FormatConverter:
    def __init__(self):
        pass

    @staticmethod
    def convert_format(input_content, output_format, model=GPTUtil.GPT4_1_MINI[Placeholder.MODEL_NAME],
                       prompt_folder="format_converter", system_prompt='system'):
        with open(Path(PROMPT_DIR, prompt_folder, system_prompt), "r", encoding="utf-8") as file:
            system_instruction = file.read()
        response = GPTUtil.client.responses.parse(
            model=model,
            instructions=system_instruction,
            input=input_content,
            text_format=output_format,
            # previous_response_id=previous_response_id,
            # reasoning={
            #     "effort": "high"
            # }
        )
        cost = GPTUtil.calculate_cost(response)
        # @todo need to test
        # output = response.output[0].content[0].parsed
        # output = response.output[0].content[0].parsed.model_dump()
        output = json.loads(response.output_text)
        return output, cost