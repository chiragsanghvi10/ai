import os
import sys
from os import path
sys.path.append( path.dirname(path.dirname( path.dirname( path.abspath(__file__) ) ) ) )
from utils import vad
from utils import misc
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

def main():
    """Performs Voice Activity detection and chunks the audio files into chunks which are stored in a specified folder  """
    chunk_folder_path = "/home/absin/Documents/dev/sentenceSimilarity/speech/transcription/transfer_learning/chunks/"
    source_folder_path = "/home/absin/Documents/dev/sentenceSimilarity/speech/transcription/transfer_learning/calls/"
    misc.reset_folders([chunk_folder_path])
    call_paths = os.listdir(source_folder_path)
    print("Going to chunk "+str(len(call_paths)) + " calls for vad")
    vad_futures = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        for call_path in call_paths:
            if call_path.endswith('.wav'):
                vad_futures.append(executor.submit(vad.perform_vad, source_folder_path + call_path, chunk_folder_path, 5, 10.0))
            else:
                print('Skipping vad on '+call_path)
    for vad_future in vad_futures:
        try:
            vad_result = vad_future.result(timeout=10)
        except Exception as e:
            print(e)

if __name__ == '__main__':
    main()
