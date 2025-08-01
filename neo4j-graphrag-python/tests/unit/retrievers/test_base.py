#  Copyright (c) "Neo4j"
#  Neo4j Sweden AB [https://neo4j.com]
#  #
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  #
#      https://www.apache.org/licenses/LICENSE-2.0
#  #
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from __future__ import annotations  # Reminder: May be removed after Python 3.9 is EOL.

import inspect
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest
from neo4j_graphrag.exceptions import Neo4jVersionError
from neo4j_graphrag.retrievers.base import Retriever
from neo4j_graphrag.types import RawSearchResult, RetrieverResult


@pytest.mark.parametrize(
    "db_version,expected_exception",
    [
        (((5, 18, 0), True, True), None),
        (((5, 3, 0), True, True), Neo4jVersionError),
        (((5, 19, 0), False, True), None),
        (((4, 3, 5), False, True), Neo4jVersionError),
        (((5, 23, 0), False, True), None),
        (((2025, 1, 0), False, True), None),
        (((2025, 1, 0), True, True), None),
    ],
)
@patch("neo4j_graphrag.retrievers.base.get_version")
def test_retriever_version_support(
    mock_get_version: MagicMock,
    driver: MagicMock,
    db_version: tuple[tuple[int, ...], bool],
    expected_exception: Optional[type[ValueError]],
) -> None:
    mock_get_version.return_value = db_version

    class MockRetriever(Retriever):
        def get_search_results(self, *args: Any, **kwargs: Any) -> RawSearchResult:
            return RawSearchResult(records=[])

    if expected_exception:
        with pytest.raises(expected_exception):
            MockRetriever(driver=driver)
    else:
        MockRetriever(driver=driver)


@patch("neo4j_graphrag.retrievers.base.get_version")
def test_retriever_search_docstring_copied(
    mock_get_version: MagicMock,
    driver: MagicMock,
) -> None:
    mock_get_version.return_value = ((5, 23, 0), False, False)

    class MockRetriever(Retriever):
        def get_search_results(self, query: str, top_k: int = 10) -> RawSearchResult:
            """My fabulous docstring"""
            return RawSearchResult(records=[])

    retriever = MockRetriever(driver=driver)
    assert retriever.search.__doc__ == "My fabulous docstring"
    signature = inspect.signature(retriever.search)
    assert "query" in signature.parameters
    query_param = signature.parameters["query"]
    assert query_param.default == query_param.empty
    assert query_param.annotation == "str"
    assert "top_k" in signature.parameters
    top_k_param = signature.parameters["top_k"]
    assert top_k_param.default == 10
    assert top_k_param.annotation == "int"


@patch("neo4j_graphrag.retrievers.base.get_version")
def test_retriever_search_docstring_unchanged(
    mock_get_version: MagicMock,
    driver: MagicMock,
) -> None:
    mock_get_version.return_value = ((5, 23, 0), False, False)

    class MockRetrieverForNoise(Retriever):
        def get_search_results(self, query: str, top_k: int = 10) -> RawSearchResult:
            """My fabulous docstring"""
            return RawSearchResult(records=[])

    class MockRetriever(Retriever):
        def get_search_results(self, *args: Any, **kwargs: Any) -> RawSearchResult:
            return RawSearchResult(records=[])

        def search(self, query: str, top_k: int = 10) -> RetrieverResult:
            """My fabulous docstring that I do not want to be updated"""
            return RetrieverResult(items=[])

    assert MockRetrieverForNoise.search is not MockRetriever.search

    retriever = MockRetriever(driver=driver)
    assert (
        retriever.search.__doc__
        == "My fabulous docstring that I do not want to be updated"
    )
