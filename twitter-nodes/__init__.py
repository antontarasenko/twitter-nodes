import re, itertools, sys, os
import networkx as nx
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# import pylab as plt
from operator import itemgetter

__author__ = 'Anton Tarasenko'
FPATH = os.path.realpath('..') + "/data/raw/" # TODO do via sys.*

def main():
    # init
    msgs = load_raw_file("test-ferguson.txt")
    users, uedges = parse_msgs(msgs, prefix="@")
    tags, tedges = parse_msgs(msgs, prefix="#")
    U = create_graph(users, uedges)
    T = create_graph(tags, tedges)
    small_plot(U)
    small_plot(T)

def load_raw_file(file):
    path = FPATH + file
    msgs = read_raw_stream(path)
    return msgs

def parse_msgs(msgs, prefix):
    edges = list()
    nodes = pd.DataFrame(columns=['name', 'mentions'])
    for msg in msgs:
        cluster = get_cluster(msg, prefix=prefix)
        cluster_edges = get_edges(cluster)
        edges = edges + cluster_edges

        # TODO put into the graph
        isrt = msg[0:3] == "RT "
        ispos = msg.count(":)") > 0
        isneg = msg.count(":(") > 0

        for node in cluster:
            # TODO make nicer
            if node in nodes['name'].values:
                ix = nodes['name'] == node
                nodes.ix[ix, 'mentions'] += nodes.ix[ix, 'mentions']
            else:
                nodes = nodes.append({'name': node, 'mentions': 1}, ignore_index=True)

    wedges = weight_edges(edges)

    return nodes, wedges

def report(G):
    print("Nodes: %s\nEdges: %s" % (len(G.nodes()), len(G.edges())))
    nodes_by_degree = sorted(G.degree_iter(), key=itemgetter(1), reverse=True)
    print("Most connections: %s" % nodes_by_degree[0:5])

def small_plot(G, save=False):
    # Plotting
    plt.figure(figsize=(12, 12))
    try:
        pos=nx.graphviz_layout(G)
    except:
        pos=nx.spring_layout(G, iterations=20)
    # nx.draw_networkx_nodes(G, pos, node_color='w', alpha=0.4)
    nx.draw_networkx_edges(G, pos, alpha=0.1, node_size=0, width=1, edge_color='k')
    nx.draw_networkx_labels(G, pos, fontsize=11)
    if save:
        plt.savefig("small_plot.png")
    else:
        plt.show()

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
    a, b = itertools.tee(iterable)
    next(b, None)
    return set(a, b)

def get_edges(cluster):
    edges = [set(i) for i in itertools.combinations(cluster, 2)]
    return edges

def weight_edges(edges):
    df = pd.DataFrame(edges)
    df['n'] = 1
    gb = df.groupby([0, 1])
    c = gb.count().reset_index()
    return c

def create_graph(nodes, wedges):
    G = nx.Graph()
    for node in nodes.iterrows():
        G.add_node(node[1]['name'], mentions = node[1]['mentions'])
    for wedge in wedges.iterrows():
        row = wedge[1]
        G.add_edge(wedge[1][0], wedge[1][1], weight=wedge[1]['n'])
    return G


if __name__ == "__main__":
    main()