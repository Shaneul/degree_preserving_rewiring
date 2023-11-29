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

def rewire(G, target_assortativity, name, sample_size = 2, timed = False, time_limit=600, method='new', return_type = 'full'):
    """
    Parameters
    ----------

    G : networkx.Graph
    target_assortativity : float in range [-1, 1]
    sample_size : int
    timed : bool
    time_limit : float
    method : string
    return_type: string
        'full' or 'summarised'

    Returns:
    --------
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
        method : The method applied. 0 = none (for info about the starting values)
                                     1 = new method, rewiring_full phase
                                     2 = new method, second phase
        summary : Whether or not the row is a summary of the entire rewiring process for a graph
    

    """

    first_row = {'name':name,
                 'iteration': 0, 
                 'time': 0, 
                 'r': nx.degree_assortativity_coefficient(G),
                 'target_r': target_assortativity, 
                 'sample_size': sample_size, 
                 'edges_rewired': 0,
                 'duplicate_edges': 0, 
                 'self_edges': 0,
                 'existing_edges': 0, 
                 'preserved': True,
                 'method': 0,
                 'summary':0}
    
    results = pd.DataFrame([first_row])

    before = degree_list(G)
    if nx.degree_assortativity_coefficient(G) < target_assortativity:
      if method == 'new':
        G = rewire_positive_full(G, results, name, sample_size, return_type)
        G = negatively_rewire(G, target_assortativity, name, results, sample_size, timed, time_limit)
      if method == 'original':
        G = positively_rewire(G, target_assortativity, name, results, sample_size, timed, time_limit)
      if method == 'max':
        G = rewire_positive_full(G, results, name, sample_size, return_type)

    else:
      if method == 'new':
        G = rewire_negative_full(G, results, name, sample_size, return_type)
        G = positively_rewire(G, target_assortativity, name, results, sample_size, timed, time_limit)
      if method == 'original':
        G = negatively_rewire(G, target_assortativity, name, results, sample_size, timed, time_limit)
      if method == 'max':
        G = rewire_negative_full(G, results, name, sample_size, return_type)

    after = degree_list(G)
    #we now have a dataframe of all of our relevant results
    summary_row = {'name': results.loc[results.index[-1], 'name'],
                   'iteration': results.loc[results.index[-1], 'iteration'], 
                   'time': results['time'].sum(), 
                   'r': nx.degree_assortativity_coefficient(G),
                   'target_r': target_assortativity, 
                   'sample_size': sample_size, 
                   'edges_rewired': results['edges_rewired'].sum(),
                   'duplicate_edges': results['duplicate_edges'].sum(), 
                   'self_edges': results['self_edges'].sum(),
                   'existing_edges': results['existing_edges'].sum(), 
                   'preserved': list(before) == list(after),
                   'method': 0,
                   'summary': 1}

    if method == 'new':
        summary_row['method'] = 1
    if method == 'original':
        summary_row['method'] = 2
    if method == 'max':
        summary_row['method'] = 2

    results.loc[len(results)] = summary_row

    if return_type == 'summary':
        summarised_results = results.loc[(results['summary']==1)]
        return summarised_results
    
    else:
        return G, results
    
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



def positively_rewire(G: nx.Graph, target_assortativity, name, results, sample_size = 2, timed = True, time_limit=600):
    """
    Function for fine tuning the assortativity value of a graph.
    
    Parameters
    ----------
    G: nx.Graph
      Graph to be rewired

    target_assortativity: double
      desired assortativity value

    results: pandas.DataFrame
      DataFrame to be added to. One row per iteration. Must have columns as in rewire function

    sample_size: int
      number of edges to be rewired per iteration. The default is 2

    timed: bool
      whether or not to stop the algorithm after a certain amount of time. The default is True

    time_limit: double
      time after which to stop iterating. The default is 600 seconds.

    Returns
    -------
    G: nx.Graph
      rewired graph

    results: pandas.DataFrame
      DataFrame of results, one line per iteration
    """

    alg_start = time.time()
    itr = 1
    while nx.degree_assortativity_coefficient(G) < target_assortativity:
        loop_start = time.time()
        itr += 1
        #define dictionary to track relevant info for each loop
        row = {'name': name,
               'iteration' : itr, 
               'time' : 0, 
               'r' : 0,
               'target_r': target_assortativity,
               'sample_size': sample_size, 
               'edges_rewired': 0,
               'duplicate_edges': 0, 
               'self_edges': 0,
               'existing_edges': 0, 
               'preserved': True,
               'method': 2,
               'summary': 0}

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
        G.remove_edges_from(edges_to_remove)
        edges_to_add, row = check_new_edges(potential_edges, G, row)
                
        if len(edges_to_add) == sample_size:
            G.add_edges_from(edges_to_add)
            row['edges_rewired'] += sample_size
        else:
            G.add_edges_from(edges_to_remove)

        row['time'] += time.time() - loop_start
        row['r'] = nx.degree_assortativity_coefficient(G)
        results.loc[len(results)] = row

        time_elapsed = time.time() - alg_start
    
        
        if timed == True:
            if time_elapsed > time_limit:
                return G, results

    return G



def negatively_rewire(G: nx.Graph, target_assortativity, name, results, sample_size = 2, timed = False, time_limit=600):
    
    """
    Function for fine tuning the assortativity value of a graph.
    
    Parameters
    ----------
    G: nx.Graph
      Graph to be rewired

    target_assortativity: double
      desired assortativity value

    results: pandas.DataFrame
      DataFrame to be added to. One row per iteration. Must have columns as in rewire function

    sample_size: int
      number of edges to be rewired per iteration. The default is 2

    timed: bool
      whether or not to stop the algorithm after a certain amount of time. The default is True

    time_limit: double
      time after which to stop iterating. The default is 600 seconds.

    Returns
    -------
    G: nx.Graph
      rewired graph

    results: pandas.DataFrame
      DataFrame of results, one line per iteration
    """
    
    alg_start = time.time()
    itr = 0
    while nx.degree_assortativity_coefficient(G) > target_assortativity:
        loop_start = time.time()
        itr += 1
        #define dictionary to track relevant info for each loop
        row = {'name' : name,
               'iteration' : itr, 
               'time' : 0, 
               'r' : 0,
               'target_r': target_assortativity,
               'sample_size': sample_size, 
               'edges_rewired': 0,
               'duplicate_edges': 0, 
               'self_edges': 0,
               'existing_edges': 0, 
               'preserved': True,
               'method': 2,
               'summary': 0}

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
        G.remove_edges_from(edges_to_remove)
        edges_to_add, row = check_new_edges(potential_edges, G, row)
        
        if len(edges_to_add) == len(potential_edges):
            G.add_edges_from(edges_to_add)
            row['edges_rewired'] += sample_size
        else:
            G.add_edges_from(edges_to_remove)

        row['time'] += time.time() - loop_start
        row['r'] = nx.degree_assortativity_coefficient(G)
        results.loc[len(results)] = row
        time_elapsed = time.time() - alg_start
        
        if timed == True:
            if time_elapsed > time_limit:
                return G, results

    return G



def rewire_negative_full(G: nx.Graph, results, name, sample_size, return_type, max_time = 600):
    """
    removes every edge from the graph and adds them back ordered in such a way
    to minimise the assortativity.

    Parameters:
    -----------
      G: nx.Graph
        graph to be rewired

      results: pandas.DataFrame
        results dataframe to be passed to function requiring the columns assigned
        in the rewiring function above

      sample_size: int
        number of edges to be rewired. Relevant only for passing the result of this 
        function to another

    Returns:
    --------
      G: nx.Graph
        rewired graph

      results: pandas.DataFrame
        results dataframe passed to the function with one row added per algorithm
        iteration
    """
    before = degree_list(G)    
    alg_start = time.time()    
    edges_to_remove = list(G.edges())                
    itr = 1
    #record the orginal degree of each node
    original_degree = {}
    nodes_descending = []
    nodes_ascending = []
    for edge in edges_to_remove:
        for node in edge:
            if node not in nodes_ascending:
                nodes_ascending.append(node)
                nodes_descending.append(node)
            original_degree[node] = G.degree(node)
    
    #sort nodes in descending order of degree
    nodes_descending = sorted(nodes_descending, key=original_degree.get, reverse=True)
    nodes_ascending = sorted(nodes_ascending, key=original_degree.get, reverse=False)

    row = {'name': name,
           'iteration' : itr, 
           'time' : 0, 
           'r' : 0,
           'target_r': 0,
           'sample_size': sample_size, 
           'edges_rewired': 0,
           'duplicate_edges': 0, 
           'self_edges': 0,
           'existing_edges': 0, 
           'preserved': True,
           'method': 1,
           'summary': 0}

    #dictionary in which to record the current degree of the nodes as we add edges 
    new_neighbors = {}
    for node in original_degree:
        new_neighbors[node] = set() #original_degree[node] - appearances[node]

    potential_edges = []
    for node in nodes_descending:
        for j in range(len(nodes_ascending)):
            target = nodes_ascending[j]
            if len(new_neighbors[node]) < original_degree[node]:
                if len(new_neighbors[target]) < original_degree[target]:
                    if node != target:
                        new_neighbors[node].add(target)
                        new_neighbors[target].add(node)
    
    edges_to_add = []
    for node in new_neighbors:
        for target in new_neighbors[node]:
            edges_to_add.append([node, target])
    
    G.remove_edges_from(edges_to_remove)
    G.add_edges_from(edges_to_add)
    row['edges_rewired'] += len(edges_to_add) 
    row['r'] += nx.degree_assortativity_coefficient(G)
    row['time'] += time.time() - alg_start
    after = degree_list(G)
    row['preserved'] = list(before) == list(after)
    results.loc[len(results)] = row
    
    edges = list(G.edges())
    
    success = True
    for node in original_degree:
        if G.degree(node) < original_degree[node]:
            success = False

    while success == False:
        itr += 1
        start = time.time()
        row = {'name': name,
               'iteration' : itr, 
               'time' : 0, 
               'r' : 0,
               'target_r': 0,
               'sample_size': sample_size, 
               'edges_rewired': 0,
               'duplicate_edges': 0, 
               'self_edges': 0,
               'existing_edges': 0, 
               'preserved': True,
               'method': 1,
               'summary': 0}

        affected_nodes = []
        total_degree = 0
        missing_degree = {}
        for node in original_degree:
            if G.degree(node) != original_degree[node]:
                missing_degree[node] = original_degree[node] - G.degree(node)
                affected_nodes.append(node)
   
        for node in affected_nodes:
            available_edges = 0
            for target in affected_nodes:
                if target != node:
                    if target not in new_neighbors[node]:
                        available_edges += 1
    
        stubs1 = []
        stubs2 = []
        for node in missing_degree:
            j = 0
            while j < missing_degree[node]:
                stubs1.append(node)
                j += 1
       
        edges = list(G.edges())
        while len(stubs2) < len(stubs1):
            edge_to_remove = random.choice(edges)
            if edge_to_remove[0] not in stubs1:
                if edge_to_remove[1] not in stubs1:
                    if G.has_edge(edge_to_remove[0], edge_to_remove[1]) == True:
                        stubs2.append(edge_to_remove[0])
                        stubs2.append(edge_to_remove[1])
                        G.remove_edge(edge_to_remove[0], edge_to_remove[1])
            edges.remove(edge_to_remove)

        stubs1 = sorted(stubs1, key = original_degree.get, reverse=False)
        stubs2 = sorted(stubs2, key = original_degree.get, reverse=True)
        for u, v in zip(stubs1, stubs2):
            G.add_edge(u, v)
            row['edges_rewired'] += 1 
        
        fails = 0
        for node in original_degree:
            if G.degree(node) != original_degree[node]:
                fails += 1
        
        if fails > 0:
            success = False
        else:
            success = True
         
        row['r'] += nx.degree_assortativity_coefficient(G)
        row['time'] += time.time() - start
        after = degree_list(G)
        row['preserved'] = list(before) == list(after)
        if return_type == 'full':
            results.loc[len(results)] = row

        if time.time() - alg_start > max_time:
            break
    
    results.loc[len(results)] = row
    
    return G



def rewire_positive_full(G: nx.Graph, results, name, sample_size, return_type, max_time = 600):
    """
    removes every edge from the graph and adds them back ordered in such a way
    to maximise the assortativity.

    Parameters:
      G: nx.Graph
        graph to be rewired

      results: pandas.DataFrame
        results dataframe to be passed to function requiring the columns assigned
        in the rewiring function above

      sample_size: int
        number of edges to be rewired. Relevant only for passing the result of this 
        function to another
    
    Returns:
    --------
      G: nx.Graph
        rewired graph

      results: pandas.DataFrame
        results dataframe passed to the function with one row added per algorithm
        iteration
    """
    itr = 1
    before = degree_list(G)    
    alg_start = time.time()    
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
    nodes = sorted(nodes, key=original_degree.get, reverse=True)

    row = {'name' : name,
           'iteration' : itr, 
           'time' : 0, 
           'r' : 0,
           'target_r': 0,
           'sample_size': sample_size, 
           'edges_rewired': 0,
           'duplicate_edges': 0, 
           'self_edges': 0,
           'existing_edges': 0, 
           'preserved': True,
           'method': 1,
           'summary': 0}

    #dictionary in which to record the current neighbors of the nodes as we add edges 
    new_neighbors = {}
    for node in original_degree:
        new_neighbors[node] = set()


    potential_edges = []
    for ind, node in enumerate(nodes):
        for target in nodes[ind:]:
            if len(new_neighbors[node]) < original_degree[node]:
                if len(new_neighbors[target]) < original_degree[target]:
                    if node != target:
                        new_neighbors[node].add(target)
                        new_neighbors[target].add(node)
    
    edges_to_add = []
    for node in new_neighbors:
        for target in new_neighbors[node]:
            edges_to_add.append([node, target])
    
    G.remove_edges_from(edges_to_remove)
    G.add_edges_from(edges_to_add)
    row['edges_rewired'] += len(edges_to_add)
    row['r'] += nx.degree_assortativity_coefficient(G)
    row['time'] += time.time() - alg_start
    after = degree_list(G)
    row['preserved'] = list(before) == list(after)
    results.loc[len(results)] = row
    
    edges = list(G.edges())
    
    #check to ensure that we have maintained the degree sequence
    success = True
    for node in original_degree:
        if G.degree(node) < original_degree[node]:
            success = False

    #if degree sequence has not been maintained, find the nodes with incorrect
    #degree and remove edges to rewire to them
    
    while success == False:
        
        itr += 1
        start = time.time()
        row = {'name': name,
               'iteration' : itr, 
               'time' : 0, 
               'r' : 0,
               'target_r': 0,
               'sample_size': sample_size, 
               'edges_rewired': 0,
               'duplicate_edges': 0, 
               'self_edges': 0,
               'existing_edges': 0, 
               'preserved': True,
               'method': 1,
               'summary': 0}

        affected_nodes = []
        total_degree = 0
        missing_degree = {}
        
        for node in original_degree:
            if G.degree(node) != original_degree[node]:
                missing_degree[node] = original_degree[node] - G.degree(node)
                affected_nodes.append(node)
        
        for node in affected_nodes:
            available_edges = 0
            for target in affected_nodes:
                if target != node:
                    if target not in new_neighbors[node]:
                        available_edges += 1
    
        stubs1 = []
        stubs2 = []
        for node in missing_degree:
            j = 0
            while j < missing_degree[node]:
                stubs1.append(node)
                j += 1

        edges = list(G.edges())
        while len(stubs2) < len(stubs1):
            edge_to_remove = random.choice(edges)
            if edge_to_remove[0] not in stubs1:
                if edge_to_remove[1] not in stubs1:
                    if G.has_edge(edge_to_remove[0], edge_to_remove[1]) == True:
                        stubs2.append(edge_to_remove[0])
                        stubs2.append(edge_to_remove[1])
                        G.remove_edge(edge_to_remove[0], edge_to_remove[1])
            edges.remove(edge_to_remove)

        stubs1 = sorted(stubs1, key = original_degree.get, reverse=False)
        stubs2 = sorted(stubs2, key = original_degree.get, reverse=False)
        for u, v in zip(stubs1, stubs2):
            G.add_edge(u, v)
            row['edges_rewired'] += 1
        
        fails = 0
        for node in original_degree:
            if G.degree(node) != original_degree[node]:
                fails += 1
        
        if fails > 0:
            success = False
        else:
            success = True
    
        row['r'] += nx.degree_assortativity_coefficient(G)
        row['time'] += time.time() - start
        after = degree_list(G)
        row['preserved'] = list(before) == list(after)
        results.loc[len(results)] = row
        if return_type == 'full':
            results.loc[len(results)] = row

        if time.time() - alg_start > max_time:
            break

    results.loc[len(results)] = row
    return G



def rewire_positive_full_deprecated(G: nx.Graph, results, sample_size):
    
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
           'target_r': 0,
           'sample_size': sample_size, 
           'edges_rewired': 0,
           'duplicate_edges': 0, 
           'self_edges': 0,
           'existing_edges': 0, 
           'preserved': True,
           'summary': 0}

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
                print('index error')
                break
            if current_degree[target] < original_degree[target]:
                potential_edges.append([node, target])
                current_degree[node] += 1
                current_degree[target] += 1
            j += 1

    G.remove_edges_from(edges_to_remove)
    edges_to_add, row = check_new_edges(potential_edges, G, row)
    if len(edges_to_add) == len(edges_to_remove):
        G.add_edges_from(edges_to_add)
        print('adding edges')
        row['edges_rewired'] += len(edges_to_add) 
    else:
        G.add_edges_from(edges_to_remove)

    print(nx.degree_assortativity_coefficient(G))
    row['r'] += nx.degree_assortativity_coefficient(G)
    row['time'] += time.time() - start
    results.loc[len(results)] = row
    return G, results
