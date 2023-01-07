# WebSite2PDF
> Simple and Fast Python framework to convert HTML files or Web Site to PDF

### Installing with pip

``` bash
pip3 install WebSite2PDF
```
or
``` bash
pip3 install git+https://github.com/uNickz/WebSite2PDF
```

### Installing with python

``` bash
python3 -m pip install git+https://github.com/uNickz/WebSite2PDF
```

## Example

### Using a url

``` python
import WebSite2PDF

url = "https://pypi.org"

c = WebSite2PDF.Client()
with open("file_name.pdf", "wb+") as file:
    file.write(c.pdf(url))
```
or
``` python
import WebSite2PDF

url = "https://pypi.org"

c = WebSite2PDF.Client()
c.pdf(url, filename = "file_name.pdf")
```

### Using a file HTML

``` python
import WebSite2PDF

file_path = "C:\Users\uNickz\index.html"

c = WebSite2PDF.Client()
with open("file_name.pdf", "wb+") as file:
    file.write(c.pdf(f"file:///{file_path}"))
```
or
``` python
import WebSite2PDF

file_path = "C:\Users\uNickz\index.html"

c = WebSite2PDF.Client()
c.pdf(f"file:///{file_path}", filename = "file_name.pdf")
```

### Using multiple urls or files HTML

``` python
import WebSite2PDF

urls_or_path = ["https://pypi.org", "file:///C:\Users\uNickz\index.html", "https://github.com/"]

c = WebSite2PDF.Client()
c.pdf(urls_or_path, filename = ["pypi.pdf", "index.pdf", "github.pdf"])
```
or
``` python
import WebSite2PDF

urls_or_path = ["https://pypi.org", "file:///C:\Users\uNickz\index.html", "https://github.com/"]
file_name = ["pypi.pdf", "index.pdf", "github.pdf"]

c = WebSite2PDF.Client()
data = c.pdf(urls_or_path)
for name, data in zip(name, data):
    with open(name, "wb+") as file:
        file.write(data)
```

### Using a delay (in seconds) before create PDF

``` python
import WebSite2PDF

url = "https://pypi.org"

c = WebSite2PDF.Client()
c.pdf(url, filename = "file_name.pdf", delay = 3)
```

### Using global [PDF Options](https://github.com/uNickz/WebSite2PDF/blob/main/PDF%20Page%20Options.md)

``` python
import WebSite2PDF

url = "https://pypi.org"

c = WebSite2PDF.Client(
    pdfOptions = {
        "landscape" = True,
        "displayHeaderFooter": True,
        "printBackground": True,
        "preferCSSPageSize": True,
    }
)
c.pdf(url, filename = "file_name.pdf")
```

### Using specific [PDF Options](https://github.com/uNickz/WebSite2PDF/blob/main/PDF%20Page%20Options.md) for a PDF

``` python
import WebSite2PDF

url = "https://pypi.org"

c = WebSite2PDF.Client(
    pdfOptions = {
        "landscape" = True,
        "displayHeaderFooter": True,
        "printBackground": True,
        "preferCSSPageSize": True,
    }
)
c.pdf(url, filename = "file_name.pdf", pdfOptions = {
    "landscape" = False,
    "displayHeaderFooter": True,
})
```

### Using global [Selenium ChromeDriver Options](https://github.com/uNickz/WebSite2PDF/blob/main/Selenium%20ChromeDriver%20Options.md)

``` python
import WebSite2PDF

url = "https://pypi.org"

c = WebSite2PDF.Client(
    pdfOptions = {
        "landscape" = True,
        "displayHeaderFooter": True,
        "printBackground": True,
        "preferCSSPageSize": True,
    }, seleniumOptions = [
        "--no-sandbox",
        "--headless",
    ]
)
c.pdf(url, filename = "file_name.pdf")
```

### Using specific [Selenium ChromeDriver Options](https://github.com/uNickz/WebSite2PDF/blob/main/Selenium%20ChromeDriver%20Options.md) for a PDF

``` python
import WebSite2PDF

url = "https://pypi.org"

c = WebSite2PDF.Client(
    pdfOptions = {
        "landscape" = True,
        "displayHeaderFooter": True,
        "printBackground": True,
        "preferCSSPageSize": True,
    }, seleniumOptions = [
        "--no-sandbox",
        "--headless",
    ]
)
c.pdf(url, filename = "file_name.pdf", pdfOptions = {
        "landscape" = False,
        "displayHeaderFooter": True,
    }, seleniumOptions = [
        "--no-sandbox",
        "--disable-gpu",
])
```