from flask import Flask, request, jsonify, render_template
import pyodbc
from datetime import datetime
import traceback

app = Flask(__name__)

def get_db_connection():
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=VOLKAN\SQLEXPRESS;'
            'DATABASE=Kutuphane;'
            'Trusted_Connection=yes;'
        )
        return conn
    except pyodbc.Error as e:
        print(f"Veritabanına bağlanılamadı: {e}")
        return None

@app.route('/sa-as')    
def index():
    return render_template('a.html')  # a.html dosyasını döndür

@app.route('/book-add', methods=['POST'])
def kitap_ekle():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Veritabanına bağlanılamadı"}), 500
    try:
        data = request.json
        print(f"Alınan veri: {data}")   
        kitap_id = data.get('KitapID')
        yazar_key = data.get('YazarID')
        kitap_baslik = data.get('KitapBasligi')
        yayin_tarih = data.get('YayinTarihi')
        if kitap_id is None or yazar_key is None or kitap_baslik is None or yayin_tarih is None:
            return jsonify({"Error": "Eksik veri: YazarID, KitapBasligi, YayinTarihi eksik"}), 400
        try:
            yayin_tarih = datetime.strptime(yayin_tarih, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"Error": "Zaman geçersiz format, YYYY-MM-DD şeklinde olmalıdır."}), 400

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO dbo.Kitaplar (KitapID, YazarID, KitapBasligi, YayinTarihi) VALUES (?, ?, ?, ?)",
            (kitap_id, yazar_key, kitap_baslik, yayin_tarih)
        )
        conn.commit()
        return jsonify({"Message": "Kitap veritabanına başarıyla eklendi"}), 201
    except Exception as e:
        print("Hata:", e)
        print("Traceback:", traceback.format_exc())
        return jsonify({"Error": f"Veritabanı bağlantı hatası: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/book-yazar', methods=['POST'])
def yazar_ekle():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Veritabanına bağlanılamadı"}), 500
    try:
        data = request.json
        print(f"Alınan veri: {data}")
        yazar_key = data.get('YazarID')
        yazar_adi = data.get('YazarAdi')
        if yazar_key is None or yazar_adi is None:
            return jsonify({"Error": "Eksik veri: YazarID veya YazarAdi eksik"}), 400
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO dbo.Yazarlar (YazarID, YazarAdi) VALUES (?, ?)",
            (yazar_key, yazar_adi)
        )
        conn.commit()
        return jsonify({"Message": "Yazar veritabanına başarıyla eklendi"}), 201
    except Exception as e:
        print("Hata:", e)
        print("Traceback:", traceback.format_exc())
        return jsonify({"Error": f"Veritabanı bağlantı hatası: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/books/getir', methods=['GET'])
def kitaplar_getir():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Veritabanına bağlanılamadı"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT k.KitapID, y.YazarAdi, k.KitapBasligi, k.YayinTarihi
            FROM dbo.Kitaplar k 
            JOIN dbo.Yazarlar y ON k.YazarID = y.YazarID
        """)
        
        books = cursor.fetchall()
        
        book_list = []
        for book in books:
            book_data = {
                "KitapID": book.KitapID,
                "YazarAdi": book.YazarAdi,
                "KitapBasligi": book.KitapBasligi,
                "YayinTarihi": book.YayinTarihi.strftime('%Y-%m-%d')
            }
            book_list.append(book_data)

        return jsonify(book_list), 200
    except Exception as e:
        print("Hata:", e)
        print("Traceback:", traceback.format_exc())
        return jsonify({"Error": f"Veritabanı bağlantı hatası: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/books-guncel', methods=['PUT'])
def books_guncel():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Veritabanına bağlanılamadı"}), 500
    
    try:
        data = request.json
        print(f"Alınan veri: {data}")
        
        kitap_id = data.get('KitapID') 
        yazar_key = data.get('YazarID') 
        kitap_baslik = data.get('KitapBasligi')  
        yayin_tarih = data.get('YayinTarihi')  
        
        if kitap_id is None:
            return jsonify({"Error": "Eksik veri: KitapID gereklidir."}), 400

        update_fields = []
        params = []
    
        if yazar_key is not None:
            update_fields.append("YazarID = ?")
            params.append(yazar_key)

        if kitap_baslik is not None:
            update_fields.append("KitapBasligi = ?")
            params.append(kitap_baslik)

        if yayin_tarih is not None:
            try:
                yayin_tarih = datetime.strptime(yayin_tarih, '%Y-%m-%d').date()
                update_fields.append("YayinTarihi = ?")
                params.append(yayin_tarih)
            except ValueError:
                return jsonify({"Error": "Zaman geçersiz format. YYYY-MM-DD şeklinde olmalıdır."}), 400

        if not update_fields:
            return jsonify({"Error": "Güncellenecek veri yok."}), 400

        params.append(kitap_id)
        
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE dbo.Kitaplar SET {', '.join(update_fields)} WHERE KitapID = ?",
            params
        )
        
        if cursor.rowcount == 0:
            return jsonify({"Message": "Güncellenecek kitap bulunamadı."}), 404
        
        conn.commit()
        return jsonify({"Message": "Kitap başarıyla güncellendi."}), 200
    except Exception as e:
        print("Hata:", e)
        print("Traceback:", traceback.format_exc())
        return jsonify({"Error": f"Veritabanı hatası: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/books-sil/<int:kitap_id>', methods=['DELETE'])
def book_delete(kitap_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"Error": "Veritabanı bağlanılamadı"}), 500
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT YazarID FROM dbo.Kitaplar WHERE KitapID = ?", (kitap_id,))
        yazar_id = cursor.fetchone()

        if yazar_id is None:
            return jsonify({"Error": "Belirtilen KitapID bulunamadı"}), 404
        
        cursor.execute("DELETE FROM dbo.Kitaplar WHERE KitapID = ?", (kitap_id,))
        
        cursor.execute("SELECT COUNT(*) FROM dbo.Kitaplar WHERE YazarID = ?", (yazar_id[0],))
        kitap_sayisi = cursor.fetchone()[0]
        
        if kitap_sayisi == 0:
            cursor.execute("DELETE FROM dbo.Yazarlar WHERE YazarID = ?", (yazar_id[0],))

        conn.commit()
        return jsonify({"Message": "Kitap ve gerekli yazar başarıyla silindi."}), 200

    except Exception as e:
        print("Hata:", e)
        return jsonify({"Error": f"Veritabanı hatası: {str(e)}"}), 500
    
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
