"""
Modulo per compressione automatica file all'upload.
Supporta: immagini (JPG/PNG), PDF, Office (XLSX/DOCX/PPTX).
"""
import io
import zipfile
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Soglia minima per provare la compressione (file molto piccoli non vale la pena)
MIN_SIZE_TO_COMPRESS = 100 * 1024  # 100 KB

# Dimensione massima immagini (downsampling)
MAX_IMAGE_DIMENSION = 1920  # pixel lato lungo
JPEG_QUALITY = 75  # 0-100


# ============================================================
# IMAGES (JPG/PNG/WebP)
# ============================================================
def compress_image(data: bytes, filename: str) -> Tuple[bytes, str]:
    """Comprime immagine: resize + ricompressione JPEG."""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(data))

        # Conversione RGBA -> RGB (per JPEG)
        if img.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize se troppo grande
        w, h = img.size
        if max(w, h) > MAX_IMAGE_DIMENSION:
            ratio = MAX_IMAGE_DIMENSION / max(w, h)
            new_size = (int(w * ratio), int(h * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        # Salva come JPEG ottimizzato
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        compressed = out.getvalue()

        # Cambia estensione se era PNG
        if filename.lower().endswith((".png", ".webp", ".bmp", ".tiff")):
            new_name = filename.rsplit(".", 1)[0] + ".jpg"
        else:
            new_name = filename

        return compressed, new_name
    except Exception as e:
        logger.warning(f"Compressione immagine fallita: {e}")
        return data, filename


# ============================================================
# PDF
# ============================================================
def compress_pdf(data: bytes, filename: str) -> Tuple[bytes, str]:
    """Comprime PDF: rimuove oggetti inutili + compressione stream + downsampling immagini interne."""
    try:
        import pikepdf

        out = io.BytesIO()
        with pikepdf.open(io.BytesIO(data)) as pdf:
            # Comprime immagini interne
            for page in pdf.pages:
                try:
                    images = page.images
                    for name, raw_image in images.items():
                        try:
                            pdfimg = pikepdf.PdfImage(raw_image)
                            pil_img = pdfimg.as_pil_image()

                            # Resize se troppo grande
                            w, h = pil_img.size
                            if max(w, h) > MAX_IMAGE_DIMENSION:
                                ratio = MAX_IMAGE_DIMENSION / max(w, h)
                                pil_img = pil_img.resize(
                                    (int(w * ratio), int(h * ratio)),
                                    resample=1  # Image.LANCZOS
                                )

                            if pil_img.mode in ("RGBA", "P", "LA"):
                                pil_img = pil_img.convert("RGB")

                            buf = io.BytesIO()
                            pil_img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)

                            # Sostituisce immagine nel PDF
                            raw_image.write(buf.getvalue(), filter=pikepdf.Name("/DCTDecode"))
                        except Exception as ex:
                            logger.debug(f"Skip immagine PDF: {ex}")
                except Exception as ex:
                    logger.debug(f"Skip pagina: {ex}")

            # Salva con compressione massima
            pdf.save(
                out,
                compress_streams=True,
                stream_decode_level=pikepdf.StreamDecodeLevel.generalized,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
                linearize=False,
            )
        return out.getvalue(), filename
    except Exception as e:
        logger.warning(f"Compressione PDF fallita: {e}")
        return data, filename


# ============================================================
# OFFICE (XLSX/DOCX/PPTX) — sono ZIP internamente
# ============================================================
def compress_office(data: bytes, filename: str) -> Tuple[bytes, str]:
    """Comprime file Office ricomprimendo le immagini interne (media folder)."""
    try:
        from PIL import Image

        out_buffer = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(data), 'r') as zin:
            with zipfile.ZipFile(out_buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
                for item in zin.namelist():
                    content = zin.read(item)

                    # Comprimi immagini interne (xl/media/, word/media/, ppt/media/)
                    if "/media/" in item and item.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif")
                    ):
                        try:
                            img = Image.open(io.BytesIO(content))
                            if img.mode in ("RGBA", "P", "LA"):
                                img = img.convert("RGB")

                            w, h = img.size
                            if max(w, h) > MAX_IMAGE_DIMENSION:
                                ratio = MAX_IMAGE_DIMENSION / max(w, h)
                                img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

                            buf = io.BytesIO()
                            img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
                            content = buf.getvalue()
                        except Exception as ex:
                            logger.debug(f"Skip immagine Office {item}: {ex}")

                    zout.writestr(item, content)

        return out_buffer.getvalue(), filename
    except Exception as e:
        logger.warning(f"Compressione Office fallita: {e}")
        return data, filename


# ============================================================
# DISPATCHER
# ============================================================
def compress_file(data: bytes, filename: str, content_type: str = "") -> Tuple[bytes, str, dict]:
    """
    Dispatcher principale: identifica il tipo e applica la compressione.
    Ritorna: (bytes_compressi, nuovo_filename, info_compressione)
    """
    original_size = len(data)

    # File piccoli: skip
    if original_size < MIN_SIZE_TO_COMPRESS:
        return data, filename, {
            "compressed": False,
            "reason": "file troppo piccolo",
            "original_size": original_size,
            "final_size": original_size,
        }

    ext = filename.lower().split(".")[-1] if "." in filename else ""

    # Routing per tipo
    if ext in ["jpg", "jpeg", "png", "webp", "bmp", "tiff", "gif"]:
        new_data, new_name = compress_image(data, filename)
    elif ext == "pdf":
        new_data, new_name = compress_pdf(data, filename)
    elif ext in ["xlsx", "docx", "pptx"]:
        new_data, new_name = compress_office(data, filename)
    else:
        return data, filename, {
            "compressed": False,
            "reason": f"tipo non supportato: {ext}",
            "original_size": original_size,
            "final_size": original_size,
        }

    new_size = len(new_data)
    saved_pct = round((1 - new_size / original_size) * 100, 1) if original_size > 0 else 0

    # Se la compressione ha PEGGIORATO, restituisci l'originale
    if new_size >= original_size:
        return data, filename, {
            "compressed": False,
            "reason": "compressione non efficace",
            "original_size": original_size,
            "final_size": original_size,
        }

    return new_data, new_name, {
        "compressed": True,
        "original_size": original_size,
        "final_size": new_size,
        "saved_bytes": original_size - new_size,
        "saved_pct": saved_pct,
    }
