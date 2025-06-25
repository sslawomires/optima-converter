from flask import Flask, request, send_file, render_template, redirect, url_for, flash
import pandas as pd
import os
from werkzeug.utils import secure_filename
import traceback

app = Flask(__name__)
app.secret_key = 'tajny_klucz'

UPLOAD_FOLDER = '/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'csv', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_csv_to_ini(csv_file_path, ini_path):
    try:
        print(f"[INFO] Wczytywanie pliku CSV: {csv_file_path}")

        with open(csv_file_path, 'rb') as f:
            head = f.read(100)
            print(f"[DEBUG] Pierwsze bajty pliku: {head}")

        df = pd.read_csv(csv_file_path, sep=';', encoding='cp1250')

        # Czyszczenie nazw kolumn
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        print(f"[INFO] Kolumny: {df.columns.tolist()}")
        print(f"[INFO] Wczytano dane: {len(df)} wierszy")

        df = df.dropna(how='all')

        # Usuwamy niepotrzebną kolumnę
        if 'Nr listu przewozowego' in df.columns:
            df.drop(columns=['Nr listu przewozowego'], inplace=True)

        # Czyszczenie kolumn kwotowych
        for col in ['Netto', 'VAT', 'Brutto']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(' ', '', regex=False)
                df[col] = df[col].str.replace(',', '.', regex=False)
                df[col] = df[col].astype(float)

        # Konwersja daty na DD/MM/RRRR
        df['Data wyst.'] = pd.to_datetime(df['Data wyst.'], format='%d.%m.%Y').dt.strftime('%d/%m/%Y')

        # Stałe dane kontrahenta
        kontrahent_nazwa = "Firma Kastor Wacław Wiecha"
        kontrahent_ulica = "al.Solidarności 10"
        kontrahent_miejscowosc = "Brzesko"
        kontrahent_kod_pocztowy = "32-800"
        kontrahent_kraj = "PL"
        kontrahent_nip = "6791015997"

        with open(ini_path, 'w', encoding='cp1250', newline='\r\n') as ini:
            for idx, row in df.iterrows():
                # Pomijamy podsumowania lub niepoprawne wiersze
                if not (isinstance(row['Numer dokumentu'], str) and row['Numer dokumentu'].startswith('FAE/')):
                    print(f"[INFO] Pomijam wiersz: {row['Numer dokumentu']}")
                    continue

                ini.write(f"[{row['Numer dokumentu']}]\r\n")
                ini.write("TYP=Dokument księgowy\r\n")
                ini.write("KONTRAHENT=Odbiorca\r\n")
                ini.write(f"NUMER DOKUMENTU={row['Numer dokumentu']}\r\n")
                ini.write(f"DATA={row['Data wyst.']}\r\n")
                ini.write("OPIS=Zakup towarów handlowych\r\n")  # poprawiony opis
                ini.write("REJESTR=5\r\n")  # rejestr zakupów
                ini.write("KOLUMNA=10\r\n")  # kolumna zakupu towarów
                ini.write(f"NETTO-23={row['Netto']:.2f}\r\n")
                ini.write(f"VAT-23={row['VAT']:.2f}\r\n")
                ini.write(f"KWOTA={(row['Netto'] + row['VAT']):.2f}\r\n")
                ini.write(f"KONTRAHENT-NAZWA PELNA={kontrahent_nazwa}\r\n")
                ini.write(f"KONTRAHENT-ULICA={kontrahent_ulica}\r\n")
                ini.write(f"KONTRAHENT-MIEJSCOWOSC={kontrahent_miejscowosc}\r\n")
                ini.write(f"KONTRAHENT-KOD POCZTOWY={kontrahent_kod_pocztowy}\r\n")
                ini.write(f"KONTRAHENT-KRAJ={kontrahent_kraj}\r\n")
                ini.write(f"KONTRAHENT-NIP={kontrahent_nip}\r\n")
                ini.write(f"DATA SPRZEDAŻY={row['Data wyst.']}\r\n")
                ini.write("\r\n")

        print(f"[INFO] Zapisano plik INI: {ini_path}")

    except Exception as e:
        print(f"[ERROR] Błąd konwersji: {e}")
        traceback.print_exc()
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    print(f"[DEBUG] request.files: {request.files}")
    if 'file' not in request.files:
        print("[ERROR] Brak pola 'file'")
        flash("Nie załączono pliku", "error")
        return redirect(url_for('index'))

    file = request.files['file']
    print(f"[DEBUG] Otrzymano plik: {file.filename}")

    if file.filename == '':
        print("[ERROR] Plik bez nazwy")
        flash("Nie wybrano pliku", "error")
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        flash("Nieobsługiwany typ pliku. Proszę wybrać plik CSV.", "error")
        return redirect(url_for('index'))

    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        print(f"[INFO] Zapisano plik: {filepath}")

        ini_filename = os.path.splitext(filename)[0] + '.ini'
        ini_path = os.path.join(UPLOAD_FOLDER, ini_filename)

        convert_csv_to_ini(filepath, ini_path)

        return redirect(url_for('success', filename=ini_filename))
    except Exception as e:
        print(f"[ERROR] Wyjątek podczas przetwarzania: {str(e)}")
        traceback.print_exc()
        flash(f"Błąd konwersji: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/success/<filename>')
def success(filename):
    return render_template('success.html', filename=filename)

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        print(f"[ERROR] Plik {file_path} nie istnieje")
        flash("Plik nie istnieje", "error")
        return redirect(url_for('index'))

    print(f"[INFO] Pobieranie pliku: {file_path}")
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
