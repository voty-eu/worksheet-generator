from fastapi import FastAPI, Response
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import random
import io

app = FastAPI()

PAGE_WIDTH, PAGE_HEIGHT = A4

def generate_expression():
    while True:
        a = random.randint(0, 10)
        b = random.randint(0, 10)
        c = a + b
        d = a - b + random.randint(0, 2)

        options = [
            (f"{a} + {b} = <i>x</i>", a + b),
            (f"{a} + <i>x</i> = {c}", c - a),
            (f"<i>x</i> + {b} = {c}", c - b),
            (f"{a} - {b} = <i>x</i>", a - b),
            (f"{a} - <i>x</i> = {c}", a - c),
            (f"<i>x</i> - {b} = {c}", c + b),
            (f"{a} - {b} + <i>x</i> = {d}", d - (a - b)),
            (f"{a} + {b} - <i>x</i> = {d}", a + b - d),
            (f"<i>x</i> - {b} + {a} = {d}", d - (a - b)),
            (f"{a} + <i>x</i> - {b} = {d}", d - (a + b)),
            (f"<i>x</i> + {b} - {a} = {d}", d + a - b),
            (f"{a} - <i>x</i> + {b} = {d}", d + (a - b)),

            (f"<i>x</i> = {a} + {b}", a + b),
            (f"{c} = <i>x</i> + {a}", c - a),
            (f"{c} = {a} + <i>x</i>", c - a),
            (f"<i>x</i> = {a} - {b}", a - b),
            (f"{c} = {a} - <i>x</i>", a - c),
            (f"{c} = <i>x</i> - {b}", c + b),
            (f"{d} = {a} - {b} + <i>x</i>", d - (a - b)),
            (f"{d} = {a} + <i>x</i> - {b}", a + b - d),
            (f"{d} = <i>x</i> - {b} + {a}", d - (a - b)),
            (f"{d} = {a} + <i>x</i> - {b}", d - (a + b)),
            (f"{d} = <i>x</i> + {b} - {a}", d + a - b),
            (f"{d} = {a} - <i>x</i> + {b}", d + (a - b)),

        ]

        expr, result = random.choice(options)

        if 0 <= result <= 100 and all(n >= 0 for n in [a, b, c, d]):
            return expr, result

def draw_number_line(c, x, y, width, result):
    segments = random.choice([3, 4, 5])
    tick_step = random.choice([2, 5, 10])

    # vyber začátek tak, aby výsledek byl jedním z ticků
    result_index = random.randint(0, segments)
    start = result - result_index * tick_step
    if start < 0:
        start = 0
        result_index = (result - start) // tick_step

    end = start + segments * tick_step
    step_px = width / segments

    c.line(x, y, x + width, y)

    for i in range(segments + 1):
        tick_x = x + i * step_px
        tick_value = start + i * tick_step
        c.line(tick_x, y - 3, tick_x, y + 3)

        # popsat jen krajní ticks
        if i == 0 or i == segments:
            c.setFont("Helvetica", 10)
            c.drawString(tick_x - 5, y - 15, str(tick_value))


def create_pdf(num_problems=11):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    margin = 20 * mm
    total_width = PAGE_WIDTH - 2 * margin
    col_widths = [total_width * w for w in (0.35, 0.25, 0.4)]
    row_height = 22 * mm
    start_y = PAGE_HEIGHT - margin - row_height
    line_counter = 0

    expr_style = ParagraphStyle(
        name='Expr',
        fontName='Helvetica',
        fontSize=14,
        leading=16,
        alignment=TA_LEFT
    )

    for i in range(num_problems):
        y = start_y - line_counter * row_height
        if y < margin:
            c.showPage()
            line_counter = 0
            y = start_y

        expr, result = generate_expression()

        x_expr = margin
        x_result = x_expr + col_widths[0]
        x_line = x_result + col_widths[1]

        # --- Výraz v levém sloupci ---
        para = Paragraph(expr, expr_style)
        para.wrapOn(c, col_widths[0], row_height)
        para.drawOn(c, x_expr, y - 4)

        # --- Výsledkový rámeček s x = ---
        c.setFont("Helvetica-Oblique", 12)
        c.drawString(x_result, y, f"x =   {result}")
        box_offset = c.stringWidth("x = ") + 2
        box_width = (col_widths[1] - 10) / 2 + 10
        box_height = 24
        c.rect(x_result + box_offset, y - 5, box_width, box_height)


        # --- Číselná osa ---
        draw_number_line(c, x_line, y + 5, col_widths[2] - 10, result)

        line_counter += 1

    c.save()
    buffer.seek(0)
    return buffer

@app.get("/worksheet")
def get_math_worksheet():
    pdf_buffer = create_pdf()
    return Response(content=pdf_buffer.read(), media_type="application/pdf", headers={
        "Content-Disposition": "inline; filename=worksheet.pdf"
    })
