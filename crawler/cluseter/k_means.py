import collections
import json
import math
import os
import nltk
import sys
from elasticsearch import Elasticsearch, NotFoundError
from tqdm import tqdm
from cluseter import termgraph

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

articles_path = '../crawler/articles'
articles = []
titles = {}
abstracts = {}
dictionary = {}
stop_words = set(nltk.corpus.stopwords.words('english'))

for article_name in os.listdir(articles_path):
    try:
        article = es.get_source(index="rg", doc_type="article", id=int(article_name.split(".")[0]))
        articles.append(article)
        abstracts[article['id']] = collections.Counter(
            x for x in nltk.word_tokenize(article.get('abstract').lower()) if x not in stop_words)
        titles[article.get('id')] = collections.Counter(
            x for x in nltk.word_tokenize(article.get('title').lower()) if x not in stop_words)
    except NotFoundError:
        pass
for doc in abstracts.values():
    for t, v in doc.iteritems():
        dictionary[t] = max(dictionary.get(t), v)


def calc_clusters(cluster_num):
    MAX_LEVEL = 5
    mean = [{} for cnum in range(cluster_num)]
    cl = []

    def distance(doc1, doc2):
        doc1_abs = abstracts[doc1]
        doc2_abs = doc2
        dist = 0
        for key in set(doc1_abs.keys()).union(set(doc2_abs.keys())):
            dist += math.pow(doc1_abs.get(key, 0) - doc2_abs.get(key, 0), 2)
        return math.sqrt(dist)

    def cal_j():
        j_index = 0
        for indx, item in enumerate(cl):
            for j in item:
                for key in mean[indx].keys():
                    j_index += math.pow(mean[indx].get(key) - abstracts.get(j).get(key, 0), 2)
        return j_index

    def make_clusters():
        for y in range(len(mean) - len(cl)):
            cl.append([])
        for y in range(len(mean)):
            cl[y] = []
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
        for z in range(len(mean)):
            mean[z] = abstracts.get(abstracts.keys()[z])
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

    k_means()
    return cal_j(), cl


def p(docs_field, kc, kt, clusters):
    n11 = 0
    n01 = 0
    n10 = 0
    n00 = 0

    for ind, c in enumerate(clusters):
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


def labeling(docs_field, num, clusters):
    import operator

    r = []
    for kc, c in enumerate(clusters):
        pt = {}
        for term in dictionary.keys():
            pt[term] = p(docs_field, kc, term, clusters)
        sorted_pt = sorted(pt.items(), key=operator.itemgetter(1))
        r.append(list(reversed(sorted_pt))[:num])
    return ["".join(x[0] + " " for x in z) for z in r]


def main(k=None):
    labels = []
    data = []
    total = len(articles)
    old_j = 0
    new_j = None
    my_clusters = None
    if not k:
        with tqdm(total=total, desc="Plotting...", file=sys.stdout) as pbar:
            for i in range(1, total + 1, 1):
                labels.append("%4d" % i)
                new_j, my_clusters = calc_clusters(i)
                data.append(new_j)
                if abs(new_j - old_j) < 0.1:
                    break
                old_j = new_j

                pbar.update(1)
        termgraph.main(labels, data)
    else:
        new_j, my_clusters = calc_clusters(k)
    clusters = {}
    title_labels = labeling(titles, TITLE_LABEL_LEN, my_clusters)
    abs_labels = labeling(abstracts, ABSTRACT_LABEL_LEN, my_clusters)
    for ix, my_cluster in enumerate(my_clusters):
        clusters.update({ix: (my_cluster, title_labels[ix], abs_labels[ix])})
    return clusters


with open("../crawler/x.json", "w") as f:
    f.write(json.dumps(main(k=5)))
