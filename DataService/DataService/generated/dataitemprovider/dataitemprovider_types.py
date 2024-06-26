# Generated by sila2.code_generator; sila2.__version__: 0.12.2
from __future__ import annotations

from typing import Any, List, NamedTuple


class CreateDataNamespace_Responses(NamedTuple):

    pass


class CreateDataCollection_Responses(NamedTuple):

    pass


class CreateDataItem_Responses(NamedTuple):

    pass


class GetDataItem_Responses(NamedTuple):

    DataItemContent: bytes
    """
    Content of the data item.
    """

    ItemProperties: List[Any]
    """
    Properties of data item.
    """
