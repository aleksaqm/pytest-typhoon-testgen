import re
from typing import List
from jinja2 import Template
from testgen.reqif_parser import TreeNode
from testgen.reqif_parser import ReqifParser
import argparse
import os
from pathlib import Path


def sanitize_name(name):
    name.replace(" ", "_")
    return re.sub(r'\W|^(?=\d)', '_', name)


class TestGenerator:
    def __init__(self, nodes: list[TreeNode], path : Path, project_id: str):
        self.nodes = nodes
        self.path = path
        self.project_id = project_id

    def generate(self):
        for node in self.nodes:
            self.walk_tree(node, self.path)

    def walk_tree(self,node : TreeNode, current_path: Path):
        if node.type == "_RequirementType":
            new_dir = current_path / sanitize_name(node.label)
            new_dir.mkdir(parents=True, exist_ok=True)
            for child in node.children:
                self.walk_tree(child, new_dir)
        elif node.type == "_TestType":
            file_path = current_path / f"test_{sanitize_name(node.label)}.py"
            test_cases = []
            for child in node.children:
                if child.type == "_TestCaseType":
                    test_cases.append(child)
            # parent_requirements : list[str] = []
            # node_copy = deepcopy(node)
            # while node_copy.parent is not None:
            #     parent_requirements.append(node_copy.parent.id)
            #     node_copy = node_copy.parent

            self.generate_test_file(file_path, test_cases)

    def generate_test_file(self, path: Path, test_cases: List[TreeNode]):

        template = Template("""
import pytest

{% for case in test_cases -%}
@pytest.mark.project_id("{{ project_id }}")
@pytest.mark.meta(id="{{ case.id }}", name="{{ case.label }}", scenario="{{ case.description }}", steps="{{ case.steps }}", prerequisites="{{ case.prerequisites }}")
{% for decorator in case.generate_parametrize_decorators() -%}
{{ decorator }}
{% endfor -%}
@pytest.mark.skip(reason="Not implemented yet.")
def test_{{ case.label.replace(" ", "_") }}({{ case.get_parameters_names() }}):
    # TODO: Implement test and dont forget to delete @pytest.mark.skip(reason="Not implemented yet.") decorator.
    pass

{% endfor -%}
    """)
        content = template.render(test_cases=test_cases, project_id=self.project_id)
        path.write_text(content, encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="Parse a .reqif file and generate pytest tests.")
    parser.add_argument('file_path', type=str, help="Path to the .reqif file")
    parser.add_argument('output_path', type=str, nargs='?', default=os.getcwd(),
                        help="Directory where tests will be generated (default: current working directory)")

    args = parser.parse_args()

    # print("Parsing .reqif file:", args.file_path)
    # print("Generating tests into:", args.output_path)

    reqif_parser = ReqifParser(args.file_path)
    data = reqif_parser.parse_reqif()
    header_data = reqif_parser.parse_header_data()

    # print("Requirements:", data)
    start_path = Path(args.output_path)
    test_generator = TestGenerator(data, start_path, header_data["project_id"])
    test_generator.generate()
