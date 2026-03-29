"""
Generates uml_final.png — a simple UML class diagram for PawPal+.
Run once: python make_uml.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 900, 520
BG = (245, 247, 250)
BOX = (255, 255, 255)
BORDER = (70, 130, 180)
HEADER_BG = (70, 130, 180)
HEADER_TXT = (255, 255, 255)
BODY_TXT = (30, 30, 30)
ARROW = (80, 80, 80)
TITLE_TXT = (30, 30, 80)

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

try:
    font_title = ImageFont.truetype("arial.ttf", 18)
    font_head  = ImageFont.truetype("arialbd.ttf", 13)
    font_body  = ImageFont.truetype("arial.ttf", 11)
except Exception:
    font_title = font_head = font_body = ImageFont.load_default()

# Title
draw.text((W // 2, 18), "PawPal+ — System Architecture (UML)", font=font_title,
          fill=TITLE_TXT, anchor="mm")

def draw_class(x, y, name, attrs, methods):
    bw = 190
    line_h = 16
    header_h = 26
    section_h = max(len(attrs), 1) * line_h + 8
    meth_h    = max(len(methods), 1) * line_h + 8
    bh = header_h + section_h + meth_h

    # shadow
    draw.rectangle([x+3, y+3, x+bw+3, y+bh+3], fill=(200, 200, 210))
    # box
    draw.rectangle([x, y, x+bw, y+bh], fill=BOX, outline=BORDER, width=2)
    # header
    draw.rectangle([x, y, x+bw, y+header_h], fill=HEADER_BG)
    draw.text((x + bw//2, y + header_h//2), f"«class» {name}",
              font=font_head, fill=HEADER_TXT, anchor="mm")
    # divider after attrs
    div1 = y + header_h + section_h
    draw.line([x, div1, x+bw, div1], fill=BORDER, width=1)

    # attributes
    for i, a in enumerate(attrs):
        draw.text((x+8, y + header_h + 4 + i*line_h), f"+ {a}", font=font_body, fill=BODY_TXT)

    # methods
    for i, m in enumerate(methods):
        draw.text((x+8, div1 + 4 + i*line_h), f"+ {m}", font=font_body, fill=BODY_TXT)

    cx = x + bw // 2
    cy_top = y
    cy_bot = y + bh
    cx_left = x
    cx_right = x + bw
    return {"top": (cx, cy_top), "bot": (cx, cy_bot),
            "left": (cx_left, y + bh//2), "right": (cx_right, y + bh//2)}

def arrow(p1, p2, label=""):
    draw.line([p1, p2], fill=ARROW, width=2)
    # arrowhead
    import math
    dx, dy = p2[0]-p1[0], p2[1]-p1[1]
    length = math.hypot(dx, dy) or 1
    ux, uy = dx/length, dy/length
    size = 9
    left  = (int(p2[0] - size*ux + size*0.5*uy), int(p2[1] - size*uy - size*0.5*ux))
    right = (int(p2[0] - size*ux - size*0.5*uy), int(p2[1] - size*uy + size*0.5*ux))
    draw.polygon([p2, left, right], fill=ARROW)
    if label:
        mx, my = (p1[0]+p2[0])//2, (p1[1]+p2[1])//2
        draw.text((mx+4, my-12), label, font=font_body, fill=ARROW)

# Draw classes
owner_pts = draw_class(30,  60,  "Owner",
    ["name: str", "pets: list[Pet]"],
    ["add_pet(pet)", "get_all_tasks()"])

pet_pts   = draw_class(250, 60,  "Pet",
    ["name: str", "species: str", "tasks: list[Task]"],
    ["add_task(task)", "remove_task(task)"])

task_pts  = draw_class(470, 60,  "Task",
    ["title: str", "time: str", "duration_minutes: int",
     "priority: str", "frequency: str", "completed: bool", "due_date: date"],
    ["mark_complete()"])

sched_pts = draw_class(140, 330, "Scheduler",
    ["owner: Owner"],
    ["get_all_tasks()", "sort_by_time()", "filter_tasks()",
     "detect_conflicts()", "mark_task_complete()", "generate_schedule()"])

# Arrows
arrow(owner_pts["right"], pet_pts["left"],   "1 has many")
arrow(pet_pts["right"],   task_pts["left"],  "1 has many")
arrow(sched_pts["top"],   owner_pts["bot"],  "manages")

out = os.path.join(os.path.dirname(__file__), "uml_final.png")
img.save(out)
print(f"Saved: {out}")
