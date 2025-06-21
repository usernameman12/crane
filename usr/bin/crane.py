#!/usr/bin/env python3
import curses, sys, os, subprocess, threading
from pygments import highlight as ph
from pygments.lexers import guess_lexer_for_filename, TextLexer
from pygments.formatters import TerminalFormatter
from pygame import mixer
from PIL import Image
import numpy as np
from wcwidth import wcwidth, wcswidth

fmt = TerminalFormatter()

def syntax(line, fname, enabled=True):
    if not enabled:
        return line
    try:
        lex = guess_lexer_for_filename(fname or "<stdin>", line)
    except Exception:
        lex = TextLexer()
    return ph(line, lex, fmt).rstrip('\n')

def launch_new_window(fname):
    # Modify this command if you use another terminal emulator
    cmd = f"xterm -e python3 {sys.argv[0]} --edit {fname}"
    subprocess.Popen(cmd, shell=True)
    sys.exit()

def play_audio(path):
    def _play():
        mixer.init()
        mixer.music.load(path)
        mixer.music.play()
    threading.Thread(target=_play, daemon=True).start()

def show_image(path):
    img = Image.open(path).convert('L').resize((40,20))
    arr = np.array(img)
    chars = "@%#*+=-:. "
    print("\n".join("".join(chars[p*9//255] for p in row) for row in arr))
    input("Press Enter to continue...")

class Editor:
    def __init__(self, stdscr, fname=None):
        self.stdscr = stdscr
        self.fname = fname
        self.lines = ['']
        self.mode = 'NORMAL'  # NORMAL, INSERT, VISUAL, CMD
        self.cursor_y = 0
        self.cursor_x = 0
        self.vis_start = None
        self.cmd_buffer = ''
        self.search_term = ''
        self.syntax_enabled = True
        self.show_line_numbers = True
        self.undo_stack = []
        self.redo_stack = []
        self.status_msg = ''
        self.load_file()
        self.init_curses()
        self.formatter = TerminalFormatter()

    def init_curses(self):
        curses.curs_set(1)
        self.stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        # Setup color pairs for themes
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Status bar
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)   # Command line
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Visual select

    def load_file(self):
        if self.fname and os.path.isfile(self.fname):
            with open(self.fname, encoding='utf-8', errors='replace') as f:
                self.lines = f.read().splitlines()
            if not self.lines:
                self.lines = ['']
        else:
            self.lines = ['']

    def save_file(self, fname=None):
        fname = fname or self.fname
        if fname:
            try:
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.lines))
                self.status_msg = f"Saved to {fname}"
                self.fname = fname
            except Exception as e:
                self.status_msg = f"Save failed: {e}"
        else:
            self.status_msg = "No filename specified"

    def push_undo(self):
        self.undo_stack.append([line[:] for line in self.lines])
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append([line[:] for line in self.lines])
            self.lines = self.undo_stack.pop()
            self.cursor_y = min(self.cursor_y, len(self.lines)-1)
            self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
            self.status_msg = "Undo"

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append([line[:] for line in self.lines])
            self.lines = self.redo_stack.pop()
            self.cursor_y = min(self.cursor_y, len(self.lines)-1)
            self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
            self.status_msg = "Redo"

    def draw(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        max_y = h - 3  # Leave room for status and command lines

        for idx in range(min(len(self.lines), max_y)):
            line = self.lines[idx]
            lineno_str = f"{idx+1:4} " if self.show_line_numbers else ""
            # Syntax highlight or raw line
            line_str = syntax(line, self.fname, self.syntax_enabled)

            # Convert to plain text for curses rendering (strip ANSI)
            try:
                from pygments.formatters.terminal import TerminalFormatter
                import re
                ansi_escape = re.compile(r'\x1b\[.*?m')
                line_str_plain = ansi_escape.sub('', line_str)
            except Exception:
                line_str_plain = line

            # Handling visual mode selection
            if self.mode == 'VISUAL' and self.vis_start and idx == self.cursor_y:
                xs, xe = sorted((self.vis_start[1], self.cursor_x))
                displayed_line = ''
                pos = 0
                for ch in line_str_plain:
                    width = max(wcwidth(ch),1)
                    attr = curses.A_REVERSE if xs <= pos < xe else 0
                    try:
                        self.stdscr.addstr(idx, len(lineno_str)+pos, ch, attr)
                    except curses.error:
                        pass
                    pos += 1
                try:
                    self.stdscr.addstr(idx, 0, lineno_str, curses.A_DIM)
                except curses.error:
                    pass
            else:
                try:
                    self.stdscr.addstr(idx, 0, lineno_str + line_str_plain[:w - len(lineno_str) - 1])
                except curses.error:
                    pass

        # Status bar
        status = f"--{self.mode}-- {self.fname or '[No Name]'} Ln {self.cursor_y+1}, Col {self.cursor_x+1}  {self.status_msg}"
        self.status_msg = ''
        try:
            self.stdscr.addstr(h - 2, 0, " " * (w - 1), curses.color_pair(1))
            self.stdscr.addstr(h - 2, 0, status[:w - 1], curses.color_pair(1))
        except curses.error:
            pass

        # Command line (only in CMD mode)
        if self.mode == 'CMD':
            prompt = ":" + self.cmd_buffer
            try:
                self.stdscr.addstr(h - 1, 0, " " * (w - 1), curses.color_pair(2))
                self.stdscr.addstr(h - 1, 0, prompt[:w - 1], curses.color_pair(2))
            except curses.error:
                pass
            self.stdscr.move(h - 1, len(prompt))
        else:
            # Move cursor to position
            cx = self.cursor_x
            if self.show_line_numbers:
                cx += 5  # account for line number width
            self.stdscr.move(self.cursor_y, cx)

        self.stdscr.refresh()

    def get_input(self):
        try:
            return self.stdscr.get_wch()
        except curses.error:
            return None

    def command_dispatch(self, cmd):
        args = cmd.strip().split()
        if not args:
            return

        c = args[0]
        rest = args[1:] if len(args) > 1 else []

        try:
            if c == 'w':  # save
                self.save_file()
            elif c == 'q':  # quit (fail if unsaved)
                sys.exit(0)
            elif c == 'q!':  # force quit
                sys.exit(0)
            elif c == 'wq':  # save and quit
                self.save_file()
                sys.exit(0)
            elif c == 'e':  # edit new file
                if rest:
                    self.fname = rest[0]
                    self.load_file()
                    self.cursor_x = self.cursor_y = 0
            elif c == 'saveas':
                if rest:
                    self.save_file(rest[0])
                    self.fname = rest[0]
            elif c == 'r':  # read file and append
                if rest:
                    try:
                        with open(rest[0], encoding='utf-8') as f:
                            self.lines.extend(f.read().splitlines())
                        self.status_msg = f"Appended {rest[0]}"
                    except Exception as e:
                        self.status_msg = f"Error reading {rest[0]}: {e}"
            elif c == 'set':
                if rest:
                    if rest[0] == 'syntax':
                        self.syntax_enabled = not self.syntax_enabled
                        self.status_msg = f"Syntax {'on' if self.syntax_enabled else 'off'}"
                    elif rest[0] == 'number':
                        self.show_line_numbers = not self.show_line_numbers
                        self.status_msg = f"Line numbers {'on' if self.show_line_numbers else 'off'}"
            elif c == '!':  # shell command
                os.system(" ".join(rest))
            elif c == 'open':  # open media file at cursor word
                if rest:
                    path = rest[0]
                    if path.endswith(('.wav', '.mp3')):
                        play_audio(path)
                    elif path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                        curses.endwin()
                        show_image(path)
                        self.init_curses()
            elif c == 'pwd':
                self.status_msg = os.getcwd()
            elif c == 'cd':
                if rest:
                    try:
                        os.chdir(rest[0])
                        self.status_msg = f"Changed dir to {rest[0]}"
                    except Exception as e:
                        self.status_msg = f"cd failed: {e}"
            elif c == 'help':
                self.status_msg = "Commands: :w :q :wq :q! :e <file> :saveas <file> :r <file> :set syntax|number :!<cmd> :open <file> :pwd :cd <dir> :replace <old>/<new> :undo :redo"
            elif c == 'replace':
                if rest:
                    try:
                        old, new = rest[0].split('/', 1)
                        self.push_undo()
                        self.lines = [ln.replace(old, new) for ln in self.lines]
                        self.status_msg = f"Replaced '{old}' with '{new}'"
                    except Exception:
                        self.status_msg = "Usage: :replace old/new"
            elif c == 'undo':
                self.undo()
            elif c == 'redo':
                self.redo()
            elif c == 'new':
                self.push_undo()
                self.lines = ['']
                self.cursor_x = self.cursor_y = 0
                self.fname = None
                self.status_msg = "New buffer"
            else:
                self.status_msg = f"Unknown command: {c}"
        except Exception as e:
            self.status_msg = f"Command error: {e}"

    def find_term(self, term):
        for i, l in enumerate(self.lines):
            idx = l.find(term)
            if idx != -1:
                self.cursor_y = i
                self.cursor_x = idx
                self.status_msg = f"Found '{term}' at Ln {i+1}"
                return True
        self.status_msg = f"'{term}' not found"
        return False

    def process_normal(self, key):
        if key == 'i':
            self.mode = 'INSERT'
        elif key == 'v':
            self.mode = 'VISUAL'
            self.vis_start = (self.cursor_y, self.cursor_x)
        elif key == ':':
            self.mode = 'CMD'
            self.cmd_buffer = ''
        elif key == '/':
            self.mode = 'CMD'
            self.cmd_buffer = '/'
        elif key == 'u':
            self.undo()
        elif key == 'r':
            self.redo()
        elif key == 'h':
            if self.cursor_x > 0:
                self.cursor_x -= 1
        elif key == 'l':
            if self.cursor_x < len(self.lines[self.cursor_y]):
                self.cursor_x += 1
        elif key == 'j':
            if self.cursor_y < len(self.lines) - 1:
                self.cursor_y += 1
                self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
        elif key == 'k':
            if self.cursor_y > 0:
                self.cursor_y -= 1
                self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
        elif key == 'p':
            # Preview media file under cursor word
            words = self.lines[self.cursor_y].split()
            # Find which word cursor is on (approximate)
            cum = 0
            for w in words:
                if cum <= self.cursor_x < cum + len(w):
                    if w.endswith(('.wav', '.mp3')):
                        play_audio(w)
                    elif w.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                        curses.endwin()
                        show_image(w)
                        self.init_curses()
                    break
                cum += len(w) + 1
        elif key == '\x1b':  # ESC
            self.mode = 'NORMAL'
            self.vis_start = None
        else:
            pass

    def process_insert(self, key):
        if key == '\x1b':
            self.mode = 'NORMAL'
        elif key == '\n':
            self.push_undo()
            line = self.lines[self.cursor_y]
            new_line = line[self.cursor_x:]
            self.lines[self.cursor_y] = line[:self.cursor_x]
            self.lines.insert(self.cursor_y + 1, new_line)
            self.cursor_y += 1
            self.cursor_x = 0
        elif key in (curses.KEY_BACKSPACE, '\x7f'):
            if self.cursor_x > 0:
                self.push_undo()
                line = self.lines[self.cursor_y]
                self.lines[self.cursor_y] = line[:self.cursor_x-1] + line[self.cursor_x:]
                self.cursor_x -= 1
            elif self.cursor_y > 0:
                self.push_undo()
                prev_line_len = len(self.lines[self.cursor_y-1])
                self.lines[self.cursor_y-1] += self.lines[self.cursor_y]
                self.lines.pop(self.cursor_y)
                self.cursor_y -= 1
                self.cursor_x = prev_line_len
        elif isinstance(key, str):
            self.push_undo()
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x] + key + line[self.cursor_x:]
            self.cursor_x += 1

    def process_visual(self, key):
        if key == '\x1b':
            self.mode = 'NORMAL'
            self.vis_start = None
        elif key in ('h','j','k','l'):
            if key == 'h':
                if self.cursor_x > 0:
                    self.cursor_x -= 1
            elif key == 'l':
                if self.cursor_x < len(self.lines[self.cursor_y]):
                    self.cursor_x += 1
            elif key == 'j':
                if self.cursor_y < len(self.lines) - 1:
                    self.cursor_y += 1
                    self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
            elif key == 'k':
                if self.cursor_y > 0:
                    self.cursor_y -= 1
                    self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
        elif key == '\n':
            self.mode = 'NORMAL'
            self.vis_start = None

    def process_cmd(self, key):
        if key == '\n':
            cmd = self.cmd_buffer.strip()
            if cmd.startswith('/'):
                term = cmd[1:]
                self.find_term(term)
            else:
                self.command_dispatch(cmd)
            self.cmd_buffer = ''
            self.mode = 'NORMAL'
        elif key == '\x1b':
            self.cmd_buffer = ''
            self.mode = 'NORMAL'
        elif isinstance(key, str):
            self.cmd_buffer += key
        elif key == curses.KEY_BACKSPACE or key == '\x7f':
            self.cmd_buffer = self.cmd_buffer[:-1]

    def run(self):
        while True:
            self.draw()
            key = self.get_input()
            if key is None:
                continue
            if self.mode == 'NORMAL':
                self.process_normal(key)
            elif self.mode == 'INSERT':
                self.process_insert(key)
            elif self.mode == 'VISUAL':
                self.process_visual(key)
            elif self.mode == 'CMD':
                self.process_cmd(key)

def main(stdscr, fname=None):
    editor = Editor(stdscr, fname)
    editor.run()

if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--edit':
        filename = sys.argv[2]
        curses.wrapper(main, filename)
    else:
        filename = sys.argv[1] if len(sys.argv) > 1 else None
        launch_new_window(filename)
