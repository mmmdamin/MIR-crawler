import collections
import json
import math
import os
import random
import sys

import requests
from tqdm import tqdm

articles_path = '../crawler/articles'
articles = []
titles = {}
abstracts = {}
for article_name in os.listdir(articles_path):
    x = requests.get('http://127.0.0.1:9200/articles/article/{}'.format(article_name.split('.')[0]))
    article = json.loads(x.text).get('_source')
    if article:
        articles.append(article)
        abstracts[article['id']] = collections.Counter(x.lower() for x in article.get('abstract').split())
        titles[article.get('id')] = collections.Counter(x.lower() for x in article.get('title').split())

MAX_LEVEL = 100
CLUSTER_NUM = 3
dictionary = {}
mean = [{} for k in range(CLUSTER_NUM)]
cl = []

for doc in abstracts.values():
    for t, v in doc.iteritems():
        dictionary[t] = max(dictionary.get(t), v)


def distance(doc1, doc2):
    doc1_abs = abstracts[doc1]
    doc2_abs = doc2
    dist = 0
    for key in set(doc1_abs.keys()).union(set(doc2_abs.keys())):
        dist += math.pow(doc1_abs.get(key, 0) - doc2_abs.get(key, 0), 2)
    return math.sqrt(dist)


def cal_j():
    j_index = 0
    for i, item in enumerate(cl):
        for j in item:
            for key in mean[i].keys():
                j_index += math.pow(mean[i].get(key) - j.get(key, 0), 2)
    return j_index


def make_clusters():
    for i in range(len(mean) - len(cl)):
        cl.append([])
    for i in range(len(mean)):
        cl[i] = []
    for doc in abstracts:
        min_dist = sys.maxint
        cluster = 0
        for j, m in enumerate(mean):
            d = distance(doc, m)
            if d < min_dist:
                min_dist = d
                cluster = j
        cl[cluster].append(doc)


def k_means():
    con = True
    while con:
        con = False
        for m in mean:
            for j, v in dictionary.iteritems():
                r = random.randint(0, v)
                m[j] = r
        make_clusters()
        for item in cl:
            if len(item) == 0:
                con = True
    c = 0

    while c < MAX_LEVEL:
        c += 1
        for k in range(len(mean)):
            mean[k] = {}
        for i, item in enumerate(cl):
            for j in item:
                for k, value in abstracts[j].iteritems():
                    mean[i].update({k: mean[i].get(k, 0) + float(value) / len(item)})
        make_clusters()


def p(docs_field, kc, kt):
    n11 = 0
    n01 = 0
    n10 = 0
    n00 = 0

    for ind, c in enumerate(cl):
        for d in c:
            doc = docs_field.get(d)
            if ind == kc:
                if doc.get(kt):
                    n11 += 1
                else:
                    n10 += 1
            else:
                if doc.get(kt):
                    n01 += 1
                else:
                    n00 += 1

    n = len(docs_field)
    n1_ = n10 + n11
    n0_ = n00 + n01
    n_1 = n01 + n11
    n_0 = n00 + n10
    return ((n11 * math.log(((n11 * n) / (n1_ * n_1 + 0.1)) + 0.1, 2)) + (
        n01 * math.log((n01 * n / (n0_ * n_1 + 0.1)) + 0.1, 2)) +
            (n00 * math.log((n00 * n / (n0_ * n_0 + 0.1)) + 0.1, 2)) + (
                n10 * math.log((n10 * n / (n1_ * n_0 + 0.1)) + 0.1, 2)) / n)


ABSTRACT_LABEL_LEN = 30
TITLE_LABEL_LEN = 3


def labeling(docs_field, num):
    import operator

    r = []
    for kc, c in enumerate(cl):
        pt = {}
        for term in dictionary.keys():
            pt[term] = p(docs_field, kc, term)
        sorted_pt = sorted(pt.items(), key=operator.itemgetter(1))
        r.append(list(reversed(sorted_pt))[:num])
    return ["".join(x[0] + " " for x in z) for z in r]


k_means()
print labeling(titles, TITLE_LABEL_LEN)
