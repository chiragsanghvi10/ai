import psycopg2
import time
import sys
from os import path
sys.path.append(path.dirname( path.dirname( path.dirname( path.dirname( path.abspath(__file__) ) ) )))
from speech.utils import constants

def fetch_chunks(page, pagination):
    print(pagination)
    start = time.time()
    host  = constants.fetch_contant_single('host')
    password  = constants.fetch_contant_single('password')
    try:
        conn = psycopg2.connect("dbname='sales' user='postgres' host='"+host+"' password='"+password+"'")
    except:
        print('Establishing connection with db failed')
    print("Connection established successsfully after: "+str(time.time()-start))
    cur = conn.cursor()
    sql = 'select * from chunks where is_verified != true and is_seen = false and file_size>30000 order by random() limit '+str(pagination)+' offset ' + str(int(page)*int(pagination))
    print(sql)
    try:
        cur.execute(sql)
    except:
        print("Query fetch failed")
    rows = cur.fetchall()
    chunks = []
    for row in rows:
        chunk = {"id":row[0], "url": "/audio/"+row[1], "transcription": row[3], "is_verified": row[8], "is_seen":row[9]}
        chunks.append(chunk)
    return chunks

def fetch_chunk(chunk_id):
    start = time.time()
    host  = constants.fetch_contant_single('host')
    password  = constants.fetch_contant_single('password')
    try:
        conn = psycopg2.connect("dbname='sales' user='postgres' host='"+host+"' password='"+password+"'")
    except:
        print('Establishing connection with db failed')
    print("Connection established successsfully after: "+str(time.time()-start))
    cur = conn.cursor()
    sql = 'select * from chunks where id =  ' + chunk_id
    try:
        cur.execute(sql)
    except:
        print("Query fetch failed")
    rows = cur.fetchall()
    chunks = []
    for row in rows:
        print(row[9])
        chunk = {"id":row[0], "url": "/audio/"+row[1], "transcription": row[3], "is_verified": row[8], "is_seen":row[9]}
        chunks.append(chunk)
    return chunks

def mark_chunk_as_verified(chunk_id, is_verified):
    start = time.time()
    host  = constants.fetch_contant_single('host')
    password  = constants.fetch_contant_single('password')
    try:
        conn = psycopg2.connect("dbname='sales' user='postgres' host='"+host+"' password='"+password+"'")
    except:
        print('Establishing connection with db failed')
    print("Connection established successsfully after: "+str(time.time()-start))
    cur = conn.cursor()
    sql = 'update chunks set is_verified = true, updated_at = now() where id = '+str(chunk_id)
    if not is_verified:
        sql = 'update chunks set is_verified = false, updated_at = now() where id = '+str(chunk_id)
    try:
        cur.execute(sql)
        conn.commit()
    except Exception as e:
        print(e)
    return fetch_chunk(chunk_id)

def update_chunk_transcription(chunk_id, transcript):
    start = time.time()
    host  = constants.fetch_contant_single('host')
    password  = constants.fetch_contant_single('password')
    try:
        conn = psycopg2.connect("dbname='sales' user='postgres' host='"+host+"' password='"+password+"'")
    except:
        print('Establishing connection with db failed')
    print("Connection established successsfully after: "+str(time.time()-start))
    cur = conn.cursor()
    sql = "update chunks set transcription = '"+transcript+"', updated_at = now() where id = "+str(chunk_id)
    try:
        cur.execute(sql)
        conn.commit()
    except:
        print("Query fetch failed")
    return fetch_chunk(chunk_id)

def mark_chunk_as_seen(chunk_id):
    start = time.time()
    host  = constants.fetch_contant_single('host')
    password  = constants.fetch_contant_single('password')
    try:
        conn = psycopg2.connect("dbname='sales' user='postgres' host='"+host+"' password='"+password+"'")
    except:
        print('Establishing connection with db failed')
    print("Connection established successsfully after: "+str(time.time()-start))
    cur = conn.cursor()
    sql = 'update chunks set is_seen = true, updated_at = now() where id = '+str(chunk_id)
    try:
        cur.execute(sql)
        conn.commit()
    except Exception as e:
        print(e)
    return fetch_chunk(chunk_id)

def fetch_verified_chunks(count, page):
    data = []
    sql = 'select * from chunks where is_verified = true order by id offset '+str((page - 1)*count)+' limit '+str(count)
    con = None
    try:
        host  = constants.fetch_contant_single('host')
        password  = constants.fetch_contant_single('password')
        conn = psycopg2.connect("dbname='sales' user='postgres' host='"+host+"' password='"+password+"'")
        cur = conn.cursor()
        cur.execute(sql)
        while True:
            row = cur.fetchone()
            if row == None:
                break
            print("ID: " + str(row[0]) + "\t\tTranscript: " + str(row[3]) + r'\t\Url:' + 'http://35.192.138.16/audio/'+str(row[1]))
            data.append({'id': row[0], 'transcript': row[3], 'url': 'http://192.168.0.102:5010/audio/'+str(row[1]), 'abs_path': row[2], 'file_size': row[7]})
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()
        print(e)
        raise
    finally:
        if con:
            con.close()
    return data
