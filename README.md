# Corvo Programming Language

**Corvo** is a small interpreted programming language designed for clarity, simplicity, and readability.  
It is ideal for beginners learning computational logic, or for teachers demonstrating programming concepts in a human-readable syntax.

---

## Overview

Corvo uses a **natural English-style syntax**, allowing programs to read like plain sentences.  
It helps learners understand key ideas such as variables, loops, conditionals, file handling, and structured data without worrying about punctuation or technical syntax.

A Corvo program runs through a Python interpreter built using the **Lark** parsing library.

---

## Features

- Human-friendly, English-like syntax  
- Variables and arithmetic expressions  
- Conditional statements (single-line and block-based)  
- Loops: `repeat`, `while`, and `for each`  
- Lists and list manipulation (`append`, `remove`, `count`, `at`)  
- Sections (functions without parameters)  
- String and numeric expressions  
- File input and output (`read`, `write`)  
- CSV read and write, column access, and cell editing  
- Safe error handling with clear messages  

---

## Getting Started

### 1. Prerequisites

You will need:
- **Python 3.8 or higher**  
- The **Lark** parsing library

To install Lark, open a terminal and run:
```bash
pip install lark
```

### 2. Download or Clone the Repository

You can download the Corvo source files or clone them directly from GitHub:

```bash
git clone https://github.com/TotoroEmotoro/Corvo.git
cd Corvo
```

### 3. Run Your First Program

Create a text file, for example `hello.txt`, and add this code:

```corvo
display "Hello from Corvo!"
```

Then run it from the command line:

```bash
python interpreter.py hello.txt
```

If everything is set up correctly, Corvo will display:

```
Hello from Corvo!
```

---

## Example Programs

### Hello World and Maths
```corvo
the x is 10
the y is 5
the total is x plus y
display "Total: " plus total
```

### Conditional Example
```corvo
ask "Enter your age: " remember as age
if age is greater than 18 then display "You can vote!" otherwise display "Too young to vote"
```

### Loops
```corvo
the count is 1
repeat 5 loops : [
    display "Hello number " plus count
    the count is count plus 1
]
```

### Sections (Functions)
```corvo
section greet is [
    display "Welcome to Corvo!"
]

greet
```

### CSV Handling
```corvo
read csv "students.csv" remember as data
display "Names: " plus get column 1 from data
set data row 2 column 3 to "Updated"
write data to csv "students_updated.csv"
```

---

## Running Corvo Programs

To run any `.corvo` or `.txt` file that contains Corvo code:

```bash
python interpreter.py my_program.txt
```

Make sure both `interpreter.py` and `grammar.lark` are in the same directory.

---

## Syntax Summary

| Feature | Example |
|----------|----------|
| **Variables** | `the score is 100` |
| **Maths** | `the total is x plus y` |
| **Display Output** | `display "Hello"` |
| **Input** | `ask "Enter name: " remember as name` |
| **If / Else** | `if x is greater than 10 then display "Big"` |
| **While Loop** | `while x is less than 10 do : [ ... ]` |
| **Repeat Loop** | `repeat 5 loops display "Hi"` |
| **For Each Loop** | `for each item in list : [ display item ]` |
| **List Creation** | `the names is ["Alice", "Bob", "Charlie"]` |
| **Append / Remove** | `append "Dan" to names` |
| **File Input / Output** | `write message to "file.txt"` |
| **CSV Input / Output** | `read csv "data.csv" remember as table` |

---

## Comprehensive Example

See `comprehensive_test.txt` for a full demonstration of all language features:
- Variables, loops, and conditionals  
- Lists and list manipulation  
- Sections (functions)  
- File reading and writing  
- CSV operations (reading, writing, column access, editing)  

---

## Technical Details

- **Interpreter:** Python, using [Lark](https://github.com/lark-parser/lark)  
- **Grammar:** Defined in `grammar.lark`  
- **Execution Model:** Tree-walk interpreter (transform-based)  
- **Error Handling:** Handles undefined variables, missing files, and invalid indices safely  

---

## Example Set

The repository includes several example Corvo programs:

| File | Description |
|------|--------------|
| `task1.txt` | Basic arithmetic |
| `task2.txt` | Age-based decision |
| `task3.txt` | Looping example |
| `task4.txt` | Simple temperature check |
| `task5.txt` | Area calculation |
| `task6.txt` | Repeat with user input |
| `GCSE1–9.txt` | Curriculum-style examples (loops, conditionals, CSVs) |
| `comprehensive_test.txt` | Full feature test |

---

## Philosophy

Corvo aims to **bridge human reasoning and programming logic**.  
It is readable, expressive, and approachable, helping learners think algorithmically without unnecessary complexity.

---

## Future Plans

- Add functions with parameters  
- Introduce arithmetic precedence  
- Support nested lists and structured data  
- Optional type checking  
- Web-based Corvo playground  

---

## Author

**Austin**  
GitHub: [TotoroEmotoro](https://github.com/TotoroEmotoro)

---

## Licence

Licensed under the **LGPL Licence**.  
See the `LICENCE` file for full details.
