from channels.consumer import SyncConsumer

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from web_scrapper.settings import BASE_DIR

from pathlib import Path

import json
import time
import os
import pandas as pd

class EchoConsumer(SyncConsumer):
    
    WEB_API_PATH = f"{Path(__file__).resolve().parent.parent.parent.absolute()}/web_api/"
    print(os.path.join(WEB_API_PATH, "courseFiles"))

    wd_options = Options()
    wd_service = Service(executable_path=os.path.join(BASE_DIR, './chromedriver'))
    wd_prefs = {"download.default_directory" : os.path.join(BASE_DIR, "courseFiles")}
    wd_options.add_experimental_option("prefs",wd_prefs)
    wd_options.add_argument("--no-sandbox")
    wd_options.add_argument("--disable-dev-shm-usage")
    wd_options.add_argument('--headless')
    
    def websocket_connect(self, event):
      print("[socket] connect event called")

      self.wd = webdriver.Chrome(options=self.wd_options, service=self.wd_service)
      self.wd_wait = WebDriverWait(self.wd, 10)

      self.send({
         'type': 'websocket.accept'
      })

    def websocket_receive(self, event):
      print("[socket] Empezando...")

      receive_payload = json.loads(event.get('text'))

      print(f"payload: {receive_payload}")

      if(receive_payload['type'] == 'login'):
         
        self.wd.get("https://moodle.uam.es/login/index.php")

        time.sleep(4)
        self.wd_wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-identityprovider-btn')))

        self.wd.find_element(By.CLASS_NAME, 'login-identityprovider-btn').click()

        time.sleep(4)
        self.wd_wait.until(EC.presence_of_element_located((By.ID, 'i0116')))
        
        self.wd.find_element(By.ID, 'i0116').send_keys(receive_payload['username'])
        self.wd.find_element(By.ID, 'idSIButton9').click()

        time.sleep(4)
       
        self.wd_wait.until(EC.presence_of_element_located((By.ID, 'i0118')))

        try:
            self.wd_wait.until(EC.presence_of_element_located((By.ID, 'usernameError')))

            send_payload = {"type": "login_error", "data": "El nombre de usuario proporcionado no existe."}
            self.send({
            'type': 'websocket.send',
            'text': json.dumps(send_payload)
            })

            self.wd.close()

            return

        except TimeoutException:
          pass

        self.wd.find_element(By.ID, 'i0118').send_keys(receive_payload['password'])
        self.wd.find_element(By.ID, 'idSIButton9').click()

        try:
          self.wd_wait.until(EC.presence_of_element_located((By.ID, 'passwordError')))

          send_payload = {"type": "login_error", "data": "La contraseña proporcionada no existe."}
          self.send({
          'type': 'websocket.send',
          'text': json.dumps(send_payload)
          })

          self.wd.close()

          return
        except TimeoutException:
          pass

        self.wd_wait.until(EC.presence_of_element_located((By.ID, 'idRichContext_DisplaySign')))

        token = self.wd.find_element('id', 'idRichContext_DisplaySign').text
        
        tryes = 0
        while True:
            
            print(f"Your token is {token}")

            if tryes < 3:
              send_payload = {"type": "token", "token": token}
              self.send({
              'type': 'websocket.send',
              'text': json.dumps(send_payload)
              })
            else:
              send_payload = {"type": "token_failed"}
              self.send({
              'type': 'websocket.send',
              'text': json.dumps(send_payload)
              })
              
              self.wd.close()
            try:
                WebDriverWait(self.wd, 64).until(EC.presence_of_all_elements_located((By.ID, 'idDiv_SAASTO_Trouble')))
            except TimeoutException:
                break
            
            tryes += 1

            self.wd.get("https://moodle.uam.es/login/index.php")

            time.sleep(4)
            self.wd_wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-identityprovider-btn')))

            self.wd.find_element(By.CLASS_NAME, 'login-identityprovider-btn').click()

            self.wd_wait.until(EC.presence_of_element_located((By.ID, 'idRichContext_DisplaySign')))

            token = self.wd.find_element('id', 'idRichContext_DisplaySign').text

        send_payload = {"type": "token_success"}
        self.send({
        'type': 'websocket.send',
        'text': json.dumps(send_payload)
        })
        
        courseId = receive_payload['courseId'].replace("/", "")

        self.wd.get("https://moodle.uam.es/auth/saml2/login.php?wants&idp=cebe5294a678ea658b3001066ac8533e&passive=off")

        time.sleep(15)

        send_payload = {"type": "course_scrap", "data": "Descargando los datos de las actividades..."}
        self.send({
        'type': 'websocket.send',
        'text': json.dumps(send_payload)
        })

        self.wd.get(f"https://moodle.uam.es/grade/export/xls/index.php?id={courseId}")

        time.sleep(4)

        self.wd.find_element('id', 'id_submitbutton').click()

        time.sleep(4)

        self.wd.get(f"https://moodle.uam.es/course/view.php?id={courseId}")

        urls = self.wd.find_elements(By.TAG_NAME, "a")

        attendaceFilter = lambda elem: 'https://moodle.uam.es/mod/attendance' in elem.get_attribute('href') if elem.get_attribute('href') is not None else None
        filteredElems = filter(attendaceFilter, urls)
        attendanceUrl = next(filteredElems, None)

        attendanceId = attendanceUrl.get_attribute("href").split("?")[1].split("=")[1]

        send_payload = {"type": "course_scrap", "data": "Descargando los datos de las asistencias..."}
        self.send({
        'type': 'websocket.send',
        'text': json.dumps(send_payload)
        })

        self.wd.get(f"https://moodle.uam.es/mod/attendance/export.php?id={attendanceId}")

        self.wd_wait.until(EC.element_to_be_clickable((By.ID, "id_includenottaken")))

        self.wd.find_element(By.ID, "id_includenottaken").click()
        self.wd.find_element(By.ID, "id_submitbutton").click()

        time.sleep(3)

        self.wd.delete_all_cookies()

        self.wd.close()

        courseFiles = os.listdir(os.path.join(BASE_DIR, "courseFiles"))
        
        courseName = receive_payload['courseName']

        courseData = pd.read_excel(os.path.join(BASE_DIR, f"courseFiles/{courseName} Calificaciones.xlsx"))
        activitiesDataframe = pd.DataFrame(courseData)

        courseAttendance = pd.read_excel(os.path.join(BASE_DIR, f"courseFiles/{courseFiles[0] if courseFiles[0] != f'{courseName} Calificaciones.xlsx' else courseFiles[1]}"), skiprows=[0,1,2])
        attendanceDataframe = pd.DataFrame(courseAttendance)

        for file in os.listdir(os.path.join(BASE_DIR, "courseFiles")):
            os.remove(os.path.join(BASE_DIR, f"courseFiles/{file}"))

        send_payload = {"type": "scrap_success", "activities": activitiesDataframe.to_json(orient='records', force_ascii=False, default_handler=str), "attendance": attendanceDataframe.to_json(orient='records', force_ascii=False, default_handler=str)}
        self.send({
        'type': 'websocket.send',
        'text': json.dumps(send_payload)
        })
    
    def websocket_disconnect(self, event):
      print("[socket] connection closed")

    