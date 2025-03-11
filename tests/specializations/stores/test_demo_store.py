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
from kgforge.specializations.stores.demo_store import DemoStore
from tests.conftest import check_report, do


@pytest.fixture
def store():
    return DemoStore()


@pytest.fixture
def registered_resource(store, valid_resource):
    store.register(valid_resource)
    assert valid_resource._synchronized is True
    return valid_resource


@pytest.fixture
def registered_resources(store, valid_resources):
    store.register(valid_resources)
    for x in valid_resources:
        assert x._synchronized is True
        assert x._store_metadata == {'version': 1, 'deprecated': False}
    return valid_resources


@pytest.mark.parametrize("data, msg", [
    ("valid_resource", None),
    ("invalid_resource", "name is missing"),
])
def test_register(store, data, msg, request):
    data = request.getfixturevalue(data)
    try:
        store.register(data)
    except Exception as e:
        assert str(e) == msg


@pytest.mark.parametrize("exception_message", ["exception raised"])
def test_register_exception(monkeypatch, store, valid_resource, exception_message):
    def _register_one(_, x, schema_id):
        raise Exception("exception raised")

    monkeypatch.setattr(
        "kgforge.specializations.stores.demo_store.DemoStore._register_one",
        _register_one,
    )
    try:
        store.register(valid_resource)
    except Exception as e:
        assert str(e) == exception_message


@pytest.mark.parametrize("data, expected_metadata", [
    ("registered_resource", "{'version': 1, 'deprecated': False}"),
])
def test_check_metadata(data, expected_metadata, request):
    data = request.getfixturevalue(data)
    def fun(x): assert str(x._store_metadata) == expected_metadata
    do(fun, data)
