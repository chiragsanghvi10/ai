import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from utils import vad
from utils import misc
from utils import objects
from utils import redis_api
import contextlib
import shutil
import wave
from transcription import google_transcribe
from transcription import deep_speech_api
import pdb
import jsonpickle
from emotion import emotion_api
import requests
import json
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import psycopg2
requests.adapters.DEFAULT_RETRIES = 50

def append_phrases(phrases, product_id):
    sql = 'select * from product_signal where product_id  ='+product_id+' and is_active = true;'
    con = None
    try:
        con = psycopg2.connect("host='db.talentify.in' dbname='sales' user='postgres' password='cx6ac54nmgGtLD1y'")
        cur = con.cursor()
        cur.execute(sql)
        while True:
            row = cur.fetchone()
            if row == None:
                break
            phrases.append(row[3])
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()

        print(e)
        sys.exit(1)

    finally:
        if con:
            con.close()
    return phrases

def transcribe_emotion(engine, task_id, language, model, loaded_model, pool, do_emotion = True):
    phrases=[]
    try:
        append_phrases(phrases, task_id)
    except:
        print('Fetching speech context failed for: '+task_id)
    task_folder = '/home/absin/git/sentenceSimilarity/speech/audio/tasks/'
    task_file_path = misc.download_file(
        'https://storage.googleapis.com/istar-static/'+task_id+'.wav', task_folder)['abs_path']
    channel_files = [task_file_path]
    # split multichannel to 2 files
    with contextlib.closing(wave.open(task_file_path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        if num_channels == 2:
            channel_files = misc.split_stereo(task_file_path)
    snippets = []
    for channel_file in channel_files:
        snippets.extend(vad.perform_vad(
            channel_file, task_folder + 'chunks/', min_chunk_length=1, max_chunk_length=50))
    print('For task: '+task_id+', total chunks produced -->'+str(len(snippets)))
    conversation_blocks = []

    if engine == 'google':
        transcription_futures = []
        with ThreadPoolExecutor(max_workers=50) as executor:
            for snippet in snippets:
                #print('Transcribing: ' + snippet.path)
                speaker = 'Customer'
                if task_id + '_1' in snippet.path:
                    speaker = 'Agent'
                rate_check_pass = False
                while redis_api.check_entries(pool) > 200:
                    time.sleep(61)
                    print("Sleeping for 61 seconds while processing: "+task_id)
                try:
                    transcription_futures.append(executor.submit(google_transcribe.transcribe_streaming, snippet, speaker, language, model, phrases))
                except:
                    print('Failed for snippet: '+snippet.path)
                redis_api.add_entry(pool)
        for transcription_future in transcription_futures:
            try:
                convs = transcription_future.result(timeout=10)
                conversation_blocks.extend(convs)
            except Exception as exc:
                print(exc)
        conversation_blocks.sort(key=lambda x: x.from_time, reverse=False)

    elif engine == 'deepspeech':
        for snippet in snippets:
            speaker = 'Customer'
            if task_id + '_1' in snippet.path:
                speaker = 'Agent'
            transcript = deep_speech_api.main(True, snippet.path)
            conversation_block = objects.ConversationBlock(snippet.from_time , snippet.to_time, speaker, transcript, 1)
            conversation_blocks.append(conversation_block)
        conversation_blocks.sort(key=lambda x: x.from_time, reverse=False)

    if do_emotion:
        # Now the emotional bit
        #loaded_model = emotion_api.getModel()
        #loaded_model._make_predict_function()
        snips = emotion_api.emotion(channel_files, loaded_model, task_folder, task_id)
        # empty chunks foilder
        shutil.rmtree(task_folder + task_id, ignore_errors=True)
        for emotion_snip in snips:
            emotion_snippet_located = False
            for conv in conversation_blocks:
                if conv.from_time <= emotion_snip.from_time and conv.to_time >= emotion_snip.to_time:
                    conv.add_signals(emotion_snip.signals)
                    emotion_snippet_located = True
            if emotion_snippet_located is False:
                print("Emotion snippet from " + str(emotion_snip.from_time) + " to: "
    						+ str(emotion_snip.to_time) + " not found")
    #print(jsonpickle.encode(conversation_blocks))
    return conversation_blocks

def emotion(task_id, loaded_model):
    task_folder = '/home/absin/git/sentenceSimilarity/speech/audio/tasks/'
    task_file_path = misc.download_file(
        'https://storage.googleapis.com/istar-static/'+task_id+'.wav', task_folder)['abs_path']
    channel_files = [task_file_path]
    # split multichannel to 2 files
    with contextlib.closing(wave.open(task_file_path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        if num_channels == 2:
            channel_files = misc.split_stereo(task_file_path)
    snips = emotion_api.emotion(channel_files, loaded_model, task_folder, task_id)
    #print(snips)
    # empty chunks foilder
    shutil.rmtree(task_folder + task_id, ignore_errors=True)
    return snips

if __name__ == '__main__':
    task_id = '17906567'
    language = 'en-US'
    model = True
