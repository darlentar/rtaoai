import base64
import io
from pydub import AudioSegment


def audio_to_item_create_event(audio_bytes: bytes) -> str:
    # Load the audio file from the byte stream
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))

    # Resample to 24kHz mono pcm16
    pcm_audio = audio.set_frame_rate(24000).set_channels(1).set_sample_width(2).raw_data

    # Encode to base64 string
    return base64.b64encode(pcm_audio).decode()
