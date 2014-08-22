import itertools
import json

import pandas as pd


__author__ = "Anton Tarasenko <antontarasenko@gmail.com>"


def main():
    # TODO plotting from command line
    pass


if __name__ == "__main__":
    main()


class DB:
    supported_types = ["hashtags", "user_mentions"]

    def __init__(self, type="hashtags"):
        self.type = type
        self.nodes = pd.DataFrame(columns=["name", "mentions", "positive", "negative", "sentiments"])
        self.edges = pd.DataFrame(columns=[0, 1, "n"])

    def populate(self, tweets):
        for c, tweet in enumerate(tweets):
            self.parse_tweet(tweet)
        return c + 1

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