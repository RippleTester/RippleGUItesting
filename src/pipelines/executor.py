import copy
import json
import logging
import os
from pathlib import Path

from fpdf import FPDF

from src.pipelines.detector import Detector
from src.pipelines.instruction_use_tool import InstructionReuseTool
from src.pipelines.placeholder import Placeholder
from src.types.docker import DockerImageBuilder, DockerComputer
from src.utils.decorators import timing
from src.utils.file_util import FileUtil
from src.utils.gpt_util import GPTUtil
from src.utils.img_util import ImgUtil
from typing import Optional, cast, Literal, Tuple, List
from anthropic.types.beta import BetaToolUnionParam

from src.utils.claude_util import ClaudeUtil

from pydantic import BaseModel, Field

from src.utils.llm_util import LLMUtil
from config import OUTPUT_DIR, PROMPT_DIR, MAX_EXECUTION_COUNT, APP_NAME_FIREFOX, MAX_UI_INSTRUCTION_COUNT

ActionType = Literal[
    "click", "right_click", "long_click", "double_click", "triple_click",
    "input", "scroll", "drag", "move", "keypress", "wait",
    # "start", "restart"
]

ScrollDirType = Literal["up", "down", "left", "right"]

FOCUS_REQUIRED_KEYS = {"ESC", "ESCAPE", "CTRL", "ALT", "SHIFT"}


class UIInstruction(BaseModel):
    action: ActionType = Field(..., alias=f"{Placeholder.ACTION}")

    scroll_direction: Optional[ScrollDirType] = Field(
        None, alias=f"{Placeholder.SCROLL_DIRECTION}",
        description="Required only when ACTION == scroll"
    )

    element_name:  Optional[str] = Field(None, alias=f"{Placeholder.ELEMENT_NAME}")
    # @todo coordinates should be [(x,y), (x,y)] due to drag using more than one coordinates
    coordinates:  Tuple[float, float] = Field(..., alias=f"{Placeholder.COORDINATES}")

    input_text: Optional[str] = Field(
        None, alias=f"{Placeholder.INPUT_TEXT}",
        description="Required only when ACTION == input"
    )

    keys: Optional[list[str]] = Field(
        None, alias=f"{Placeholder.KEYS}",
        description="List of key names for keypress (e.g. ['ctrl', 'c'])"
    )

class StepUIInstruction(BaseModel):
    step: str = Field(..., alias=f"{Placeholder.STEP}")
    ui_instructions: list[UIInstruction] = Field(..., alias=f"{Placeholder.UI_INSTRUCTIONS}")

class InstructionUseToolOutput(BaseModel):
    chain_of_thoughts: str
    steps: list[StepUIInstruction]

class ComputerUseToolInput(BaseModel):
    chain_of_thoughts: str = Field(..., alias=f"{Placeholder.CHAIN_OF_THOUGHTS}")
    step: str = Field(..., alias=f"{Placeholder.STEP}")
    ui_instructions: list[UIInstruction] = Field(..., alias=f"{Placeholder.UI_INSTRUCTIONS}")


class ComputerUseTool:
    def __init__(self, system_prompt=f'{Placeholder.COMPUTER_USE_TOOL}', prompt_folder=Placeholder.EXECUTOR):
        self.name = f'{Placeholder.COMPUTER_USE_TOOL}'
        with open(Path(PROMPT_DIR, prompt_folder, system_prompt), "r", encoding="utf-8") as file:
            self.description = file.read()

        self.input_schema = ComputerUseToolInput.model_json_schema(by_alias=True)

    def to_params(self):
        return cast(
            BetaToolUnionParam,
            {"name": self.name,
             "description": self.description,
             "input_schema": self.input_schema},
        )

    @staticmethod
    def perform_action(
            action,
            element_coord,
            element_input,
            scroll_direction,
            keys,
            computer,
            commit_id=None,
            app=None,
    ):
        """
        action          -> e.g. 'click', 'double_click', 'type', 'scroll'
        element_coord   -> dictionary with { 'x': int, 'y': int }
        element_input   -> string to type (if action == 'type')
        scroll_direction-> e.g. 'up' or 'down' (if action == 'scroll')
        """
        if element_coord:
            x = element_coord[0]
            y = element_coord[1]
        # if computer is None:
        #     computer = DockerComputer()
        # with DockerComputer() as comp:
        if action == "click" or action == "tap":
            # Single left-click at (x, y)
            computer.click(x, y)

        elif action == "right_click":
            computer.click(x, y, button="right")

        elif action == "middle_click":
            computer.click(x, y, button="middle")

        elif action == "long_click":
            computer.long_click(x, y)

        elif action == "double_click" or action == "double_tap":
            # Double-click at (x, y)
            computer.double_click(x, y)

        elif action == "triple_click" or action == "triple_tap":
            computer.triple_click(x, y)

        elif action == "type" or action == "input":
            if element_coord:
                computer.move(x, y)
            # Type the given input text
            computer.type(element_input)

        elif action == "scroll":
            """
            For vertical scrolling with xdotool:

              - button 4 => scroll up

              - button 5 => scroll down

            We interpret 'scroll_direction' as either 'up' or 'down' 

            and call comp.scroll() accordingly.

            """
            # if no (x, y) provided, default to screen center
            if x is None or y is None:
                w, h = computer.dimensions
                x, y = w // 2, h // 2
            if scroll_direction == "up":
                # Scroll up 3 "clicks"
                computer.scroll(x, y, scroll_x=0, scroll_y=-3)  # -3 triggers button 4 (scroll up)
            elif scroll_direction == "down":
                # Scroll down 3 "clicks"
                computer.scroll(x, y, scroll_x=0, scroll_y=3)  # +3 triggers button 5 (scroll down)
            else:
                print("Unknown scroll direction:", scroll_direction)

        elif action == "drag":
            # @todo
            """
            For dragging, you may need a path:
               path = [{"x": 100, "y": 100}, {"x": 105, "y": 105}, {"x":110, "y":110}]
            If 'element_coord' is just a single point, 
            you might do a short path from (x, y) to (x+N, y+N).
            """
            path = [
                {"x": x, "y": y},
                {"x": x + 100, "y": y + 20},  # example: move diagonally
            ]
            computer.drag(path)
        elif action == "wait":
            # Default wait_time = 1000 ms
            computer.wait()

        elif action == "move":
            computer.move(x, y)

        elif action == "keypress":
            # If no `keys` list is provided, you could parse element_input or do something else:
            # e.g., interpret element_input as a space-separated string of keys
            if keys is None:
                # fallback if not explicitly provided
                keys = element_input.split()

            keys_upper = {k.upper() for k in keys}
            # 🔑 Only click when focus is required AND selection is not needed
            if element_coord and keys_upper & FOCUS_REQUIRED_KEYS:
                computer.click(x, y)
                computer.wait(100)
            computer.keypress(keys)

        # elif action == "restart" or action == "start":
        #     computer.run_single_build(commit_id=commit_id, app=app)

        else:
            print(f"Unknown action: {action}")


class Executor:
    def __init__(self):
        pass

    @staticmethod
    def setup_docker_computer(build_info):
        # setup docker computer #########################################
        reponame = build_info[Placeholder.SOFTWARE_NAME]
        if reponame == APP_NAME_FIREFOX:
            base_image = f"{reponame.lower()}:{DockerImageBuilder.BASE_ENV_TAG}"
            if not DockerImageBuilder.docker_image_exists(base_image):
                print(f"[!] Base image missing, building: {base_image}")
                base_image = DockerImageBuilder.build_base_image(reponame=reponame)
            image_name = base_image
        else:
            diff_image = DockerImageBuilder.ensure_diff_image(
                reponame=reponame,
                before_commit=build_info[Placeholder.PARENT_COMMIT_ID],
                after_commit=build_info[Placeholder.COMMIT_ID],
            )
            image_name = diff_image
        computer = DockerComputer.run_from_image(image=image_name)
        DockerComputer.open_vnc_gui()
        return computer

    @staticmethod
    def execute_test_scenario(build_info, test_scenario, index_output_filepath,
                              computer_use_tool=None, use_instruction_reuse_tool=False,
                              use_extracted_executor_memory=True,
                              include_executor_history_image=False,
                              instruction_reuse_tool_model=GPTUtil.GPT5_2,
                              executor_model=ClaudeUtil.CLAUDE_SONNET_4_5,
                              replay_wait_time=3000):
        """
        include Play + Replay
        """
        if computer_use_tool is None:
            computer_use_tool = ComputerUseTool().to_params()

        computer = Executor.setup_docker_computer(build_info)
        # index_output_filepath = Path(output_filepath, f"{index}")
        index_output_filepath = Path(index_output_filepath)
        if not os.path.exists(index_output_filepath):
            os.makedirs(index_output_filepath)
        execution_memory_for_reuse = None
        if use_instruction_reuse_tool:
            index = int(index_output_filepath.name) if index_output_filepath.name.isdigit() else None
            prev_path = index_output_filepath.parent / str(index - 1) if index and index > 0 else None
            if prev_path:
                last_player_output = FileUtil.load_json(Path(prev_path, f"{Placeholder.PLAYER}.json"))
                execution_memory_for_reuse = Executor.extract_execution_memory_from_player_output(last_player_output)

        (player_output, messages), duration_mins_after_change = Executor.execute_after_code_change_version(build_info, test_scenario, computer, computer_use_tool,
                                                                                                           execution_memory_for_reuse=execution_memory_for_reuse,
                                                                                                           use_extracted_executor_memory=use_extracted_executor_memory,
                                                                                                           include_executor_history_image=include_executor_history_image,
                                                                                                           instruction_reuse_tool_model=instruction_reuse_tool_model,
                                                                                                           executor_model=executor_model)
        if player_output is None and messages is None:
            return None
        player_output[f"{Placeholder.DURATION_MINS}"] = duration_mins_after_change
        total_cost = Executor.calculate_total_cost(player_output)
        player_output[Placeholder.TOTAL_COST] = total_cost
        FileUtil.dump_json(Path(index_output_filepath, f"{Placeholder.PLAYER}.json"), player_output)

        # Replayer ################################################################################################
        computer = Executor.setup_docker_computer(build_info)
        replay_output, duration_mins_before_change = Executor.execute_before_code_change_version(build_info, player_output, computer, wait_time=replay_wait_time)
        replay_output[f"{Placeholder.DURATION_MINS}_AFTER_CHANGE"] = duration_mins_after_change
        replay_output[f"{Placeholder.DURATION_MINS}_BEFORE_CHANGE"] = duration_mins_before_change
        if len(replay_output[Placeholder.OUTPUT]) > 1:
            replay_output[Placeholder.OUTPUT][-2][Placeholder.ANSWER][Placeholder.TOTAL_DURATION_MINS] = duration_mins_before_change + duration_mins_after_change
            replay_output[Placeholder.OUTPUT][-2][Placeholder.ANSWER][Placeholder.TOTAL_COST] = total_cost
        replay_output = Replayer.annotate_screenshots_by_pixel(replay_output, index_output_filepath)
        FileUtil.dump_json(Path(index_output_filepath,
                                f"{Placeholder.REPLAYER}.json"), replay_output)
        Replayer.create_pdf_with_annotated_screenshot(replay_output, index_output_filepath)
        return replay_output

    @staticmethod
    def calculate_total_cost(play_output):
        total_cost = 0
        for one_output in play_output[Placeholder.OUTPUT]:
            # One Claude call may return multiple actions, split into multiple one_outputs.
            # If CHAIN_OF_THOUGHTS is an empty string, it means this result belongs to a previous call
            # and its cost has already been accounted for, so it should not be counted again.
            if one_output and one_output[Placeholder.ANSWER] and one_output[Placeholder.ANSWER][Placeholder.CHAIN_OF_THOUGHTS]:
                total_cost += one_output[Placeholder.ANSWER].get(Placeholder.COST, {}).get(Placeholder.TOTAL_COST, 0)
        if Placeholder.REUSABLE_INSTRUCTIONS in play_output.keys():
            total_cost += play_output[Placeholder.REUSABLE_INSTRUCTIONS][Placeholder.COST][Placeholder.TOTAL_COST]
        return total_cost

    @staticmethod
    @timing
    def execute_after_code_change_version(build_info, test_scenario, computer, computer_use_tool,
                                          execution_memory_for_reuse=None,
                                          use_extracted_executor_memory=True,
                                          include_executor_history_image=False,
                                          instruction_reuse_tool_model=GPTUtil.GPT5_2,
                                          executor_model=ClaudeUtil.CLAUDE_SONNET_4_5):
        is_version_started= computer.run_single_build(commit_id=build_info[Placeholder.COMMIT_ID],
                                  build_id=build_info[Placeholder.BUILD_ID_FIRST_WITH],
                                  app=build_info[Placeholder.SOFTWARE_NAME])
        if is_version_started:
            reusable_instructions = None
            if execution_memory_for_reuse:
                test_scenario_without_oracles = {
                    "summary": test_scenario.get("summary"),
                    "steps": [
                        {"step": step.get("step")}
                        for step in test_scenario.get("steps", [])
                    ]
                }
                reusable_instructions, response_id = InstructionReuseTool.get_reusable_instructions(test_scenario_without_oracles, execution_memory_for_reuse,
                                                                                                       previous_response_id=None,
                                                                                                       model=instruction_reuse_tool_model, )
            player_output, messages = Executor.run_loop(test_scenario, build_info=build_info, computer=computer, tools=[computer_use_tool],
                                                        model=executor_model, reusable_instructions=reusable_instructions,
                                                        use_extracted_executor_memory=use_extracted_executor_memory,
                                                        include_executor_history_image=include_executor_history_image)
            return player_output, messages
        return None, None

    @staticmethod
    @timing
    def execute_before_code_change_version(build_info, player_output, computer, wait_time=3000):
        computer.run_single_build(commit_id=build_info[Placeholder.PARENT_COMMIT_ID],
                                  build_id=build_info[Placeholder.BUILD_ID_LAST_WITHOUT],
                                  app=build_info[Placeholder.SOFTWARE_NAME])
        replay_output = Replayer.replay(player_output, computer=computer, wait_time=wait_time,
                                        commit_id=build_info[Placeholder.PARENT_COMMIT_ID],
                                        app=build_info[Placeholder.SOFTWARE_NAME])
        return replay_output


    @staticmethod
    def run_loop(input_content,
                 build_info,
                 computer,
                 max_loop_count=MAX_EXECUTION_COUNT,
                 prompt_folder=Placeholder.EXECUTOR, system_prompt="system_claude",
                 tools=[],
                 # output_format=None,
                 wait_time=3000, # ms
                 model=ClaudeUtil.CLAUDE_SONNET_4,
                 reusable_instructions=None,
                 use_extracted_executor_memory=True,
                 include_executor_history_image=False,
                 max_ui_instruction_count=MAX_UI_INSTRUCTION_COUNT,
                 ):
        """
        run loop -> the whole interactions for the test scenario
        """
        player_output = {
            Placeholder.SCENARIO: input_content,
            # Placeholder.REUSABLE_INSTRUCTIONS: reusable_instructions,
            Placeholder.OUTPUT: []
        }
        if reusable_instructions:
            player_output[Placeholder.REUSABLE_INSTRUCTIONS] = reusable_instructions
            reusable_instructions = reusable_instructions["steps"]

        i = 0
        ui_instruction_count = 0
        messages = []
        tool_use_id = None
        # test_scenario only input summary and steps (without oracles) into executor
        input_content_without_oracles = {
                "summary": input_content.get("summary"),
                "steps": [
                    {"step": step.get("step")}
                    for step in input_content.get("steps", [])
                ]
            }

        step = input_content_without_oracles

        while step != '' and i < max_loop_count and ui_instruction_count < max_ui_instruction_count:
            if i == 0:
                computer.wait(wait_time)
                base64_image = computer.screenshot()

            answer, messages, tool_use_id = Executor.run_once(input_content_without_oracles, base64_image,
                                                              prompt_folder=prompt_folder,
                                                              system_prompt=system_prompt,
                                                              tools=tools, model=model,
                                                              messages=messages, tool_use_id=tool_use_id,
                                                              reusable_instructions=reusable_instructions,
                                                              use_extracted_executor_memory=use_extracted_executor_memory,
                                                              include_executor_history_image=include_executor_history_image)
            # print(tool_use_id)
            # print(messages)
            try:
                parsed_ans = ComputerUseToolInput.model_validate(answer)
                cots = parsed_ans.chain_of_thoughts
                step = parsed_ans.step
                for instruction_index, instruction in enumerate(parsed_ans.ui_instructions):
                    ui_instruction_count = ui_instruction_count + 1
                    # element_coord =
                    # if with_image_scale:
                    #     element_coord = ImgUtil.scale_coordinates(element_coord, with_image_scale)
                    ComputerUseTool.perform_action(instruction.action, instruction.coordinates, instruction.input_text,
                                            instruction.scroll_direction, instruction.keys, computer,
                                                   commit_id=build_info[Placeholder.COMMIT_ID], app=build_info[Placeholder.SOFTWARE_NAME])
                    if instruction_index != 0:
                        cots = ""
                    one_output_pair = {
                        Placeholder.SCREENSHOT: base64_image,
                        Placeholder.ANSWER: {
                            Placeholder.CHAIN_OF_THOUGHTS: cots,
                            Placeholder.STEP: step,
                            Placeholder.UI_INSTRUCTION: answer[Placeholder.UI_INSTRUCTIONS][instruction_index],
                            Placeholder.COST: answer[Placeholder.COST],
                            Placeholder.DURATION_MINS: answer[Placeholder.DURATION_MINS]
                        }
                    }
                    player_output[Placeholder.OUTPUT].append(one_output_pair)
                    computer.wait(wait_time)
                    base64_image = computer.screenshot()
            except Exception as e:
                logging.warn(f"ComputerUseToolInput.model_validate: {e}")
                pass
            # step = answer[Placeholder.STEP]
            i = i + 1
        one_output_pair = {
            Placeholder.SCREENSHOT: base64_image,
            Placeholder.ANSWER: None
        }
        player_output[Placeholder.OUTPUT].append(one_output_pair)

        return player_output, messages

    @staticmethod
    def run_once(step, base64_image,
                 prompt_folder="executor",
                 system_prompt="system_claude",
                 tools = [],
                 model=ClaudeUtil.CLAUDE_SONNET_4,
                 messages=None,
                 tool_use_id=None,
                 reusable_instructions=None,
                 use_extracted_executor_memory=True,
                 include_executor_history_image=False
                 ):
        """
        run once -> one interaction for the test scenario
        """
        system_instructions = ClaudeUtil.get_instructions(prompt_folder, system_prompt)
        text_input = step
        if use_extracted_executor_memory:
            extracted_memory = Executor.extract_execution_memory_from_messages(messages)
            text_input = {
                Placeholder.SCENARIO: step,
                Placeholder.EXECUTION_MEMORY: extracted_memory,
            }
            tool_use_id = None
        if reusable_instructions:
            text_input[Placeholder.REUSABLE_INSTRUCTIONS] = reusable_instructions
        question = ClaudeUtil.question(text_input, base64_image, tool_use_id=tool_use_id)
        # print(json.dumps(question, indent=2))
        messages = LLMUtil.add_role_content_dict_into_messages(LLMUtil.ROLE_USER, question, messages)
        input_messages = messages
        if use_extracted_executor_memory:
            input_messages = []
            input_messages = LLMUtil.add_role_content_dict_into_messages(LLMUtil.ROLE_USER, question, input_messages)
        # print(json.dumps(input_messages, indent=4))
        # print(system_instructions)
        (response, cost), duration_mins = ClaudeUtil.chat_completions(messages=input_messages,
                                                     system_instruction=system_instructions,
                                                     model=model, tools=tools)
        answer, tool_use_id, tool_name = Executor.process_response(response)
        answer_copy = copy.deepcopy(answer)
        if tool_use_id is not None:
            answer_copy = [
                {'type': 'tool_use',
                 'id': tool_use_id,
                 'name': tool_name,
                 'input': answer_copy}
            ]
        messages = LLMUtil.add_role_content_dict_into_messages(LLMUtil.ROLE_ASSISTANT, answer_copy, messages)
        # messages_copy = copy.deepcopy(messages)
        # with this might be good execution; without this, faster and cheaper
        if not include_executor_history_image:
            messages = ClaudeUtil.get_messages_without_image_encode(messages)
        # LLMUtil.show_messages(messages)

        # print(answer)
        # print(type(answer))
        # answer = LLMUtil.add_into_answer(answer, cost)
        answer[Placeholder.COST] = cost
        if duration_mins:
            answer[Placeholder.DURATION_MINS] = duration_mins

        return answer, messages, tool_use_id

    @staticmethod
    def extract_execution_memory_from_player_output(player_output):
        execution_memory = {
            f"{Placeholder.SCENARIO}": player_output.get(f"{Placeholder.SCENARIO}"),
            f"{Placeholder.OUTPUT}": []
        }

        for item in player_output.get(f"{Placeholder.OUTPUT}", []):
            ans = item.get(f"{Placeholder.ANSWER}")
            if not isinstance(ans, dict):
                continue

            kept = {}
            for k in (f"{Placeholder.CHAIN_OF_THOUGHTS}", f"{Placeholder.STEP}", f"{Placeholder.UI_INSTRUCTION}"):
                if k in ans:
                    kept[k] = ans[k]

            if kept:
                execution_memory[f"{Placeholder.OUTPUT}"].append(kept)

        return execution_memory

    @staticmethod
    def extract_execution_memory_from_messages(trace: list[dict]) -> list[dict]:
        extracted_memory = []

        for msg in trace:
            if msg.get("role") != "assistant":
                continue

            for block in msg.get("content", []):
                if block.get("type") != "tool_use":
                    continue

                inp = block.get("input", {})

                extracted_memory.append({
                    f"{Placeholder.CHAIN_OF_THOUGHTS}": inp.get(f"{Placeholder.CHAIN_OF_THOUGHTS}", ""),
                    f"{Placeholder.STEP}": inp.get(f"{Placeholder.STEP}", ""),
                    f"{Placeholder.UI_INSTRUCTIONS}": inp.get(f"{Placeholder.UI_INSTRUCTIONS}", [])
                })

        return extracted_memory

    @staticmethod
    def process_response(response):
        tool_use_block = next(
            (b for b in response.content
             if (isinstance(b, dict) and b.get("type") == "tool_use") or
             (hasattr(b, "type") and getattr(b, "type") == "tool_use")),
            None
        )
        if tool_use_block:
            if isinstance(tool_use_block, dict):
                answer = tool_use_block.get("input")
                tool_use_id = tool_use_block.get("id")
                tool_name = tool_use_block.get("name")
            else:
                answer = getattr(tool_use_block, "input", None)
                tool_use_id = getattr(tool_use_block, "id", None)
                tool_name = getattr(tool_use_block, "name", None)
        else:
            first_block = response.content[0]
            if isinstance(first_block, dict):
                answer = first_block.get("text")
            else:
                answer = getattr(first_block, "text", None)
            tool_use_id = None
            tool_name = None
        return answer, tool_use_id, tool_name

    @staticmethod
    def convert_encode_img_into_filepath(player_output, output_dir):
        output = player_output[Placeholder.OUTPUT]
        for index, one_output in enumerate(output):
            screenshot = ImgUtil.decode_image(one_output[Placeholder.SCREENSHOT])
            filepath = Path(output_dir, f"{Placeholder.SCREENSHOT}_{index}.png")
            one_output[Placeholder.SCREENSHOT] = filepath
            FileUtil.dump_img(filepath, screenshot)
        return output


class Replayer(Executor):

    @staticmethod
    def replay(player_output,
               computer,
               wait_time=3000,  # ms
               commit_id=None,
               app=None,
               ):
    # replay just by reusing the existing operation

    # with (DockerComputer() as computer):
        for one_output in player_output[Placeholder.OUTPUT]:
            # sleep 3000/1000 seconds
            computer.wait(wait_time)
            base64_image = computer.screenshot()
            one_output[Placeholder.SCREENSHOT_BEFORE_CHANGE] = one_output.get(Placeholder.SCREENSHOT_BEFORE_CHANGE, base64_image)
            one_output_ans = one_output[Placeholder.ANSWER]
            if one_output_ans:
                action = one_output_ans[Placeholder.UI_INSTRUCTION][Placeholder.ACTION]
                element_coords = None
                if Placeholder.COORDINATES in one_output_ans[Placeholder.UI_INSTRUCTION].keys() and one_output_ans[Placeholder.UI_INSTRUCTION][Placeholder.COORDINATES]:
                    element_coord_x = one_output_ans[Placeholder.UI_INSTRUCTION][Placeholder.COORDINATES][0]
                    element_coord_y = one_output_ans[Placeholder.UI_INSTRUCTION][Placeholder.COORDINATES][1]
                    element_coords = (element_coord_x, element_coord_y)

                element_input = one_output_ans[Placeholder.UI_INSTRUCTION].get(Placeholder.INPUT_TEXT, None)
                scroll_direction = one_output_ans[Placeholder.UI_INSTRUCTION].get(Placeholder.SCROLL_DIRECTION,
                                                                                  None)
                keys = one_output_ans[Placeholder.UI_INSTRUCTION].get(Placeholder.KEYS, None)

                ComputerUseTool.perform_action(action, element_coords, element_input, scroll_direction, keys, computer,
                                               commit_id=commit_id, app=app)
        return player_output

    @staticmethod
    def cover_top_bar_with_black_padding(base64_screenshot, output_filepath, img_name):
        screenshot = ImgUtil.decode_image(base64_screenshot)
        FileUtil.dump_img(Path(output_filepath, img_name), screenshot)
        ImgUtil.cover_top_bar_with_black_padding(Path(output_filepath, img_name),
                                                 Path(output_filepath, img_name),
                                                 top_bar_height=25)
        return str(Path(output_filepath, img_name))

    @staticmethod
    def annotate_screenshots_by_pixel(replay_output, output_filepath):
        output_filepath = Path(output_filepath, Placeholder.SCREENSHOT)
        if not os.path.exists(output_filepath):
            # If it doesn't exist, create itv
            os.makedirs(output_filepath)
        for index, screenshot_operation in enumerate(replay_output[Placeholder.OUTPUT]):
            base64_screenshot = screenshot_operation[Placeholder.SCREENSHOT]
            img_name = f"{Placeholder.SCREENSHOT}_{index}.png"
            img_filepath_after_change = Replayer.cover_top_bar_with_black_padding(base64_screenshot, output_filepath, img_name)
            # print(element_list)
            base64_screenshot_before_change = screenshot_operation[Placeholder.SCREENSHOT_BEFORE_CHANGE]
            img_name_before_change = f"{Placeholder.SCREENSHOT_BEFORE_CHANGE}_{index}.png"
            img_filepath_before_change = Replayer.cover_top_bar_with_black_padding(base64_screenshot_before_change, output_filepath,
                                                          img_name_before_change)
            boxes = ImgUtil.detect_image_differences_by_pixel(img_filepath_before_change, img_filepath_after_change)

            annotated_img_filepath_after_change, element_list = ImgUtil.draw_bounding_boxes(output_filepath, img_name,
                                                                                            boxes)
            annotated_img_filepath_before_change, element_list = ImgUtil.draw_bounding_boxes(output_filepath,
                                                                                             img_name_before_change,
                                                                                             boxes)
            annotated_screenshot = {
                Placeholder.SCREENSHOT: str(Path(output_filepath, img_name_before_change)),
                Placeholder.PARSED_SCREENSHOT: str(annotated_img_filepath_before_change),
                # Placeholder.PARSED_INFO: element_list,
            }
            screenshot_operation[Placeholder.SCREENSHOT_BEFORE_CHANGE] = annotated_screenshot

            annotated_screenshot_after_change = {
                Placeholder.SCREENSHOT: str(Path(output_filepath, img_name)),
                Placeholder.PARSED_SCREENSHOT: str(annotated_img_filepath_after_change),
                # Placeholder.PARSED_INFO: element_list,
            }
            screenshot_operation[Placeholder.SCREENSHOT] = annotated_screenshot_after_change
            screenshot_operation[Placeholder.PARSED_INFO] = screenshot_operation.get(Placeholder.PARSED_INFO,
                                                                                     element_list)

        return replay_output

    @staticmethod
    def create_pdf_with_annotated_screenshot(output_dict, pdf_filepath):
        """
        show player output in a pdf
        """
        pdf_filepath = Path(pdf_filepath, f"{Placeholder.REPLAYER}.pdf")

        screenshot_operation_list = output_dict[Placeholder.OUTPUT]
        if screenshot_operation_list:
            pdf = FPDF()
            pdf.add_page()
            test_scenario = output_dict[Placeholder.SCENARIO]
            text = json.dumps(test_scenario, indent=5)

            pdf.set_font("Arial", size=6)
            line_height = 3
            pdf.multi_cell(0, line_height, text)

            # REUSABLE_INSTRUCTIONS
            if output_dict.get(Placeholder.REUSABLE_INSTRUCTIONS):
                pdf.add_page()
                reusable_text = json.dumps(
                    output_dict[Placeholder.REUSABLE_INSTRUCTIONS],
                    indent=5,
                )
                pdf.multi_cell(0, line_height, "=== REUSABLE INSTRUCTIONS ===")
                pdf.ln(1)
                pdf.multi_cell(0, line_height, reusable_text)

            for screenshot_operation_dict in screenshot_operation_list:
                pdf.add_page()
                operation = screenshot_operation_dict[Placeholder.ANSWER]

                if operation:
                    cost_keep_keys = [
                        Placeholder.MODEL_NAME,
                        Placeholder.PRICE_PER_INPUT_TOKEN,
                        Placeholder.PRICE_PER_OUTPUT_TOKEN,
                        "input_tokens",
                        "output_tokens",
                        Placeholder.TOTAL_COST
                    ]
                    operation[Placeholder.COST] = {
                        k: v for k, v in operation[Placeholder.COST].items()
                        if k in cost_keep_keys
                    }

                    formatted_text = json.dumps(operation, indent=2, ensure_ascii=True)
                    pdf.set_font("Courier", size=6)
                    pdf.multi_cell(0, 6, formatted_text)
                    pdf.ln(4)
                else:
                    pdf.set_font("Arial", "I", size=6)
                    pdf.cell(0, 8, "(No operation text available)", ln=True)
                    pdf.ln(4)

                # -----------------------------
                # 🔧 CHANGED: image layout logic
                # -----------------------------

                current_y = pdf.get_y()

                page_width = pdf.w - 2 * pdf.l_margin
                half_width = page_width / 2.0

                IMAGE_TOP_MARGIN = 10  # 🆕 ADDED
                IMAGE_GAP = 5  # 🆕 ADDED

                # ---- LEFT IMAGE ----
                left_img_path = screenshot_operation_dict[
                    Placeholder.SCREENSHOT_BEFORE_CHANGE
                ][Placeholder.PARSED_SCREENSHOT]

                # 🆕 ADDED: ensure enough space before drawing image
                Detector.ensure_space_for_image(
                    pdf,
                    image_path=left_img_path,
                    display_width=half_width,
                    top_margin=IMAGE_TOP_MARGIN
                )

                current_y = pdf.get_y()  # 🔧 CHANGED: refresh Y after possible add_page

                left_img = FileUtil.load_img(left_img_path)
                pdf.image(
                    left_img,
                    x=pdf.l_margin,
                    y=current_y + IMAGE_TOP_MARGIN,
                    w=half_width
                )

                # ---- RIGHT IMAGE ----
                right_img_path = screenshot_operation_dict[
                    Placeholder.SCREENSHOT
                ][Placeholder.PARSED_SCREENSHOT]

                right_img = FileUtil.load_img(right_img_path)
                pdf.image(
                    right_img,
                    x=pdf.l_margin + half_width + IMAGE_GAP,
                    y=current_y + IMAGE_TOP_MARGIN,
                    w=half_width
                )

            pdf.output(pdf_filepath)

        return pdf_filepath

