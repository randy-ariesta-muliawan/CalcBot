# CalcBot

CalcBot is a simple web-based calculator application built with Python. It provides a clean interface for performing basic arithmetic operations and is structured to be easy to run, understand, and customize.

## Features
- Web interface for basic arithmetic (addition, subtraction, multiplication, division)
- Clean HTML templates for input and output pages
- Simple and readable project structure
- Easy to extend with new operations or UI improvements

## Project Structure
```
CalcBot/
├── app.py
├── requirements.txt
├── templates/
│   ├── index.html
│   └── result.html
├── static/
│   ├── favicon/
└── README.md
```

## Requirements
- Python 3.8+
- pip

All dependencies are listed in `requirements.txt`.

## Installation & Running Locally

### 1. Clone the repository
```
git clone https://github.com/randy-ariesta-muliawan/CalcBot.git
cd CalcBot
```

### 2. Create a virtual environment (optional but recommended)
```
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Run the application
```
python app.py
```

### 5. Open in your browser
```
http://127.0.0.1:5000
```

## Usage
1. Open the main page.
2. Enter two numbers and choose an arithmetic operation.
3. Submit the form to see the result displayed.

## Customization
- Modify `app.py` to add more operations or improve logic.
- Edit HTML templates inside the `templates/` folder.
- Update CSS files in `static/`.
- Add tests using any Python testing framework.

## Deployment
To deploy on services like Render, Railway, or Heroku:

1. Make sure `requirements.txt` is complete.
2. (Optional) Add a `Procfile` if using a production server such as Gunicorn:
   ```
   web: gunicorn app:app
   ```
3. Configure environment variables such as `PORT` if required.

## Troubleshooting
- If the app fails to start, verify your Python version and installed dependencies.
- If port 5000 is already in use, run Flask on another port:
  ```
  flask run --port 8000
  ```

## Contributing
1. Fork this repository.
2. Create a new branch:
   ```
   git checkout -b feature/my-update
   ```
3. Commit your changes.
4. Push the branch and open a Pull Request.
