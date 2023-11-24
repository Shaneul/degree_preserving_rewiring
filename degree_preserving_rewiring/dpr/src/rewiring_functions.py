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

def rewire_positive_full(G: nx.Graph, target_assort, sample_size = 2, timed = False, time_limit=600):
    
    start = time.time()
    edges_rewired = 0
    successful_loops = 0
    loops = 0
    duplicate_edge_count = 0
    reverse_edge_count = 0
    self_edge_count = 0
    has_edge_fails = 0
    time_elapsed = 0
    
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

#    print(f'Took {loops} iterations with sample size {sample_size}. Had {repeated_edge_fails} loops where the same edge was picked twice. Tried to add an existing edge {has_edge_fails} times')
    return G, nx.degree_assortativity_coefficient(G), time_elapsed, successful_loops, loops, edges_rewired, duplicate_edge_count, reverse_edge_count, self_edge_count, has_edge_fails


def rewire_negative_full(G: nx.Graph, target_assort, sample_size = 2, timed = False, time_limit=600):
    
    start = time.time()
    edges_rewired = 0
    successful_loops = 0
    loops = 0
    duplicate_edge_count = 0
    reverse_edge_count = 0
    self_edge_count = 0
    has_edge_fails = 0
    time_elapsed = 0
    
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

#    print(f'Took {loops} iterations with sample size {sample_size}. Had {repeated_edge_fails} loops where the same edge was picked twice. Tried to add an existing edge {has_edge_fails} times')
    return G, nx.degree_assortativity_coefficient(G), time_elapsed, successful_loops, loops, edges_rewired, duplicate_edge_count, reverse_edge_count, self_edge_count, has_edge_fails
