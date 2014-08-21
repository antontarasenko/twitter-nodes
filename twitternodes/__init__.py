import json
import itertools
from math import log
import sys
import os

import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import re


__author__ = 'Anton Tarasenko'


def main():
    return True


class DB:
    supported_types = ["hashtags", "user_mentions"]

    def __init__(self, type="hashtags"):
        self.type = type
        self.nodes = pd.DataFrame(columns=["name", "mentions", "positive", "negative", "sentiments"])
        self.edges = pd.DataFrame(columns=[0, 1, "n"])

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
        # if len(self.nodes.index) > 0:
        try:
            gb = self.nodes.groupby("name")
            return gb.agg(sum).reset_index()
        except:
            pass


    def weigh_edges(self):
        edges = self.edges
        edges['n'] = 1
        try:
            gb = edges.groupby([0, 1])
            return gb.count().reset_index()
        except:
            pass

    def load_json(self, file):
        # Start from scratch
        self.nodes = pd.DataFrame()
        self.edges = pd.DataFrame()
        with open(file) as f:
            self.populate(json.load(f))
        nodes = self.group_nodes()
        edges = self.weigh_edges()
        return nodes, edges

    def load_live(n=100):
        pass


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


if __name__ == "__main__":
    main()