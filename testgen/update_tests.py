import argparse
from pathlib import Path
from typing import List

from jinja2 import Template

from testgen import ReqifParser, TreeNode
from testgen.generator import TestGenerator, sanitize_name
from gitignore_parser import parse_gitignore


def update_tests(test_generator: TestGenerator, matches):
    path = test_generator.path
    for node in test_generator.nodes:
        update_requirement_node(node, test_generator, path, matches)


def update_requirement_node(node, test_generator: TestGenerator, path: Path, matches):
    if node.type == "_RequirementType":
        folder_path = Path.joinpath(path, sanitize_name(node.label))
        print("PAZIIIIII")
        print(folder_path)
        print(matches(folder_path))

        if not folder_path.exists():
            if not matches(folder_path):
                folder_path.mkdir(parents=True, exist_ok=True)
        for child in node.children:
            update_requirement_node(child, test_generator, folder_path, matches)
    elif node.type == "_TestType":
        file_path = Path.joinpath(path, f"test_{sanitize_name(node.label)}.py")
        print("VIIPRAAA")
        print(file_path)
        print(matches(file_path))
        if matches(file_path):
            return
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
    full_func_block = []
    has_skip = False

    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('import '):
            i += 1
            continue
        if current_func:
            if line and not line.startswith(' ') and not line.startswith('\t'):
                existing_functions[current_func] = {
                    'body': '\n'.join(func_content),
                    'has_skip': has_skip,
                    'full_block': '\n'.join(full_func_block)
                }
                current_func = None
                has_skip = False
                full_func_block = []
        if line.strip().startswith('@'):
            if current_func is None:
                if len(full_func_block) > 0:
                    full_func_block.append(line)
                else:
                    full_func_block = [line]
            if line.strip().startswith('@pytest.mark.skip'):
                has_skip = True
        elif line.strip().startswith('def test_'):
            current_func = line.strip().split('def ')[1].split('(')[0]
            full_func_block.append(line)
            func_content = []
        else:
            func_content.append(line)
            full_func_block.append(line)
        i += 1

    if current_func:
        existing_functions[current_func] = {
            'body': '\n'.join(func_content),
            'has_skip': has_skip,
            'full_block': '\n'.join(full_func_block)
        }

    test_case_names = [f"test_{case.label.replace(' ', '_')}" for case in test_cases]

    update_template = Template("""import pytest

{% for case in test_cases -%}
@pytest.mark.project_id("{{ project_id }}")
@pytest.mark.meta(id="{{ case.id }}", scenario="{{ case.description }}", steps="{{ case.steps }}", prerequisites="{{ case.prerequisites }}")
{%- set func_name = "test_" ~ case.label.replace(" ", "_") -%}
{%- for decorator in case.generate_parametrize_decorators() %}
{{ decorator }}
{%- endfor %}
{%- if (func_name in existing_functions and existing_functions[func_name]['has_skip']) or (func_name not in existing_functions) %}
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
{%- for func_name, func_info in existing_functions.items() %}
{%- if func_name not in test_case_names %}
{{ func_info['full_block'] }}

{% endif -%}
{%- endfor -%}""")

    content = update_template.render(
        test_cases=test_cases,
        project_id=test_generator.project_id,
        existing_functions=existing_functions,
        test_case_names=test_case_names
    )

    file_path.write_text(content, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="Check test coverage against reqif file")
    parser.add_argument('reqif_path', type=str, help="Path to the .reqif file")
    parser.add_argument('tests_path', type=str, help="Path to the tests directory")

    args = parser.parse_args()

    reqif_path = Path(args.reqif_path)
    tests_path = Path(args.tests_path)

    ignore_file_path = tests_path / '.typhoonignore'
    matches = None
    if ignore_file_path.exists():
        matches = parse_gitignore(ignore_file_path, base_dir=tests_path)

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

    update_tests(test_generator, matches)
