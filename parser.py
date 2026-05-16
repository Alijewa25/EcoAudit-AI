import fitz  # PyMuPDF

class PDFProcessor:
    """PDF text extractor optimized for ESG auditing (invoices & reports)."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract_text(self) -> str:
        """Extracts text while maintaining layout as much as possible."""
        try:
            full_text = []
            with fitz.open(self.file_path) as doc:
                for page in doc:
                    # 'blocks' rejimi mətnin strukturunu (paraqraf və cədvəl ardıcıllığını) 
                    # düz mətndən daha yaxşı qoruyur.
                    blocks = page.get_text("blocks")
                    # Blokları yuxarıdan aşağı, soldan sağa sıralayırıq
                    # blocks entries are tuples like (x0, y0, x1, y1, "text", ...)
                    blocks.sort(key=lambda b: (b[1], b[0]))

                    for b in blocks:
                        # b[4] is the textual content for the block
                        text = b[4] if len(b) > 4 else ''
                        full_text.append(text)

            # Mətnləri təmizləyirik və birləşdiririk
            final_content = "\n".join(full_text).strip()

            if not final_content:
                # Əgər mətn yoxdursa, böyük ehtimalla sənəd skan olunub (şəkil formatındadır)
                return "Parsing Error: The PDF appears to be an image. Please provide a searchable PDF (OCR)."

            return final_content

        except Exception as exc:
            print(f"⚠️ PDF Extraction Error: {exc}")
            return f"Parsing Error: {str(exc)}"

    def get_metadata(self) -> dict:
        """Sənəd haqqında əlavə məlumatları (tarix, müəllif) çıxarır."""
        try:
            with fitz.open(self.file_path) as doc:
                return doc.metadata
        except:
            return {}