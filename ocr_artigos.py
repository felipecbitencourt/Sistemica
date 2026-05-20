"""
Extrai texto de PDFs escaneados via EasyOCR.
Requer: pip install easyocr  (instala PyTorch e o modelo automaticamente)
        PyMuPDF já instalado (fitz)

Uso: python ocr_artigos.py
Saída: Artigos_md/<nome>.md  (substitui arquivos vazios gerados antes)

Nota: na primeira execução o EasyOCR baixa o modelo (~200 MB).
"""

import fitz          # PyMuPDF – renderiza páginas como imagem
import pathlib
import io
import numpy as np
from PIL import Image

# ── Configuração ────────────────────────────────────────────────────────────

BASE = pathlib.Path(r"C:\Users\felip\Códigos\sistemica")

LANGS     = ['pt', 'en']   # português + inglês (cobrem referências mistas)
DPI       = 200            # 200 DPI é suficiente para texto impresso
THRESHOLD = 50             # mínimo de caracteres para considerar texto nativo

FOLDERS = [
    (BASE / "Artigos",  BASE / "Artigos_md"),
    (BASE / "Slides",   BASE / "Slides_md"),
]

# ── Inicializa EasyOCR (carrega modelo uma vez) ──────────────────────────────

def init_reader():
    try:
        import easyocr
    except ImportError:
        print("✗ EasyOCR não encontrado!\n\n  Instale com:  pip install easyocr\n")
        return None
    print("Carregando modelo EasyOCR (pode demorar na primeira vez)...")
    reader = easyocr.Reader(LANGS, gpu=False)
    print("✓ Modelo carregado\n")
    return reader

# ── Função principal ─────────────────────────────────────────────────────────

def ocr_pdf(pdf_path: pathlib.Path, out_path: pathlib.Path, reader, dpi: int):
    doc = fitz.open(str(pdf_path))
    n   = doc.page_count
    md_lines = [f"# {pdf_path.stem}\n\n"]

    for i in range(n):
        page = doc[i]

        # Tenta texto nativo primeiro (rápido, sem OCR)
        native = page.get_text("text").strip()
        if len(native) > THRESHOLD:
            md_lines.append(f"\n---\n<!-- página {i+1} -->\n\n{native}\n")
            print(f"  p{i+1}/{n} [nativo]", end="\r", flush=True)
            continue

        # Sem texto nativo → renderizar como imagem e fazer OCR
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        img_array = np.array(img)

        results = reader.readtext(img_array, detail=0, paragraph=True)
        text = "\n".join(results).strip()

        if text:
            md_lines.append(f"\n---\n<!-- página {i+1} -->\n\n{text}\n")
        else:
            md_lines.append(f"\n---\n<!-- página {i+1} — sem texto detectado -->\n")

        print(f"  p{i+1}/{n} [ocr]   ", end="\r", flush=True)

    doc.close()
    out_path.write_text("".join(md_lines), encoding="utf-8")
    print()
    return n


def main():
    reader = init_reader()
    if reader is None:
        return

    for src_dir, out_dir in FOLDERS:
        out_dir.mkdir(exist_ok=True)
        pdfs = sorted(src_dir.glob("*.pdf"))
        if not pdfs:
            continue

        print(f"── {src_dir.name} ({len(pdfs)} arquivos) ──────────────────")
        for pdf in pdfs:
            out = out_dir / (pdf.stem + ".md")

            # Pula se já tiver conteúdo substancial (> 500 chars)
            if out.exists() and out.stat().st_size > 500:
                print(f"  [ok] {pdf.name} (já extraído)")
                continue

            print(f"  → {pdf.name} ...")
            pages = ocr_pdf(pdf, out, reader, DPI)
            size  = out.stat().st_size
            print(f"  ✓ {pages} págs | {size // 1024} KB -> {out.name}")

        print()

    print("Concluído! Arquivos em Artigos_md/ e Slides_md/")


if __name__ == "__main__":
    main()
