from DataService.DataService import Server as DataService, Client as DataClient
from PlannerService.PlannerService import Server as PlannerService, Client as PlannerClient
from CameraAdaptor.CameraAdaptor import Server as CameraAdaptor, Client as CameraClient
from AnalyserService.AnalyserService import Server as AnalyserService, Client as AnalyserClient
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


dataService = DataService(name=DATA_SERVICE_NAME)
dataService.start_insecure(address=SERVER_ADDRESS, port=DATA_SERVICE_PORT)
dataClient = DataClient(address=SERVER_ADDRESS,  port=DATA_SERVICE_PORT, insecure=True)

plannerService = PlannerService(name=PLANNER_SERVICE_NAME)
plannerService.start_insecure(address=SERVER_ADDRESS, port=PLANNER_SERVICE_PORT)
plannerClient = PlannerClient(address=SERVER_ADDRESS,  port=PLANNER_SERVICE_PORT, insecure=True)

cameraAdaptor = CameraAdaptor(name=CAMERA_ADAPTOR_NAME)
cameraAdaptor.start_insecure(address=SERVER_ADDRESS, port=CAMERA_ADAPTOR_PORT)
cameraClient = CameraClient(address=SERVER_ADDRESS,  port=CAMERA_ADAPTOR_PORT, insecure=True)

analyserService = AnalyserService(name=ANALYSER_SERVICE_NAME)
analyserService.start_insecure(address=SERVER_ADDRESS, port=ANALYSER_SERVICE_PORT)
analyserClient = AnalyserClient(address=SERVER_ADDRESS,  port=ANALYSER_SERVICE_PORT, insecure=True)

experimentIndex = 0
collectionName = f"collection_{experimentIndex}"

#setup
dataClient.DataItemProvider.CreateDataNamespace(DataNamespaceName="namespace")
dataClient.DataItemProvider.CreateDataCollection(CollectionPath=f"namespace/{collectionName}")

plannerClient.BinarySearchController.InitializeExperimentParameters(High=100, Low=0, Target=42)
plannerClient.BinarySearchController.CalculateMidPoint()

plannerClient.ExperimentPlanProvider.SubmitExperimentDesignPlan(Target=42, Tolerance=0.3)
plannerClient.ExperimentPlanProvider.StoreExperimentPlan(ItemPath=f"namespace/{collectionName}/experiment_plan")

# inital experiment
experimentPlanItem = dataClient.DataItemProvider.GetDataItem(ItemPath=f"namespace/{collectionName}/experiment_plan")
experimentPlan = json.loads(experimentPlanItem.DataItemContent.decode('utf-8'))
concentrationSDS = experimentPlan["concentrationSDS"]["concentration"]

cameraClient.CameraController.CaptureImage(ExperimentPlanPath=f"namespace/{collectionName}/experiment_plan")
cameraClient.CameraController.StoreImage(ItemPath=f"namespace/{collectionName}/image")

analyserClient.PendantDropAnalyserController.AnalyseImage(ImagePath=f"namespace/{collectionName}/image")
analyserClient.PendantDropAnalyserController.StoreAnalysisResulsts(ItemPath=f"namespace/{collectionName}/analysis")

imageDataItem = dataClient.DataItemProvider.GetDataItem(ItemPath=f"namespace/{collectionName}/image")
imageArray = np.asarray(bytearray(imageDataItem.DataItemContent), dtype="uint8")
image = cv.imdecode(buf=imageArray, flags=cv.IMREAD_COLOR)
cv.imshow("test", image)
cv.waitKey(10)

#further tests
while True:
    experimentIndex += 1
    collectionName = f"collection_{experimentIndex}"
    dataClient.DataItemProvider.CreateDataCollection(CollectionPath=f"namespace/{collectionName}")
    plannerClient.BinarySearchController.UpdateSearchRange(MeasurementPath=f"namespace/collection_{experimentIndex-1}/analysis")
    plannerClient.BinarySearchController.CalculateMidPoint()
    plannerClient.ExperimentPlanProvider.CreateExperimentPlan(PreviousMeasurementItemPath=f"namespace/collection_{experimentIndex-1}/analysis")
    plannerClient.ExperimentPlanProvider.StoreExperimentPlan(ItemPath=f"namespace/{collectionName}/experiment_plan")
    experimentPlanItem = dataClient.DataItemProvider.GetDataItem(ItemPath=f"namespace/{collectionName}/experiment_plan")
    experimentPlan = json.loads(experimentPlanItem.DataItemContent.decode('utf-8'))
    if experimentPlan["stop"] == True:
        break
    else:
        concentrationSDS = experimentPlan["concentrationSDS"]["concentration"]
        cameraClient.CameraController.CaptureImage(ExperimentPlanPath=f"namespace/{collectionName}/experiment_plan")
        cameraClient.CameraController.StoreImage(ItemPath=f"namespace/{collectionName}/image")
        analyserClient.PendantDropAnalyserController.AnalyseImage(ImagePath=f"namespace/{collectionName}/image")
        analyserClient.PendantDropAnalyserController.StoreAnalysisResulsts(ItemPath=f"namespace/{collectionName}/analysis")
        imageDataItem = dataClient.DataItemProvider.GetDataItem(ItemPath=f"namespace/{collectionName}/image")
        imageArray = np.asarray(bytearray(imageDataItem.DataItemContent), dtype="uint8")
        image = cv.imdecode(buf=imageArray, flags=cv.IMREAD_COLOR)
        cv.imshow("test", image)
        cv.waitKey(10)

dataService.stop()
plannerService.stop()
cameraAdaptor.stop()
