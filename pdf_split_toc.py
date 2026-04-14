"""
MVP: Split a PDF into chapters based on its Table of Contents (TOC) metadata.
Usage: python pdf_split_toc.py input.pdf
"""
import sys
from pathlib import Path
import pypdf


def get_toc(reader):
    """Extract TOC entries as list of (title, page_index)."""
    entries = []

    def walk(outline, reader):
        for item in outline:
            if isinstance(item, list):
                walk(item, reader)
            else:
                try:
                    page_idx = reader.get_destination_page_number(item)
                    entries.append((item.title, page_idx))
                except Exception:
                    pass

    walk(reader.outline, reader)
    return entries


def split_pdf(input_path):
    reader = pypdf.PdfReader(input_path)
    total_pages = len(reader.pages)

    toc = get_toc(reader)
    if not toc:
        print("No TOC found in this PDF.")
        sys.exit(1)

    print(f"Found {len(toc)} chapters:")
    for title, page in toc:
        print(f"  p{page + 1:>4}  {title}")

    out_dir = Path(input_path).stem + "_chapters"
    Path(out_dir).mkdir(exist_ok=True)

    for i, (title, start) in enumerate(toc):
        end = toc[i + 1][1] if i + 1 < len(toc) else total_pages

        writer = pypdf.PdfWriter()
        for p in range(start, end):
            writer.add_page(reader.pages[p])

        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title).strip()
        out_file = Path(out_dir) / f"{i+1:02d}_{safe_title}.pdf"
        with open(out_file, "wb") as f:
            writer.write(f)
        print(f"  -> {out_file}  ({end - start} pages)")

    print(f"\nDone. Files saved in '{out_dir}/'")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pdf_split_toc.py <file.pdf>")
        sys.exit(1)
    split_pdf(sys.argv[1])
