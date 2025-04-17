import re
import xml.etree.ElementTree as ET

class ReqifParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.namespace = ''

    def _parse_spec_object(self, spec_object):
        obj_data = {}

        for elem in spec_object:
            if elem.tag.endswith("CHILDREN"):
                obj_data["CHILDREN"] = [self._parse_spec_object(child) for child in elem]
            elif elem.tag.endswith("PARAMETERS"):
                obj_data["PARAMETERS"] = self._parse_params(elem)
            else:
                obj_data[elem.tag.split("}")[-1]] = elem.text

        return obj_data

    def parse_reqif(self):
        parsed_data = []

        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()
            self.namespace = self._get_namespace(root)

            core_content = root.find(f".//{{{self.namespace}}}CORE-CONTENT")
            if core_content is not None:
                specifications = core_content.find(f"{{{self.namespace}}}SPECIFICATIONS")
                if specifications is not None:
                    for spec_object in specifications.findall(
                            f"{{{self.namespace}}}SPEC-OBJECT"):
                        parsed_object = self._parse_spec_object(spec_object)
                        parsed_data.append(parsed_object)
            else:
                print("CORE-CONTENT not found in the file.")

        except Exception as e:
            print(f"Error parsing the file: {e}")

        return parsed_data

    def _get_namespace(self, element):
        match = re.match(r'\{(.*)}', element.tag)
        return match.group(1) if match else ''

    def _parse_params(self, parameters_element):
        parameters = []
        for parameter in parameters_element.findall(f"{{{self.namespace}}}PARAMETER"):
            param_data = {
                "name": parameter.find(f"{{{self.namespace}}}NAME").text,
                "type": parameter.find(f"{{{self.namespace}}}TYPE").text,
                "value": parameter.find(f"{{{self.namespace}}}VALUE").text,
            }
            parameters.append(param_data)
        return parameters