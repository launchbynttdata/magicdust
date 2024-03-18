import os
import tempfile

import pytest

from libs.terraform.module_search import module_search


def create_mock_module(path):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "main.tf"), "a") as main_file:
        main_file.write("")


@pytest.fixture
def mock_terraform_module():
    # Module: Any folder with a 'main.tf'
    module = tempfile.mkdtemp()

    # Define nested modules
    submodules = [
        os.path.join(module, "modules", "rabbit"),
        os.path.join(module, "modules", "shark"),
        os.path.join(module, "examples", "main"),
    ]

    # Cached Dependency: Any module within a hidden folder
    cached_dependencies = [os.path.join(module, ".terraform", "lion")]

    # Initialize modules
    for m in [module] + submodules + cached_dependencies:
        create_mock_module(m)

    return {
        "module": module,
        "submodules": submodules,
        "cached_dependencies": cached_dependencies,
    }


def test_raises_error_without_existing_path():
    with pytest.raises(FileNotFoundError) as expectation:
        module_search("")
    assert expectation


def test_raises_error_without_a_folder():
    with pytest.raises(NotADirectoryError) as expectation:
        handler, name = tempfile.mkstemp()
        module_search(name)
    assert expectation


def test_returns_array_with_terraform_module_given_terraform_module(
    mock_terraform_module,
):
    result = module_search(mock_terraform_module["module"])
    assert mock_terraform_module["module"] in result


def test_returns_array_including_nested_modules_given_directory_with_nested_modules(
    mock_terraform_module,
):
    result = module_search(mock_terraform_module["module"])
    for submodule in mock_terraform_module["submodules"]:
        assert submodule in result


def test_returns_array_without_hidden_modules_given_directory_with_hidden_modules(
    mock_terraform_module,
):
    result = module_search(mock_terraform_module["module"])
    for hidden_module in mock_terraform_module["cached_dependencies"]:
        assert not hidden_module in result
