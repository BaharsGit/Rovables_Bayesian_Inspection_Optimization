import os
import shutil
folder = "../Log/" + "Run" + "9" + "/"
tempDir = "../controllers/bayes_supervisor/Data/Temp" + "9" + "/"
saveDest = "../controllers/bayes_supervisor/Data/Temp"
for file in os.listdir(tempDir):
    if file.endswith(".csv"):
        print("File FOUND")
        shutil.move(tempDir + file, folder + file)
    else: 
        print("NO FILE FOUND")

os.rmdir(tempDir)
