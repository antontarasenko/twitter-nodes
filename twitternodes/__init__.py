import json
import itertools
import sys
import os

import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt


__author__ = 'Anton Tarasenko'


def main():
    try:
        ifile = sys.argv[2]
        if not os.path.isfile(ifile): raise Exception("File not found")
    except:
        ifile = input("Enter filename: ").strip()
    try:
        ext = sys.argv[3]
        if ext not in ["pdf", "png", "svg"]: raise Exception("Wrong format")
    except:
        ext = "pdf"

    f = open(ifile)

    un = DB("user_mentions")
    un.populate(json.load(f))
    users = un.group_nodes()
    uedges = un.weigh_edges()
    U = create_graph(users, uedges)

    f.close()
    small_plot(U, saveas="users." + ext)

    print("Done.")


class DB:
    supported_types = ["hashtags", "user_mentions"]

    def __init__(self, type="hashtags"):
        self.type = type
        self.nodes = pd.DataFrame()
        self.edges = pd.DataFrame()

    def populate(self, tweets):
        for c, tweet in enumerate(tweets):
            self.parse_tweet(tweet)
        return c

    def parse_tweet(self, tweet):
        entities = tweet['entities'][self.type]

        insert = {'mentions': 1,
                  'retweeted': 1 if tweet['retweeted'] else 0,
                  'positive': 1 if tweet['text'].count(":)") > 0 else 0,
                  'negative': 1 if tweet['text'].count(":(") > 0 else 0}
        insert['sentiments'] = insert['positive'] - insert['negative']
        cluster = set()

        for entity in entities:
            if self.type == "hashtags":
                insert['name'] = entity['text'].lower()
            elif self.type == "user_mentions":
                insert['name'] = entity['screen_name'].lower()
            else:
                return False

            self.nodes = self.nodes.append(insert, ignore_index=True)
            cluster.add(insert['name'])
        if len(cluster) > 1:
            self.edges = self.edges.append([set(edge) for edge in itertools.combinations(cluster, 2)],
                                           ignore_index=True)

    def group_nodes(self):
        gb = self.nodes.groupby("name")
        return gb.agg(sum).reset_index()

    def weigh_edges(self):
        edges = self.edges
        edges['n'] = 1
        gb = edges.groupby([0, 1])
        return gb.count().reset_index()

    def load_dump(self, file):
        with open(file) as f:
            self.populate(json.load(f))
        nodes = self.group_nodes()
        edges = self.weigh_edges()
        return nodes, edges

    def load_live(n=100):
        pass


def small_plot(G, saveas="", **kwargs):
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
                           node_size=normalize_size(nodesize, 500),
                           node_color=color_sentiments(sentiments))

    # Edges
    edgewidth = []
    for edge in G.edges(data=True):
        edgewidth.append(edge[2]['weight'])
    nx.draw_networkx_edges(G, pos, alpha=0.03, node_size=0, width=normalize_size(edgewidth, 10), edge_color='k')

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


def color_sentiments(sentiments):
    """
    Red-green scale for sentiments around the node.

    :param senti: List of (positive - negative) mentions.
    :return:
    """
    return ['g' if i > 0 else ('r' if i < 0 else 'w') for i in sentiments]


def normalize_size(sizes, scale=10):
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


def create_graph(nodes, edges):
    G = nx.Graph()
    for node in nodes.iterrows():
        r = node[1]
        G.add_node(r['name'],
                   mentions=r['mentions'],
                   retweeted=r['retweeted'],
                   sentiments=r['sentiments'])
    for edge in edges.iterrows():
        row = edge[1]
        G.add_edge(edge[1][0], edge[1][1], weight=edge[1]['n'])
    return G


if __name__ == "__main__":
    main()