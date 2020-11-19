import urllib3
import math
import xml.etree.ElementTree as ET


#Translink API https://developer.translink.ca/ServicesRtti/ApiReference

#Defining geographic maxima and minima for Delta
deltaLatFloor = [49.003192,-123.068576]
deltaLatRoof = [49.152959,-122.972304]
deltaLongWest = [49.064212,-123.148544]
deltaLongEast = [49.134125,-122.891214]

#Defining geographic maxima and minima for Coquitlam
coquitlamLongEast = [49.330606,-122.678321]
coquitlamLongWest = [49.251285,-122.894074]
coquitlamLatFloor = [49.220181,-122.844169] 
coquitlamLatRoof = [49.349397,-122.780631]
coquitlamCenterPoint = [49.268204,-122.821810]

burnabyLongEast = [49.246689,-122.893283]
burnabyLongWest = [49.246689,-123.024089]
burnabyLatFloor = [49.180977,-122.974994]
burnabyLatRoof = [49.294628,-122.969501]
burnabyCenterPoint = [49.241982,-122.958515]

portCoquitlamLongEast = [49.257915, -122.730194]
portCoquitlamLongWest = [49.257540, -122.794254]
portCoquitlamLatFloor = [49.225962, -122.802064]
portCoquitlamLatRoof = [49.273952, -122.780496]
portCoquitlamCenterPoint = [49.247530,-122.785727]

portMoodyLongEast = [49.293552,-122.821610]
portMoodyLongWest = [49.301618,-122.939030]
portMoodyLatFloor = [49.271082,-122.883398]
portMoodyLatRoof = [49.329779,-122.880035]
portMoodyCenterPoint = [49.282889,-122.827340]  


#Bus stop detection radius
radius = 1000
currentCity = "PORT MOODY"

#Defines routestop matrix
routeStopMatrix = []
routeList = []

#Generates check queue
def improvedGenerateCheckQueue(longWest,longEast,latRoof,latFloor):
    checkQueue = []
    x = float(abs(longWest[1] - longEast[1])/10.0)
    y = float(abs(latFloor[0] - latRoof[0])/10.0)
    for i in range(0,10):
        for j in range (0,10):
            longp = longWest[1]+i*x
            latp = latFloor[0]+j*y
            checkQueue.append([latp,longp])
    return checkQueue

#Gets all stops in the XML return from the Translink API
def getStops(root):
    global currentCity
    for child in root:
        name = ""
        routes = ""
        city = ""
        for baby in child:
            if(baby.tag == 'StopNo'):
                name = baby.text
            if(baby.tag == 'Routes'):
                routes = baby.text
            if(baby.tag == 'City'):
                city = baby.text
            if(routes is not None and name is not None and city==currentCity):
                if(',' in routes):
                    routes = routes.split(', ')
                    for route in routes:
                        notInMatrix = True
                        for key in routeStopMatrix:
                            if(route in key):
                                notInMatrix=False
                                if(name not in key):
                                    key.append(name)       
                        if(notInMatrix):
                            routeStopMatrix.append([route,name])
                elif(routes != ""):
                    notInMatrix = True
                    for key in routeStopMatrix:
                        if(routes in key):
                            notInMatrix=False
                            if(name not in key):
                                key.append(name)       
                    if(notInMatrix):
                        routeStopMatrix.append([routes,name])

#Gets a list of routes from the root
def getRoutes(root):
    for child in root:
        for baby in child:
            if(baby.tag == 'Routes'):
                if(baby.text is not None):
                    if(',' in baby.text):
                        routes = baby.text.split(', ')
                        for route in routes:
                            if(route not in routeList):
                                routeList.append(route)
                    elif(baby.text!=''):
                        if(baby.text not in routeList):
                            routeList.append(baby.text)


#Truncates numbers to a set number of places
#Code source: https://stackoverflow.com/questions/8595973/truncate-to-three-decimals-in-python/8595991
def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper*number)/stepper

#Generates list of stops in a route from the routeStopMatrix
def generateRoute(routeNumber):
    routeStopList = []
    for pair in routeStopMatrix:
        if(routeNumber in pair):
            routeStopList.append(pair[1])
            routeStopMatrix.remove(pair)
    return routeStopList

#Gets coords for a stopNumber
def getCoords(stopNumber):
    http = urllib3.PoolManager()
    url = 'https://api.translink.ca/rttiapi/v1/stops/'+str(stopNumber)+'?apikey=lt7s9J9QzEKRZ3R2oAmM'
    r = http.request('GET',url)
    data = ET.fromstring(r.data)
    lat = ''
    lon = ''
    for child in data:
        if(child.tag=='Latitude'):
            lat = child.text
        if(child.tag=='Longitude'):
            lon = child.text
    if(lat==""or lon==""):
        print("couldn't find stop")
        return [truncate(portMoodyCenterPoint[0],6),truncate(portMoodyCenterPoint[1],6)]
    lat = float(lat)
    lon = float(lon)
    return [lat, lon]

#Gets the distance difference between coords
def getCoordDifference(coord1, coord2):
    latDif = abs(coord1[0]-coord2[0])
    lonDif = abs(coord1[1]-coord2[0])
    return latDif+lonDif

#Determines position of stop in list
def getCoordDirection(coordMain, coordComp):
    latDif = coordMain[0]-coordComp[0]
    lonDif = coordMain[1]-coordComp[0]
    sum = latDif+lonDif
    if(sum>0):
        return 'right'
    else:
        return 'left'

#Finds the closest stop to the stop at index
def findClosest(index, stopList):
    currClosIndex = 0
    currDif = 10000 
    indexCoords = getCoords(stopList[index])
    direction = ''
    for stop in stopList:
        if(stopList[index]!=stop):
            stopCoords = getCoords(stop)
            newDif = getCoordDifference(stopCoords, indexCoords)
            if(currDif>newDif):
                currDif = newDif
                currClosIndex = stopList.index(stop)
                direction = getCoordDirection(indexCoords,stopCoords) 
    return [direction, currClosIndex]

#Swaps index1 and index2 in swapList
def swap(index1, index2, swapList):
    temp = swapList[index1]
    swapList[index1] = swapList[index2]
    swapList[index2] = temp
    return swapList

#Sorts the stop list based on geographic location
def sortStopList(stopList):
    newList = stopList
    for stop in stopList:
        print(stopList.index(stop))
        stopIndex = newList.index(stop)
        closTuple = findClosest(stopIndex,newList)
        direction = closTuple[0]
        closIndex = closTuple[1]
        if(direction == 'left'):
            if(closIndex-1>=0):
                newList = swap(closIndex-1,stopIndex,newList)
            else:
                temp = newList[stopIndex]
                newList.remove(temp)
                newList.insert(0, temp)
        else:
            if(closIndex+1<=len(newList)-1):
                newList = swap(closIndex+1,stopIndex,newList)
            else:
                temp = newList[stopIndex]
                newList.remove(temp)
                newList.insert(len(newList)-1,temp)
    return newList

#Uses Harversine formula to calculate the km distance between two coords
#Code source: http://www.movable-type.co.uk/scripts/latlong.html
def getCoordDistance(coord1, coord2):
    r = 6371e3

    lat1 = coord1[0]
    lat2 = coord2[0]
    lon1 = coord1[1]
    lon2 = coord2[1] 

    phi1 = lat1 * math.pi/180
    phi2 = lat2 * math.pi/180
    deltaPhi = (lat1-lat2) * math.pi/180
    deltaRho = (lon1-lon2) * math.pi/180

    varA = math.sin(deltaPhi/2) * math.sin(deltaPhi/2) + math.cos(phi1) * math.cos(phi2) * math.sin(deltaRho/2) * math.sin(deltaRho/2)

    varC = 2 * math.atan2(math.sqrt(varA), math.sqrt(1-varA))
    
    return varC*r/1000



    #Returns the route's length in km
def getRouteLength(route):
    prev = ""
    sum = 0
    for stop in route:
        if(not (prev == "")):
            stopCoords = getCoords(stop)
            prevCoords = getCoords(prev)
            sum = sum + abs(getCoordDistance(stopCoords,prevCoords))
        prev = stop

    return sum
            

#Calculates distance of public transit of target City
coordinateQueue = improvedGenerateCheckQueue(portMoodyLongWest,portMoodyLongEast,portMoodyLatRoof,portMoodyLatFloor)
http = urllib3.PoolManager()
radius = 2000
print("Radius: ",radius,"m")

for coord in coordinateQueue:
    clat = coord[0]
    clong = coord[1]

    clat = truncate(clat,6)
    clong = truncate(clong,6)

    url = 'https://api.translink.ca/rttiapi/v1/stops?apikey=lt7s9J9QzEKRZ3R2oAmM&lat='+str(clat)+'&long='+str(clong)+'&radius='+str(radius)
    r = http.request('GET',url)
    root = ET.fromstring(r.data)
    getStops(root)

sum = 0

for route in routeStopMatrix:
    print(route)
    route.reverse()
    routeNum = route.pop()
    route = sortStopList(route)
    sum = sum + getRouteLength(route)
print("Total Length",sum," in ", currentCity)