from flask import Flask, request, send_file, render_template, redirect, url_for, flash
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'tajny_klucz'

UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def convert_csv_to_ini(csv_file_path, ini_path):
    try:
        print(f"[INFO] Wczytywanie pliku CSV: {csv_file_path}")
        with open(csv_file_path, 'rb') as f:
            head = f.read(100)
            print(f"[DEBUG] Pierwsze bajty pliku: {head}")

        # Wczytaj CSV ze średnikiem, kodowaniem cp1250 (Windows-1250)
        df = pd.read_csv(csv_file_path, sep=';', encoding='cp1250')
        print(f"[INFO] Wczytano dane: {len(df)} wierszy")

        df = df.dropna(how='all')  # Usuń puste wiersze

        # Konwersja liczb
        for col in ['Netto', 'VAT', 'Brutto']:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False).astype(float)

        # Przekształcenie daty
        df['Data wyst.'] = pd.to_datetime(df['Data wyst.'], format='%d.%m.%Y').dt.strftime('%Y-%m-%d')

        print(f"[INFO] Generowanie pliku INI...")

        with open(ini_path, 'w', encoding='cp1250', newline='\r\n') as ini:
            for _, row in df.iterrows():
                ini.write(f"[{row['Numer dokumentu']}]\r\n")
                ini.write("TYP=Dokument księgowy\r\n")
                ini.write(f"NUMER={row['Numer dokumentu']}\r\n")
                ini.write(f"DATA={row['Data wyst.']}\r\n")
                ini.write(f"KONTRAHENT={row['Kontrahent']}\r\n")
                ini.write(f"NIP={row['NIP']}\r\n")
                ini.write(f"NETTO={row['Netto']:.2f}\r\n")
                ini.write(f"VAT={row['VAT']:.2f}\r\n")
                ini.write(f"BRUTTO={row['Brutto']:.2f}\r\n\r\n")

        print(f"[INFO] Zapisano plik INI: {ini_path}")

    except Exception as e:
        print(f"[ERROR] Błąd konwersji: {e}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files or request.files['file'].filename == '':
        flash("Nie załączono pliku", "error")
        return redirect(url_for('index'))

    try:
        file = request.files['file']
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        print(f"[INFO] Zapisano plik: {filepath}")

        ini_filename = os.path.splitext(file.filename)[0] + '.ini'
        ini_path = os.path.join(UPLOAD_FOLDER, ini_filename)

        convert_csv_to_ini(filepath, ini_path)

        return redirect(url_for('success', filename=ini_filename))
    except Exception as e:
        flash(f"Błąd konwersji: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/success/<filename>')
def success(filename):
    return render_template('success.html', filename=filename)

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        flash("Plik nie istnieje", "error")
        return redirect(url_for('index'))

    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    from waitress import serve
    import os
    port = int(os.environ.get("PORT", 10000))  # Render ustawia zmienną PORT
    print(f"[INFO] Start aplikacji na porcie {port}")
    serve(app, host='0.0.0.0', port=port)
