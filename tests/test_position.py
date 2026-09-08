import asyncio
import time

from core.app import (
    state,
    set_anchor,
    get_position,
)


def reset_state():
    state.anchor_position = 0.0
    state.anchor_clock = time.perf_counter()
    state.playing = False
    state.rate = 1.0
    state.duration = 0.0


async def test_playing_position():
    reset_state()

    await set_anchor(
        position=10.0,
        playing=True,
        rate=1.0
    )

    await asyncio.sleep(0.5)

    position = await get_position()

    assert 10.4 <= position <= 10.7, (
        f"Unexpected position: {position}"
    )


async def test_pause():
    reset_state()

    await set_anchor(
        position=20.0,
        playing=False,
        rate=1.0
    )

    await asyncio.sleep(0.5)

    position = await get_position()

    assert 19.9 <= position <= 20.1, (
        f"Position moved while paused: {position}"
    )


async def test_resume():
    reset_state()

    await set_anchor(
        position=30.0,
        playing=False,
        rate=1.0
    )

    paused_position = await get_position()

    await set_anchor(
        position=paused_position,
        playing=True,
        rate=1.0
    )

    await asyncio.sleep(0.5)

    position = await get_position()

    assert 0.4 <= position - paused_position <= 0.7, (
        f"Unexpected resume position: {position}"
    )


async def test_seek_forward():
    reset_state()

    await set_anchor(
        position=10.0,
        playing=True,
        rate=1.0
    )

    await asyncio.sleep(0.2)

    await set_anchor(
        position=100.0,
        playing=True,
        rate=1.0
    )

    position = await get_position()

    assert 99.9 <= position <= 100.2, (
        f"Seek forward failed: {position}"
    )


async def test_seek_backward():
    reset_state()

    await set_anchor(
        position=100.0,
        playing=True,
        rate=1.0
    )

    await asyncio.sleep(0.2)

    await set_anchor(
        position=20.0,
        playing=True,
        rate=1.0
    )

    position = await get_position()

    assert 19.9 <= position <= 20.2, (
        f"Seek backward failed: {position}"
    )


async def test_playback_rate():
    reset_state()

    await set_anchor(
        position=0.0,
        playing=True,
        rate=2.0
    )

    await asyncio.sleep(0.5)

    position = await get_position()

    assert 0.8 <= position <= 1.2, (
        f"Playback rate failed: {position}"
    )


async def test_duration_limit():
    reset_state()

    state.duration = 10.0

    await set_anchor(
        position=9.0,
        playing=True,
        rate=2.0
    )

    await asyncio.sleep(1.0)

    position = await get_position()

    assert position <= 10.0, (
        f"Position exceeded duration: {position}"
    )


async def main():
    await test_playing_position()
    print("Playing position       : PASS")

    await test_pause()
    print("Pause                   : PASS")

    await test_resume()
    print("Resume                  : PASS")

    await test_seek_forward()
    print("Seek forward            : PASS")

    await test_seek_backward()
    print("Seek backward           : PASS")

    await test_playback_rate()
    print("Playback rate           : PASS")

    await test_duration_limit()
    print("Duration limit          : PASS")

    print()
    print("All position tests passed.")


if __name__ == "__main__":
    asyncio.run(main())