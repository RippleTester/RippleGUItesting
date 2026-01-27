import copy
import re
from pathlib import Path

from src.pipelines.placeholder import Placeholder
from config import PROMPT_DIR


class LLMUtil:
    # NO_KNOWLEDGE_BASE_ASSISTANT_ID = "asst_H3veqzbHkGhrmwjuh4ROkb42"
    # NO_KNOWLEDGE_BASE_VECTOR_STORE_ID = "vs_ZbQL6MIdSh8CraHiYiXqqVa5"

    ROLE = 'role'
    ROLE_SYSTEM = 'system'
    ROLE_USER = 'user'
    ROLE_ASSISTANT = 'assistant'
    SESSION_PROMPT = ""

    TEXT_INPUT = """
    {{
        "type": "text",
        "text": {text_value}
    }}
    """

    IMAGE_BASE64_INPUT = """
    {{
        "type": "image_url",
        "image_url": {{
            "url": "data:image/png;base64,{base64_image}",
            "detail": "{img_detail}"
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
        "type": "image_url",
        "image_url": {{
            "url": "data:image/png;base64,{base64_image}",
            "detail": "{img_detail}"
        }}
    }}
]
"""

    QUESTION_WITH_2_IMAGE_BASE64 = """
    [
        {{
            "type": "text",
            "text": 
                {text_value}
        }},
        {{
            "type": "image_url",
            "image_url": {{
                "url": "data:image/png;base64,{base64_image}",
                "detail": "{img_detail}"
            }}
        }},
        {{
            "type": "image_url",
            "image_url": {{
                "url": "data:image/png;base64,{base64_image1}",
                "detail": "{img_detail}"
            }}
        }}
    ]
    """

    @staticmethod
    def add_into_answer(answer, total_cost, duration_mins=None):
        answer_copy = copy.deepcopy(answer)
        answer_copy[Placeholder.COST] = total_cost
        if duration_mins:
            answer_copy[Placeholder.DURATION_MINS] = duration_mins
        return answer_copy

    @staticmethod
    def get_messages(session_prompt=None, qa_pairs=None):
        """
        model="gpt-3.5-turbo",
        Args:
            system_role: for session_prompt,
            question_role: for question,
            answer_role: for answer,
            session_prompt: for system_role introduction
            qa_pairs (examples): (Q, A) pairs

        Returns:
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Who won the world series in 2020?"},
                {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
                {"role": "user", "content": "Where was it played?"}
            ]
        """
        if session_prompt:
            messages = [{'role': LLMUtil.ROLE_SYSTEM, 'content': session_prompt}]
        if qa_pairs:
            for qa in qa_pairs:
                role_content_dict = {'role': LLMUtil.ROLE_USER, 'content': qa[0]}
                messages.append(role_content_dict)
                role_content_dict = {'role': LLMUtil.ROLE_ASSISTANT, 'content': qa[1]}
                messages.append(role_content_dict)
        return messages

    @staticmethod
    def add_role_content_dict_into_messages(role, content, messages):
        if messages is None:
            messages = []
        role_content_dict = {'role': role, 'content': content}
        messages.append(role_content_dict)
        return messages

    @staticmethod
    def show_messages(messages):
        for message in messages:
            # if isinstance(message['content'], dict):
            #     pass
            # else:
            print(f"{message['role']}: {message['content']}")

    @staticmethod
    def get_messages_without_image_encode(messages):
        for message in messages:
            if message['role'] == LLMUtil.ROLE_USER:
                question = message['content']
                message['content'] = LLMUtil.get_question_without_image_encode(question)
        return messages

    @staticmethod
    def get_question_without_image_encode(question):
        question_without_image_encode = []
        for one_dict in question:
            if one_dict['type'] != "image_url":
                question_without_image_encode.append(one_dict)
                # one_dict["image_url"]["url"] = None
            # elif one_dict['type'] == "input_image":
            #     one_dict["image_url"] = None
        return question_without_image_encode

    @staticmethod
    def calculate_tokens(messages):
        question = ''
        answer = ''
        system = ''
        for message in messages:
            if message['role'] == LLMUtil.ROLE_USER:
                question = message['content']
            elif message['role'] == LLMUtil.ROLE_ASSISTANT:
                answer = message['content']
            elif message["role"] == LLMUtil.ROLE_SYSTEM:
                system = message['content']
        question = system + question
        # print("#######test##########")
        # print(question)
        # print(answer)
        # print("#######test##########")
        question_tokens = question.split()
        answer_tokens = answer.split()
        print(f"###len(que_tokens): {len(question_tokens)} len(ans_tokens): {len(answer_tokens)}###")
        return len(question_tokens), len(answer_tokens)

    # @staticmethod
    # def calculate_costs(model_name,
    #                     prompt_tokens, completion_tokens, cached_tokens=None,
    #                     price_per_prompt_token=None, price_per_completion_token=None,
    #                     ):
    #     from code_testing.utils.gpt_util import GPTUtil
    #     model_name = re.sub(r'(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})', '', model_name).strip('-')
    #
    #     if price_per_prompt_token is None or price_per_completion_token is None:
    #         if model_name in [GPTUtil.GPT5[Placeholder.MODEL_NAME]]:
    #             # Define pricing per million tokens
    #             price_per_prompt_token = GPTUtil.GPT5[Placeholder.PRICE_PER_INPUT_TOKEN]
    #             price_per_cache_token = GPTUtil.GPT5[Placeholder.PRICE_PER_CACHED_INPUT_TOKEN]
    #             price_per_completion_token = GPTUtil.GPT5[Placeholder.PRICE_PER_OUTPUT_TOKEN]
    #         elif model_name in [GPTUtil.GPT4_1[Placeholder.MODEL_NAME]]:
    #             # Define pricing per million tokens
    #             price_per_prompt_token = GPTUtil.GPT4_1[Placeholder.PRICE_PER_INPUT_TOKEN]
    #             price_per_completion_token = GPTUtil.GPT4_1[Placeholder.PRICE_PER_OUTPUT_TOKEN]
    #         elif model_name in [GPTUtil.GPT4_1_MINI[Placeholder.MODEL_NAME]]:
    #             price_per_prompt_token = GPTUtil.GPT4_1_MINI[Placeholder.PRICE_PER_INPUT_TOKEN]
    #             price_per_completion_token = GPTUtil.GPT4_1_MINI[Placeholder.PRICE_PER_OUTPUT_TOKEN]
    #         elif model_name in [GPTUtil.O4_MINI[Placeholder.MODEL_NAME]]:
    #             price_per_prompt_token = GPTUtil.O4_MINI[Placeholder.PRICE_PER_INPUT_TOKEN]
    #             price_per_completion_token = GPTUtil.O4_MINI[Placeholder.PRICE_PER_OUTPUT_TOKEN]
    #         elif model_name in [GPTUtil.O3[Placeholder.MODEL_NAME]]:
    #             price_per_prompt_token = GPTUtil.O3[Placeholder.PRICE_PER_INPUT_TOKEN]
    #             price_per_completion_token = GPTUtil.O3[Placeholder.PRICE_PER_OUTPUT_TOKEN]
    #     # elif model_name in [ClaudeUtil.CLAUDE_3_7_SONNET[Placeholder.MODEL_NAME]]:
    #     #     price_per_prompt_token = ClaudeUtil.CLAUDE_3_7_SONNET[Placeholder.PRICE_PER_INPUT_TOKEN]
    #     #     price_per_completion_token = ClaudeUtil.CLAUDE_3_7_SONNET[Placeholder.PRICE_PER_OUTPUT_TOKEN]
    #     # Calculate cost for the prompt tokens
    #     prompt_cost = prompt_tokens * price_per_prompt_token
    #     if cached_tokens:
    #         prompt_tokens = prompt_tokens - cached_tokens
    #         prompt_cost = prompt_tokens * price_per_prompt_token
    #         prompt_cost += cached_tokens * price_per_cache_token
    #     # Calculate cost for the completion tokens
    #     completion_cost = completion_tokens * price_per_completion_token
    #     # Total cost
    #     total_cost = prompt_cost + completion_cost
    #     # print(f"Model: {model_name}\nprice_per_prompt_token: {price_per_prompt_token}\nprice_per_completion_token: {price_per_completion_token}\nInput tokens: {prompt_tokens}\nOutput tokens: {completion_tokens}\nTotal costs: {total_cost} USD")
    #     cost = {
    #         "model": model_name,
    #         "price_per_prompt_token": price_per_prompt_token,
    #         "price_per_completion_token": price_per_completion_token,
    #         "prompt_tokens": prompt_tokens,
    #         "completion_tokens": completion_tokens,
    #         "total_cost": total_cost
    #     }
    #     if cached_tokens:
    #         cost["cached_tokens"] = cached_tokens
    #         cost["price_per_cached_token"] = price_per_cache_token
    #
    #     return cost

    @staticmethod
    def get_instructions(prompt_folder, system_prompt="system"):
        with open(Path(PROMPT_DIR, prompt_folder, system_prompt), "r", encoding="utf-8") as file:
            system_instruction = file.read()
        return system_instruction


