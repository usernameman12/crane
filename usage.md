## 📘 `USAGE.md`

````markdown
# CRANE – Command-line Rich Advanced Navigation Editor

**CRANE** is a powerful terminal-based text editor with:
- Multiple modes (Normal, Insert, Visual)
- Mouse support
- Syntax highlighting
- Media playback (audio/image preview)
- Line numbers
- Command-line features (`:w`, `:q`, `:open`, `:saveas`, `:!`, etc.)

---

## 🛠️ Installation

You can install CRANE from source or system-wide (`sudo`) using GitHub.

### ✅ Requirements

Install Python and dependencies:

```bash
sudo apt update
sudo apt install python3 python3-pip -y
pip3 install pygments pillow pygame numpy
````

---

## 🔃 Clone the Repository

```bash
git clone https://github.com/usernameman12/crane
cd crane
```

---

## 🧪 Run Locally (Test Mode)

```bash
python3 crane.py yourfile.txt
```

---

## 📦 Install System-Wide (sudo)

You can install CRANE so it's available as a global command (`cranetextedit` or `crane`):

### Option 1: Install with a Bash Script

```bash
sudo cp crane.py /usr/bin/crane.py
sudo cp launcher.sh /usr/bin/cranetextedit
sudo chmod +x /usr/bin/crane.py /usr/bin/cranetextedit
```

*(or manually make a launcher like this)*:

```bash
echo -e '#!/bin/bash\npython3 /usr/bin/crane.py "$@"' | sudo tee /usr/bin/cranetextedit
sudo chmod +x /usr/bin/cranetextedit
```

Now you can run:

```bash
cranetextedit myfile.txt
or:
crane myfile.txt
```

---

## 📄 Usage

* Start CRANE:

  ```bash
  cranetextedit yourfile.txt
  ```

### 🔁 Modes

| Key   | Mode   |
| ----- | ------ |
| `i`   | Insert |
| `v`   | Visual |
| `ESC` | Normal |

### 📜 Commands (press `:`)

| Command          | Action                   |
| ---------------- | ------------------------ |
| `:w`             | Save file                |
| `:q`             | Quit                     |
| `:wq`            | Save & quit              |
| `:open filename` | Open file                |
| `:saveas name`   | Save file under new name |
| `:!command`      | Run shell command        |
| `:help`          | Show command help        |

### 🔍 Extras

* `/` → Search text
* `r` → Replace string (enter as `old/new`)
* `p` → Preview/play selected file if audio/image
* Mouse → Click to move cursor (in most terminals)

---

## 📦 Uninstall

```bash
sudo rm /usr/bin/cranetextedit /usr/bin/crane.py
```

---

## 🧑‍💻 Dev

To modify or contribute:

```bash
git clone https://github.com/usernameman12/crane
cd crane
nano crane.py
```

---

## 🐧 Supported OS

* Ubuntu/Debian
* Arch Linux (manual `PKGBUILD` supported)
* Any Linux system with Python 3

---

## 📬 Contact

Created by [@usernameman12](https://github.com/usernameman12)

```
