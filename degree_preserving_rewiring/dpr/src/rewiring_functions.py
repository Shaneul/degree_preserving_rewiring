# -*- coding: utf-8 -*-
"""
Created on Thu Aug  3 14:39:46 2023

@author: shane
"""

import networkx as nx
import numpy as np
import time
import random

def degree_list(G):
    """
    Parameters
    ----------

    G : networkx.graph OR list


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

def positively_rewire_original(G: nx.Graph, target_assort, sample_size = 2, timed = False, time_limit=600):
    start = time.time()
    edges_rewired = 0
    successful_loops = 0
    loops = 0
    time_elapsed = 0
    while nx.degree_assortativity_coefficient(G) < target_assort:
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
        edges_to_add = []
        G.remove_edges_from(edges_to_remove)
        for edge in potential_edges:
            if G.has_edge(edge[0], edge[1]) == False:
                if edge[0] != edge[1]:
                    if [edge[1], edge[0]] not in potential_edges:
                        if potential_edges.count(edge) == 1:
                            edges_to_add.append(edge)
                
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
                    return G, nx.degree_assortativity_coefficient(G), time_elapsed, successful_loops, loops, edges_rewired

#    print(f'Took {loops} iterations with sample size {sample_size}. Had {repeated_edge_fails} loops where the same edge was picked twice. Tried to add an existing edge {has_edge_fails} times')
    return G, nx.degree_assortativity_coefficient(G), time_elapsed, successful_loops, loops, edges_rewired


def positively_rewire_subgraph(G, target_assort, sample_size=10, timed=False, time_limit=120):
    """
    This version should be used for short tailed distributions 
    e.g. exponential, poisson

    Parameters
    ----------
    G : nx.Graph
        Graph to be rewired.
    target_assort : float
        desired assortativity value.
    sample_size : int, optional
        number of edges to rewire at one time. The default is 10.
        testing required to see how the sample size affectes performance
    rank: bool, optional
        whether or not to rank the nodes to rewire them in the most effective
        way, False performs better, may be obsolete
    Returns
    -------
    G : nx.Graph
        Rewired graph, overwrites original graph.

    """
    initial_assortativity = nx.degree_assortativity_coefficient(G)
    edges_rewired = 0
    loops = 0
    successful_loops = 1
    start = time.time()
    while nx.degree_assortativity_coefficient(G) < target_assort:
        E_k = 0
        G_edges = list(G.edges())
        for e in G_edges:
            E_k += G.degree(e[0]) + G.degree(e[1])

        deg_dict = {}
        nodes = []
        for node in G.nodes():
            deg_dict[node] = G.degree(node)
            nodes.append(node)
        nodes_sorted = sorted(nodes, key=deg_dict.get)
        set1 = [nodes_sorted[i] for i in range(len(nodes_sorted)) if i % 2 == 1]
        set2 = [nodes_sorted[i] for i in range(len(nodes_sorted)) if i % 2 == 0]
        G1 = G.subgraph(list(set1))
        G2 = G.subgraph(list(set2))
        #need better way of splitting perhaps, this way is the same every time
        #and so can run out of nodes to rewire
        #print(f'subgraph time: {t2 -t1}')
        G1_edges = list(G1.edges())
        G2_edges = list(G2.edges())
        #print(f'G1: {len(G1_edges)}, G2; {len(G2_edges)}, sample: {sample_size}')
        try:
            edges_to_remove_1 = random.sample(G1_edges, sample_size)
        except ValueError:
            return ['NA'] * 6
        
        try:
            edges_to_remove_2 = random.sample(G2_edges, sample_size)
        except ValueError:
            return ['NA'] * 6
        
        deg_dict = {}
        G1_nodes = []
        G2_nodes = []
        for edge in edges_to_remove_1:
            for node in edge:
                G1_nodes.append(node)
                deg_dict[node] = G.degree(node)
        for edge in edges_to_remove_2:
            for node in edge:
                G2_nodes.append(node)
                deg_dict[node] = G.degree(node)
                
        G1_nodes_sorted = sorted(G1_nodes, key=deg_dict.get)
        G2_nodes_sorted = sorted(G2_nodes, key=deg_dict.get)
        
        potential_edges = [[G1_nodes_sorted[i], G2_nodes_sorted[i]] for i in range(len(G1_nodes_sorted))]
        edges_to_add = []
        for edge in potential_edges:
            if G.has_edge(edge[0], edge[1]) == False:
                if potential_edges.count(edge) == 1:
                    if [edge[1], edge[0]] not in potential_edges:
                        edges_to_add.append(edge)
                
                            
        if len(edges_to_add) == len(potential_edges):
            edges_to_remove_1.extend(edges_to_remove_2)
            G.remove_edges_from(edges_to_remove_1)
            G.add_edges_from(edges_to_add)
            successful_loops += 1
            edges_rewired += len(edges_to_add)

        loops += 1
        time_elapsed = time.time() - start
        if timed == True:
            if time_elapsed > time_limit:
                if nx.degree_assortativity_coefficient(G) < target_assort:
                    return G, nx.degree_assortativity_coefficient(G), time_elapsed, successful_loops, loops, edges_rewired
                    
    return G, nx.degree_assortativity_coefficient(G), time_elapsed, successful_loops, loops, edges_rewired


def negatively_rewire(G, target_assort, sample_size, timed, time_limit):
    initial_assortativity = nx.degree_assortativity_coefficient(G)
    start = time.time()
    successful_loops = 0
    loops = 0
    edges_rewired = 0
    time_elapsed = 0
    while nx.degree_assortativity_coefficient(G) > target_assort:
        G_edges = list(G.edges())
        edge_sample = random.sample(G_edges, sample_size)
        deg_dict = {}
        nodes = []
        for edge in edge_sample:
            for node in edge:
                nodes.append(node)
                deg_dict[node] = G.degree(node)

        nodes_sorted = sorted(nodes, key = deg_dict.get)
        n_nodes = int(len(nodes_sorted)/2)
        potential_edges = [(nodes_sorted[i], nodes_sorted[len(nodes) - 1 - i]) for i in range(n_nodes)]


        edges_to_add = []
        for edge in potential_edges:
            if G.has_edge(edge[0], edge[1]) == False:
                if edge[0] != edge[1]:
                    if [edge[1], edge[0]] not in potential_edges:
                        if potential_edges.count(edge) == 1:
                            edges_to_add.append(edge)

        if len(edges_to_add) == len(potential_edges):
            G.remove_edges_from(edge_sample)
            G.add_edges_from(edges_to_add)
            successful_loops += 1
            edges_rewired += len(potential_edges)
        
        loops += 1
        if timed == True:
            time_elapsed = time.time() - start
            if time_elapsed > time_limit:
                return G, nx.degree_assortativity_coefficient(G), time_elapsed, successful_loops, loops, edges_rewired


    return G, nx.degree_assortativity_coefficient(G), time_elapsed, successful_loops, loops, edges_rewired
