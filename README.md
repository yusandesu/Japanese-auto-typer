# Japanese Auto Typer

A small desktop tool that "types" text for you into whatever window currently
has keyboard focus — with human-like variable speed, occasional typos that
get noticed and corrected, and natural pauses. Works with Japanese (kana,
kanji, mixed) as well as plain text.

It does **not** simulate an IME. Instead it copies each character to the
clipboard and sends the OS paste shortcut (Ctrl+V / Cmd+V), one character at
a time, with randomized delays in between. This reliably handles any
Japanese text without needing to drive input-method conversion.

## How it works

1. You paste the text you want typed into the app.
2. You press Start and get a few seconds (configurable) to click into the
   target text field — a chat window, an editor, a form, anything that
   accepts pasted text.
3. The app then "types" the text for you: variable speed, occasional random
   pauses (longer after 。/、/!/?), and occasional typos (a wrong character,
   or two characters swapped) that get backspaced and corrected, just like a
   real person.

## Setup

```bash
pip install -r requirements.txt
```

On Linux you also need Tkinter (usually not installed by default) and, for
`pyautogui` to control the keyboard, an X11 session:

```bash
sudo apt install python3-tk   # Debian/Ubuntu
```

Wayland: `pyautogui` key-sending is unreliable on native Wayland. If your
session is Wayland, either switch to an Xorg session, or use XWayland
(most desktops do this automatically for non-Wayland-native apps).

On macOS, grant "Accessibility" permission to your terminal / Python when
prompted (System Settings → Privacy & Security → Accessibility), otherwise
simulated keystrokes are blocked.

## Usage

GUI (recommended):

```bash
python main.py
```

Paste your text, adjust speed/typo settings if you like, click **Start**,
then quickly click into the target application before the countdown ends.
Click **Stop** at any time to cancel, or move your mouse to a screen corner
(pyautogui's built-in fail-safe).

CLI, for scripting:

```bash
python main.py --cli --file message.txt --cpm-min 200 --cpm-max 350 --delay 5
# or
cat message.txt | python main.py --cli --stdin
```

## Settings

- **Speed (chars/min)**: a new random speed within [min, max] is picked for
  *every character*, so the cadence isn't robotic.
- **Typo chance**: probability per character that a mistake happens — either
  a wrong character that gets backspaced and fixed, or two adjacent
  characters typed in the wrong order and then corrected.
- **Random pause chance**: probability of an extra "thinking" pause after a
  character, independent of typos. Sentence-ending punctuation (。、!?)
  always triggers a slightly longer pause.
- **Start delay**: seconds before typing begins, so you can switch windows.
- **Hiragana → kanji conversion (IME simulation)**: on by default (needs
  `pykakasi`, included in requirements.txt). Every kanji word is first typed
  as its hiragana reading, paused on briefly (like looking at IME
  conversion candidates), then replaced by the kanji — the same two-step
  flow a real Japanese IME uses, instead of the kanji just appearing
  instantly. Typos can happen during the hiragana part too.
- **Google Docs bullets**: off by default. When enabled, any line in your
  pasted text that starts with `- ` or `* ` (e.g. `- first point`) is typed
  as a real Google Docs bulleted-list item, by sending Google Docs' actual
  "toggle bulleted list" shortcut (Ctrl+Shift+8) before typing that line —
  not just a typed `•` character. **Only enable this when typing into
  Google Docs** — that shortcut does something unrelated in other apps
  (e.g. it toggles formatting marks in Microsoft Word).

The final text typed is always exactly what you pasted — typos are always
corrected, never left in.

## Limitations

- Fields that block paste (some password inputs, some anti-paste forms)
  won't work, since this tool relies on paste-per-character.
- Needs a real display/desktop session (X11, macOS, or Windows) — it drives
  the actual keyboard, so it won't do anything useful in a headless
  terminal-only environment.
- Use it for legitimate purposes (accessibility, demos, testing chat UIs,
  practicing, etc.) — don't use it to defeat proctoring/anti-cheat systems
  or otherwise misrepresent human authorship where that would violate a
  service's terms or academic/exam integrity rules.

## Tests

The typing-simulation logic (`auto_typer/core.py`) has no OS dependency and
is unit tested:

```bash
python -m unittest discover -s tests -v
```
