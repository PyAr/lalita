# -*- coding: utf-8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import os
import pkg_resources
import re
import sqlite3
from random import random, randrange

if pkg_resources.resource_exists(__name__, 'logs.sqlite'):
    db_filename = pkg_resources.resource_filename(__name__, 'logs.sqlite')
else:
    db_filename = 'logs.sqlite'

conn = sqlite3.connect(db_filename)
cursor = conn.cursor()

def magic(line):
    count = 0
    if not line: return count
    for i,c in enumerate(line):
        count += i*ord(c)
    return float(count)/len(line)

try:
    cursor.execute("""create table logs (id integer primary key, next integer, whom text, txt text, magic real)""")
    pattern = re.compile('\d\d:\d\d <.([^>]*)> (.*)')
    personal_pattern = re.compile('[^:]*:(.*)')
    logs = pkg_resources.resource_string(__name__, '#pyar.log')
    matchs = re.findall(pattern,logs)
    matchs.reverse()
    for name,match in matchs:
        personal = re.findall(personal_pattern,match)
        if personal:
            match = personal[0]
        try:
            number = magic(match)
        except ZeroDivisionError:
            continue
        if cursor.lastrowid is None:
            cursor.execute('insert into logs values (NULL,NULL,?,?,?)', (name,match,number))
        else:
            cursor.execute('insert into logs values (NULL,?,?,?,?)', (cursor.lastrowid,name,match,number))
    conn.commit()
except sqlite3.OperationalError:
    pass

_repeating_you = ['repitiendote','lo mismo digo','igual que vos decis','haciendote eco','repeating you']
def repeating():
    return _repeating_you[randrange(len(_repeating_you))]

_easy_answer = ['si', 'no', 'siempre', 'creo que yo', 'la verdad es que no', 'puede, puede...']
def easy_answer():
    return _easy_answer[randrange(len(_easy_answer))]

def contestame(comment,delta=0.1):
    _counter = 0
    if comment.endswith('?') and random() > 0.8:
        return easy_answer()
    n = magic(comment)
    words = filter(lambda x:len(x)>3,sorted(comment.split(),cmp=lambda x,y:cmp(len(x),len(y))))
    fetchs = []
    while not fetchs:
        _counter += 1
        r = random()
        print r,_counter
        if r < 0.9 and words:
            i = randrange(len(words))
            word = words[i]
            word.strip(u'?!¿¡')
            while len(word) > 3 and not fetchs:
                print word
                for j in range(1,10):
                    delta = delta + j/10.0
                    fetchs = cursor.execute('select txt from logs where magic > ? and magic < ? and txt like ?',(n-delta,n+delta,'%%%s%%' % word)).fetchall()
                word = word[:-1]
            words.pop(i)
        else:
            print 'salgo por random'
            delta += 0.05
            fetchs = cursor.execute('select txt from logs where magic > ? and magic < ? ',(n-delta,n+delta)).fetchall()
    msg = fetchs[randrange(len(fetchs))][0]
    if msg.lower() == comment.lower():
        if random() > 0.5:
            msg = '%s%s %s' % (repeating(),':,'[randrange(2)],msg)
    return msg
