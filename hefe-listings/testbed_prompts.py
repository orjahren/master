# We wish to decrease the driveability of the scenario by enhancing it with more
# details, increasing its complexity

# Prompt structure:
"""
1 - Context: We are working with a driving simulation environment for the Carla simulator.
2 - Task: Decrease the driveability of the scenario by enhancing it with more details and complexity.
3 - Input: <scenario_description, in python carla scenario format>
4 - Output: An enhanced version of the scenario description with additional
details and complexity, still in Python carla scenario format. ONLY output the
code, without any additional text or explanation.
"""

from typing import Callable, Literal

PromptName = Literal[
    "basic",
    "no_explanation",
    "no_explanation_strict",
    "cot",
    "cot_strict_methods_in_file",
    "cot_strict_carla_api",
    "minimal_changes",
    "minimal_changes_shared_file",
    "minimal_changes_specific_metric",
]


def name_to_prompt_fn(name: PromptName):
    prompts: dict[PromptName, Callable[[str], str]] = {
        "basic": lambda python_carla_scenario_raw: f"""
    1 - Context: We are working with a driving simulation environment for the Carla simulator.
    2 - Task: Decrease the driveability of the scenario by enhancing it with more details and complexity.
    3 - Input: {python_carla_scenario_raw}
    4 - Output: An enhanced version of the scenario description with additional
    details and complexity, still in Python carla scenario format.
    """,
        "no_explanation": lambda python_carla_scenario_raw: f"""
    1 - Context: You are a tool for decreasing the driveability of scenarios in the driving simulator Carla.
    2 - Task: Decrease the driveability of the scenario by enhancing it with more details and complexity.
    3 - Input, the Python specification for the scenario: {python_carla_scenario_raw}
    4 - Output: An enhanced version of the scenario with additional details and
    complexity, still in Python carla scenario format. Only ever output the code,
    without any additional text or explanation.
    """,
        "no_explanation_strict": lambda python_carla_scenario_raw: f"""
    1 - Context: You are a tool for decreasing the driveability of scenarios in the driving simulator Carla.
    2 - Task: Decrease the driveability of the scenario by enhancing it with more details and complexity.
    3 - Input, the Python specification for the scenario: {python_carla_scenario_raw}
    4 - Output: An enhanced version of the scenario with additional details and
    complexity, still in Python carla scenario format. Only ever output the code,
    without any additional text or explanation. It is important that you only
    use methods and classes that are part of the official Carla API, and do not
    invent new ones or use non-existent ones.
    """,
        "cot": lambda python_carla_scenario_raw: f"""
    1 - Context: You are a tool for decreasing the driveability of scenarios in the driving simulator Carla.
    2 - Task: Decrease the driveability of the scenario by enhancing it with more details and complexity.
    3 - Input, the Python specification for the scenario: {python_carla_scenario_raw}
    4 - Reasoning: Think step by step about how to make the scenario more complex and less driveable, considering possible obstacles, traffic, weather, and other factors using only the official Carla API.
    5 - Output: Only output the enhanced scenario code in Python Carla scenario format, with no additional text or explanation.
    """,
        # Samme som den over bare med "kun bruk metoder som finnes i filen"
        "cot_strict_methods_in_file": lambda python_carla_scenario_raw: f"""
    1 - Context: You are a tool for decreasing the driveability of scenarios in the driving simulator Carla.
    2 - Task: Decrease the driveability of the scenario by enhancing it with
    more details and complexity, using only the same methods that are already
    provided in the file.
    3 - Input, the Python specification for the scenario: {python_carla_scenario_raw}
    4 - Reasoning: Think step by step about how to make the scenario more complex and less driveable, considering possible obstacles, traffic, weather, and other factors using only the official Carla API.
    5 - Output: Only output the enhanced scenario code in Python Carla scenario format, with no additional text or explanation.
    """,
        # Samme som den over bare med "kun bruk Carla-APIet"
        "cot_strict_carla_api": lambda python_carla_scenario_raw: f"""
    1 - Context: You are a tool for decreasing the driveability of scenarios in the driving simulator Carla.
    2 - Task: Decrease the driveability of the scenario by enhancing it with
    more details and complexity, using only methods that are part of the
    official Carla API, version 0.9.15.
    3 - Input, the Python specification for the scenario: {python_carla_scenario_raw}
    4 - Reasoning: Think step by step about how to make the scenario more complex and less driveable, considering possible obstacles, traffic, weather, and other factors using only the official Carla API.
    5 - Output: Only output the enhanced scenario code in Python Carla scenario format, with no additional text or explanation.
    """,
        # Minmal changes. Her maa vi faa noe til aa kjore!!
        "minimal_changes": lambda python_carla_scenario_raw: f"""
    1 - Context: You are a tool for decreasing the driveability of scenarios in the driving simulator Carla.
    2 - Task: Decrease the driveability of the scenario by enhancing it with
    more details and complexity, using only methods that are part of the
    official Carla API, version 0.9.15.
    3 - Input, the Python specification for the scenario: {python_carla_scenario_raw}
    4 - Reasoning: Think step by step about how to make the scenario more complex and less driveable, considering possible obstacles, traffic, weather, and other factors using only the official Carla API.
    5 - Output: Only output the enhanced scenario code in Python Carla scenario
    format, with no additional text or explanation. Make sure to only use
    methods and concepts that are already present in the input scenario, and
    do not introduce any new methods or concepts. The changes should be as
    minimal as possible while still achieving the goal of decreasing driveability.
    """,
        # Minmal changes, men kun ett spesifikt scenario i filen
        "minimal_changes_shared_file": lambda python_carla_scenario_raw, scenario_name: f"""
    1 - Context: You are a tool for decreasing the driveability of scenarios in the driving simulator Carla.
    2 - Task: Decrease the driveability of the scenario by enhancing it with
    more details and complexity, using only methods that are part of the
    official Carla API, version 0.9.15.
    3 - Input, the Python specification for the scenario:
    {python_carla_scenario_raw}. Note that there are several scenarios in the file,
    but you should only modify the one called {scenario_name}. Don't change any of the
    other scenarios.
    4 - Reasoning: Think step by step about how to make the scenario more complex and less driveable, considering possible obstacles, traffic, weather, and other factors using only the official Carla API.
    5 - Output: Only output the enhanced scenario code in Python Carla scenario
    format, with no additional text or explanation. Make sure to only use
    methods and concepts that are already present in the input scenario, and
    do not introduce any new methods or concepts. The changes should be as
    minimal as possible while still achieving the goal of decreasing driveability.
    """,
        # Minmal changes. Her maa vi faa noe til aa kjore!!
        "minimal_changes_specific_metric": lambda python_carla_scenario_raw, specific_metric: f"""
    1 - Context: You are a tool for decreasing the driveability of scenarios in the driving simulator Carla.
    2 - Task: Decrease the driveability of the scenario by enhancing it with
    more details and complexity, using only methods that are part of the
    official Carla API, version 0.9.15.
    3 - Input, the Python specification for the scenario: {python_carla_scenario_raw}
    4 - Reasoning: Think step by step about how to make the scenario more complex and less driveable, considering possible obstacles, traffic, weather, and other factors using only the official Carla API.
    5 - Output: Only output the enhanced scenario code in Python Carla scenario
    format, with no additional text or explanation. Make sure to only use
    methods and concepts that are already present in the input scenario, and
    do not introduce any new methods or concepts. The changes should be as
    minimal as possible while still achieving the goal of decreasing
    driveability.
    Focus on making the scenario more difficult with respect to the
    following specific metric: {specific_metric}
    """,

        # Minmal changes, men kun ett spesifikt scenario i filen OG en metric
        "minimal_changes_shared_file_specific_metric": lambda python_carla_scenario_raw, scenario_name, specific_metric: f"""
    1 - Context: You are a tool for decreasing the driveability of scenarios in the driving simulator Carla.
    2 - Task: Decrease the driveability of the scenario by enhancing it with
    more details and complexity, using only methods that are part of the
    official Carla API, version 0.9.15.
    3 - Input, the Python specification for the scenario:
    {python_carla_scenario_raw}. Note that there are several scenarios in the file,
    but you should only modify the one called {scenario_name}. Don't change any of the
    other scenarios.
    4 - Reasoning: Think step by step about how to make the scenario more complex and less driveable, considering possible obstacles, traffic, weather, and other factors using only the official Carla API.
    5 - Output: Only output the enhanced scenario code in Python Carla scenario
    format, with no additional text or explanation. Make sure to only use
    methods and concepts that are already present in the input scenario, and
    do not introduce any new methods or concepts. The changes should be as
    minimal as possible while still achieving the goal of decreasing
    driveability.
    Focus on making the scenario more difficult with respect to the
    following specific metric: {specific_metric}
    """,
    }

    return prompts[name]


# TODO: Lage bedre system for aa definere hvilke prompts som trenger hvilke ekstra inputs.
def prompt_takes_specific_metric(prompt_name: PromptName) -> bool:
    return prompt_name in ["minimal_changes_specific_metric", "minimal_changes_shared_file_specific_metric"]


# TODO: Lage bedre system for aa definere hvilke prompts som trenger hvilke ekstra inputs
def prompt_takes_scenario_name(prompt_name: PromptName) -> bool:
    return prompt_name in ["minimal_changes_shared_file_specific_metric"]

# TODO: "Scenario name" er lett aa forveksle med "prompt name" eller filnavn paa scnearioet. Kanskje bytte navn paa en av dem?


def get_prompt_for_python_scenario_enhancement(python_carla_scenario_raw: str, prompt_name: PromptName, scenario_name: str, specific_metric: str) -> str:
    prompt_fn = name_to_prompt_fn(prompt_name)

    if prompt_takes_scenario_name(prompt_name) and prompt_takes_specific_metric(prompt_name):
        return prompt_fn(python_carla_scenario_raw, scenario_name, specific_metric)
    elif prompt_takes_scenario_name(prompt_name):
        return prompt_fn(python_carla_scenario_raw, scenario_name)
    elif prompt_takes_specific_metric(prompt_name):
        return prompt_fn(python_carla_scenario_raw, specific_metric)
    else:
        return prompt_fn(python_carla_scenario_raw)
