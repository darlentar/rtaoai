#!/usr/bin/env bash
mypy .
ruff format .
ruff check . --fix
