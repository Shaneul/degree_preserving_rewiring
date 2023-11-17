import networkx as nx
import pickle

def create_network(dataset, headers):
    with open(dataset) as d:
        j = 0
        while j < headers:
            next(d)
            j += 1
        G = nx.Graph()
        for line in d:
            l = line.strip().split()
            G.add_edge(l[0], l[1])

    G = nx.convert_node_labels_to_integers(G, first_label=0)
    return G

def Create_Network1(dataset): ##Use if file has one header
    data = dataset
    with open(data) as df:
        G = nx.Graph()
        next(df)
        for line in df:
            l = line.strip().split()
            G.add_edge(l[0], l[1])        

    G = nx.convert_node_labels_to_integers(G, first_label = 0)  
    return G

def Create_Network2(dataset): ##Use if file has 2 headers
    data = dataset
    with open(data) as df:
        G = nx.Graph()
        next(df)
        next(df)
        for line in df:
            l = line.strip().split()
            G.add_edge(l[0], l[1])        

    G = nx.convert_node_labels_to_integers(G, first_label = 0)  
    return G

def Create_asoiaf(dataset):
    G = pickle.load(open('data/' + dataset))
    return G

def Create_from_tsv(dataset):
    G = nx.Graph()

    #Reads through text files and creates networks
    with open('data/'+dataset,'rb') as f:
        headers = f.readline().decode('cp1252').strip().split('\t')
        links, h_link = headers.index('Friendly links'), headers.index('Hostile Links')
        gend = headers.index('Gender')
        for line in f:
            l = line.decode('cp1252').split('\t')
            if line[0] == b'%':
                continue
            l = [u.strip().replace('"','') for u in l]
            u = l[0]
            if len(u) > 1:
                if u in G and len(G.nodes()[u]) < 1:
                    G.nodes()[u]['Sex'] = l[gend].upper()
                G.add_node(u,Sex=l[gend].upper())
            for v in l[links:]:
                ltype = 'friendly'
                if l.index(v) >= h_link:
                    ltype = 'hostile'
                        #Uncomment this next line to remove hostile links
#                        continue
                if len(u) > 1 and len(v) > 1:
                    if G.has_edge(u,v):
                        G.get_edge_data(u,v)['weight'] += 1
                    else:
                        G.add_edge(u,v,weight=1, link=ltype)


        for u in [v for v in G if len(G.nodes()[v]) < 1]:
            G.nodes()[u]['Sex'] = ''
    return G

