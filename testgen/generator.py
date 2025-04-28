import re
from copy import deepcopy
from typing import List
from jinja2 import Template
from testgen.reqif_parser import TreeNode
from pathlib import Path


def sanitize_name(name):
    return re.sub(r'\W|^(?=\d)', '_', name)


def generate_test_file(path: Path, test_cases: List[TreeNode], parent_requirements: List[str] = None):
    parent_requirements = parent_requirements or []
    template = Template("""
import pytest

{% for case in test_cases -%}
@pytest.mark.requirements(["{{ parent_requirements | join('", "') }}"])
@pytest.mark.meta(id="{{ case.id }}", name="{{ case.label }}", scenario="{{ case.description }}", steps="{{ case.steps }}", prerequisites="{{ case.prerequisites }}")
{% for decorator in case.generate_parametrize_decorators() -%}
{{ decorator }}
{% endfor -%}
def test_{{ case.label }}():
    # TODO: Implement test
    pass

{% endfor -%}
""")
    content = template.render(test_cases=test_cases, parent_requirements=parent_requirements)
    path.write_text(content, encoding="utf-8")


class TestGenerator:
    def __init__(self, nodes: list[TreeNode], path : Path):
        self.nodes = nodes
        self.path = path

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
            parent_requirements : list[str] = []
            node_copy = deepcopy(node)
            while node_copy.parent is not None:
                parent_requirements.append(node_copy.parent.label)
                node_copy = node_copy.parent

            generate_test_file(file_path, test_cases, parent_requirements)
