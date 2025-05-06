import pytest
import allure


def pytest_collection_modifyitems(items):
    for item in items:
        meta_marker = item.get_closest_marker("meta")
        if meta_marker:
            item.user_properties.append(("internal_meta", meta_marker.kwargs))
            item.own_markers = [m for m in item.own_markers if m.name != "meta"]


def pytest_runtest_setup(item):
    for name, value in item.user_properties:
        if name == "internal_meta":
            meta = value
            allure.dynamic.id(meta.get("id", ""))
            name = meta.get("name", "")
            if name != "":
                allure.dynamic.title(meta.get("name"))
            # allure.dynamic.label("name", meta.get("name", ""))
            allure.dynamic.label("scenario", meta.get("scenario", ""))
            allure.dynamic.label("steps", meta.get("steps", []))
            allure.dynamic.label("prerequisites", meta.get("prerequisites", []))

