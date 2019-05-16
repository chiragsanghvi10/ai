import psycopg2
import time
import requests
import os
import sys
from os import path
sys.path.append( path.dirname(( path.dirname( path.dirname( path.abspath(__file__) ) ) )))
from utils import misc
from utils import constants
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import contextlib
import wave

def download_split_task(file_name, stereo_folder, mono_folder):
    url = 'https://storage.googleapis.com/istar-static/' + file_name
    download_result = misc.download_file(url, stereo_folder)
    if download_result["success"]:
        channel_files = [download_result["abs_path"]]
        # split multichannel to 2 files
        with contextlib.closing(wave.open(download_result["abs_path"], 'rb')) as wf:
            num_channels = wf.getnchannels()
            if num_channels == 2:
                channel_files = misc.split_stereo(download_result["abs_path"], mono_folder)
    else :
        channel_files = []
    return {"abs_path": channel_files, "success": download_result["success"]}

"""Fetches all the calls made by ECC using sql connects with the system, takes the SQL host and password from the command line:"""
def main():
    downloaded_task_count = 0
    stereo_folder = "/home/absin/Documents/dev/sentenceSimilarity/speech/transcription/transfer_learning/calls_dual/"
    mono_folder = "/home/absin/Documents/dev/sentenceSimilarity/speech/transcription/transfer_learning/calls/"
    misc.reset_folders([stereo_folder, mono_folder])
    host = input("Enter host: ")
    password = input("Enter password: ")
    start = time.time()
    sql = 'select * from task where actor in (select org_user.userid from org_user where org_user.organizationid = 67) limit 10'
    try:
        conn = psycopg2.connect("dbname='sales' user='postgres' host='"+host+"' password='"+password+"'")
        print("Database Connection established successsfully after: "+str(time.time()-start))
    except:
        print('Establishing connection with db failed')
        raise
    cur = conn.cursor()
    try:
        cur.execute(sql)
    except:
        print("Query fetch failed")
        raise
    rows = cur.fetchall()
    print("Fetched "+str(len(rows))+" tasks after: "+str(time.time()-start))
    futures = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        for row in rows:
            file_name = str(row[0])+'.wav'
            futures.append(executor.submit(download_split_task, file_name, stereo_folder, mono_folder))

    for future in futures:
        try:
            download_result = future.result(timeout=10)
            if download_result["success"]:
                downloaded_task_count += len(download_result["abs_path"])
        except Exception as e:
            print(e)
    print("Total calls downloaded: "+str(downloaded_task_count))

if __name__ == '__main__':
    main()
