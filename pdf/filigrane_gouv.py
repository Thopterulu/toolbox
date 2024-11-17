from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

path = input("Entrez le chemin du dossier contenant le fichier PDF: ")

TEXT_FILIGRANE = "Document exclusivement destiné à la location immobilière"

# Set up Chrome driver
driver = webdriver.Firefox()

# Navigate to the webpage
driver.get("https://filigrane.beta.gouv.fr/")

# Locate the button
input_file = driver.find_element(By.ID, "file-upload")

# Fournir le chemin absolu du fichier à télécharger

input_file.send_keys(path)
time.sleep(2)

input_text = driver.find_element(By.CLASS_NAME, "fr-input")

input_text.send_keys(TEXT_FILIGRANE)

button_submit = driver.find_element(
    By.XPATH, "//button[span[text()='Ajouter le filigrane']]"
)
button_submit.click()

# time.sleep(20)

try:
    bouton = WebDriverWait(driver, 10).until(  # Attente de 10 secondes maximum
        EC.presence_of_element_located(
            (By.XPATH, "//a[contains(text(), 'Télécharger le document filigrané')]")
        )
    )
    print("Bouton trouvé !")
    bouton.click()  # Cliquer sur le bouton, si nécessaire
except:
    print("Le bouton n'est pas apparu dans le délai imparti.")
finally:
    time.sleep(10)
    driver.quit()
