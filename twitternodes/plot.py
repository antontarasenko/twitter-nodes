import os
import re

from matplotlib import pyplot as plt
import networkx as nx

from twitternodes import DB, Stream


__author__ = "Anton Tarasenko <antontarasenko@gmail.com>"


def main():
    return True


def graph(nodes, edges):
    G = nx.Graph()
    added_nodes = set()
    for node in nodes.iterrows():
        r = node[1]
        G.add_node(r['name'],
                   mentions=r['mentions'],
                   retweeted=r['retweeted'],
                   sentiments=r['sentiments'])
        added_nodes.add(r['name'])
    for edge in edges.iterrows():
        row = edge[1]
        G.add_edge(edge[1][0], edge[1][1], weight=edge[1]['n'])

    # Ensure that if nodes are filtered, edges don't have excluded nodes
    G.remove_nodes_from(set(G.nodes()) - added_nodes)

    return G


def gradient(sentiments):
    """
    Red-green scale for sentiments around the node.

    :param senti: List of (positive - negative) mentions.
    :return:
    """
    return ['g' if i > 0 else ('r' if i < 0 else 'w') for i in sentiments]


def normalize(values, scale=10):
    """
    Normalize node size and edge width.

    :param values: List of numbers.
    :param scale: Scale for resizing.
    :return:
    """
    min = 0
    maxi = max(values) if len(values) > 0 else scale
    new_size = [( size / (maxi - min) ) * scale for size in values]
    return new_size


def plot(G, saveas="", **kwargs):
    # Plotting
    plt.figure(facecolor="#FEF8E8", **kwargs)
    try:
        pos = nx.graphviz_layout(G)
    except:
        pos = nx.spring_layout(G, iterations=20)

    # Nodes
    nodesize = []
    sentiments = []
    for node in G.nodes(data=True):
        nodesize.append(node[1]['mentions'])
        sentiments.append(node[1]['sentiments'])
    nx.draw_networkx_nodes(G, pos, alpha=0.1,
                           node_size=normalize(nodesize, 500),
                           node_color=gradient(sentiments))

    # Edges
    edgewidth = []
    for edge in G.edges(data=True):
        edgewidth.append(edge[2]['weight'])
    nx.draw_networkx_edges(G, pos, alpha=0.03, node_size=0, width=normalize(edgewidth, 10), edge_color='k')

    # Labels
    font = {'color': 'k',
            'fontsize': 10}
    nx.draw_networkx_labels(G, pos, font=font)

    font['fontsize'] = 15
    plt.title("Network with %d nodes and %d edges" % (G.number_of_nodes(), G.number_of_edges()), font)

    plt.axis("off")
    # Saving
    if len(saveas) > 0:
        plt.savefig(saveas)
        print("Plot saved to %s" % os.path.realpath(saveas))
    else:
        plt.show()


def plot_json(file, ext="pdf"):
    for i in ["hashtags", "user_mentions"]:
        db = DB(i)
        G = graph(*db.load_json(file))
        plot(G, saveas="%s.%s.%s" % (re.sub("\.json$", "", file), i, ext))
    return True


def plot_live(*args, **kwargs):
    s = Stream()
    s.fetch_live(*args, **kwargs)
    db = DB()
    db.populate(s.tweets)
    G = graph(db.group_nodes(), db.weigh_edges())
    plot(G)
    return None