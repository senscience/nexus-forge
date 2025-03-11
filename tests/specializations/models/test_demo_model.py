#
# Blue Brain Nexus Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Blue Brain Nexus Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Blue Brain Nexus Forge. If not, see <https://choosealicense.com/licenses/lgpl-3.0/>.
import pytest


@pytest.fixture
def valid_person(valid_resource):
    valid_resource.name = "John Doe"
    return valid_resource


@pytest.fixture
def validated_resource(model, valid_person):
    model.validate(valid_person, execute_actions_before=False, type_="Person")
    assert valid_person._validated is True
    return valid_person


@pytest.mark.parametrize("data, msg", [
    ("valid_resource", None),
    ("invalid_resource", "ValidationError: name is missing"),
])
def test_validate(model, data, msg, request):
    data = request.getfixturevalue(data)
    try:
        model.validate(data, execute_actions_before=False, type_="Person")
    except Exception as e:
        assert str(e) == msg


@pytest.mark.parametrize("exception_message", ["Exception: exception raised"])
def test_validate_exception(monkeypatch, model, valid_resource, exception_message):
    def _validate_one(_, x, type_: str, inference: str):
        raise Exception("exception raised")

    monkeypatch.setattr(
        "kgforge.specializations.models.demo_model.DemoModel._validate_one",
        _validate_one,
    )
    try:
        model.validate(valid_resource, execute_actions_before=False, type_="Person")
    except Exception as e:
        assert str(e) == exception_message


@pytest.mark.parametrize("modified", [False, True])
def test_modify_resource(validated_resource, modified):
    if modified:
        validated_resource.name = "Jane Doe"
        validated_resource._validated = False
    assert validated_resource._validated == (not modified)


@pytest.mark.parametrize("data, expected_status", [
    ("valid_resource", True),
    ("invalid_resource", False),
])
def test_validated_status(data, expected_status, request):
    data = request.getfixturevalue(data)
    assert data._validated == expected_status
