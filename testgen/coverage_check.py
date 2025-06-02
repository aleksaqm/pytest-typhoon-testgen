import argparse
import ast
import json
import os
import sys
from pathlib import Path
from typing import Dict, Set, List, Optional
from dataclasses import dataclass

from gitignore_parser import parse_gitignore

from testgen import TreeNode

from testgen.reqif_parser import ReqifParser
from testgen.generator import sanitize_name


@dataclass
class TestStructure:
    folders: Set[str]
    files: Set[str]
    test_cases: Dict[str, Dict]
    skipped_test_cases: Optional[list]


@dataclass
class Difference:
    missing_folders: Set[str]
    extra_folders: Set[str]
    missing_files: Set[str]
    extra_files: Set[str]
    missing_tests: Dict[str, Dict]
    extra_tests: Dict[str, Dict]
    modified_tests: Dict[str, Dict]


def get_existing_structure(tests_path: Path) -> TestStructure:
    folders = set()
    files = set()
    test_cases = {}
    skipped_test_cases = []
    for root, dirs, filenames in os.walk(tests_path):
        rel_path = Path(root).relative_to(tests_path)
        if str(rel_path) != '.':
            folders.add(str(rel_path))
        for filename in filenames:
            if filename.startswith('test_') and filename.endswith('.py'):
                abs_file_path = Path(root) / filename
                rel_file_path = abs_file_path.relative_to(tests_path)
                files.add(str(rel_file_path))
                test_cases[str(rel_file_path)], new_skipped_test_cases = parse_test_file(Path(abs_file_path), rel_file_path)
                skipped_test_cases += new_skipped_test_cases

    return TestStructure(folders=folders, files=files, test_cases=test_cases, skipped_test_cases=skipped_test_cases)


def get_expected_structure(reqif_path: str) -> TestStructure:
    parser = ReqifParser(reqif_path)
    data = parser.parse_reqif()

    folders = set()
    files = set()
    test_cases = {}

    def process_node(node, current_path: Path):
        if node.type == "_RequirementType":
            folder_name = sanitize_name(node.label)
            folders.add(str(current_path / folder_name))
            for child in node.children:
                process_node(child, current_path / folder_name)
        elif node.type == "_TestType":
            file_name = f"test_{sanitize_name(node.label)}.py"
            file_path = str(current_path / file_name)
            files.add(file_path)
            test_cases[file_path] = {
                sanitize_name(child.label): get_test_params(child)
                for child in node.children
                if child.type == "_TestCaseType"
            }

    for node in data:
        process_node(node, Path())

    return TestStructure(folders=folders, files=files, test_cases=test_cases, skipped_test_cases=None)


def parse_test_file(file_path: Path, rel_file_path: Path) -> (Dict[str, Dict], []):
    test_cases = {}
    skipped_cases = []
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            params = {}
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if (
                        isinstance(decorator.func, ast.Attribute) and
                        isinstance(decorator.func.value, ast.Attribute) and
                        isinstance(decorator.func.value.value, ast.Name) and
                        decorator.func.value.value.id == 'pytest' and
                        decorator.func.value.attr == 'mark'
                    ):
                        marker_name = decorator.func.attr
                        if marker_name == 'meta':
                            for keyword in decorator.keywords:
                                try:
                                    params[keyword.arg] = ast.literal_eval(keyword.value)
                                except Exception:
                                    params[keyword.arg] = None
                        elif marker_name == 'parametrize':
                            if decorator.args:
                                param_name = ast.literal_eval(ast.unparse(decorator.args[0]))
                                try:
                                    param_values = ast.literal_eval(ast.unparse(decorator.args[1]))
                                except:
                                    param_values = []
                                if 'parameters' not in params:
                                    params['parameters'] = {}
                                params['parameters'][param_name] = param_values
                        elif marker_name == 'skip':
                            # params['skipped'] = True
                            skipped_cases.append(str(rel_file_path) + "\\" + node.name[5:])
                            # if params.get('id'):
                            #     skipped_cases.append(str(file_path) + "\\" + node.name[5:])


            test_cases[node.name[5:]] = params
    return test_cases, skipped_cases


def get_test_params(test_case_node : TreeNode) -> Dict:
    parameters = {}
    for parameter in test_case_node.parameters:
        parameters[parameter.name] = parameter.value

    return {
        'id': test_case_node.id,
        'name': test_case_node.label,
        'scenario': test_case_node.description,
        'steps': test_case_node.steps,
        'prerequisites': test_case_node.prerequisites,
        'parameters': parameters
    }


def compare_structures(existing: TestStructure, expected: TestStructure) -> Difference:
    def normalize_value(value):
        if isinstance(value, str):
            try:
                if value.startswith('[') and value.endswith(']'):
                    return eval(value)
            except:
                pass
        return value

    modified_tests = {}
    for file in expected.files & existing.files:
        file_changes = {}
        existing_tests_by_id = {
            test_data.get('id'): (name, test_data)  # 'name' is the function name (dict key)
            for name, test_data in existing.test_cases.get(file, {}).items()
            if test_data.get('id') is not None
        }
        expected_tests_by_id = {
            test_data.get('id'): (name, test_data)  # 'name' is the function name (dict key)
            for name, test_data in expected.test_cases[file].items()
            if test_data.get('id') is not None
        }

        for test_id in set(existing_tests_by_id.keys()) & set(expected_tests_by_id.keys()):
            existing_name, existing_params = existing_tests_by_id[test_id]
            expected_name, expected_params = expected_tests_by_id[test_id]

            param_changes = {}

            if existing_name != expected_name:
                param_changes['name'] = (existing_name, expected_name)

            for param in set(existing_params) | set(expected_params):
                if param != 'id' and param != 'name':
                    existing_value = normalize_value(existing_params.get(param))
                    expected_value = normalize_value(expected_params.get(param))

                    if existing_value != expected_value:
                        param_changes[param] = (existing_value, expected_value)

            existing_params_set = set(existing_params.get('parameters', []))
            expected_params_set = set(expected_params.get('parameters', []))
            if existing_params_set != expected_params_set:
                param_changes['parameters'] = (
                    sorted(list(existing_params_set)),
                    sorted(list(expected_params_set))
                )

            if param_changes:
                file_changes[test_id] = param_changes

        if file_changes:
            modified_tests[file] = file_changes

    return Difference(
        missing_folders=expected.folders - existing.folders,
        extra_folders=existing.folders - expected.folders,
        missing_files=expected.files - existing.files,
        extra_files=existing.files - expected.files,
        missing_tests={
            file: {name: expected.test_cases[file][name]
                   for name in expected.test_cases[file].keys()
                   if file not in existing.test_cases or
                   name not in existing.test_cases.get(file, {})}
            for file in expected.test_cases
        },
        extra_tests={
            file: {name: existing.test_cases[file][name]
                   for name in existing.test_cases[file].keys()
                   if file not in expected.test_cases or
                   name not in expected.test_cases[file]}
            for file in existing.files
        },

        modified_tests=modified_tests,
    )


def main():
    parser = argparse.ArgumentParser(description="Check test coverage against reqif file")
    parser.add_argument('reqif_path', type=str, help="Path to the .reqif file")
    parser.add_argument('tests_path', type=str, help="Path to the tests directory")
    parser.add_argument('ignore_file', type=str, help="Path to the ignore file", nargs='?', default=None,)


    args = parser.parse_args()

    tests_path = Path(args.tests_path)
    if not tests_path.exists():
        print(f"Error: Tests path '{tests_path}' does not exist")
        return

    matches = None
    if args.ignore_file:
        ignore_file = Path(args.ignore_file)
        if ignore_file.exists():
            ignore_dir = ignore_file.parent
            print(ignore_file)
            matches = parse_gitignore(ignore_file, base_dir=ignore_dir)

    existing = get_existing_structure(tests_path)
    expected = get_expected_structure(args.reqif_path)

    differences = compare_structures(existing, expected)
    diff_dict = {
        'missing_folders': list(differences.missing_folders),
        'extra_folders': list(differences.extra_folders),
        'missing_files': list(differences.missing_files),
        'extra_files': list(differences.extra_files),
        'missing_tests': differences.missing_tests,
        'extra_tests': differences.extra_tests,
        'modified_tests': differences.modified_tests,
        'skipped_tests': existing.skipped_test_cases,
    }
    print(json.dumps(diff_dict))
    sys.exit(0)
