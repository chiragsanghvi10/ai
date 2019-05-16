import csv
import requests
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

warnings.simplefilter('ignore',InsecureRequestWarning)

CSV_PATH = '/home/absin/Downloads/oyo/talentify_Export_ACD_Logger_Data2019_04_23_19_22_09.csv'

def check_url(url):
    url_works = False
    try:
        r = requests.head(url,verify=False)
        #print(r.status_code)
        if r.status_code == 200:
            url_works = True
    except requests.ConnectionError as e:
        #print("failed to connect -->"+str(url)+str(e))
        url_works = False
    #print('trying --> '+url+' --> '+str(url_works))
    return url_works

def check_url_mult(url, iter):
    url_works = False
    for i in range(1, iter+1):
        url_works = check_url(url)
        if not url_works:
            url_works = check_url(url)
        else:
            break
    return url_works

def find_right_url(row, line_count):
    right_url = None
    try:
        path = str(row[7]).replace('/var/spool/asterisk/','')
        file_name = str(row[8])
        node_index = 0
        success = False
        #nodes = [41, 42, 48, 51, 52, 87, 91, 95, 96]
        nodes = range(41, 100)
        while not success:
            url = 'https://115.249.54.19/logger/node_logger_'+str(nodes[node_index])+'/' + path  + file_name
            if not check_url_mult(url, 5):
                url = url.replace('.mp3','.wav')
                if not check_url_mult(url, 5):
                    node_index += 1
                else:
                    success = True
                    right_url = url
            else:
                success = True
                right_url = url
            if node_index>=len(nodes):
                print(str(line_count)+' ---> '+url+' --> '+str(check_url_mult(url, 1)))
                break
    except Exception as e:
        print(e)
    return right_url

def download_file(url, folder):
    success = False
    local_filename = url.split('/')[-1]
    if not os.path.exists(folder):
        os.makedirs(folder)
    page = "a"
    if os.path.exists(folder + local_filename):
        page = None
        print('Already exists skipping downloading file ' + local_filename + ' ... to '+folder)
    else:
        print('Downloading file ' + local_filename + ' ... to '+folder)

    while page == "a":
        try:
            with requests.get(url, stream=True, verify=False) as r:
                page = r
                r.raise_for_status()
                with open(folder + local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            # filter out keep-alive new chunks
                            f.write(chunk)
                            # f.flush()
            break
        except:
            print(" while downloading "+url+", Connection refused by the server.. gonna sleep for 5 seconds and then retry ZZzzzz...")
            time.sleep(5)
            continue
    if os.path.exists(folder + local_filename):
        print("Successfully downloaded "+local_filename + " from url: "+url+" to folder: "+folder)
        success = True
    else:
        print("Failed to download "+local_filename + " from url: "+url+" to folder: "+folder)
    return {"abs_path": folder + local_filename, "success": success}

def threadable(row, line_count, folder):
    url  = find_right_url(row, line_count)
    if url:
        return download_file(url,folder)
    else:
        return {"success": False}


def main_action():
    tried = 0
    success = 0
    folder = '/home/absin/Downloads/oyo/2019_04_23/'
    futures = []
    with open(CSV_PATH) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        with ThreadPoolExecutor(max_workers=500) as executor:
            for row in csv_reader:
                if line_count >= 3:
                    if os.path.exists(folder + str(row[8])):
                        success += 1
                        print('Already exists, so skipping file ' + str(row[8]) + ' ... to '+folder)
                    else:
                        tried+=1
                        try:
                            futures.append(executor.submit(threadable, row , line_count,folder))
                        except Exception as e:
                            print(e)
                line_count +=1
    for future in futures:
        try:
            download_result = future.result(timeout=20)
            if download_result["success"]:
                success += 1
        except Exception as e:
            print(e)
        print('Finished: '+str(success/len(futures)*100.0))
    print(f'Processed {line_count} lines.')
    print(f'Tried {tried} lines.')
    print(f'Scueeded {success} lines.')

main_action()
#print(check_url('https://115.249.54.19/logger/node_logger_43/monitor_0/450549-1/2019_04_22/meetme_conf_rec_450549-1_1555918669_433777_1555919024_43729.wav'))
