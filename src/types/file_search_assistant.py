import ast
import json

from src.pipelines.format_converter import FormatConverter
from src.pipelines.placeholder import Placeholder
from src.utils.gpt_util import GPTUtil
from src.utils.llm_util import LLMUtil


class FileSearch:
    # @todo https://platform.openai.com/docs/guides/function-calling
    # @todo https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models
    def __init__(self, assistant=None, vector_store=None, thread=None):
        self.assistant = assistant
        self.vector_store = vector_store
        self.thread = thread  # use thread as memory to save conversation

    def initiate(self,
                 assistant_id=None, vector_store_id=None, thread_id=None,
                 assistant_name=None, instructions=None, vector_store_name=None, vector_store_filepath=None,
                 model_name=GPTUtil.GPT4O, temperature=0.2):
        if assistant_id is None:
            assistant, vector_store = GPTUtil.create_assistant(assistant_name=assistant_name,
                                                               instructions=instructions,
                                                               vector_store_id=vector_store_id,
                                                               vector_store_name=vector_store_name,
                                                               vector_store_filepath=str(vector_store_filepath),
                                                               model_name=model_name,
                                                               temperature=temperature
                                                               )
        else:
            assistant = GPTUtil.retrieve_assistant_by_id(assistant_id)
            vector_store = GPTUtil.retrieve_vector_store_by_id(vector_store_id)
        if thread_id is None:
            thread = GPTUtil.create_thread()
        else:
            thread = GPTUtil.retrieve_thread_by_id(thread_id)

        self.assistant = assistant
        self.vector_store = vector_store
        self.thread = thread

    def ask_assistant(self, text_input, img_input_by_filepath=None,
                      # assistant_name=None,
                      assistant_id=None, vector_store_id=None, thread_id=None,
                      assistant_name=None, instructions=None, vector_store_name=None, vector_store_filepath=None,
                      model_name=GPTUtil.GPT4O, temperature=0.2,
                      with_instances=True,
                      ):

        if self.assistant is None:
            self.initiate(assistant_id, vector_store_id, thread_id, assistant_name,
                          instructions=instructions, vector_store_name=vector_store_name,
                          vector_store_filepath=vector_store_filepath,
                          model_name=model_name, temperature=temperature
                          )
        # question = self.question(steps, with_cots)
        # print(question)
        thread_messages = GPTUtil.get_thread_messages(
            self.thread.id,
            text_input, img_input_by_filepath=img_input_by_filepath,
            with_instances=with_instances
        )
        run = GPTUtil.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
        )
        total_cost = LLMUtil.calculate_costs(run.model, run.usage.prompt_tokens, run.usage.completion_tokens)

        messages = list(GPTUtil.client.beta.threads.messages.list(
            thread_id=self.thread.id,
            run_id=run.id))

        GPTUtil.show_thread_messages(self.thread.id)
        # print("*****************************************************")
        # print(messages)
        # print("*****************************************************")
        message_content = messages[0].content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = GPTUtil.client.files.retrieve(file_citation.file_id)

        output = message_content.value
        return output, total_cost

    def process_output(self, output):
        try:
            """
             the input string is not a valid JSON format. 
             The string appears to be a Python dictionary representation, 
             but it's being treated as a JSON string. 
             To fix this issue, Use ast.literal_eval() instead of json.loads():
            """
            try:
                output = ast.literal_eval(output)
            except Exception as e:
                # @todo
                print(f"FileSearch.process_output inner: ast.literal_eval Exception: {e}\n{output}")
                output = json.loads(output)
                pass
        except Exception as e:
            print(f"FileSearch.process_output out: {e}\n{output}")
            pass

        # return current_step, sub_steps, all_steps_completion
        return output

    def search_file(self, text_input, img_input_by_filepath=None, assistant_id=None, vector_store_id=None, thread_id=None,
                    assistant_name=None, instructions=None, vector_store_name=None, vector_store_filepath=None,
                    model_name=GPTUtil.GPT4O, temperature=0.2,
                    with_output_format=False  # if with format, then use FormatConverter
                    ):
        output, cost = self.ask_assistant(text_input, img_input_by_filepath,
                                          assistant_id, vector_store_id, thread_id,
                                          assistant_name, instructions,
                                          vector_store_name, vector_store_filepath,
                                          model_name=model_name, temperature=temperature)
        # print(planner_output)
        if with_output_format:
            # output, _, format_verifier_cost = FormatVerifier.verify_format(output,
            #                                                                with_output_format)
            output, format_converter_cost = FormatConverter.convert_format(output, with_output_format)

        # current_step, sub_steps, steps_completion = self.process_ans(planner_output)
        output = self.process_output(output)

        print(f"************************Cost: {cost}*************************")
        output[Placeholder.COST] = output.get(Placeholder.COST, cost)
        if with_output_format:
            # output[Placeholder.FORMAT_VERIFIER_COST] = output.get(Placeholder.FORMAT_VERIFIER_COST,
            #                                                       format_verifier_cost)
            output[Placeholder.FORMAT_CONVERTER_COST] = output.get(Placeholder.FORMAT_CONVERTER_COST,
                                                                   format_converter_cost)
        output = json.dumps(output)
        # return json.loads(planner_output), current_step, sub_steps, steps_completion
        return json.loads(output)
