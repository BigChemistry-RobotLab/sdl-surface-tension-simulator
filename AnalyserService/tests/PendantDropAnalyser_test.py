import sys, os
# when running this test in the cmd add the line below to fix backwards reference problem by appending the root project folder to the imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))) 

import cv2 as cv
from DataService.DataService import Server as DataService, Client as DataClient
from AnalyserService.AnalyserService import Server as AnalyserService, Client as AnalyserClient
import unittest
import json

SERVER_ADDRESS = "127.0.0.1"

DATA_SERVICE_NAME = "DataService"
DATA_SERVICE_PORT = 50052

ANALYSER_SERVICE_NAME = "AnalyserService"
ANALYSER_SERVICE_PORT = 50053

# Tests pendant drop analyser feature using an image of pendant drop with an interfacial surface tension of 72 mN/m +/- 1
class TestPendantDropAnalyser(unittest.TestCase):
    def setUp(self):
        # Create and start data service
        self.dataService = DataService(name=DATA_SERVICE_NAME)
        self.dataService.start_insecure(address=SERVER_ADDRESS, port=DATA_SERVICE_PORT)

        # Create data client to interact with the data service
        self.dataClient = DataClient(address=SERVER_ADDRESS,  port=DATA_SERVICE_PORT, insecure=True)

        # Create and start analyser service
        self.analyserService = AnalyserService(name=ANALYSER_SERVICE_NAME)
        self.analyserService.start_insecure(address=SERVER_ADDRESS, port=ANALYSER_SERVICE_PORT)

        # Create analyser client to interact with the analyser service
        self.analyserClient = AnalyserClient(address=SERVER_ADDRESS,  port=ANALYSER_SERVICE_PORT, insecure=True)

        # Create namespace and collection in which the image and analysis will be stored
        self.dataClient.DataItemProvider.CreateDataNamespace(DataNamespaceName="namespace")
        self.dataClient.DataItemProvider.CreateDataCollection(CollectionPath="namespace/collection")

        # Store experiment plan with only neccesary analysis parameters
        experimentPlan = {
                "needleDiameter": {
                    "diameter": 0.68,
                    "unit": "cm"
                },
                "density": {
                    "density": 0.999,
                    "unit": "g/cm3"
                }
            }

        self.dataClient.DataItemProvider.CreateDataItem(
            ItemPath="namespace/collection/plan",
            Content= json.dumps(experimentPlan).encode(encoding='utf-8'),
            ItemProperties=[]
        )

        # Read test image and store it in data service
        image = cv.imread(os.path.abspath(
            "AnalyserService/tests/pendant_drop.jpg"))
        imageBytes = cv.imencode('.jpg', image)[1].tobytes()
        self.dataClient.DataItemProvider.CreateDataItem(
            ItemPath="namespace/collection/test_image",
            Content=imageBytes,
            ItemProperties=[]
        )

    def test_pendant_drop_analyser(self):
        # Determine the interfacial surface tension of the stored test image
        self.analyserClient.PendantDropAnalyserController.AnalyseImage(ImagePath="namespace/collection/test_image", ExperimentPlanPath="namespace/collection/plan")
        
        # Store interfacial surface tension in data service
        self.analyserClient.PendantDropAnalyserController.StoreAnalysisResulsts(ItemPath="namespace/collection/analysis")

        # Get analysis from data service and check if it has an interfacial surface tension of 72 mN/m +/- 1
        analysisDataItem = self.dataClient.DataItemProvider.GetDataItem(ItemPath="namespace/collection/analysis")
        interfacialTension = float(analysisDataItem.DataItemContent.decode('utf-8'))
        print(f"interfacial surface tension: {interfacialTension}")
        self.assertAlmostEqual(first=interfacialTension, second=72, delta=1)

    def tearDown(self):
        # Stop data and analyser service
        self.dataService.stop()
        self.analyserService.stop()

if __name__ == '__main__': 
    unittest.main()
