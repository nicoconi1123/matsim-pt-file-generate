
from xml.dom.minidom import parse,Document,DOMImplementation
import xml.dom.minidom
from math import radians, cos, sin, asin, sqrt
import math
import pandas as pd
import datetime
import  time
#

#Calculation of Euclidean distance by latitude and longitude
def GeoDistance(lng1,lat1,lng2,lat2):
    lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
    dlon=lng2-lng1
    dlat=lat2-lat1
    a=sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    dis=2*asin(sqrt(a))*6371*1000
    return dis
#Two types of coordinate conversion
def WGS84toMercator(x,y):
    x=x*20037508.342789/180
    y= math.log(math.tan((90+y)*math.pi/360))/(math.pi/180)
    y = y * 20037508.34789 / 180
    return x,y
def MercatortoWGS84(x,y):
    a=x/20037508.342789*180
    b=y/20037508.342789*180
    c=180/math.pi*(2*math.atan(math.exp(b*math.pi/180))-math.pi/2)
    return a,c
#String in time format converted to seconds
def StrToSecond(a):
    h = int(a[0:2])
    m = int(a[3:5])
    s = int(a[6:8])
    tt = 3600 * h + 60 * m + s
    return tt
def SetNode(tree, nodes, id, x, y,isMercator,isTransfer):
    if isMercator==False:
        x,y=WGS84toMercator(float(x),float(y))
    newxml_node = tree.createElement('node')
    newxml_node.setAttribute('id', str(id))
    newxml_node.setAttribute('x', str(x))
    newxml_node.setAttribute('y', str(y))
    if isTransfer==True:
        text1 = tree.createTextNode(' ')
        newxml_node.appendChild(text1)
    else:
        text1 = tree.createTextNode('')
        newxml_node.appendChild(text1)
    nodes.appendChild(newxml_node)
def SetLink(tree,links,id,from_node,to,length):
    newxml_link=tree.createElement('link')
    newxml_link.setAttribute('id',str(id))
    newxml_link.setAttribute('from', str(from_node))
    newxml_link.setAttribute('to', str(to))
    newxml_link.setAttribute('length', str(length))
    newxml_link.setAttribute('freespeed', str(12))
    newxml_link.setAttribute('capacity', str(2000))
    newxml_link.setAttribute('permlanes', str(1))
    newxml_link.setAttribute('oneway', str(1))
    newxml_link.setAttribute('modes', 'pt')
    links.appendChild(newxml_link)
def WriteBusNodeLink(bus_info,bus_xml):
    imp = DOMImplementation()

    dt = imp.createDocumentType(qualifiedName='network', publicId='',
                                systemId='http://www.matsim.org/files/dtd/network_v2.dtd')
    newxml_domtree = imp.createDocument(None, 'network', dt)

    newxml_network = newxml_domtree.documentElement
    newxml_domtree.appendChild(newxml_network)

    newxml_nodes = newxml_domtree.createElement('nodes')
    newxml_network.appendChild(newxml_nodes)

    newxml_links = newxml_domtree.createElement('links')
    newxml_network.appendChild(newxml_links)
    #stop is one node actually. In order to adapt to the format of matsim，we divided it into two nodes 10 meters apart,
    # similar to bus platforms
    #stop is the input stop，node is the virtual platform node. A stop has two nodes accordingly.
    for  busline_dict in bus_info:
        bus_name=list(busline_dict.keys())[0]
        line_info = list(busline_dict.values())[0]
        for stop_num in range(len(line_info)-1):

            x1,y1=WGS84toMercator(float(line_info[stop_num]['x']),float(line_info[stop_num]['y']))
            x2, y2 = WGS84toMercator(float(line_info[stop_num+1]['x']), float(line_info[stop_num+1]['y']))
            link_length=GeoDistance(float(line_info[stop_num]['x']),float(line_info[stop_num]['y']),
                                    float(line_info[stop_num + 1]['x']), float(line_info[stop_num + 1]['y']))
            ratio = 10 / link_length
            # stop_from
            SetNode(newxml_domtree, newxml_nodes, bus_name + str(line_info[stop_num]['id']) + '_A', x1 - ratio * (x2 - x1),
                    y1 - ratio * (y2 - y1), True, False)
            # stop_to
            SetNode(newxml_domtree, newxml_nodes, bus_name + str(line_info[stop_num]['id']) + '_B', x1 + ratio * (x2 - x1),
                    y1 + ratio * (y2 - y1), True, False)
            if stop_num==len(line_info)-2:
                SetNode(newxml_domtree, newxml_nodes, bus_name+ str(line_info[stop_num+1]['id']) + '_A', x2 - ratio * (x2 - x1),
                        y2 - ratio * (y2 - y1), True,False)
                # SetNode(newxml_domtree, newxml_nodes, new_id[1], new_lon[1], new_lat[1],False)
                SetNode(newxml_domtree, newxml_nodes, bus_name + str(line_info[stop_num+1]['id']) + '_B', x2 + ratio * (x2 - x1),
                        y2 + ratio * (y2 - y1), True,True)
    nodelist = newxml_domtree.getElementsByTagName('node')
    for node_num in range(len(nodelist) - 1):
        from_node = nodelist[node_num]

        to_node = nodelist[node_num + 1]
        link_id = ''
        if from_node.childNodes[0].data == ' ':
            continue
        lon1, lat1 = MercatortoWGS84(float(from_node.attributes['x'].value), float(from_node.attributes['y'].value))
        lon2, lat2 = MercatortoWGS84(float(to_node.attributes['x'].value), float(to_node.attributes['y'].value))
        link_length = GeoDistance(lon1, lat1, lon2, lat2)
        if from_node.attributes['id'].value[-1] == 'A':
            link_id = from_node.attributes['id'].value[:-2]
        elif from_node.attributes['id'].value[-1] == 'B':
            link_id = 'from_' + from_node.attributes['id'].value + '_to_' + to_node.attributes['id'].value
        else:
            print('link name error!!!')

        SetLink(newxml_domtree, newxml_links, link_id, from_node.attributes['id'].value,
                to_node.attributes['id'].value, link_length, )
        SetLink(newxml_domtree, newxml_links, link_id + '_r', to_node.attributes['id'].value,
                from_node.attributes['id'].value, link_length)
    with open(bus_xml, 'w') as f:
        # 缩进 - 换行 - 编码
        newxml_domtree.writexml(f,indent='\t', addindent='\t',newl='\n',encoding='utf-8')

def WriteTransitSchedule(stop_list_all,schedule_xml,transit_list_all):
    imp_pt = DOMImplementation()
    depart_id=0
    dt_pt = imp_pt.createDocumentType(qualifiedName='transitSchedule', publicId='',
                                systemId='http://www.matsim.org/files/dtd/transitSchedule_v2.dtd')
    ptsch_domtree = imp_pt.createDocument(None, 'transitSchedule', dt_pt)

    ptsch_transitschedule = ptsch_domtree.documentElement
    ptsch_domtree.appendChild(ptsch_transitschedule)

    ptsch_transitStops = ptsch_domtree.createElement('transitStops')
    ptsch_transitschedule.appendChild(ptsch_transitStops)

    vehicle_id_list_all=[]
    ##generate transitStops
    for line_dict in stop_list_all:
        bus_label=stop_list_all.index(line_dict)
        label=list(line_dict.keys())[0]
        # feasible_subway_line_label.append(label)
        stop_list=list(line_dict.values())[0]

    ##generate transitline
        transitline_info = []

        for item in transit_list_all:

            if list(item.values())[0][0]==label:
                transitline_info=list(item.values())[0]

        # print(feasible_subway_line_name)
        simplename=transitline_info[0]
        transit_strat_time = transitline_info[1]
        transit_end_time = transitline_info[2]
        interval=transitline_info[3]
        if ' ' in simplename:
            num = simplename.index(' ')
            simple_name = simplename[:num - 1]
        else:
            simple_name=simplename
        #transitline
        ptsch_transitLine = ptsch_domtree.createElement('transitLine')
        ptsch_transitLine.setAttribute('id',simple_name)
        ptsch_transitschedule.appendChild(ptsch_transitLine)
        #transitroute
        ptsch_transitRoute = ptsch_domtree.createElement('transitRoute')
        ptsch_transitRoute.setAttribute('id', simple_name+'1')
        ptsch_transitLine.appendChild(ptsch_transitRoute)
            #reverse
        ptsch_transitRoute_r = ptsch_domtree.createElement('transitRoute')
        ptsch_transitRoute_r.setAttribute('id', simple_name + '2')
        ptsch_transitLine.appendChild(ptsch_transitRoute_r)
        #transitmode
        ptsch_transportMode = ptsch_domtree.createElement('transportMode')
        text = ptsch_domtree.createTextNode('pt')
        ptsch_transportMode.appendChild(text)
        ptsch_transitRoute.appendChild(ptsch_transportMode)
             # reverse
        ptsch_transportMode_r = ptsch_domtree.createElement('transportMode')
        text_r = ptsch_domtree.createTextNode('pt')
        ptsch_transportMode_r.appendChild(text_r)
        ptsch_transitRoute_r.appendChild(ptsch_transportMode_r)
        #routeprofile
        ptsch_routeProfile = ptsch_domtree.createElement('routeProfile')
            #stop和stopfacility
        for stop in stop_list:
            stop_id='stop_'+simplename+stop['id']
            stop_linkRefId=simplename+stop['id']
            lon,lat=WGS84toMercator(float(stop['x']),float(stop['y']))
            stopFacility=ptsch_domtree.createElement('stopFacility')
            stopFacility.setAttribute('id',stop_id)
            stopFacility.setAttribute('x', str(lon))
            stopFacility.setAttribute('y', str(lat))
            stopFacility.setAttribute('linkRefId', stop_linkRefId)
            ptsch_transitStops.appendChild(stopFacility)

            #reverse stopfacility
            stopFacility_r = ptsch_domtree.createElement('stopFacility')
            stopFacility_r.setAttribute('id', stop_id+'_r')
            stopFacility_r.setAttribute('x', str(lon+5))#随便设置的地点
            stopFacility_r.setAttribute('y', str(lat+5))
            stopFacility_r.setAttribute('linkRefId', stop_linkRefId+'_r')
            ptsch_transitStops.appendChild(stopFacility_r)
            #正向stop
            stop_node = ptsch_domtree.createElement('stop')
            stop_node.setAttribute('refId',stop_id)
            offset=stop_list.index(stop)*120+30
            offsettime=datetime.timedelta(seconds=offset)
            if len(str(offsettime))==8:
                set_offset=str(offsettime)
            else:
                set_offset = '0'+str(offsettime)
            if stop_list.index(stop)==0:
                stop_node.setAttribute('departureOffset',set_offset)
            elif stop_list.index(stop)==len(stop_list)-1:
                stop_node.setAttribute('arrivalOffset', set_offset)
            else:
                stop_node.setAttribute('departureOffset', set_offset)
                stop_node.setAttribute('arrivalOffset', set_offset)
            stop_node.setAttribute('awaitDeparture', 'false')
            ptsch_routeProfile.appendChild(stop_node)
        ptsch_transitRoute.appendChild(ptsch_routeProfile)

             # reverse
        ptsch_routeProfile_r = ptsch_domtree.createElement('routeProfile')
        re_list=list(reversed(stop_list))
        for stop_r in re_list:
            stop_id_r = 'stop_' + simplename+stop_r['id']+'_r'
            # stop_linkRefId_r = stop_r['id']

            stop_node_r = ptsch_domtree.createElement('stop')
            stop_node_r.setAttribute('refId', stop_id_r)
            offset = re_list.index(stop_r) * 120 + 30
            offsettime = datetime.timedelta(seconds=offset)
            if len(str(offsettime)) == 8:
                set_offset = str(offsettime)
            else:
                set_offset = '0' + str(offsettime)
            if re_list.index(stop_r) == 0:
                stop_node_r.setAttribute('departureOffset', set_offset)
            elif re_list.index(stop_r) == len(re_list) - 1:
                stop_node_r.setAttribute('arrivalOffset', set_offset)
            else:
                stop_node_r.setAttribute('departureOffset', set_offset)
                stop_node_r.setAttribute('arrivalOffset', set_offset)
            stop_node_r.setAttribute('awaitDeparture', 'false')
            ptsch_routeProfile_r.appendChild(stop_node_r)
        ptsch_transitRoute_r.appendChild(ptsch_routeProfile_r)
        #route
        ptsch_route = ptsch_domtree.createElement('route')

            #link
        # linklist=subway_tree.getElementsByTagName('link')
        for stop_num in range(len(stop_list)-1):
            from_stop=stop_list[stop_num]
            to_stop=stop_list[stop_num+1]
            from_stop_id=from_stop['id']
            to_stop_id = to_stop['id']
            link=ptsch_domtree.createElement('link')
            link.setAttribute('refId',simplename+from_stop_id)
            ptsch_route.appendChild(link)
            link1 = ptsch_domtree.createElement('link')
            link1.setAttribute('refId', 'from_'+simplename+from_stop_id+'_B_to_'+simplename+to_stop_id+'_A')
            ptsch_route.appendChild(link1)
            if stop_num==len(stop_list)-2:
                link2 = ptsch_domtree.createElement('link')
                link2.setAttribute('refId',simplename+to_stop_id)
                ptsch_route.appendChild(link2)
        ptsch_transitRoute.appendChild(ptsch_route)
            #reverse link

        ptsch_route_r = ptsch_domtree.createElement('route')
        for stop_num_r in range(len(re_list)-1):
            from_stop_r=re_list[stop_num_r]
            to_stop_r=re_list[stop_num_r+1]
            from_stop_id_r=from_stop_r['id']
            to_stop_id_r = to_stop_r['id']
            link_r=ptsch_domtree.createElement('link')
            link_r.setAttribute('refId',simplename+from_stop_id_r+'_r')
            ptsch_route_r.appendChild(link_r)
            link1_r = ptsch_domtree.createElement('link')
            link1_r.setAttribute('refId', 'from_'+simplename+to_stop_id_r+'_B_to_'+simplename+from_stop_id_r+'_A_r')
            ptsch_route_r.appendChild(link1_r)
            if stop_num_r==len(re_list)-2:
                link2_r = ptsch_domtree.createElement('link')
                link2_r.setAttribute('refId',simplename+to_stop_id_r+'_r')
                ptsch_route_r.appendChild(link2_r)
        ptsch_transitRoute_r.appendChild(ptsch_route_r)


        vehicle_id_list_one=[]
        #departures
        ptsch_departures = ptsch_domtree.createElement('departures')
        start_depart_time=StrToSecond(transit_strat_time)
        end_depart_time=StrToSecond(transit_end_time)
        for item in range(int(24*60/(60/interval))):
            a=int(start_depart_time+interval*item)
            if a>end_depart_time:
                break
            tt=datetime.timedelta(seconds=a)
            if len(str(tt))==8:
                set_tt=str(tt)
            else:
                set_tt = '0'+str(tt)
            ptsch_departure=ptsch_domtree.createElement('departure')
            ptsch_departure.setAttribute('id',str(depart_id))#防止不同line车辆id一样
            depart_id=depart_id+1
            ptsch_departure.setAttribute('departureTime', set_tt)

            aa=bus_label*1000+item%25
            if aa<10:
                aa='0'+str(aa)
            else:
                aa=str(aa)
            ptsch_departure.setAttribute('vehicleRefId', aa)
            ptsch_departures.appendChild(ptsch_departure)
            if item<25:
                vehicle_id_list_one.append(bus_label*1000+(item%25))
        ptsch_transitRoute.appendChild(ptsch_departures)

        # reverse departures
        ptsch_departures_r = ptsch_domtree.createElement('departures')

        for item_r in range(int(24*60/(60/interval))):
            a=int(start_depart_time+interval*item_r)
            if a>end_depart_time:
                break
            tt=datetime.timedelta(seconds=a)
            if len(str(tt))==8:
                set_tt=str(tt)
            else:
                set_tt = '0'+str(tt)
            ptsch_departure_r=ptsch_domtree.createElement('departure')
            ptsch_departure_r.setAttribute('id',str(depart_id))#防止车辆id一样
            depart_id=depart_id+1
            ptsch_departure_r.setAttribute('departureTime', set_tt)

            aa_r=bus_label*1000+25+item_r%25

            ptsch_departure_r.setAttribute('vehicleRefId', str(aa_r))
            ptsch_departures_r.appendChild(ptsch_departure_r)
            if item_r<25:

                vehicle_id_list_one.append(aa_r)
        ptsch_transitRoute_r.appendChild(ptsch_departures_r)
        vehicle_id_list_all.append({label:vehicle_id_list_one})
    with open(schedule_xml, 'w') as f:
        # 缩进 - 换行 - 编码
        ptsch_domtree.writexml(f, indent='\t', addindent='\t', newl='\n', encoding='utf-8')
    return vehicle_id_list_all


def WriteTransitVehicle(vehicle_xml,transit_list_all,vehicle_id_all):
    domtree_veh = Document()

    vehicleDefinitions= domtree_veh.createElement('vehicleDefinitions')
    vehicleDefinitions.setAttribute('xmlns','http://www.matsim.org/files/dtd')
    vehicleDefinitions.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    vehicleDefinitions.setAttribute('xsi:schemaLocation', 'http://www.matsim.org/files/dtd http://www.matsim.org/files/dtd/vehicleDefinitions_v1.0.xsd')
    domtree_veh.appendChild(vehicleDefinitions)

    # vehicletype类型一定要设置在前面
    # vehicletyp type must be set in front

    for line in vehicle_id_all:
        label = list(line.keys())[0]
        # feasible_subway_line_label.append(label)

        transit_info=[]
        for item in transit_list_all:

            if list(item.values())[0][0]==label:
                transit_info=list(item.values())[0]
        num_length=transit_info[4]
        num_seats=transit_info[5]
        num_standingroom=transit_info[6]

        #vehicleType
        vehicletype=domtree_veh.createElement('vehicleType')
        vehicletype.setAttribute('id',str(label))
        vehicleDefinitions.appendChild(vehicletype)
        #description
        description=domtree_veh.createElement('description')
        text = domtree_veh.createTextNode('pt')
        description.appendChild(text)
        vehicletype.appendChild(description)
        #capacity
        capacity=domtree_veh.createElement('capacity')
        vehicletype.appendChild(capacity)
            #seats
        seats=domtree_veh.createElement('seats')
        seats.setAttribute('persons',str(num_seats))
        capacity.appendChild(seats)
            # standingroom
        standingroom=domtree_veh.createElement('standingRoom')
        standingroom.setAttribute('persons',str(num_standingroom))
        capacity.appendChild(standingroom)
        # length
        length=domtree_veh.createElement('length')
        length.setAttribute('meter',str(num_length))
        vehicletype.appendChild(length)
    for line1 in vehicle_id_all:
        label = list(line1.keys())[0]
        id_list = list(line1.values())[0]
        for id in id_list:
            vehicle=domtree_veh.createElement('vehicle')
            if id<10:
                id='0'+str(id)
            vehicle.setAttribute('id',str(id))
            vehicle.setAttribute('type',str(label))
            vehicleDefinitions.appendChild(vehicle)

    with open(vehicle_xml, 'w') as f:
        # 缩进 - 换行 - 编码
        domtree_veh.writexml(f, indent='\t', addindent='\t', newl='\n', encoding='utf-8')

def AddOneXMLtoAnother(subway_xml,network_xml,new_xml):
    DOMTree_subway = xml.dom.minidom.parse(subway_xml)
    root_subway  = DOMTree_subway.documentElement
    node_subway  = root_subway.getElementsByTagName('node')
    link_subway = root_subway.getElementsByTagName('link')


    DOMTree_network= xml.dom.minidom.parse(network_xml)
    root_network =DOMTree_network.documentElement
    nodes_network = root_network.getElementsByTagName('nodes')[0]
    links_network= root_network.getElementsByTagName('links')[0]

    for item in node_subway:
        nodes_network.appendChild(item)
    for item in link_subway:
        links_network.appendChild(item)

    with open(new_xml, 'w') as f:
        # 缩进 - 换行 - 编码
        DOMTree_network.writexml(f, indent='\t', addindent='\t',newl='\n',encoding='utf-8')

if __name__=='__main__':
# 1. ---------------------------------------------generate pt line list

    data = pd.read_excel("input/test_data.xlsx")#Input file path
    row, col = data.shape
    all_list=[]
    for num in range(row):

        busstop_info=data.loc[num]
        location=busstop_info[2].split(',')
        x=float(location[0])
        y=float(location[1])

        if type(busstop_info[1])!=float:

            if num!=0:
                busline_dict_all = {name:line_list}
                all_list.append(busline_dict_all)
            line_list=[]
            name=busstop_info[1]
        busline_dict_single = {'id':busstop_info[3],'x':x,'y':y}

        line_list.append(busline_dict_single)
        if num==row-1:
            busline_dict_all = {name: line_list}
            all_list.append(busline_dict_all)


    print(all_list)

#2. ---------------------------------------------generate pt network
    bus_xml = 'output/transit_network.xml'#output file path
    WriteBusNodeLink(all_list, bus_xml)
#3. ---------------------------------------------generate pt schedule
    data = pd.read_excel("input/test_info.xlsx", header=None, )#Input file path
    row, col = data.shape
    transitschedule_list_all = []
    # [name,]
    for row_num in range(row):
        transitschedule_list_one = []
        for item in data.loc[row_num]:
            transitschedule_list_one.append(item)
        transitschedule_list_all.append({row_num: transitschedule_list_one})
    # print(transitschedule_list_all)
    schedule_xml='output/transitschedule.xml'#output file path
    vehicle_id_all=WriteTransitSchedule(all_list,schedule_xml,transitschedule_list_all)
#4. ---------------------------------------------generate pt vehicle
    vehicle_xml='output/transitVehicles.xml'
    WriteTransitVehicle(vehicle_xml,transitschedule_list_all,vehicle_id_all)
#5. ---------------------------------------------intergrate pt network and roadway network
    network_xml='input/network.xml'#Input file path
    new_xml='output/final_network.xml'#output file path
    AddOneXMLtoAnother(bus_xml, network_xml, new_xml)



