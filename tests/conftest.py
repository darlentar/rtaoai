from pathlib import Path
import pytest
from typing import Any
import json


@pytest.fixture
def get_json():
    def _get_json(path: Path | str) -> Any:
        with open(Path(__file__).resolve().parent / path) as f:
            return json.load(f)

    return _get_json


@pytest.fixture
def get_audio():
    def _get_audio(path: Path | str) -> bytes:
        with open(Path(__file__).resolve().parent / path, "rb") as f:
            return f.read()

    return _get_audio
