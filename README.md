# Mini Language Compiler (Web-Based)

## 📌 Project Description

This project is a web-based Mini Language Compiler developed using Python and Flask. It performs lexical and syntax analysis on user-provided source code and displays tokens, errors, parse results, and symbol table in a user-friendly interface.

## 🚀 Features

* Lexical Analysis (Token Generation)
* Syntax Analysis using Parser
* Error Detection with Suggestions
* Symbol Table Generation
* Web Interface using Flask
* Real-time Code Compilation

## 🛠️ Technologies Used

* Python
* Flask
* HTML, CSS
* Regular Expressions

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

## ▶️ How to Run

1. Install dependencies:

```
pip install flask
```

2. Run the application:

```
python app.py
```

3. Open browser and go to:

```
http://127.0.0.1:5000/
```

## 📊 Output

* Tokens list
* Syntax errors (if any)
* Parse tree
* Symbol table

## 🎯 Conclusion

This project demonstrates the working of a compiler front-end including lexical and syntax analysis along with a web interface for better visualization.


