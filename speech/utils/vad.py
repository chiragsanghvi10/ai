import os, sys
from os import path
import wave
import contextlib
import webrtcvad
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from utils import objects


"""Writes a .wav file.

Takes the path, and frames and writes the frame data to the path file.
"""
def write_wave(path, frames, sample_rate):
    wav_file=wave.open(path,"w")
    nchannels = 1
    sampwidth = 2
    nframes = len(frames)
    comptype = "NONE"
    compname = "not compressed"
    wav_file.setparams((nchannels, sampwidth, sample_rate, nframes, comptype, compname))
    wav_file.writeframes(b''.join(frames))
    wav_file.close()
    #print('Created chunk file at: '+path)
"""Reads a .wav file.

Takes the path, and returns (PCM audio data, sample rate).
"""
def read_wave(path):
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        assert num_channels == 1
        sample_width = wf.getsampwidth()
        assert sample_width == 2
        sample_rate = wf.getframerate()
        assert sample_rate in (8000, 16000, 32000)
        frames = wf.getnframes()
        pcm_data = wf.readframes(frames)
        duration = frames / sample_rate
        return pcm_data, sample_rate, duration

def perform_vad(file_path, chunk_folder_path, min_chunk_length = 2.5, max_chunk_length = 3.0):
    snippets = []
    print('Processing '+ file_path+' for voice activity detection...')
    if os.path.isdir(chunk_folder_path) is False:
        print('Creating chunk folder at: '+chunk_folder_path)
        os.makedirs(chunk_folder_path)
    aggressiveness = 2
    directory = os.fsencode(chunk_folder_path)
    fileName = os.path.basename(file_path).replace('.wav','')
    vad = webrtcvad.Vad(aggressiveness)
    chunk_count = 0
    accumulated_frames = []
    audio, sample_rate, audio_length = read_wave(file_path)
    assert sample_rate == 8000, "Only 8000Hz input WAV files are supported for now!"
    frame_duration_ms = 30
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    chunk_from = 0.0
    chunk_to = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        frame = objects.Frame(audio[offset:offset + n], timestamp, duration)
        is_speech = vad.is_speech(frame.bytes, sample_rate)
        if(is_speech):
            accumulated_frames.append(audio[offset:offset + n])
            if(chunk_from == chunk_to):
                chunk_from = offset/len(audio)*audio_length
            chunk_to = (offset+n)/len(audio)*audio_length
            if(len(accumulated_frames)>0):
                if(chunk_to - chunk_from>max_chunk_length):
                    chunk_file_path = chunk_folder_path+fileName+"_{:03}".format(chunk_count)+'.wav'
                    write_wave(chunk_file_path,accumulated_frames,sample_rate)
                    snippets.append(objects.Snippet(chunk_file_path, chunk_from, chunk_to))
                    print('Creating chunk from: '+ str(chunk_from)  +'to: '+ str(chunk_to) +': '+ chunk_file_path)
                    chunk_count = chunk_count + 1
                    accumulated_frames = []
                    chunk_from = chunk_to
        else:
            if(len(accumulated_frames)>0):
                if(chunk_to - chunk_from>min_chunk_length):
                    chunk_file_path = chunk_folder_path+fileName+"_{:03}".format(chunk_count)+'.wav'
                    write_wave(chunk_file_path,accumulated_frames,sample_rate)
                    snippets.append(objects.Snippet(chunk_file_path, chunk_from, chunk_to))
                    print('Creating chunk from: '+ str(chunk_from)  +'to: '+ str(chunk_to) +': '+ chunk_file_path)
                    chunk_count = chunk_count + 1
                accumulated_frames = []
                chunk_from = chunk_to
        timestamp += duration
        offset += n
    return snippets


if __name__=='__main__':
        perform_vad('/home/absin/Downloads/17916689.wav', '/home/absin/Downloads/17916689/', 0.5, 3.0)
