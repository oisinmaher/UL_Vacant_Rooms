import os
import pickle


class ScrapeInfo():
    """Loads (or scrapes) the weekly room schedule and reports vacancies.

    All data returned by `run()` is plain structured data; rendering is the
    GUI's job.
    """

    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    TIMES = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]

    def __init__(self):
        self.building_rooms = {"Computer Science Building": ["CS1044", "CS1045", "CS2044", "CS2046", "CS3005A", "CS3005B", "CS3004B"]}
        self.building_to_pkl = {"Computer Science Building": "cs_building_schedule.pkl"}

    def get_room_timetable(self, room_number):
        """Scrape one room's weekly timetable from the UL timetable website.

        Returns a 5x9 boolean matrix (day x hour) where True means vacant.
        Selenium is imported lazily so the rest of the module works without it.
        """
        import time
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

    def retrieve(self, building):
        building_path = self.building_to_pkl[building]
        if os.path.exists(building_path) and os.path.getsize(building_path) > 0:
            with open(building_path, 'rb') as f:
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

        with open(self.building_to_pkl[building], 'wb') as f:
            pickle.dump(vacant_rooms, f)
        return vacant_rooms

    def run(self, building, day, time, force_scrape=False):
        """Return a structured report of vacant rooms for the given day/time.

        Result shape:
            {
                "building": str,
                "day": str,
                "slots": [(time_str, [room, ...]), ...],   # next 3 hours
                "fully_free": [room, ...],                  # free for all 3 hours
            }
        """
        vacant_rooms = None if force_scrape else self.retrieve(building)
        if vacant_rooms:
            print("Info retrieved from cache")
        else:
            print("No cached data, scraping info")
            vacant_rooms = self.build(building)

        d = self.DAYS.index(day)
        t = self.TIMES.index(time)
        t_last = min(9, t + 3)

        if t_last == 9:
            # No slot data beyond the last hour; start from all rooms
            # and let each listed slot narrow the set down.
            fully_free = set(self.building_rooms[building])
        else:
            fully_free = set(vacant_rooms[(d, t_last)])
        slots = []
        while t < t_last:
            current = sorted(vacant_rooms[(d, t)])
            slots.append((self.TIMES[t], current))
            fully_free = {room for room in current if room in fully_free}
            t += 1

        return {
            "building": building,
            "day": day,
            "slots": slots,
            "fully_free": sorted(fully_free),
        }
