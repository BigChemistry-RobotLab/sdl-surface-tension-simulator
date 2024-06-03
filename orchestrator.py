from prefect import flow, task
from DataService.DataService import Server as DataService, Client as DataClient
from PlannerService.PlannerService import Server as PlannerService, Client as PlannerClient
from CameraAdaptor.CameraAdaptor import Server as CameraAdaptor, Client as CameraClient
from AnalyserService.AnalyserService import Server as AnalyserService, Client as AnalyserClient
from OpentronsAdaptor.OpentronsOT2Adaptor import Server as OpentronsAdaptor, Client as OpentronsClient
import time
import json
import numpy as np
import cv2 as cv
from tkinter import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
from PIL import Image, ImageTk
import math

# --------------------------- Iterface ---------------------------
root = Tk()

variableFrame = LabelFrame(
    master=root, text="Simulation variables", padx=15, pady=15)
variableFrame.grid(row=0, column=0, sticky="nsew")

targetLabelText = Label(master=variableFrame, text="Target surface tension")
targetLabelText.pack()
targetVar = IntVar(value=42)
targetLabel = Entry(master=variableFrame, textvariable=targetVar)
targetLabel.pack()

lowLabelText = Label(master=variableFrame, text="Low (concentration SDS)")
lowLabelText.pack()
lowVar = IntVar(value=0)
lowVar = Entry(master=variableFrame, textvariable=lowVar)
lowVar.pack()

highLabelText = Label(master=variableFrame, text="High (concentration SDS)")
highLabelText.pack()
highVar = IntVar(value=20)
highVar = Entry(master=variableFrame, textvariable=highVar)
highVar.pack()

simulationSpeedLabelText = Label(master=variableFrame, text="Simulation Step Delay")
simulationSpeedLabelText.pack()
simulationSpeedVar = IntVar(value=0.5)
simulationSpeedVar = Entry(master=variableFrame, textvariable=simulationSpeedVar)
simulationSpeedVar.pack()

button = Button(master=variableFrame, text="Run campaign")
button.pack()

progressFrame = LabelFrame(
    master=root, text="Progress", padx=15, pady=15)
progressFrame.grid(row=0, column=1, sticky="nsew")

ExperimentName = Label(master=progressFrame)
ExperimentName.pack()

statusLabel = Label(master=progressFrame)
statusLabel.pack()

imageFrame = LabelFrame(master=root, text="Drop Image", padx=15, pady=15)
imageFrame.grid(row=1, column=0, sticky="nsew")

dropImageLabel = Label(master=imageFrame)
dropImageLabel.pack()

graphFrame = LabelFrame(
    master=root, text="Surface Tension Graph", padx=15, pady=15)
graphFrame.grid(row=1, column=1, sticky="nsew")

fig = Figure(figsize=(5, 4), dpi=100)
canvas = FigureCanvasTkAgg(figure=fig, master=graphFrame)

x = []
y = []

def DisplayGraph(dataClient: DataClient, surfaceTensionPath, experimentPlanPath):
    experimentPlanItem = dataClient.DataItemProvider.GetDataItem(
        ItemPath=experimentPlanPath)
    experimentPlan = json.loads(
        experimentPlanItem.DataItemContent.decode('utf-8'))
    concentrationSDS = experimentPlan["concentrationSDS"]["concentration"]
    x.append(concentrationSDS)
    surfaceTensionItem = dataClient.DataItemProvider.GetDataItem(
        ItemPath=surfaceTensionPath)
    surfaceTension = float(surfaceTensionItem.DataItemContent.decode('utf-8'))
    y.append(surfaceTension)
    canvas.figure.clear()
    plt = fig.add_subplot(111)
    plt.scatter(x, y)
    plt.set_ylim([30, 80])
    plt.set_xlim([float(lowVar.get()), float(highVar.get())])
    plt.axhline(y=surfaceTension, color="r")
    plt.text(float(lowVar.get()) + 1, surfaceTension, "{:.2f}".format(
        surfaceTension), fontsize=10, va='center', ha='center', backgroundcolor='w')
    plt.axvline(x=concentrationSDS, color="r")
    plt.text(concentrationSDS, 33, "{:.2f}".format(
        concentrationSDS), fontsize=10, va='center', ha='center', backgroundcolor='w')
    plt.set_xlabel("Concentration SDS (mM)")
    plt.set_ylabel("Surface tension (mN/m)")
    canvas.draw()
    canvas.get_tk_widget().pack()

def DisplayDrop(dataClient: DataClient, imagePath: str):
    imageDataitem = dataClient.DataItemProvider.GetDataItem(ItemPath=imagePath)
    nparr = np.asarray(bytearray(imageDataitem.DataItemContent), dtype="uint8")
    image = cv.imdecode(buf=nparr, flags=cv.IMREAD_COLOR)
    image = cv.resize(image, (400, 400), cv.INTER_LINEAR)
    pil_image = Image.fromarray(image)
    tk_image = ImageTk.PhotoImage(pil_image)
    dropImageLabel.image = tk_image
    dropImageLabel.configure(image=tk_image)

def click():
    del x[:]
    del y[:]
    plt = fig.add_subplot(111)
    plt.remove()
    canvas.draw()
    canvas.get_tk_widget().pack()
    button.config(state="disabled")
    update_thread = threading.Thread(target=RunCampaign)
    update_thread.start()


button.config(command=click)

def window():
    root.mainloop()
# ------------------------- Orchestrator -------------------------

SERVER_ADDRESS = "127.0.0.1"

DATA_SERVICE_NAME = "DataService"
DATA_SERVICE_PORT = 50052

PLANNER_SERVICE_NAME = "PlannerService"
PLANNER_SERVICE_PORT = 50054

CAMERA_ADAPTOR_NAME = "CameraAdaptor"
CAMERA_ADAPTOR_PORT = 50055

ANALYSER_SERVICE_NAME = "AnalyserService"
ANALYSER_SERVICE_PORT = 50053

OPENTRONS_ADAPTOR_NAME = "OpentronsAdaptor"
OPENTRONS_ADAPTOR_PORT = 50056

WAIT_TIME = 0.5
TOLERANCE = 0.25


@flow(
    name="Surface tension taget campaign",
    description="Tries to reach a target interfacial surface tension of a pendant drop using binary search, each experiment a new drop is created based on a concentration of SDS."
)
def RunCampaign():
    try:
        statusLabel.config(text="Starting services")
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
        
        opentronsAdaptor = OpentronsAdaptor(name=OPENTRONS_ADAPTOR_NAME)
        opentronsAdaptor.start_insecure(
            address=SERVER_ADDRESS, port=OPENTRONS_ADAPTOR_PORT)
        opentronsClient = OpentronsClient(
            address=SERVER_ADDRESS,  port=OPENTRONS_ADAPTOR_PORT, insecure=True)
        
        experimentIndex = 0
        collectionName = f"collection_{experimentIndex}"

        dataClient.DataItemProvider.CreateDataNamespace(
            DataNamespaceName="namespace")

        dataClient.DataItemProvider.CreateDataCollection(
            CollectionPath=f"namespace/{collectionName}")
        
        ExperimentName.configure(text="Initial experiment")

        InitializeExperimentPlan(plannerClient=plannerClient,
                                 experimentPlanStoragePath=f"namespace/{collectionName}/experiment_plan")
        PrepareDrop(opentronsClient=opentronsClient, experimentPlanStoragePath=f"namespace/{collectionName}/experiment_plan")
        CaptureImage(cameraClient=cameraClient, experimentPlanPath=f"namespace/{collectionName}/experiment_plan",
                     imageStoragePath=f"namespace/{collectionName}/image")
        DisplayDrop(dataClient=dataClient,
                    imagePath=f"namespace/{collectionName}/image")
        AnalyseImage(analyserClient=analyserClient, imagePath=f"namespace/{collectionName}/image", experimentPlanPath=f"namespace/{collectionName}/experiment_plan",
                     analysisStoragePath=f"namespace/{collectionName}/analysis")
        DisplayGraph(dataClient=dataClient,
                     surfaceTensionPath=f"namespace/{collectionName}/analysis", experimentPlanPath=f"namespace/{collectionName}/experiment_plan")

        while True:
            experimentIndex += 1
            ExperimentName.configure(text=f"Experiment nr.{experimentIndex}")
            collectionName = f"collection_{experimentIndex}"
            dataClient.DataItemProvider.CreateDataCollection(
                CollectionPath=f"namespace/{collectionName}")
            PlanExperiment(plannerClient=plannerClient, previousAnalysisPath=f"namespace/collection_{experimentIndex-1}/analysis",
                           experimentPlanStoragePath=f"namespace/{collectionName}/experiment_plan")
            experimentPlan = json.loads(dataClient.DataItemProvider.GetDataItem(
                ItemPath=f"namespace/{collectionName}/experiment_plan").DataItemContent.decode('utf-8'))
            if experimentPlan["stop"] == True:
                break
            else:
                PrepareDrop(opentronsClient=opentronsClient, experimentPlanStoragePath=f"namespace/{collectionName}/experiment_plan")
                CaptureImage(cameraClient=cameraClient, experimentPlanPath=f"namespace/{collectionName}/experiment_plan",
                             imageStoragePath=f"namespace/{collectionName}/image")
                DisplayDrop(dataClient=dataClient,
                            imagePath=f"namespace/{collectionName}/image")
                AnalyseImage(analyserClient=analyserClient, imagePath=f"namespace/{collectionName}/image", experimentPlanPath=f"namespace/{collectionName}/experiment_plan",
                             analysisStoragePath=f"namespace/{collectionName}/analysis")
                DisplayGraph(dataClient=dataClient,
                             surfaceTensionPath=f"namespace/{collectionName}/analysis", experimentPlanPath=f"namespace/{collectionName}/experiment_plan")
    finally:
        statusLabel.config(text="Shutting down services")
        dataService.stop()
        plannerService.stop()
        cameraAdaptor.stop()
        analyserService.stop()

        statusLabel.config(text="Target interfacial surface tension reached!")
        button.config(state="active")

@task(
    name="Capture image",
    description="Generates image from SDS concentration in experiment plan, and stores the image in the data service",
    tags=["Observe"]
)
def CaptureImage(cameraClient: CameraClient, experimentPlanPath, imageStoragePath):
    statusLabel.config(text="Capturing image")
    time.sleep(float(simulationSpeedVar.get()))
    cameraClient.CameraController.CaptureImage(experimentPlanPath)
    time.sleep(float(simulationSpeedVar.get()))
    statusLabel.config(text="Storing image")
    cameraClient.CameraController.StoreImage(ItemPath=imageStoragePath)

@task(
    name="Analyse image",
    description="Retrieves image from data service, analyses it and stores analysis in data service.",
    tags=["Orient"]
)
def AnalyseImage(analyserClient: AnalyserClient, imagePath, experimentPlanPath, analysisStoragePath):
    statusLabel.config(text="Analysing image")
    time.sleep(float(simulationSpeedVar.get()))
    analyserClient.PendantDropAnalyserController.AnalyseImage(
        ImagePath=imagePath, ExperimentPlanPath=experimentPlanPath)
    statusLabel.config(text="Storing analysis")
    time.sleep(float(simulationSpeedVar.get()))
    analyserClient.PendantDropAnalyserController.StoreAnalysisResulsts(
        ItemPath=analysisStoragePath)

@task(
    name="Plan new experiment",
    description="Retreives analysis result from previous experiment, calulates midpoint with binary search, creates new experiment plan and stores it in data service.",
    tags=["Decide"]
)
def PlanExperiment(plannerClient: PlannerClient, previousAnalysisPath, experimentPlanStoragePath):
    statusLabel.config(text="Updating binary search range")
    time.sleep(float(simulationSpeedVar.get()))
    plannerClient.BinarySearchController.UpdateSearchRange(
        MeasurementPath=previousAnalysisPath)
    statusLabel.config(text="Calucating search space midpoint")
    time.sleep(float(simulationSpeedVar.get()))
    plannerClient.BinarySearchController.CalculateMidPoint()
    statusLabel.config(text="Creating experiment plan")
    time.sleep(float(simulationSpeedVar.get()))
    plannerClient.ExperimentPlanProvider.CreateExperimentPlan(
        PreviousMeasurementItemPath=previousAnalysisPath)
    statusLabel.config(text="Storing experiment plan")
    time.sleep(float(simulationSpeedVar.get()))
    plannerClient.ExperimentPlanProvider.StoreExperimentPlan(
        ItemPath=experimentPlanStoragePath)

@task(
    name="Initialize experiment plan",
    description="Initializes variables for binary search, calculates midpoint for initial experiment, sbumits initial experiment design plan with variables and stores that experiment plan in the data store.",
    tags=["Decide"]
)
def InitializeExperimentPlan(plannerClient: PlannerClient, experimentPlanStoragePath):
    plannerClient.BinarySearchController.InitializeExperimentParameters(
        High=float(highVar.get()), Low=float(lowVar.get()), Target=targetVar.get())
    statusLabel.config(text="Calucating search space midpoint")
    time.sleep(float(simulationSpeedVar.get()))
    plannerClient.BinarySearchController.CalculateMidPoint()
    statusLabel.config(text="Initializing experiment plan")
    time.sleep(float(simulationSpeedVar.get()))
    plannerClient.ExperimentPlanProvider.SubmitExperimentDesignPlan(
        Target=targetVar.get(), Tolerance=TOLERANCE)
    statusLabel.config(text="Storing experiment plan")
    time.sleep(float(simulationSpeedVar.get()))
    plannerClient.ExperimentPlanProvider.StoreExperimentPlan(
        ItemPath=experimentPlanStoragePath)

@task(
    name="Prepare drop",
    description="Prepares drop using the opentron (doenst really have any impact on the flow, but is only for simulation purposes)",
    tags=["Act"]
)
def PrepareDrop(opentronsClient: OpentronsClient, experimentPlanStoragePath):
    statusLabel.config(text="Preparing pendant drop")
    time.sleep(float(simulationSpeedVar.get()))
    opentronsClient.OpentronsOT2Controller.PrepareDrop(ExperimentPlanPath=experimentPlanStoragePath)

if __name__ == "__main__":
    window()
