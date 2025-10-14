import os


# TODO: Implementer denne
# TODO: Fastslaa hvilket format vi bruker (OpenSCENARIO/CommonRoad/andre)
def file_format_is_valid(file_format: str) -> bool:
    """
    Check if the file format is valid.

    Args:
        file_format (str): The file format to check.

    Returns:
        bool: True if the file format is valid, False otherwise.
    """
    return file_format in ["json", "yaml", "yml", "csv", "txt"]


def enumerate_enhanced_scenarios(scenario_repository_path: str, scenario_name: str) -> int:
    """
    Enumerate enhanced scenarios in a given scenario path.

    Args:
        scenario_repository_path (str): The path to the scenario directory.
        scenario_name (str): The name of the scenario.

    Returns:
        int: The number of enhanced scenarios found.
    """
    # TODO: Can probably refactor this
    acc = 0
    for scenario in os.listdir(scenario_repository_path):
        print(f"Checking scenario: {scenario}")
        if scenario_name in scenario and "enhanced" in scenario:
            acc += 1
    return acc


# TODO: Should use better names. Need a way of tracking enhanced scenario
# metadata
# - Timestamp
# - What prompt was used
# - What model was used
# - What the original scenario was
# - What changes were made?
def get_enhanced_scenario_name(scenario_repository_path: str, scenario_name: str) -> str:
    """
    Get the enhanced scenario name. 

    Args:
        scenario_repository_path (str): The path to the scenario directory.
        scenario_name (str): The base name of the scenario.

    Returns:
        str: The enhanced scenario name.
    """
    num_enhanced_scenarios = enumerate_enhanced_scenarios(
        scenario_repository_path, scenario_name)
    if num_enhanced_scenarios == 0:
        return f"{scenario_name}-enhanced"
    else:
        # Big brain time...who needs UUIDs when you can just count files?
        return f"{scenario_name}-enhanced-{num_enhanced_scenarios + 1}"


def get_available_scenarios(scenario_repository_path: str) -> list:
    def extension_is_ok(filename: str) -> bool:
        # TODO: Verify which formats we want to support
        return filename in ["xosc", "py"]

    return [filename for filename in os.listdir(scenario_repository_path) if extension_is_ok(filename)]


# TODO: Should strip newlines??
def scenario_path_to_string(scenario_path: str) -> str:
    with open(scenario_path, 'r') as file:
        return file.read()


# TODO: Let this function determine output file name?
def save_enhanced_scenario(scenario_str: str, output_path: str):
    with open(output_path, 'w') as file:
        file.write(scenario_str)
