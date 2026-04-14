"""
MVP: Split a PDF into chapters based on its Table of Contents (TOC) metadata.
Source: Google Drive public file (hardcoded).
Usage: python pdf_split_toc.py
"""
import io
import re
import sys
import tempfile
from pathlib import Path
import gdown
import pypdf

DRIVE_URL = "https://drive.google.com/file/d/1dq3-FP7QtmSQaed8cR6JWkYcOcL0ARCR/view?usp=drivesdk"


def extract_file_id(share_url):
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", share_url)
    if not match:
        raise ValueError("Cannot extract file ID from URL")
    return match.group(1)


def download_pdf(share_url):
    file_id = extract_file_id(share_url)
    print(f"Downloading from Google Drive (id={file_id})...")
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name
    gdown.download(id=file_id, output=tmp_path, quiet=False)
    data = Path(tmp_path).read_bytes()
    Path(tmp_path).unlink()
    print(f"Downloaded {len(data) / 1024:.1f} KB")
    return io.BytesIO(data), file_id


def get_toc(reader):
    entries = []

    def walk(outline):
        for item in outline:
            if isinstance(item, list):
                walk(item)
            else:
                try:
                    page_idx = reader.get_destination_page_number(item)
                    entries.append((item.title, page_idx))
                except Exception:
                    pass

    walk(reader.outline)
    return entries


def split_pdf(pdf_stream, name):
    reader = pypdf.PdfReader(pdf_stream)
    total_pages = len(reader.pages)

    toc = get_toc(reader)
    if not toc:
        print("No TOC found in this PDF.")
        sys.exit(1)

    print(f"Found {len(toc)} chapters:")
    for title, page in toc:
        print(f"  p{page + 1:>4}  {title}")

    out_dir = Path(name + "_chapters")
    out_dir.mkdir(exist_ok=True)

    for i, (title, start) in enumerate(toc):
        end = toc[i + 1][1] if i + 1 < len(toc) else total_pages

        writer = pypdf.PdfWriter()
        for p in range(start, end):
            writer.add_page(reader.pages[p])

        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title).strip()
        out_file = out_dir / f"{i+1:02d}_{safe_title}.pdf"
        with open(out_file, "wb") as f:
            writer.write(f)
        print(f"  -> {out_file}  ({end - start} pages)")

    print(f"\nDone. Files saved in '{out_dir}/'")


if __name__ == "__main__":
    pdf_stream, file_id = download_pdf(DRIVE_URL)
    split_pdf(pdf_stream, file_id)
