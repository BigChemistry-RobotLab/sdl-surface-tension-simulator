# Generated by sila2.code_generator; sila2.__version__: 0.12.2
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sila2.server import FeatureImplementationBase, MetadataDict

from .experimentplanprovider_types import (
    CreateExperimentPlan_Responses,
    StoreExperimentPlan_Responses,
    SubmitExperimentDesignPlan_Responses,
)

if TYPE_CHECKING:

    from ...server import Server


class ExperimentPlanProviderBase(FeatureImplementationBase, ABC):
    parent_server: Server

    def __init__(self, parent_server: Server):
        """

        TODO (stores plan with target and checks if goal is reached)

        """
        super().__init__(parent_server=parent_server)

    @abstractmethod
    def SubmitExperimentDesignPlan(
        self, Target: float, Tolerance: float, *, metadata: MetadataDict
    ) -> SubmitExperimentDesignPlan_Responses:
        """
        Submit experiment design plan.


        :param Target: Desired value that the algorithm aims to achieve.

        :param Tolerance: Acceptable deviation allowed between the measurement and the target value.

        :param metadata: The SiLA Client Metadata attached to the call

        """

    @abstractmethod
    def CreateExperimentPlan(
        self, PreviousMeasurementItemPath: str, *, metadata: MetadataDict
    ) -> CreateExperimentPlan_Responses:
        """
        Creates new experiment plan for experiment in which a target is to be reached by checking if the goal has been reached.


        :param PreviousMeasurementItemPath: Path to the data item that holds the measurement of the previous experiment.

        :param metadata: The SiLA Client Metadata attached to the call

        """

    @abstractmethod
    def StoreExperimentPlan(self, ItemPath: str, *, metadata: MetadataDict) -> StoreExperimentPlan_Responses:
        """
        Store experiment plan


        :param ItemPath: Storage location of the data item in the form of of a file path.

        :param metadata: The SiLA Client Metadata attached to the call

        """
