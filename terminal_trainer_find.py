#!/usr/bin/env python3
"""
Interactive *find* quiz.
The script builds a fresh sandbox for each question, runs the chosen command
inside it, and checks the command’s actual output against the expected output.
"""

import os, random, subprocess, tempfile, textwrap, time, shutil
from pathlib import Path

# --------------------------------------------------------------------------- #
#  Helper ­– create the directory / file / symlink layout for a question      #
# --------------------------------------------------------------------------- #
def build_fs(root: str, spec: list[dict]) -> None:
    """
    Build the file-system layout described by *spec* inside *root*.

    Each item in *spec* is a dict with keys:
      path         (str, required)  – relative path to create
      type         (str, required)  – 'dir', 'file', or 'symlink'
      size         (int, optional)  – bytes to write if type == 'file'
      executable   (bool, optional) – make file executable
      mtime        (float, optional)– epoch seconds to set as mtime
      target       (str, required for symlink) – symlink target
    """
    for item in spec:
        rel = Path(root) / item["path"]
        if item["type"] == "dir":
            rel.mkdir(parents=True, exist_ok=True)
        elif item["type"] == "file":
            rel.parent.mkdir(parents=True, exist_ok=True)
            with rel.open("wb") as fh:
                fh.write(b"x" * item.get("size", 0))
            if item.get("executable"):
                rel.chmod(rel.stat().st_mode | 0o111)
            if "mtime" in item:
                os.utime(rel, (item["mtime"], item["mtime"]))
        elif item["type"] == "symlink":
            tgt = Path(root) / item["target"]
            tgt.parent.mkdir(parents=True, exist_ok=True)
            if not tgt.exists():
                tgt.touch()
            rel.symlink_to(item["target"])
        else:
            raise ValueError(f"Unknown type {item['type']!r}")

# --------------------------------------------------------------------------- #
#  Question bank                                                              #
# --------------------------------------------------------------------------- #
questions = [
    {
        "question": "List *only* directories (not files) at depth 1 under "
                    "the directory **garden**.",
        "description": "garden/ with two sub-directories and several files "
                       "below them (plants/ and tools/).",
        "setup": [
            {"path": "garden", "type": "dir"},
            {"path": "garden/plants", "type": "dir"},
            {"path": "garden/tools", "type": "dir"},
            {"path": "garden/plants/roses.txt", "type": "file"},
            {"path": "garden/plants/tulips.txt", "type": "file"},
            {"path": "garden/tools/shovel", "type": "file"},
            {"path": "garden/tools/rake", "type": "file"},
        ],
        "options": {
            "A": "find garden -type d",
            "B": "find garden -maxdepth 1 -type d",
            "C": "find garden -depth 1 -type d",
            "D": "find garden -type d -mindepth 1",
        },
        "expected_output": "garden\ngarden/plants\ngarden/tools\n",
        "answer": "B",
    },
    {
        "question": "List all regular **.txt** files anywhere beneath "
                    "the directory **garden**.",
        "description": "Same *garden* tree as above, plus an *archive.txt* "
                       "directory so commands that don’t restrict to files "
                       "will include it.",
        "setup": [
            {"path": "garden", "type": "dir"},
            {"path": "garden/plants", "type": "dir"},
            {"path": "garden/tools", "type": "dir"},
            {"path": "garden/notes.txt", "type": "dir"},  # bogus dir
            {"path": "garden/plants/roses.txt", "type": "file"},
            {"path": "garden/plants/tulips.txt", "type": "file"},
        ],
        "options": {
            "A": "find garden -name '*.txt'",
            "B": "find garden -type f -name '*.txt'",
            "C": "find garden -type f -iname '*.TXT'",
            "D": "find garden -name '*.txt' -maxdepth 1",
        },
        "expected_output": ("garden/plants/roses.txt\n"
                            "garden/plants/tulips.txt\n"),
        "answer": "B",
    },
    {
        "question": "Find files larger than **1 kiB** inside **data/**.",
        "description": "data/ contains *big.dat* (≈2 kB) and *small.dat*.",
        "setup": [
            {"path": "data", "type": "dir"},
            {"path": "data/big.dat", "type": "file", "size": 2048},
            {"path": "data/small.dat", "type": "file", "size": 200},
        ],
        "options": {
            "A": "find data -type f -size +1k",
            "B": "find data -size +1024c",
            "C": "find data -type f -size 1k+",
            "D": "find data -type f -size +1000",
        },
        "expected_output": "data/big.dat\n",
        "answer": "A",
    },
    {
        "question": "Show **only empty directories** in the current tree.",
        "description": "There is an empty directory *emptydir/*, a directory "
                       "*fulldir/* with a file inside, and a zero-byte "
                       "file *empty.txt*.",
        "setup": [
            {"path": "emptydir", "type": "dir"},
            {"path": "fulldir", "type": "dir"},
            {"path": "fulldir/full.txt", "type": "file", "size": 50},
            {"path": "empty.txt", "type": "file", "size": 0},
        ],
        "options": {
            "A": "find . -empty",
            "B": "find . -type d -empty",
            "C": "find . -type f -empty",
            "D": "find . -empty -mindepth 1",
        },
        "expected_output": "./emptydir\n",
        "answer": "B",
    },
    {
        "question": "Which command lists executable regular files under "
                    "**scripts/**?",
        "description": "scripts/ has *run.sh* (executable) and *notes.txt*.",
        "setup": [
            {"path": "scripts", "type": "dir"},
            {"path": "scripts/run.sh", "type": "file",
             "size": 100, "executable": True},
            {"path": "scripts/notes.txt", "type": "file", "size": 20},
        ],
        "options": {
            "A": "find scripts -perm -u+x",
            "B": "find scripts -type f -executable",
            "C": "find scripts -type f -perm /a=x",
            "D": "find scripts -type f -perm +111",
        },
        "expected_output": "scripts/run.sh\n",
        "answer": "B",
    },
    {
        "question": "Find files modified **more than 7 days ago** in *logs/*. "
                    "(Ignore access-time updates.)",
        "description": "logs/old.log is 8 days old, logs/recent.log is now.",
        "setup": [
            {"path": "logs", "type": "dir"},
            {"path": "logs/old.log", "type": "file",
             "size": 10, "mtime": time.time() - 8 * 86400},
            {"path": "logs/recent.log", "type": "file", "size": 10},
        ],
        "options": {
            "A": "find logs -type f -mtime +7",
            "B": "find logs -mtime 7 -type f",
            "C": "find logs -type f -mtime -7",
            "D": "find logs -mtime +1w -type f",
        },
        "expected_output": "logs/old.log\n",
        "answer": "A",
    },
    {
        "question": "Identify symbolic links in the current directory tree.",
        "description": "link.txt → original.txt",
        "setup": [
            {"path": "original.txt", "type": "file", "size": 5},
            {"path": "link.txt", "type": "symlink", "target": "original.txt"},
        ],
        "options": {
            "A": "find . -type l",
            "B": "find . -symlink",
            "C": "find . -type f -links 1",
            "D": "find . -lname '*'",
        },
        "expected_output": "./link.txt\n",
        "answer": "A",
    },
    {
        "question": "Case-insensitive search: list a file named **readme** "
                    "in any mix of capitals.",
        "description": "Files: README, readme.md, ReadMe.txt.",
        "setup": [
            {"path": "README", "type": "file", "size": 1},
            {"path": "readme.md", "type": "file", "size": 1},
            {"path": "ReadMe.txt", "type": "file", "size": 1},
        ],
        "options": {
            "A": "find . -iname 'readme'",
            "B": "find . -name 'README'",
            "C": "find . -type f -iname 'readme*'",
            "D": "find . -iname 'readme' -type f",
        },
        "expected_output": "./README\n",
        "answer": "A",
    },
]

# --------------------------------------------------------------------------- #
#  Quiz runner                                                                #
# --------------------------------------------------------------------------- #
random.shuffle(questions)
score = 0
os.system("clear")
print("\n📂 FIND QUIZ\n")

for q in questions:
    print("\n" + q["question"])
    print()
    print(textwrap.indent(textwrap.fill(q["description"], width=70), "  "))
    print()

    for opt, cmd in sorted(q["options"].items()):
        print(f"{opt}: {cmd}")

    answer = input("Your answer (A/B/C/D): ").strip().upper()
    cmd_template = q["options"].get(answer)
    if not cmd_template:
        print("❌ Invalid option.")
        input("Press Enter to continue...")
        os.system("clear")
        continue

    # ---- create sandbox FS, run command there ----
    with tempfile.TemporaryDirectory() as tmp:
        build_fs(tmp, q["setup"])
        try:
            result = subprocess.run(
                cmd_template,
                shell=True,
                capture_output=True,
                text=True,
                cwd=tmp,
            )
            actual_output = result.stdout
        except Exception as e:
            actual_output = f"ERROR: {e}"

    if actual_output == q["expected_output"]:
        print("✅ Correct!")
        try:
            subprocess.Popen(
                ["paplay",
                 "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass
        score += 1
    else:
        print(f"❌ Incorrect. The correct answer was {q['answer']}")
        print("Expected:\n" + q["expected_output"])
        print("Got:\n" + actual_output)

    input("Press Enter to continue...")
    os.system("clear")

print(f"\n🎯 Quiz complete! You got {score} out of {len(questions)} correct.")
