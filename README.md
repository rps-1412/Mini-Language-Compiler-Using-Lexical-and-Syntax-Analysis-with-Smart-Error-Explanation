# 🚀 Mini Language Compiler (Web-Based)

## 📌 Overview

This project is a **web-based Mini Language Compiler** built using Python and Flask.
It performs **Lexical Analysis** and **Syntax Analysis** on user input code and displays tokens, errors, and symbol table in an interactive interface.

---

## 🌟 Features

* 🔍 Lexical Analysis (Token Generation using Regex)
* 🧠 Syntax Analysis (Parser Implementation)
* ⚠️ Smart Error Detection & Explanation
* 📊 Symbol Table Generation
* 🌐 Web Interface using Flask
* ⚡ Real-time Code Processing

---

## 🛠️ Tech Stack

* **Backend:** Python (Flask)
* **Frontend:** HTML, CSS
* **Core Logic:** Regular Expressions, Parsing Techniques

---

## 📂 Project Structure

```
project/
 ├── app.py
 ├── lexer.py
 ├── parser.py
 ├── symbol_table.py
 ├── error_handler.py
 ├── grammar.txt
 ├── static/
 │     └── style.css
 └── templates/
       └── index.html
```

---

## ▶️ How to Run

### 1️⃣ Install Dependencies

```
pip install flask
```

### 2️⃣ Run Application

```
python app.py
```

### 3️⃣ Open in Browser

```
http://127.0.0.1:5000/
```

---

## 📊 Output Includes

* ✅ Tokens List
* ✅ Syntax Errors (if any)
* ✅ Parse Results
* ✅ Symbol Table

---

## 💡 Working

1. User inputs code in the web interface
2. Lexer breaks code into tokens
3. Parser checks syntax rules
4. Errors are detected and explained
5. Symbol table stores identifiers

---

## 🎯 Applications

* Compiler Design Learning
* Educational Tools
* Code Analysis Systems

---

## ⭐ Conclusion

This project demonstrates the working of a **compiler front-end**, including lexical and syntax analysis, integrated with a web-based interface for better usability.
