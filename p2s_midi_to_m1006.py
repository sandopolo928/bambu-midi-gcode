#!/usr/bin/env python3
"""
MIDI -> M1006 for Bambu Lab P2S (format taken from the stock P2S start G-code):
  M1006 A<note1> B<dur> L<vol>  C<note2> D<dur> M<vol>  E<note3> F<dur> N<vol>
  3 voices (3 motors), note = MIDI number (0 = rest), dur in UNIT ms (default 10 ms), vol 0-100.

Usage:
  pip install mido
  python p2s_midi_to_m1006.py song.mid                 # all tracks, first 12 s
  python p2s_midi_to_m1006.py song.mid --list          # show tracks
  python p2s_midi_to_m1006.py song.mid --tracks 1 2 --max-sec 8 --transpose -12 --tempo 1.1
Output: song_p2s.gcode -> paste between ";=====printer start sound =====" lines.
"""
import argparse, mido

def load_notes(path, tracks):
    mid = mido.MidiFile(path)
    notes = []
    for ti, tr in enumerate(mid.tracks):
        if tracks and ti not in tracks:
            continue
        # tempo map from merged file so timing is correct for every track
        pass
    # use merged playback for correct tempo; keep track index via meta
    t = 0.0; on = {}
    merged = mido.merge_tracks([ (tr if (not tracks or i in tracks) else [m for m in tr if m.is_meta]) for i, tr in enumerate(mid.tracks)])
    tempo = 500000
    for msg in merged:
        t += mido.tick2second(msg.time, mid.ticks_per_beat, tempo)
        if msg.type == 'set_tempo':
            tempo = msg.tempo
        elif msg.type == 'note_on' and msg.velocity > 0 and msg.channel != 9:  # skip drums
            on[(msg.channel, msg.note)] = (t, msg.velocity)
        elif msg.type in ('note_off', 'note_on') and (msg.channel, msg.note) in on:
            st, v = on.pop((msg.channel, msg.note))
            notes.append((st, t, msg.note, v))
    return sorted(notes)

def to_gcode(notes, unit_ms, max_sec, transpose, tempo, vol, min_ms, start_sec=0.0, loops=1):
    notes = [(s / tempo - start_sec, e / tempo - start_sec, n + transpose, v) for s, e, n, v in notes]
    notes = [(max(0.0, s), e, n, v) for s, e, n, v in notes if e > 0]
    if loops > 1 and notes:
        L = min(max(e for _, e, *_ in notes), max_sec)
        base = [x for x in notes if x[0] < L]
        notes = [(s + k * L, min(e, L) + k * L, n, v) for k in range(loops) for s, e, n, v in base]
        max_sec = L * loops
    notes = [x for x in notes if x[0] < max_sec]
    cuts = sorted({0.0} | {s for s, *_ in notes} | {min(e, max_sec) for _, e, *_ in notes})
    lines = []
    for a, b in zip(cuts, cuts[1:]):
        ms = (b - a) * 1000
        if ms < min_ms:
            continue
        active = sorted({n for s, e, n, _ in notes if s <= a < e}, reverse=True)[:3]  # keep highest 3
        active = [max(21, min(108, n)) for n in active] + [0] * (3 - len(active))
        d = max(1, round(ms / unit_ms))
        lv = [vol if n else 0 for n in active]
        lines.append(f"M1006 A{active[0]} B{d} L{lv[0]} C{active[1]} D{d} M{lv[1]} E{active[2]} F{d} N{lv[2]}")
    return "\n".join(["M17", "M400 S1", "M1006 S1", *lines, "M1006 W"]) + "\n"

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("midi"); p.add_argument("--list", action="store_true")
    p.add_argument("--tracks", type=int, nargs="*")
    p.add_argument("--max-sec", type=float, default=12)
    p.add_argument("--transpose", type=int, default=0)
    p.add_argument("--tempo", type=float, default=1.0, help=">1 = faster")
    p.add_argument("--unit-ms", type=float, default=10, help="ms per B/D/F unit (calibrate!)")
    p.add_argument("--vol", type=int, default=50)
    p.add_argument("--start-sec", type=float, default=0, help="skip first N seconds")
    p.add_argument("--loops", type=int, default=1, help="repeat fragment N times")
    p.add_argument("--min-ms", type=float, default=30)
    a = p.parse_args()
    if a.list:
        for i, tr in enumerate(mido.MidiFile(a.midi).tracks):
            print(i, tr.name, sum(1 for m in tr if m.type == 'note_on'), "notes")
        raise SystemExit
    g = to_gcode(load_notes(a.midi, a.tracks), a.unit_ms, a.max_sec, a.transpose, a.tempo, a.vol, a.min_ms, a.start_sec, a.loops)
    secs = sum(int(l.split(" B")[1].split()[0]) for l in g.splitlines() if l.startswith("M1006 A")) * a.unit_ms / 1000
    print(f"~{secs:.1f} s")
    out = a.midi.rsplit(".", 1)[0] + "_p2s.gcode"
    open(out, "w").write(g)
    print(f"{out}: {g.count('M1006 A')} commands")
