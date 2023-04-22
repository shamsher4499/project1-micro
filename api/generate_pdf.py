from io import BytesIO
from django.http import HttpResponse
from reportlab.pdfgen import canvas

def generate_pdf():
    # Create a file-like buffer to receive PDF data.
    buffer = BytesIO()

    # Create the PDF object, using the BytesIO object as its "file."
    p = canvas.Canvas(buffer)

    data = 'shamsher'
    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    p.drawString(100, 100, f"Hello {data} dsfds dsfsdf dsf dsfsdfsdf sdfdsf dsfdsf dsf sdf dsf sdf dsfds f dsf dsf sdfds fsdf.")

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    buffer.seek(0)
    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    return buffer