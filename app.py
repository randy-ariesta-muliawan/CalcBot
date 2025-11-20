from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import sympy as sp
import json
import requests
import re
from pathlib import Path

# Inisialisasi Flask dengan folder static dan template
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Mengaktifkan CORS untuk pengembangan

# Konfigurasi Gemini (ambil dari environment, fallback ke default yang ada)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
GEMINI_API_URL = os.environ.get('GEMINI_API_URL',
    ('https://generativelanguage.googleapis.com/v1beta/models/'
     'gemini-2.5-flash-preview-09-2025:generateContent?key=' + GEMINI_API_KEY)
)

# Simbol dan fungsi SymPy yang diizinkan saat parsing ekspresi pengguna
SYMPY_LOCALS = {
    'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
    'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan,
    'ln': sp.log, 'log': sp.log, 'sqrt': sp.sqrt,
    'pi': sp.pi, 'π': sp.pi, 'e': sp.E, 'exp': sp.exp
}

def sanitize_expr_input(s):
    """Bersihkan input agar cocok dengan sintaks SymPy:
       - ^ -> ** (pangkat)
       - π -> pi
    """
    if s is None:
        return ''
    s = s.replace('^', '**').replace('π', 'pi')
    return s

def parse_expr(expr_str, variable='x'):
    """Parse string menjadi ekspresi SymPy.
    Mengembalikan tuple (expr, None) saat sukses, atau (None, error_msg) saat gagal.
    """
    expr_str_s = sanitize_expr_input(expr_str)
    try:
        x = sp.symbols(variable)
        expr = sp.sympify(expr_str_s, locals=SYMPY_LOCALS)  # parsing aman dengan nama lokal terbatas
        return expr, None
    except Exception as e:
        return None, str(e)

def sympy_to_latex(expr):
    """Konversi ekspresi SymPy menjadi LaTeX. Jika gagal, kembalikan representasi string."""
    try:
        return sp.latex(expr)
    except:
        return str(expr)

def ask_gemini_for_explanation(context_text, expr_latex, result_latex, operation):
    """Kirim prompt ke Gemini (LLM) untuk mendapatkan penjelasan langkah demi langkah.
       Mengembalikan (explanation, key_formula, error_message).
       Jika GEMINI_API_KEY tidak tersedia, kembalikan error message (penjelasan tidak dibuat).
    """
    if not GEMINI_API_KEY:
        return None, None, 'GEMINI_API_KEY not configured; LLM explanation skipped.'

    op_name = {'limit': 'limit', 'derivative': 'turunan', 'integral': 'integral'}.get(operation, operation)

    # Prompt berbahasa Indonesia yang meminta output JSON dengan explanation dan key_formula
    prompt = (
        f"Anda adalah asisten matematika berbahasa Indonesia yang ahli dalam menjelaskan konsep kalkulus.\n\n"
        f"Berikan penjelasan yang jelas, lengkap, dan mudah dipahami untuk hasil komputasi {op_name} berikut.\n\n"
        f"INFORMASI KOMPUTASI:\n{context_text}\n\n"
        f"Ekspresi dalam LaTeX: {expr_latex}\n"
        f"Hasil dalam LaTeX: {result_latex}\n\n"
        f"INSTRUKSI PENTING:\n"
        f"1. Jelaskan setiap langkah dengan detail, jangan skip langkah apapun\n"
        f"2. Gunakan format LaTeX untuk SEMUA ekspresi matematika:\n"
        f"   - \\( ... \\) untuk inline math\n"
        f"   - \\[ ... \\] untuk display math\n"
        f"3. Pisahkan paragraf dengan baris kosong (akan dikonversi jadi <br><br>)\n"
        f"4. Jelaskan konsep matematika yang relevan (aturan pangkat, rantai, dll.)\n"
        f"5. Untuk konstanta integrasi, jelaskan mengapa muncul dan apa artinya\n"
        f"6. Semua simbol matematika HARUS dibungkus oleh \\( ... \\)\n\n"
        f"Balas dengan JSON: {{\"explanation\": \"...\", \"key_formula\": \"...\"}}"
    )

    payload = {
        'contents': [{ 'parts': [{ 'text': prompt }] }],
        'generationConfig': {
            'responseMimeType': 'application/json',
            'temperature': 0.4
        }
    }

    try:
        resp = requests.post(GEMINI_API_URL, json=payload, timeout=30)  # panggil API Gemini
        resp.raise_for_status()
        data = resp.json()
        # Ambil teks raw dari struktur response Gemini
        raw_text = data.get('candidates', [])[0].get('content', {}).get('parts', [])[0].get('text', '')

        try:
            # Coba parsing sebagai JSON langsung
            parsed = json.loads(raw_text)
            explanation = parsed.get('explanation', '')
            key_formula = parsed.get('key_formula', '')
        except json.JSONDecodeError:
            # Jika tidak valid JSON, coba ekstrak dengan regex / fallback ke raw_text
            m = re.search(r'"explanation"\s*:\s*"((?:[^"\\]|\\.)*)"', raw_text, re.DOTALL)
            if m:
                explanation = m.group(1)
            else:
                explanation = raw_text
            key_formula = ''

        if explanation:
            # Bersihkan escape berlebih supaya MathJax dapat merendernya
            explanation = explanation.replace('\\"', '"').replace("\\'", "'")
            explanation = explanation.replace('\\\\(', '\\(').replace('\\\\)', '\\)')
            explanation = explanation.replace('\\\\[', '\\[').replace('\\\\]', '\\]')
            explanation = explanation.replace('\\n\\n', '\n\n').replace('\\n', '\n')
            explanation = explanation.strip()

        return explanation, key_formula, None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, None, f'Gemini request failed: {str(e)}'

def backend_normalize_explanation(explanation: str) -> str:
    """Post-process penjelasan AI untuk memperbaiki over-escaping atau kesalahan kecil."""
    if not explanation:
        return explanation
    ex = str(explanation)

    # Normalisasi delimiter LaTeX yang ke-escape berlebih
    ex = re.sub(r'\\+\s*\\\(', r'\\(', ex)
    ex = re.sub(r'\\+\s*\\\)', r'\\)', ex)
    ex = re.sub(r'\\+\s*\\\[', r'\\[', ex)
    ex = re.sub(r'\\+\s*\\\]', r'\\]', ex)

    # Collapse runs of backslashes before letters: '\\\\alpha' -> '\alpha'
    ex = re.sub(r'\\\\{2,}([a-zA-Z])', r'\\\1', ex)

    # Perbaiki transkripsi limit, misal 'x o 1' -> '\lim_{x \to 1}'
    ex = re.sub(r'lim_\{([^}]*)\s+[oO]\s+([^}]*)\}', r'\\lim_{\\1 \\to \\2}', ex)
    ex = re.sub(r'lim_\{([^}]*)\s+to\s+([^}]*)\}', r'\\lim_{\\1 \\to \\2}', ex, flags=re.IGNORECASE)
    ex = re.sub(r'lim_?([a-zA-Z0-9_]+)to([a-zA-Z0-9_+-]+)', lambda m: f"\\lim_{{{m.group(1)} \\to {m.group(2)}}}", ex, flags=re.IGNORECASE)

    # Perbaiki double \cdot
    ex = re.sub(r'\\cdot\s*\\cdot', r'\\cdot', ex)

    # Hapus backslash stray yang tidak diikuti oleh karakter valid
    ex = re.sub(r'\\(?![\\\(\)\[\]a-zA-Z])', '', ex)

    return ex.strip()

@app.route('/')
def index():
    # Render halaman kalkulator utama
    return render_template('kalkulator.html')

@app.route('/graph')
def graph():
    # Render halaman graphing
    return render_template('graph.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    # Serve file static (mirip behavior Flask default)
    return send_from_directory('static', filename)

@app.route('/api/compute', methods=['POST'])
def compute():
    # Ambil payload JSON dari client
    payload = request.json or {}
    expr_str = payload.get('expression', '')
    op = payload.get('operation', 'derivative')
    var = payload.get('variable', 'x')
    limit_point = payload.get('limit_point')
    limit_dir = payload.get('limit_direction', 'both')
    derivative_order = int(payload.get('derivative_order', 1))
    integral_lower = payload.get('integral_lower')
    integral_upper = payload.get('integral_upper')

    # Parse ekspresi dengan SymPy
    expr, err = parse_expr(expr_str, variable=var)
    if err:
        return jsonify({'error': f'Parsing error: {err}'}), 400

    x = sp.symbols(var)
    response = {'result': None, 'result_latex': None, 'steps': [], 'steps_latex': [], 'explanation': None, 'explanation_latex': None}

    try:
        # Sederhanakan ekspresi dan siapkan representasi LaTeX
        simplified = sp.simplify(expr)
        expr_latex = sympy_to_latex(expr)
        simplified_latex = sympy_to_latex(simplified)

        response['steps'].append(f'Ekspresi terparsing: {sp.pretty(expr)}')
        response['steps_latex'].append(f'Ekspresi awal: \\( f({var}) = {expr_latex} \\)')

        if str(simplified) != str(expr):
            response['steps'].append(f'Ekspresi disederhanakan: {sp.pretty(simplified)}')
            response['steps_latex'].append(f'Setelah disederhanakan: \\( {simplified_latex} \\)')

        result_expr = None

        if op == 'derivative':
            # Hitung turunan sesuai orde yang diminta
            result_expr = sp.diff(simplified, x, derivative_order)
            result_latex = sympy_to_latex(result_expr)
            response['result'] = sp.pretty(result_expr)
            response['result_latex'] = result_latex
            response['steps'].append(f'Turunan orde {derivative_order}: {sp.pretty(result_expr)}')
            if derivative_order == 1:
                response['steps_latex'].append(f"\\[ f'({var}) = \\frac{{d}}{{d{var}}} \\left( {simplified_latex} \\right) = {result_latex} \\]")
            elif derivative_order == 2:
                response['steps_latex'].append(f"\\[ f''({var}) = \\frac{{d^2}}{{d{var}^2}} \\left( {simplified_latex} \\right) = {result_latex} \\]")
            else:
                response['steps_latex'].append(f"\\[ f^{{({derivative_order})}}({var}) = {result_latex} \\]")

        elif op == 'integral':
            # Integral tentu jika batas bawah & atas diberikan
            if integral_lower and integral_upper and integral_lower.strip() and integral_upper.strip():
                a = sp.sympify(sanitize_expr_input(integral_lower), locals=SYMPY_LOCALS)
                b = sp.sympify(sanitize_expr_input(integral_upper), locals=SYMPY_LOCALS)
                anti = sp.integrate(simplified, x)
                eval_b = anti.subs(x, b)
                eval_a = anti.subs(x, a)
                definite = sp.simplify(eval_b - eval_a)
                response['result'] = sp.pretty(definite)
                response['result_latex'] = sympy_to_latex(definite)
                response['steps'].append(f'Antiderivatif: {sp.pretty(anti)}')
                response['steps_latex'].append(f'\\[ \\int {simplified_latex} \\, d{var} = {sympy_to_latex(anti)} + C \\]')
                response['steps'].append(f'Evaluasi batas: F({b}) - F({a}) = {sp.pretty(definite)}')
                response['steps_latex'].append(f'\\[ \\int_{{{sympy_to_latex(a)}}}^{{{sympy_to_latex(b)}}} {simplified_latex} \\, d{var} = \\left[ {sympy_to_latex(anti)} \\right]_{{{sympy_to_latex(a)}}}^{{{sympy_to_latex(b)}}} = {sympy_to_latex(definite)} \\]')
            else:
                # Integral tak tentu: tambahkan konstanta C
                anti = sp.integrate(simplified, x)
                response['result'] = sp.pretty(anti) + ' + C'
                response['result_latex'] = sympy_to_latex(anti) + ' + C'
                response['steps'].append(f'Antiderivatif: {sp.pretty(anti)} + C')
                response['steps_latex'].append(f'\\[ \\int {simplified_latex} \\, d{var} = {sympy_to_latex(anti)} + C \\]')

        elif op == 'limit':
            # Operasi limit memerlukan limit_point
            if not limit_point:
                return jsonify({'error': 'limit_point harus disediakan untuk operasi limit'}), 400
            lp_str = str(limit_point).lower()
            if lp_str in ['oo', 'inf', 'infty', 'infinity', '∞']:
                lp_sym = sp.oo; lp_latex = '\\infty'
            elif lp_str in ['-oo', '-inf', '-infty', '-infinity', '-∞']:
                lp_sym = -sp.oo; lp_latex = '-\\infty'
            else:
                lp_sym = sp.sympify(sanitize_expr_input(limit_point), locals=SYMPY_LOCALS)
                lp_latex = sympy_to_latex(lp_sym)
            dir_arg = None; dir_latex = ''
            if limit_dir == 'left':
                dir_arg = '-'; dir_latex = '^-'
            elif limit_dir == 'right':
                dir_arg = '+'; dir_latex = '^+'
            lim = sp.limit(simplified, x, lp_sym) if dir_arg is None else sp.limit(simplified, x, lp_sym, dir=dir_arg)
            response['result'] = sp.pretty(lim); response['result_latex'] = sympy_to_latex(lim)
            response['steps'].append(f'Limit menuju {limit_point}: {sp.pretty(lim)}')
            response['steps_latex'].append(f'\\[ \\lim_{{{var} \\to {lp_latex}{dir_latex}}} {simplified_latex} = {sympy_to_latex(lim)} \\]')
        else:
            return jsonify({'error': f'Unknown operation: {op}'}), 400

        # Siapkan konteks singkat yang akan dikirim ke LLM untuk penjelasan
        context_text = '\n'.join(response['steps']) + '\nHasil akhir: ' + str(response['result'])

        # Panggil Gemini untuk penjelasan
        explanation, key_formula, ex_err = ask_gemini_for_explanation(context_text, expr_latex, response['result_latex'], op)

        if explanation:
            explanation = backend_normalize_explanation(explanation)
            # Simpan penjelasan dari Gemini (dalam LaTeX yang sudah dinormalisasi)
            response['explanation_latex'] = explanation
            response['explanation'] = explanation
            if key_formula:
                response['key_formula_latex'] = backend_normalize_explanation(key_formula)
        else:
            # Jika Gemini gagal, sertakan pesan fallback
            response['explanation'] = f'Penjelasan AI tidak tersedia. {ex_err or ""}'
            response['explanation_latex'] = None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error saat menghitung: {str(e)}'}), 500

    # Kembalikan hasil JSON ke client
    return jsonify(response)

if __name__ == '__main__':
    # Pastikan folder templates dan static ada saat menjalankan secara lokal
    Path('templates').mkdir(exist_ok=True)
    Path('static').mkdir(exist_ok=True)
    # Jalankan server Flask (debug True untuk pengembangan)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)

