# Generated by sila2.code_generator; sila2.__version__: 0.12.2
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sila2.server import FeatureImplementationBase, MetadataDict

from .pendantdropanalysercontroller_types import AnalyseImage_Responses, StoreAnalysisResulsts_Responses

if TYPE_CHECKING:

    from ...server import Server


class PendantDropAnalyserControllerBase(FeatureImplementationBase, ABC):
    parent_server: Server

    def __init__(self, parent_server: Server):
        """

        Experiment-specific service that retrieves an image from the data service, then analyses that image to determine the surface tension of the pendant drop in the image.
        And stores the results of the analysis in data service. In this mocked service, only the volume of SDS is retrieved from the data service
        and this value is compared to a function that caluclates the surface tension.

        """
        super().__init__(parent_server=parent_server)

    @abstractmethod
    def AnalyseImage(self, ImagePath: str, *, metadata: MetadataDict) -> AnalyseImage_Responses:
        """
        Retrieve an image from the data service and determine its interfacial tension.


        :param ImagePath: File path from where to fetch the image to be analysed.

        :param metadata: The SiLA Client Metadata attached to the call

        """

    @abstractmethod
    def StoreAnalysisResulsts(self, ItemPath: str, *, metadata: MetadataDict) -> StoreAnalysisResulsts_Responses:
        """
        Store analysis results of image.


        :param ItemPath: Storage location of the data item in the form of of a file path like so: namespaceName/collectionName/dataItemName.

        :param metadata: The SiLA Client Metadata attached to the call

        """
