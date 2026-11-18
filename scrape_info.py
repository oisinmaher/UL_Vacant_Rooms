"""Data layer for the UL vacant rooms app.

The selenium / Qt dependencies are imported lazily so this module can be
imported (and its pure data logic tested) in environments where they are
not installed.
"""

import os
import pickle
import time

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIMES = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]


class ScrapeInfo:
    def __init__(self):
        self._here = os.path.dirname(os.path.abspath(__file__))
        self.building_rooms = {
            "Computer Science Building": [
                "CS1044", "CS1045", "CS2044", "CS2046", "CS3005A", "CS3005B", "CS3004B",
            ]
        }
        self.building_to_pkl = {"Computer Science Building": "cs_building_schedule.pkl"}

    # ------------------------------------------------------------------ #
    # Scraping
    # ------------------------------------------------------------------ #
    def get_room_timetable(self, room_number):
        """Scrape the UL timetable site for a single room.

        Returns a 5 (days) x 9 (hours) matrix of booleans:
        ``vacant[day][hour] is True`` when the room is free.
        """
        # Imported lazily so this module works without selenium installed.
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.keys import Keys

        room_number = room_number.upper()
        driver = webdriver.Chrome()
        driver.get("https://www.timetable.ul.ie/UA/Default.aspx")

        time.sleep(1)
        cookies = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]'))
        )
        cookies.click()
        driver.get("https://www.timetable.ul.ie/UA/RoomTimetable.aspx")

        dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="select2-HeaderContent_RoomDropdown-container"]'))
        )
        dropdown.click()

        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/span/span/span[1]/input'))
        )
        search_box.send_keys(room_number)
        search_box.send_keys(Keys.RETURN)

        time.sleep(1)
        table = driver.find_element(By.XPATH, '//*[@id="MainContent_RoomTimetableGridView"]')
        rows_raw = table.find_elements(By.TAG_NAME, "tr")
        rows = []

        vacant = [[True] * 9 for _ in range(5)]
        for i in range(3, 20, 2):
            rows.append(rows_raw[i])
        for i in range(0, 9):
            cells = rows[i].find_elements(By.TAG_NAME, "td") or rows[i].find_elements(By.TAG_NAME, "th")
            for j in range(0, 5):
                if len(cells[j].text) > 1:
                    vacant[j][i] = False

        driver.quit()
        return vacant

    def _pkl_path(self, building):
        return os.path.join(self._here, self.building_to_pkl[building])

    def retrieve(self, building):
        building_path = self._pkl_path(building)
        if os.path.exists(building_path) and os.path.getsize(building_path) > 0:
            with open(building_path, "rb") as f:
                return pickle.load(f)
        return False

    def build(self, building):
        room_nums = self.building_rooms[building]
        vacant_rooms = {}
        for i in range(0, 5):
            for j in range(0, 9):
                vacant_rooms[(i, j)] = []
        for room in room_nums:
            print(room)
            vacant = self.get_room_timetable(room)
            for i in range(0, 5):
                for j in range(0, 9):
                    if vacant[i][j]:
                        vacant_rooms[(i, j)].append(room)

        with open(self._pkl_path(building), "wb") as f:
            pickle.dump(vacant_rooms, f)
        return vacant_rooms

    # ------------------------------------------------------------------ #
    # Querying
    # ------------------------------------------------------------------ #
    def query(self, building, day, time):
        """Return the free-room data for a building, day and start time.

        Returns a dict with:
        - ``day`` / ``building``: echoes of the input.
        - ``times``: list of start-of-hour labels covered (up to 3 hours).
        - ``slots``: list (parallel to ``times``) of room numbers free in
          that hour.
        - ``always_free``: rooms free for *every* hour in the range.
        """
        vacant_rooms = self.retrieve(building)
        if not vacant_rooms:
            print("No previous data, scraping info")
            vacant_rooms = self.build(building)
        else:
            print("Info retrieved from database")

        d = DAYS.index(day)
        t = TIMES.index(time)
        t_last = min(len(TIMES), t + 3)

        slots = [sorted(vacant_rooms.get((d, i), [])) for i in range(t, t_last)]
        always_free = sorted(set.intersection(*(set(rooms) for rooms in slots)))

        return {
            "building": building,
            "day": day,
            "times": TIMES[t:t_last],
            "slots": slots,
            "always_free": always_free,
        }

    def run(self, building, day, time):
        """Human-readable text version of :meth:`query` (kept for CLI use)."""
        result = self.query(building, day, time)
        span = f"{result['times'][0]}–{result['times'][-1]}" if len(result["times"]) > 1 else result["times"][0]
        lines = [f"{result['day']} {span}", ""]
        for hour, rooms in zip(result["times"], result["slots"]):
            lines.append(f"{hour}: {', '.join(rooms) if rooms else 'no rooms free'}")
        lines.append("")
        if result["always_free"]:
            lines.append(
                f"Rooms free for the full {len(result['times'])} hours: "
                f"{', '.join(result['always_free'])}"
            )
        else:
            lines.append(f"No rooms free for the full {len(result['times'])} hours")
        return "\n".join(lines)
