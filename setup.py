import re

from setuptools import setup, find_packages

with open("requirements.txt", encoding = "utf-8") as r:
    requires = [i.strip() for i in r]

with open("WebSite2PDF/__init__.py", encoding = "utf-8") as f:
    version = re.findall(r"__version__ = \"(.+)\"", f.read())[0]

with open("README.md", encoding = "utf-8") as f:
    readme = f.read()

setup(
    name = "WebSite2PDF",
    version = version,
    description = "Simple and Fast Python framework to convert HTML files or Web Site to PDF",
    long_description = readme,
    long_description_content_type = "text/markdown",
    url = "https://github.com/uNickz/WebSite2PDF",
    download_url = "https://github.com/uNickz/WebSite2PDF/releases/latest",
    author = "uNickz",
    author_email = "unickz.dev@gmail.com",
    license = "LGPLv3",
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    keywords = "python file html site website pdf converter convert",
    project_urls = {
        "Tracker": "https://github.com/uNickz/WebSite2PDF/issues",
        "Source": "https://github.com/uNickz/WebSite2PDF",
        "Documentation": "https://github.com/uNickz/WebSite2PDF/blob/main/README.md",
    },
    python_requires = ">=3.7",
    packages = find_packages(),
    install_requires = requires,
)