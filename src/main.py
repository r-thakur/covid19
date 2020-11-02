import PyPDF2
from bs4 import BeautifulSoup
import requests
import json
import re
from urllib.request import urlopen, Request
import ssl
import sys
from string import Template
import config
import flask
import pandas
import region
from datetime import datetime, timedelta
from multiprocessing import Lock
from flask import Flask



app = Flask(__name__)
regions = {}
caseInformation = {}
lastUpdatedTime = ""
prevURL = ""

# lock = Lock()
# initNeeded = True

def parsePDF(fileLocation):
    global regions
    regions.clear()

    print(fileLocation)
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
    requestWHeader = Request(fileLocation, headers=hdr)
    pdfFile = urlopen(requestWHeader,context = ssl.SSLContext())
    data = pdfFile.read()
    with open("current.pdf", "wb") as code:
        code.write(data)



    pdf_file = open("current.pdf",'rb')
    read_pdf = PyPDF2.PdfFileReader(pdf_file)
    pages = []
    page = read_pdf.getPage(8)
    pages.append(page)
    page = read_pdf.getPage(9)
    pages.append(page)
    page = read_pdf.getPage(10)
    pages.append(page)

    for page in pages:
        page_content = page.extractText().replace("\n","")
        # print(page_content)
        x = re.findall("[A-Z][a-z&A-Z ,/-]+ +[-0-9]+ +[-0-9]+", page_content)
        healthUnits = []
        # x = x.split(" ")
        # print(x)
        for subString in x:
            if "health" in subString.lower():
                healthUnits.append(subString)
        for subString in healthUnits:
            healthUnitsWithValues = subString.split(" ")
            currLastDay = healthUnitsWithValues[-2]
            currDay = healthUnitsWithValues[-1]
            # print(currDay,currLastDay)
            #print(healthUnitsWithValues)
            tempName = ""
            for x in healthUnitsWithValues[:-2]:
                tempName = tempName + x + " "
            tempName = tempName[:-1]
            # print(tempName)
            tempRegion = region.Region(tempName,0,currDay,currLastDay)
            regions[tempName] = tempRegion
            
        popFile = open("HealthUnitPopulations.txt",'r')
        for x in popFile:
            currRegion = x.replace("\n","")
            if currRegion in regions.keys():
                population = int(next(popFile))
                regions[currRegion].setPopulation(population)     
                regions[currRegion].calculatePer100()
    pdf_file.close()
    popFile.close()

@app.route('/')
def hello_world():
    return ''


@app.route('/covidHTML/<per100>')
def covidInfoWithHTML(per100):
    refreshData()
    per100 = int(per100)
    gtaData = ""
    for x in regions.keys():
        if regions[x].isPartOfGTA():
            gtaData += '<tr>'
            gtaData += '<td data-label="Health District">' + regions[x].getName() + "</td>"
            gtaData += '<td data-label="New Cases Today">' + regions[x].getCasesTodayString() + "</td>"
            gtaData += '<td data-label="Cases Today (Per 100k)">' + str(regions[x].getPer100k()) + "</td>"
            gtaData += '<td data-label="Cases Yesterday">' + str(regions[x].getCasesYesterdayString()) + "</td>"
            gtaData += "</tr>"
    outsideData = ""
    for x in regions.keys():
        if regions[x].getPer100k() > per100 and not regions[x].isPartOfGTA():
            outsideData += '<tr>'
            outsideData += '<td data-label="Health District">' + regions[x].getName() + "</td>"
            outsideData += '<td data-label="New Cases Today">' + regions[x].getCasesTodayString() + "</td>"
            outsideData += '<td data-label="Cases Today (Per 100k)">' + str(regions[x].getPer100k()) + "</td>"
            outsideData += '<td data-label="Cases Yesterday">' + str(regions[x].getCasesYesterdayString()) + "</td>"
            outsideData += "</tr>"

    return flask.render_template('index.html',NewCases=caseInformation["NewCasesToday"],TotalTests=caseInformation["TotalTestsCompleted"],PercentPositive=caseInformation["PercentPositive"],GTARows=gtaData, OutsideRows = outsideData,ActiveCases = caseInformation["TotalActiveCases"],DeltaActiveCases = caseInformation["DeltaActiveCases"], DeltaHospitalizations = caseInformation["DeltaHospitalizations"], TotalHospitalizations = caseInformation["TotalHospitalizations"], LastUpdated = lastUpdatedTime.date(), Per100k = per100)

@app.route('/refresh')
def refreshDataEndpoint():
    # global initNeeded
    # initNeeded = True
    initData()
    return "Refresh was successful"

def refreshData():
    global prevURL, lastUpdatedTime
    timeAt1030 = datetime.today().replace(hour = 15, minute = 31, second= 0, microsecond=0)
    timeRightNow = datetime.today()
    if (timeRightNow > timeAt1030 and timeAt1030 > lastUpdatedTime):
        url = pullPDF()
        if (url != prevURL):
            parsePDF(url)
            pullCSV()
            prevURL = url
            lastUpdatedTime=datetime.today()

def initData():
    global prevURL, lastUpdatedTime
    url = pullPDF()
    parsePDF(url)
    pullCSV()
    prevURL = url
    lastUpdatedTime=datetime.today()
    print("Initialization complete")


# def initData():
#     global prevURL, lastUpdatedTime, initNeeded
#     with lock:
#         if (initNeeded):
#             initNeeded=False
#             url = pullPDF()
#             parsePDF(url)
#             pullCSV()
#             prevURL = url
#             lastUpdatedTime=datetime.today()
            
#             print("Initialization complete")


# def printAll(per100 = 2):
#     print(newCasesToday + "/" + totalTestsCompleted + " = " + str(round((float(newCasesToday)/float(totalTestsCompleted)*100),2))+"%")
#     print("(New Cases/Total Tests) completed in the last 24 hours")

#     print()
#     print("*GTA*")
#     for x in regions.keys():
#         if regions[x].isPartOfGTA():
#             regions[x].printRelevant()

#     print()
#     print("*Outside of GTA with greater than " + str(per100) + " per 100k*")
#     for x in regions.keys():
#         if regions[x].getPer100k() > per100 and not regions[x].isPartOfGTA():
#             regions[x].printRelevant()


def pullPDF():
    pdfFilePage = requests.get("https://covid-19.ontario.ca/covid-19-epidemiologic-summaries-public-health-ontario")
    html = pdfFilePage.text
    soup = BeautifulSoup(html, "html.parser")
    linkLookupStr = (soup.find("div", {"id": "block-ds-theme-content"}).findAll("a"))
    #regexString = '(?<=\<a href=").+?(pdf)'
    #x = re.findall(regexString, linkLookupStr)[0]

    currURL = str(linkLookupStr[3]).split('\"')[1]

    return currURL

def pullCSV():
    global caseInformation
    # global totalTestsCompleted, newCasesToday, totalActiveCases, deltaActiveCases
    csvURL = "https://data.ontario.ca/dataset/f4f86e54-872d-43f8-8a86-3892fd3cb5e6/resource/ed270bb8-340b-41f9-a7c6-e8ef587e6d11/download/covidtesting.csv"

    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'}
    requestWHeader = Request(csvURL, headers=hdr)
    csvFile = urlopen(requestWHeader,context = ssl.SSLContext())

    df = pandas.read_csv(csvFile)
    # deltaActiveCases = int(df.tail(1)['Confirmed Positive'].values[0] - df.tail(2)['Confirmed Positive'].head(1).values[0])
    caseInformation["DeltaActiveCases"] = int(df.tail(1)['Confirmed Positive'].values[0] - df.tail(2)['Confirmed Positive'].head(1).values[0])
    if (caseInformation["DeltaActiveCases"] >= 0):
        # deltaActiveCases = '+'+str(deltaActiveCases)
        caseInformation["DeltaActiveCases"] = '+'+str(caseInformation["DeltaActiveCases"])
    else:
        # deltaActiveCases = '-'+str(deltaActiveCases)
        caseInformation["DeltaActiveCases"] = str(caseInformation["DeltaActiveCases"])

    # totalActiveCases = int(df.tail(1)['Confirmed Positive'].values[0])
    caseInformation["TotalActiveCases"] = int(df.tail(1)['Confirmed Positive'].values[0])

    caseInformation["TotalHospitalizations"] = int(df.tail(1)['Number of patients hospitalized with COVID-19'].values[0])
    caseInformation["DeltaHospitalizations"] = int(df.tail(1)['Number of patients hospitalized with COVID-19'].values[0] - df.tail(2)['Number of patients hospitalized with COVID-19'].head(1).values[0])
    if (caseInformation["DeltaHospitalizations"] >= 0):
        # deltaActiveCases = '+'+str(deltaActiveCases)
        caseInformation["DeltaHospitalizations"] = '+'+str(caseInformation["DeltaHospitalizations"])
    else:
        # deltaActiveCases = '-'+str(deltaActiveCases)
        caseInformation["DeltaHospitalizations"] = str(caseInformation["DeltaHospitalizations"])


    # newCasesToday = int(df.tail(1)['Total Cases'].values[0] - df.tail(2)['Total Cases'].head(1).values[0])
    caseInformation["NewCasesToday"] = int(df.tail(1)['Total Cases'].values[0] - df.tail(2)['Total Cases'].head(1).values[0])
    # totalTestsCompleted = int(df.tail(1)['Total tests completed in the last day'].values[0])
    caseInformation["TotalTestsCompleted"] = int(df.tail(1)['Total tests completed in the last day'].values[0])

    caseInformation["PercentPositive"] = str(round((float(caseInformation["NewCasesToday"])/float(caseInformation["TotalTestsCompleted"])*100),2))

initData()

if __name__ == "__main__":
    prevURL = ""
    if (len(sys.argv) > 1):
        printAll(int(sys.argv[1]))
    else:
        app.run(host='0.0.0.0',port=config.PORT, debug=config.DEBUG_MODE)
        


    