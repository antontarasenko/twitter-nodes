from operator import itemgetter

__author__ = 'Anton Tarasenko'

import re, itertools, sys, os
import networkx as nx
import matplotlib.pyplot as plt

TFILE = os.path.realpath('..') + "/data/raw/test-ferguson.txt"

def main():
    # init
    msgs = read_raw_stream(TFILE)
    edges = list()
    for msg in msgs:
        cluster = get_cluster(msg)
        cluster_edges = get_edges(cluster)
        edges = edges + cluster_edges
    wedges = weight_edges(edges)

    # Report
    G = create_graph(wedges)
    print("Nodes: %s\nEdges: %s" % (len(G.nodes()), len(G.edges())))
    nodes_by_degree = sorted(G.degree_iter(), key=itemgetter(1), reverse=True)
    print("Most connections: %s" % nodes_by_degree[0:5])

    # Plotting
    plt.figure(figsize=(10, 10))
    try:
        pos=nx.graphviz_layout(G)
    except:
        pos=nx.spring_layout(G, iterations=20)
    nx.draw_networkx_nodes(G, pos, node_color='w', alpha=0.4)
    nx.draw_networkx_edges(G, pos, alpha=0.4, node_size=0, width=1, edge_color='k')
    nx.draw_networkx_labels(G, pos, fontsize=14)
    plt.show();

def read_raw_stream(file):
    with open(file) as f:
        msgs = f.readlines()
    return msgs

def get_cluster(msg, prefix='#'):
    matches = map(lambda x: x.lower(), re.findall('[%s](\w+)' % prefix, msg))
    # remove duplicates
    cluster = set(matches)
    return cluster

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return set(a, b)

def get_edges(cluster):
    edges = [set(i) for i in itertools.combinations(cluster, 2)]
    return edges

def weight_edges(edges):
    wedges = set()
    # TODO Make faster
    for edge in edges:
        wedges.add((tuple(edge), edges.count(edge)))
    return wedges

def create_graph(wedges):
    G = nx.Graph()
    for wedge in wedges:
        G.add_edge(wedge[0][0], wedge[0][1], weight=wedge[1])
    return G


if __name__ == "__main__":
    main()