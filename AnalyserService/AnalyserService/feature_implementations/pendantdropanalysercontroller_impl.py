# Generated by sila2.code_generator; sila2.__version__: 0.12.2
from __future__ import annotations

from typing import TYPE_CHECKING
from DataService.DataService import Client as DataClient
import imutils
from scipy.spatial.distance import euclidean
import numpy as np
import itertools
import cv2 as cv
import datetime

from sila2.server import MetadataDict

from ..generated.pendantdropanalysercontroller import (
    AnalyseImage_Responses,
    PendantDropAnalyserControllerBase,
    StoreAnalysisResulsts_Responses,
)

if TYPE_CHECKING:
    from ..server import Server

class PendantDropAnalyserControllerImpl(PendantDropAnalyserControllerBase):
    def __init__(self, parent_server: Server) -> None:
        self.dataService = DataClient(address="127.0.0.1",  port=50052, insecure=True)
        super().__init__(parent_server=parent_server)

    def DetermineInterfacialSurfaceTension(self, image , needleDiameter: float, density: float) -> float:
        max_distance = 0
        min_distance=float('inf')

        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (9, 9), 0)
        canny = cv.Canny(blur, 20, 20)
        dilate = cv.dilate(canny, None, iterations=1)
        erode = cv.erode(dilate, None, iterations=1)

        contours = imutils.grab_contours(cv.findContours(erode.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE))
        longest_contour = sorted(contours, key=lambda x: len(x), reverse=True)[0]

        cv.drawContours(image, [longest_contour], -1, (0, 255, 0), thickness=2)

        x, y, w, h = cv.boundingRect(longest_contour)

        top_left = (x, y)
        top_right = (x + w, y)
        bottom_left = (x, y + h)

        drop_width = euclidean(top_left, top_right)

        if drop_width > 150:
            crop_img = np.zeros_like(image)
            cv.drawContours(crop_img, [longest_contour], -1, (0, 255, 0), thickness=2)
            
            crop_img = cv.cvtColor(crop_img, cv.COLOR_BGR2GRAY)
            crop_img = crop_img[int(top_left[1]):int(bottom_left[1] - drop_width), int(top_left[0]):int(top_right[0])]

            cnts_2, _ = cv.findContours(crop_img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

            contourleft, contourright = max(itertools.combinations(cnts_2, 2), 
                                            key=lambda pair: euclidean(cv.minEnclosingCircle(pair[0])[0], 
                                                                    cv.minEnclosingCircle(pair[1])[0]))

            for cnt1, cnt2 in itertools.product(contourleft, contourright):
                for point1, point2 in itertools.product(cnt1, cnt2):
                    x1, _ = point1.ravel()
                    x2, _ = point2.ravel()
                    distance_x = abs(x1 - x2)
                    if distance_x < min_distance:
                        min_distance = distance_x
                    if distance_x > max_distance:
                        max_distance = distance_x

            drop_shape_ratio = max_distance/(drop_width)
            if 0.2 < drop_shape_ratio < 1.1:
                scale=(needleDiameter/(min_distance))
                denew=scale*drop_width

            if ((drop_shape_ratio>=0.3) and (drop_shape_ratio<=0.4)):
                drop_shape_factor=(0.34074/(drop_shape_ratio**2.52303))+(123.9495*(drop_shape_ratio**5))-(72.82991*(drop_shape_ratio**4))+(0.01320*(drop_shape_ratio**3))-(3.38210*(drop_shape_ratio**2))+(5.52969*(drop_shape_ratio))-1.07260
            elif ((drop_shape_ratio>0.4) and (drop_shape_ratio<=0.46)):
                drop_shape_factor=(0.32720/(drop_shape_ratio**2.56651))-(0.97553*(drop_shape_ratio**2))+(0.84059*drop_shape_ratio)-(0.18069)
            elif ((drop_shape_ratio>0.46) and (drop_shape_ratio<=0.59)):
                drop_shape_factor=(0.31968/(drop_shape_ratio**2.59725))-(0.46898*(drop_shape_ratio**2))+(0.50059*drop_shape_ratio)-(0.13261)
            elif ((drop_shape_ratio>0.59) and (drop_shape_ratio<=0.68)):
                drop_shape_factor=(0.31522/(drop_shape_ratio**2.62435))-(0.11714*(drop_shape_ratio**2))+(0.15756*drop_shape_ratio)-(0.05285)
            elif ((drop_shape_ratio>0.68) and (drop_shape_ratio<=0.9)):
                drop_shape_factor=(0.31345/(drop_shape_ratio**2.64267))-(0.09155*(drop_shape_ratio**2))+(0.14701*drop_shape_ratio)-(0.05877)
            elif ((drop_shape_ratio>0.9) and (drop_shape_ratio<=1)):
                drop_shape_factor=(0.30715/(drop_shape_ratio**2.84636))-(0.69116*(drop_shape_ratio**3))+(1.08315*(drop_shape_ratio**2))-(0.18341*drop_shape_ratio)-(0.20970)

            interfacial_tension =(density*9.81*(denew**2)*drop_shape_factor)

            if 15 < interfacial_tension < 300:
                return interfacial_tension

    def GetDatItemPropertyByKey(self, properties, key: str):
        for property in properties:
            if property[0] == key:
                return property
        return None

    def AnalyseImage(self, ImagePath: str, *, metadata: MetadataDict) -> AnalyseImage_Responses:
        imageDataItem = self.dataService.DataItemProvider.GetDataItem(ItemPath=ImagePath)
        imageArray = np.asarray(bytearray(imageDataItem.DataItemContent), dtype="uint8")
        image = cv.imdecode(buf=imageArray, flags=cv.IMREAD_COLOR)
        needleDiameter = float(self.GetDatItemPropertyByKey(properties=imageDataItem.ItemProperties, key='needle_diameter')[1])
        density = float(self.GetDatItemPropertyByKey(properties=imageDataItem.ItemProperties, key='density')[1])
        self.interfacial_tension = self.DetermineInterfacialSurfaceTension(image=image, needleDiameter=needleDiameter, density=density)
        self.analysisTimeStamp = datetime.datetime.now().timestamp()
        return AnalyseImage_Responses()

    def StoreAnalysisResulsts(self, ItemPath: str, *, metadata: MetadataDict) -> StoreAnalysisResulsts_Responses:
        self.dataService.DataItemProvider.CreateDataItem(
            ItemPath=ItemPath,
            Content=str(self.interfacial_tension).encode(encoding='utf-8'),
            ItemProperties=[
                tuple(["creationTime", f"{self.analysisTimeStamp}"]),
                tuple(["unit", "mN/m"])
            ]
        )
        return StoreAnalysisResulsts_Responses()
