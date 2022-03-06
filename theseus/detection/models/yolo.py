# Author: Zylo117
import json
import numpy as np

import torch
from torch import nn

from typing import Any, Dict


class BaseBackbone(nn.Module):
    def __init__(self, **kwargs):
        super(BaseBackbone, self).__init__()
        pass

    def forward(self, batch):
        pass

    def detect(self, batch):
        pass


class YoloBackbone(BaseBackbone):
    """
    Some yolov5 models with various pretrained backbones from hub

    weight : `str` 
        weight path to load custom yolov5 weight
    min_conf: `float` 
        NMS confidence threshold
    min_iou: `float`
        NMS IoU threshold
    max_det: `int` 
        maximum number of detections per image - 300 for YOLO
    """

    def __init__(
            self,
            weight: str,
            min_iou: float,
            min_conf: float,
            max_det: int = 300,
            **kwargs):

        super().__init__(**kwargs)
        self.model = torch.hub.load(
            'ultralytics/yolov5', 'custom', path=weight, force_reload=True)

        self.class_names = self.model.names

        self.model.conf = min_conf  # NMS confidence threshold
        self.model.iou = min_iou  # NMS IoU threshold
        self.model.multi_label = False  # NMS multiple labels per box
        self.model.max_det = max_det  # maximum number of detections per image

    def get_model(self):
        """
        Return the full architecture of the model, for visualization
        """
        return self.model

    def forward(self, x: torch.Tensor):
        outputs = self.model(x)
        return outputs

    def get_prediction(self, adict: Dict[str, Any], device: torch.device):
        inputs = adict["img_names"]
        results = self.model(inputs)  # inference
        # print('Results: ', results)
        outputs = results.pandas().xyxy

        out = []
        for i, output in enumerate(outputs):
            output = json.loads(output.to_json(orient="records"))

            boxes = []
            labels = []
            scores = []
            for obj_dict in output:
                boxes.append([obj_dict['xmin'], obj_dict['ymin'], obj_dict['xmax'] -
                              obj_dict['xmin'], obj_dict['ymax']-obj_dict['ymin']])
                labels.append(obj_dict["class"])
                scores.append(obj_dict["confidence"])

            if len(boxes) > 0:
                out.append({
                    'bboxes': np.array(boxes),
                    'classes': np.array(labels),
                    'scores': np.array(scores),
                })
            else:
                out.append({
                    'bboxes': np.array(()),
                    'classes': np.array(()),
                    'scores': np.array(()),
                })

        return out
