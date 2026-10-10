# Task 4: Object Detection and Tracking

Real-time object detection and tracking using OpenCV, YOLOv8, and Deep SORT.

## Features
- Webcam or video-file input
- YOLOv8 pretrained object detection
- Bounding boxes
- Object labels
- Unique tracking IDs
- Deep SORT multi-object tracking
- FPS display
- Active-object count
- Save annotated frame with `S`

## Install

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run

```powershell
python object_detection_tracking.py
```

The first run downloads `yolov8n.pt` automatically if it is not already available.

## Video file

Change:

```python
VIDEO_SOURCE = 0
```

to:

```python
VIDEO_SOURCE = "input.mp4"
```

and put `input.mp4` in this folder.

## Controls

- `Q` or `ESC` = quit
- `S` = save current annotated frame

## Optional class filtering

To detect only selected classes:

```python
ALLOWED_CLASSES = {"person", "car", "dog"}
```

Use `None` to detect all supported YOLO/COCO classes.

## Processing pipeline

Webcam/video -> OpenCV -> YOLOv8 -> detections -> Deep SORT -> tracking IDs -> annotated live display
