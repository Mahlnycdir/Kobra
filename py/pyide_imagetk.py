"""Ersatz fuer PIL.ImageTk: Pillow-Bilder in tkinter-Widgets anzeigen."""
import io
import tkinter


def _png(image):
    buf = io.BytesIO()
    im = image
    if im.mode not in ("RGB", "RGBA", "L", "LA", "P", "1"):
        im = im.convert("RGBA")
    im.save(buf, format="PNG", compress_level=1)
    return buf.getvalue()


class PhotoImage(tkinter.PhotoImage):
    def __init__(self, image=None, size=None, **kw):
        if image is None and "file" in kw:
            from PIL import Image
            image = Image.open(kw.pop("file"))
            image.load()
        elif image is None and "data" in kw:
            from PIL import Image
            data = kw.pop("data")
            image = Image.open(io.BytesIO(data))
            image.load()
        if isinstance(image, str):
            from PIL import Image
            image = Image.new(image, size or (1, 1))
        self._pil = image
        if image is not None:
            tkinter.PhotoImage.__init__(self, data=_png(image), **kw)
        else:
            tkinter.PhotoImage.__init__(self, **kw)

    def paste(self, im, box=None):
        self._pil = im
        self.configure(data=_png(im))

    def __str__(self):
        return self.name


class BitmapImage(PhotoImage):
    pass


def getimage(photo):
    return getattr(photo, "_pil", None)
