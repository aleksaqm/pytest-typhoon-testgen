import json
from pathlib import Path

from testgen import upload_allure_report
from testgen.settings import get_settings

def get_project_id(allure_name):
    path = Path(f"./{allure_name}")
    project_id = ""
    if path.exists():
        path = path.joinpath("data", "test-cases")
        if path.exists():
            for file in path.iterdir():
                if file.is_file() and file.suffix == ".json":
                    file_text = file.read_text(encoding="utf-8")
                    data = json.loads(file_text)
                    labels = data.get("labels", "")
                    for label in labels:
                        if label.get("name") == "project_id":
                            project_id = label.get("value")
                            break
                    if project_id == "":
                        continue

                    project_id += '.zip'
                    break
    else:
        print("Report not found")
        raise Exception("Report not found")

    if project_id == "":
        project_id = "report.zip"

    return project_id

def main():
    zip_name = get_project_id(get_settings().ALLURE_RESULTS_DIR)
    allure_results_dir = Path(get_settings().ALLURE_RESULTS_DIR)
    upload_allure_report(zip_name, get_settings().SERVER_URL, allure_results_dir)