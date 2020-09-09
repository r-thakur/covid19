import PyPDF2
from bs4 import BeautifulSoup
import requests
import json
import re
import urllib2


def parsePDF(fileLocation):
    global ottawaCasesToday
    global durhamCasesToday
    global peelCasesToday
    global yorkCasesToday
    global torontoCasesToday
    global windsorCasesToday
    global ottawaCasesYest
    global durhamCasesYest
    global peelCasesYest
    global yorkCasesYest
    global torontoCasesYest
    global windsorCasesYest
    print fileLocation
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
    requestWHeader = urllib2.Request(fileLocation, headers=hdr)
    pdfFile = urllib2.urlopen(requestWHeader)
    data = pdfFile.read()
    with open("current.pdf", "wb") as code:
        code.write(data)



    pdf_file = open("current.pdf",'rb')
    read_pdf = PyPDF2.PdfFileReader(pdf_file)


    #find cases in ottawa
    page = read_pdf.getPage(8)
    page_content = page.extractText().replace("\n","")
    x = re.findall("(?<=\Ottawa Public Health ).*?  ", page_content)[0]
    x = x.split(" ")
    ottawaCasesToday = x[1]
    ottawaCasesYest = x[0]

    #find cases in Durham, peel, york, toronto, windsor
    page = read_pdf.getPage(9)
    page_content = page.extractText().replace("\n","")
    x = re.findall("(?<=\Durham Region Health Department ).*?  ", page_content)[0]
    x = x.split(" ")
    durhamCasesToday = x[1]
    durhamCasesYest = x[0]
    x = re.findall("(?<=\ Peel Public Health ).*?  ", page_content)[0]
    x = x.split(" ")
    peelCasesToday = x[1]
    peelCasesYest = x[0]
    x = re.findall("(?<=\ York Region Public Health ).*?  ", page_content)[0]
    x = x.split(" ")
    yorkCasesToday = x[1]
    yorkCasesYest = x[0]
    x = re.findall("(?<=\ Toronto Public Health ).*?  ", page_content)[0]
    x = x.split(" ")
    torontoCasesToday = x[1]
    torontoCasesYest = x[0]
    x = re.findall("(?<=\Essex County Health Unit ).*?  ", page_content)[0]
    x = x.split(" ")
    windsorCasesToday = x[1]
    windsorCasesYest = x[0]

def parseSite(url):
    global totalTestsCompleted
    global newCasesToday
    jsonAsText = requests.get(url)
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


def printAll():
    print newCasesToday + "/" + totalTestsCompleted
    print "(New Cases/Total Tests) completed in the last 24 hours"
    print round((float(newCasesToday)/float(totalTestsCompleted.replace(",",""))*100),2),"%"
    print
    print "*GTA*"
    print "Toronto: " + torontoCasesToday + " (Yesterday: " + torontoCasesYest + ")"
    print "Durham: " + durhamCasesToday + " (Yesterday: " + durhamCasesYest + ")"
    print "York: " + yorkCasesToday + " (Yesterday: " + yorkCasesYest + ")"
    print "Peel: " + peelCasesToday + " (Yesterday: " + peelCasesYest + ")"
    print
    print "*Outside*"
    print "Ottawa: " + ottawaCasesToday + " (Yesterday: " + ottawaCasesYest + ")"
    print "Windsor: " + windsorCasesToday + " (Yesterday: " + windsorCasesYest + ")"


def pullPDF():
    global url
    pdfFilePage = requests.get("https://covid-19.ontario.ca/covid-19-epidemiologic-summaries-public-health-ontario")
    html = pdfFilePage.text
    soup = BeautifulSoup(html, "html.parser")
    linkLookupStr = (soup.find("div", {"id": "block-ds-theme-content"}).findAll("a"))
    #regexString = '(?<=\<a href=").+?(pdf)'
    #x = re.findall(regexString, linkLookupStr)[0]

    url = str(linkLookupStr[3]).split('\"')[1]

    

if __name__ == "__main__":
    parseSite("https://api.ontario.ca/api/drupal/page%2Fhow-ontario-is-responding-covid-19?fields=body")
    pullPDF()
    parsePDF(url)

    printAll()