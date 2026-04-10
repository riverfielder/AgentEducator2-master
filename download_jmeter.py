import urllib.request
import zipfile
import os
import sys

URL = "https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-5.6.3.zip"
ZIP_FILE = "jmeter.zip"

print(f"Downloading JMeter from {URL} ... This may take a minute or two.")
urllib.request.urlretrieve(URL, ZIP_FILE)

print("Download complete. Extracting...")
with zipfile.ZipFile(ZIP_FILE, 'r') as z:
    z.extractall('.')

print("Extraction complete. JMeter is installed at './apache-jmeter-5.6.3'.")
try:
    os.remove(ZIP_FILE)
except:
    pass
