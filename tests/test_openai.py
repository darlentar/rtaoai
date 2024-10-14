import os
import json
import pytest
from pathlib import Path

from rtaoai.openai.events import (
    ConversationItemCreate,
    AudioTranscriptDelta,
    AudioTranscriptDone,
    AudioDelta,
    AudioDone,
)
from rtaoai.openai.processors import FakeOpenAI, EventHandler


def load_scenario(scenario_name: str) -> list[str]:
    steps = []
    scneario_dir = Path(__file__).resolve().parent / Path(f"scenarios/{scenario_name}")
    files = os.listdir(scneario_dir)
    for f in sorted(files, key=lambda f: f):
        with open(scneario_dir / f) as file:
            steps.append(json.load(file))
    return steps


@pytest.mark.asyncio
async def test_opanai_on_item_create():
    scenario = load_scenario("ask_order")
    received_items = []

    async def on_item_created(item: ConversationItemCreate):
        received_items.append(item.item.id)

    openai = FakeOpenAI(
        events=scenario,
        event_handler=EventHandler(on_item_created=on_item_created),
    )
    await openai.run()

    assert received_items == [
        "item_AIK0wpoIes7XyDYXRDYu4",
        "item_AIK0wRecrZqZlLV2oUVja",
    ]


@pytest.mark.asyncio
async def test_opanai_on_transcript_delta():
    scenario = load_scenario("ask_order")
    received_items = []

    async def on_transcript_delta(delta: AudioTranscriptDelta):
        received_items.append((delta.item_id, delta.delta))

    openai = FakeOpenAI(
        events=scenario,
        event_handler=EventHandler(on_transcript_delta=on_transcript_delta),
    )
    await openai.run()

    assert len(received_items) == 21
    assert received_items[:5] == [
        (
            "item_AIK0wRecrZqZlLV2oUVja",
            "I",
        ),
        (
            "item_AIK0wRecrZqZlLV2oUVja",
            " can",
        ),
        (
            "item_AIK0wRecrZqZlLV2oUVja",
            " help",
        ),
        (
            "item_AIK0wRecrZqZlLV2oUVja",
            " with",
        ),
        (
            "item_AIK0wRecrZqZlLV2oUVja",
            " that",
        ),
    ]


@pytest.mark.asyncio
async def test_opanai_on_transcript_done():
    scenario = load_scenario("ask_order")
    received_items = []

    async def on_transcript_delta_done(delta: AudioTranscriptDone):
        received_items.append((delta.item_id, delta.transcript))

    openai = FakeOpenAI(
        events=scenario,
        event_handler=EventHandler(on_transcript_delta_done=on_transcript_delta_done),
    )
    await openai.run()

    assert received_items == [
        (
            "item_AIK0wRecrZqZlLV2oUVja",
            "I can help with that. Could you please provide the order number or "
            "any details related to your order?",
        ),
    ]


@pytest.mark.asyncio
async def test_opanai_on_audio_delta():
    scenario = load_scenario("ask_order")
    received_items = []

    async def on_audio_delta(delta: AudioDelta):
        received_items.append((delta.item_id, delta.delta))

    openai = FakeOpenAI(
        events=scenario,
        event_handler=EventHandler(on_audio_delta=on_audio_delta),
    )
    await openai.run()

    assert len(received_items) == 21
    assert received_items[:2] == [
        (
            "item_AIK0wRecrZqZlLV2oUVja",
            "BgAGAAIABgAEAAIABwACAAgABQAHAAQA/f8GAPz/CAAAAAYAAQAAAAUA/P8CAP3/AwABAAAAAgD+/wEA//8AAP/////+//7//v/+/wMA/f8AAP//+f////j//v/0/wMA+v8AAPz/+f/7//j//f/1//3/+//+//f/+//3//z/+v/8//v/9//3//X/9//5//v/9//7//X/+f/y//v/+f/4//j/9//2//T/9v/6//r//v/6//v/+P/y//v/8f/+//L/+P/z/+///v/w//r/7//6//D/+P/6//f/+P/v//z/9P/6//H/9v/0//L/+f/z//n/8P/3//T/+P/0//b/8f/y/+//8f/2/+//+P/s//H/8f/z/+z/8v/x//D/8//4//D/8f/s/+//7v/t//H/6v/y/+r/8f/t/+//8f/y//b/7f/z/+7/8v/u/+//+P/w//X/7v/y//P/8v/4/+//9//t//X/8v/2//f/9v/2//P//P/5//b/+P/1//n/+P/6//n/+//9//v/8//7//r/+v/8//z//v/3//r/+P/9//r/+v/9//v//f/4//7/AAD8////+/8AAPv/BwAEAAIABAD8/wYA/f8MAPv/EgAAAAYABQACAAQA//8TAAkACAAGAAoADAADAA0ABgASAAsADAALAA0AGAANABYABwAYAA8AFQASABIAGAAOABsAEgAbABIAFQAWABAAHQAUABkAEgAaABoAGAAeABcAGwATABYAEQAXABQAGAAYABQAGQATABcAFQAUABgADwAWABIAFAARABMAEgAKAB0ACwAdABIAFAARAA8AGAAGABsABwAYAAUAGAATABMAFAAMABQACwAXABEAEwANABUADwAUAA4ADAAMAA8AEgAOABIACwAOAA0AEAAPAA8ACQALAA4ACQAMAA4ADgAJAA4ACAAPAAsACgAIAAkACgAHAAoA//8AAAcAAAAFAP//CAD+/wMA+//9/wIA/f8JAPf/AADy/wAA9//+//b/+v/8//b//f/x//3/8P8AAPH//P/w//v/9v/w//b/8v/6//L/9v/z//n/9v/5//X/+v/1//j/6f/y//L/9v/8//L/+//n//3/5/8AAPD/9//s//b/8v/p//H/7f/4//D/7//q//L/8f/3/+X/9P/l/+r/6P/v/+n/6v/v//D/7//s/+f/7P/o/+f/6P/o/+j/6P/q/+v/5v/p/+j/5v/m/+b/8v/m/+7/3//t/+f/6f/s/+f/7f/f/+v/5v/t/+P/7P/o/+3/7f/v/+7/6v/s//L/6//z//D/9P/x//L/7//y/+7/9f/0//T/9f/w//b/6//8//L/+v/1//X/+v/p//7/7f8BAO7//P/3/+7//P/v/wAA6v8BAPL/9f/x//n/+v/z//z/8f////L//P/4//r/+//1//j/8f/4//T/9f/4//f/9//4//v//f/3////9P/9//T//v/5//r/+f/4/wAAAAAAAP3/+//9//j/BQADAP7/BAD+/wcA+P8NAPv/CwAAAAkABQAAAAsAAAAQAP7/EwD//w4AAAAHAAgACAAQAAEADwD//wwAAAAPAAIABgADAAcABQADAAoAAgAQAP//CwD//wsABgAFAA0A+/8QAPv/EwD9/w0AAgADAAgA/v8QAP//DAAEAAYACwAAAAsAAwAMAAYABQAJAAYACwAHAAkADAAHABAABAAVAAEAEwABABUACQAUAAkACgAQAAgAFwAEABgABAAaAAcAEwAPAAwAFgAMABkAEwAWABQADgAVAAoAFwASABMAEgANABQAEgAYAAsAEwAHABIAFAAdAAoAFwAMABAAEQATAA8ADQAXAAwAFAAHABcADAAUABIABwASAAsAFgANABUADgAHABUACwAXAAgACwANAAgADQABABEABAAOAAwACAATAAcADwAGABAACAAKAAoACgAGAAgAAwAIAAYABQAIAAQACwAAAAkA//8CAAIAAAAKAPv/AwD0/wgA+v8KAAIA+f/+//n/AwD1/wkA9P/+//7/9P8BAPD/AgDp//v/8v/u//f/6P8AAOH/+P/o/+//8f/o//X/4v/1/+b/9P/t/+3/7P/n/+3/6P/v/+b/8P/s/+r/5//n/+3/4//s/+f/6v/q/+X/6//i/+n/6v/o/+n/4v/t/+T/7v/p/+j/7P/q/+r/6v/t//D/6//t/+//5v/x/+b/7//l/+r/9v/o//H/5P/0/+j/6//v/+T/9//l//T/6f/x//L/6f/2/+r/9//v//P/9f/u//f/7f/z//D/8v/6//T/+P/z//D//P/r//v/6//7//X/8P8AAOv/AQDm////9//2//7/8P8GAPH/AADy//3////8/wEA+/8AAAAA/f8BAPj//v8BAPb/CgD3/wsA+P8EAP7/BAAIAPj/DQD3/woAAAAPAAEACQALAAcADgADABMABQAXAAcAEAAIABAAEQAKABUABQAXAAkAGAAMABQACwAOABIACwAYAAgAHgADABcADgARABsABwAjAAoAJwAKAB4ADwAPAB0ADQAmAA0AHQAQABsAFwATABsAEAAbAA8AFQARABAAGAARABMADwATABYAEQAbAAkAGgALABUADAAOABEACAAaAAUAFAAAABEABwAPAA4ACQAQAAUADQAAAA0A+v8IAAIABAAEAP3/CgD4/wcA+/8EAP7/AAAIAPj/AAD2//3//v/5/wAA+P8DAPn/+//9//f//P/0/wAA8P////L/+v/0//P/+v/n//7/5f/8/+v/9v/z/+n/+//k//3/5f/7/+3/8//0/+7/9//u//X/7f/0/+3/9f/q//T/5//1/+7/8P/y/+j/+P/i//f/6f/1/+r/8P/z/+f/9f/m//P/7P/0/+//6v/1/+v/+P/t//v/8P/w//b/7v/8//H/9P/v//v/9P/1//r/9//5//b////6//z/+f/7//z/+P8AAPv/+//1//3//v/+/wQA/P8AAP////8BAAIAAgACAAUABwAGAAgABgAEAAYABwAJAAYADQAJAA8ACAAMAAoADQALABAADwAMAA8ADwAUAAwAFAARABAAEgANABIADgASABEADgAQABAAEwARABMAEAAQABQAEAAVABMAEQAPABIAEQAPABMAEAARAAwAEwAOABUAEAAPAA4ADAAPAAoADwANAA4AEAALAA4ABwALAAoACgAOAAoADQAEAA0ACQAIAAoABgAJAAUABAADAAgACQAFAAQAAwAFAAMABQACAAEAAAAAAAAA/f8AAAAAAQD//wIAAAD8////+v8AAP7//f/5//z/+P/9//n/+v/4//z/+v/3//v/9//4//X/9v/1//X/+v/2//f/9P/y//b/7//2//L/9f/0/+//8//t//T/8P/2//H/8f/x//T/8//w//X/8v/1//D/9P/y//L/9v/z//X/9P/2//f/9f/2//P/9v/w//b/9v/4//T/9f/6//X//v/3//j/9P/3//b/+P/4//j/+P/1//b/9//7//b/+v/2//r/9v/5//f/9//4//X/+P/3//j/+P/7//r/9v/3//T/9//1//T/9//z//r/9v/4//r/9f/7//f/+//4//v/+v/6//r/+v/8//z/+v/6//z//P/8//7//P/9//v/+//8//j//f/9//z////8//z//P/7/wAA/v/+/wAA//8DAP//AAD8//z/AAD//////f8CAAAABAABAAAA/P///wEABAAJAAEABgD+/wIABQAJAAMABQAEAAQABgAJAAkACAAJAAYABwAFAAgACQAKAAkABgAGAAwACQALAAgABwAGAAQABQAEAAYAAwAGAAMABQADAAUAAQAAAAYAAwACAAYACAAHAAEAAwAFAAkACQAJAAkACQAJAAcACQAIAAcACAAIAAkABAAFAAYABgAIAAkABQAFAAQABQACAAMABgADAAAAAAABAAQABAAIAAYABQACAAYADAAJAAoABQAJAAcABgAHAAoACQAGAAgAAwAFAAQACQAIAAUACwAGAAsACwAQABAAEQARABIAFQASABUAFQAZABgAGgAdABoAHQAYABgAGQAZAB0AGQAcAB4AHgAaAB4AIQAgABgAHAAfACAAIwAeAB8AHAAiACAAJQAoACoAMwAtADUAJgAtAC4AKgAuACoAKwAlACMAIgAbABgAFwATABIAFQAWABcAFAAVABYAGQAbABwAHgAbABwAFgAUABEADwANAA0ADAALAA0ABgAJAA4AEwAVABUAGAARAAsABgAAAP3/9v/y/+7/8f/x//H/8f/r/+z/7P/u//X/+P/2//L/7P/p/+b/4f/m/+L/5v/e/9v/3f/M/77/t/+4/8D/wf/I/8b/xf/C/7f/tf+2/7z/u/++/8f/vf+1/6r/of+f/6D/qv++/9P/1v/T/8n/yf+9/7b/tv+z/7X/r/+u/6L/lv+F/4L/l/+9//H/GgA2ADwAKgAhABkAHQAgABoACAD1/+L/yf+w/5j/jf+H/5L/uP/Z/+7/5P/Y/9r/5/8DABEAGQAIAPH/2v/J/8r/yP/H/8b/zP/V/9j/0f/H/7r/tf+u/7b/yf/b//P/HwBTAIoAswDJAMsAtQCGAEcA/v+5/4f/Wv9E/zX/If8b/yf/Qv9y/7H/3v8FAA0A8v+o/zj/yP6A/on+2P5S/7L/5//9/xMANQBfAJkAyQDiAMUAZwDZ/0b/wP6G/qP+CP+K//T/HwAcAB8ALwBrAG0AKACK//z+Af9B/5z/jv93/6v/WwCfAe8CTwQUBUIFqgRrAxACfwB5/+D+xf7Z/p3+Hv5f/Q79Xf0l/gP/ef+Q/5H/vv/S/7L/rP8CANkAzwFzAp4CdgIAAmwB8gClAIYAPADf/3H/Ov9Z/5f/wv+6/wwAmwD1AIEAQf/v/Vn92f3t/loAuAFwAocCZQKaAmEDEQToA7wC7QAP/4/92vwB/YP9/v0O/gb+GP5Z/vX+9f9/AVED7wQkBtUGIwfwBkwGiAWeBB8EygOQAzMDNQILAcT/Kf/x/jz/AAD2AHoBqABn/93+d/8XAX4BGAFzARwDTgYuB1kFzf/o+kv48Pnz/wEGbwj8AVn07+a44XbmK/FQ+34EqQxwE5cUlxDQCokHsQifCLYGrf8U9rrpSd9h2wvh5e+s/k4LnBIyGK8aVBipEG0HOALb//j+lPrg83PtIumW5zjrUfRwAGcLig9SDaYIWgQEAYj+Ofyx+rv71vye/zwEcgm6DrcQ2Q7DCbwF6QJMAcX7pO7R3rrQsst2z4jZEOdq9xcIThV9HVEfbR1fGCwSLg3TCtcIigNg+cvuw+oF74z4xQAkBIQCHf5Q+B7zDO8/7Drq1eib6UftOvNj+Mj8lwB/BEQJig07ET4T7RBRCgcCUPti9tvy8e+u773zRvgl/Of8yvsL+uH4ufkl/44JHhNlGQ4aZhmKGTkZcBYOEjAOBgoWBf38MfS87GvnIOVG537unPlUBKIK+wwiDY4MiwsXCnoIZAcPBe4ARPtr9f3xA/Mi+VwC9wulEhMWsBaQFWgUlBOYE4gTOxKoDgEJ3QKC/TH7RfyMAJcGmwxoEWsTahJODpIIZwLY/Af5Qvfz93L5uvr2+/X91wEABxcNJhPhF2UZWxbSD1IHhv98+O/ySO6b6XHjh9uz1P7Rc9W33P/mE/KY/OMDwwXJAtD7nfLG503gjeBt63z6OwV+Bc/8VvJ467vrmvH6+Nj7uPzG/ZIEIQ62EjAOYALK9dvrj+dg5dDls+RR4u7iE+qV9zwHrhZoJUc17j/0QYQ5NSnAFbICgPSF7kzv8u8l7eXlZeCZ4bPoPPYmBqoT5hmTFrUNwAXKAeD/eP9Y/2ICZwcJDKIOxA6vDZUKbQgmCGYLIQ4cDUMILwKV/zcALQQ0CmgRfBebGu0YpxPVCxoCIPls8iDwHPHD8+v2lPrv/lcE3Qu4FNweeCaRKGAl7R2tFF4LBwOH/Hz48fVp9Ir0ifU89xn54Pvo/z0FiQk1C8oKVAieBYwC0AAeAXgDSAbsB9EHaAYzBDYBDP4r+vf15+9b553dmdRTz8bOStQq35Lsfvl+AmAHCgm6CSQM/RDBFngbjBk6DiT8UucY10jNucnZy1bUrt8U6zb1z/pf/cb93/zc+wP+0/7c/T3/egKyDg8fai69OE07tjEVHkMHo/KY4iXV5MexuZO1vrgWxX3Y4exZAqMV5SPgKbwqax8xC6Lzb+Bm2y/iN/AC/v8JYBGMFgoZshrFGkYXxxJ8CXr/d/Om6NzhkeF06Rr3OQiTFhghGCfHKLYmryBbGBIP3whdBW8FHgj2CxgRyRX9GCkaPRrlFyYUOQ9fCh4HGQTDANX9QvxW/O3+LASeCjkR9hOiEYsKmABZ9yfx5/C19mEAzgrBEHwR",
        ),
        (
            "item_AIK0wRecrZqZlLV2oUVja",
            "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",
        ),
    ]


@pytest.mark.asyncio
async def test_opanai_on_audio_done():
    scenario = load_scenario("ask_order")
    received_items = []

    async def on_audio_done(delta: AudioDone):
        received_items.append((delta.item_id,))

    openai = FakeOpenAI(
        events=scenario,
        event_handler=EventHandler(on_audio_done=on_audio_done),
    )
    await openai.run()

    assert received_items == [
        ("item_AIK0wRecrZqZlLV2oUVja",),
    ]
