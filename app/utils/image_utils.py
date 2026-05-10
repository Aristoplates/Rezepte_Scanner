from PIL import Image
import io

def resize_image(image_bytes: bytes, max_size: int=2048) -> bytes:
    """
    Resize image if it exceeds max_size in either dimension.
    Returns optimized JPEG bytes.
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Convert RGBA/P to RGB for JPEG compatibility
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Resize if too large
    w, h = img.size
    if w > max_size or h > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return buf.getvalue()


def get_image_preview(imeage_bytes: bytes, max_size: int = 400) -> bytes:
    """Generate a small preview thumbnail"""
    img = Image.open(io.BytesIO(imeage_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    return buf.getvalue()