import asyncio
import os
import types
import httpx
import requests
import time

from realtime_ai_character.logger import get_logger
from realtime_ai_character.utils import Singleton
from realtime_ai_character.audio.text_to_speech.base import TextToSpeech

logger = get_logger(__name__)
DEBUG = False

config = types.SimpleNamespace(**{
    'chunk_size': 1024,
    'url': 'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream',
    'headers': {
        'Accept': 'audio/mpeg',
        'Content-Type': 'application/json',
        'xi-api-key': os.environ['ELEVEN_LABS_API_KEY']
    },
    'data': {
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }
})

# https://lab.api.unrealspeech.com/stream?speaker_index=0&text=


async def get_audio_from_unreal_speech(text="To grow rapidly, you need to make something you can sell to a big market. That's the difference between Google and a barbershop. A barbershop doesn't scale."):
    url = "https://lab.api.unrealspeech.com/stream"
    params = {
        "text": text,
        "speaker_index": 5
    }

    # start_time = time.time()
    response = await requests.get(url, params=params, stream=True)

    # if response.status_code == 200:
    for chunk in response.iter_content(chunk_size=1024):
        print(chunk)
        # process the 1024-byte 'chunk'
    #         print(chunk)
    #         print("Received chunk of audio", time.time() - start_time)
    #     # you can write chunk to a file, or process it here as needed
    # else:
    #     print("Error occurred. Status code:", response.status_code)

    # print(f"\nTime taken: {(time.time() - start_time):.2f} seconds")


class ElevenLabs(Singleton, TextToSpeech):
    def __init__(self):
        super().__init__()
        logger.info("Initializing [ElevenLabs Text To Speech] voices...")

    async def stream(self, text, websocket, tts_event: asyncio.Event, voice_id="21m00Tcm4TlvDq8ikWAM",
                     first_sentence=False, language='en-US') -> None:
        if DEBUG:
            return
        if voice_id == "":
            logger.info(
                f"voice_id is not found in .env file, using ElevenLabs default voice")
            voice_id = "21m00Tcm4TlvDq8ikWAM"
        headers = config.headers
        if language != 'en-US':
            config.data["model_id"] = 'eleven_multilingual_v1'
        data = {
            "text": text,
            **config.data,
        }
        url = config.url.format(voice_id=voice_id)
        if first_sentence:
            url = url + '?optimize_streaming_latency=4'
        async with httpx.AsyncClient() as client:
            url = "https://lab.api.unrealspeech.com/stream"
            params = {
                "text": text,
                "speaker_index": 5
            }
            # response = await client.post(url, json=data, headers=headers)
            response = await client.get(url, params=params)
            if response.status_code != 200:
                logger.error(
                    f"ElevenLabs returns response {response.status_code}")
            async for chunk in response.aiter_bytes():
                await asyncio.sleep(0.1)
                if tts_event.is_set():
                    # stop streaming audio
                    break
                await websocket.send_bytes(chunk)
