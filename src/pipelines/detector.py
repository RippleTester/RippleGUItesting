import copy
import json
from tqdm import tqdm
from pathlib import Path

from src.pipelines.placeholder import Placeholder
from src.utils.claude_util import ClaudeUtil
from src.utils.file_util import FileUtil
from src.utils.gpt_util import GPTUtil
from pydantic import BaseModel
from typing import cast
from anthropic.types.beta import BetaToolUnionParam
from src.utils.img_util import ImgUtil
from fpdf import FPDF

from src.utils.llm_util import LLMUtil
from config import PROMPT_DIR, MAX_DETECTION_COUNT


class BugReport(BaseModel):
    summary: str
    steps_to_reproduce: list[str]
    expected_behaviors: list[str]
    actual_behaviors: list[str]

class DetectorOutputFormat(BaseModel):
    chain_of_thoughts: str
    bug_reports: list[BugReport]


class BugReportTool:
    def __init__(self, system_prompt=f'{Placeholder.BUG_REPORT_TOOL}', prompt_folder=Placeholder.DETECTOR):
        self.name = f'{Placeholder.BUG_REPORT_TOOL}'
        with open(Path(PROMPT_DIR, prompt_folder, system_prompt), "r", encoding="utf-8") as file:
            self.description = file.read()
        # self.description = (
        #     "You are a precise `computer_use_tool` that generates UI instructions based on the current GUI state and step. "
        # )

        self.input_schema = DetectorOutputFormat.model_json_schema(by_alias=True)

    def to_params(self):
        return cast(
            BetaToolUnionParam,
            {"name": self.name,
             "description": self.description,
             "input_schema": self.input_schema},
        )


class Detector:
    def __init__(self):
        pass

    @staticmethod
    def get_user_input(one_player_output, code_change_intent=None, code_change_description=None, test_scenario=None,
                       with_response=True):
        """
        code_change_intent + code_change_description
        test_scenario
        Step-Screenshot Pairs:
            • Parsed Screenshot *before* the code change (with associated parsed information)
            • Parsed Screenshot *after* the code change (with associated parsed information)
            • Next Step
        """
        input_list = []
        if code_change_intent is not None:
            text_input = {
                Placeholder.CODE_CHANGE_INTENT: code_change_intent,
                Placeholder.CODE_CHANGE_DESCRIPTION: code_change_description,
                Placeholder.SCENARIO: test_scenario,
            }
            text_input = GPTUtil.get_text_input(text_input, with_response=with_response)
            input_list.append(text_input)
        screenshot_after_change_dict = one_player_output[Placeholder.SCREENSHOT]
        screenshot_before_change_dict = one_player_output[Placeholder.SCREENSHOT_BEFORE_CHANGE]
        screenshot_dict_list = [screenshot_before_change_dict, screenshot_after_change_dict]
        for screenshot_index, screenshot_dict in enumerate(screenshot_dict_list):
            parsed_info = screenshot_dict[Placeholder.PARSED_INFO]
            remove = {Placeholder.INTERACTIVITY, Placeholder.TYPE}  # any iterable of keys
            parsed_info = [
                {k: v for k, v in d.items() if k not in remove}
                for d in parsed_info  # parsed_info 是 list
            ]
            text_input = {Placeholder.PARSED_INFO: parsed_info}
            text_input = GPTUtil.get_text_input(text_input, with_response=with_response)
            input_list.append(text_input)

            screenshot_parsed = screenshot_dict[Placeholder.PARSED_SCREENSHOT]
            screenshot_parsed = ImgUtil.encode_image(screenshot_parsed)
            image_input = GPTUtil.get_image_base64_input(screenshot_parsed, with_response=with_response)
            input_list.append(image_input)
        operation = one_player_output[Placeholder.ANSWER]
        text_input = f"{Placeholder.OPERATION}: {operation}\n"
        text_input = GPTUtil.get_text_input(text_input, with_response=with_response)
        input_list.append(text_input)
        user_input = [
            {
                "role": "user",
                "content": input_list,
            }
        ]
        return user_input

    @staticmethod
    def get_input_list(one_player_output,
                       code_change_intent=None, change_intent_explanation=None,
                       test_scenario=None, with_response=True):
        """
        code_change_intent + code_change_description
        test_scenario
        Step-Screenshot Pairs:
            • Parsed Screenshot *before* the code change (with associated parsed information)
            • Parsed Screenshot *after* the code change (with associated parsed information)
            • Next Step
        """
        input_list = []
        if code_change_intent is not None:
            text_input = {
                Placeholder.CODE_CHANGE_INTENT: code_change_intent,
                Placeholder.CHANGE_INTENT_EXPLANATION: change_intent_explanation,
                Placeholder.SCENARIO: test_scenario,
            }
            text_input = GPTUtil.get_text_input(text_input, with_response=with_response)
            input_list.append(text_input)
        parsed_info = one_player_output[Placeholder.PARSED_INFO]
        if len(parsed_info) != 0:
            screenshot_after_change_dict = one_player_output[Placeholder.SCREENSHOT]
            screenshot_before_change_dict = one_player_output[Placeholder.SCREENSHOT_BEFORE_CHANGE]
            screenshot_dict_list = [screenshot_before_change_dict, screenshot_after_change_dict]
            text_input = {Placeholder.PARSED_INFO: parsed_info}
            text_input = GPTUtil.get_text_input(text_input, with_response=with_response)
            input_list.append(text_input)
            for screenshot_index, screenshot_dict in enumerate(screenshot_dict_list):
                screenshot_parsed = screenshot_dict[Placeholder.PARSED_SCREENSHOT]
                screenshot_parsed = ImgUtil.encode_image(screenshot_parsed)
                image_input = GPTUtil.get_image_base64_input(screenshot_parsed, with_response=with_response)
                input_list.append(image_input)
        operation = one_player_output[Placeholder.ANSWER]
        remove = {Placeholder.COST, Placeholder.CHAIN_OF_THOUGHTS}  # any iterable of keys
        if operation is not None:  # ← guard against None
            operation = [
                {k: v for k, v in operation.items() if k not in remove}
                # for d in operation  # parsed_info 是 list
            ]
        text_input = f"{Placeholder.OPERATION}: {operation}\n"
        text_input = GPTUtil.get_text_input(text_input, with_response=with_response)
        input_list.append(text_input)
        return input_list

    @staticmethod
    def run_once(user_input,
                 output_format=DetectorOutputFormat, previous_response_id=None,
                 prompt_folder="detector", system_prompt="system", model=GPTUtil.GPT5_2,
                 reasoning='medium'):
        """
        one detection for one interaction of the test scenario
        """

        system_instructions = GPTUtil.get_instructions(prompt_folder, system_prompt)
        (response, cost), duration_mins = GPTUtil.parse_response(user_input, output_format=output_format,
                                          previous_response_id=previous_response_id,
                                          system_instructions=system_instructions,
                                          model=model, reasoning=reasoning)
        # print(json.dumps(json.loads(response.model_dump_json()), indent=2))
        # output = json.loads(response.output_text)
        outputs = GPTUtil.get_response_outputs(response)
        if outputs:
            output = outputs[0]
            output[Placeholder.COST] = cost
            output[Placeholder.DURATION_MINS] = duration_mins
        # print(json.dumps(output, indent=2))
        else:
            output = None
        return output, response.id

    @staticmethod
    def run_once_with_messages(user_input,
                 output_format=DetectorOutputFormat, messages=None,
                 prompt_folder="detector", system_prompt="system",
                 model=GPTUtil.GPT5, reasoning='medium'):
        """
        one detection for one interaction of the test scenario
        """
        messages.append(user_input)
        # messages_copy = copy.deepcopy(messages)
        # messages_copy = LLMUtil.get_messages_without_image_encode(messages_copy)
        # LLMUtil.show_messages(messages_copy)
        # system_instructions = GPTUtil.get_instructions(prompt_folder, system_prompt)
        (response, cost), duration_mins = GPTUtil.chat_completions_by_structured_outputs(messages, response_format=output_format,
                                          model=model)
        # print(json.dumps(json.loads(response.model_dump_json()), indent=2))
        output_text = response.choices[0].message.content
        LLMUtil.add_role_content_dict_into_messages(LLMUtil.ROLE_ASSISTANT, output_text, messages)
        output = json.loads(response.choices[0].message.parsed.model_dump_json())
        # print(type(output))
        output[Placeholder.COST] = cost
        output[Placeholder.DURATION_MINS] = duration_mins
        # print(json.dumps(output, indent=2))
        messages = LLMUtil.get_messages_without_image_encode(messages)
        return output, messages

    @staticmethod
    def run_once_by_claude(user_input, tools=None,
                 messages=None,
                 prompt_folder="detector", system_prompt="system", model=GPTUtil.GPT5, tool_use_id=None,):
        """
        one detection for one interaction of the test scenario
        """
        system_instructions = ClaudeUtil.get_instructions(prompt_folder, system_prompt)
        question = ClaudeUtil.question(user_input, tool_use_id=tool_use_id)
        messages = LLMUtil.add_role_content_dict_into_messages(LLMUtil.ROLE_USER, question, messages)

        (response, cost), duration_mins = ClaudeUtil.chat_completions(messages=messages,
                                                     system_instruction=system_instructions,
                                                     model=model, tools=tools)
        output, tool_use_id, tool_name = ClaudeUtil.process_response(response)
        output_copy = copy.deepcopy(output)
        if tool_use_id is not None:
            output_copy = [
                {'type': 'tool_use',
                 'id': tool_use_id,
                 'name': tool_name,
                 'input': output_copy}
            ]
        messages = LLMUtil.add_role_content_dict_into_messages(LLMUtil.ROLE_ASSISTANT, output_copy, messages)
        messages_copy = copy.deepcopy(messages)
        messages_copy = LLMUtil.get_messages_without_image_encode(messages_copy)
        # output = LLMUtil.add_into_answer(output, cost)
        # print(json.dumps(json.loads(response.model_dump_json()), indent=2))
        output = json.loads(output)
        output[Placeholder.COST] = cost
        output[Placeholder.DURATION_MINS] = duration_mins
        print(json.dumps(output, indent=2))
        return output, messages_copy, tool_use_id

    @staticmethod
    def adjust_screenshot_operation_list(screenshot_operation_list):
        """
        adjust screenshot_operation_list where:
            - First screenshot has no operation (None).
            - Each subsequent screenshot is paired with the operation from the previous step.
        """
        prev_op = None
        for screenshot_operation in screenshot_operation_list:
            temp_prev_op = screenshot_operation[Placeholder.ANSWER]
            screenshot_operation[Placeholder.ANSWER] = prev_op
            prev_op = temp_prev_op
        return screenshot_operation_list

    @staticmethod
    def run_loop(code_change_intent, change_intent_explanation,
                 player_output,
                 model=GPTUtil.GPT5,
                 max_detection_count=MAX_DETECTION_COUNT,
                 prompt_folder=Placeholder.DETECTOR, system_prompt=Placeholder.SYSTEM, with_response=False,
                 reasoning='medium'):
        """
        the whole detection for the whole interactions of the test scenario
        """
        detection_count = 0
        input_output_list = []
        detector_output_list = []
        if with_response:
            previous_response_id = None
        else:
            system_instructions = GPTUtil.get_instructions(prompt_folder, system_prompt)
            messages = LLMUtil.get_messages(system_instructions)
        test_scenario = player_output[Placeholder.SCENARIO]
        test_scenario = {k: v for k, v in test_scenario.items() if k not in {'test_data'}}
        screenshot_operation_list = player_output[Placeholder.OUTPUT]
        screenshot_operation_list = Detector.adjust_screenshot_operation_list(screenshot_operation_list)
        input_list = []
        for index, screenshot_operation in enumerate(tqdm(screenshot_operation_list, ascii=True)):
            if index == 0:
                one_input_list = Detector.get_input_list(one_player_output=screenshot_operation,
                                                         code_change_intent=code_change_intent,
                                                         change_intent_explanation=change_intent_explanation,
                                                         test_scenario=test_scenario, with_response=with_response)
            else:
                one_input_list = Detector.get_input_list(one_player_output=screenshot_operation, with_response=with_response)
            input_list.extend(one_input_list)
            if len(screenshot_operation[Placeholder.PARSED_INFO]) != 0:
                user_input = [
                    {
                        "role": "user",
                        "content": input_list,
                    }
                ]
                input_output_list.append(user_input)
                if with_response:
                    output, previous_response_id = Detector.run_once(user_input, previous_response_id=previous_response_id,
                                                                     model=model,
                                                                     reasoning=reasoning)
                else:
                    user_input = user_input[0]
                    output, messages = Detector.run_once_with_messages(user_input, messages=messages,
                                                                       model=model,
                                                                       reasoning=reasoning)
                detector_output_list.append(output)
                input_output_list.append(output)
                input_list = []
                detection_count += 1
                if detection_count >= max_detection_count:
                    return detector_output_list, input_output_list

        return detector_output_list, input_output_list

    @staticmethod
    def run_loop_by_claude(code_change_intent, change_intent_explanation,
                           # change_impact_analysis,
                           player_output,
                            model=ClaudeUtil.CLAUDE_OPUS_4_1, tools=[]):
        """
        the whole detection for the whole interactions of the test scenario
        """
        input_output_list = []
        detector_output_list = []
        messages = None
        tool_use_id = None
        test_scenario = player_output[Placeholder.SCENARIO]
        screenshot_operation_list = player_output[Placeholder.OUTPUT]
        screenshot_operation_list = Detector.adjust_screenshot_operation_list(screenshot_operation_list)
        input_list = []
        for index, screenshot_operation in enumerate(screenshot_operation_list):
            if index == 0:
                one_input_list = Detector.get_input_list(one_player_output=screenshot_operation,
                                                         code_change_intent=code_change_intent,
                                                         change_intent_explanation=change_intent_explanation,
                                                         # change_impact_analysis,
                                                         test_scenario=test_scenario)
            else:
                one_input_list = Detector.get_input_list(one_player_output=screenshot_operation)
            input_list.extend(one_input_list)
            # print(len(screenshot_operation[Placeholder.PARSED_INFO]))
            if len(screenshot_operation[Placeholder.PARSED_INFO]) != 0:
                user_input = [
                    {
                        "role": "user",
                        "content": input_list,
                    }
                ]
                input_output_list.append(user_input)
                output, messages, tool_use_id = Detector.run_once_by_claude(user_input, messages=messages,
                                                                            tools=tools, tool_use_id=tool_use_id,
                                                                            model=model)
                # print(previous_response_id)
                detector_output_list.append(output)
                input_output_list.append(output)
                input_list = []
                # FileUtil.dump_json(Path(OUTPUT_DIR, 'test_detector_input_output.json'), input_output_list)

        return detector_output_list, input_output_list

    @staticmethod
    def detect_bugs(code_change_intent, change_intent_explanation,
                    replay_output, detector_model, index_output_filepath,
                    bug_report_tool=None, max_detection_count=MAX_DETECTION_COUNT, with_response=False,
                    reasoning="medium"):
        """
        the whole detection for the whole interactions of the test scenario
        +
        save output
        +
        create_pdf
        """
        if detector_model[Placeholder.MODEL_NAME].startswith("gpt"):
            detector_output, detector_input_output = Detector.run_loop(code_change_intent,
                                                                       change_intent_explanation,
                                                                       replay_output,
                                                                       model=detector_model,
                                                                       max_detection_count=max_detection_count,
                                                                       with_response=with_response,
                                                                       reasoning=reasoning)

        elif detector_model[Placeholder.MODEL_NAME].startswith("claude"):
            detector_output, detector_input_output = Detector.run_loop_by_claude(code_change_intent, change_intent_explanation,
                                                                                 # change_impact_analysis,
                                                                       replay_output, model=detector_model,
                                                                                 tools=[bug_report_tool])
        total_cost, total_duration_mins = Detector.calculate_cost_and_duration_time(detector_output)
        if detector_output:
            detector_output[-1][Placeholder.TOTAL_COST] = total_cost
            detector_output[-1][Placeholder.TOTAL_DURATION_MINS] = total_duration_mins
        FileUtil.dump_json(Path(index_output_filepath,
                                f'{Placeholder.DETECTOR}_{detector_model[Placeholder.MODEL_NAME]}.json'),
                                detector_input_output)
        # FileUtil.dump_json(Path(index_output_filepath, f'{Placeholder.DETECTOR}.json'),
        #                    detector_input_output)

        Detector.create_pdf(replay_output, detector_output, index_output_filepath)

    @staticmethod
    def calculate_cost_and_duration_time(detector_output):
        total_cost = 0
        total_duration_mins = 0
        for one_output in detector_output:
            total_cost += one_output[Placeholder.COST][Placeholder.TOTAL_COST]
            total_duration_mins += one_output[Placeholder.DURATION_MINS]
        return total_cost, total_duration_mins

    @staticmethod
    def process_answer(raw):
        parsed = DetectorOutputFormat.model_validate(raw)  # allow Enum auto-coercion

        return parsed.chain_of_thoughts, [bug.model_dump() for bug in parsed.bug_reports]

    @staticmethod
    def create_pdf(replayer_output, detector_output, pdf_filepath):
        """
        show player output in a pdf
        """
        detector_output_index = 0
        pdf_filepath = Path(pdf_filepath, f"{Placeholder.OUTPUT}.pdf")

        screenshot_operation_list = replayer_output[Placeholder.OUTPUT]
        # steps = output_dict[Placeholder.STEPS]
        if screenshot_operation_list:
            pdf = FPDF()
            pdf.add_page()
            test_scenario = replayer_output[Placeholder.SCENARIO]
            text = json.dumps(test_scenario, indent=5)
            # Add text
            pdf.set_font("Arial", size=6)
            line_height = 3  # You can change this value to adjust the line height
            pdf.multi_cell(0, line_height, text)
            # REUSABLE_INSTRUCTIONS
            if replayer_output.get(Placeholder.REUSABLE_INSTRUCTIONS):
                pdf.add_page()
                reusable_text = json.dumps(
                    replayer_output[Placeholder.REUSABLE_INSTRUCTIONS],
                    indent=5,
                )
                pdf.multi_cell(0, line_height, "=== REUSABLE INSTRUCTIONS ===")
                pdf.ln(1)
                pdf.multi_cell(0, line_height, reusable_text)
            for screenshot_operation_dict in screenshot_operation_list:
                pdf.add_page()
                operation = screenshot_operation_dict[Placeholder.ANSWER]
                if operation:
                    cost_keep_keys = [Placeholder.MODEL_NAME, Placeholder.PRICE_PER_INPUT_TOKEN,
                                      Placeholder.PRICE_PER_OUTPUT_TOKEN, "input_tokens", "output_tokens",
                                      Placeholder.TOTAL_COST]
                    operation[Placeholder.COST] = {k: v for k, v in operation[Placeholder.COST].items() if
                                                   k in cost_keep_keys}
                    # Convert the dict to a multi‐line, indented JSON string
                    formatted_text = json.dumps(operation, indent=2, ensure_ascii=True)

                    # Option A: Use a monospace font so the JSON lines up
                    pdf.set_font("Courier", size=6)
                    # Print each line with multi_cell so it wraps automatically
                    pdf.multi_cell(0, 6, formatted_text)
                    pdf.ln(4)  # small vertical gap before images
                else:
                    # If no 'operation' key or it's empty, print a placeholder
                    pdf.set_font("Arial", "I", size=6)
                    pdf.cell(0, 8, "(No operation text available)", ln=True)
                    pdf.ln(4)

                # -----------------------------
                # 🔧 CHANGED: image layout logic
                # -----------------------------

                # current_y = pdf.get_y()

                page_width = pdf.w - 2 * pdf.l_margin
                half_width = page_width / 2.0

                IMAGE_TOP_MARGIN = 10
                IMAGE_GAP = 5

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

                parsed_info = screenshot_operation_dict[Placeholder.PARSED_INFO]
                if parsed_info and detector_output_index < len(detector_output):
                    pdf.add_page()
                    bug = detector_output[detector_output_index]
                    text = json.dumps(bug, indent=5)
                    # Add text
                    pdf.set_font("Arial", size=6)
                    line_height = 3  # You can change this value to adjust the line height
                    pdf.multi_cell(0, line_height, text)
                    detector_output_index = detector_output_index + 1

            # Save the temporary PDF
            pdf.output(pdf_filepath)
        return pdf_filepath

    @staticmethod
    def ensure_space_for_image(pdf, image_path, display_width, top_margin=10):
        """
        Ensure there is enough vertical space to render the image.
        If not, start a new page.

        🔧 Used before pdf.image() to prevent image being cut off
        """
        img = FileUtil.load_img(image_path)
        img_w, img_h = img.size

        display_height = display_width * img_h / img_w

        current_y = pdf.get_y()
        page_bottom = pdf.h - pdf.b_margin

        if current_y + top_margin + display_height > page_bottom:
            pdf.add_page()



