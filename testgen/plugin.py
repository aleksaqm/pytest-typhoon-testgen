import os
import zipfile
from pathlib import Path
import requests
import pytest
import allure
from .settings import get_settings

global zip_file_name

def pytest_addoption(parser):
    group = parser.getgroup('reporting')
    group.addoption(
        '--report',
        action='store_true',
        default=False,
        help='Enable the reporting plugin'
    )


@pytest.hookimpl()
def pytest_sessionstart(session):
    if session.config.getoption("report"):
        global zip_file_name
        zip_file_name = ""

def pytest_collection_modifyitems(items):
    if not items[0].config.getoption('report'):
        return
    for item in items:
        meta_marker = item.get_closest_marker("meta")
        project_id_marker = item.get_closest_marker("project_id")
        if meta_marker:
            item.user_properties.append(("internal_meta", meta_marker.kwargs))
            item.own_markers = [m for m in item.own_markers if m.name != "meta"]
        if project_id_marker:
            item.user_properties.append(("project_id", project_id_marker.args[0]))

def pytest_runtest_setup(item):
    if not item.config.getoption('report'):
        return
    global zip_file_name
    for name, value in item.user_properties:
        if name == "internal_meta":
            meta = value
            identification = meta.get("id", "")
            allure.dynamic.id(identification)
            name = meta.get("name", "")
            if name != "":
                allure.dynamic.title(meta.get("name"))
            # allure.dynamic.label("name", meta.get("name", ""))
            allure.dynamic.label("scenario", meta.get("scenario", ""))
            allure.dynamic.label("steps", meta.get("steps", []))
            allure.dynamic.label("prerequisites", meta.get("prerequisites", []))
        if name == "project_id":
            project_id = value
            allure.dynamic.label("project_id", project_id)
            zip_file_name = project_id

@pytest.hookimpl()
def pytest_sessionfinish(session, exitstatus):
    if not session.config.getoption('report'):
        return
    global zip_file_name
    allure_results_dir = Path(get_settings().ALLURE_RESULTS_DIR)
    zip_file_name += ".zip"
    if allure_results_dir.exists() and allure_results_dir.is_dir():
        with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(allure_results_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, allure_results_dir)
                    zipf.write(file_path, arcname)
        print(f"Successfully created ZIP file: {zip_file_name}")
    else:
        print("Allure results directory does not exist or is not a valid directory.")
        return

    server_url = get_settings().SERVER_URL + "/upload"
    try:
        with open(zip_file_name, 'rb') as f:
            response = requests.post(server_url, files={'file': f}, timeout=30)
        if response.status_code == 200:
            print("Allure ZIP file successfully uploaded to the server.")
        else:
            print(f"Failed to upload file. Server responded with status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while uploading the file: {e}")


