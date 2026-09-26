#!/usr/bin/env python3
import os, re, socket, sys, time
import xml.etree.ElementTree as ET
from datetime import datetime
DEVICE="192.0.2.10:5555"
YOUTUBE_PACKAGE="com.amazon.firetv.youtube"
NETFLIX_PACKAGE="com.netflix.ninja"
TV_VOLUME_STATE=os.path.join(os.path.dirname(__file__), ".firetv_tv_volume_level")
MONTHS=("enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre")
def frame(s): return f"{len(s):04x}".encode()+s.encode()
def run(command):
    with socket.create_connection(("127.0.0.1",5037), timeout=2) as sock:
        sock.sendall(frame("host:transport:"+DEVICE)); sock.recv(4)
        sock.sendall(frame("shell:"+command)); sock.settimeout(2)
        try:
            while sock.recv(4096): pass
        except (socket.timeout, ConnectionResetError): pass


def output(command):
    """Run a shell command through the resident ADB server and return output."""
    with socket.create_connection(("127.0.0.1", 5037), timeout=2) as sock:
        sock.sendall(frame("host:transport:" + DEVICE))
        if sock.recv(4) != b"OKAY":
            return ""
        sock.sendall(frame("shell:" + command))
        sock.settimeout(2)
        chunks = []
        try:
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
        except (socket.timeout, ConnectionResetError):
            pass
        return b"".join(chunks).decode("utf-8", "replace")


def awake():
    state = output("dumpsys power")
    return "mWakefulness=Awake" in state or "Display Power: state=ON" in state
def key(value): run("input keyevent "+value)
def tap(x,y): run(f"input tap {x} {y}")

def _ui_tree():
    """Return the current accessibility tree when Fire TV exposes one."""
    raw = output("uiautomator dump /dev/tty 2>/dev/null")
    start = raw.find("<hierarchy")
    end = raw.rfind("</hierarchy>")
    if start < 0 or end < start:
        return None
    try:
        return ET.fromstring(raw[start:end + len("</hierarchy>")])
    except ET.ParseError:
        return None

def _node_label(node):
    return " ".join((node.attrib.get(name, "") for name in ("text", "content-desc"))).casefold()

def _node_center(node):
    match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.attrib.get("bounds", ""))
    if not match:
        return None
    left, top, right, bottom = (int(value) for value in match.groups())
    return ((left + right) // 2, (top + bottom) // 2)

def _find_ui_node(*needles):
    """Find a visible accessibility node by text or content description."""
    root = _ui_tree()
    if root is None:
        return None
    markers = tuple(str(needle).casefold() for needle in needles)
    for node in root.iter("node"):
        label = _node_label(node)
        if label and any(marker in label for marker in markers):
            center = _node_center(node)
            if center is not None:
                return center
    return None

def _wait_for_ui_node(*needles, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        center = _find_ui_node(*needles)
        if center is not None:
            return center
        time.sleep(0.5)
    return None

def _wait_for_package(package, timeout=20):
    """Wait until the requested Android package owns the focused window."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if package in output("dumpsys window windows"):
            return True
        time.sleep(0.5)
    return False

def ensure_awake(timeout=20):
    """Wake the Fire TV through ADB and require a real awake-state confirmation."""
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            if awake():
                return
            key("KEYCODE_HOME")
        except Exception as exc:
            last_error = exc
        time.sleep(2)
    detail = f": {last_error}" if last_error else ""
    raise SystemExit("Fire TV no confirmó estado despierto" + detail)

def enter_denis_profile():
    """Select Denis when the YouTube profile picker is shown; skip it if already inside YouTube."""
    search_markers = ("buscar", "búsqueda", "busqueda", "search")
    if _find_ui_node(*search_markers) is not None:
        return
    profile = _wait_for_ui_node("denis", timeout=12)
    if profile is not None:
        tap(*profile)
    else:
        # Some Fire TV YouTube builds expose no profile text to UIAutomator; use the focused profile.
        key("KEYCODE_DPAD_CENTER")
    time.sleep(3)

def focus_youtube_search():
    """Focus YouTube search before injecting text; retain keyboard/coordinate fallbacks for older builds."""
    search_markers = ("buscar", "búsqueda", "busqueda", "search")
    search = _wait_for_ui_node(*search_markers, timeout=8)
    if search is not None:
        tap(*search)
    else:
        key("KEYCODE_SEARCH")
        time.sleep(2)
        search = _find_ui_node(*search_markers)
        if search is not None:
            tap(*search)
        else:
            tap(1085, 465)
    time.sleep(2)

def tv_volume_level():
    """Return the tracked visible TV volume, defaulting to the confirmed 10."""
    try:
        value = int(open(TV_VOLUME_STATE, encoding="ascii").read().strip())
    except (OSError, ValueError):
        value = 10
    return min(100, max(0, value))

def save_tv_volume_level(value):
    """Persist the last requested visible TV level with restrictive permissions."""
    temporary = TV_VOLUME_STATE + ".tmp"
    with open(temporary, "w", encoding="ascii") as handle:
        handle.write(str(value) + "\n")
    os.chmod(temporary, 0o600)
    os.replace(temporary, TV_VOLUME_STATE)

def volume(level):
    """Set the visible TV level through Fire TV remote volume keys."""
    if not isinstance(level, int) or not 0 <= level <= 100:
        raise SystemExit("El volumen debe estar entre 0 y 100")
    current = tv_volume_level()
    key_name = "KEYCODE_VOLUME_UP" if level > current else "KEYCODE_VOLUME_DOWN"
    for _ in range(abs(level - current)):
        key(key_name)
        time.sleep(0.08)
    save_tv_volume_level(level)
    print(f"OK: volumen solicitado al TV {level}% mediante el mando Fire TV")

def volume_delta(direction, steps):
    """Move the tracked visible TV volume by a bounded number of points."""
    if direction not in {"up", "down"} or not 1 <= steps <= 3:
        raise SystemExit("Dirección o pasos de volumen no permitidos")
    current = tv_volume_level()
    target = min(100, current + steps) if direction == "up" else max(0, current - steps)
    key_name = "KEYCODE_VOLUME_UP" if direction == "up" else "KEYCODE_VOLUME_DOWN"
    for _ in range(abs(target - current)):
        key(key_name)
        time.sleep(0.08)
    save_tv_volume_level(target)
    print(f"OK: volumen solicitado al TV {target}% mediante el mando Fire TV")

def news():
    now=datetime.now(); query=f"Noticias ecuador {now.day} de {MONTHS[now.month-1]} {now.year}"
    ensure_awake()
    key("KEYCODE_HOME")
    run("am force-stop " + YOUTUBE_PACKAGE)
    run("am start -n " + YOUTUBE_PACKAGE + "/dev.cobalt.app.MainActivity")
    if not _wait_for_package(YOUTUBE_PACKAGE):
        raise SystemExit("YouTube no confirmó la ventana activa")
    time.sleep(3)
    enter_denis_profile()
    focus_youtube_search()
    run("input text " + query.replace(" ", "%s"))
    time.sleep(2)
    key("KEYCODE_ENTER")
    if not _wait_for_package(YOUTUBE_PACKAGE, timeout=10):
        raise SystemExit("YouTube perdió la ventana activa después de buscar")
    time.sleep(10)
    print("OK: YouTube noticias: "+query)
def netflix():
    """Launch Netflix cold so the app presents its profile picker."""
    ensure_awake()
    key("KEYCODE_HOME")
    run("am force-stop " + NETFLIX_PACKAGE)
    run("am start -n " + NETFLIX_PACKAGE + "/.MainActivity")
    if not _wait_for_package(NETFLIX_PACKAGE, timeout=15):
        raise SystemExit("Netflix no confirmó la ventana activa")
    time.sleep(8)
    print("OK: Netflix abierta en el selector de perfiles")
def ecuavisa():
    package = "com.digitalproserver.ecuavisa"
    activity = package + "/.WelcomeVideoActivity"
    key("KEYCODE_HOME")
    time.sleep(2)
    run("am force-stop " + package)
    run("am start -n " + activity)
    time.sleep(8)
    focused = output("dumpsys window windows")
    if package not in focused:
        raise SystemExit("Ecuavisa Play no confirmó la pantalla activa")
    print("OK: Ecuavisa Play abierta")

if len(sys.argv) == 2 and sys.argv[1] in {"volume", "volume_delta"}:
    raise SystemExit("usage: firetv_adb.py volume LEVEL | volume_delta up|down STEPS")
if len(sys.argv)!=2 and not (len(sys.argv)==3 and sys.argv[1]=="volume") and not (len(sys.argv)==4 and sys.argv[1]=="volume_delta"):
    raise SystemExit("usage: firetv_adb.py wake|off|news|netflix|ecuavisa|volume LEVEL|volume_delta up|down STEPS")
if sys.argv[1]=="news": news()
elif sys.argv[1]=="netflix": netflix()
elif sys.argv[1]=="ecuavisa": ecuavisa()
elif sys.argv[1]=="wake":
    key("KEYCODE_HOME")
    time.sleep(2)
    if not awake():
        key("KEYCODE_HOME")
        time.sleep(2)
    if not awake():
        raise SystemExit("Fire TV no confirmó estado despierto")
elif sys.argv[1]=="off":
    # KEYCODE_SLEEP is the reliable standby operation on this Fire TV.
    for _ in range(2):
        key("KEYCODE_SLEEP")
        time.sleep(2)
        if not awake():
            print("OK: Fire TV en standby")
            break
    else:
        raise SystemExit("Fire TV no confirmó standby después de 2 intentos")
elif sys.argv[1]=="volume":
    try:
        requested = int(sys.argv[2])
    except (IndexError, ValueError):
        raise SystemExit("El volumen debe ser un entero entre 0 y 100")
    volume(requested)
elif sys.argv[1]=="volume_delta":
    try:
        volume_delta(sys.argv[2], int(sys.argv[3]))
    except (IndexError, ValueError):
        raise SystemExit("usage: firetv_adb.py volume_delta up|down STEPS")
else: raise SystemExit("unknown action")
