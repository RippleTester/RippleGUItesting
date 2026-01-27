class Placeholder:
    SOFTWARE_NAME = "SOFTWARE_NAME"
    INSTRUCTIONS = "INSTRUCTIONS"
    UI_INSTRUCTION = "UI_INSTRUCTION"
    UI_INSTRUCTIONS = "UI_INSTRUCTIONS"
    STEP_INSTRUCTION = "STEP_INSTRUCTION"
    # model######################################################
    MODEL_NAME = "model_name"
    PRICE_PER_CACHED_INPUT_TOKEN = "price_per_cached_input_token"
    PRICE_PER_INPUT_TOKEN = "price_per_input_token"
    PRICE_PER_OUTPUT_TOKEN = "price_per_output_token"
    PRICE_PER_CACHE_WRITES_TOKEN = "price_per_cache_writes_token"
    PRICE_PER_CACHE_HITS_TOKEN = "price_per_cache_hits_token"
    PRICE_PER_5M_CACHE_WRITES_TOKEN = "price_per_5m_cache_writes_token"
    PRICE_PER_1H_CACHE_WRITES_TOKEN = "price_per_1h_cache_writes_token"
    PRICE_PER_CACHE_HITS_REFRESHES_TOKEN = "price_per_cache_hits_refreshes_token"

    # agent######################################################
    POST_PROCESSOR = "post_processor"
    SELECTOR = "selector"
    CONSTRUCTOR = "constructor"
    GENERATOR = "generator"
    CHANGE_INTENT_EXPLANATION = "change_intent_explanation"
    CODE_CHANGES_EXPLANATION = "code_changes_explanation"
    IMPACT_ANALYSIS = "impact_analysis"
    SCENARIO_GENERATION_EXPLANATION = "scenario_generation_explanation"
    INSPECTOR = "inspector"
    KNOWLEDGE_SEARCH_TOOL = "knowledge_search_tool"
    FILE_SEARCH = "file_search"
    # SCENARIO_ANALYZE_TOOL = "scenario_analyze_tool"
    ENHANCER = "enhancer"
    PATH_ENHANCER = "path_enhancer"
    STEP_DIVERSITY_ANALYSIS = "step_diversity_analysis"
    SEARCH_QUERY_GENERATION = "search_query_generation"
    DATA_ENHANCER = "data_enhancer"
    SCENARIO_OUTLINE_ANALYSIS = "scenario_outline_analysis"
    SEARCH_DATA_QUERY_GENERATION = "search_data_query_generation_explanation"
    # SCENARIO_GENERATE_TOOL = "scenario_generate_tool"
    QUERY = "query"
    QUERIES = "queries"
    RESPONSE_ID = "RESPONSE_ID"
    # EXPLORER = "explorer"
    # GUARDIAN = "guardian"
    PLANNER = "planner"
    PLAYER = "player"
    EXECUTOR = "executor"
    REPLAYER = "replayer"
    DETECTOR = "detector"

    EXECUTION_MEMORY = "EXECUTION_MEMORY"
    REUSABLE_INSTRUCTIONS = "REUSABLE_INSTRUCTIONS"
    UBUNTU_COMMON_STEP_INSTRUCTIONS = "ubuntu_common_step_instructions"
    COMMON_STEP_INSTRUCTIONS = "COMMON_STEP_INSTRUCTIONS"
    # tool######################################################
    TOOL = "tool"
    COMPUTER_USE_TOOL = "computer_use_tool"
    INSTRUCTION_REUSE_TOOL = "instruction_reuse_tool"
    BUG_REPORT_TOOL = "bug_report_tool"
    # role ######################################################
    SYSTEM = "system"

    RANK = 'RANK'
    COUNT = 'COUNT'

    # GUIParser
    INTERACTIVE_ELEMENTS = "INTERACTIVE_ELEMENTS"
    INTERACTIVE_ELEMENT = "INTERACTIVE_ELEMENT"
    ELEMENTS = "elements"

    INTERACTIVITY = "interactivity"
    TYPE = "type"

    WIDTH = "width"
    HEIGHT = "height"

    # file
    FILE_MODIFIED = 'modified'  # modify content, rename
    FILE_ADDED = 'added'
    FILE_REMOVED = 'removed'
    FILE_COPY = 'copy'  # copy from A to B with/without modifying content

    FILES = 'FILES'
    FILEPATH = 'FILEPATH'
    FILE_PATCH = 'FILE_PATCH'

    INFO = 'INFO'
    BUILD_INFO = 'BUILD_INFO'
    COMMIT_ID = "COMMIT_ID"
    PARENT_COMMIT_ID = "PARENT_COMMIT_ID"
    PARENT_COMMIT_DATE = "PARENT_COMMIT_DATE"
    DATE = "DATE"
    PUSH_DATE = "PUSH_DATE"
    COMMITS = "COMMITS"

    CODE_CHANGE = "CODE_CHANGE"
    CODE_CHANGES = "CODE_CHANGES"
    CODE_CHANGE_DESCRIPTION = "CHANGE_DESC"
    CODE_CHANGE_INTENT = "CHANGE_INTENT"
    FILE_CONTENT = "FILE_CONTENT"
    COCHANGE_FILE_CONTENT = "COCHANGE_FILE_CONTENT"
    PRECEDING_CHANGE_INTENTS = "PRECEDING_CHANGE_INTENTS"

    BUILDS = "BUILDS"
    BUILD_ID_FIRST_WITH = "BUILD_ID_FIRST_WITH"
    BUILD_ID_LAST_WITHOUT = "BUILD_ID_LAST_WITHOUT"
    # action######################################################
    TAP = 'tap'
    CLICK = 'click'
    LONG_TAP = 'long_tap'
    DOUBLE_TAP = 'double_tap'
    INPUT = 'input'
    SCROLL = 'scroll'
    SCROLL_DIRECTION = 'SCROLL_DIRECTION'
    SCROLL_UP = 'up'
    SCROLL_DOWN = 'down'
    SCROLL_LEFT = 'left'
    SCROLL_RIGHT = 'right'
    HOME = 'home'
    ENTER = 'enter'
    LANDSCAPE = 'landscape'
    PORTRAIT = 'portrait'
    KEYS = 'KEYS'

    # New actions
    RIGHT_TAP = 'right_tap'
    DRAG_AND_DROP = "drag_and_drop"
    MOVE_RELATIVE = "move_relative"
    CAPTURE_REGION = "capture_region"
    LOCATE = "locate"
    ALERT = "alert"
    CONFIRM = "confirm"
    GET_MOUSE_POSITION = "get_mouse_position"

    ACTION = 'ACTION'
    ACTIONS = 'ACTIONS'
    ACTIONS_INFO = [TAP, LONG_TAP, DOUBLE_TAP, INPUT, SCROLL, HOME, ENTER, LANDSCAPE, PORTRAIT]

    COORDINATES = 'coordinates'
    COORDINATE_X = 'x_coordinate'
    COORDINATE_Y = 'y_coordinate'

    CENTER_COORDINATES = 'center_coordinates'

    NO = 'no'

    APP_DIR = 'APP_DIR'
    SCREENSHOT_OPERATION_LIST = 'SCREENSHOT_OPERATION_LIST'
    OUTPUT_LIST = 'OUTPUT_LIST'
    PLANNER_OUTPUT = 'PLANNER_OUTPUT'
    PLANNER_COST = 'PLANNER_COST'
    PLAYER_VERIFIER_OUTPUT_LIST = 'PLAYER_VERIFIER_OUTPUT_LIST'
    PLAYER_OUTPUT = 'PLAYER_OUTPUT'
    VERIFIER_OUTPUT = 'VERIFIER_OUTPUT'

    COST = 'COST'

    DURATION_MINS = 'DURATION_MINS'
    TOTAL_DURATION_MINS = 'TOTAL_DURATION_MINS'

    SUB_STEP = 'SUB_STEP'
    SUB_STEPS = 'SUB_STEPS'
    STEP = 'STEP'
    STEPS = 'STEPS'
    ORACLES = 'ORACLES'
    OPERATION = 'OPERATION'
    OPERATIONS = 'OPERATIONS'
    SCREENSHOT = 'SCREENSHOT'
    PARSED_SCREENSHOT = 'PARSED_SCREENSHOT'
    PARSED_ = 'PARSED_'
    PARSED_INFO = 'PARSED_INFO'
    SCREENSHOT_BEFORE_CHANGE = 'SCREENSHOT_BEFORE_CHANGE'
    SCALE = 'SCALE'
    WITH_NUMS = '_with_nums'
    SCREENSHOT_WITH_NUMS = 'SCREENSHOT_WITH_NUMS'

    PREVIOUS_STEP = 'PREVIOUS_STEP'
    PREVIOUS_STEP_NUM = 'PREVIOUS_STEP_NUM'
    PREVIOUS_STEP_COMPLETION = 'PREVIOUS_STEP_COMPLETION'
    CURRENT_STEP = 'CURRENT_STEP'
    CURRENT_STEP_NUM = 'CURRENT_STEP_NUM'
    STEP_NO = 'STEP_NO'
    STEP_COMPLETION = 'STEP_COMPLETION'
    NEXT_STEP_NO = 'NEXT_STEP_NO'
    ELEMENT_NUM = 'ELEMENT_NUM'
    ELEMENT_NAME = 'ELEMENT_NAME'
    ELEMENT_CATEGORY = 'ELEMENT_CATEGORY'
    ELEMENT_INPUT = 'ELEMENT_INPUT'
    INPUT_TEXT = 'INPUT_TEXT'

    ALL_STEPS_COMPLETION = 'ALL_STEPS_COMPLETION'

    MISSING_STEP = 'MISSING_STEP'
    COMPOUND_STEP = 'COMPOUND_STEP'

    CHAIN_OF_THOUGHTS = "CHAIN_OF_THOUGHTS"
    ANSWER = "ans"

    ELEMENT_LOCATOR_OUTPUT_FORMAT = {
        # PLAYER_OUTPUT: {
        # CHAIN_OF_THOUGHTS: "The logical reasoning required to identify which actions need to be performed, "
        #                    "which specific element to perform on this GUI.",
        STEP: "Current step's text",
        ACTION: "Specifies the type of action to perform.",
        SCROLL_DIRECTION: f"{SCROLL_UP}, {SCROLL_DOWN}, {SCROLL_LEFT} or {SCROLL_RIGHT}",
        ELEMENT_NAME: "Corresponds to the text description of the element in the GUI.",
        ELEMENT_CATEGORY: "Corresponds to the category of the element in the GUI, such as button, icon, checkbox, "
                          "radiobutton, dropdown menu, slider, link, tab,textfield, ...",
        # ELEMENT_CATEGORY: "Corresponds to the category of the element in the GUI.",
        ELEMENT_NUM: "A number corresponding to the numerical identifier of the element in the GUI.",
        ELEMENT_INPUT: "Specifies the input into the element if needed.",
    }

    STEP_IDENTIFIER = {
        CHAIN_OF_THOUGHTS: "The logical reasoning required to identify.",
        STEP_NO: "Describes the number of current step of the process.",
        MISSING_STEP: ["", ],
        SUB_STEPS: ["", ],
        # STEP_COMPLETION: "True or False. Indicates whether the step has been completed or not.",
        # NEXT_STEP_NO: "Specifies the next step number, which needs to operate."
    }

    STEP_COMPLETER = {
        CHAIN_OF_THOUGHTS: "The logical reasoning required to identify if the step is completed by the GUI.",
        STEP_NO: "Describes the number of current step of the process.",
        STEP_COMPLETION: "True or False. Indicates whether the step has been completed or not.",
        NEXT_STEP_NO: "Specifies the next step number, which needs to operate."
    }
    BUG = "BUG"
    BUGS = "BUGS"
    SUMMARY = "SUMMARY"
    PRECONDITIONS = "PRECONDITIONS"
    STEPS_TO_REPRODUCE = "STEPS_TO_REPRODUCE"
    EXPECTED_BEHAVIORS = "EXPECTED_BEHAVIORS"
    ACTUAL_BEHAVIORS = "ACTUAL_BEHAVIORS"
    STEP_NOS = "STEP_NOS"
    GUI_NUMS = "GUI_NUMS"
    STEP_VERIFICATION = "STEP_VERIFICATION"

    EXECUTION_NUM = 'EXECUTION_NUM'

    STEP_HISTORY_LIST = 'STEP_HISTORY_LIST'
    PREVIOUS_STEP_HISTORY = 'PREVIOUS_STEP_HISTORY'
    OPERATION_HISTORY = 'OPERATION_HISTORY'
    OPERATION_HISTORY_LIST = 'OPERATION_HISTORY_LIST'
    FREQUENCY = "FREQUENCY"

    STEP_HISTORY_LIST_FORMAT = {
        STEP_HISTORY_LIST: [
            {
                STEP: "",
                OPERATION_HISTORY_LIST: [
                    {
                        ACTION: "",
                        ELEMENT_NUM: "",
                        ELEMENT_INPUT: "",
                        SCROLL_DIRECTION: "",
                        EXECUTION_NUM: "Number of times the operation is executed",
                    }
                ]
            }
        ]
    }

    # KG constuction
    BUG_ID_LOWER = "bug_id"
    BUG_ID = "BUG_ID"
    REFERENCE = 'REFERENCE'
    RETRIEVAL_RESULT = "RETRIEVAL_RESULT"
    RETRIEVAL_OUTPUT = {
        CHAIN_OF_THOUGHTS: "",
        RETRIEVAL_RESULT: [
            {
                STEPS: [],
            }
        ]
    }

    CLUSTER = "CLUSTER"
    CLUSTER_INDEX = "CLUSTER_INDEX"
    CLUSTER_INDEXES = "CLUSTER_INDEXES"
    REFERENCED_BUG_IDS = 'REFERENCED_BUG_IDS'
    STEP_WITH_CLUSTER_INDEX_FORMAT = '{' \
                                     f'{STEP}: "", {CLUSTER_INDEX}: ""' \
                                     '}'

    STEP_WITH_CLUSTER_INDEX_REFERENCE_FORMAT = '{' \
                                               f'{STEP}: "", {CLUSTER_INDEX}: [], {REFERENCED_BUG_IDS}: []' \
                                               '}'
    PLANNER_OUTPUT_FORMAT = {
        # f"{CURRENT_STEP}": "Return the step to be executed. If all steps are complete, return None.",
        # f"{SUB_STEPS}": [f"Sub-steps for {CURRENT_STEP}. If all steps are complete, return None."],
        f"{CURRENT_STEP}": "Represents the step that needs to be executed next. "
                           "If there are no more steps, this should be an empty string.",
        f"{SUB_STEPS}": ["A list of sub-steps related to the current step. "
                         "If no sub-steps are left, this should be an empty list.", ],
        f"{ALL_STEPS_COMPLETION}": "True or False. "
                                   f"It should be True only when both {CURRENT_STEP} and {SUB_STEPS} are empty, "
                                   f"indicating that all steps have been completed."
    }

    CREATIVE_THINKING_ORACLES = "CREATIVE_THINKING_ORACLES"
    STEP_WITH_CLUSTER_INDEX_ORACLES_FORMAT = '{' \
                                             f'{STEP}: "", {CLUSTER_INDEX}: [], ' \
                                             f'{ORACLES}: ["", ]' \
                                             '}'
    EXECUTED_STEP = "EXECUTED_STEP"
    CONCISE_STEP = "CONCISE_STEP"
    REPRESENTATIVE_STEP = "REPRESENTATIVE_STEP"
    REPRESENTATIVE_STEPS = "REPRESENTATIVE_STEPS"
    CLUSTERS = "CLUSTERS"

    TOTAL_COST = "total_cost"
    ORACLE_FINDER_COST = "ORACLE_FINDER_COST"
    ORACLE_FINDER_OUTPUT = "ORACLE_FINDER_OUTPUT"
    ORACLE_FINDER_OUTPUT_FORMAT = {
        # CHAIN_OF_THOUGHTS: "",
        # EXECUTED_STEP: "",
        CLUSTERS: ["", ],
        ORACLES: ["", ],
    }

    CLUSTER_OUTPUT_FORMAT = {
        CLUSTER_INDEX: "",
        REPRESENTATIVE_STEPS: ["", ],
    }

    CLUSTER_IDENTIFIER_OUTPUT_FORMAT = {
        CLUSTERS: [CLUSTER_OUTPUT_FORMAT, ],
    }

    STEP_IDENTIFIER_OUTPUT_FORMAT = {
        CHAIN_OF_THOUGHTS: "",
        EXECUTED_STEP: "",
        STEPS: ["", ],
        # ORACLES: ["", ],
    }

    BUG_TYPE = 'BUG_TYPE'
    BUG_SEVERITY = 'BUG_SEVERITY'
    CONFIDENCE = 'CONFIDENCE'
    CODE_ANALYZER_COST = "CODE_ANALYZER_COST"
    FORMAT_CONVERTER_COST = "FORMAT_CONVERTER_COST"
    VERIFIER_OUTPUT_FORMAT = {
        # CHAIN_OF_THOUGHTS: "",
        CREATIVE_THINKING_ORACLES: ["", ],
        BUGS: [
            {
                # EXECUTED_STEP: "",
                # ORACLES: ["", ],
                CONFIDENCE: 'The confidence level that this found bug is a real bug, rated from 1 (weakly confident) to 5 (strongly confident)',
                BUG_TYPE: "Enhancement or Defect",
                # @todo add definition: https://wiki.mozilla.org/BMO/UserGuide/BugFields#bug_type
                # BUG_SEVERITY: "Warning or Error",
                SUMMARY: "The summary of bug",
                # PRECONDITIONS: "The preconditions to reproduce bug",
                STEPS_TO_REPRODUCE: ["steps to reproduce the bug", ],
                EXPECTED_BEHAVIORS: "Expected behaviors",
                ACTUAL_BEHAVIORS: "Actual behaviors",
                # STEP_NOS: "The numbers of relevant steps",
                # GUI_NUMS: "The numbers of relevant GUIs",
            },
        ]
    }

    VERIFIER_OUTPUT_FORMAT_WO_ORACLES = {
        # STEP_VERIFICATION: {
        #     CHAIN_OF_THOUGHTS: "",
        #     STEP_COMPLETION: "True or False. Indicates whether the step has been completed or not."
        # },
        BUGS: [
            {
                CHAIN_OF_THOUGHTS: "",
                EXECUTED_STEP: "",
                # ORACLES: ["", ],
                CREATIVE_THINKING_ORACLES: ["", ],
                SUMMARY: "The summary of bug",
                STEPS_TO_REPRODUCE: ["steps to reproduce the bug", ],
                EXPECTED_BEHAVIORS: "Expected behaviors",
                ACTUAL_BEHAVIORS: "Actual behaviors",
                STEP_NOS: "The numbers of relevant steps",
                GUI_NUMS: "The numbers of relevant GUIs", },
        ]

    }

    # INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    SUMMARY = 'SUMMARY'
    DESCRIPTION = 'DESCRIPTION'
    CLOSED_ISSUES = 'CLOSED_ISSUES'
    # PRECONDITIONS = 'PRECONDITIONS'
    STEPS_TO_REPRODUCE = 'STEPS_TO_REPRODUCE'
    EXPECTED_RESULTS = 'EXPECTED_RESULTS'
    ACTUAL_RESULTS = 'ACTUAL_RESULTS'
    NOTES = 'NOTES'
    AFFECTED_VERSIONS = 'AFFECTED_VERSIONS'
    AFFECTED_PLATFORMS = 'AFFECTED_PLATFORMS'
    OTHERS = 'OTHERS'
    # add extra parts
    ATTACHMENTS = 'ATTACHMENTS'
    BACKGROUNDS = 'BACKGROUNDS'
    TASKS = 'TASKS'

    STEP_CLUSTER = 'STEP_CLUSTER'
    STEP_TYPE = 'STEP_TYPE'
    STEP_TYPE_ACTION = 'ACTION'

    STEP_TYPE_CHECK = 'CHECK'

    SCENARIO = 'TEST_SCENARIO'
    # SCENARIOS = 'TEST_SCENARIOS'
    SCENARIOS = 'test_scenarios'
    # SCENARIOS = 'scenarios'
    SCENARIO_DEFINITION_FOR_EXTRACTOR = f"{SCENARIO} represents a user interface (UI)-based testing scenario, providing a sequence of steps. These steps encompass both actions to be executed and expected outcomes to verify."

    SCENARIO_EXTRACTION_JSON_FORMAT = '{' \
                                      f'"{SUMMARY}": "",' \
                                      f'"{STEPS}": ["",],' \
                                      '}'

    SCENARIOS_EXTRACTION_JSON_FORMAT = '{' \
                                       f'{SCENARIOS}":[{SCENARIO_EXTRACTION_JSON_FORMAT}, ]' \
                                       '}'
    SCENARIOS_EXTRACTION_COTS_JSON_FORMAT = "{" \
                                            f'"{CHAIN_OF_THOUGHTS}": "", ' \
                                            f'"{SCENARIOS_EXTRACTION_JSON_FORMAT},' \
                                            "}\n"

    STEP_WITH_TYPE_JSON_FORMAT = '{' \
                                 f'{STEP}: "", {STEP_TYPE}: ""' \
                                 '}'

    STEPS_SPLITTER_JSON_FORMAT = '{' \
                                 f'{STEPS}":[{STEP_WITH_TYPE_JSON_FORMAT}, ]' \
                                 '}'

    NON_OPERATION = 'NON_OPERATION'

    UNIQUE_BUG_NO = 'UNIQUE_BUG_NO'
    DUPLICATE_BUGS = 'DUPLICATE_BUGS'
    DEDUPLICATOR_OUTPUT = 'DEDUPLICATOR_OUTPUT'

    DEDUPLICATOR_FORMAT = {
        DEDUPLICATOR_OUTPUT:
            [
                {
                    UNIQUE_BUG_NO: "",
                    DUPLICATE_BUGS: [
                    ]
                },
            ]
    }

    VALID_ISSUES = "VALID_ISSUES"
    INVALID_ISSUES = "INVALID_ISSUES"
    CLASSIFIER_RESULT = 'CLASSIFIER_RESULT'

    CLASSIFIER_FORMAT = {
        CLASSIFIER_RESULT: "True or False",
    }

    TYPE_ENHANCEMENT = 'ENHANCEMENT'
    TYPE_DEFECT = 'DEFECT'

    BUG_VALIDITY = 'VALIDITY'
    VALID = 'VALID'
    INVALID = 'INVALID'

    VALIDITY_REASON = 'VALIDITY_REASON'
    VALID_OPTION_1 = 'Oracle from creative thinking'
    VALID_OPTION_2 = 'Oracle from KG'

    INVALID_OPTION_1 = 'Response delay or incomplete loading'
    INVALID_OPTION_2 = 'Dynamic changes not captured'
    INVALID_OPTION_3 = 'Executor location error'
    INVALID_OPTION_4 = 'Executor limited operation type'
    INVALID_OPTION_5 = 'Hallucination'
    INVALID_OPTION_6 = 'Misunderstood or overlooked'
    INVALID_OPTION_7 = 'Unexecuted execution plan'
    INVALID_OPTION_8 = 'Unreasonable or unnecessary'

    PLAN_CURRENT_STEP_VALIDITY = 'PLAN_CURRENT_STEP_VALIDITY'
    PLAN_SUB_STEPS_VALIDITY = 'PLAN_SUB_STEPS_VALIDITY'

    PLAY_STEP_PARSE_VALIDITY = 'PLAY_STEP_PARSE_VALIDITY'
    PLAY_STEP_PARSE_INVALID_OPTION_1 = 'INVALID_ACTION'
    PLAY_STEP_PARSE_INVALID_OPTION_2 = 'INVALID_ELEMENT'
    PLAY_STEP_PARSE_INVALID_OPTION_3 = 'INVALID_INPUT'
    PLAY_STEP_PARSE_INVALIDITY_REASON = 'PLAY_STEP_PARSE_INVALIDITY_REASON'
    PLAY_ELEMENT_LOCATION_VALIDITY = 'PLAY_ELEMENT_LOCATION_VALIDITY'
