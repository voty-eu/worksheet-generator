from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import random
import io
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

app = FastAPI()

PAGE_WIDTH, PAGE_HEIGHT = A4

pdfmetrics.registerFont(TTFont("CMUSans", "/usr/share/fonts/truetype/cmu/cmunss.ttf"))
pdfmetrics.registerFont(TTFont("CMUSans-Bold", "/usr/share/fonts/truetype/cmu/cmunsx.ttf"))
pdfmetrics.registerFont(TTFont("CMUSans-Italic", "/usr/share/fonts/truetype/cmu/cmunsi.ttf"))
pdfmetrics.registerFont(TTFont("CMUSans-BoldItalic", "/usr/share/fonts/truetype/cmu/cmunso.ttf"))

registerFontFamily(
    'CMUSans',
    normal='CMUSans',
    bold='CMUSans-Bold',
    italic='CMUSans-Italic',
    boldItalic='CMUSans-BoldItalic'
)


def generate_expression():
    while True:
        a = random.randint(0, 20)
        b = random.randint(0, 20)
        c = a + b
        d = a - b + random.randint(0, 20)

        options = [
            (f"{a} + {b} = <b><i>x</i></b>", a + b),
            (f"{a} + <b><i>x</i></b> = {c}", c - a),
            (f"<b><i>x</i></b> + {b} = {c}", c - b),
            (f"{a} - {b} = <b><i>x</i></b>", a - b),
            (f"{a} - <b><i>x</i></b> = {c}", a - c),
            (f"<b><i>x</i></b> - {b} = {c}", c + b),
            (f"{a} - {b} + <b><i>x</i></b> = {d}", d - (a - b)),
            (f"{a} + {b} - <b><i>x</i></b> = {d}", a + b - d),
            (f"<b><i>x</i></b> - {b} + {a} = {d}", d - (a - b)),
            (f"{a} + <b><i>x</i></b> - {b} = {d}", d - (a + b)),
            (f"<b><i>x</i></b> + {b} - {a} = {d}", d + a - b),
            (f"{a} - <b><i>x</i></b> + {b} = {d}", d + (a - b)),

            (f"<b><i>x</i></b> = {a} + {b}", a + b),
            (f"{c} = <b><i>x</i></b> + {a}", c - a),
            (f"{c} = {a} + <b><i>x</i></b>", c - a),
            (f"<b><i>x</i></b> = {a} - {b}", a - b),
            (f"{c} = {a} - <b><i>x</i></b>", a - c),
            (f"{c} = <b><i>x</i></b> - {b}", c + b),
            (f"{d} = {a} - {b} + <b><i>x</i></b>", d - (a - b)),
            (f"{d} = {a} + <b><i>x</i></b> - {b}", a + b - d),
            (f"{d} = <b><i>x</i></b> - {b} + {a}", d - (a - b)),
            (f"{d} = {a} + <b><i>x</i></b> - {b}", d - (a + b)),
            (f"{d} = <b><i>x</i></b> + {b} - {a}", d + a - b),
            (f"{d} = {a} - <b><i>x</i></b> + {b}", d + (a - b)),

        ]

        expr, result = random.choice(options)

        if 0 <= result <= 100 and all(n >= 0 for n in [a, b, c, d]):
            return expr, result


def draw_number_line(c, x, y, width, result):
    segment_candidates = [1, 2, 3, 4, 5, 10]
    segments = random.choice([3, 4, 5])
    tick_step = random.choice([s for s in segment_candidates if result % s == 0])

    # vyber začátek tak, aby výsledek byl jedním z ticků
    result_index = random.randint(0, segments - 1)

    c.line(x, y, x + width, y)

    start = result - result_index * tick_step

    try:
        first_mark_index = random.choice(
            [i for i in range(0, segments) if i != result_index and start + i * tick_step >= 0])
        second_mark_index = random.choice(
            [i for i in range(first_mark_index + 1, segments + 1) if i != result_index] + [segments])
    except IndexError as e:
        # fallback
        first_mark_index = max(result_index - 1, 0)
        second_mark_index = segments

    step_px = width / segments
    for i in range(segments + 1):
        tick_x = x + i * step_px
        tick_value = start + i * tick_step
        c.line(tick_x, y - 3, tick_x, y + 3)

        # popsat jen krajní ticks
        if i == first_mark_index or i == second_mark_index:
            c.setFont("CMUSans", 10)
            tick_str = str(tick_value)
            c.drawString(tick_x - c.stringWidth(tick_str) / 2, y - 15, tick_str)


def create_pdf(num_problems=12):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setTitle("Matematika – pracovní list")
    c.setAuthor('voty@voty.eu')
    c.setSubject("Sčítání a odčítání malých čísel")
    c.setKeywords("matematika, děti, pracovní list, příklady, PDF")
    c.setCreator("http://edu.voty.eu")


    margin = 20 * mm
    total_width = PAGE_WIDTH - 2 * margin
    col_widths = [total_width * w for w in (0.35, 0.25, 0.4)]
    row_height = 20 * mm
    start_y = PAGE_HEIGHT - margin - row_height
    line_counter = 0

    expr_style = ParagraphStyle(
        name='Expr',
        fontName='CMUSans',
        fontSize=14,
        leading=16,
        alignment=TA_LEFT
    )

    print(c.getAvailableFonts())

    c.line(margin, PAGE_HEIGHT - margin * 1.1, PAGE_WIDTH - margin, PAGE_HEIGHT - margin * 1.1)
    c.setFont("CMUSans", 10)
    c.drawString(margin, PAGE_HEIGHT - margin * 1.1 + 5, "Sčítání a odčítání (malá čísla)")

    results = []

    for i in range(num_problems):
        y = start_y - line_counter * row_height
        if y < margin:
            c.showPage()
            line_counter = 0
            y = start_y

        expr, result = generate_expression()
        results.append(result)

        x_expr = margin
        x_result = x_expr + col_widths[0]
        x_line = x_result + col_widths[1]

        # --- Výraz v levém sloupci ---
        para = Paragraph(expr, expr_style)
        para.wrapOn(c, col_widths[0], row_height)
        para.drawOn(c, x_expr, y - 4)

        # --- Výsledkový rámeček s x = ---
        c.setFont("CMUSans-Italic", 12)
        c.drawString(x_result, y, f"x = ")
        box_offset = c.stringWidth("x = ") + 2
        box_width = (col_widths[1] - 10) / 2 + 10
        box_height = 24
        c.rect(x_result + box_offset, y - 7, box_width, box_height)

        # --- Číselná osa ---
        draw_number_line(c, x_line, y + 5, col_widths[2] - 10, result)

        line_counter += 1

    c.line(margin, margin * 1.1, PAGE_WIDTH - margin, margin * 1.1)
    c.setFont("CMUSans", 8)
    c.drawString(margin, margin * 0.9, "Generated by Math Worksheet Generator http://edu.voty.eu")
    c.setFont("CMUSans-Italic", 5)
    c.drawString(150 * mm, margin / 2, f"Results: {', '.join(map(str, results))}")

    c.save()
    buffer.seek(0)
    return buffer


@app.get("/worksheet")
def get_math_worksheet():
    pdf_buffer = create_pdf()

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="matematika.pdf"'}
    )