#!/usr/bin/env python3

from util import read_osm_data, great_circle_distance, to_local_kml_url

# NO ADDITIONAL IMPORTS!


ALLOWED_HIGHWAY_TYPES = {
    'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified',
    'residential', 'living_street', 'motorway_link', 'trunk_link',
    'primary_link', 'secondary_link', 'tertiary_link',
}


DEFAULT_SPEED_LIMIT_MPH = {
    'motorway': 60,
    'trunk': 45,
    'primary': 35,
    'secondary': 30,
    'residential': 25,
    'tertiary': 25,
    'unclassified': 25,
    'living_street': 10,
    'motorway_link': 30,
    'trunk_link': 30,
    'primary_link': 30,
    'secondary_link': 30,
    'tertiary_link': 25,
}






def build_auxiliary_structures(nodes_filename, ways_filename):
    """
    Creates a set of ways and a set of nodes from the files; returns these sets in a tupe (nodes, ways)
    """
    relevant_nodes = set()

    node_web = {}  # node_id mapped to children of node
    node_coord = {}  # node_id: (lat, lon)

    for way in read_osm_data(ways_filename): #loops thru ways in the given dataset

        if way['tags'].get('highway') in ALLOWED_HIGHWAY_TYPES: # finds speed limit of current way
            if 'maxspeed_mph' in way['tags']:
                speed_limit = way['tags']['maxspeed_mph']
            else:
                speed_limit = DEFAULT_SPEED_LIMIT_MPH[way['tags']['highway']]

            for i in range(len(way['nodes'])): # organizes a nodes_web (node_id's mapped to their neighbors). NOTE: only considers relevant nodes
                relevant_nodes.add(way['nodes'][i])
                if way['nodes'][i] not in node_web:
                    node_web[way['nodes'][i]] = {}

            for i in range(len(way['nodes']) - 1): # assumes MAX speed limit if a node is in 2 different ways
                node_web[way['nodes'][i]][way['nodes'][i + 1]] = max(speed_limit, node_web[way['nodes'][i]].get(way['nodes'][i + 1], 0))


            if not way['tags'].get('oneway') == 'yes': # 2 directional highway
                for i in range(len(way['nodes']) - 1, 0, -1):
                    node_web[way['nodes'][i]][way['nodes'][i - 1]] = max(speed_limit, node_web[way['nodes'][i]].get(way['nodes'][i - 1], 0))



    for node in read_osm_data(nodes_filename): #creates cood_coordinate dictionary
        if node['id'] in relevant_nodes:
            node_coord[node['id']] = node['lat'], node['lon']

    return (node_web, node_coord)


def find_nearest_node(loc, aux_structures):
    '''
    Finds nearest node. Takes in location (lat, lon) and a dictionary of nodes_web (in aux structures)
    '''
    min_dist = float("inf")

    node_coords = aux_structures[1] #node_id: coord
    for node in node_coords.keys():
        d = great_circle_distance((node_coords[node][0], node_coords[node][1]), loc)
        if d < min_dist: # finds min distance from node to loc
            min_dist = d
            n1 = node
    return n1


def find_path(aux_structures, loc1, loc2, short=True):
    '''
    Finds a path from loc1 to loc2.
    '''


    n1 = find_nearest_node(loc1, aux_structures)
    n2 = find_nearest_node(loc2, aux_structures)
    agenda = [[0, 0, [n1]]]

    visited = set()

    while agenda:
        if short:
            agenda = sorted(agenda, key=lambda x: x[0])
        else:
            agenda = sorted(agenda, key=lambda x: x[1])
        popped = agenda.pop(0)
        current_path = popped[2]
        # create agenda by looping thru children of terminal node of current path
        terminal_node = current_path[-1]
        if terminal_node not in visited:
            if terminal_node == n2:  # if terminal node is destination node
                return [aux_structures[1][node] for node in current_path]
            visited.add(terminal_node)
            children_of_terminal_n = aux_structures[0][terminal_node]
            for neighbor in children_of_terminal_n: #loop thru neighbor nodes
                if neighbor not in visited:
                    new_path = current_path.copy()
                    new_path.append(neighbor)
                    if short:
                        d = popped[1] #distance so far
                        d += great_circle_distance((aux_structures[1][neighbor][0], #added distance of neighbor node from last node
                                                    aux_structures[1][neighbor][1]),
                                                   (aux_structures[1][terminal_node][0],
                                                    aux_structures[1][terminal_node][1]))

                        h = great_circle_distance(aux_structures[1][neighbor], aux_structures[1][n2])  # heuristic
                        agenda.append([h + d, d, new_path])
                    else:
                        t = popped[1]
                        t += great_circle_distance((aux_structures[1][neighbor][0],
                                                    aux_structures[1][neighbor][1]),
                                                   (aux_structures[1][terminal_node][0],
                                                    aux_structures[1][terminal_node][1])) / aux_structures[0][terminal_node][neighbor] #finds time to new node
                        agenda.append([0, t, new_path])

    return None




def find_short_path(aux_structures, loc1, loc2):
    """
    Return the shortest path between the two locations

    Parameters:
        aux_structures: the result of calling build_auxiliary_structures
        loc1: tuple of 2 floats: (latitude, longitude), representing the start
              location
        loc2: tuple of 2 floats: (latitude, longitude), representing the end
              location

    Returns:
        a list of (latitude, longitude) tuples representing the shortest path
        (in terms of distance) from loc1 to loc2.
    """
    return find_path(aux_structures, loc1, loc2)




def find_fast_path(aux_structures, loc1, loc2):
    """
    Return the shortest path between the two locations, in terms of expected
    time (taking into account speed limits).

    Parameters:
        aux_structures: the result of calling build_auxiliary_structures
        loc1: tuple of 2 floats: (latitude, longitude), representing the start
              location
        loc2: tuple of 2 floats: (latitude, longitude), representing the end
              location

    Returns:
        a list of (latitude, longitude) tuples representing the shortest path
        (in terms of time) from loc1 to loc2.
    """
    return find_path(aux_structures, loc1, loc2, short=False)


if __name__ == '__main__':
    # additional code here will be run only when lab.py is invoked directly
    # (not when imported from test.py), so this is a good place to put code
    # used, for example, to generate the results for the online questions.

    # #********LENGTH OF NODES*******
    # node_list = []
#     # for node in read_osm_data('resources/cambridge.nodes'):
#     #     node_list.append(node)
    #
    # print("Total nodes: ", len(node_list))
    # cambridge_nodes = read_osm_data('resources/cambridge.nodes')
    # node_list = []
    # node_list_with_name = []
    # for node in cambridge_nodes:
    #     if 'name' in node['tags']:
    #         node_list_with_name.append(node)
    # print(len(node_list_with_name))


    # for node in node_set:
    #     if node

    # for node in read_osm_data('resources/cambridge.nodes'):
    #     print(node)
    #***********77 MASS AVE*************
    # for node in read_osm_data('resources/cambridge.nodes'):
    #     if 'name' in node['tags']:
    #         if node['tags']['name'] == '77 Massachusetts Ave':
    #             print(node['id'])

    #*********WAYS*********
    # ways = []
    # for way in read_osm_data('resources/cambridge.ways'):
    #     ways.append(way)
    # print(len(ways))

    # one_ways = []
    # for way in read_osm_data('resources/cambridge.ways'):
    #     if way['tags'].get('oneway') == 'yes':
    #         one_ways.append(way)
    # print(len(one_ways))


    #*********SHORTEST PATH TEST***********
    # for way in read_osm_data('resources/cambridge.ways'):
    #     print(way)
    # for node in read_osm_data('resources/cambridge.nodes'):
    #     print(node)


    # for way in read_osm_data(ways_filename):
    #     if way['tags'].get('highway') != None:
    #         if way['tags']['highway'] in ALLOWED_HIGHWAY_TYPES:
    #             ways[way['id']] = dist_from_way(way, nodes_filename)
    # dataset = 'mit'
    # # print("MIT WAYS: \n\n\n\n", [item for item in read_osm_data("resources/mit.ways")])
    # aux_structures = build_auxiliary_structures("resources/mit.nodes", "resources/mit.ways")
    # # print("Aux structures in main: ", aux_structures)
    # loc1 = (42.3603, -71.095)
    # loc2 = (42.3573, -71.0928)
    #
    # path = find_short_path(aux_structures, loc1, loc2)
    # print(path)
    #
    # midwest_nodes = [item for item in read_osm_data('resources/midwest.nodes')]
    # print(midwest_nodes)
    # lat1 = [node['lat'] for node in midwest_nodes if node['id'] == 233941454]
    # lon1 = [node['lon'] for node in midwest_nodes if node['id'] == 233941454]
    #
    # lat2 = [node['lat'] for node in midwest_nodes if node['id'] == 233947199]
    # lon2 = [node['lon'] for node in midwest_nodes if node['id'] == 233947199]
    #
    # print(lat1, lat2)
    # print(great_circle_distance((lat1[0], lon1[0]), (lat2[0], lon2[0])))
    midwest_ways = [item for item in read_osm_data('resources/midwest.ways')]
    # print(midwest_ways)

    # cum_dist = 0
    # our_path = None
    # our_path = [path for path in midwest_ways if path['id'] == 21705939]
    # nodes = get_path_nodes(our_path[0], 'resources/midwest.nodes', 'resources/midwest.ways')
    #
    #
    # for i in range(len(nodes)-1):
    #     print("nodes: ", nodes)
    #     print("\n\n\nnodes[i]", nodes[i])
    #     print(nodes[i]['lat'])
    #     cum_dist+=great_circle_distance((nodes[i]['lat'], nodes[i]['lon']), (nodes[i+1]['lat'], nodes[i+1]['lon']))
    # print(cum_dist)





    # print(great_circle_distance((42.363745, -71.100999), (42.361283, -71.239677)))
    # big_func = build_auxiliary_structures('resources/midwest.nodes', 'resources/midwest.ways')[2]
    # lat1, lon1 = big_func(233941454)['lat'], big_func(233941454)['lon']
    # lat2, lon2 = big_func(233947199)['lat'], big_func(2233947199)['lon']
    #
    # print(great_circle_distance((lat1, lon1), (lat2, lon2)))

    #********AUX STRUCTURES TEST*********
    # node_coord = {}
    # # create a dictionary from node_id: (lat, lon)
    # for node in read_osm_data('resources/midwest.nodes'):
    #     node_coord[node['id']] = node['lat'], node['lon']
    # print(node_coord)
    #
    # nodes_web = {}  # node_id mapped to children of node
    #
    # for way in read_osm_data('resources/midwest.ways'):
    #     if way['tags'].get('highway') in ALLOWED_HIGHWAY_TYPES:
    #         for i in range(len(way['nodes']) - 1):
    #             nodes_web.setdefault(way['nodes'][i], set()).add(way['nodes'][i + 1])
    #         if not way['tags'].get('oneway') == 'yes':
    #             for i in range(len(way['nodes']) - 1, 0, -1):
    #                 nodes_web.setdefault(way['nodes'][i], set()).add(way['nodes'][i - 1])
    # print("nodes_web: ", nodes_web)

    # build a func for this (take id_list, loc)
    # min_dist = float("inf")
    # _, node_coords, __, __, _ = build_auxiliary_structures('resources/midwest.nodes', 'resources/midwest.ways')
    # print(node_coords)
    # for node in node_coords.keys():
    #     # print(great_circle_distance((node_coords[node][0], node_coords[node][1]), (41.4452463, -89.3161394)))
    #     s = great_circle_distance((node_coords[node][0], node_coords[node][1]), (41.4452463, -89.3161394))
    #     if s < min_dist:
    #         min_dist = s
    #         print(min_dist)
    #         n1 = node
    # print(n1)
    # aux_structures = build_auxiliary_structures('resources/mit.nodes', 'resources/mit.ways')
    # # print(find_nearest_node((41.4452463, -89.3161394), aux_structures))
    # print(aux_structures[0])
    # print(aux_structures[1])
    #
    # loc1 = (42.3603, -71.095)  # near Building 35
    # loc2 = (42.3573, -71.0928)  # Near South Maseeh
    # print(find_short_path(aux_structures, loc1, loc2))

    aux_structures = build_auxiliary_structures('resources/mit.nodes', 'resources/mit.ways')
    # inps = ((42.359242, -71.093765), (42.360485, -71.108349))

    # print(find_short_path(aux_structures, (42.359242, -71.093765), (42.360485, -71.108349)))
    # print(aux_structures)

    #******SHORT PATH TEST********
    # loc1 = (42.355, -71.1009)  # New House
    # loc2 = (42.3612, -71.092)  # 34-501
    # expected_path = [
    #     (42.355, -71.1009), (42.3575, -71.0952), (42.3582, -71.0931),
    #     (42.3592, -71.0932), (42.36, -71.0907), (42.3612, -71.092),
    # ]
    #
    # print('expected path: \n', expected_path)
    # print('result: \n', find_short_path(aux_structures, loc1, loc2))









    #********FAST PATH TEST***********
    # loc1 = (42.355, -71.1009)  # New House
    # loc2 = (42.3612, -71.092)  # 34-501
    # expected_path = [
    #     (42.355, -71.1009), (42.3575, -71.0927), (42.3582, -71.0931),
    #     (42.3592, -71.0932), (42.3601, -71.0952), (42.3612, -71.092),
    # ]
    # print('expected path: \n', expected_path)
    # print('result: \n', find_fast_path(aux_structures, loc1, loc2))

    #*******FAST PATH 2 TEST*******

    loc1 = (42.36, -71.0907)  # near Lobby 26
    loc2 = (42.3592, -71.0932)  # Near Lobby 7
    expected_path = [
        (42.36, -71.0907), (42.3612, -71.092),
        (42.3601, -71.0952), (42.3592, -71.0932),
    ]

    print('expected path: \n', expected_path)
    print('result: \n', find_fast_path(aux_structures, loc1, loc2))






