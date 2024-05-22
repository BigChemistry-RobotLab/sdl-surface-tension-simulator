from DataService.DataService import Server as DataService, Client as DataClient
from PlannerService.PlannerService import Server as PlannerService, Client as PlannerClient
import json

SERVER_ADDRESS = "127.0.0.1"

DATA_SERVICE_NAME = "DataService"
DATA_SERVICE_PORT = 50052

PLANNER_SERVICE_NAME = "PlannerService"
PLANNER_SERVICE_PORT = 50054


dataService = DataService(name=DATA_SERVICE_NAME)
dataService.start_insecure(address=SERVER_ADDRESS, port=DATA_SERVICE_PORT)
dataClient = DataClient(address=SERVER_ADDRESS,  port=DATA_SERVICE_PORT, insecure=True)

plannerService = PlannerService(name=PLANNER_SERVICE_NAME)
plannerService.start_insecure(address=SERVER_ADDRESS, port=PLANNER_SERVICE_PORT)
plannerClient = PlannerClient(address=SERVER_ADDRESS,  port=PLANNER_SERVICE_PORT, insecure=True)

experimentIndex = 0
collectionName = f"collection_{experimentIndex}"

#setup
dataClient.DataItemProvider.CreateDataNamespace(DataNamespaceName="namespace")
dataClient.DataItemProvider.CreateDataCollection(CollectionPath=f"namespace/{collectionName}")

plannerClient.BinarySearchController.InitializeExperimentParameters(High=100, Low=0, Target=42)
plannerClient.BinarySearchController.CalculateMidPoint()

plannerClient.ExperimentPlanProvider.SubmitExperimentDesignPlan(Target=42, Tolerance=0.01)
plannerClient.ExperimentPlanProvider.StoreExperimentPlan(ItemPath=f"namespace/{collectionName}/experiment_plan")

# inital experiment
experimentPlanItem = dataClient.DataItemProvider.GetDataItem(ItemPath=f"namespace/{collectionName}/experiment_plan")
experimentPlan = json.loads(experimentPlanItem.DataItemContent.decode('utf-8'))
concentrationSDS = experimentPlan["concentrationSDS"]["concentration"]

result = concentrationSDS

dataClient.DataItemProvider.CreateDataItem(ItemPath=f"namespace/{collectionName}/result", Content=str(result).encode(encoding='utf-8'), ItemProperties=[])

#further tests
while True:
    experimentIndex += 1
    collectionName = f"collection_{experimentIndex}"
    dataClient.DataItemProvider.CreateDataCollection(CollectionPath=f"namespace/{collectionName}")
    plannerClient.BinarySearchController.UpdateSearchRange(MeasurementPath=f"namespace/collection_{experimentIndex-1}/result")
    plannerClient.BinarySearchController.CalculateMidPoint()
    plannerClient.ExperimentPlanProvider.CreateExperimentPlan(PreviousMeasurementItemPath=f"namespace/collection_{experimentIndex-1}/result")
    plannerClient.ExperimentPlanProvider.StoreExperimentPlan(ItemPath=f"namespace/{collectionName}/experiment_plan")
    experimentPlanItem = dataClient.DataItemProvider.GetDataItem(ItemPath=f"namespace/{collectionName}/experiment_plan")
    experimentPlan = json.loads(experimentPlanItem.DataItemContent.decode('utf-8'))
    if experimentPlan["stop"] == True:
        break
    else:
        concentrationSDS = experimentPlan["concentrationSDS"]["concentration"]
        print(concentrationSDS)
        result = concentrationSDS
        dataClient.DataItemProvider.CreateDataItem(ItemPath=f"namespace/{collectionName}/result", Content=str(result).encode(encoding='utf-8'), ItemProperties=[])

dataService.stop()
plannerService.stop()
