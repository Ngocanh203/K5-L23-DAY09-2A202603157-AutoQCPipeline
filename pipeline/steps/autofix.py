"""Tự sửa các lỗi bắt buộc được quy định và ghi log từng thay đổi."""

from collections import defaultdict

import yaml

from ..common import ERROR, parse_yolo_line


DROP_LINE_CODES = {"BAD_FORMAT", "BAD_CLASS_ID", "BOX_ZERO", "DUP_BOX"}
REMOVE_IMAGE_CODES = {"LEAK_TEST", "CORRUPT_IMAGE", "BAD_SIZE"}


def _fix_entry(image, line, action, before, after):
    return {
        "image": image,
        "line": line,
        "action": action,
        "before": before,
        "after": after,
    }


def _clip_box(text):
    class_id, cx, cy, width, height = parse_yolo_line(text)

    left = max(0.0, cx - width / 2)
    top = max(0.0, cy - height / 2)
    right = min(1.0, cx + width / 2)
    bottom = min(1.0, cy + height / 2)

    if right <= left or bottom <= top:
        return None

    clipped_box = (
        (left + right) / 2,
        (top + bottom) / 2,
        right - left,
        bottom - top,
    )
    return " ".join([str(class_id), *(f"{value:.16g}" for value in clipped_box)])


def fix(ds, issues, cfg):
    changes = []
    images_to_remove = set()
    missing_labels = set()
    line_issues = defaultdict(lambda: defaultdict(set))
    rename_classes = False

    for issue in issues:
        if issue.severity != ERROR:
            continue

        code = issue.code
        if code in REMOVE_IMAGE_CODES or code.startswith("DUP_IMAGE_"):
            images_to_remove.add(issue.image)
        elif code == "MISSING_LABEL_FILE":
            missing_labels.add(issue.image)
        elif code == "BAD_CLASS_NAME":
            rename_classes = True
        elif issue.line is not None and (
            code in DROP_LINE_CODES or code == "BOX_OUT_OF_IMAGE"
        ):
            line_issues[issue.image][issue.line].add(code)

    for stem in sorted(images_to_remove):
        image_path = ds.image_path(stem)
        label_path = ds.label_path(stem)
        removed_names = []

        if image_path is not None and image_path.is_file():
            image_path.unlink()
            removed_names.append(image_path.name)

        if label_path.is_file():
            label_path.unlink()
            removed_names.append(label_path.name)

        if removed_names:
            changes.append(_fix_entry(
                stem, None, "remove_image", ", ".join(removed_names), "",
            ))

    if rename_classes:
        path = ds.yaml_path
        data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}
        data = data or {}
        before = data.get("names")
        after = list(cfg["classes"])

        if before != after:
            data["names"] = after
            path.write_text(
                yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            changes.append(_fix_entry(
                "data.yaml", None, "rename_classes", str(before), str(after),
            ))

    for stem in sorted(missing_labels - images_to_remove):
        if not ds.label_path(stem).exists():
            changes.append(_fix_entry(
                stem, None, "needs_label", "(không có file)", "chuyển người gán",
            ))

    for stem in sorted(line_issues.keys() - images_to_remove):
        path = ds.label_path(stem)
        if not path.is_file():
            continue

        original_text = path.read_text(encoding="utf-8", errors="replace")
        kept_lines = []
        file_changes = []

        for line_no, text in enumerate(
            original_text.splitlines(keepends=True), start=1
        ):
            codes = line_issues[stem].get(line_no)
            if not codes or not text.strip():
                kept_lines.append(text)
                continue

            before = text.rstrip("\r\n")

            if codes & DROP_LINE_CODES:
                after = None
            else:
                try:
                    after = _clip_box(before)
                except (ValueError, OverflowError):
                    after = None

            if after is None:
                file_changes.append(_fix_entry(
                    stem, line_no, "drop_line", before, "",
                ))
            else:
                line_ending = text[len(before):]
                kept_lines.append(after + line_ending)
                if after != before:
                    file_changes.append(_fix_entry(
                        stem, line_no, "clip_box", before, after,
                    ))

        if file_changes:
            path.write_text("".join(kept_lines), encoding="utf-8")
            changes.extend(file_changes)

    return changes
