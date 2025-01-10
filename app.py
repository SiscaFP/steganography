from flask import Flask, request, jsonify, render_template
from stegano import lsb
import os
from math import log10, sqrt
import numpy as np 
import matplotlib.pyplot as plt

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def char_to_bin(char):
    return format(ord(char), '08b')

def bin_to_char(binary):
    return chr(int(binary, 2))

def sgl_to_bin(text):
    sgl_mapping = {
        'a': 'ᔑ', 'b': 'ʖ', 'c': 'ᓵ', 'd': '↸', 'e': 'ᒷ',
        'f': '⎓', 'g': '⊣', 'h': '⍑', 'i': '╎', 'j': '⋮',
        'k': 'ꖌ', 'l': 'ꖎ', 'm': 'ᒲ', 'n': 'リ', 'o': '𝙹',
        'p': '！¡', 'q': 'ᑑ', 'r': '∷', 's': 'ᓭ', 't': 'ℸ',
        'u': '⚍', 'v': '⍊', 'w': '∴', 'x': '/', 'y': '||',
        'z': '⨅'
    }
    binary_text = ""
    for char in text:
        if char in sgl_mapping:
            binary_text += char_to_bin(char)
        else:
            binary_text += char_to_bin(char)
    return binary_text

def bin_to_sgl(binary_message):
    sgl_mapping = {
        'a': 'ᔑ', 'b': 'ʖ', 'c': 'ᓵ', 'd': '↸', 'e': 'ᒷ',
        'f': '⎓', 'g': '⊣', 'h': '⍑', 'i': '╎', 'j': '⋮',
        'k': 'ꖌ', 'l': 'ꖎ', 'm': 'ᒲ', 'n': 'リ', 'o': '𝙹',
        'p': '！¡', 'q': 'ᑑ', 'r': '∷', 's': 'ᓭ', 't': 'ℸ',
        'u': '⚍', 'v': '⍊', 'w': '∴', 'x': '/', 'y': '||',
        'z': '⨅'
    }
    sgl_text = ''.join(sgl_mapping[bin_to_char(binary_message[i:i+8])] for i in range(0, len(binary_message), 8))
    return sgl_text

def cesar_cipher(text, shift, encrypt=True):
    if not all(char.isalpha() for char in text):
        raise ValueError("Pesan hanya boleh berisi huruf alfabet")
    
    result = ""
    for char in text:
        if char.isalpha():
            shift_base = ord('A') if char.isupper() else ord('a')
            if encrypt:
                result += chr((ord(char) - shift_base + shift) % 26 + shift_base)
            else:
                result += chr((ord(char) - shift_base - shift) % 26 + shift_base)
        else:
            result += char
    return result


def calculate_psnr(image1_path, image2_path):
    # Baca gambar
    img1 = plt.imread(image1_path).astype(np.float64)
    img2 = plt.imread(image2_path).astype(np.float64)

    # Pastikan gambar memiliki ukuran yang sama
    if img1.shape != img2.shape:
        raise ValueError("Gambar harus memiliki dimensi yang sama")

    # Normalisasi nilai piksel jika diperlukan (0-1 -> 0-255)
    if img1.max() <= 1.0:
        img1 *= 255.0
    if img2.max() <= 1.0:
        img2 *= 255.0

    # Hitung MSE
    mse = np.mean((img1 - img2) ** 2)

    # Format MSE agar tidak menggunakan notasi eksponensial
    formatted_mse = float("{:.8f}".format(mse))

    # Jika MSE nol (gambar identik), PSNR tak terhingga
    if mse == 0:
        return float('inf'), formatted_mse

    # Hitung PSNR dengan rumus 10 * log10(MAX^2 / MSE)
    max_pixel = 255.0
    psnr = 10 * log10(max_pixel ** 2 / mse)
    print(f"Max Pixel: {255.0}")
    print(f"MSE: {mse}")
    print(f"PSNR: {psnr}")
    return float("{:.2f}".format(psnr)), formatted_mse



@app.route('/encode', methods=['POST'])
def encode():
    image = request.files['image']
    message = request.form['message']
    shift = int(request.form['shift'])

    if image and message:
        try:
            # Encode pesan ke format biner dan SGL
            encrypted_message = cesar_cipher(message, shift, encrypt=True)
            binary_message = sgl_to_bin(encrypted_message)
            sgl_message = bin_to_sgl(binary_message)

            # Sembunyikan pesan di dalam gambar
            hidden_image = lsb.hide(image, binary_message)
            image_path = os.path.join('static', image.filename)
            
            # Simpan gambar tersembunyi ke folder static
            hidden_image.save(image_path)

            # Kembalikan JSON dengan informasi tambahan
            return jsonify({
                "image_path": f"/static/{image.filename}",
                "message": "Pesan telah disembunyikan",
                "original_message": message,
                "encrypted_message": encrypted_message,
                "sgl_message": sgl_message
            })
        except ValueError as e:
            return jsonify({"message": str(e)})
    return jsonify({"message": "Terjadi kesalahan!"})



@app.route('/decode', methods=['POST'])
def decode():
    image = request.files['image']
    shift = int(request.form['shift'])
    
    if image:
        binary_message = lsb.reveal(image)
        if binary_message:
            cipher_text = ''.join(bin_to_char(binary_message[i:i+8]) for i in range(0, len(binary_message), 8))
            decoded_message = cesar_cipher(cipher_text, shift, encrypt=False)
            return jsonify({"decoded_message": decoded_message})
    return jsonify({"message": "Tidak ada pesan tersembunyi dalam gambar!"})

@app.route('/calculate', methods=['POST'])
def calculate():
    original_image = request.files['original_image']
    stego_image = request.files['stego_image']

    if original_image and stego_image:
        original_path = os.path.join('static', original_image.filename)
        stego_path = os.path.join('static', stego_image.filename)

        original_image.save(original_path)
        stego_image.save(stego_path)

        # Hitung PSNR dan MSE
        try:
            psnr, mse = calculate_psnr(original_path, stego_path)
            return jsonify({"psnr": psnr, "mse": mse})
        except ValueError as e:
            return jsonify({"message": str(e)})
    return jsonify({"message": "Terjadi kesalahan!"})

if __name__ == '__main__':
    app.run(debug=True)
