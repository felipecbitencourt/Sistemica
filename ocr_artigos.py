"""
Extrai texto de PDFs escaneados via Tesseract OCR.
Requer: Tesseract instalado (com pacote de língua 'por')
        pip install pytesseract  (já instalado)
        PyMuPDF já instalado (fitz)

Uso: python ocr_artigos.py
Saída: Artigos_md/<nome>.md  (substitui arquivos vazios gerados antes)
"""

import fitz          # PyMuPDF – renderiza páginas como imagem
import pytesseract
import pathlib
from PIL import Image
import io

# ── Configuração ────────────────────────────────────────────────────────────

BASE = pathlib.Path(r"C:\Users\felip\Códigos\sistemica")

# Ajuste se o Tesseract não estiver no PATH padrão
# Exemplo: pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

LANG      = "por"          # português; use "por+eng" se houver muito inglês
DPI       = 200            # 200 DPI é rápido e suficiente para texto impresso
THRESHOLD = 50             # mínimo de caracteres por página para incluir

# ── Quais pastas/arquivos processar ─────────────────────────────────────────

FOLDERS = [
    (BASE / "Artigos",  BASE / "Artigos_md"),
    (BASE / "Slides",   BASE / "Slides_md"),   # os slides já têm texto, mas
                                                # esta linha re-tenta os vazios
]

# ── Função principal ─────────────────────────────────────────────────────────

def ocr_pdf(pdf_path: pathlib.Path, out_path: pathlib.Path, lang: str, dpi: int):
    """Converte cada página do PDF em imagem e aplica OCR."""
    doc = fitz.open(str(pdf_path))
    n   = doc.page_count
    md_lines = [f"# {pdf_path.stem}\n\n"]

    for i in range(n):
        page = doc[i]

        # Tenta texto nativo primeiro (rápido)
        native = page.get_text("text").strip()
        if len(native) > THRESHOLD:
            md_lines.append(f"\n---\n<!-- página {i+1} -->\n\n{native}\n")
            continue

        # Sem texto nativo → renderizar como imagem e fazer OCR
        mat  = fitz.Matrix(dpi / 72, dpi / 72)   # escala para o DPI desejado
        pix  = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
        img  = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img, lang=lang).strip()

        if text:
            md_lines.append(f"\n---\n<!-- página {i+1} -->\n\n{text}\n")
        else:
            md_lines.append(f"\n---\n<!-- página {i+1} — sem texto detectado -->\n")

        print(f"  p{i+1}/{n}", end="\r", flush=True)

    doc.close()
    out_path.write_text("".join(md_lines), encoding="utf-8")
    return n


def main():
    # Verifica se o Tesseract está acessível
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract {version} detectado\n")
    except pytesseract.TesseractNotFoundError:
        print(
            "✗ Tesseract não encontrado!\n\n"
            "  Instale de: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "  Inclua o pacote de língua 'Portuguese' (por) na instalação.\n\n"
            "  Se o instalador estiver em local não-padrão, edite a linha:\n"
            "  pytesseract.pytesseract.tesseract_cmd = r'C:\\caminho\\tesseract.exe'\n"
        )
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

            print(f"  → {pdf.name} ...", end=" ", flush=True)
            pages = ocr_pdf(pdf, out, LANG, DPI)
            size  = out.stat().st_size
            print(f"✓ {pages} págs | {size//1024} KB salvo em {out.name}")

        print()

    print("Concluído! Arquivos em Artigos_md/ e Slides_md/")


if __name__ == "__main__":
    main()
