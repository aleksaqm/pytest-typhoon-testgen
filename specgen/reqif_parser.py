import re
import json
from xml.etree import ElementTree


class TreeNode:
    def __init__(self, identifier, label, description, node_type, priority=None, status=None,
                 steps=None, prerequisites=None, test_data=None, expected_results=None, parameters=None):
        self.id = identifier
        self.label = label
        self.description = description
        self.type = node_type
        self.priority = priority
        self.status = status
        self.steps = steps if steps is not None else []
        self.prerequisites = prerequisites if prerequisites is not None else []
        self.test_data = test_data if test_data is not None else []
        self.expected_results = expected_results if expected_results is not None else []
        self.parameters = parameters if parameters is not None else []
        self.children = []
        self.parent = None

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def __repr__(self):
        return f"TreeNode({self.id}, {self.label}, {self.description}, {self.priority}, {self.status}, steps={self.steps}, parameters={self.parameters}, children={len(self.children)})"


class ReqifParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.namespace = ''
        self.spec_objects_map = {}

    def parse_reqif(self):
        try:
            tree = ElementTree.parse(self.file_path)
            root = tree.getroot()
            self.namespace = self._get_namespace(root)

            core_content = root.find(f".//{{{self.namespace}}}CORE-CONTENT")
            if core_content is None:
                raise ValueError("CORE-CONTENT not found in the ReqIF file")

            content = core_content.find(f"{{{self.namespace}}}REQ-IF-CONTENT")
            if content is None:
                raise ValueError("REQ-IF-CONTENT not found")

            spec_objects = content.find(f"{{{self.namespace}}}SPEC-OBJECTS")
            if spec_objects:
                self._parse_spec_objects(spec_objects)
            else:
                raise ValueError("No SPEC-OBJECTS found in this file.")

            specifications = content.find(f"{{{self.namespace}}}SPECIFICATIONS")
            if specifications:
                return self._parse_hierarchy(specifications)
            else:
                raise ValueError("No SPECIFICATIONS found in this file.")

        except Exception as e:
            print(f"Error parsing ReqIF file: {e}")
            return []

    def _parse_spec_objects(self, spec_objects_element):
        for spec_object in spec_objects_element.findall(f"{{{self.namespace}}}SPEC-OBJECT"):
            identifier = spec_object.get("IDENTIFIER", "")
            spec_type = spec_object.find(f"{{{self.namespace}}}TYPE/{{{self.namespace}}}SPEC-OBJECT-TYPE-REF")
            spec_type = spec_type.text if spec_type is not None else ""

            values = spec_object.find(f"{{{self.namespace}}}VALUES")
            label = ""
            description = ""
            priority = ""
            status = ""
            steps = []
            prerequisites = []
            test_data = []
            expected_results = []
            parameters = []

            if values:
                for attr_value in values.findall(f"{{{self.namespace}}}ATTRIBUTE-VALUE-STRING"):
                    definition_ref = attr_value.find(
                        f"{{{self.namespace}}}DEFINITION/{{{self.namespace}}}ATTRIBUTE-DEFINITION-STRING-REF").text
                    the_value = attr_value.get("THE-VALUE", "")

                    if definition_ref == "_Requirement_Title" or definition_ref == "_Test_Title" or definition_ref == "_TestCase_Title":
                        label = the_value
                    elif definition_ref == "_Requirement_Description" or definition_ref == "_Test_Description" or definition_ref == "_TestCase_Description":
                        description = the_value
                    elif definition_ref == "_Priority":
                        priority = the_value
                    elif definition_ref == "_Status":
                        status = the_value
                    elif definition_ref == "_Steps":
                        steps = the_value.split(",")
                    elif definition_ref == "_Prerequisites":
                        prerequisites = the_value.split(",")
                    elif definition_ref == "_TestData":
                        test_data = the_value.split(",")
                    elif definition_ref == "_ExpectedResults":
                        expected_results = the_value.split(",")
                    elif definition_ref == "_Parameters":
                        try:
                            parameters = json.loads(the_value)
                        except json.JSONDecodeError as e:
                            print(f"Error decoding parameters JSON: {e}")

            node = TreeNode(
                identifier,
                label,
                description,
                spec_type,
                priority,
                status,
                steps=steps,
                prerequisites=prerequisites,
                test_data=test_data,
                expected_results=expected_results,
                parameters=parameters
            )

            self.spec_objects_map[identifier] = node

    def _parse_hierarchy(self, specifications_element):
        nodes = []
        for specification in specifications_element.findall(f"{{{self.namespace}}}SPECIFICATION"):
            children = specification.find(f"{{{self.namespace}}}CHILDREN")
            if children:
                for hierarchy in children.findall(f"{{{self.namespace}}}SPEC-HIERARCHY"):
                    self._build_hierarchy(hierarchy, None, nodes)
        return nodes

    def _build_hierarchy(self, hierarchy, parent, nodes):
        object_ref = hierarchy.find(f"{{{self.namespace}}}OBJECT/{{{self.namespace}}}SPEC-OBJECT-REF")
        object_ref = object_ref.text if object_ref is not None else None

        if object_ref and object_ref in self.spec_objects_map:
            node = self.spec_objects_map[object_ref]

            if parent:
                parent.add_child(node)
            else:
                nodes.append(node)

            children = hierarchy.find(f"{{{self.namespace}}}CHILDREN")
            if children:
                for child_hierarchy in children.findall(f"{{{self.namespace}}}SPEC-HIERARCHY"):
                    self._build_hierarchy(child_hierarchy, node, nodes)

    @staticmethod
    def _get_namespace(element):
        match = re.match(r'\{(.*)}', element.tag)
        return match.group(1) if match else ''

