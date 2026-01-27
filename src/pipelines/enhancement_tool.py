import json
from src.pipelines.generation_tool import Scenario, Step
from src.pipelines.placeholder import Placeholder
from src.utils.gpt_util import GPTUtil
from src.utils.llm_util import LLMUtil
from config import APP_NAME_FIREFOX
from pydantic import BaseModel


class Example(BaseModel):
    representative_reason: str
    value: str

class TestData(BaseModel):
    name: str
    requirement: str
    examples: list[Example] | None

class ScenarioWithData(BaseModel):
    # explanation: str
    test_data: list[TestData] | None
    summary: str
    steps: list[Step]

class DataEnhancementOutput(BaseModel):
    test_scenarios: list[ScenarioWithData]

class PathEnhancementOutput(BaseModel):
    step_diversity_analysis: list[str]
    search_query_generation: list[str]
    test_scenarios: list[Scenario]

class EnhancementTool:

    @staticmethod
    def enhance(input_content,
                prompt_folder=Placeholder.ENHANCER,
                system_prompt=Placeholder.SYSTEM,
                output_format=None,
                previous_response_id=None, model=GPTUtil.GPT5,
                tools=[],
                include_search_results=True,
                vector_store_ids=None,
                build_info = None,
                reponame=APP_NAME_FIREFOX
                ):

        instructions = None
        if previous_response_id is None:
            instructions = LLMUtil.get_instructions(
                prompt_folder=prompt_folder,
                system_prompt=system_prompt)
        if vector_store_ids:
            file_search_tool = {
                "type": "file_search",
                "vector_store_ids": vector_store_ids
            }
            tools.append(file_search_tool)
        # output_format = EnhancerOutput
        if tools and include_search_results:
            include_search_results = ["file_search_call.results"]
        else:
            include_search_results = []
        (response, cost), duration_mins = GPTUtil.parse_response(str(input_content),
                                                output_format=output_format,
                                                previous_response_id=previous_response_id,
                                                system_instructions=instructions,
                                                tools=tools,
                                                include=include_search_results,
                                                model=model)
        # print(json.dumps(json.loads(response.model_dump_json()), indent=2))
        # output = json.loads(response.output_text)
        outputs = GPTUtil.get_response_outputs(response)
        if outputs:
            output = outputs[0]
            output[Placeholder.RESPONSE_ID] = output.get(Placeholder.RESPONSE_ID, response.id)
            tool = GPTUtil.extract_tool_invocations_from_response(response)
            output[Placeholder.TOOL] = output.get(Placeholder.TOOL, tool)
            output[Placeholder.COST] = output.get(Placeholder.COST, cost)
            output[Placeholder.DURATION_MINS] = output.get(Placeholder.DURATION_MINS, duration_mins)
            output[Placeholder.INFO] = output.get(Placeholder.INFO, build_info)
        else:
            output = None
        messages = LLMUtil.get_messages(instructions, [(input_content, output)])
        # LLMUtil.show_messages(messages)

        return output, messages