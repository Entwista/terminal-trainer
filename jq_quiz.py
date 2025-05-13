#!/bin/python3

import random
import textwrap
import subprocess
import json
import tempfile
import os
import platform

def clear_terminal():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

questions = [
    {
        "question": "Pretty-print the following JSON:",
        "json": {"foo": "bar", "baz": [1, 2, 3]},
        "options": {
            "A": "cat file.json",
            "B": "jq '.' file.json",
            "C": "jq -c '.' file.json",
            "D": "jq -r '.' file.json"
        },
        "expected_output": """{
  "foo": "bar",
  "baz": [
    1,
    2,
    3
  ]
}
""",
        "answer": "B"
    },
    {
        "question": "Access the value of the key 'name':",
        "json": {"name": "Alice"},
        "options": {
            "A": "jq '.name' file.json",
            "B": "jq 'name' file.json",
            "C": "jq '[.name]' file.json",
            "D": "jq '.\"name\"' file.json"
        },
        "expected_output": '"Alice"\n',
        "answer": "A"
    },
    {
        "question": "Extract the first object in the array 'users':",
        "json": {"users": [{"id": 1}, {"id": 2}]},
        "options": {
            "A": "jq '.users.0' file.json",
            "B": "jq '.users[1]' file.json",
            "C": "jq '.users[0]' file.json",
            "D": "jq '.users | first' file.json"
        },
        "expected_output": """{
  "id": 1
}
""",
        "answer": "C"
    },
    {
        "question": "Loop over array of users:",
        "json": {"users": [{"name": "a"}, {"name": "b"}]},
        "options": {
            "A": "jq '.users | each' file.json",
            "B": "jq '.users[]' file.json",
            "C": "jq '.users[*]' file.json",
            "D": "jq '.users | .[]' file.json"
        },
        "expected_output": """{
  "name": "a"
}
{
  "name": "b"
}
""",
        "answer": "B"
    },
    {
        "question": "Filter users where 'active' is true:",
        "json": {"users": [{"active": True}, {"active": False}]},
        "options": {
            "A": "jq '.users[] | select(.active)' file.json",
            "B": "jq '.users | .active == true' file.json",
            "C": "jq 'select(.users[].active)' file.json",
            "D": "jq '.users[] | where(.active)' file.json"
        },
        "expected_output": """{
  "active": true
}
""",
        "answer": "A"
    },
    {
        "question": "Count the number of users:",
        "json": {"users": [{}, {}, {}]},
        "options": {
            "A": "jq '.users | length' file.json",
            "B": "jq 'length(users)' file.json",
            "C": "jq '.length(users)' file.json",
            "D": "jq 'count(.users)' file.json"
        },
        "expected_output": '3\n',
        "answer": "A"
    },
    {
        "question": "Convert array to CSV:",
        "json": {"users": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]},
        "options": {
            "A": "jq '.users | @csv' file.json",
            "B": "jq -r '.users[] | [.id, .name] | @csv' file.json",
            "C": "jq -r '.users | @csv' file.json",
            "D": "jq '.users[] | join(\",\")' file.json"
        },
        "expected_output": """1,"a"
2,"b"
""",
        "answer": "B"
    },
    {
        "question": "Rename fields during transformation:",
        "json": {"users": [{"name": "Alice", "active": True}]},
        "options": {
            "A": "jq '.users[] | {name, active}' file.json",
            "B": "jq '.users[] | {user: .name, status: .active}' file.json",
            "C": "jq '.users[] | [.name, .active]' file.json",
            "D": "jq '.users[] | map_values(.)' file.json"
        },
        "expected_output": """{
  "user": "Alice",
  "status": true
}
""",
        "answer": "B"
    },
    {
        "question": "Combine name and email fields:",
        "json": {"users": [{"name": "Alice", "email": "alice@example.com"}]},
        "options": {
            "A": "jq '.users[] | .name + \" <\" + .email + \">\"' file.json",
            "B": "jq '.users[] | \"(.name) <(.email)>\"' file.json",
            "C": "jq -r '.users[] | \"\(.name) <\(.email)>\"' file.json",
            "D": "jq '.users[] | join(\" <\")' file.json"
        },
        "expected_output": "Alice <alice@example.com>\n",
        "answer": "C"
    },
    {
        "question": "Sort users by name:",
        "json": {"users": [{"name": "Zoe"}, {"name": "Amy"}]},
        "options": {
            "A": "jq '.users | order_by(.name)' file.json",
            "B": "jq '.users | sort_by(.name)' file.json",
            "C": "jq 'sort(users.name)' file.json",
            "D": "jq '.users[].name | sort' file.json"
        },
        "expected_output": """[
  {
    "name": "Amy"
  },
  {
    "name": "Zoe"
  }
]
""",
        "answer": "B"
    }
]

random.shuffle(questions)
score = 0

clear_terminal()
print("\n📘 JQ QUIZ\n")

for q in questions:
    print("\n" + q["question"])
    print("JSON =")
    print(textwrap.indent(textwrap.fill(str(q["json"]), width=70), "  "))
    print()

    for opt, cmd in sorted(q["options"].items()):
        print(f"{opt}: {cmd}")

    answer = input("Your answer (A/B/C/D): ").strip().upper()
    selected_cmd = q["options"].get(answer)
    if not selected_cmd:
        print("❌ Invalid option.")
        input("Press Enter to continue...")
        clear_terminal()
        continue

    with tempfile.NamedTemporaryFile(mode='w+', delete=True) as tmp:
        json.dump(q["json"], tmp)
        tmp.flush()
        command = selected_cmd.replace("file.json", tmp.name)
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            actual_output = result.stdout
        except Exception as e:
            actual_output = f"ERROR: {e}"
    expected = q["expected_output"]

    if actual_output == expected:
        print("✅ Correct!")
        try:
            subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga'], stderr=subprocess.DEVNULL)
        except Exception:
            pass  # Ignore sound errors if sound player not available
        score += 1
    else:
        print(f"❌ Incorrect. The correct answer was {q['answer']}")

    input("Press Enter to continue...")
    clear_terminal()

print(f"\n🎯 Quiz complete! You got {score} out of {len(questions)} correct.")