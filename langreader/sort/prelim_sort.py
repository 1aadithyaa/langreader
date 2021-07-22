"""
preliminary classification of texts, given that the user knows (and only knows) top n words, where
n is an element of {100, 250, 500, 1000, 2000, 3000, ..., 10000}
"""
import sys
sys.path.insert(0, "")

import langreader.sort.vectorize as v
import langreader.app.corpus as corpus
import sqlite3
import numpy as np
import time
import pickle
from nltk.corpus import stopwords
import os
import math

modified_stopwords = set(v.preprocess(" ".join(stopwords.words('english'))))
igv = v.get_indexed_global_vector(remove_stopwords=True)

sgv = [word for word in sorted(igv.items(), key=lambda item: item[1][0], reverse=True)] # sorted global vector
rank_dictionary = {k[0]: math.log(v + 1) for v, k in enumerate(sgv)}

text_type_list = ['poem', 'short_story', 'news']
words_known_list = [100, 250, 500, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]

i = 0

def get_top_n_user_profile(n): # get vector where top n most frequent words have a score of 1, while the rest are -1; words unknown in the dictionary are given a score of -2
    wv = [-1] * (len(sgv) + 1) # the last value is for words unknown in the dictionary

    for i in range(n):
        wv[igv[sgv[i][0]][1]] = 1

    wv[len(sgv)] = 0
    
    return wv

def get_word_vector_from_frequency_vector(sgv, rfv):
    global i 
    print(i, end = '\r')
    i += 1
    
    wv = [0] * (len(igv) + 1)

    for key, value in rfv.items():
        if key in igv:
            wv[igv[key][1]] = value
        else:
            wv[len(igv)] += value # last value is for words unknown in the dictionary

    return wv

def get_readability(user_prof, word_vector, curve=True):
    x = np.dot(user_prof, word_vector)
    if curve:
        if x >= .95:
            result = 1 - (.95 - x)**2
        else:
            result = 1 - 16*(.95 - x)**2
        return result
    else:
        return x

def record_k_most_readable_texts(n, k, exec_stmt):
    
    up = get_top_n_user_profile(n)

    conn = sqlite3.connect("resources/sqlite/corpus.sqlite")
    c = conn.cursor()
    c.execute("SELECT * FROM Repository " + exec_stmt)
    all_texts = c.fetchall()
    # print(type(all_texts))
    text_tuples_list = [(tup[0], tup[1], get_word_vector_from_frequency_vector(sgv, pickle.loads(tup[11]))) for tup in all_texts] # 0 > article_id; 1 > article_title; 11 > frequency_vector

    return sorted(text_tuples_list, key=lambda tuple: get_readability(up, tuple[2], curve=True), reverse=True)[:k] #TODO: get rid of tuple[3], set tuple[2] as get_word_vector_from_frequency_vector(sgv, pickle.loads(tuple[11]))


def get_baseline_profile_from_level(language_level):
    known_words = -1
    if language_level == 'A1':
        known_words = 300
    if language_level == 'A2':
        known_words = 600
    if language_level == 'B1':
        known_words = 1250
    if language_level == 'B2':
        known_words = 2500
    if language_level == 'C1':
        known_words = 5000
    if language_level == 'C2':
        known_words = 10000
    
    # set known words to 1; set the next known_words words to 0; the rest are -1
    wv = [-1] * (len(sgv) + 1) 
    for i in range(known_words):
        wv[igv[sgv[i][0]][1]] = 1
    for i in range(known_words, known_words*2):
        if i >= len(sgv):
            break
        wv[igv[sgv[i][0]][1]] = 0
    
    wv[len(sgv)] = 0

    return wv


def get_words_to_check_from_profile(user_profile, k):
    return sorted(list(zip(user_profile, igv)), key=lambda pair: pair[0]**2)[:k]


def get_weighted_random_words_from_profile(user_profile, top_k, n):
    words = get_words_to_check_from_profile(user_profile, top_k)
    p_dist = [1.1 - j[0]**2 for j in words]
    p_dist = [j/sum(p_dist) for j in p_dist]
    return [i for i in np.random.choice([j[1] for j in words], n, p=p_dist, replace=False)]


def update_profile(user_profile, words_to_update, words_values):
    for word, value in zip(words_to_update, words_values):
        user_profile[igv[word][1]] = value


def record_prelim_sort():
    exec_stmt = "WHERE text_type = "
    for text_type in text_type_list:
        for n in words_known_list:
            global i 
            i = 0
            filename = 'langreader/sort/resources/prelim/' + text_type + '/knows' + str(n) + '.prelim'
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            pickle.dump(record_k_most_readable_texts(n, 1000, exec_stmt + "'" + text_type + "'"), open(filename, 'wb'))


def get_prelim_sort(text_type, n):
    return pickle.load(open('langreader/sort/resources/prelim/' + text_type + '/knows' + str(n) + '.prelim', 'rb'))


def get_top_k_texts_from_user_profile(user_profile, text_type, k, user_id):
    user_sum = 0
    for i in user_profile:
        user_sum += i
    
    last_n = words_known_list[0]
    for n in words_known_list:
        if user_sum > get_vector_sum_for_top_n(n):
            break
        last_n = n
    
    prelim_sort = get_prelim_sort(text_type, last_n)
    delete_texts = set(corpus.get_all_texts_to_not_suggest(user_id))

    return [(text_tuple[0], text_tuple[1]) for text_tuple in prelim_sort if text_tuple[0] not in delete_texts][:k] # 0 > article_id; 1 > article_title



def sort_with_user_profile(prelim_sort, user_profile):
    return sorted(prelim_sort, key=lambda tuple: get_readability(user_profile, tuple[2], curve=True), reverse=True)


def get_vector_sum_for_top_n(n):
    return n*2 - len(igv)


if __name__ == '__main__':
    print(rank_dictionary)
    quit()
    record_prelim_sort()
    for text_type in text_type_list:
        for n in words_known_list:
            print(len(get_prelim_sort(text_type, n)))