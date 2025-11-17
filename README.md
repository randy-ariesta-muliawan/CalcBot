# CalcBot

CalcBot is an advanced web-based calculator application built with Python. It focuses on symbolic and numeric calculus operations, providing users with tools to compute limits, derivatives, integrals, and visualize functions through an integrated graphing calculator. CalcBot is designed for students, educators, and anyone who needs quick access to powerful calculus tools directly from a browser.

## Features
- Symbolic and numeric **limit** calculation  
- Symbolic and numeric **derivative** computation  
- **Definite and indefinite integral** solving  
- **Graphing calculator** with function plotting  
- Clean HTML templates for input and result pages  
- Simple, readable project structure  
- Easy to extend with more mathematical operations or UI improvements  

## Project Structure
```
CalcBot/
├── app.py
├── calc_core.py
├── requirements.txt
├── templates/
│   ├── graph.html
│   └── kalkulator.html
├── static/
│   ├── css/
│   └── js/
└── README.md
```

## Requirements
- Python 3.8+
- pip

Recommended Python packages:
- Flask (web framework)
- SymPy (symbolic mathematics)
- NumPy (numeric evaluation)
- Matplotlib or Plotly (graphing)
- Gunicorn (for deployment)

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
2. Choose an operation: Limit, Derivative, Integral, or Graph.  
3. Enter a function such as:  
   - `sin(x)/x`  
   - `x**2 * exp(x)`  
   - `1/(x-1)`  
4. Submit the form to view symbolic results, numeric evaluation, and plots if applicable.

## Implementation Notes
- Uses **SymPy** for symbolic limits, derivatives, and integrals.  
- Input is safely parsed using SymPy’s expression parser.  
- Graphs are generated using Matplotlib or Plotly.  
- Error handling is included for invalid input.  
- Results are rendered through HTML templates.

## Deployment
For deployment on Render, Railway, Heroku, or any cloud platform:

1. Ensure `requirements.txt` is complete.  
2. (Optional) Add a `Procfile` for Gunicorn:
```
web: gunicorn app:app
```
3. Configure environment variables (e.g., `PORT`).

## Troubleshooting
- Plots not displaying → Ensure plot directory exists.  
- Heavy expressions may require optimization.
