import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

MODEL_PATH = "yolov8n.pt"
VIDEO_SOURCE = 0  # Change to "input.mp4" for a video file
CONFIDENCE_THRESHOLD = 0.40
ALLOWED_CLASSES = None  # Example: {"person", "car", "dog"}

print("Loading YOLO model...")
model = YOLO(MODEL_PATH)
print("YOLO model loaded.")

tracker = DeepSort(
    max_age=30,
    n_init=2,
    nms_max_overlap=1.0,
    max_cosine_distance=0.3,
    nn_budget=None,
)

cap = cv2.VideoCapture(VIDEO_SOURCE)

if not cap.isOpened():
    raise RuntimeError(
        "Could not open the video source. Check your webcam or video file path."
    )

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

previous_time = 0.0

print("Starting object detection and tracking...")
print("Press Q or ESC to quit. Press S to save a frame.")

while True:
    success, frame = cap.read()

    if not success:
        print("Could not read the next frame.")
        break

    results = model(
        frame,
        conf=CONFIDENCE_THRESHOLD,
        verbose=False,
    )

    detections = []

    for result in results:
        if result.boxes is None:
            continue

        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = model.names[class_id]

            if (
                ALLOWED_CLASSES is not None
                and class_name not in ALLOWED_CLASSES
            ):
                continue

            detections.append(
                (
                    [x1, y1, x2 - x1, y2 - y1],
                    confidence,
                    class_name,
                )
            )

    tracks = tracker.update_tracks(detections, frame=frame)

    active_objects = 0

    for track in tracks:
        if not track.is_confirmed():
            continue

        if track.time_since_update > 1:
            continue

        active_objects += 1
        track_id = track.track_id
        x1, y1, x2, y2 = map(int, track.to_ltrb())

        class_name = track.get_det_class() or "object"

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(frame.shape[1] - 1, x2)
        y2 = min(frame.shape[0] - 1, y2)

        cv2.rectangle(
            frame, (x1, y1), (x2, y2), (0, 255, 0), 2
        )

        label = f"{class_name} | ID {track_id}"

        (text_width, text_height), baseline = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            2,
        )

        label_top = max(0, y1 - text_height - baseline - 8)

        cv2.rectangle(
            frame,
            (x1, label_top),
            (x1 + text_width + 10, y1),
            (0, 255, 0),
            -1,
        )

        cv2.putText(
            frame,
            label,
            (x1 + 5, y1 - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        cv2.circle(
            frame,
            (center_x, center_y),
            4,
            (0, 255, 255),
            -1,
        )

    current_time = cv2.getTickCount()

    if previous_time != 0:
        fps = cv2.getTickFrequency() / (current_time - previous_time)
    else:
        fps = 0.0

    previous_time = current_time

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (15, 15),
        (310, 105),
        (0, 0, 0),
        -1,
    )

    frame = cv2.addWeighted(
        overlay,
        0.55,
        frame,
        0.45,
        0,
    )

    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (30, 43),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        f"Tracked Objects: {active_objects}",
        (30, 72),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.60,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        "Q: Quit | S: Save",
        (30, 96),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (200, 220, 255),
        1,
        cv2.LINE_AA,
    )

    cv2.imshow(
        "Task 4 - Object Detection and Tracking",
        frame,
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q") or key == 27:
        break

    if key == ord("s"):
        cv2.imwrite("tracked_output.jpg", frame)
        print("Saved frame to tracked_output.jpg")

cap.release()
cv2.destroyAllWindows()
print("Program stopped.")
