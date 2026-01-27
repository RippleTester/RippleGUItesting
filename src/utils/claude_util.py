import copy
import json
import re
from pathlib import Path

import anthropic
import backoff

from src.pipelines.format_converter import FormatConverter
from src.pipelines.placeholder import Placeholder
from src.utils.decorators import timing
from src.utils.llm_util import LLMUtil
from config import PROMPT_DIR


class ClaudeUtil:
    API_KEY = ""

    client = anthropic.Anthropic(api_key=API_KEY)

    # https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching#pricing
    # Premium model combining maximum intelligence with practical performance -> Moderate
    CLAUDE_OPUS_4_5 = {
        Placeholder.MODEL_NAME: "claude-opus-4-5",
        Placeholder.PRICE_PER_INPUT_TOKEN: 5.0 / 1_000_000,  # $3 per 1M prompt tokens (input)
        # Placeholder.PRICE_PER_5M_CACHE_WRITES_TOKEN: 18.75 / 1_000_000,  # https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
        # Placeholder.PRICE_PER_1H_CACHE_WRITES_TOKEN: 30.00 / 1_000_000,  # https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
        # Placeholder.PRICE_PER_CACHE_HITS_REFRESHES_TOKEN: 1.50 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 25.0 / 1_000_000,  # $15 per 1M output tokens (output)
    }

    CLAUDE_OPUS_4_1 = {
        Placeholder.MODEL_NAME: "claude-opus-4-1-20250805",
        Placeholder.PRICE_PER_INPUT_TOKEN: 15.0 / 1_000_000,  # $3 per 1M prompt tokens (input)
        Placeholder.PRICE_PER_5M_CACHE_WRITES_TOKEN: 18.75 / 1_000_000,  # https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
        Placeholder.PRICE_PER_1H_CACHE_WRITES_TOKEN: 30.00 / 1_000_000,  # https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
        Placeholder.PRICE_PER_CACHE_HITS_REFRESHES_TOKEN: 1.50 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 75.0 / 1_000_000,  # $15 per 1M output tokens (output)
    }
    # Our smartest model for complex agents and coding -> Fast
    CLAUDE_SONNET_4_5 = {
        Placeholder.MODEL_NAME: "claude-sonnet-4-5",
        Placeholder.PRICE_PER_INPUT_TOKEN: 3.0 / 1_000_000,  # $3 per 1M prompt tokens (input)
        # Placeholder.PRICE_PER_5M_CACHE_WRITES_TOKEN: 3.75 / 1_000_000,  # https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
        # Placeholder.PRICE_PER_1H_CACHE_WRITES_TOKEN: 6.00 / 1_000_000,  # https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
        # Placeholder.PRICE_PER_CACHE_HITS_REFRESHES_TOKEN: 0.3 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 15.0 / 1_000_000,  # $15 per 1M output tokens (output)
    }

    CLAUDE_SONNET_4 = {
        Placeholder.MODEL_NAME: "claude-sonnet-4-20250514",
        Placeholder.PRICE_PER_INPUT_TOKEN: 3.0 / 1_000_000,  # $3 per 1M prompt tokens (input)
        Placeholder.PRICE_PER_5M_CACHE_WRITES_TOKEN: 3.75 / 1_000_000,  # https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
        Placeholder.PRICE_PER_1H_CACHE_WRITES_TOKEN: 6.00 / 1_000_000,  # https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
        Placeholder.PRICE_PER_CACHE_HITS_REFRESHES_TOKEN: 0.3 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 15.0 / 1_000_000,  # $15 per 1M output tokens (output)
    }
    # Our fastest model with near-frontier intelligence
    CLAUDE_HAIKU_4_5 = {
        Placeholder.MODEL_NAME: "claude-haiku-4-5",
        Placeholder.PRICE_PER_INPUT_TOKEN: 1.0 / 1_000_000,  # $3 per 1M prompt tokens (input)
        # Placeholder.PRICE_PER_5M_CACHE_WRITES_TOKEN: 18.75 / 1_000_000,  # https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
        # Placeholder.PRICE_PER_1H_CACHE_WRITES_TOKEN: 30.00 / 1_000_000,  # https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
        # Placeholder.PRICE_PER_CACHE_HITS_REFRESHES_TOKEN: 1.50 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 5.0 / 1_000_000,  # $15 per 1M output tokens (output)
    }

    TOOL_USE_INPUT = """
    {{
        "type": "tool_result",
        "tool_use_id": "{tool_use_id}"
    }}
    """

    TEXT_INPUT = """
    {{
        "type": "text",
        "text": {text_value}
    }}
    """

    IMAGE_BASE64_INPUT = """
    {{
        "type": "image",
        "source": {{
            "type": "base64",
            "media_type": "{image1_media_type}",
            "data": "{image1_data}"
        }}
    }}
    """

    QUESTION_WITH_IMAGE_BASE64 = """
[
    {{
        "type": "text",
        "text": {text_value}
    }},
    {{
        "type": "image",
        "source": {{
            "type": "base64",
            "media_type": "{image1_media_type}",
            "data": "{image1_data}",
        }}
    }}
]
"""

    @staticmethod
    @backoff.on_exception(backoff.expo,
                          (
                                  anthropic.RateLimitError,
                                  anthropic.InternalServerError,
                                  anthropic.APIConnectionError,
                                  anthropic.APITimeoutError,
                                  anthropic.APIStatusError,  # filtered by giveup()
                          ), max_tries=5)
    @timing
    def chat_completions(messages,  # without system_instruction
                         system_instruction=[],
                         tools=None,
                         model=CLAUDE_SONNET_4[Placeholder.MODEL_NAME],
                         max_tokens=12800,
                         beta=False
                         ):
        # @todo extended thinking https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/extended-thinking-tips
        # @todo Prompt caching https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
        # Extract the content of the first message with role "system"
        # system_instruction = next((msg['content'] for msg in messages if msg.get("role") == "system"), None)
        # # print(system_instruction)  # Output: System instructions
        # # Filter out messages with role "system"
        # messages = [msg for msg in messages if msg.get(LLMUtil.ROLE) != LLMUtil.ROLE_SYSTEM]

        if tools is None:
            tools = []
        model_name = model[Placeholder.MODEL_NAME]
        if beta:
            # computer use
            response = ClaudeUtil.client.beta.messages.create(
                system=system_instruction,
                model=model_name,
                max_tokens=max_tokens,
                messages=messages,
                tools=tools,
            )
        else:
            response = ClaudeUtil.client.messages.create(
                system=system_instruction,
                model=model_name,
                max_tokens=max_tokens,
                messages=messages,
                tools=tools,
            )
        total_cost = ClaudeUtil.calculate_cost(response)
        return response, total_cost

    @staticmethod
    def calculate_cost(response):
        # @todo cache prompt, extended thinking, tool use developed by claude
        model_name = response.model
        # Clean the model name by removing date substrings and extraneous hyphens
        cleaned_model_name = re.sub(r'(\d{8}|\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})', '', model_name ).strip('-')
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        # cache_creation_input_tokens = response.usage.cache_creation_input_tokens
        # cache_read_input_tokens = response.usage.cache_read_input_tokens
        if cleaned_model_name in [ClaudeUtil.CLAUDE_SONNET_4_5[Placeholder.MODEL_NAME], ]:
            model_dict = ClaudeUtil.CLAUDE_SONNET_4_5
        elif cleaned_model_name in [ClaudeUtil.CLAUDE_OPUS_4_5[Placeholder.MODEL_NAME], ]:
            model_dict = ClaudeUtil.CLAUDE_OPUS_4_5
        elif cleaned_model_name in [ClaudeUtil.CLAUDE_HAIKU_4_5[Placeholder.MODEL_NAME], ]:
            model_dict = ClaudeUtil.CLAUDE_HAIKU_4_5
        elif cleaned_model_name in [ClaudeUtil.CLAUDE_OPUS_4_1[Placeholder.MODEL_NAME], ]:
            model_dict = ClaudeUtil.CLAUDE_OPUS_4_1
        elif cleaned_model_name in [ClaudeUtil.CLAUDE_SONNET_4[Placeholder.MODEL_NAME]]:
            model_dict = ClaudeUtil.CLAUDE_SONNET_4
        else:
            raise ValueError(f"Model '{model_name} ({cleaned_model_name})' not recognized for cost calculation")
        prize_per_input_token = model_dict[Placeholder.PRICE_PER_INPUT_TOKEN]
        prize_per_output_token = model_dict[Placeholder.PRICE_PER_OUTPUT_TOKEN]

        total_cost = {Placeholder.TOTAL_COST: input_tokens * prize_per_input_token + output_tokens * prize_per_output_token}
        response_usage_dict = json.loads(response.usage.model_dump_json())
        # print(response_usage_dict)
        # print(model_dict)
        cost_dict = model_dict | response_usage_dict | total_cost
        # print(cost_dict)
        return cost_dict

    @staticmethod
    def get_messages_without_image_encode(messages):
        for message in messages:
            if message['role'] == LLMUtil.ROLE_USER:
                question = message['content']
                message['content'] = ClaudeUtil.get_question_without_image_encode(question)
        return messages

    @staticmethod
    def get_question_without_image_encode(question):
        question_without_image_encode = []
        for one_dict in question:
            if one_dict['type'] != "image":
                question_without_image_encode.append(one_dict)
                # one_dict["source"]["data"] = None
        return question_without_image_encode

    @staticmethod
    def get_instructions(prompt_folder, system_prompt="system"):
        with open(Path(PROMPT_DIR, prompt_folder, system_prompt), "r", encoding="utf-8") as file:
            system_instruction = file.read()
        # qa_pairs = None
        # messages = LLMUtil.get_messages(system_instruction, qa_pairs)
        return system_instruction

    @staticmethod
    def question(text_value=None,
                 base64_images=None,
                 tool_use_id=None):
        question = []
        if tool_use_id is not None:
            tool_use_input = ClaudeUtil.TOOL_USE_INPUT.format(tool_use_id=tool_use_id)
            # print(tool_use_input)
            tool_use_input = json.loads(tool_use_input)
            question.append(tool_use_input)
        if text_value:
            text_value = f"{text_value}"  # make sure that text_value is a string,
            text_value = json.dumps(text_value)  # because if text_value is a dict, then this step converts it into string
            text_input = ClaudeUtil.TEXT_INPUT.format(text_value=text_value)
            text_input = json.loads(text_input)  # because if text_value is a dict, then this converts it back to dict
            question.append(text_input)
            # print(text_input)
        if base64_images:
            if not isinstance(base64_images, list):
                base64_images = [base64_images]  # convert single string to list
            for image_input in base64_images:
                if image_input:
                    image_input = ClaudeUtil.IMAGE_BASE64_INPUT.format(image1_media_type='image/png', image1_data=image_input)
                    image_input = json.loads(image_input)
                    question.append(image_input)
        question = json.dumps(question)
        return json.loads(question)

    @staticmethod
    def ask_claude(text_input, image_input=None, system_instructions=None,
                   tools=None, tool_use_id=None, model=CLAUDE_SONNET_4, messages=None, ):
        # copy from Executor.play
        question = ClaudeUtil.question(text_value=text_input, base64_images=image_input, tool_use_id=tool_use_id)
        messages = LLMUtil.add_role_content_dict_into_messages(LLMUtil.ROLE_USER, question, messages)
        response, cost = ClaudeUtil.chat_completions(messages=messages, system_instruction=system_instructions,
                                                     tools=tools, model=model)
        # 先把字符串转成对象
        obj = json.loads(response.model_dump_json())
        # 再格式化输出
        # print(json.dumps(obj, indent=4, ensure_ascii=False))

        answer, tool_use_id, tool_name = ClaudeUtil.process_response(response)
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
        # messages_copy = ClaudeUtil.get_messages_without_image_encode(messages_copy)
        # LLMUtil.show_messages(messages_copy)

        answer = LLMUtil.add_into_answer(answer, cost)

        return answer, messages, tool_use_id, tool_name

    @staticmethod
    def process_response(response):
        # 尝试在response.content里找type=tool_use的块
        tool_use_block = next(
            (b for b in response.content
             if (isinstance(b, dict) and b.get("type") == "tool_use") or
             (hasattr(b, "type") and getattr(b, "type") == "tool_use")),
            None
        )
        if tool_use_block:
            # 兼容dict和object
            if isinstance(tool_use_block, dict):
                answer = tool_use_block.get("input")
                tool_use_id = tool_use_block.get("id")
                tool_name = tool_use_block.get("name")
            else:
                answer = getattr(tool_use_block, "input", None)
                tool_use_id = getattr(tool_use_block, "id", None)
                tool_name = getattr(tool_use_block, "name", None)
        else:
            # 默认取第一块的text
            first_block = response.content[0]
            if isinstance(first_block, dict):
                answer = first_block.get("text")
            else:
                answer = getattr(first_block, "text", None)
            tool_use_id = None
            tool_name = None
        return answer, tool_use_id, tool_name

    @staticmethod
    def validate_anthropic_messages(messages):
        for i, msg in enumerate(messages):
            # if not isinstance(msg["content"], list):
            #     raise ValueError(f"messages[{i}].content not list")
            for j, block in enumerate(msg["content"]):
                if not isinstance(block, dict) or "type" not in block:
                    print(msg)
                    raise ValueError(f"messages[{i}].content[{j}] miss type: {block}")

