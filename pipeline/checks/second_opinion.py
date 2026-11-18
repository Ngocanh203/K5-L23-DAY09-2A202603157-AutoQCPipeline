"""Đối chiếu nhãn YOLO với dự đoán đã lưu và tạo cảnh báo cho người duyệt."""

from ..common import WARN, Issue, iou_xywh, parse_yolo_line
from ..model_cache import get_preds


def _read_boxes(ds, stem):
    boxes = []
    for line_no, text in ds.read_label_lines(stem) or []:
        try:
            class_id, cx, cy, width, height = parse_yolo_line(text)
        except (ValueError, OverflowError):
            continue

        if 0 <= class_id < len(ds.classes) and width > 0 and height > 0:
            boxes.append((line_no, class_id, (cx, cy, width, height)))

    return boxes


def run(ds, cfg, preds=None):
    if preds is None:
        preds = get_preds(ds, cfg, "checker")

    settings = cfg["second_opinion"]
    min_iou = settings["iou_missing"]
    issues = []

    for image_path in ds.image_files():
        stem = image_path.stem
        if stem not in preds or not ds.label_path(stem).is_file():
            continue

        predictions = preds[stem]
        labels = _read_boxes(ds, stem)
        image_size = ds.image_size(stem)

        if image_size is not None:
            image_width, image_height = image_size
            for class_id, confidence, cx, cy, width, height in predictions:
                if confidence < settings["conf"]:
                    continue

                area_px = (width * image_width) * (height * image_height)
                if area_px < settings["min_area_px"]:
                    continue

                box = (cx, cy, width, height)
                candidates = []
                for _, label_class, label_box in labels:
                    overlap = iou_xywh(box, label_box)
                    if overlap >= min_iou:
                        candidates.append((label_class, overlap))

                if not candidates:
                    issues.append(Issue(
                        "second_opinion", WARN, "POSSIBLE_MISSING", stem,
                        f"Model thấy đối tượng lớp {class_id} chưa có box khớp",
                        extra={"conf": confidence},
                    ))
                    continue

                same_class_ious = [
                    overlap for label_class, overlap in candidates
                    if label_class == class_id
                ]
                if same_class_ious:
                    best_iou = max(same_class_ious)
                    if best_iou < settings["iou_loose"]:
                        issues.append(Issue(
                            "second_opinion", WARN, "POSSIBLE_LOOSE_BOX", stem,
                            f"Box cùng lớp có IoU {best_iou:.3f}, cần xem lại biên",
                            extra={"conf": confidence, "iou": best_iou},
                        ))
                    continue

                label_class, best_iou = max(candidates, key=lambda item: item[1])
                if best_iou >= settings["iou_match"]:
                    issues.append(Issue(
                        "second_opinion", WARN, "POSSIBLE_WRONG_CLASS", stem,
                        f"Nhãn là lớp {label_class}, model dự đoán lớp {class_id}",
                        extra={"conf": confidence, "iou": best_iou},
                    ))

        prediction_boxes = [
            tuple(prediction[2:]) for prediction in predictions
            if prediction[1] >= settings["fp_conf"]
        ]
        for line_no, _, label_box in labels:
            best_iou = max(
                (iou_xywh(label_box, box) for box in prediction_boxes),
                default=0.0,
            )
            if best_iou < min_iou:
                issues.append(Issue(
                    "second_opinion", WARN, "POSSIBLE_FALSE_POS", stem,
                    "Box nhãn không khớp với dự đoán nào đủ độ tin cậy",
                    line=line_no,
                    extra={"iou": best_iou},
                ))

    return issues
