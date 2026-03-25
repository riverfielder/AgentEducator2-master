import urllib.request
import zlib
import base64
import sys
import ssl

def generate_png(puml_file, output_file):
    with open(puml_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Kroki URL-safe base64 + zlib
    compressed = zlib.compress(text.encode('utf-8'), 9)
    encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
    url = f"https://kroki.io/plantuml/png/{encoded}"
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response, open(output_file, 'wb') as out_file:
            out_file.write(response.read())
        print(f"Generated {output_file} successfully via Kroki.")
    except Exception as e:
        print(f"Failed to generate {output_file}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_plantuml.py <input.puml> <output.png>")
        sys.exit(1)
    
    generate_png(sys.argv[1], sys.argv[2])
