from zipfile import ZipFile
import os
from os import path
import sys
sys.path.append(path.dirname( path.dirname( path.dirname( path.dirname( path.abspath(__file__) ) ) )))
from speech.utils import misc
from speech.utils import constants
import time
import psycopg2

wavs_transferred = 0
scripts_processed = 0
wavs_db = 0

def read_lines(file_path):
    """reads all the files from a file"""
    lines = []
    dictionary = {}
    global scripts_processed
    with open(file_path) as fp:
        lines = fp.readlines()
    for line in lines:
        if len(line.strip().split('\t'))==2:
            file_name = line.strip().split('\t')[0].replace(u'\ufeff', '')
            transcription = line.strip().split('\t')[1]
            dictionary[file_name+'.WAV'] = transcription
            scripts_processed += 1
    return dictionary

def make_chunk_entry(lines, wav_path, wav_file_name, cur, conn):
    file_size = os.stat(wav_path).st_size
    #print(lines)
    #print(wav_file_name)
    global wavs_db
    sql = 'INSERT INTO public.chunks (file_name, abs_path, transcription, url, created_at, updated_at, file_size, is_verified, is_seen, "source") VALUES(\'' + wav_file_name + '\', \'' + wav_path + '\', \'' + lines[wav_file_name].replace('\'', '\'\'') + '\', NULL, now(), now(), ' + str(file_size) + ', false, false, \'CHINA\');'
    try:
        #print(sql)
        cur.execute(sql)
        conn.commit()
        wavs_db += 1
    except Exception as e:
        print(e)


def main():
    """"This method will create entries in chunks table for all the audio snippets provided by the chinese guy"""
    chunk_folder_path = '/home/absin/Documents/dev/sentenceSimilarity/speech/transcription/transfer_learning/chunks'
    zip_file_path = "/home/absin/Downloads/china/King-ASR-071.zip"
    zip_extract_dir = os.path.dirname(zip_file_path)
    start = time.time()
    global wavs_transferred
    try:
        conn = psycopg2.connect("dbname='sales' user='postgres' host='"+constants.fetch_contant_single('host')+"' password='"+constants.fetch_contant_single('password')+"'")
    except Exception as e:
        #print('Establishing connection with db failed')
        print(e)
    print("Connection established successsfully after: "+str(time.time()-start))
    cur = conn.cursor()
    with ZipFile(zip_file_path, 'r') as zipObj:
        zip_dir_path = zipObj.extractall(zip_extract_dir)
    print(zip_dir_path)
    channels = ['/home/absin/Downloads/china/King-ASR-071/DATA/CHANNEL0', '/home/absin/Downloads/china/King-ASR-071/DATA/CHANNEL1', '/home/absin/Downloads/china/King-ASR-071/DATA/CHANNEL2']
    lines = {}
    for channel in channels:
        lines = {}
        for script_file in os.listdir(channel+'/SCRIPT'):
            curr_lines = read_lines(channel+'/SCRIPT/'+script_file)
            print('In script file: '+channel+'/SCRIPT/'+script_file+'read a total of -->'+str(len(curr_lines))+'lines')
            print('before-->'+str(len(lines)))
            lines.update(curr_lines)
            print('after-->'+str(len(lines)))

        for speaker_folder in os.listdir(channel+'/WAVE'):
            for session_folder in os.listdir(channel+'/WAVE/'+speaker_folder):
                for wav_file in os.listdir(channel+'/WAVE/'+speaker_folder+'/'+session_folder):
                    misc.copy_files(channel+'/WAVE/'+speaker_folder+'/'+session_folder+'/'+wav_file, chunk_folder_path)
                    wavs_transferred += 1
                    make_chunk_entry(lines, channel+'/WAVE/'+speaker_folder+'/'+session_folder+'/'+wav_file, wav_file, cur, conn)
        print('Done channel --> '+channel)
    print('wavs_transferred-->'+str(wavs_transferred))
    print('scripts_processed-->'+str(scripts_processed))
    print('wavs_db-->'+str(wavs_db))

if __name__ == '__main__':
    main()
