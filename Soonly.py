import os
import json
import tkinter as tk
from datetime import datetime, timedelta, timezone
from dateutil import parser
from calendar_fetcher import get_upcoming_events, choose_calendars

CONFIG_FILE = "config.json"
CACHE_FILE = "events_cache.json"
CACHE_EXPIRY_MINUTES = 5

class ConfigManager:
    @staticmethod
    # Load configuration from config.json
    def load():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    @staticmethod
    # Save configuration to config.json
    def save(config):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    @staticmethod
    # Get saved window transparency
    def get_transparency():
        return float(ConfigManager.load().get("transparency", 0.9))

    @staticmethod
    # Set and save window transparency
    def set_transparency(value):
        cfg = ConfigManager.load()
        cfg["transparency"] = value
        ConfigManager.save(cfg)

    @staticmethod
    # Save window position and size
    def get_window_geometry():
        cfg = ConfigManager.load()
        return cfg.get("win_x", 100), cfg.get("win_y", 100), cfg.get("win_width", 400), cfg.get("win_height", 320)

    @staticmethod
    def set_window_geometry(x, y, width, height):
        cfg = ConfigManager.load()
        cfg.update({"win_x": x, "win_y": y, "win_width": width, "win_height": height})
        ConfigManager.save(cfg)

    @staticmethod
    # Get excluded event titles
    def get_excluded_titles():
        return ConfigManager.load().get("excluded_titles", [])

class CacheManager:
    @staticmethod
    # Load events from cache file
    def load():
        if not os.path.exists(CACHE_FILE):
            return None
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines[0].startswith("#"):
                    lines = lines[1:]
                data = json.loads("".join(lines))
            ts = parser.parse(data["timestamp"])
            if datetime.now(timezone.utc) - ts > timedelta(minutes=CACHE_EXPIRY_MINUTES):
                return None
            return data["events"]
        except:
            return None

    @staticmethod
    # Save events to cache file	
    def save(events):
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "events": events
        }
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(f"# Cached at {datetime.now().isoformat()}\n")
            json.dump(data, f, ensure_ascii=False, indent=2)

class EventWidget:
    # Initialize GUI and main loop
    def __init__(self):
        self.root = tk.Tk()
        self.event_data = []
        self.labels = []
        self.last_cache_time = None
        self.setup_ui()
        self.refresh_data()
        self.root.after(1000, self.update_display)
        self.root.mainloop()

    def setup_ui(self):
        # Create and configure main UI elements
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", ConfigManager.get_transparency())
        x, y, w, h = ConfigManager.get_window_geometry()
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self.countdown = tk.Label(self.root, font=("Arial", 16, "bold"), fg="blue")
        self.countdown.pack(pady=10)

        self.age_label = tk.Label(self.root, font=("Arial", 9), fg="gray")
        self.age_label.place(x=0, y=0)

        self.resize_handle = tk.Label(self.root, text="⬍", cursor="bottom_right_corner", fg="gray", font=("Arial", 12))
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        self.resize_handle.bind("<Button-1>", self.start_resize)
        self.resize_handle.bind("<B1-Motion>", self.do_resize)

        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)
        self.root.bind("<Configure>", self.save_position)
        self.root.bind("<Button-3>", self.show_context_menu)

        self.context_menu = self.build_menu()

    def start_resize(self, event):
        # Start resize drag
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._resize_start_width = self.root.winfo_width()
        self._resize_start_height = self.root.winfo_height()

    def do_resize(self, event):
        # Perform resize during drag
        dx = event.x_root - self._resize_start_x
        dy = event.y_root - self._resize_start_y
        new_width = max(200, self._resize_start_width + dx)
        new_height = max(150, self._resize_start_height + dy)
        self.root.geometry(f"{new_width}x{new_height}")
        ConfigManager.set_window_geometry(self.root.winfo_x(), self.root.winfo_y(), new_width, new_height)

    def build_menu(self):
        # Build right-click context menu
        menu = tk.Menu(self.root, tearoff=0)
        transparency = tk.Menu(menu, tearoff=0)
        for label, alpha in [("100%", 1.0), ("90%", 0.9), ("80%", 0.8), ("70%", 0.7)]:
            transparency.add_command(label=label, command=lambda v=alpha: self.set_transparency(v))
        menu.add_command(label="Refresh", command=self.manual_refresh)
        menu.add_cascade(label="Transparency", menu=transparency)
        menu.add_command(label="Select Calendars", command=self.open_calendar_chooser)
        menu.add_separator()
        menu.add_command(label="Close", command=self.root.destroy)
        return menu

    def start_move(self, event):
        # Start window drag
        self._x = event.x
        self._y = event.y

    def do_move(self, event):
        # Move window while dragging
        x = self.root.winfo_pointerx() - self._x
        y = self.root.winfo_pointery() - self._y
        self.root.geometry(f"+{x}+{y}")

    def save_position(self, event):
        # Save current window position and size
        ConfigManager.set_window_geometry(self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height())

    def set_transparency(self, val):
        # Set window transparency
        self.root.attributes("-alpha", val)
        ConfigManager.set_transparency(val)

    def show_context_menu(self, event):
        # Show right-click menu at cursor
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def refresh_data(self):
        # Periodically refresh event data
        cached = CacheManager.load()
        if cached:
            self.event_data = cached
        else:
            self.event_data = get_upcoming_events(count=10)
            CacheManager.save(self.event_data)
        self.root.after(300000, self.refresh_data)

    def manual_refresh(self):
        # Manual refresh of events
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        self.event_data = get_upcoming_events(count=10)
        CacheManager.save(self.event_data)
        self.update_display()

    def open_calendar_chooser(self):
        # 
        choose_calendars()
        self.manual_refresh()

    def update_display(self):
        # Update visual display of events
        for lbl in self.labels:
            lbl.destroy()
        self.labels.clear()

        now = datetime.now(timezone.utc)
        future = []
        excluded_titles = ConfigManager.get_excluded_titles()

        previous_event = None
        for event in self.event_data:
            title = event['summary'].strip() if 'summary' in event else "(ללא כותרת)"
            if title in excluded_titles:
                continue

            start = parser.parse(event['start'])
            end = parser.parse(event['end'])
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)

            if now < end:
                # If there is a previous event – calculate gap
                if previous_event:
                    prev_end = parser.parse(previous_event['end'])
                    if prev_end.tzinfo is None:
                        prev_end = prev_end.replace(tzinfo=timezone.utc)
                    gap_minutes = int((start - prev_end).total_seconds() / 60)
                    if gap_minutes > 0:
                        gap_label = tk.Label(
                            self.root,
                            text=f"{gap_minutes} דק׳",
                            fg="gray",
                            bg=self.root["bg"],
                            font=("Arial", 9),
                            wraplength=360,
                            justify="center"
                        )
                        gap_label.pack(pady=1)
                        self.labels.append(gap_label)

                # Event display	
                duration_minutes = int((end - start).total_seconds() / 60)

                if start <= now:
                    # Remaining time	
                    remaining = int((end - now).total_seconds() / 60)
                    remaining = max(0, remaining)
                    text = (
                        f"כעת: {title}\n"
                        f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')} "
                        f"(נותרו: {remaining} דק׳)"
                    )
                    color = "goldenrod"
                else:
                    text = (
                        f"{title}\n"
                        f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')} "
                        f"({duration_minutes} דק׳)"
                    )
                    color = "black"

                lbl = tk.Label(
                    self.root,
                    text=text,
                    fg=color,
                    bg=self.root["bg"],
                    font=("Arial", 10),
                    wraplength=360,
                    justify="center"
                )
                lbl.pack(pady=1)
                self.labels.append(lbl)

                previous_event = event
                future.append(event)

                if len(future) >= 10:
                    break

        if future:
            now = datetime.now(timezone.utc)
            first_event = future[0]
            first_start = parser.parse(first_event['start'])
            first_end = parser.parse(first_event['end'])

            countdown = None
            color = "gray"

            # Event hasn't started yet
            if now < first_start:
                countdown = first_start - now

            # Event started – show 00:00:00 for one minute
            elif first_start <= now < first_start + timedelta(minutes=1):
                self.countdown.config(text="00:00:00", fg="red")
            else:
                # After one minute – show countdown to next event
                next_event = None
                for evt in future[1:]:
                    evt_start = parser.parse(evt['start'])
                    if evt_start > now:
                        next_event = evt
                        break
                if next_event:
                    countdown = parser.parse(next_event['start']) - now

            if countdown and countdown.total_seconds() > 0:
                mins, secs = divmod(int(countdown.total_seconds()), 60)
                hours, mins = divmod(mins, 60)
                text = f"{hours:02}:{mins:02}:{secs:02}" if countdown.total_seconds() <= 60 else f"{hours:02}:{mins:02}"
                color = (
                    "green" if countdown.total_seconds() > 600
                    else "orange" if countdown.total_seconds() > 60
                    else "red"
                )
                self.countdown.config(text=text, fg=color)
            elif countdown is None:
                pass  # Already set to 00:00:00
            else:
                self.countdown.config(text="", fg="gray")

        if os.path.exists(CACHE_FILE):
            age = int((datetime.now() - datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))).total_seconds() / 60)
            self.age_label.config(text=f"{age} דק׳", fg="gray" if age < CACHE_EXPIRY_MINUTES else "red")

        self.root.after(1000, self.update_display)

if __name__ == "__main__":
    EventWidget()
