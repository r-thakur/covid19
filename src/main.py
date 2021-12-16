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
import io


app = Flask(__name__)
regions = {}
caseInformation = {}
lastUpdatedTime = ""
prevURL = ""

vaccineUpdateDate = ""
ontarioUpdateDate = ""
pdfUpdateDate = ""

# lock = Lock()
# initNeeded = True

def parsePDF(fileLocation):
    global regions
    regions.clear()

    print(fileLocation)

    '''
    hdr = {'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
  'sec-ch-ua-mobile': '?0',
  'Upgrade-Insecure-Requests': '1',
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
  'accept': '*/*'}
    requestWHeader = Request(fileLocation, headers=hdr)
    pdfFile = urlopen(requestWHeader,context = ssl.SSLContext())
    data = pdfFile.read()
    bytesFile = io.BytesIO(data)
    read_pdf = PyPDF2.PdfFileReader(bytesFile)
    '''

    payload={}
    headers = {
    'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
    'sec-ch-ua-mobile': '?0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
    }

    response = requests.request("GET", fileLocation, headers=headers, data=payload)
    data = response.content
    bytesFile = io.BytesIO(data)
    read_pdf = PyPDF2.PdfFileReader(bytesFile)


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
        x = re.findall("[A-Z][a-z&A-Z ,*/-]+ +[-0-9,*]+ +[-0-9,*]+", page_content)
        healthUnits = []
        for subString in x:
            if "health" in subString.lower():
                healthUnits.append(subString)
        for subString in healthUnits:
            healthUnitsWithValues = subString.split(" ")

            healthUnitsWithValues = list(filter(None, healthUnitsWithValues)) 

            currLastDay = re.sub('[^0-9/-]','', healthUnitsWithValues[-2]) 
            currDay = re.sub('[^0-9/-]','', healthUnitsWithValues[-1])  
            tempName = ""
            for x in healthUnitsWithValues[:-2]:
                tempName = tempName + x + " "
            tempName = re.sub('[^a-z A-Z]','',tempName[:-1])
            tempRegion = region.Region(tempName,0,currDay,currLastDay)
            regions[tempName] = tempRegion
        popFile = open("HealthUnitPopulations.txt",'r')
        for x in popFile:
            currRegion = x.replace("\n","")
            if currRegion in regions.keys():
                population = int(next(popFile))
                regions[currRegion].setPopulation(population)     
                regions[currRegion].calculatePer100()
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
    return flask.render_template('index.html',\
        NewCases=caseInformation["NewCasesToday"],\
            TotalTests=caseInformation["TotalTestsCompleted"],\
                PercentPositive=caseInformation["PercentPositive"],\
                    GTARows=gtaData, \
                        OutsideRows = outsideData,\
                            ActiveCases = caseInformation["TotalActiveCases"],\
                                DeltaActiveCases = caseInformation["DeltaActiveCases"], \
                                    DeltaHospitalizations = caseInformation["DeltaHospitalizations"], \
                                        TotalHospitalizations = caseInformation["TotalHospitalizations"], \
                                            LastUpdated = lastUpdatedTime.date(),\
                                                Per100k = per100,\
                                                    DeltaWeekActiveCases = caseInformation["DeltaWeekActiveCases"],\
                                                        DeltaWeekHospitalizations = caseInformation["DeltaWeekHospitalizations"],\
                                                            TotalICUCases = caseInformation["TotalICUCases"],\
                                                                Deaths = caseInformation["Deaths"],\
                                                                    DeltaWeekDeaths = caseInformation["DeltaWeekDeaths"],\
                                                                        VaccineDate = caseInformation["VaccineDate"],\
                                                                            VaccinesAdministered = caseInformation["VaccinesAdministered"],\
                                                                                VaccinePercentage = caseInformation["VaccinePercentage"],\
                                                                                    PrevVaccineDate= caseInformation["PrevVaccineDate"],\
                                                                                        DeltaVaccinesAdministered = caseInformation["DeltaVaccinesAdministered"],\
                                                                                            LastUpdatedDate = caseInformation["LastUpdatedDate"],\
                                                                                                PDFUpdatedDate = caseInformation["PDFUpdatedDate"],\
                                                                                                    VaccinesCompleted = caseInformation["VaccinesCompleted"],
                                                                                                    PeopleWithAtLeastOneDose = caseInformation["PeopleWithAtLeastOneDose"],
                                                                                                    OneDoseVaccinePercentage = caseInformation["OneDoseVaccinePercentage"],
                                                                                                    PeopleWithThreeDoses = caseInformation["PeopleWithThreeDoses"],
                                                                                                    ThreeDoseVaccinePercentage = caseInformation["ThreeDoseVaccinePercentage"])


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
    #if (timeRightNow > timeAt1030 and timeAt1030 > lastUpdatedTime):
    url = pullPDF()
    if (url != prevURL):
        parsePDF(url)
        prevURL = url
    if (pdfUpdateDate > vaccineUpdateDate):
        pullCSV()

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
    global caseInformation, pdfUpdateDate
    pdfFilePage = requests.get("https://covid-19.ontario.ca/covid-19-epidemiologic-summaries-public-health-ontario")
    html = pdfFilePage.text
    soup = BeautifulSoup(html, "html.parser")
    linkLookupStr = (soup.find("div", {"id": "block-ds-theme-content"}).findAll("a"))
    #regexString = '(?<=\<a href=").+?(pdf)'
    #x = re.findall(regexString, linkLookupStr)[0]

    currURL = str(linkLookupStr[3]).split('\"')[1]

    caseInformation["PDFUpdatedDate"] = (re.findall("[0-9]+-[0-9]+-[0-9]+",currURL))[0]
    pdfUpdateDate = datetime.strptime(caseInformation["PDFUpdatedDate"], '%Y-%m-%d')
    return currURL


def checkIfEmptyAndConvertToInt(cell):
    if (not cell.isnull().values.any()):
        return int(cell.values[0])
    else:
        return "Not Available"



def pullCSV():
    global caseInformation, vaccineUpdateDate, ontarioUpdateDate
    csvURL = "https://data.ontario.ca/dataset/f4f86e54-872d-43f8-8a86-3892fd3cb5e6/resource/ed270bb8-340b-41f9-a7c6-e8ef587e6d11/download/covidtesting.csv"

    vaccineURL = "https://data.ontario.ca/dataset/752ce2b7-c15a-4965-a3dc-397bf405e7cc/resource/8a89caa9-511c-4568-af89-7f2174b4378c/download/vaccine_doses.csv"

    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'}
    requestWHeader = Request(csvURL, headers=hdr)
    csvFile = urlopen(requestWHeader,context = ssl.SSLContext())

    vaccineWHeader = Request(vaccineURL, headers=hdr)
    vaccineData = urlopen(vaccineWHeader,context = ssl.SSLContext())


    vaccineDF = pandas.read_csv(vaccineData)
    vaccineDF.dropna(subset = ["report_date"], inplace=True)
    lastVaccineRow = vaccineDF.tail(1)
    prevVaccineRow = vaccineDF.tail(2).head(1)
    caseInformation["VaccineDate"] = lastVaccineRow["report_date"].values[0]
    # vaccineUpdateDate = datetime.strptime(caseInformation["VaccineDate"], '%Y-%m-%d')
    try:
        caseInformation["VaccineDate"] = datetime.strptime(caseInformation["VaccineDate"], "%m/%d/%Y").strftime("%Y-%m-%d") 
        vaccineUpdateDate = datetime.strptime(caseInformation["VaccineDate"], '%Y-%m-%d')
    except:
        caseInformation["VaccineDate"] = lastVaccineRow["report_date"].values[0]
        vaccineUpdateDate = datetime.strptime(caseInformation["VaccineDate"], '%Y-%m-%d')

    caseInformation["PrevVaccineDate"] = prevVaccineRow["report_date"].values[0]
    try:
        caseInformation["PrevVaccineDate"] = datetime.strptime(caseInformation["PrevVaccineDate"], "%m/%d/%Y").strftime("%Y-%m-%d") 
    except:
        caseInformation["PrevVaccineDate"] = prevVaccineRow["report_date"].values[0]

    caseInformation["VaccinesAdministered"] = lastVaccineRow["total_doses_administered"].values[0]
    caseInformation["VaccinesCompleted"] = str(int(lastVaccineRow["total_individuals_fully_vaccinated"].values[0]))


    caseInformation["PeopleWithAtLeastOneDose"] = int(lastVaccineRow["total_individuals_at_least_one"].values[0])
    #print(caseInformation["VaccinesAdministered"])
    caseInformation["PrevVaccinesAdministered"] = prevVaccineRow["total_doses_administered"].values[0]

    caseInformation["PeopleWithThreeDoses"] = int(prevVaccineRow["total_individuals_3doses"].values[0])

    caseInformation["DeltaVaccinesAdministered"] = str(int(caseInformation["VaccinesAdministered"]) - int(caseInformation["PrevVaccinesAdministered"]))

    if caseInformation["VaccinesCompleted"] != "Not Available":
        vaccinePerPopulationPercentage = str(round((float(caseInformation["VaccinesCompleted"]))/(12*10000),2))+"%"
        caseInformation["VaccinePercentage"] = vaccinePerPopulationPercentage
        caseInformation["OneDoseVaccinePercentage"] = str(round((float(caseInformation["PeopleWithAtLeastOneDose"]))/(14.75*10000),2))+"%"
        caseInformation["ThreeDoseVaccinePercentage"] = str(round((float(caseInformation["PeopleWithThreeDoses"]))/(14.75*10000),2))+"%"


    df = pandas.read_csv(csvFile)
    lastRow = df.tail(1)
    secondLastRow = df.tail(2)
    seventhLastRow = df.tail(7)

    
    #caseInformation["LastUpdatedDate"] = datetime.strptime(lastRow['Reported Date'].values[0], "%m/%d/%Y").strftime("%Y-%m-%d")  
    caseInformation["LastUpdatedDate"] = lastRow['Reported Date'].values[0]
    try:
        ontarioUpdateDate = datetime.strptime(caseInformation["LastUpdatedDate"], '%Y-%m-%d')
    except:
        pass

    caseInformation["DeltaActiveCases"] = int(lastRow['Confirmed Positive'].values[0] - secondLastRow['Confirmed Positive'].head(1).values[0])
    if (caseInformation["DeltaActiveCases"] >= 0):
        caseInformation["DeltaActiveCases"] = '+'+str(caseInformation["DeltaActiveCases"])
    else:
        caseInformation["DeltaActiveCases"] = str(caseInformation["DeltaActiveCases"])


    caseInformation["DeltaWeekActiveCases"] = int(lastRow['Confirmed Positive'].values[0] - seventhLastRow['Confirmed Positive'].head(1).values[0])
    if (caseInformation["DeltaWeekActiveCases"] >= 0):
        caseInformation["DeltaWeekActiveCases"] = '+'+str(caseInformation["DeltaWeekActiveCases"])
    else:
        caseInformation["DeltaWeekActiveCases"] = str(caseInformation["DeltaWeekActiveCases"])


    caseInformation["TotalActiveCases"] = int(lastRow['Confirmed Positive'].values[0])

    if (not lastRow['Number of patients in ICU, testing positive for COVID-19'].isnull().values.any()):
        caseInformation["TotalICUCases"] = int(lastRow['Number of patients in ICU, testing positive for COVID-19'].values[0])
    else:
        caseInformation["TotalICUCases"] = "Value not available"

    

    caseInformation["TotalHospitalizations"] = int(lastRow['Number of patients hospitalized with COVID-19'].values[0])
    caseInformation["DeltaHospitalizations"] = int(lastRow['Number of patients hospitalized with COVID-19'].values[0] - secondLastRow['Number of patients hospitalized with COVID-19'].head(1).values[0])
    if (caseInformation["DeltaHospitalizations"] >= 0):
        caseInformation["DeltaHospitalizations"] = '+'+str(caseInformation["DeltaHospitalizations"])
    else:
        caseInformation["DeltaHospitalizations"] = str(caseInformation["DeltaHospitalizations"])

    caseInformation["DeltaWeekHospitalizations"] = int(lastRow['Number of patients hospitalized with COVID-19'].values[0] - seventhLastRow['Number of patients hospitalized with COVID-19'].head(1).values[0])
    if (caseInformation["DeltaWeekHospitalizations"] >= 0):
        caseInformation["DeltaWeekHospitalizations"] = '+'+str(caseInformation["DeltaWeekHospitalizations"])
    else:
        caseInformation["DeltaWeekHospitalizations"] = str(caseInformation["DeltaWeekHospitalizations"])


    caseInformation["Deaths"] = int(lastRow['Deaths'].values[0])
    caseInformation["DeltaWeekDeaths"] = int(lastRow['Deaths'].values[0] - seventhLastRow['Deaths'].head(1).values[0])
    if (caseInformation["DeltaWeekDeaths"] >= 0):
        caseInformation["DeltaWeekDeaths"] = '+'+str(caseInformation["DeltaWeekDeaths"])
    else:
        caseInformation["DeltaWeekDeaths"] = str(caseInformation["DeltaWeekDeaths"])



    caseInformation["NewCasesToday"] = int(lastRow['Total Cases'].values[0] - secondLastRow['Total Cases'].head(1).values[0])
    caseInformation["TotalTestsCompleted"] = checkIfEmptyAndConvertToInt(lastRow['Total tests completed in the last day'])
    #print(caseInformation["TotalTestsCompleted"])

    if (caseInformation["TotalTestsCompleted"] is not "Not Available"):
        caseInformation["PercentPositive"] = str(round((float(caseInformation["NewCasesToday"])/float(caseInformation["TotalTestsCompleted"])*100),2))
    else:
        caseInformation["PercentPositive"] = "?"

#initData()

if __name__ == "__main__":
    prevURL = ""
    if (len(sys.argv) > 1):
        printAll(int(sys.argv[1]))
    else:
        app.run(host='0.0.0.0',port=config.PORT, debug=config.DEBUG_MODE)
        


    