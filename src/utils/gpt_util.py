import json
import re
from pathlib import Path

import openai
import backoff
from openai import OpenAI

from src.pipelines.placeholder import Placeholder
from src.utils.decorators import timing
from src.utils.llm_util import LLMUtil
import requests
from io import BytesIO

from config import PROMPT_DIR, DATA_DIR, ROOT_DIR, APP_NAME_FIREFOX


class GPTUtil:

    OPENAI_API_KEY = ""
    OPENAI_API_KEY_PERSONAL = ""
    # VECTOR_STORE_FILE = Path(DATA_DIR, "vector_store_ids.json")

    client = OpenAI(api_key=OPENAI_API_KEY_PERSONAL)
    client_personal = OpenAI(api_key=OPENAI_API_KEY_PERSONAL)

    client_gpt_oss_20b = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

    COMPUTER_USE_PREVIEW = {
        Placeholder.MODEL_NAME: "computer-use-preview",
        Placeholder.PRICE_PER_INPUT_TOKEN: 3.00 / 1_000_000,
        Placeholder.PRICE_PER_CACHED_INPUT_TOKEN: 0.00 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 12.00 / 1_000_000,
    }

    O3 = {
        # most powerful reasoning model
        # https://openai.com/index/thinking-with-images/
        # OpenAI o3 and o4-mini are the latest visual reasoning models in our o-series.
        # For the first time, our models can think with images in their chain-of-thought—not just see them,
        # which is achieved by transforming user uploaded images with tools,
        # allowing them to crop, zoom in, and rotate, in addition to other simple image processing techniques.
        # More importantly, these capabilities come natively, without relying on separate specialized models.
        Placeholder.MODEL_NAME: "o3",
        Placeholder.PRICE_PER_INPUT_TOKEN: 2.00 / 1_000_000,
        Placeholder.PRICE_PER_CACHED_INPUT_TOKEN: 0.50 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 8.00 / 1_000_000,
    }

    O4_MINI = {
        # Faster, more affordable reasoning model, text and image
        # https://openai.com/index/thinking-with-images/
        # OpenAI o3 and o4-mini are the latest visual reasoning models in our o-series.
        # For the first time, our models can think with images in their chain-of-thought—not just see them,
        # which is achieved by transforming user uploaded images with tools,
        # allowing them to crop, zoom in, and rotate, in addition to other simple image processing techniques.
        # More importantly, these capabilities come natively, without relying on separate specialized models.
        Placeholder.MODEL_NAME: "o4-mini",
        Placeholder.PRICE_PER_INPUT_TOKEN: 1.10 / 1_000_000,
        Placeholder.PRICE_PER_CACHED_INPUT_TOKEN: 0.275 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 4.40 / 1_000_000,
    }

    GPT5_2 = {
        # GPT-5.1 is our flagship model for coding, reasoning, and agentic tasks across domains.
        Placeholder.MODEL_NAME: "gpt-5.2",
        Placeholder.PRICE_PER_INPUT_TOKEN: 1.75 / 1_000_000,
        Placeholder.PRICE_PER_CACHED_INPUT_TOKEN: 0.175 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 14.00 / 1_000_000,
    }

    GPT5_1 = {
        # GPT-5.1 is our flagship model for coding, reasoning, and agentic tasks across domains.
        Placeholder.MODEL_NAME: "gpt-5.1",
        Placeholder.PRICE_PER_INPUT_TOKEN: 1.25 / 1_000_000,
        Placeholder.PRICE_PER_CACHED_INPUT_TOKEN: 0.125 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 10.00 / 1_000_000,
    }

    GPT5 = {
        # GPT-5 is our flagship model for coding, reasoning, and agentic tasks across domains.
        Placeholder.MODEL_NAME: "gpt-5",
        Placeholder.PRICE_PER_INPUT_TOKEN: 1.25 / 1_000_000,
        Placeholder.PRICE_PER_CACHED_INPUT_TOKEN: 0.125 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 10.00 / 1_000_000,
    }

    GPT5_CHAT = {
        # GPT-5 is our flagship model for coding, reasoning, and agentic tasks across domains.
        Placeholder.MODEL_NAME: "gpt-5-chat-latest",
        Placeholder.PRICE_PER_INPUT_TOKEN: 1.25 / 1_000_000,
        Placeholder.PRICE_PER_CACHED_INPUT_TOKEN: 0.125 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 10.00 / 1_000_000,
    }

    GPT5_MINI = {
        # GPT-5 is our flagship model for coding, reasoning, and agentic tasks across domains.
        Placeholder.MODEL_NAME: "gpt-5-mini",
        Placeholder.PRICE_PER_INPUT_TOKEN: 0.25 / 1_000_000,
        Placeholder.PRICE_PER_CACHED_INPUT_TOKEN: 0.025 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 2.00 / 1_000_000,
    }

    GPT5_NANO = {
        # GPT-5 is our flagship model for coding, reasoning, and agentic tasks across domains.
        Placeholder.MODEL_NAME: "gpt-5-nano",
        Placeholder.PRICE_PER_INPUT_TOKEN: 0.05 / 1_000_000,
        Placeholder.PRICE_PER_CACHED_INPUT_TOKEN: 0.005 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 0.40 / 1_000_000,
    }

    GPT4_1 = {
        # flagship model for complex tasks. It is well suited for problem solving across domains.
        Placeholder.MODEL_NAME: "gpt-4.1",
        Placeholder.PRICE_PER_INPUT_TOKEN: 2.00 / 1_000_000,
        Placeholder.PRICE_PER_CACHED_INPUT_TOKEN: 0.50 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 8.00 / 1_000_000,
    }

    GPT4_1_MINI = {
        # Balanced for intelligence, speed, and cost
        Placeholder.MODEL_NAME: "gpt-4.1-mini",
        Placeholder.PRICE_PER_INPUT_TOKEN: 0.40/1_000_000,
        Placeholder.PRICE_PER_CACHED_INPUT_TOKEN: 0.10 / 1_000_000,
        Placeholder.PRICE_PER_OUTPUT_TOKEN: 1.60/1_000_000,
    }

    FILE_SEARCH_TOOL = """
    {{
        "type": "file_search",
        "vector_store_ids": {vector_store_ids}
    }}
    """

    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"

    # SESSION_PROMPT = ""
    # CHAT_LOG = None
    # CHAIN_OF_THOUGHTS = 'CHAIN_OF_THOUGHTS'

    TEXT_INPUT = """
    {{
        "type": "input_text",
        "text": {text_value}
    }}
    """

    IMAGE_BASE64_INPUT = """
    {{
        "type": "input_image",
        "image_url": "data:image/png;base64,{base64_image}"
    }}
    """

    TEXT_INPUT_FOR_COMPLETION = """
    {{
        "type": "text",
        "text": {text_value}
    }}
    """

    IMAGE_BASE64_INPUT_FOR_COMPLETION = """
    {{
        "type": "image_url",
        "image_url": {{"url": "data:image/png;base64,{base64_image}"}}
    }}
    """

    @staticmethod
    def get_text_input(text_input, with_response=True):
        """
        chat.completion -> GPTUtil.TEXT_INPUT_FOR_COMPLETION
        response -> GPTUtil.TEXT_INPUT
        """
        text_template = GPTUtil.TEXT_INPUT
        if not with_response:
            text_template = GPTUtil.TEXT_INPUT_FOR_COMPLETION
        text_input = json.dumps(str(text_input))  # strip the surrounding quotes from json.dumps
        text_input = text_template.format(text_value=text_input)
        text_input.strip()  # This is now a valid JSON string
        # Convert to a Python dict
        text_input = json.loads(text_input)
        return text_input

    @staticmethod
    def get_image_base64_input(base64_image, with_response=True):
        """
        chat.completion -> GPTUtil.IMAGE_BASE64_INPUT_FOR_COMPLETION
        response -> GPTUtil.IMAGE_BASE64_INPUT
        """
        image_template = GPTUtil.IMAGE_BASE64_INPUT
        if not with_response:
            image_template = GPTUtil.IMAGE_BASE64_INPUT_FOR_COMPLETION
        image_input = image_template.format(base64_image=base64_image)
        image_input = json.loads(image_input)
        return image_input

    # @staticmethod
    # def get_text_input(text_input):
    #     text_input = json.dumps(str(text_input))  # strip the surrounding quotes from json.dumps
    #     text_input = GPTUtil.TEXT_INPUT.format(text_value=text_input)
    #     text_input.strip()  # This is now a valid JSON string
    #     # Convert to a Python dict
    #     text_input = json.loads(text_input)
    #     return text_input
    #
    # @staticmethod
    # def get_image_base64_input(base64_image):
    #     image_input = GPTUtil.IMAGE_BASE64_INPUT.format(base64_image=base64_image)
    #     image_input = json.loads(image_input)
    #     return image_input

    @staticmethod
    def get_response_outputs(response):
        """
        从 response 对象中提取所有 output_text 内容。
        返回一个列表，每个元素是 parsed JSON 或原始 text。
        """
        response_dict = json.loads(response.model_dump_json())
        results = []
        for item in response_dict.get("output", []):
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        results.append(content.get("parsed") or json.loads(content["text"]))
        return results

    @staticmethod
    def calculate_cost(response):
        model_name = response.model
        if response.object == "chat.completion":
            cached_input_tokens = response.usage.prompt_tokens_details.cached_tokens
            uncached_input_tokens = response.usage.prompt_tokens - cached_input_tokens
            output_tokens = response.usage.completion_tokens
        else:
            if type(response.usage.input_tokens_details) is dict:
                cached_input_tokens = response.usage.input_tokens_details["cached_tokens"]
            else:
                cached_input_tokens = response.usage.input_tokens_details.cached_tokens
            uncached_input_tokens = response.usage.input_tokens - cached_input_tokens
            output_tokens = response.usage.output_tokens
        # Clean the model name by removing date substrings and extraneous hyphens
        cleaned_model_name = re.sub(
            r'(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})', '', model_name
        ).strip('-')

        # Determine pricing based on the cleaned model name
        if cleaned_model_name in [GPTUtil.GPT5_2[Placeholder.MODEL_NAME]]:
            model_dict = GPTUtil.GPT5_2
        elif cleaned_model_name in [GPTUtil.GPT5_1[Placeholder.MODEL_NAME]]:
            model_dict = GPTUtil.GPT5_1
        elif cleaned_model_name in [GPTUtil.GPT5[Placeholder.MODEL_NAME], GPTUtil.GPT5_CHAT[Placeholder.MODEL_NAME],]:
            model_dict = GPTUtil.GPT5
        elif cleaned_model_name in [GPTUtil.GPT5_MINI[Placeholder.MODEL_NAME],]:
            model_dict = GPTUtil.GPT5_MINI
        elif cleaned_model_name in [GPTUtil.GPT5_NANO[Placeholder.MODEL_NAME],]:
            model_dict = GPTUtil.GPT5_NANO
        elif cleaned_model_name in [GPTUtil.GPT4_1[Placeholder.MODEL_NAME]]:
            model_dict = GPTUtil.GPT4_1
        elif cleaned_model_name in [GPTUtil.GPT4_1_MINI[Placeholder.MODEL_NAME]]:
            model_dict = GPTUtil.GPT4_1_MINI
        elif cleaned_model_name in [GPTUtil.O4_MINI[Placeholder.MODEL_NAME]]:
            model_dict = GPTUtil.O4_MINI
        elif cleaned_model_name in [GPTUtil.O3[Placeholder.MODEL_NAME]]:
            model_dict = GPTUtil.O3
        elif cleaned_model_name in [GPTUtil.COMPUTER_USE_PREVIEW[Placeholder.MODEL_NAME]]:
            model_dict = GPTUtil.COMPUTER_USE_PREVIEW
        else:
            raise ValueError(f"Model '{cleaned_model_name}' not recognized for cost calculation")

        price_per_prompt_token = model_dict[Placeholder.PRICE_PER_INPUT_TOKEN]
        price_per_completion_token = model_dict[Placeholder.PRICE_PER_OUTPUT_TOKEN]
        price_per_cached_input_token = model_dict[Placeholder.PRICE_PER_CACHED_INPUT_TOKEN]

        # Calculate costs:
        prompt_cost = (uncached_input_tokens * price_per_prompt_token) + \
                      (cached_input_tokens * price_per_cached_input_token)
        completion_cost = output_tokens * price_per_completion_token
        total_cost = prompt_cost + completion_cost

        response_usage_dict = json.loads(response.usage.model_dump_json())
        total_cost = {Placeholder.TOTAL_COST: total_cost}
        cost_dict = model_dict | response_usage_dict | total_cost
        return cost_dict

    # https://platform.openai.com/docs/guides/tools-file-search
    # ######### File Search #################################################################################
    @staticmethod
    def create_file(file_path):
        """
        Upload the file to the File API
        <= 8MB
        """
        if file_path.startswith("http://") or file_path.startswith("https://"):
            # Download the file content from the URL
            response = requests.get(file_path)
            file_content = BytesIO(response.content)
            file_name = file_path.split("/")[-1]
            file_tuple = (file_name, file_content)
            result = GPTUtil.client.files.create(
                file=file_tuple,
                purpose="assistants"
            )
        else:
            # Handle local file path
            with open(file_path, "rb") as file_content:
                result = GPTUtil.client.files.create(
                    file=file_content,
                    purpose="assistants"
                )
        print(f"File id: {result.id}")
        return result.id

    @staticmethod
    def create_vector_store_by_name(vector_store_name):
        vector_store = GPTUtil.client.vector_stores.create(
            name=vector_store_name
        )
        print(f"Vector store id: {vector_store.id}")
        return vector_store.id

    @staticmethod
    def add_file_to_vector_store(vector_store_id, file_id):
        result = GPTUtil.client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_id
        )
        print(result)
        status = result.status
        # while status != 'completed' or status != 'failed':
        while status == 'in_progress':
            result = GPTUtil.client.vector_stores.files.list(
                vector_store_id=vector_store_id
            )
            # print(result)
            if result.data:
                status = result.data[0].status
        print(result)

    @staticmethod
    def create_vector_store(filepaths, vector_store_name):
        """
        创建或复用 vector store：
        - 如果本地记录里已经有同名的 vector_store_id，就直接返回它
        - 否则新建并存到本地记录
        """
        # 1. 先查缓存
        stores = GPTUtil.load_vector_stores()
        if vector_store_name in stores:
            print(f"Vector store '{vector_store_name}' exists: {stores[vector_store_name]}")
            return stores[vector_store_name]

        # 2. 没有则创建
        vector_store_id = GPTUtil.create_vector_store_by_name(vector_store_name)
        for filepath in filepaths:
            file_id = GPTUtil.create_file(filepath)
            GPTUtil.add_file_to_vector_store(vector_store_id, file_id)
        print(f"vector_store_id: {vector_store_id}")

        # 3. 保存到本地文件
        stores[vector_store_name] = vector_store_id
        GPTUtil.save_vector_stores(stores)

        return vector_store_id

    @staticmethod
    def search_file(input_content, output_format=None, previous_response_id=None, system_instructions=None,
                    vector_store_ids=None, max_num_results=20, include_search_results=None, metadata_filter=None,
                    model=GPT4_1_MINI):
        """
        @todo https://platform.openai.com/docs/guides/tools-file-search#metadata-filtering
        @todo https://platform.openai.com/docs/guides/retrieval
        @todo https://platform.openai.com/docs/guides/retrieval#attribute-filtering
        @todo set attributes on vector store files
        "filters": {
            "type": "eq",
            "key": "type",
            "value": "blog"
        }
        """
        if vector_store_ids is None:
            vector_store_ids = []
        file_search_tool = {
                "type": "file_search",
                "vector_store_ids": vector_store_ids,
                "max_num_results": max_num_results
            }
        tools = [file_search_tool, ]
        if include_search_results:
            include_search_results = ["file_search_call.results"]
        response, cost = GPTUtil.parse_response(input_content, output_format, previous_response_id, system_instructions,
                                           tools, include_search_results,
                                           model)
        return response, cost

    @staticmethod
    def load_vector_stores(reponame):
        vector_store_filepath = Path(DATA_DIR, reponame, "vector_store_ids.json")
        if vector_store_filepath.exists():
            vector_stores = json.loads(vector_store_filepath.read_text(encoding="utf-8"))
            return vector_stores
        return {}

    @staticmethod
    def save_vector_stores(data, reponame):
        vector_store_filepath = Path(DATA_DIR, reponame, "vector_store_ids.json")
        vector_store_filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def delete_vector_store_file(reponame):
        vector_store_filepath = Path(DATA_DIR, reponame, "vector_store_ids.json")

        if vector_store_filepath.exists():
            vector_store_filepath.unlink()
            print("Deleted:", vector_store_filepath)
        else:
            print("File does not exist:", vector_store_filepath)

    # https://platform.openai.com/docs/api-reference/responses
    ################################## responses ###############################################################
    @staticmethod
    def get_instructions(prompt_folder, system_prompt="system_gpt"):
        with open(Path(PROMPT_DIR, prompt_folder, system_prompt), "r", encoding="utf-8") as file:
            system_instruction = file.read()
        return system_instruction

    @staticmethod
    @backoff.on_exception(backoff.expo,(
        openai.RateLimitError,
        openai.InternalServerError,
        openai.APIConnectionError,
        openai.APITimeoutError,
        openai.APIError,), max_tries=5)
    @timing
    def create_response(input_content, output_format=None, previous_response_id=None, system_instructions=None,
                        tools=None, include=None,
                        model=GPT5):
        if tools is None:
            tools = []
        model_name = model[Placeholder.MODEL_NAME]
        response = GPTUtil.client.responses.create(
            model=model_name,
            instructions=system_instructions,
            tools=tools,
            include=include,
            input=input_content,
            # text={
            #     "type": "json_schema",
            #     "json_schema": output_format.model_json_schema(by_alias=True)
            # }
            # text_format=output_format,
            previous_response_id=previous_response_id,
            # stream=True,
        )
        cost = GPTUtil.calculate_cost(response)
        return response, cost

    @staticmethod
    @backoff.on_exception(backoff.expo,(
        openai.RateLimitError,
        openai.InternalServerError,
        openai.APIConnectionError,
        openai.APITimeoutError,
        openai.APIError,), max_tries=5)
    @timing
    def parse_response(input_content, output_format=None, previous_response_id=None, system_instructions=None,
                       tools=None, include=None,
                       model=GPT5, reasoning='medium'):
        if tools is None:
            tools = []
        model_name = model[Placeholder.MODEL_NAME]
        # @todo might be remove oneday
        client = GPTUtil.client
        if model_name == GPTUtil.GPT5[Placeholder.MODEL_NAME]:
            client = GPTUtil.client_personal

        response = client.responses.parse(
            model=model_name,
            instructions=system_instructions,
            tools=tools,
            include=include,
            input=input_content,
            # text=output_format,
            text_format=output_format,
            previous_response_id=previous_response_id,
            reasoning={"effort": reasoning}
            # stream=True,
        )
        cost = GPTUtil.calculate_cost(response)
        return response, cost

    @staticmethod
    def extract_tool_invocations_from_response(response):
        """
        from OpenAI Responses extract tool invocation and file citation
        Return:
          {
            "tool_calls": [
              {
                "id": "...",
                "tool": "file_search",
                "queries": [...],
                "status": "completed",
                "results": [...]/None
              },
              ...
            ],
            "file_citations": [
              {
                "file_id": "...",
                "filename": "file_contents.json",
                "index": 123
              },
              ...
            ],
            "parallel_tool_calls": <bool or None>
          }
        """
        raw = json.loads(response.model_dump_json())
        tool_calls = []
        file_citations = []

        for item in raw.get("output", []):
            t = item.get("type")

            # 1) file_search
            if t == "file_search_call":
                tool_calls.append({
                    "id": item.get("id"),
                    "tool": "file_search",
                    "queries": item.get("queries") or [],
                    "status": item.get("status"),
                    # only when include=["file_search_call.results"]
                    "results": item.get("results"),
                })

            # 2) from message extract（file_citation）
            if t == "message":
                for part in item.get("content", []):
                    for ann in part.get("annotations", []):
                        if ann.get("type") == "file_citation":
                            file_citations.append({
                                "file_id": ann.get("file_id"),
                                "filename": ann.get("filename"),
                                "index": ann.get("index"),
                            })

        return {
            "tool_calls": tool_calls,
            "file_citations": file_citations,
            "parallel_tool_calls": raw.get("parallel_tool_calls"),
        }

    # https://platform.openai.com/docs/guides/responses-vs-chat-completions
    ################################## chat completions ###############################################################

    @staticmethod
    @backoff.on_exception(backoff.expo,(
        openai.RateLimitError,
        openai.InternalServerError,
        openai.APIConnectionError,
        openai.APITimeoutError,
        openai.APIError,), max_tries=5)
    @timing
    def chat_completions_by_structured_outputs(messages, response_format, model=GPT5,
                                               # reasoning='medium',
                                               temperature=1):
        model_name = model[Placeholder.MODEL_NAME]
        # @todo might be remove oneday
        # @todo reasoning
        client = GPTUtil.client
        if model_name == GPTUtil.GPT5[Placeholder.MODEL_NAME]:
            client = GPTUtil.client_personal
        completion = client.beta.chat.completions.parse(
            model=model_name,
            # seed=1,
            messages=messages,
            # temperature=temperature,
            # https://platform.openai.com/docs/guides/structured-outputs
            response_format=response_format,
            # reasoning_effort=reasoning,
        )
        total_cost = GPTUtil.calculate_cost(completion)
        return completion, total_cost

    @staticmethod
    @backoff.on_exception(backoff.expo, openai.RateLimitError)
    def chat_completions_by_json_mode(messages, model=GPT4_1, temperature=1):
        """
        ask LLM question
        Args:
            temperature (): number Optional Defaults to 1
                            What sampling temperature to use, between 0 and 2.
                            Higher values like 0.8 will make the output more random,
                            while lower values like 0.2 will make it more focused and deterministic.
                            We generally recommend altering this or top_p but not both.
            model ():
            messages ():

        Returns: answer

        """
        model = model[Placeholder.MODEL_NAME]
        response = GPTUtil.client.chat.completions.create(
            model=model,
            # seed=1,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        total_cost = LLMUtil.calculate_costs(response.model,
                                             response.usage.prompt_tokens,
                                             response.usage.completion_tokens)
        answer = response.choices[0].message.content
        return answer, total_cost

    @staticmethod
    @backoff.on_exception(backoff.expo, openai.RateLimitError)
    def embedding(texts, model=TEXT_EMBEDDING_3_LARGE):
        """
        # Example texts
        input: texts = ["example text 1", "example text 2"]
        return embeddings = [embedding1, embedding2]
        """
        response = GPTUtil.client.embeddings.create(input=texts, model=model).data
        embeddings = []
        for one_embedding in response:
            embeddings.append(one_embedding.embedding)
        return embeddings

    @staticmethod
    def get_messages_without_image_encode(messages):
        for message in messages:
            if message['role'] == LLMUtil.ROLE_USER:
                question = message['content']
                message['content'] = GPTUtil.get_question_without_image_encode(question)
        return messages

    @staticmethod
    def get_question_without_image_encode(question):
        for one_dict in question:
            if one_dict['type'] == "image_url":
                one_dict["image_url"]["url"] = None
        return question
