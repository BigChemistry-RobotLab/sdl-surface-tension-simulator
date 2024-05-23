# Generated by sila2.code_generator; sila2.__version__: 0.12.2
# -----
# This class does not do anything useful at runtime. Its only purpose is to provide type annotations.
# Since sphinx does not support .pyi files (yet?), this is a .py file.
# -----

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:

    from typing import Iterable, Optional

    from pendantdropanalysercontroller_types import AnalyseImage_Responses, StoreAnalysisResulsts_Responses
    from sila2.client import ClientMetadataInstance


class PendantDropAnalyserControllerClient:
    """

    Experiment-specific service that retrieves an image from the data service, then analyses that image to determine the surface tension of the pendant drop in the image.
    And stores the results of the analysis in data service. In this mocked service, only the volume of SDS is retrieved from the data service
    and this value is compared to a function that caluclates the surface tension.

    """

    def AnalyseImage(
        self, ImagePath: str, *, metadata: Optional[Iterable[ClientMetadataInstance]] = None
    ) -> AnalyseImage_Responses:
        """
        Retrieve an image from the data service and determine its interfacial tension.
        """
        ...

    def StoreAnalysisResulsts(
        self, ItemPath: str, *, metadata: Optional[Iterable[ClientMetadataInstance]] = None
    ) -> StoreAnalysisResulsts_Responses:
        """
        Store analysis results of image.
        """
        ...