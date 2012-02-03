import sys
import sqlite3
from collections import namedtuple

conn = sqlite3.connect("wnjpn-0.9.db")

def is_exist_word(word):
    result = conn.execute("select * from word where lemma=?", (word))
    if result.length > 1:
        return True
    return False


