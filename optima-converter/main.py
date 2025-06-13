from flask import Flask, request, send_file, render_template, redirect, url_for, flash
import pandas as pd
import os
import traceback

app = Flask(__name__)
app.secret_key = 'tajny_klucz'

UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def convert_csv_to_ini(csv_file_path, ini_path):
    print(f"[INFO] Start konwersji: {csv_file_path}")
    try:
        # Wczytaj dane
        df = pd.read_csv(csv_file_path, sep=';', encoding='utf-8')
        print(f"[INFO] Wczytano CSV, liczba wierszy: {len(df)}")

        df = df.dropna(how='all')
        print(f"[INFO] Po usunięciu pustych wierszy: {len(df)}")

        # Konwersja liczb
        for col in ['Netto', 'VAT', 'Brutto']:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False).astype(float)
        print(f"[INFO] Przekonwertowano wartości liczbowe")

        # Daty
        df['Data wyst.'] = pd.to_datetime(df['Data wyst.'], format='%d.%m.%Y').dt.strftime('%Y-%m-%d')
        print(f"[INFO] Przekonwertowano daty")

        # Zapis do ini
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

        print(f"[SUCCESS] Plik INI zapisany do: {ini_path}")
    except Exception as e:
        print(f"[ERROR] Błąd podczas konwersji CSV do INI: {e}")
        traceback.print_exc()
        raise

@app.route('/')
def index():
    print("[INFO] Wywołanie: index")
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    print("[INFO] Wywołanie: upload")
    if 'file' not in request.files:
        flash("Nie załączono pliku", "error")
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash("Nie wybrano pliku", "error")
        return redirect(url_for('index'))

    try:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        print(f"[INFO] Zapisano plik do: {filepath}")

        ini_filename = os.path.splitext(file.filename)[0] + '.ini'
        ini_path = os.path.join(UPLOAD_FOLDER, ini_filename)
        print(f"[INFO] Ścieżka docelowa INI: {ini_path}")

        convert_csv_to_ini(filepath, ini_path)

        print(f"[INFO] Konwersja zakończona, przekierowanie do success")
        return redirect(url_for('success', filename=ini_filename))
    except Exception as e:
        print(f"[ERROR] Błąd w upload(): {e}")
        traceback.print_exc()
        flash(str(e), "error")
        return redirect(url_for('index'))

@app.route('/success/<filename>')
def success(filename):
    print(f"[INFO] Wywołanie success dla pliku: {filename}")
    return render_template('success.html', filename=filename)

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        flash("Plik nie istnieje", "error")
        print(f"[ERROR] Brak pliku do pobrania: {file_path}")
        return redirect(url_for('index'))

    print(f"[INFO] Pobieranie pliku: {file_path}")
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    from waitress import serve
    port = int(os.environ.get("PORT", 5000))
    print(f"[INFO] Uruchamianie serwera na porcie {port}")
    serve(app, host='0.0.0.0', port=port)
