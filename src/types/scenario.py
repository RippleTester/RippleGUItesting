from typing import Dict, List
import re

"""
ScenarioOutline + Examples
https://cucumber.io/docs/gherkin/reference/#scenario-outline
https://cucumber.io/docs/gherkin/reference/#examples
"""

class ParametrizedStep:
    def __init__(self, template: str):
        self.template = template
        self.variables = self.extract_variables()

    def extract_variables(self) -> List[str]:
        # Extract variables in the form <var_name>
        return re.findall(r"<(.*?)>", self.template)

    def fill(self, values: Dict[str, str]) -> str:
        result = self.template
        for var in self.variables:
            if var in values:
                result = result.replace(f"<{var}>", values[var])
            else:
                raise ValueError(f"Missing value for variable: {var}")
        return result

    def __repr__(self):
        return f"ParametrizedSentence(template={self.template})"


class Scenario:
    def __init__(self, summary: str, steps: List[ParametrizedStep], examples: List[Dict[str, str]]):
        self.summary = summary
        self.steps = steps
        self.examples = examples  # Each example is a dict of variable values

    def render(self) -> str:
        scenario_blocks = []
        for i, example in enumerate(self.examples):
            scenario_name = f"{self.summary} - Example {i + 1}"
            rendered_steps = [step.fill(example) for step in self.steps]
            scenario_blocks.append(self._render_block(scenario_name, rendered_steps, example))
        return "\n\n".join(scenario_blocks)

    def _render_block(self, title: str, steps: List[str], example: Dict[str, str]) -> str:
        block = [f"Scenario: {title}"]
        for step in steps:
            block.append(f"  {step}")
        return "\n".join(block)

    def __repr__(self):
        return f"Scenario(summary={self.summary}, steps={len(self.steps)} steps, examples={len(self.examples)} examples)"
