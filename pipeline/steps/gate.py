"""Quyết định Release, Hold hoặc Rework dựa trên kết quả QC."""

from ..common import ERROR, WARN


def decide(issues, image_stems, cfg, reviewed=frozenset()):
    images = set(image_stems)
    warn_images = set()
    n_errors = 0

    for issue in issues:
        if issue.severity == ERROR:
            n_errors += 1
        elif (
            issue.severity == WARN
            and issue.image in images
            and issue.image not in reviewed
        ):
            warn_images.add(issue.image)

    n_images = len(images)
    n_warn_images = len(warn_images)
    warn_ratio = n_warn_images / n_images if n_images else 0.0
    hold_threshold = cfg["gate"]["warn_ratio_hold"]

    warning_summary = (
        f"Còn {n_warn_images}/{n_images} ảnh có cảnh báo chưa được duyệt "
        f"({warn_ratio:.2%}), ngưỡng Hold là {hold_threshold:.2%}."
    )

    if n_errors:
        decision = "Rework"
        reasons = [f"Còn {n_errors} lỗi bắt buộc.", warning_summary]
    elif warn_ratio >= hold_threshold:
        decision = "Hold"
        reasons = [warning_summary]
    else:
        decision = "Release"
        reasons = ["Còn 0 lỗi bắt buộc.", warning_summary]

    return {
        "decision": decision,
        "n_errors": n_errors,
        "n_warn_images": n_warn_images,
        "n_images": n_images,
        "warn_ratio": round(warn_ratio, 4),
        "reasons": reasons,
    }
