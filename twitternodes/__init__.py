import re, itertools, sys, os
import networkx as nx
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# import pylab as plt
from operator import itemgetter

__author__ = 'Anton Tarasenko'

def main():
    # init
    try:
        ifile = sys.argv[2]
        if not os.path.isfile(ifile): raise Exception("File not found")
    except:
        ifile = input("Enter filename: ")

    try:
        format = sys.argv[3]
        if format not in ["pdf", "png", "svg"]: raise Exception("Wrong format")
    except:
        format = "pdf"

    msgs = read_raw_stream(ifile)
    users, uedges = parse_msgs(msgs, prefix="@")
    tags, tedges = parse_msgs(msgs, prefix="#")
    U = create_graph(users, uedges)
    T = create_graph(tags, tedges)
    small_plot(U, saveas="users." + format)
    small_plot(T, saveas="tags." + format)
    print("Done.")

def parse_msgs(msgs, prefix):
    edges = list()
    nodes = pd.DataFrame(columns=['name', 'mentions'])
    for msg in msgs:
        cluster = get_cluster(msg, prefix=prefix)
        cluster_edges = get_edges(cluster)
        edges = edges + cluster_edges

        # TODO put into the graph
        rt = 1 if msg[0:3] == "RT " else 0
        pos = 1 if msg.count(":)") > 0 else 0
        neg = 1 if msg.count(":(") > 0 else 0

        for node in cluster:
            keys = ['mentions', 'retweets', 'positive', 'negative', 'sentiments']
            values = [1, rt, pos, neg, pos - neg]
            if node in nodes['name'].values:
                nodes.ix[nodes['name'] == node, keys] += values
            else:
                nodes = nodes.append(dict(zip(['name'] + keys, [node] + values)),
                                     ignore_index=True)

    wedges = weight_edges(edges)

    return nodes, wedges

def report(G):
    print("Nodes: %s\nEdges: %s" % (len(G.nodes()), len(G.edges())))
    nodes_by_degree = sorted(G.degree_iter(), key=itemgetter(1), reverse=True)
    print("Most connections: %s" % nodes_by_degree[0:5])

def small_plot(G, saveas=""):
    # Plotting
    plt.figure(figsize=(12, 12), facecolor="#FEF8E8")
    try:
        pos=nx.graphviz_layout(G)
    except:
        pos=nx.spring_layout(G, iterations=20)

    # Nodes
    nodesize = []
    sentiments = []
    for node in G.nodes(data=True):
        nodesize.append(node[1]['mentions'])
        sentiments.append(node[1]['sentiments'])
    nx.draw_networkx_nodes(G, pos, alpha=0.1,
                           node_size=normalize_size(nodesize, 500),
                           node_color=color_sentiments(sentiments))

    # Edges
    edgewidth = []
    for edge in G.edges(data=True):
        edgewidth.append(edge[2]['weight'])
    nx.draw_networkx_edges(G, pos, alpha=0.03, node_size=0, width=normalize_size(edgewidth, 10), edge_color='k')

    # Labels
    # TODO find fonts
    font = {# 'fontname'   : 'Monaco', #
            'color'      : 'k',
            # 'fontweight' : 'bold',
            'fontsize'   : 10}
    nx.draw_networkx_labels(G, pos, font=font)

    font['fontsize'] = 15
    plt.title("Network with %d nodes and %d edges" % (G.number_of_nodes(), G.number_of_edges()), font)

    plt.axis("off")
    # Saving
    if len(saveas) > 0:
        plt.savefig(saveas)
    else:
        plt.show()

def color_sentiments(senti):
    """
    Red-green scale for sentiments around the node.

    :param senti: List of (positive - negative) mentions.
    :return:
    """
    return ['g' if i > 0 else ('r' if i < 0 else 'w') for i in senti]

def normalize_size(sizes, scale = 10):
    """
    Normalize node size and edge width.

    :param size: List of numbers.
    :param scale: Scale for resizing.
    :return:
    """
    min = 0
    maxi = max(sizes)
    nsize = [( size / maxi ) * scale for size in sizes]
    return nsize

def read_raw_stream(file, n=0):
    with open(file) as f:
        msgs = f.readlines() if n == 0 else list(itertools.islice(f, n))
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
    if len(edges) > 0:
        df = pd.DataFrame(edges)
        df['n'] = 1
        gb = df.groupby([0, 1])
        return gb.count().reset_index()
    else:
        return pd.DataFrame(columns=[0,1])

def create_graph(nodes, wedges):
    G = nx.Graph()
    for node in nodes.iterrows():
        r = node[1]
        G.add_node(r['name'],
                   mentions = r['mentions'],
                   retweets = r['retweets'],
                   sentiments = r['sentiments'])
    for wedge in wedges.iterrows():
        row = wedge[1]
        G.add_edge(wedge[1][0], wedge[1][1], weight=wedge[1]['n'])
    return G


if __name__ == "__main__":
    main()