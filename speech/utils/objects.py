class Frame(object):
    """Represents a "frame" of audio data."""
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration

class Snippet(object):
    """Represents a snippet of the audio file post performing vad."""
    def __init__(self, path, from_time, to_time):
        self.path = path
        self.from_time = from_time
        self.to_time = to_time
        self.responses = []
        self.signals = []
    def add_signal(self , signal):
        self.signals.append(signal)
    def add_transcription(self, responses):
        self.responses = responses
    def set_speaker(self, speaker):
        self.speaker = speaker


class ConversationBlock(object):
    """Represents a conversation block specific to a speaker, the base of the analysis object"""
    def __init__(self, from_time, to_time, speaker, text, confidence):
        self.speaker = speaker
        self.from_time = from_time
        self.to_time = to_time
        self.text = text
        self.confidence = confidence
        self.signals = []
        self.words = []

    def add_signal(self , signal):
        self.signals.append(signal)

    def add_signals(self , signals):
        self.signals.extend(signals)

    def add_word(self , word):
        self.words.append(word)

    def add_words(self , words):
        self.words.extend(words)

    def set_from_time(self, from_time):
        self.from_time = from_time

class Signal(object):
    """Represents the signals which can be textual or voice based like emotion"""
    def __init__(self, name, value):
        self.value = value
        self.name = name
