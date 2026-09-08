from core.lyrics import search_lyrics, parse_lrc, get_current_lyric


title = "Cupid (Twin Version)"
artist = "FIFTY FIFTY"

print("Searching lyrics...")
lrc = search_lyrics(title, artist)

if lrc:
    lyrics = parse_lrc(lrc)

    print(f"Found {len(lyrics)} lyric lines")
    print()

    for lyric in lyrics[:5]:
        print(lyric)

    print()
    print("At 30 seconds:")
    print(get_current_lyric(lyrics, 30))