import json
from enum import Enum
from pathlib import Path

from src.pipelines.placeholder import Placeholder
from src.utils.file_util import FileUtil
from src.utils.gpt_util import GPTUtil
from src.utils.llm_util import LLMUtil
from pydantic import BaseModel

class FilterReason(str, Enum):
    KEEP = "keep"
    DUPLICATE = "duplicate"
    SCREENSHOT_TIMING = "screenshot_timing"
    UNSTABLE_GUI = "unstable_gui"
    NOT_A_BUG = "not_a_bug"

class BugReportFlag(BaseModel):
    bug_no: int
    summary: str

    keep: bool
    reason: FilterReason
    rationale: str  # concise, not chain-of-thought
    duplicate_of_bug_summary_list: list[str] | None = None  # representative summary

class PostProcessorOutput(BaseModel):
    bug_report_flags: list[BugReportFlag]


class PostProcessor:
    def __init__(self):
        pass

    @staticmethod
    def load_bugs_from_detector_output(generator_dir):
        bug_list = []
        bug_index = 0
        # Find all subdirectories whose names are digits (e.g. "0", "1", "2")
        # and sort them numerically to ensure deterministic ordering
        step_dirs = sorted(
            [p for p in generator_dir.iterdir() if p.is_dir() and p.name.isdigit()],
            key=lambda p: int(p.name),
        )

        for step_dir in step_dirs:
            # Locate detector_*.json in the step directory
            # There should normally be exactly one
            detector_files = list(step_dir.glob("detector_*.json"))

            if not detector_files:
                # Skip steps that do not contain a detector output
                continue

            detector_path = detector_files[0]

            detector_output = FileUtil.load_json(detector_path)
            for index, one_output in enumerate(detector_output):
                if index % 2 == 1:
                # Extract bug reports (field name depends on detector schema)
                    for bug in one_output["bug_reports"]:
                        bug["bug_no"] = bug_index
                        bug_list.append(bug)
                        bug_index = bug_index + 1

        return bug_list


    @staticmethod
    def filter_bugs(case_path,
                  output_format=PostProcessorOutput,
                  prompt_folder=Placeholder.POST_PROCESSOR, system_prompt=Placeholder.SYSTEM,
                  model=GPTUtil.GPT5_2, reasoning='medium'):
        case_root = Path(case_path)

        generator_dirs = [
            p for p in case_root.iterdir()
            if p.is_dir() and p.name.startswith("generator_")
        ]

        if not generator_dirs:
            raise RuntimeError(f"No generator_* directory found in {case_root}")
        generator_dir = generator_dirs[0]

        input_content = PostProcessor.load_bugs_from_detector_output(generator_dir)
        if isinstance(input_content, (dict, list)):
            input_content = json.dumps(input_content, ensure_ascii=False, indent=2)

        system_instructions = LLMUtil.get_instructions(prompt_folder, system_prompt)
        duration_mins = None
        if input_content.strip():
            (response, cost), duration_mins = GPTUtil.parse_response(input_content, output_format=output_format, system_instructions=system_instructions,
                                    model=model, reasoning=reasoning)
        else:
            response, cost = None, None
        output = {
            Placeholder.COST: cost,
            Placeholder.DURATION_MINS: duration_mins,
        }
        if response:
            response_output = json.loads(response.output_text)
            output = output | response_output
        FileUtil.dump_json(Path(generator_dir, f"{Placeholder.POST_PROCESSOR}.json"), output)
        return output

