import requests
import json
from PIL import Image, ImageOps
import numpy as np
import pandas as pd
import os
import model
import time

LAT = 0
LONG = 1

import ray
ray.init(_node_ip_address="0.0.0.0")

def createRow(paths, row):
    paths = sorted(paths)
    images = [Image.open(f"./snapshots/{path}") for path in paths][::-1]

    width = sum([img.width for img in images])
    print(width)
    dst = Image.new('RGB', (width, images[0].height))

    for i in range(len(images)):
        img = images[i]
        dst.paste(img, (i * int(img.width), i))
  
    dst.save("./snapshotRows/{}.jpeg".format(str(row)))
    return dst

def cropIamges(images):
    for i, image in enumerate(images):
        width, height = image.size
        newImage = image.crop((0, 9, width, height))
        images[i] = newImage

    return images


def concatRows():
    paths = os.listdir("snapshotRows")

    paths = sorted(paths, key = lambda x : int(x.split(".")[0]))
    images = [Image.open(f"./snapshotRows/{path}") for path in paths]
    images = cropIamges(images)
    height = sum([img.height for img in images])
    dst = Image.new('RGB', (images[0].width, height))

    for i in range(len(images)):
        img = images[i]
        dst.paste(img, (0,  int(i * img.height) - 5))
  
    dst.save("./fullpic/{}.jpeg".format("full" ))
    return dst

def get_concat_v(im1, im2):
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst


def getImage(bottomLeft=(39.627921, -121.798852), topRight=(40.627921, -120.798852), filepath="", date="2021-07-14"):
    minLattitude, minLongitude = bottomLeft
    maxLattitude, maxLongitude = topRight

    # normal sattellite images 
    URL = """https://wvs.earthdata.nasa.gov/api/v1/snapshot?REQUEST=GetSnapshot&LAYERS=MODIS_Aqua_CorrectedReflectance_TrueColor,MODIS_Aqua_Thermal_Anomalies_Day&CRS=EPSG:4326&TIME={}&WRAP=DAY,DAY&BBOX={},{},{},{}&FORMAT=image/jpeg&WIDTH=455&HEIGHT=455&AUTOSCALE=FALSE&ts=1636752682648""".format(date, bottomLeft[LAT], bottomLeft[LONG], topRight[LAT], topRight[LONG])
   
#    neon green like images
    # URL = """https://wvs.earthdata.nasa.gov/api/v1/snapshot?REQUEST=GetSnapshot&LAYERS=MODIS_Terra_CorrectedReflectance_Bands721&CRS=EPSG:4326&TIME=2021-10-13&WRAP=DAY&BBOX={},{},{},{}&FORMAT=image/jpeg&WIDTH=800&HEIGHT=600&AUTOSCALE=TRUE&ts=1638048982455""".format(bottomLeft[LAT], bottomLeft[LONG], topRight[LAT], topRight[LONG])

    print(URL)
    resp = requests.get(URL, stream=True, data={"key1" : "value1"})
    if resp.status_code == 200:

        img = Image.open(resp.raw)
        if filepath:
            img.save(filepath)
        else:
            img.save(f"./snapshots/{minLattitude},{minLongitude},{maxLattitude},{maxLongitude}.jpeg")

    else:
        raise Exception("Too Many Requests")

remoteGetImage = ray.remote(getImage)

def createSearchGrid():
     

    # create boundary covering 
        #   N/S: northern Oregon to SoCal
        #   E/W : California coast to central Nevada

    topLeft = (45, -127)
    bottomLeft = (32, -127)
    
    topRight = (45, -117)
    bottomRight = (32, -117)

    searchHeight = abs(topLeft[LAT] - bottomLeft[LAT]) + 1
    searchWidth = abs(topLeft[LONG] - topRight[LONG]) + 1

    print(searchHeight, searchWidth)

    searchGrid = [[(0,0)] * searchWidth for x in range(searchHeight)]

    for x in range(len(searchGrid[0])):
        for y in range(len(searchGrid)):
            searchGrid[y][x] = (topLeft[LAT] - y, topLeft[LONG] + x)
            
    return searchGrid

def search(sg, date="2021-07-14", parallel=True):
    removeImages()
    # the anchoring point for each image search aka bottom left corner
    # top right coordinates will always be lat + 1 long + 1
    
    flattened = [j for sub in sg for j in sub]

    res_ids  = []
    startTime = time.time()
    for bl in flattened:
        tr = (bl[LAT] + 1, bl[LONG] + 1)

        if parallel:
            res_ids.append(remoteGetImage.remote(bl, tr, date=date))
        else:
            getImage(bl, tr, date=date)

    if parallel:
        ray.get(res_ids)

    endTime = time.time()

    print("\n\nTime Taken to Fetch Images: {}\n\n".format(endTime - startTime))
def getTrainingData(sg, dates=["2021-07-14"]):
    # the anchoring point for each image search aka bottom left corner
    # top right coordinates will always be lat + 1 long + 1
    
    flattened = [j for sub in sg for j in sub]

    for index, bl  in enumerate(flattened):
        for date in dates:
            tr = (bl[LAT] + 1, bl[LONG] + 1)
            getImage(bl, tr, filepath="{}_{}.jepg".format(date, index))

def printSG(sg):
    print(pd.DataFrame(sg))

def getRow(sg, row):
    return pd.DataFrame(sg).iloc[row]

def getRowPaths(row=None):
    row = list(map(str, row.values))
    allFiles  = os.listdir("./snapshots")
    paths = []
    
    for file in allFiles:
        # bl = "(" + ",".join(list(map(str,file))).split(",")[:2] + ")"
        bl = "(" + ", ".join(file.split(",")[:2]) + ")"
        if bl in row:
            paths.append(file)

    return paths
        # print(bl)

def createFinalRows(sg):
    for i in range(len(sg)):
        paths = getRowPaths(getRow(sg, i))
        print(paths)
        createRow(paths, i)

def predictFires():
    BASEPATH = "./snapshots"
    paths = os.listdir(BASEPATH)

    for img in paths: 
        isFire = model.predict(BASEPATH + "/" + img)
        # isFire = model.predict.remote(BASEPATH + "/" + img)

        if isFire: 
            print(img)
            orig = Image.open(BASEPATH + "/" + img).convert("L")
            red = ImageOps.colorize(orig, black ="red", white ="yellow")   
            red.save(BASEPATH + "/" + img)

def removeImages():
    dirs = ["./snapshots", "./snapshotRows", "./fullpic"]
    for d in dirs:
        filelist = [f for f in os.listdir(d) if f.endswith(".jpeg") ]
        for f in filelist:
            os.remove(os.path.join(d, f))



# divide up west coast into 1x1 deg squares
sg = createSearchGrid()
printSG(sg)

# scrape all of the imgs from NASA
search(sg, date="2017-12-09", parallel=False)
# printSG(getRow(sg, 0))

# predictFires()

createFinalRows(sg)

concatRows()

# get the training data
# [dixie, august fire complex, creek fire, thomas fire]
# getTrainingData(sg, dates=["2021-07-14", "2020-08-16", "2020-08-04", "2017-12-04"])
    
