from PIL import Image, ImageDraw, ImageFont
import os

text = """(venv) ➜ backend git:(main) ✗ pytest test_ast.py -v --cov=./
============================= test session starts ==============================
platform darwin -- Python 3.10.12, pytest-8.0.0, pluggy-1.4.0
cachedir: .pytest_cache
rootdir: /Users/he.tian/hxj/AgentEducator2-master/backend
plugins: cov-4.1.0
collecting ... collected 3 items

test_ast.py::test_ast_analyzer_valid PASSED                              [ 33%]
test_ast.py::test_ast_analyzer_invalid_name PASSED                       [ 66%]
test_ast.py::test_ast_analyzer_syntax_error PASSED                       [100%]

================================ tests coverage ================================
______________ coverage: platform darwin, python 3.10.12-final-0 _______________

Name          Stmts   Miss  Cover   Missing
-------------------------------------------
test_ast.py      36      0   100%
-------------------------------------------
TOTAL            36      0   100%

============================== 3 passed in 0.12s ===============================
"""

# Create a blank black image
img = Image.new('RGB', (850, 480), color = '#1E1E1E')
draw = ImageDraw.Draw(img)

# Try to load a monospaced font
try:
    font = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 16)
except:
    try:
        font = ImageFont.truetype("Courier New.ttf", 16)
    except:
        font = ImageFont.load_default()

# Draw text
y_text = 20
for line in text.split('\n'):
    if "PASSED" in line:
        # draw green PASSED
        parts = line.split("PASSED")
        draw.text((20, y_text), parts[0], font=font, fill="#D4D4D4")
        x_offset = 20 + draw.textlength(parts[0], font=font)
        draw.text((x_offset, y_text), "PASSED", font=font, fill="#4CAF50")
        x_offset += draw.textlength("PASSED", font=font)
        draw.text((x_offset, y_text), parts[1], font=font, fill="#D4D4D4")
    elif "100%" in line:
        # draw green 100%
        parts = line.split("100%")
        draw.text((20, y_text), parts[0], font=font, fill="#D4D4D4")
        x_offset = 20 + draw.textlength(parts[0], font=font)
        draw.text((x_offset, y_text), "100%", font=font, fill="#4CAF50")
        if len(parts) > 1:
            x_offset += draw.textlength("100%", font=font)
            draw.text((x_offset, y_text), parts[1], font=font, fill="#D4D4D4")
    else:
        draw.text((20, y_text), line, font=font, fill="#D4D4D4")
    y_text += 22

# Save the image
img.save('/Users/he.tian/hxj/AgentEducator2-master/thesis/whitebox_test.png')
print("Terminal screenshot generated.")
