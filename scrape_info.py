import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import pickle
import time


class ScrapeInfo():
    def __init__(self):
        self.building_rooms = {"Computer Science Building": ["CS1044", "CS1045", "CS2044", "CS2046", "CS3005A", "CS3005B", "CS3004B"]}
        self.building_to_pkl = {"Computer Science Building": "cs_building_schedule.pkl"}

    def get_room_timetable(self, room_number):
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

        with open('cs_building_schedule.pkl', 'wb') as f:
            pickle.dump(vacant_rooms, f)
        return vacant_rooms

    def run(self, building, day, time):
        vacant_rooms = self.retrieve(building)
        if not vacant_rooms:
            print("No previous data, scraping info")
            vacant_rooms = self.build(building)
        else:
            print("Info retrieved from database")


        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        times = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]

        d = days.index(day)
        t = times.index(time)
        t_last = min(9, t+3)

        fully_free = set(vacant_rooms[(d, t_last)])
        rooms_vacant = f"{days[d]}:\n"
        while t < t_last:
            rooms_vacant += f"{times[t]}:\n"
            fully_free_temp = set()
            for room in vacant_rooms[(d, t)]:
                if room in fully_free:
                    fully_free_temp.add(room)

            fully_free = fully_free_temp
            rooms_vacant += f"{vacant_rooms[(d, t)]}\n"
            t += 1
        rooms_vacant += f"Rooms available for next 3 hours\n{fully_free}:\n"
        return rooms_vacant
