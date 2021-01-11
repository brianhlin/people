import pytest
from merge import compute_merge, Append, Replace, merge_people, merge_contact_details


@pytest.mark.parametrize(
    "a, b, output",
    [
        # no diff
        ({"a": "one", "b": "two"}, {"a": "one", "b": "two"}, []),
        # simple difference
        ({"a": "one", "b": "two"}, {"a": "bad", "b": "two"}, [Replace("a", "one", "bad")]),
        # missing key from first
        ({"a": "one"}, {"a": "one", "b": "two"}, [Replace("b", None, "two")]),
        # missing key from second
        ({"a": "one", "b": "two"}, {"a": "one"}, []),
    ],
)
def test_compute_merge_simple(a, b, output):
    assert compute_merge(a, b) == output


@pytest.mark.parametrize(
    "a, b, output",
    [
        # no diff
        ({"a": {"b": "c"}}, {"a": {"b": "c"}}, []),
        # nothing new on right
        ({"a": {"b": "c"}}, {"a": {}}, []),
        # replace
        ({"a": {}}, {"a": {"b": "c"}}, [Replace("a.b", None, "c")]),
    ],
)
def test_compute_merge_nested(a, b, output):
    assert compute_merge(a, b) == output


@pytest.mark.parametrize(
    "a, b, output",
    [
        # no errors
        ({"a": [{"b": 1}, {"c": 2}]}, {"a": [{"b": 1}, {"c": 2}]}, []),
        # no errors - just different order
        ({"a": [{"b": 1}, {"c": 2}]}, {"a": [{"c": 2}, {"b": 1}]}, []),
        # extra item left
        ({"a": [{"b": 1}, {"c": 2}, {"d": 3}]}, {"a": [{"b": 1}, {"c": 2}]}, []),
        # extra item right
        (
            {"a": [{"b": 1}, {"c": 2}]},
            {"a": [{"b": 1}, {"c": 2}, {"d": 3}]},
            [Append("a", {"d": 3})],
        ),
    ],
)
def test_compute_merge_list(a, b, output):
    assert compute_merge(a, b) == output


@pytest.mark.parametrize(
    "a, b, keep_both, output",
    [
        # discard id
        ({"id": "1"}, {"id": "2"}, False, []),
        # keep id
        (
            {"id": "1"},
            {"id": "2"},
            True,
            [Append("other_identifiers", {"identifier": "2", "scheme": "openstates"})],
        ),
        # append name
        (
            {"name": "A"},
            {"name": "B"},
            True,
            [Append("other_names", {"name": "A"}), Replace("name", "A", "B")],
        ),
    ],
)
def test_compute_merge_special_cases(a, b, keep_both, output):
    assert compute_merge(a, b, keep_both_ids=keep_both) == output


@pytest.mark.parametrize(
    "old, new, expected",
    [
        # no changes
        ({"name": "Anna"}, {"name": "Anna"}, {"name": "Anna"}),
        # field only in old
        (
            {"name": "Anna", "birth_date": "1980"},
            {"name": "Anna"},
            {"name": "Anna", "birth_date": "1980"},
        ),
        # field only in new
        (
            {"name": "Anna"},
            {"name": "Anna", "birth_date": "1980"},
            {"name": "Anna", "birth_date": "1980"},
        ),
        # special: name field differs
        (
            {"name": "Bob"},
            {"name": "Robert"},
            {"name": "Robert", "other_names": [{"name": "Bob"}]},
        ),
    ],
)
def test_simple_merge(old, new, expected):
    assert merge_people(old, new) == expected


@pytest.mark.parametrize(
    "old, new, expected",
    [
        # more in first list
        (
            {"other_names": [{"name": "A"}, {"name": "B"}]},
            {"other_names": [{"name": "A"}]},
            {"other_names": [{"name": "A"}, {"name": "B"}]},
        ),
        # more in second list
        (
            {"other_names": [{"name": "A"}]},
            {"other_names": [{"name": "A"}, {"name": "B"}]},
            {"other_names": [{"name": "A"}, {"name": "B"}]},
        ),
        # each list is unique
        (
            {"other_names": [{"name": "A"}]},
            {"other_names": [{"name": "B"}]},
            {"other_names": [{"name": "A"}, {"name": "B"}]},
        ),
    ],
)
def test_list_merge(old, new, expected):
    # note that keep doesn't matter for these
    assert merge_people(old, new, None) == expected


@pytest.mark.parametrize(
    "old, new, expected",
    [
        # simplest case
        (
            {"id": "ocd-person/1"},
            {"id": "ocd-person/2"},
            {
                "id": "ocd-person/1",
                "other_identifiers": [{"scheme": "openstates", "identifier": "ocd-person/2"}],
            },
        ),
        # already has identifiers
        (
            {
                "id": "ocd-person/1",
                "other_identifiers": [{"scheme": "openstates", "identifier": "ocd-person/0"}],
            },
            {"id": "ocd-person/2"},
            {
                "id": "ocd-person/1",
                "other_identifiers": [
                    {"scheme": "openstates", "identifier": "ocd-person/0"},
                    {"scheme": "openstates", "identifier": "ocd-person/2"},
                ],
            },
        ),
    ],
)
def test_keep_both_ids(old, new, expected):
    assert merge_people(old, new, keep_both_ids=True) == expected


@pytest.mark.parametrize(
    "old, new",
    [
        (
            [{"note": "Capitol Office", "voice": "123"}],
            [{"note": "Capitol Office", "voice": "123"}],
        ),
        (
            [
                {"note": "Capitol Office", "voice": "123"},
                {"note": "District Office", "address": "abc"},
            ],
            [
                {"note": "Capitol Office", "voice": "123"},
                {"note": "District Office", "address": "abc"},
            ],
        ),
    ],
)
def test_merge_contact_details_no_change(old, new):
    assert merge_contact_details(old, new) is None


@pytest.mark.parametrize(
    "old, new, expected",
    [
        # replace a value with a new one
        (
            [{"note": "Capitol Office", "voice": "123"}],
            [{"note": "Capitol Office", "voice": "456"}],
            [{"note": "Capitol Office", "voice": "456"}],
        ),
        # merge two partial records
        (
            [{"note": "Capitol Office", "voice": "123"}],
            [{"note": "Capitol Office", "fax": "456"}],
            [{"note": "Capitol Office", "voice": "123", "fax": "456"}],
        ),
        # merge two offices into a single list
        (
            [{"note": "Capitol Office", "voice": "123"}],
            [{"note": "District Office", "voice": "456"}],
            [
                {"note": "Capitol Office", "voice": "123"},
                {"note": "District Office", "voice": "456"},
            ],
        ),
    ],
)
def test_merge_contact_details_changes(old, new, expected):
    assert merge_contact_details(old, new) == expected


def test_merge_extras():
    # replace was adding a key like extras._internal_id
    old = {"extras": {"_internal_id": 123}}
    new = {}
    expected = old.copy()
    assert merge_people(new, old) == expected
