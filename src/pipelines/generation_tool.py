import json
from pathlib import Path

from pydantic import BaseModel

from src.pipelines.placeholder import Placeholder

from src.utils.dict_util import DictUtil
from src.utils.gpt_util import GPTUtil
from src.utils.llm_util import LLMUtil
from config import PROMPT_DIR, APP_NAME_FIREFOX, FIREFOX_COMMIT_MESSAGE_LINK, GITHUB_COMMIT_LINK


class Step(BaseModel):
    step: str
    oracles: list[str] | None

class Scenario(BaseModel):
    explanation: str
    summary: str
    steps: list[Step]

class GenerationOutput(BaseModel):
    """
    Output model for the code exploration and test scenario generation workflow.
    """
    change_intent_explanation: list[str]  # Explanation of the intent behind the code changes
    code_changes_explanation: list[str]  # Description of the specific code changes made
    impact_analysis: list[str]  # Analysis of the potential impact on end-user scenarios
    test_scenarios: list[Scenario]


class GenerationTool:

    def __init__(self):
        pass

    @staticmethod
    def get_instructions(foldername=Placeholder.GENERATOR, system_prompt=Placeholder.SYSTEM):
        with open(Path(PROMPT_DIR, foldername, system_prompt), "r", encoding="utf-8") as file:
            instructions = file.read()
        return instructions

    @staticmethod
    def get_code_change_intent(commit):
        # @todo code change intent into a list
        # bug = commit.bugs[0]
        code_change_intent = []
        # print(len(commit.bugs))
        for bug in commit.bugs:
            # print(bug)
            one_code_change_intent = {
                Placeholder.SUMMARY: bug.summary,
                Placeholder.DESCRIPTION: bug.description.text,
            }
            closed_issues = []
            for closed_issue in bug.closed_issues:
                closed_issues.append({
                    Placeholder.SUMMARY: closed_issue.summary,
                    Placeholder.DESCRIPTION: closed_issue.description.text,
                })

            if closed_issues:
                one_code_change_intent[Placeholder.CLOSED_ISSUES] = closed_issues
            code_change_intent.append(one_code_change_intent)
        # print(json.dumps(code_change_intent, indent=2))
        return code_change_intent

    @staticmethod
    def get_input_from_commits(commits, with_change_desc=True, with_change_intent=True,
              # with_file_content=False,
              with_relevant_scenarios=False,
              # with_cochange_file_content=False,
              reponame=APP_NAME_FIREFOX,
              # ownername=None,
                               ):
        """
        commits: code patch, code_change_desc (commit messages), change_intent (linked bug reports)
        file_content: get from files
        relevant_scenarios:
        cochange_file_content: get from cochanges
        """
        input = {}
        if with_change_intent:
            # @todo pass all commits? or all commits share the same code change intent?
            change_intent = GenerationTool.get_code_change_intent(commits[0])
            input[Placeholder.CODE_CHANGE_INTENT] = input.get(Placeholder.CODE_CHANGE_INTENT, change_intent)
            # print(json.dumps(input, indent=2))
        input[Placeholder.CODE_CHANGES] = input.get(Placeholder.CODE_CHANGES, [])
        if reponame == APP_NAME_FIREFOX:
            merge_commits = commits
        else:
            merge_commits = commits[0].bugs[0].merge_commits
        for merge_commit in merge_commits:
            commit_dict = {
                Placeholder.FILES: []
            }
            if with_change_desc:
                if reponame == APP_NAME_FIREFOX:
                    commit_dict[Placeholder.CODE_CHANGE_DESCRIPTION] = merge_commit.message
                else:
                    commit_dict[Placeholder.CODE_CHANGE_DESCRIPTION] = ""
                    for commit in commits:
                        if isinstance(commit, str):
                            message = commit
                            print(message)
                            commit_dict[Placeholder.CODE_CHANGE_DESCRIPTION] = message
                        else:
                            message = commit.message

                        commit_dict[Placeholder.CODE_CHANGE_DESCRIPTION] += f"{message}\n"
                        # commit_dict[Placeholder.CODE_CHANGE_DESCRIPTION] += f"{commit.message}\n"
            for file_patch in merge_commit.file_patches:
                file_dict = {
                    Placeholder.FILEPATH: file_patch.filepath,
                    Placeholder.FILE_PATCH: file_patch.get_file_patch_text(),
                }
                # @todo this is too big to LLMs context,
                # @todo so add by file_search, or refer to bug fixing task how to access the repo
                # if with_file_content:
                #     files = with_file_content
                #     file = files.get_file_by_filepath(file_patch.filepath)
                #     file_content = None
                #     if file:
                #         file_content = file.get_file_content()
                #     file_dict[Placeholder.FILE_CONTENT] = file_dict.get(Placeholder.FILE_CONTENT, file_content)
                commit_dict[Placeholder.FILES].append(file_dict)
            if with_relevant_scenarios:
                # @todo finer granularity
                relevant_scenarios = with_relevant_scenarios
                if reponame == APP_NAME_FIREFOX:
                    ranked_scenarios = relevant_scenarios[f"{FIREFOX_COMMIT_MESSAGE_LINK}{merge_commit.id}"]["ranked_scenarios"]
                else:
                    # @todo
                    ranked_scenarios = relevant_scenarios[merge_commit.html_url]["ranked_scenarios"]
                keys_to_remove = ["id", "scenarios", "attachments", "tossing_path", "creation_time", "closed_time", "last_change_time",
                                  "status", "labels", "relation", "keywords", "merged_at", "merge_commits",
                                  "closer_pulls", "closed_pulls",
                                  # "closed_issues",
                                  "crossref_issues", "crossref_pulls",
                                  Placeholder.RANK, Placeholder.COUNT]

                ranked_scenarios = DictUtil.remove_keys(ranked_scenarios, keys_to_remove)
                commit_dict[Placeholder.PRECEDING_CHANGE_INTENTS] = commit_dict.get(Placeholder.PRECEDING_CHANGE_INTENTS,
                                                                                    ranked_scenarios)
            input[Placeholder.CODE_CHANGES].append(commit_dict)
        return input

    @staticmethod
    def generate(input_content,
                previous_response_id=None, model=GPTUtil.GPT5,
                # with_file_content=False,
                tools=[],
                include_search_results=True,
                vector_store_ids=None,
                build_info=None,
                reponame=APP_NAME_FIREFOX
                ):

        instructions = None
        if previous_response_id is None:
            instructions = LLMUtil.get_instructions(
                prompt_folder=Placeholder.GENERATOR,
                system_prompt=Placeholder.SYSTEM)
        if vector_store_ids:
            file_search_tool = {
                "type": "file_search",
                "vector_store_ids": vector_store_ids
            }
            tools.append(file_search_tool)

        output_format = GenerationOutput
        if tools and include_search_results:
            include_search_results = ["file_search_call.results"]
        else:
            include_search_results = []
        (response, cost), duration_time = GPTUtil.parse_response(str(input_content),
                                                output_format=output_format,
                                                previous_response_id=previous_response_id,
                                                system_instructions=instructions,
                                                tools=tools,
                                                include=include_search_results,
                                                model=model)
        # print(json.dumps(json.loads(response.model_dump_json()), indent=2))
        # # print(response)
        # output = json.loads(response.output_text)
        outputs = GPTUtil.get_response_outputs(response)
        if outputs:
            output = outputs[0]
            output[Placeholder.RESPONSE_ID] = output.get(Placeholder.RESPONSE_ID, response.id)
            tool = GPTUtil.extract_tool_invocations_from_response(response)
            output[Placeholder.TOOL] = output.get(Placeholder.TOOL, tool)
            output[Placeholder.COST] = output.get(Placeholder.COST, cost)
            output[Placeholder.DURATION_MINS] = output.get(Placeholder.DURATION_MINS, duration_time)
            output[Placeholder.INFO] = output.get(Placeholder.INFO, build_info)
        else:
            output = None
        messages = LLMUtil.get_messages(instructions, [(input_content, output)])
        # LLMUtil.show_messages(messages)

        return output, messages

