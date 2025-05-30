import argparse
import ast
from pathlib import Path
from typing import List

from jinja2 import Template

from testgen import ReqifParser, TreeNode
from testgen.generator import TestGenerator, sanitize_name


def update_tests(test_generator: TestGenerator):
    path = test_generator.path
    for node in test_generator.nodes:
        update_requirement_node(node, test_generator, path)


def update_requirement_node(node, test_generator: TestGenerator, path: Path):
    if node.type == "_RequirementType":
        folder_path = Path.joinpath(path, sanitize_name(node.label))
        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
        for child in node.children:
            update_requirement_node(child, test_generator, folder_path)
    elif node.type == "_TestType":
        file_path = Path.joinpath(path, f"test_{sanitize_name(node.label)}.py")
        test_cases = []
        for child in node.children:
            if child.type == "_TestCaseType":
                test_cases.append(child)
        if not file_path.exists():
            file_path.touch()
            test_generator.generate_test_file(file_path, test_cases)
        else:
            update_test_file(file_path, test_cases, test_generator)


def update_test_file(file_path: Path, test_cases: List[TreeNode], test_generator: TestGenerator):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    existing_functions = {}
    current_func = None
    func_content = []
    has_skip = False

    for line in content.splitlines():
        if line.strip().startswith('@pytest.mark.skip'):
            has_skip = True
        elif line.strip().startswith('def test_'):
            current_func = line.strip().split('def ')[1].split('(')[0]
            func_content = []
        elif current_func:
            if line and not line.startswith(' ') and not line.startswith('\t'):
                existing_functions[current_func] = {
                    'body': '\n'.join(func_content),
                    'has_skip': has_skip
                }
                current_func = None
                has_skip = False
            else:
                func_content.append(line)

    if current_func:
        existing_functions[current_func] = {
            'body': '\n'.join(func_content),
            'has_skip': has_skip
        }

    update_template = Template("""
import pytest

{% for case in test_cases -%}
@pytest.mark.project_id("{{ project_id }}")
@pytest.mark.meta(id="{{ case.id }}", scenario="{{ case.description }}", steps="{{ case.steps }}", prerequisites="{{ case.prerequisites }}")
{%- set func_name = "test_" ~ case.label.replace(" ", "_") -%}
{%- for decorator in case.generate_parametrize_decorators() %}
{{ decorator }}
{%- endfor %}
{%- if func_name in existing_functions and existing_functions[func_name]['has_skip'] %}
@pytest.mark.skip(reason="Not implemented yet.")
{%- endif %}
def {{ func_name }}({{ case.get_parameters_names() }}):
{%- if func_name in existing_functions %}
{{ existing_functions[func_name]['body'] }}
{%- else %}
    # TODO: Implement test and dont forget to delete @pytest.mark.skip(reason="Not implemented yet.") decorator.
    pass
{%- endif %}

{% endfor -%}
    """)

    content = update_template.render(
        test_cases=test_cases,
        project_id=test_generator.project_id,
        existing_functions=existing_functions
    )

    file_path.write_text(content, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="Check test coverage against reqif file")
    parser.add_argument('reqif_path', type=str, help="Path to the .reqif file")
    parser.add_argument('tests_path', type=str, help="Path to the tests directory")

    args = parser.parse_args()

    reqif_path = Path(args.reqif_path)
    tests_path = Path(args.tests_path)

    if not reqif_path.exists():
        print(f"Error: Reqif path '{reqif_path}' does not exist")
        return

    if not tests_path.exists():
        print(f"Error: Tests path '{tests_path}' does not exist")
        return

    reqif_parser = ReqifParser(reqif_path)
    data = reqif_parser.parse_reqif()
    header_data = reqif_parser.parse_header_data()

    test_generator = TestGenerator(data, tests_path, header_data["project_id"])

    update_tests(test_generator)
