# bambu-midi-gcode
Convert MIDI files into M1006 G-code so Bambu Lab printers play your own  melody through the stepper motors at print start or finish. Includes a  library of tunes reworked by hand to fit the motors' narrow range, since  straight conversions mostly sound like noise. Paste the output into  Machine start G-code in Bambu Studio.
Custom melodies on a Bambu Lab P2S
The script turns a MIDI file into M1006 commands. You paste them into the printer profile and the stepper motors play the tune. Tested on a P2S. I ran it in PowerShell, but any terminal works — cmd, bash, macOS Terminal.
One-time setup
pip install mido

Put p2s_midi_to_m1006.py and your MIDI file in the same folder, then open a terminal there.
Step 1. Look at the tracks
python p2s_midi_to_m1006.py song.mid --list

Output:

0 Drum Kit 753 notes

1 Grand Piano 53 notes

2 Violin 272 notes

3 Bass Guitar 383 notes

Skip the drums. Take the melody and the bass. Only 3 notes play at once — one per motor.
Step 2. Build the G-code
python p2s_midi_to_m1006.py song.mid --tracks 2 3 --max-sec 10

You get song_p2s.gcode next to the MIDI. The script prints the length and the number of commands.
Step 3. Paste it into Bambu Studio
Printer settings (the edit icon next to the printer) → turn on Advanced → Machine G-code tab.
Save the profile as a copy, e.g. "P2S music", so the stock one stays intact.
In Machine start G-code, replace everything between the two ;=====printer start sound===== lines with the contents of song_p2s.gcode. Keep the divider lines.
Save the profile — the * next to its name should disappear.
Re-slice the model and print.

For a finish sound, do the same in Machine end G-code.

On Windows, copy through WordPad or Notepad and keep the line breaks intact.
Options
Flag
What it does
--list
show MIDI tracks
--tracks 2 3
which tracks to use
--transpose 12
pitch shift in semitones, +12 = one octave up
--max-sec 10
length of the fragment
--start-sec 10
start at second 10
--loops 2
repeat the fragment
--tempo 1.2
faster (>1) or slower (<1)
--min-ms 60
drop very short notes
--vol 100
volume 0–100
--unit-ms 10
duration unit calibration, 10 ms on the P2S

Examples
python p2s_midi_to_m1006.py doom.mid --tracks 0 1 --transpose 12 --max-sec 20

python p2s_midi_to_m1006.py gta4.mid --tracks 3 5 --start-sec 10 --max-sec 12

python p2s_midi_to_m1006.py tetris.mid --tracks 1 --max-sec 8 --loops 2

python p2s_midi_to_m1006.py song.mid --max-sec 300 --transpose -12 --vol 100
No sound?
Open song_p2s.gcode and check the numbers after A:

above 84 — too high, the motors stay silent. Add --transpose -12
below 45 — too low, add --transpose 12
the usable range is 50–80; the stock P2S chime uses 53–61

Other common causes: the profile was not saved, the model was not re-sliced, or the code went into the process settings instead of the printer settings.
Good to know
The duration unit is 10 ms, so B100 ≈ 1 second. MIDI tempo is converted automatically — no BPM to set.
Notes shorter than 50 ms blur together. Fix with --tempo 0.8 or --min-ms 60.
A chord is 3 notes max. If the MIDI has more, the script keeps the top 3.
8-bit MIDI files sound best — NES, Game Boy, chiptune. Orchestral scores and piano with sustain turn into a drone.
To convert MP3 to MIDI, use Spotify's Basic Pitch. A full song comes out messy; a clean single melody works fine.
Keep start sounds to 5–10 seconds — the printer waits the whole time. Long tracks belong in the finish sound.

