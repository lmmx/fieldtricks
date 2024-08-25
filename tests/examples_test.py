from pytest import importorskip


def test_nested():
    importorskip("examples.nested").check()


def test_field_extrusion():
    importorskip("examples.field_extrusion").check()
