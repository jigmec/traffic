import tkinter as tk
import random

# ---------- Layout ----------
WIDTH, HEIGHT = 800, 400
ROAD_TOP, ROAD_H = 140, 120
ROAD_BOTTOM = ROAD_TOP + ROAD_H
CROSS_X, CROSS_W = 370, 60
STOP_LINE = CROSS_X - 10
DETECT_DIST = 120      # GALLERY CHALLENGE: "close enough to stop"
MIN_BRAKE_DIST = 35    # on yellow, cars closer than this keep going

RED_TIME, YELLOW_TIME, WALK_DELAY = 300, 90, 60   # in frames

# ---------- State ----------
light = "red"          # PEDESTRIAN light: red (wait) -> yellow (get ready) -> green (walk) -> red
timer = 0
cars = []
COLORS = ["#e63946", "#457b9d", "#f4a261", "#2a9d8f", "#9b5de5"]

ped = {"x": CROSS_X + CROSS_W // 2, "y": ROAD_TOP - 40, "r": 10,
       "speed": 1.6, "crossing": False}
PED_START_Y = ped["y"]
PED_END_Y = ROAD_BOTTOM + 30

root = tk.Tk()
root.title("Pedestrian Crossing Simulator")
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, highlightthickness=0)
canvas.pack()
status = tk.Label(root, text="", font=("Arial", 12))
status.pack(pady=6)


# ---------- Cars ----------
def spawn_car():
    if cars and cars[-1]["x"] < 120:      # keep a gap
        return
    cars.append({"x": -80, "y": ROAD_TOP + 70, "w": 70, "h": 36, "speed": 0.0,
                 "max_speed": 2 + random.random() * 1.5,
                 "color": random.choice(COLORS)})


# ---------- Collision detection (rectangle overlap) ----------
def overlaps(a, b):
    return (a["x"] < b["x"] + b["w"] and a["x"] + a["w"] > b["x"] and
            a["y"] < b["y"] + b["h"] and a["y"] + a["h"] > b["y"])

def ped_box():
    return {"x": ped["x"] - ped["r"], "y": ped["y"] - ped["r"],
            "w": ped["r"] * 2, "h": ped["r"] * 2}

CROSSING_ZONE = {"x": CROSS_X - 5, "y": ROAD_TOP, "w": CROSS_W + 10, "h": ROAD_H}

def car_in_crossing():
    return any(overlaps(c, CROSSING_ZONE) for c in cars)


# ---------- GALLERY CHALLENGE ----------
def distance_to_stop_line(car):
    """Gap between the car's FRONT edge and the stop line."""
    return STOP_LINE - (car["x"] + car["w"])

def should_stop(car):
    d = distance_to_stop_line(car)
    if light == "green":     # pedestrians walking: cars must stop
        return 0 <= d < DETECT_DIST
    if light == "yellow":    # pedestrians about to walk: cars slow down
        return MIN_BRAKE_DIST <= d < DETECT_DIST   # too close to stop? keep going
    return False   # red for pedestrians: cars go


# ---------- Update ----------
def update():
    global light, timer
    if random.random() < 0.02:
        spawn_car()
    timer += 1

    # Signal state machine
    if light == "red" and timer > RED_TIME:
        light, timer = "yellow", 0
    elif light == "yellow" and timer > YELLOW_TIME:
        light, timer = "green", 0
    elif light == "green":
        # Pedestrian walks only on GREEN, after a short delay, and only if no car is in the crossing
        if not ped["crossing"] and timer > WALK_DELAY and not car_in_crossing():
            ped["crossing"] = True
        if ped["crossing"] and ped["y"] >= PED_END_Y:
            ped["crossing"] = False
            ped["y"] = PED_START_Y
            light, timer = "red", 0

    # Move cars
    for i, car in enumerate(cars):
        blocked = should_stop(car)
        if i > 0:
            ahead = cars[i - 1]
            if ahead["x"] - (car["x"] + car["w"]) < 15:
                blocked = True
        if blocked:
            car["speed"] = max(0.0, car["speed"] - 0.15)
        else:
            car["speed"] = min(car["max_speed"], car["speed"] + 0.05)
        car["x"] += car["speed"]
    while cars and cars[0]["x"] > WIDTH + 50:
        cars.pop(0)

    # Move pedestrian
    if ped["crossing"]:
        ped["y"] += ped["speed"]
        if any(overlaps(c, ped_box()) for c in cars):
            ped["y"] -= ped["speed"]      # safety freeze

    if light == "red":
        msg = "Pedestrian waits. Cars go."
    elif light == "yellow":
        msg = "Get ready: cars are slowing down."
    else:
        msg = "WALK: pedestrian is crossing." if ped["crossing"] else \
              "Cars stopping. Waiting for the crossing to clear..."
    status.config(text=f"Signal: {light.upper()} | {msg}")


# ---------- Background (drawn once) ----------
def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def draw_tree(x, y, scale=1.0):
    canvas.create_rectangle(x - 5 * scale, y, x + 5 * scale, y + 38 * scale, fill="#6b4226", outline="")
    for dx, dy, r, col in ((0, -8, 30, "#2d6a4f"), (-18, 6, 22, "#40916c"),
                           (18, 6, 22, "#40916c"), (0, -24, 20, "#52b788")):
        canvas.create_oval(x + (dx - r) * scale, y + (dy - r) * scale,
                           x + (dx + r) * scale, y + (dy + r) * scale, fill=col, outline="")

def draw_cloud(x, y, s=1.0):
    for dx, dy, w, h in ((0, 0, 60, 24), (22, -12, 44, 26), (-20, -4, 38, 20), (40, 2, 40, 18)):
        canvas.create_oval(x + (dx - w / 2) * s, y + (dy - h / 2) * s,
                           x + (dx + w / 2) * s, y + (dy + h / 2) * s, fill="#ffffff", outline="")

def draw_background():
    rnd = random.Random(7)   # fixed seed so the scenery is always the same

    # Sky gradient
    for i in range(0, 100, 2):
        canvas.create_rectangle(0, i, WIDTH, i + 2, fill=mix("#4ea8de", "#ffd6a5", i / 100), outline="")

    # Sun with soft glow
    for r, col in ((46, "#ffe8b0"), (34, "#ffd77a"), (24, "#ffc83d")):
        canvas.create_oval(660 - r, 34 - r, 660 + r, 34 + r, fill=col, outline="")

    draw_cloud(120, 30, 1.0)
    draw_cloud(290, 52, 0.7)
    draw_cloud(520, 24, 0.9)

    # Distant hills
    canvas.create_polygon(0, 100, 0, 72, 90, 56, 200, 70, 310, 52, 430, 72, 560, 58,
                          690, 74, 800, 60, 800, 100, fill="#8fb8a8", outline="")

    # City skyline (muted so the signals stand out)
    x = 0
    while x < WIDTH:
        w, h = rnd.randint(40, 70), rnd.randint(30, 62)
        col = rnd.choice(["#9aa5b8", "#a7b0c2", "#8e9ab0"])
        canvas.create_rectangle(x, 98 - h, x + w, 98, fill=col, outline="")
        for wy in range(98 - h + 6, 92, 10):
            for wx in range(x + 6, x + w - 8, 12):
                canvas.create_rectangle(wx, wy, wx + 6, wy + 5,
                                        fill="#ffe9a8" if rnd.random() < 0.3 else "#c9d3e3", outline="")
        x += w + 2

    # Hedge behind the pavement
    canvas.create_rectangle(0, 94, WIDTH, 106, fill="#2d6a4f", outline="")
    for hx in range(0, WIDTH, 14):
        canvas.create_oval(hx, 90, hx + 18, 106, fill="#40916c", outline="")

    # Top pavement with tile lines + curb
    canvas.create_rectangle(0, 104, WIDTH, ROAD_TOP, fill="#d8d4cc", outline="")
    for tx in range(0, WIDTH, 40):
        canvas.create_line(tx, 104, tx, ROAD_TOP, fill="#c4bfb5")
    canvas.create_line(0, 122, WIDTH, 122, fill="#c4bfb5")
    canvas.create_rectangle(0, ROAD_TOP - 5, WIDTH, ROAD_TOP, fill="#a8a39a", outline="")

    # Bottom pavement + curb, then grass with scenery
    canvas.create_rectangle(0, ROAD_BOTTOM, WIDTH, ROAD_BOTTOM + 30, fill="#d8d4cc", outline="")
    for tx in range(0, WIDTH, 40):
        canvas.create_line(tx, ROAD_BOTTOM, tx, ROAD_BOTTOM + 30, fill="#c4bfb5")
    canvas.create_rectangle(0, ROAD_BOTTOM, WIDTH, ROAD_BOTTOM + 5, fill="#a8a39a", outline="")
    canvas.create_rectangle(0, ROAD_BOTTOM + 30, WIDTH, HEIGHT, fill="#74b86a", outline="")
    for gy in range(ROAD_BOTTOM + 36, HEIGHT, 14):          # grass stripes
        canvas.create_rectangle(0, gy, WIDTH, gy + 7, fill="#6aae60", outline="")
    for _ in range(40):                                      # flowers
        fx, fy = rnd.randint(5, WIDTH - 5), rnd.randint(ROAD_BOTTOM + 40, HEIGHT - 8)
        canvas.create_oval(fx - 3, fy - 3, fx + 3, fy + 3,
                           fill=rnd.choice(["#ffffff", "#ffd166", "#ff8fab", "#cdb4db"]), outline="")
    for tx, ty, s in ((60, 300, 1.0), (190, 320, 0.8), (580, 304, 1.0), (730, 322, 0.85)):
        draw_tree(tx, ty, s)

    # Road surface with texture and edge lines
    canvas.create_rectangle(0, ROAD_TOP, WIDTH, ROAD_BOTTOM, fill="#4a4e57", outline="")
    for _ in range(260):
        rx, ry = rnd.randint(0, WIDTH), rnd.randint(ROAD_TOP + 8, ROAD_BOTTOM - 8)
        canvas.create_line(rx, ry, rx + rnd.randint(2, 5), ry, fill=rnd.choice(["#555a64", "#42464e"]))
    canvas.create_line(0, ROAD_TOP + 5, WIDTH, ROAD_TOP + 5, fill="#e8e8e8", width=2)
    canvas.create_line(0, ROAD_BOTTOM - 5, WIDTH, ROAD_BOTTOM - 5, fill="#e8e8e8", width=2)
    canvas.create_line(0, ROAD_TOP + ROAD_H // 2, WIDTH, ROAD_TOP + ROAD_H // 2,
                       fill="#ffd60a", width=3, dash=(25, 20))

    # Zebra crossing
    for y in range(ROAD_TOP + 8, ROAD_BOTTOM - 10, 18):
        canvas.create_rectangle(CROSS_X, y, CROSS_X + CROSS_W, y + 9, fill="#f5f5f5", outline="")

    # Detection zone + stop line
    mid = ROAD_TOP + ROAD_H // 2
    canvas.create_rectangle(STOP_LINE - DETECT_DIST, mid + 4, STOP_LINE, ROAD_BOTTOM - 6,
                            fill="#8a8a3a", outline="", stipple="gray25")
    canvas.create_rectangle(STOP_LINE, mid + 4, STOP_LINE + 4, ROAD_BOTTOM - 6, fill="#ffffff", outline="")


# ---------- Moving things (redrawn every frame, tagged "dyn") ----------
def rect(x1, y1, x2, y2, fill):
    canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="", tags="dyn")

def oval(x1, y1, x2, y2, fill):
    canvas.create_oval(x1, y1, x2, y2, fill=fill, outline="", tags="dyn")

def draw_signals():
    # Car traffic light
    x, y = STOP_LINE - 30, ROAD_TOP - 90
    rect(x + 12, y + 90, x + 18, ROAD_TOP - 5, "#555")
    rect(x, y, x + 30, y + 90, "#111")
    for colour, dy in (("red", 18), ("yellow", 45), ("green", 72)):
        if light == colour:
            oval(x + 1, y + dy - 14, x + 29, y + dy + 14, mix("#111111", {"red": "#ff3b30", "yellow": "#ffd60a", "green": "#34c759"}[colour], 0.35))
        oval(x + 4, y + dy - 11, x + 26, y + dy + 11, colour if light == colour else "#333")

def draw():
    canvas.delete("dyn")
    draw_signals()

    for car in cars:
        x, y, w, h = car["x"], car["y"], car["w"], car["h"]
        oval(x + 4, y + h - 2, x + w - 4, y + h + 8, "#2f3238")     # shadow
        rect(x, y, x + w, y + h, car["color"])
        rect(x + 14, y - 10, x + w - 14, y + 2, car["color"])        # roof
        rect(x + 18, y - 7, x + w - 18, y + 1, "#cfe8ff")
        rect(x + w - 22, y + 6, x + w - 8, y + h - 6, "#cfe8ff")
        rect(x + w - 4, y + h - 14, x + w, y + h - 8, "#fff3b0")     # headlight
        for wx in (x + 15, x + w - 15):
            oval(wx - 7, y + h - 7, wx + 7, y + h + 7, "#111")
            oval(wx - 3, y + h - 3, wx + 3, y + h + 3, "#aaa")
        if car["speed"] < 0.1:
            rect(x, y + 8, x + 4, y + 16, "red")

    # Pedestrian (stick figure)
    px, py = ped["x"], ped["y"]
    oval(px - 10, py + 18, px + 10, py + 24, "#b8b3aa")              # shadow
    oval(px - 7, py - 19, px + 7, py - 5, "#ffcc99")
    for coords in ((px, py - 5, px, py + 10), (px - 8, py, px + 8, py),
                   (px, py + 10, px - 6, py + 20), (px, py + 10, px + 6, py + 20)):
        canvas.create_line(*coords, fill="#1d3557", width=4, tags="dyn")


def loop():
    update()
    draw()
    root.after(16, loop)

draw_background()
loop()
root.mainloop()
