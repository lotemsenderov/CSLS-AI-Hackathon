from fields import FIELDS

import search


def test_fields_is_nonempty_list_of_unique_strings():
    assert isinstance(FIELDS, list)
    assert len(FIELDS) > 0
    assert all(isinstance(f, str) and f for f in FIELDS)
    assert len(FIELDS) == len(set(FIELDS))


def test_every_conference_field_is_in_the_taxonomy():
    conferences = search.load_conferences()
    unknown = {c["field"] for c in conferences} - set(FIELDS)
    assert not unknown, f"conferences use fields not in FIELDS: {unknown}"


def test_every_taxonomy_field_has_at_least_one_conference():
    conferences = search.load_conferences()
    covered = {c["field"] for c in conferences}
    uncovered = set(FIELDS) - covered
    assert not uncovered, f"fields in the dropdown with zero conferences: {uncovered}"