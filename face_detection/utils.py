def clip_box(box: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x, y, w, h = box
    x = max(0, min(x, width - 1))
    y = max(0, min(y, height - 1))
    w = max(1, min(w, width - x))
    h = max(1, min(h, height - y))
    return x, y, w, h


def expand_box(
    box: tuple[int, int, int, int],
    width: int,
    height: int,
    scale: float = 1.25,
) -> tuple[int, int, int, int]:
    x, y, w, h = box
    cx = x + w / 2
    cy = y + h / 2
    new_w = int(w * scale)
    new_h = int(h * scale)
    new_x = int(cx - new_w / 2)
    new_y = int(cy - new_h / 2)
    return clip_box((new_x, new_y, new_w, new_h), width, height)


def draw_landmarks(frame, landmarks):
    return frame
