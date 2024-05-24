from prefect import flow, task
from DataService.DataService import Server as DataService, Client as DataClient
from PlannerService.PlannerService import Server as PlannerService, Client as PlannerClient
from CameraAdaptor.CameraAdaptor import Server as CameraAdaptor, Client as CameraClient
from AnalyserService.AnalyserService import Server as AnalyserService, Client as AnalyserClient
import time
import json
import numpy as np
import cv2 as cv

SERVER_ADDRESS = "127.0.0.1"

DATA_SERVICE_NAME = "DataService"
DATA_SERVICE_PORT = 50052

PLANNER_SERVICE_NAME = "PlannerService"
PLANNER_SERVICE_PORT = 50054

CAMERA_ADAPTOR_NAME = "CameraAdaptor"
CAMERA_ADAPTOR_PORT = 50055

ANALYSER_SERVICE_NAME = "AnalyserService"
ANALYSER_SERVICE_PORT = 50053


@flow
def RunCampaign():
    experimentIndex = 0
    collectionName = f"collection_{experimentIndex}"

    dataClient.DataItemProvider.CreateDataNamespace(
        DataNamespaceName="namespace")

    dataClient.DataItemProvider.CreateDataCollection(
        CollectionPath=f"namespace/{collectionName}")

    InitializeExperimentPlan(
        experimentPlanStoragePath=f"namespace/{collectionName}/experiment_plan")
    PrepareDrop()
    CaptureImage(experimentPlanPath=f"namespace/{collectionName}/experiment_plan",
                 imageStoragePath=f"namespace/{collectionName}/image")
    AnalyseImage(imagePath=f"namespace/{collectionName}/image", experimentPlanPath=f"namespace/{collectionName}/experiment_plan",
                 analysisStoragePath=f"namespace/{collectionName}/analysis")
    DisplayImage(imagePath=f"namespace/{collectionName}/image")

    while True:
        experimentIndex += 1
        collectionName = f"collection_{experimentIndex}"
        dataClient.DataItemProvider.CreateDataCollection(
            CollectionPath=f"namespace/{collectionName}")
        PlanExperiment(previousAnalysisPath=f"namespace/collection_{experimentIndex-1}/analysis",
                       experimentPlanStoragePath=f"namespace/{collectionName}/experiment_plan")
        experimentPlan = json.loads(dataClient.DataItemProvider.GetDataItem(
            ItemPath=f"namespace/{collectionName}/experiment_plan").DataItemContent.decode('utf-8'))
        if experimentPlan["stop"] == True:
            break
        else:
            PrepareDrop()
            CaptureImage(experimentPlanPath=f"namespace/{collectionName}/experiment_plan",
                         imageStoragePath=f"namespace/{collectionName}/image")
            AnalyseImage(imagePath=f"namespace/{collectionName}/image", experimentPlanPath=f"namespace/{collectionName}/experiment_plan",
                         analysisStoragePath=f"namespace/{collectionName}/analysis")
            DisplayImage(imagePath=f"namespace/{collectionName}/image")


def DisplayImage(imagePath):
    imageDataItem = dataClient.DataItemProvider.GetDataItem(ItemPath=imagePath)
    imageArray = np.asarray(
        bytearray(imageDataItem.DataItemContent), dtype="uint8")
    image = cv.imdecode(buf=imageArray, flags=cv.IMREAD_COLOR)
    cv.imshow("test", image)
    cv.waitKey(100)


@task
def CaptureImage(experimentPlanPath, imageStoragePath):
    cameraClient.CameraController.CaptureImage(experimentPlanPath)
    cameraClient.CameraController.StoreImage(ItemPath=imageStoragePath)


@task
def AnalyseImage(imagePath, experimentPlanPath, analysisStoragePath):
    analyserClient.PendantDropAnalyserController.AnalyseImage(
        ImagePath=imagePath, ExperimentPlanPath=experimentPlanPath)
    analyserClient.PendantDropAnalyserController.StoreAnalysisResulsts(
        ItemPath=analysisStoragePath)

@task
def PlanExperiment(previousAnalysisPath, experimentPlanStoragePath):
    plannerClient.BinarySearchController.UpdateSearchRange(
        MeasurementPath=previousAnalysisPath)
    plannerClient.BinarySearchController.CalculateMidPoint()
    plannerClient.ExperimentPlanProvider.CreateExperimentPlan(
        PreviousMeasurementItemPath=previousAnalysisPath)
    plannerClient.ExperimentPlanProvider.StoreExperimentPlan(
        ItemPath=experimentPlanStoragePath)


@task
def InitializeExperimentPlan(experimentPlanStoragePath):
    plannerClient.BinarySearchController.InitializeExperimentParameters(
        High=100, Low=0, Target=42)
    plannerClient.BinarySearchController.CalculateMidPoint()
    plannerClient.ExperimentPlanProvider.SubmitExperimentDesignPlan(
        Target=42, Tolerance=0.4)
    plannerClient.ExperimentPlanProvider.StoreExperimentPlan(
        ItemPath=experimentPlanStoragePath)


@task
def PrepareDrop():
    time.sleep(0.1)


if __name__ == "__main__":
    try:
        dataService = DataService(name=DATA_SERVICE_NAME)
        dataService.start_insecure(
            address=SERVER_ADDRESS, port=DATA_SERVICE_PORT)
        dataClient = DataClient(address=SERVER_ADDRESS,
                                port=DATA_SERVICE_PORT, insecure=True)

        plannerService = PlannerService(name=PLANNER_SERVICE_NAME)
        plannerService.start_insecure(
            address=SERVER_ADDRESS, port=PLANNER_SERVICE_PORT)
        plannerClient = PlannerClient(
            address=SERVER_ADDRESS,  port=PLANNER_SERVICE_PORT, insecure=True)

        cameraAdaptor = CameraAdaptor(name=CAMERA_ADAPTOR_NAME)
        cameraAdaptor.start_insecure(
            address=SERVER_ADDRESS, port=CAMERA_ADAPTOR_PORT)
        cameraClient = CameraClient(
            address=SERVER_ADDRESS,  port=CAMERA_ADAPTOR_PORT, insecure=True)

        analyserService = AnalyserService(name=ANALYSER_SERVICE_NAME)
        analyserService.start_insecure(
            address=SERVER_ADDRESS, port=ANALYSER_SERVICE_PORT)
        analyserClient = AnalyserClient(
            address=SERVER_ADDRESS,  port=ANALYSER_SERVICE_PORT, insecure=True)

        RunCampaign()
    finally:
        dataService.stop()
        plannerService.stop()
        cameraAdaptor.stop()
        analyserService.stop()
