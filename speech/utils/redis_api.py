import redis
from datetime import datetime
# The interface provides 2 methods:
# Adding a new request with time at which its called to the redis
# Checking how many requests have been made in the last minute

def add_entry(pool):
    r = redis.Redis(connection_pool=pool)
    key = datetime.now().strftime('%Y-%m-%d %H:%M')
    r.set(key, check_entries(pool) + 1)

def check_entries(pool):
    r = redis.Redis(connection_pool=pool)
    key = datetime.now().strftime('%Y-%m-%d %H:%M')
    if not r.get(key):
        r.set(key, '1')
    return int(r.get(key).decode("utf-8"))

if __name__ == '__main__':
    pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
    add_entry(pool)
    print(check_entries(pool))
