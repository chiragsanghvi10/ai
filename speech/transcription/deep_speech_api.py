# This is the python client for deepspeech
# Most of the code has been generously borrowed from https://github.com/mozilla/DeepSpeech/blob/master/native_client/python/client.py
from deepspeech import Model, printVersions
import time
import wave
import numpy as np
import shlex
import subprocess
try:
    from shhlex import quote
except ImportError:
    from pipes import quote


import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from utils import objects
from utils import constants

# These constants control the beam search decoder
# Beam width used in the CTC decoder when building candidate transcriptions
BEAM_WIDTH = 500
# The alpha hyperparameter of the CTC decoder. Language Model weight
LM_ALPHA = 0.75
# The beta hyperparameter of the CTC decoder. Word insertion bonus.
LM_BETA = 1.85
# These constants are tied to the shape of the graph used (changing them changes
# the geometry of the first layer), so make sure you use the same constants that
# were used during training
# Number of MFCC features to use
N_FEATURES = 26
# Size of the context window used for producing timesteps in the input vector
N_CONTEXT = 9
def convert_samplerate(audio_path):
    sox_cmd = 'sox {} --type raw --bits 16 --channels 1 --rate 16000 --encoding signed-integer --endian little --compression 0.0 --no-dither - '.format(quote(audio_path))
    try:
        output = subprocess.check_output(shlex.split(sox_cmd), stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('SoX returned non-zero status: {}'.format(e.stderr))
    except OSError as e:
        raise OSError(e.errno, 'SoX not found, use 16kHz files or install it: {}'.format(e.strerror))
    return 16000, np.frombuffer(output, np.int16)

def main(use_lm, audio_path):
    start = time.time()
    conversation_blocks = []
    model_path = constants.fetch_contant('deepspeech', 'model_path')
    alphabet_path = constants.fetch_contant('deepspeech', 'alphabet_path')
    print('Loading model from file {}'.format(model_path), file=sys.stderr)
    ds = Model(model_path, N_FEATURES, N_CONTEXT, alphabet_path, BEAM_WIDTH)
    print('Loaded accoustic model after: '+str((time.time())-start), file=sys.stderr)
    if use_lm:
        lm_path = constants.fetch_contant('deepspeech', 'lm_path')
        trie_path = constants.fetch_contant('deepspeech', 'trie_path')
        print('Loading language model from files {} {}'.format(lm_path, trie_path), file=sys.stderr)
        ds.enableDecoderWithLM(alphabet_path, lm_path, trie_path, LM_ALPHA, LM_BETA)
        print('Loaded language model after: '+str((time.time())-start), file=sys.stderr)
    fin = wave.open(audio_path, 'rb')
    fs = fin.getframerate()
    if fs != 16000:
        print('Warning: original sample rate ({}) is different than 16kHz. Resampling might produce erratic speech recognition.'.format(fs), file=sys.stderr)
        fs, audio = convert_samplerate(audio_path)
    else:
        audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)
    audio_length = fin.getnframes() * (1/16000)
    fin.close()
    print('Running inference.', file=sys.stderr)
    transcription = ds.stt(audio, fs)
    print('Inference finished after: '+str((time.time())-start), file=sys.stderr)
    return transcription

if __name__ == '__main__':
    print(main(use_lm, audio_path))
