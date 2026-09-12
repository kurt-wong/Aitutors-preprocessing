# -*- coding: utf-8 -*-
"""extract_json 边界契约(固化 R24-C2)。"""
import pytest

import reslice_pipeline as rp


def test_fenced_json():
    assert rp.extract_json('```json\n{"units": []}\n```') == {"units": []}


def test_trailing_comma_tolerated():
    assert rp.extract_json('{"units": [],}') == {"units": []}


def test_plain_text_raises():
    with pytest.raises(ValueError):
        rp.extract_json("这是纯文本没有任何JSON")


def test_truncated_json_raises():
    with pytest.raises(ValueError):
        rp.extract_json('{"units": [{"a": 1}')
