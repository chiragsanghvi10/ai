import io
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from utils import vad
from utils import misc
from utils import objects
import time

# [START speech_transcribe_streaming]
def transcribe_streaming(snippet, speaker, language, model, phrases):
    start = time.time()
    print('Started transcription of file: '+str(snippet.path))
    """Streams transcription of the given audio file."""
    from google.cloud import speech
    from google.cloud.speech import enums
    from google.cloud.speech import types
    client = speech.SpeechClient()

    # [START speech_python_migration_streaming_request]
    with io.open(snippet.path, 'rb') as audio_file:
        content = audio_file.read()

    # In practice, stream should be a generator yielding chunks of audio data.
    stream = [content]
    requests = (types.StreamingRecognizeRequest(audio_content=chunk)
                for chunk in stream)

    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=8000,
        language_code=language,
        # Enhanced models are only available to projects that
        # opt in for audio data collection.
        use_enhanced=True,
        # A model must be specified to use enhanced model.
        model='video',
        enable_word_time_offsets=True,
        enable_automatic_punctuation=True,
        speech_contexts=[speech.types.SpeechContext(phrases=phrases)])
    if not model:
        config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=8000,
        language_code=language,
        enable_word_time_offsets=True,
        enable_automatic_punctuation=True,
        speech_contexts=[speech.types.SpeechContext(phrases=phrases)])
    streaming_config = types.StreamingRecognitionConfig(config=config)
    delta = 0
    multiple_results = False
    # streaming_recognize returns a generator.
    # [START speech_python_migration_streaming_response]
    responses = client.streaming_recognize(streaming_config, requests)
    # [END speech_python_migration_streaming_request]
    conversation_blocks = []
    for response in responses:
        if len(response.results)>1:
            multiple_results = True
        for result in response.results:
            alternatives = result.alternatives
            for alternative in alternatives:
                #print(alternative.transcript+"-->>")
                conversation_block = objects.ConversationBlock(snippet.from_time , snippet.to_time, speaker, alternative.transcript, alternative.confidence)
                for word_info in alternative.words:
                    word = word_info.word
                    start_time = word_info.start_time
                    end_time = word_info.end_time
                    word = objects.ConversationBlock(snippet.from_time + word_info.start_time.seconds + word_info.start_time.nanos * 1e-9,
                        snippet.from_time + word_info.end_time.seconds + word_info.end_time.nanos * 1e-9, speaker, word, alternative.confidence)
                    delta = word_info.start_time.seconds + word_info.start_time.nanos * 1e-9
                    conversation_block.add_word(word)
                if multiple_results:
                    print('For snippet: '+snippet.path + ' multiple conversation blocks received')
                    conversation_block.set_from_time(snippet.from_time + delta)
            conversation_blocks.append(conversation_block)
    print('Finished transcription of: '+str(snippet.path)+' after: '+str((time.time())-start))
    return conversation_blocks
    # [END speech_python_migration_streaming_response]
# [END speech_transcribe_streaming]
