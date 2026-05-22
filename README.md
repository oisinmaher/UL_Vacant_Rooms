# UL Vacant Rooms Display

This program allows you to choose a building in UL (currently only CS building), a day and a time. It will then output which rooms are vacant over the following 3 hours. This can be helpful if you want to go to a room to study, or work on project with your mates.
<br>
Gathers info from [UL Timetable Website](https://www.timetable.ul.ie/) using **Selenium**
Has a GUI built in **Qt** with **PySide6**
After scraping info, it is saved to a .pkl file using **Pickle** to prevent having to scrape info each use

Install Selenium and PySide6 with `pip install -r requirements.txt`

<img width="1920" height="1080" alt="vacant room showc" src="https://github.com/user-attachments/assets/69a31a73-baae-4efd-b7b4-f93b8cf43855" />
