def to_pdf(df, title):
    pdf = FPDF()
    pdf.set_auto_page_break(True, 10)
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(0, 10, title, ln=True, align="C")
    pdf.ln(4)
    pdf.set_font("Arial", size=10)
    cols = df.columns
    # header
    for c in cols:
        pdf.cell(40, 8, c, border=1)
    pdf.ln()
    # data
    for _, row in df.iterrows():
        for c in cols:
            pdf.cell(40, 8, str(row[c]), border=1)
        pdf.ln()
    byte = io.BytesIO()
    pdf.output(byte)
    return byte.getvalue()
