import urllib3
import math
import xml.etree.ElementTree as ET


#Translink API https://developer.translink.ca/ServicesRtti/ApiReference

#Defining geographic maxima and minima for Delta and other constants
latfloor = [49.003192,-123.068576]
latroof = [49.152959,-122.972304]
longwest = [49.064212,-123.148544]
longeast = [49.134125,-122.891214]
radius = 1000

#Defines routestop matrix
routeStopMatrix = []
routeList = []

#Generates coordinate check queue
def generateCheckQueue():
    checkQueue = []
    for i in range (0,10):
        for j in range (0,10):
            longp = longwest[1]+i*0.01
            latp = latfloor[0]+j*0.01
            checkQueue.append([latp,longp])
    return checkQueue

#Gets all stops in the XML return from the Translink API
def getStops(root):
    for child in root:
        name = ""
        routes = ""
        for baby in child:
            if(baby.tag == 'StopNo'):
                name = baby.text
            if(baby.tag == 'Routes'):
                routes = baby.text
            if(routes is not None and name is not None):
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
        return [truncate(longwest[0],6),truncate(longwest[1],6)]
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
            


                
coordinateQueue = generateCheckQueue()
http = urllib3.PoolManager()

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
    route.reverse()
    routeNum = route.pop()
    route = sortStopList(route)
    print(route)
    sum = sum + getRouteLength(route)
print("Total Length",sum)

