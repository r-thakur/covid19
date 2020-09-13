class Region:
    GTA = ['Peel Public Health', 'Toronto Public Health', 'Durham Region Health Department', 'York Region Public Health']
    def __init__(self, name, population, casesToday, casesYesterday):
        self.name = name
        self.population = population
        self.casesToday = casesToday
        self.casesYesterday = casesYesterday
        self.partOfGTA = False
        if (name in self.GTA):
            self.partOfGTA = True
    def printAll(self):
        print("Name: "+self.name)
        print("Population: "+str(self.population))
        print("Cases Today: "+self.casesToday)
        print("Cases Yesterday: "+self.casesYesterday)
        print("Part of GTA?: "+str(self.partOfGTA))
        print("Cases per 100k: "+str(self.per100))

    def printRelevant(self):
        print(self.name + ": " + str(self.casesToday) + " (Yesterday: "+ self.casesYesterday + ")")
        print(str(self.per100) + " per 100k")

    def getPer100k(self):
        return self.per100

    def isPartOfGTA(self):
        return self.partOfGTA

    def setPopulation(self,population):
        self.population = population
    def calculatePer100(self):
        self.per100 = round((float(self.casesToday)/self.population*100000),3)

