from .. import WebSite2PDF

if __name__ == "__main__":
    c = WebSite2PDF.Client()
    pdf_path = c.pdf(url = "https://pypi.org", filename = "file_name.pdf")
    print(f"PDF Created! Path: {pdf_path}")