from channels.generic.websocket import AsyncWebsocketConsumer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select


from web_scrapper.settings import BASE_DIR

from pathlib import Path

import json
import time
import os
import pandas as pd
import asyncio
import functools
from threading import Semaphore as sem

filesSem = sem()

def web_login_local(receive_payload, wd, wd_wait):
   
  wd.get("http://localhost:8080/login/index.php")

  time.sleep(4)
  wd_wait.until(EC.presence_of_element_located((By.ID, 'username')))
  
  wd.find_element(By.ID, 'username').send_keys(receive_payload['username'])
  wd.find_element(By.ID, 'password').send_keys(receive_payload['password'])
  wd.find_element(By.ID, 'loginbtn').click()

def web_scrap_local(receive_payload, wd, wd_wait):

  courseId = receive_payload['courseId'].replace("/", "")

  filesSem.acquire()

  print("[socket] Descargando datos...")

  wd.get(f"http://localhost:8080/grade/export/xls/index.php?id={courseId}")

  time.sleep(4)

  wd.find_element('id', 'id_submitbutton').click()

  time.sleep(4)

  wd.get(f"http://localhost:8080/course/view.php?id={courseId}")

  urls = wd.find_elements(By.TAG_NAME, "a")

  attendaceFilter = lambda elem: 'http://localhost:8080/mod/attendance' in elem.get_attribute('href') if elem.get_attribute('href') is not None else None
  filteredElems = filter(attendaceFilter, urls)
  attendanceUrl = next(filteredElems, None)

  attendanceId = attendanceUrl.get_attribute("href").split("?")[1].split("=")[1]

  wd.get(f"http://localhost:8080/mod/attendance/export.php?id={attendanceId}")

  wd_wait.until(EC.element_to_be_clickable((By.ID, "id_includenottaken")))

  wd.find_element(By.ID, "id_includenottaken").click()
  wd.find_element(By.ID, "id_submitbutton").click()

  time.sleep(3)

  wd.delete_all_cookies()

  wd.close()

  for file in os.listdir(os.path.join(BASE_DIR, "courseFiles")):
      os.remove(os.path.join(BASE_DIR, f"courseFiles/{file}"))

  courseFiles = os.listdir(os.path.join(BASE_DIR, "courseFiles"))
  
  courseName = receive_payload['courseName']

  courseData = pd.read_excel(os.path.join(BASE_DIR, f"courseFiles/{courseName} Calificaciones.xlsx"))
  activitiesDataframe = pd.DataFrame(courseData)

  courseAttendance = pd.read_excel(os.path.join(BASE_DIR, f"courseFiles/{courseFiles[0] if courseFiles[0] != f'{courseName} Calificaciones.xlsx' else courseFiles[1]}"), skiprows=[0,1,2])
  attendanceDataframe = pd.DataFrame(courseAttendance)

  for file in os.listdir(os.path.join(BASE_DIR, "courseFiles")):
      os.remove(os.path.join(BASE_DIR, f"courseFiles/{file}"))
  
  filesSem.release()

  return {"activitiesDataframe": activitiesDataframe, "attendanceDataframe": attendanceDataframe}

def web_login(receive_payload, wd, wd_wait):
  
  try:
    wd.get("https://moodle.uam.es/login/index.php")

    time.sleep(4)
    wd_wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-identityprovider-btn')))

    wd.find_element(By.CLASS_NAME, 'login-identityprovider-btn').click()

    time.sleep(4)
    wd_wait.until(EC.presence_of_element_located((By.ID, 'i0116')))
    
    wd.find_element(By.ID, 'i0116').send_keys(receive_payload['username'])
    wd.find_element(By.ID, 'idSIButton9').click()

    time.sleep(4)
    wd_wait.until(EC.presence_of_element_located((By.ID, 'i0118')))

    wd.find_element(By.ID, 'i0118').send_keys(receive_payload['password'])
    wd.find_element(By.ID, 'idSIButton9').click()

    wd_wait.until(EC.presence_of_element_located((By.ID, 'idRichContext_DisplaySign')))

    token = wd.find_element('id', 'idRichContext_DisplaySign').text
  except:
    return None
  
  return token

def web_token_confirm_app(wd, wd_wait):
    
    try:
      WebDriverWait(wd, 64).until(EC.presence_of_all_elements_located((By.ID, 'idDiv_SAASTO_Trouble')))
    except TimeoutException:

      return None
    
    wd.get("https://moodle.uam.es/login/index.php")

    time.sleep(4)
    wd_wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-identityprovider-btn')))

    wd.find_element(By.CLASS_NAME, 'login-identityprovider-btn').click()

    wd_wait.until(EC.presence_of_element_located((By.ID, 'idRichContext_DisplaySign')))

    token = wd.find_element('id', 'idRichContext_DisplaySign').text

    return token

def web_scrap(receive_payload, wd, wd_wait):

  filesSem.acquire()

  courseId = receive_payload['courseId'].replace("/", "")
  group = receive_payload['group'].replace("/", "")

  try:

    wd.get("https://moodle.uam.es/auth/saml2/login.php?wants&idp=cebe5294a678ea658b3001066ac8533e&passive=off")

    time.sleep(15)

    wd.get(f"https://moodle.uam.es/group/index.php?id={courseId}")

    wd_wait.until(EC.element_to_be_clickable((By.ID, "groups")))

    wd.get(f"https://moodle.uam.es/grade/export/xls/index.php?id={courseId}")

    wd.find_element('id', 'id_submitbutton').click()

    time.sleep(4)

    wd.get(f"https://moodle.uam.es/course/view.php?id={courseId}")

    urls = wd.find_elements(By.TAG_NAME, "a")

    attendaceFilter = lambda elem: 'https://moodle.uam.es/mod/attendance' in elem.get_attribute('href') if elem.get_attribute('href') is not None else None
    filteredElems = filter(attendaceFilter, urls)
    attendanceUrl = next(filteredElems, None)

    attendanceId = attendanceUrl.get_attribute("href").split("?")[1].split("=")[1]

    wd.get(f"https://moodle.uam.es/mod/attendance/export.php?id={attendanceId}")

    wd_wait.until(EC.element_to_be_clickable((By.ID, "id_includenottaken")))

    wd.find_element(By.ID, "id_includenottaken").click()
    wd.find_element(By.ID, "id_submitbutton").click()

    time.sleep(15)

    wd.delete_all_cookies()

    wd.close()

    courseFiles = os.listdir(os.path.join(BASE_DIR, "courseFiles"))
    
    courseName = receive_payload['courseName']

    courseData = pd.read_excel(os.path.join(BASE_DIR, f"courseFiles/{courseName} Calificaciones.xlsx"))
    activitiesDataframe = pd.DataFrame(courseData)

    #courseAttendance = pd.read_excel(os.path.join(BASE_DIR, f"courseFiles/prueba.xlsx"), skiprows=[0,1,2])
    courseAttendance = pd.read_excel(os.path.join(BASE_DIR, f"courseFiles/{courseFiles[0] if courseFiles[0] != f'{courseName} Calificaciones.xlsx' else courseFiles[1]}"), skiprows=[0,1,2])
    attendanceDataframe = pd.DataFrame(courseAttendance)

    for file in os.listdir(os.path.join(BASE_DIR, "courseFiles")):
      
      if file == 'prueba.xlsx':
        print(file)
      else:
        os.remove(os.path.join(BASE_DIR, f"courseFiles/{file}"))
  except Exception as e:

    print(e)
    filesSem.release()

    return None
  
  filesSem.release()

  return {"activitiesDataframe": activitiesDataframe, "attendanceDataframe": attendanceDataframe}

class EchoConsumer(AsyncWebsocketConsumer):
    
    WEB_API_PATH = f"{Path(__file__).resolve().parent.parent.parent.absolute()}/web_api/"
    
    wd_options = Options()
    
    wd_prefs = {"download.default_directory" : os.path.join(BASE_DIR, "courseFiles")}
    wd_options.add_experimental_option("prefs",wd_prefs)
    wd_options.add_argument("--no-sandbox")
    wd_options.add_argument("--disable-dev-shm-usage")
    wd_options.add_argument('--headless')
    
    latestchromedriver = ChromeDriverManager().install()
    wd_service = Service(executable_path=latestchromedriver)

    async def websocket_connect(self, event):

      print("[socket] connect event called")

      self.wd = webdriver.Chrome(service=self.wd_service, options=self.wd_options)
      self.wd_wait = WebDriverWait(self.wd, 10)

      await self.accept()

    async def websocket_receive(self, event):
      print("[socket] Empezando...")

      loop = asyncio.get_event_loop()

      receive_payload = json.loads(event.get('text'))

      if(receive_payload['type'] == 'login'):
        """
        # Web scrap for testing

        await loop.run_in_executor(None, functools.partial(web_login_local, receive_payload, self.wd, self.wd_wait))

        send_payload = {"type": "token_success"}
        await self.send(json.dumps(send_payload))

        courseInfo =  await loop.run_in_executor(None, functools.partial(web_scrap_local, receive_payload, self.wd, self.wd_wait))

        """

        # Web scrap in final moodle page

        token = await loop.run_in_executor(None, functools.partial(web_login, receive_payload, self.wd, self.wd_wait))

        if token is None:
          send_payload = {"type": "login_error", "data": "Error iniciando sesion, porfavor verificar las credenciales."}
          await self.send(json.dumps(send_payload))

          return

        token_attemp = 0
        while token != None:

          if token_attemp == 3:
            
            send_payload = {"type": "token_failed"}
            await self.send(json.dumps(send_payload))
            
            return
          
          send_payload = {"type": "token", "token": token}
          await self.send(json.dumps(send_payload))

          token = await loop.run_in_executor(None, functools.partial(web_token_confirm_app, self.wd, self.wd_wait))

          token_attemp += 1

        send_payload = {"type": "token_success"}
        await self.send(json.dumps(send_payload))
        
        courseInfo =  await loop.run_in_executor(None, functools.partial(web_scrap, receive_payload, self.wd, self.wd_wait))
        
        if courseInfo is None:
          send_payload = {"type": "scrap_error","data": "Error en la recopilacion de datos."}
          await self.send(json.dumps(send_payload))

          return

        send_payload = {"type": "scrap_success", "activities": courseInfo["activitiesDataframe"].to_json(orient='records', force_ascii=False, default_handler=str), "attendance": courseInfo["attendanceDataframe"].to_json(orient='records', force_ascii=False, default_handler=str)}
        await self.send(json.dumps(send_payload))
    
    async def websocket_disconnect(self, event):
      print("[socket] connection closed")

    