import json
import re
from datetime import datetime
from pathlib import Path

from src.pipelines.enhancement_tool import EnhancementTool, PathEnhancementOutput, DataEnhancementOutput
from src.pipelines.generation_tool import GenerationTool
from src.pipelines.placeholder import Placeholder
from src.utils.file_util import FileUtil
from src.utils.gpt_util import GPTUtil
from config import APP_NAME_FIREFOX


class Generator:

    def __init__(self):
        pass

    @staticmethod
    def generate_test_scenarios(bug, with_change_desc=True, with_change_intent=True,
                                with_file_content=False,
                                with_relevant_scenarios=False,
                                model=GPTUtil.GPT5,
                                with_path_enhancement=True,
                                with_path_file_search=False,
                                with_data_enhancement=True,
                                output_filepath=None,
                                reponame=APP_NAME_FIREFOX):
        build_info = bug.get_info_for_testing(reponame)
        print(build_info)
        # commits = bug.commits[1:]
        commits = bug.commits
        input_content = GenerationTool.get_input_from_commits(commits, with_change_desc, with_change_intent,
                                                         # with_file_content,
                                                         with_relevant_scenarios,
                                                         # with_cochange_file_content,
                                                         reponame=reponame
                                                         )
        generator_output, generator_messages = GenerationTool.generate(input_content, model=model,
                                                                  vector_store_ids=with_file_content,
                                                                  build_info=build_info,)

        FileUtil.dump_json(Path(output_filepath, f"{Placeholder.GENERATOR}.json"), generator_messages)

        if with_path_enhancement or with_data_enhancement:
            generator_output_next_input = {k: v for k, v in generator_output.items() if k not in {Placeholder.COST,
                                                                                       Placeholder.DURATION_MINS,
                                                                                       Placeholder.INFO,
                                                                                       Placeholder.TOOL,
                                                                                       Placeholder.CODE_CHANGES_EXPLANATION,
                                                                                       Placeholder.RESPONSE_ID
                                                                                       }}
        # Path enhancement##########################################################################################
        path_enhancer_output = None

        if with_path_enhancement:
            path_file_search_vector_store_ids = []
            if with_path_file_search:
                path_file_search_vector_store_ids = Generator.get_knowledge_base_vector_store_ids(bug, reponame)
            path_enhancer_output, path_enhancer_messages = EnhancementTool.enhance(generator_output_next_input,
                                                                                   prompt_folder=Placeholder.ENHANCER,
                                                                                   system_prompt=f"{Placeholder.SYSTEM}_path",
                                                                                   output_format=PathEnhancementOutput,
                                                                                   vector_store_ids=path_file_search_vector_store_ids,
                                                                                   model=model,
                                                                                   build_info=build_info, )
            FileUtil.dump_json(Path(output_filepath, f"{Placeholder.PATH_ENHANCER}.json"), path_enhancer_messages)
            if with_data_enhancement:
                path_enhancer_output_next_input = {k: v for k, v in path_enhancer_output.items() if k not in {Placeholder.COST,
                                                                                                   Placeholder.DURATION_MINS,
                                                                                                   Placeholder.INFO,
                                                                                                   Placeholder.TOOL,
                                                                                                   Placeholder.STEP_DIVERSITY_ANALYSIS,
                                                                                                   Placeholder.SEARCH_QUERY_GENERATION,
                                                                                                   Placeholder.RESPONSE_ID
                                                                                                   }}

        # Data enhancement##########################################################################################
        data_enhancer_output = None
        if with_data_enhancement:
            data_enhancer_input = generator_output_next_input
            if with_path_enhancement:
                data_enhancer_input = path_enhancer_output_next_input
            data_enhancer_output, data_enhancer_messages = EnhancementTool.enhance(data_enhancer_input,
                                                                                   prompt_folder=Placeholder.ENHANCER,
                                                                                   system_prompt=f"{Placeholder.SYSTEM}_data",
                                                                                   output_format=DataEnhancementOutput,
                                                                                   # vector_store_ids=[bugs_vector_store_id],
                                                                                   vector_store_ids=None,
                                                                                   tools=[],
                                                                                   model=model,
                                                                                   build_info=build_info, )
            FileUtil.dump_json(Path(output_filepath, f"{Placeholder.DATA_ENHANCER}.json"), data_enhancer_messages)

        if with_data_enhancement:
            return generator_messages, data_enhancer_output
        elif with_path_enhancement:
            return generator_messages, path_enhancer_output
        else:
            return generator_messages, generator_output

    @staticmethod
    def get_knowledge_base_vector_store_ids(bug, reponame):
        stores = GPTUtil.load_vector_stores(reponame)
        bug_dt = bug.closed_time
        if bug_dt is None:
            return []

        dated_stores = []
        for key, vs_id in stores.items():
            # Try full datetime format: YYYY-MM-DDTHH:MM:SS
            m = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", key)
            if m:
                dt = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S")
                dated_stores.append((dt, vs_id))
                continue

            # Otherwise, try date only: YYYY-MM-DD
            m = re.search(r"(\d{4}-\d{2}-\d{2})", key)
            if m:
                dt = datetime.strptime(m.group(1), "%Y-%m-%d")
                dated_stores.append((dt, vs_id))

        if not dated_stores:
            return []

        # Keep only stores with date <= bug's closed_time
        eligible = [item for item in dated_stores if item[0] <= bug_dt]
        if not eligible:
            return []

        # Pick the latest (closest prior or equal)
        best = max(eligible, key=lambda x: x[0])
        return [best[1]]



