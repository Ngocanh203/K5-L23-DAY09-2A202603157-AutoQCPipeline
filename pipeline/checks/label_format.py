"""Kiểm tra định dạng và hình học của các dòng nhãn YOLO."""

from ..common import ERROR, WARN, Issue, iou_xywh, parse_yolo_line


def run(ds, cfg):
    settings = cfg["label_format"]
    issues = []

    for label_file in ds.label_files():
        stem = label_file.stem
        image_size = ds.image_size(stem)
        boxes_by_class = {}

        for line_no, text in ds.read_label_lines(stem) or []:
            try:
                class_id, cx, cy, w, h = parse_yolo_line(text)
            except (ValueError, OverflowError) as exc:
                issues.append(Issue(
                    "label_format", ERROR, "BAD_FORMAT", stem, str(exc),
                    line=line_no,
                ))
                continue

            if not 0 <= class_id < len(ds.classes):
                issues.append(Issue(
                    "label_format", ERROR, "BAD_CLASS_ID", stem,
                    f"ID lớp {class_id} nằm ngoài danh sách lớp",
                    line=line_no,
                ))
                continue

            if w <= 0 or h <= 0:
                issues.append(Issue(
                    "label_format", ERROR, "BOX_ZERO", stem,
                    "Chiều rộng và chiều cao của box phải lớn hơn 0",
                    line=line_no,
                ))
                continue

            left = cx - w / 2
            right = cx + w / 2
            top = cy - h / 2
            bottom = cy + h / 2
            overflow = max(0.0, -left, right - 1, -top, bottom - 1)

            if overflow > settings["overflow_tol"]:
                issues.append(Issue(
                    "label_format", ERROR, "BOX_OUT_OF_IMAGE", stem,
                    f"Box tràn biên {overflow:.6f}",
                    line=line_no,
                    extra={"overflow": overflow},
                ))

            box = (cx, cy, w, h)
            earlier_boxes = boxes_by_class.setdefault(class_id, [])
            if any(
                iou_xywh(box, earlier) > settings["dup_box_iou"]
                for earlier in earlier_boxes
            ):
                issues.append(Issue(
                    "label_format", ERROR, "DUP_BOX", stem,
                    "Box trùng với một box cùng lớp ở dòng trước",
                    line=line_no,
                ))
            earlier_boxes.append(box)

            if image_size is not None:
                image_width, image_height = image_size
                short_side_px = min(w * image_width, h * image_height)
                if short_side_px < settings["min_box_px"]:
                    issues.append(Issue(
                        "label_format", WARN, "BOX_TINY", stem,
                        f"Cạnh ngắn của box là {short_side_px:.2f} px",
                        line=line_no,
                    ))

            if w * h > settings["max_box_frac"]:
                issues.append(Issue(
                    "label_format", WARN, "BOX_HUGE", stem,
                    f"Diện tích chuẩn hóa của box là {w * h:.4f}",
                    line=line_no,
                ))

    return issues
