import WebSite2PDF

if __name__ == "__main__":
    c = WebSite2PDF.Client(
        pdfOptions = {
            "printBackground": True,
            "preferCSSPageSize": True,
        },
    )
    pdf_path = c.pdf(url = "https://pypi.org", filename = "{title}.pdf")
    print(f"PDF Created! Path: {pdf_path}")