# -*- coding: utf-8 -*-
"""
Created on Thu Aug  3 14:39:46 2023

@author: shane
"""

import networkx as nx
import numpy as np
import pandas as pd
import time
import random

def rewire(G, target_assortativity, sample_size = 2, timed = False, time_limit=600, method):
    """
    Parameters
    ----------

    G : networkx.Graph
    target_assortativity : float in range [-1, 1]
    sample_size : int
    timed : bool
    time_limit : float
    method : string

    Returns:

    G : networkx.Graph
        rewired graph, rewiring done in place

    results : pandas.DataFrame()
        dataframe with all necessary info to plot results
        columns:
        iteration : number of loops completed so far (unsuccessful loops included)
        time : time taken for the current loop
        r : assortativity of the graph at the END of the current iteration
        sample_size : number of edges being selected at each iteration
                      N.B. The first loop will have a sample size = to the number of edges
                      but the row will be given the sample_size value of the succeeding rows
                      to allow for easy grouping
        edges_selected : cumulative number of edges sampled (unnsuccessful loops included)
        edges_rewired : cumulative number of edges rewired 
        duplicate_edges : The number of duplicate edges in the list of potential edges (one edge appearing twice = 1 here)
        self_edges : The number of self edges in the list of potential edges
        existing_edges : The number of edges in the list of potential edges that already exist in the graph
        preserved : If the degree_list has been preserved (only present in first and last rows)
    """

    first_row = {'iteration': 0, 
                 'time': 0, 
                 'r': nx.degree_assortativity_coefficient(G),
                 'target_r': target_assortativity, 
                 'sample_size': sample_size, 
                 'edges_rewired': 0,
                 'duplicate_edges': 0, 
                 'self_edges': 0,
                 'existing_edges': 0, 
                 'preserved': True}
    
    results = pd.DataFrame(first_row)

    if nx.degree_assortativity_coefficient(G) < target_assortativity:
      if method == 'new':
        G, results = rewire_positive_full(G, results)
        G, results = negatively_rewire(G, target_assortativity, results, sample_size, timed, time_limit)
      if method == 'original':
        G, results = positively_rewire(G, target_assortativity, results, sample_size, timed, time_limit)
    else:
      if method == 'new':
        G, results = rewire_negative_full(G, results)
        G, results = positively_rewire(G, target_assortativity, results, sample_size, timed, time_limit)
      if method == 'original':
        G, results = negatively_rewire(G, target_assortativity, results, sample_size, timed, time_limit)

    #we now have a dataframe of all of our relevant results

def degree_list(G):
    """
    Parameters
    ----------

    G : networkx.Graph OR list


    Returns
    -------
    np.ndarray
        sorted array of degrees

    """
    if type(G) == nx.classes.graph.Graph:
        degree_dict = dict(G.degree())
        degree_list = list(degree_dict.values())
    else:
        degree_list = G
    degree_list.sort()
    return np.array(degree_list)


def check_new_edges(potential_edges, G, row):
    """
    Takes the edges that will be potentially added to the Graph and checks
    for any issues
    Parameters
    ---------
    potential_edges : list of lists
        the edges to be checked
    
    G : networkx.Graph
        graph needed to check if any potential edges exist already

    row : the row to be added to the results DataFrame is edited here

    Returns
    -------
    edges_to_add : list of lists
        the checked edges

    row : dict
        the information to go into the results DataFrame

    """
    edges_to_add = []
    for edge in potential_edges:
        if G.has_edge(edge[0], edge[1]) == False:
            if edge[0] != edge[1]:
                if [edge[1], edge[0]] not in potential_edges:
                    if potential_edges.count(edge) == 1:
                        edges_to_add.append(edge)
                    else:
                        row['duplicate_edges'] += 0.5
                else:
                    row['duplicate_edges'] += 0.5
            else:
                row['self_edges'] += 1
        else:
            row['existing_edges'] += 1

    return edges_to_add, row 

def positively_rewire(G: nx.Graph, target_assortativity, results, sample_size = 2, timed = False, time_limit=600):
    alg_start = time.time()
    itr = 1
    while nx.degree_assortativity_coefficient(G) < target_assortativity:
        loop_start = time.time()
        itr += 1
        #define dictionary to track relevant info for each loop
        row = {'iteration' : itr, 
               'time' : 0, 
               'r' : 0,
               'target_r': target_assortativity
               'sample_size': sample_size, 
               'edges_rewired': 0,
               'duplicate_edges': 0, 
               'self_edges': 0,
               'existing_edges': 0, 
               'preserved': True}

        edges = list(G.edges())                
        edges_to_remove = random.sample(edges, sample_size)
        deg_dict = {}
        nodes = []
        for edge in edges_to_remove:
            for node in edge:
                nodes.append(node)
                deg_dict[node] = G.degree(node)
    
        nodes_sorted = sorted(nodes, key=deg_dict.get)
        potential_edges = [[nodes_sorted[i], nodes_sorted[i+1]] for i in range(0,len(nodes_sorted),2)]
        edges_to_add, row = check_new_edges(potential_edges, G, row)
                
        if len(edges_to_add) == sample_size:
            G.add_edges_from(edges_to_add)
            row['edges_rewired'] += sample_size
        else:
            G.add_edges_from(edges_to_remove)

        row['time'] += time.time() - start
        row['r'] = nx.degree_assortativity_coefficient(G)
        results.loc[len(results)] = row

        time_elapsed = time.time() - alg_start
    
        
        if timed == True:
            if time_elapsed > time_limit:
                if nx.degree_assortativity_coefficient(G) < target_assort:
                    return G, results

    return G, results


def negatively_rewire(G: nx.Graph, target_assortativity, results, sample_size = 2, timed = False, time_limit=600):
    alg_start = time.time()
    itr = 0
    while nx.degree_assortativity_coefficient(G) > target_assortativity:
        loop_start = time.time()
        itr += 1
        #define dictionary to track relevant info for each loop
        row = {'iteration' : itr, 
               'time' : 0, 
               'r' : 0,
               'target_r': target_assortativity
               'sample_size': sample_size, 
               'edges_rewired': 0,
               'duplicate_edges': 0, 
               'self_edges': 0,
               'existing_edges': 0, 
               'preserved': True}

        edges = list(G.edges())                
        edges_to_remove = random.sample(edges, sample_size)
        deg_dict = {}
        nodes = []
        for edge in edges_to_remove:
            for node in edge:
                nodes.append(node)
                deg_dict[node] = G.degree(node)
    
        nodes_sorted = sorted(nodes, key = deg_dict.get)
        n_nodes = int(len(nodes_sorted)/2)
        
        potential_edges = [(nodes_sorted[i], nodes_sorted[len(nodes) - 1 - i]) for i in range(n_nodes)]
        edges_to_add, row = check_new_edges(potential_edges, G, row)
                
        if len(edges_to_add) == sample_size:
            G.add_edges_from(edges_to_add)
            row['edges_rewired'] += sample_size
        else:
            G.add_edges_from(edges_to_remove)

        row['time'] += time.time() - start
        row['r'] = nx.degree_assortativity_coefficient(G)
        results.loc[len(results)] = row

        time_elapsed = time.time() - alg_start
    
        
        if timed == True:
            if time_elapsed > time_limit:
                if nx.degree_assortativity_coefficient(G) < target_assort:
                    return G, results

    return G, results

def rewire_positive_full(G: nx.Graph, results):
    
    start = time.time()    
    edges_to_remove = list(G.edges())                
    #record the orginal degree of each node
    original_degree = {}
    nodes = []
    for edge in edges_to_remove:
        for node in edge:
            if node not in nodes:
                nodes.append(node)
            original_degree[node] = G.degree(node)
    
    #sort nodes in descending order of degree
    nodes_sorted = sorted(nodes, key=original_degree.get, reverse=True)
        
    row = {'iteration' : 1, 
           'time' : 0, 
           'r' : 0,
           'target_r': target_assortativity
           'sample_size': sample_size, 
           'edges_rewired': 0,
           'duplicate_edges': 0, 
           'self_edges': 0,
           'existing_edges': 0, 
           'preserved': True}

    #dictionary in which to record the current degree of the nodes as we add edges 
    current_degree = {}
    for node in original_degree:
        current_degree[node] = 0#original_degree[node] - appearances[node]

    potential_edges = []
    for ind, node in enumerate(nodes_sorted):
        j = ind + 1
        while current_degree[node] < original_degree[node]:
            try:
                target = nodes_sorted[j]
            except IndexError:
                break
            if current_degree[target] < original_degree[target]:
                potential_edges.append([node, target])
                current_degree[node] += 1
                current_degree[target] += 1
            j += 1

    G.remove_edges_from(edges_to_remove)
    edges_to_add, row = check_new_edges(potential_edges, G, row)

    if len(edges_to_add) == sample_size:
        G.add_edges_from(edges_to_add)
        row['edges_rewired'] += len(edges_to_add) 
    else:
        G.add_edges_from(edges_to_remove)
    
    row['r'] += nx.degree_assortativity_coefficient(G)
    row['time'] += time.time() - start
    results.append(row)
    return G, results


def rewire_negative_full(G: nx.Graph, results):
    
    start = time.time()    
    edges_to_remove = list(G.edges())                
    #record the orginal degree of each node
    original_degree = {}
    nodes = []
    for edge in edges_to_remove:
        for node in edge:
            if node not in nodes:
                nodes.append(node)
            original_degree[node] = G.degree(node)
    
    #sort nodes in descending order of degree
    nodes_sorted = sorted(nodes, key=original_degree.get, reverse=True)
        
    row = {'iteration' : 1, 
           'time' : 0, 
           'r' : 0,
           'target_r': target_assortativity
           'sample_size': sample_size, 
           'edges_rewired': 0,
           'duplicate_edges': 0, 
           'self_edges': 0,
           'existing_edges': 0, 
           'preserved': True}

    #dictionary in which to record the current degree of the nodes as we add edges 
    current_degree = {}
    for node in original_degree:
        current_degree[node] = 0#original_degree[node] - appearances[node]

    potential_edges = []
    for ind, node in enumerate(nodes_sorted):
        j = 1
        while current_degree[node] < original_degree[node]:
            try:
                target = nodes_sorted[-j]
            except IndexError:
                break
            if current_degree[target] < original_degree[target]:
                potential_edges.append([node, target])
                current_degree[node] += 1
                current_degree[target] += 1
            j += 1

    G.remove_edges_from(edges_to_remove)
    edges_to_add, row = check_new_edges(potential_edges, G, row)

    if len(edges_to_add) == sample_size:
        G.add_edges_from(edges_to_add)
        row['edges_rewired'] += len(edges_to_add) 
    else:
        G.add_edges_from(edges_to_remove)
    
    row['r'] += nx.degree_assortativity_coefficient(G)
    row['time'] += time.time() - start
    results.append(row)
    return G, results

def rewire_negative_full_deprecated(G: nx.Graph, target_assort, sample_size = 2, timed = False, time_limit=600):
    
    start = time.time()
    
    while nx.degree_assortativity_coefficient(G) < target_assort:
        edges = list(G.edges())                
        edges_to_remove = random.sample(edges, sample_size)
        original_degree = {}
        nodes = []
        for edge in edges_to_remove:
            for node in edge:
                if node not in nodes:
                    nodes.append(node)
                original_degree[node] = G.degree(node)
    
                    
        nodes_sorted = sorted(nodes, key=original_degree.get, reverse=True)
        
        appearances = {}
        for edge in edges_to_remove:
            for node in edge:
                if node in appearances:
                    appearances[node] += 1
                else:
                    appearances[node] = 1

        current_degree = {}
        for node in original_degree:
            current_degree[node] = original_degree[node] - appearances[node]

        edges_to_add = []
        potential_edges = []
        for ind, node in enumerate(nodes_sorted):
            j = 1
            while current_degree[node] < original_degree[node]:
                try:
                    target = nodes_sorted[-j]
                except IndexError:
                    break
                if current_degree[target] < original_degree[target]:
                    potential_edges.append([node, target])
                    current_degree[node] += 1
                    current_degree[target] += 1
                j += 1

        G.remove_edges_from(edges_to_remove)
        if len(potential_edges) > 0:
            for edge in potential_edges:
                if G.has_edge(edge[0], edge[1]) == False:
                    if edge[0] != edge[1]:
                        if [edge[1], edge[0]] not in potential_edges:
                            if potential_edges.count(edge) == 1:
                                edges_to_add.append(edge)
                            else:
                                duplicate_edge_count += 1
                        else:
                            reverse_edge_count += 1
                    else:
                        self_edge_count += 1
                else:
                    has_edge_fails += 1
        

        if len(edges_to_add) == sample_size:
            G.add_edges_from(edges_to_add)
            edges_rewired += sample_size
            successful_loops += 1
        else:
            G.add_edges_from(edges_to_remove)
        loops += 1 
        time_elapsed = time.time() - start
        if timed == True:
            if time_elapsed > time_limit:
                if nx.degree_assortativity_coefficient(G) < target_assort:
                    return G, nx.degree_assortativity_coefficient(G), time_elapsed, successful_loops, loops, edges_rewired, duplicate_edge_count, reverse_edge_count, self_edge_count, has_edge_fails 

    return G, nx.degree_assortativity_coefficient(G), time_elapsed, successful_loops, loops, edges_rewired, duplicate_edge_count, reverse_edge_count, self_edge_count, has_edge_fails
