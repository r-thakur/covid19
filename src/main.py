import PyPDF2
from bs4 import BeautifulSoup
import requests
import json
import re
from urllib.request import urlopen, Request
import ssl
import sys
import server
from string import Template

import region
# import tabula


def parsePDF(fileLocation):
    global regions

    regions = {}

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
        x = re.findall("[A-Z][a-z&A-Z ,/-]+ +[0-9]+ +[0-9]+", page_content)
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


@server.app.route('/covid/<per100>')
def covidInfo(per100):
    per100 = int(per100)
    returnObj = ""
    returnObj += "<p>" + (newCasesToday + "/" + totalTestsCompleted + " = " + str(round((float(newCasesToday)/float(totalTestsCompleted.replace(",",""))*100),2))+"%") + "</p>"
    returnObj += "<p>(New Cases/Total Tests) completed in the last 24 hours</p>"
    returnObj += "<p></p>"
    for x in regions.keys():
        if regions[x].isPartOfGTA():
            returnObj += "<p>" + regions[x].getCasesTodayAndYestString() + "</p>"
            returnObj += "<p>" + regions[x].getPer100kString() + "</p>"
    returnObj += "<p></p>"
    returnObj += "<p>" + "*Outside of GTA with greater than " + str(per100) + " per 100k*" +"</p>"
    for x in regions.keys():
        if regions[x].getPer100k() > per100 and not regions[x].isPartOfGTA():
            returnObj += "<p>" + regions[x].getCasesTodayAndYestString() + "</p>"
            returnObj += "<p>" + regions[x].getPer100kString() + "</p>"
    return  returnObj
        

@server.app.route('/refresh')
def refreshData():
    parseSite()
    pullPDF()
    return "Refresh was successful"
    

def parseSite():
    global totalTestsCompleted
    global newCasesToday
    jsonAsText = requests.get("https://api.ontario.ca/api/drupal/page%2Fhow-ontario-is-responding-covid-19?fields=body")
    # print jsonAsText
    jsonObj = jsonAsText.json()
    html= jsonObj["body"]["und"][0]["value"]
    soup = BeautifulSoup(html, "html.parser")
    soupStr = str(soup)
    #Find total tests completed in the last day
    x = re.findall("Total tests completed in the previous day.+\n.+", soupStr)[0]
    x = x.split("<td>")[1]
    x = x.split("</td>")[0]
    totalTestsCompleted = x

    #Find total new cases
    x = re.findall("Change from previous report \(new cases.+\n.+\n.+", soupStr)[0]
    x = x.split("<td>")[1]
    x = x.split("</td>")[0]
    newCasesToday = x   
    #print totalTestsCompleted, newCasesToday


def printAll(per100 = 2):
    print(newCasesToday + "/" + totalTestsCompleted + " = " + str(round((float(newCasesToday)/float(totalTestsCompleted.replace(",",""))*100),2))+"%")
    print("(New Cases/Total Tests) completed in the last 24 hours")

    print()
    print("*GTA*")
    for x in regions.keys():
        if regions[x].isPartOfGTA():
            regions[x].printRelevant()

    print()
    print("*Outside of GTA with greater than " + str(per100) + " per 100k*")
    for x in regions.keys():
        if regions[x].getPer100k() > per100 and not regions[x].isPartOfGTA():
            regions[x].printRelevant()


def pullPDF():
    pdfFilePage = requests.get("https://covid-19.ontario.ca/covid-19-epidemiologic-summaries-public-health-ontario")
    html = pdfFilePage.text
    soup = BeautifulSoup(html, "html.parser")
    linkLookupStr = (soup.find("div", {"id": "block-ds-theme-content"}).findAll("a"))
    #regexString = '(?<=\<a href=").+?(pdf)'
    #x = re.findall(regexString, linkLookupStr)[0]

    url = str(linkLookupStr[3]).split('\"')[1]

    parsePDF(url)
    

if __name__ == "__main__":
    parseSite()
    pullPDF()


    if (len(sys.argv) > 1):
        printAll(int(sys.argv[1]))
    else:
        server.app.run(host='0.0.0.0')


    