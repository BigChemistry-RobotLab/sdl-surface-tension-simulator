# Generated by sila2.code_generator; sila2.__version__: 0.12.2

from typing import Optional
from uuid import UUID, uuid4

from sila2.server import SilaServer

from .feature_implementations.pendantdropanalysercontroller_impl import PendantDropAnalyserControllerImpl
from .generated.pendantdropanalysercontroller import PendantDropAnalyserControllerFeature


class Server(SilaServer):
    def __init__(
        self,
        server_uuid: Optional[UUID] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        if name is None:
            name = "AnalyserService"
        if description is None:
            description = "Analysis service to determine the surface tension of pendant drop image."
        super().__init__(
            server_name=name,
            server_description=description,
            server_type="Service",
            server_version="0.1",
            server_vendor_url="https://gitlab.com/SiLA2/sila_python",
            server_uuid=server_uuid if server_uuid is not None else uuid4(),
        )

        self.pendantdropanalysercontroller = PendantDropAnalyserControllerImpl(self)
        self.set_feature_implementation(PendantDropAnalyserControllerFeature, self.pendantdropanalysercontroller)
