#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dosya Türüne Göre Ayır  (PySide6)
=================================
Bir klasördeki dosyaları seçtiğiniz TÜRE (fotoğraf, görsel, 3D baskı dosyası,
video, belge, arşiv, kod ... veya tüm dosyalar) göre filtreleyip, çekim/dosya
tarihine göre yeni klasörlere kopyalar/taşır.

File Sorter by Type  (PySide6)
==============================
Filters files in a folder by TYPE (photo, image/design, 3D-print file, video,
document, archive, code ... or all files) and copies/moves them into new
folders based on capture/file date.

Yeni (1.7): "Türe göre klasörle" düzeni — veri kurtarma çıktıları gibi karışık
yığınları Fotoğraf / Video / Belgeler / … klasörlerine ayırır; uzantısız dosyaları
içeriğinden (sihirli baytlardan) tanır.
New (1.7): "Folder by type" layout — sorts messy data-recovery dumps into
Photos / Videos / Documents / … folders and identifies extensionless files by content.

Gereksinimler / Requirements:
    pip install PySide6 pillow

Çalıştırma / Run:
    python dosya_turune_gore_ayir.py
"""

import os
import shutil
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import (
    QObject, QRectF, QSettings, QSize, Qt, QThread, Signal, Slot,
)
from PySide6.QtGui import (
    QColor, QFont, QPainter, QPainterPath, QPalette, QPen,
)
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListView, QMainWindow,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QRadioButton,
    QScrollArea, QVBoxLayout, QWidget,
)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:  # Pillow yoksa dosya tarihine düşülür
    PIL_AVAILABLE = False

from breeze import (  # ortak Breeze teması (koyu arduvaz + mercan vurgu)
    PALETTES, PathField, Check, Combo, Radio, build_palette, build_qss,
)

APP_TITLE = "Dosya Türüne Göre Ayır"
APP_VERSION = "1.7.0"
SETTINGS_ORG = "BuRsTFiRe47"
SETTINGS_APP = "DosyaTuruneGoreAyir"

# ---------------------------------------------------------------------------
# Dosya türü kategorileri / File type categories
# Her kategori bir uzantı kümesidir; "Tüm Dosyalar" için None = filtre yok.
# Each category is a set of extensions; "All Files" uses None = no filter.
# ---------------------------------------------------------------------------
PHOTO_EXTS = {
    ".jpg", ".jpeg", ".jpe", ".png", ".heic", ".heif", ".tif", ".tiff",
    ".bmp", ".gif", ".webp", ".raw", ".cr2", ".cr3", ".nef", ".arw",
    ".dng", ".orf", ".rw2", ".raf", ".pef", ".srw",
}
IMAGE_DESIGN_EXTS = {
    ".svg", ".ai", ".eps", ".psd", ".xcf", ".ico", ".cur", ".dib",
    ".indd", ".sketch", ".fig", ".cdr", ".afdesign", ".afphoto",
}
PRINT3D_EXTS = {
    ".stl", ".obj", ".3mf", ".gcode", ".gco", ".bgcode", ".amf", ".ply",
    ".step", ".stp", ".iges", ".igs", ".fcstd", ".skp", ".blend", ".3ds",
    ".dae", ".x3d",
}
VIDEO_EXTS = {
    ".mp4", ".mpeg", ".mpg", ".avi", ".mkv", ".m4v", ".3gp", ".wmv",
    ".flv", ".webm", ".mts", ".m2ts", ".mov", ".swf", ".rm", ".rmvb",
    ".vob", ".ogv",
}
AUDIO_EXTS = {
    ".mp3", ".wav", ".wma", ".mid", ".midi", ".flac", ".aac", ".ogg",
    ".m4a", ".opus", ".aiff",
}
DOCUMENT_EXTS = {
    ".doc", ".docx", ".dot", ".dotx", ".xls", ".xlsx", ".xlw", ".ppt",
    ".pptx", ".pdf", ".odt", ".ods", ".odp", ".rtf", ".txt", ".csv", ".md",
}
ARCHIVE_EXTS = {
    ".zip", ".rar", ".7z", ".z", ".bz2", ".gz", ".tar", ".cab", ".xz",
    ".iso", ".tgz",
}
CODE_EXTS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".htm", ".css", ".scss",
    ".json", ".xml", ".yml", ".yaml", ".c", ".h", ".cpp", ".hpp", ".cs",
    ".java", ".go", ".rs", ".sh", ".bat", ".ps1", ".ino", ".sql",
}
MAIL_EXTS = {".pst", ".eml", ".mab", ".msg", ".mbox"}

# Dropdown sırası bu sözlüğün sırasıdır / dropdown order = dict order
CATEGORIES = {
    "Fotoğraf": PHOTO_EXTS,
    "Görsel (Tasarım / Grafik)": IMAGE_DESIGN_EXTS,
    "Görsel + Fotoğraf": PHOTO_EXTS | IMAGE_DESIGN_EXTS,
    "3D Baskı Dosyaları": PRINT3D_EXTS,
    "Video": VIDEO_EXTS,
    "Ses": AUDIO_EXTS,
    "Belgeler": DOCUMENT_EXTS,
    "Arşivler": ARCHIVE_EXTS,
    "Kod / Geliştirici Dosyaları": CODE_EXTS,
    "E-posta": MAIL_EXTS,
    "Tüm Dosyalar": None,
}

FORMAT_PRESETS = {
    "Yıl / Ay / Gün  (2026/08/03)": "%Y/%m/%d",
    "Yıl-Ay-Gün  (2026-08-03)": "%Y-%m-%d",
    "Yıl / Ay  (2026/08)": "%Y/%m",
    "Yıl-Ay  (2026-08)": "%Y-%m",
    "Sadece Yıl  (2026)": "%Y",
    "Yıl / Ay Adı  (2026/Ağustos)": "%Y/%B",
    "Gün-Ay-Yıl  (03-08-2026)": "%d-%m-%Y",
    "Özel (aşağıya kendi formatınızı yazın)": "CUSTOM",
}

TR_MONTHS = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
}

# ---------------------------------------------------------------------------
# Çekirdek mantık / Core logic
# ---------------------------------------------------------------------------
def _parse_exif_dt(raw) -> Optional[datetime]:
    if isinstance(raw, bytes):
        raw = raw.decode(errors="ignore")
    raw = str(raw).strip().strip("\x00")[:19]
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def get_exif_date(path: Path) -> Optional[datetime]:
    """Çekim tarihini EXIF'ten okur (DateTimeOriginal -> Digitized -> DateTime)."""
    if not PIL_AVAILABLE:
        return None
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if not exif:
                return None
            candidates = []
            try:
                sub = exif.get_ifd(0x8769)  # Exif alt dizini
                candidates += [sub.get(36867), sub.get(36868)]
            except Exception:
                pass
            candidates.append(exif.get(306))
            for raw in candidates:
                if raw:
                    dt = _parse_exif_dt(raw)
                    if dt and dt.year > 1970:
                        return dt
    except Exception:
        return None
    return None


def get_item_date(path: Path, use_exif: bool) -> datetime:
    if use_exif and path.suffix.lower() in PHOTO_EXTS:
        d = get_exif_date(path)
        if d:
            return d
    return datetime.fromtimestamp(path.stat().st_mtime)


def format_folder_name(dt: datetime, pattern: str) -> str:
    # %B için sistem diline bağlı kalmadan Türkçe ay adı kullan
    return dt.strftime(pattern.replace("%B", TR_MONTHS[dt.month]))


def unique_destination(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    i = 1
    while True:
        candidate = dest.with_name(f"{stem} ({i}){suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def already_in_place(src: Path, target: Path) -> bool:
    """Hedefte aynı dosya zaten varsa True (aynı dosya veya aynı boyut + değiştirilme zamanı).
    Böylece aynı klasörü tekrar çalıştırmak '(1)' kopyaları üretmez."""
    try:
        if os.path.samefile(src, target):
            return True
        a, b = src.stat(), target.stat()
        return a.st_size == b.st_size and abs(a.st_mtime - b.st_mtime) < 2
    except OSError:
        return False


def format_ext_preview(exts, limit: int = 16) -> str:
    if exts is None:
        return "Filtre yok — klasördeki her dosya işlenir"
    shown = sorted(exts)
    if len(shown) > limit:
        return f"{', '.join(shown[:limit])} ve {len(shown) - limit} tür daha"
    return ", ".join(shown)


def _norm(path) -> str:
    return os.path.normcase(os.path.realpath(str(path)))


# ---------------------------------------------------------------------------
# Türe göre klasörleme / Folder-by-type
# ---------------------------------------------------------------------------
# Klasör adı -> uzantı kümesi (ilk eşleşen kazanır). "Diğer" ve "Boş Dosyalar" özel.
TYPE_FOLDERS = {
    "Fotoğraflar": PHOTO_EXTS,
    "Görseller (Tasarım)": IMAGE_DESIGN_EXTS,
    "3D Baskı": PRINT3D_EXTS,
    "Videolar": VIDEO_EXTS,
    "Ses": AUDIO_EXTS,
    "Belgeler": DOCUMENT_EXTS,
    "Arşivler": ARCHIVE_EXTS,
    "Kod": CODE_EXTS,
    "E-posta": MAIL_EXTS,
}
OTHER_FOLDER = "Diğer"
EMPTY_FOLDER = "Boş Dosyalar"
NOEXT_FOLDER = "uzantısız"

LAYOUTS = {
    "Tarihe göre  (Yıl/Ay/Gün …)": "date",
    "Türe göre  (Fotoğraflar, Videolar, Belgeler …)": "type",
    "Türe göre, içinde tarihe göre  (Videolar/2026/08 …)": "type_date",
}

_EXT_TO_FOLDER = {e: name for name, exts in reversed(list(TYPE_FOLDERS.items())) for e in exts}


def folder_for_ext(ext: str) -> Optional[str]:
    return _EXT_TO_FOLDER.get(ext.lower())


def safe_ext(ext: str) -> str:
    """Klasör adı olarak kullanılabilir uzantı: '.JPG' -> 'jpg'; garip karakterler atılır."""
    e = "".join(c for c in ext.lower().lstrip(".") if c.isalnum())[:12]
    return e or NOEXT_FOLDER


def sniff_ext(path: Path) -> Optional[str]:
    """Dosya içeriğinden (sihirli baytlar) uzantı tahmini; bulunamazsa None.
    Veri kurtarma yazılımlarının uzantısız/yanlış adlandırdığı dosyalar için."""
    try:
        with open(path, "rb") as f:
            h = f.read(4096)
    except OSError:
        return None
    if len(h) < 4:
        return None
    if h.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if h.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if h.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if h.startswith((b"II*\x00", b"MM\x00*")):
        return ".tif"
    if h[:2] == b"BM" and len(h) > 14 and h[6:10] == b"\x00\x00\x00\x00":
        return ".bmp"
    if h.startswith(b"RIFF") and len(h) >= 12:
        kind = h[8:12]
        return {b"WEBP": ".webp", b"WAVE": ".wav", b"AVI ": ".avi"}.get(kind)
    if h.startswith(b"%PDF"):
        return ".pdf"
    if h.startswith(b"PK\x03\x04"):
        if b"word/" in h:
            return ".docx"
        if b"xl/" in h:
            return ".xlsx"
        if b"ppt/" in h:
            return ".pptx"
        return ".zip"
    if h.startswith(b"Rar!\x1a\x07"):
        return ".rar"
    if h.startswith(b"7z\xbc\xaf\x27\x1c"):
        return ".7z"
    if h.startswith(b"\x1f\x8b"):
        return ".gz"
    if h.startswith(b"BZh"):
        return ".bz2"
    if h[4:8] == b"ftyp":
        brand = h[8:12]
        if brand in (b"heic", b"heix", b"hevc", b"mif1", b"heim"):
            return ".heic"
        if brand == b"qt  ":
            return ".mov"
        if brand.startswith(b"3g"):
            return ".3gp"
        if brand in (b"M4A ", b"M4B "):
            return ".m4a"
        return ".mp4"
    if h.startswith(b"ID3") or h[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return ".mp3"
    if h.startswith(b"OggS"):
        return ".ogg"
    if h.startswith(b"fLaC"):
        return ".flac"
    if h.startswith(b"\x1a\x45\xdf\xa3"):
        return ".mkv"
    if h.startswith(b"FLV\x01"):
        return ".flv"
    if h.startswith(b"\x00\x00\x01\xba"):
        return ".mpg"
    if h.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return ".doc"
    if h.startswith(b"{\\rtf"):
        return ".rtf"
    if h.startswith(b"SQLite format 3\x00"):
        return ".sqlite"
    if h.startswith(b"MZ"):
        return ".exe"
    if h.startswith(b"\x7fELF"):
        return ".elf"
    if h.startswith(b"%!PS"):
        return ".eps"
    if h.startswith(b"8BPS"):
        return ".psd"
    # düz metin mi?  (NUL yok, UTF-8 / Windows-1254 olarak okunabilir)
    if b"\x00" not in h:
        head = h.lstrip(b"\xef\xbb\xbf")
        low = head[:200].lstrip().lower()
        if low.startswith(b"<?xml"):
            return ".xml"
        if low.startswith((b"<!doctype html", b"<html")):
            return ".html"
        try:
            head.decode("utf-8")
            return ".txt"
        except UnicodeDecodeError as e:
            if e.start >= len(head) - 4:       # 4 KB sınırında kesilen çok baytlı karakter
                return ".txt"
            printable = sum(1 for b in head if b in (9, 10, 13) or 32 <= b < 127 or b >= 0xA0)
            if printable / len(head) > 0.95:   # Windows-1254 / Latin-1 metin
                return ".txt"
    return None


def type_destination(cfg, p: Path):
    """Türe göre hedef alt yolu ve dosya adı. -> (parçalar, dosya_adı, tanınan_uzantı_mı)"""
    name = p.name
    ext = p.suffix.lower()
    try:
        if cfg.empty_sep and p.stat().st_size == 0:
            return [EMPTY_FOLDER], name, False
    except OSError:
        pass
    folder = folder_for_ext(ext)
    sniffed = False
    if folder is None and cfg.sniff:
        guess = sniff_ext(p)
        if guess:
            folder = folder_for_ext(guess) or OTHER_FOLDER
            sniffed = True
            if not ext and cfg.add_ext:
                name = p.name + guess
            ext = guess                      # alt klasör adı tanınan uzantıdan gelsin
    parts = [folder or OTHER_FOLDER]
    if cfg.ext_sub:
        parts.append(safe_ext(ext))
    return parts, name, sniffed


def remove_empty_dirs(root: str, dest: str) -> int:
    """Taşıma sonrası boşalan kaynak alt klasörlerini siler (yalnızca gerçekten boş olanları)."""
    removed = 0
    rn, dn = _norm(root), _norm(dest)
    for r, _dirs, _files in os.walk(root, topdown=False):
        n = _norm(r)
        if n == rn or n == dn or n.startswith(dn + os.sep):
            continue
        try:
            os.rmdir(r)
            removed += 1
        except OSError:
            pass
    return removed


@dataclass
class SortConfig:
    source: str
    dest: str
    pattern: str
    category: str
    exts: Optional[frozenset]
    recurse: bool
    use_exif: bool
    move: bool
    dry_run: bool
    prefix: bool
    reverse: bool
    layout: str = "date"          # "date" | "type" | "type_date"
    ext_sub: bool = False         # Fotoğraflar/jpg gibi uzantı alt klasörü
    sniff: bool = False           # uzantısız/bilinmeyen dosyaları içeriğinden tanı
    add_ext: bool = False         # uzantısız dosyaya tanınan uzantıyı ekle
    empty_sep: bool = True        # 0 baytlıları "Boş Dosyalar"a koy
    clean_empty: bool = False     # taşıma sonrası boş kaynak klasörleri sil


class SortWorker(QObject):
    log = Signal(str)
    progress = Signal(int, int)
    done = Signal(int, int, int, bool, bool)  # ok, hata, atlanan, önizleme, durduruldu

    def __init__(self, cfg: SortConfig):
        super().__init__()
        self.cfg = cfg
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def _collect(self):
        cfg = self.cfg
        src, dest = _norm(cfg.source), _norm(cfg.dest)
        # Hedef klasör kaynağın içindeyse, önceki çalıştırmaların çıktısını tekrar tarama
        prune = dest != src and dest.startswith(src + os.sep)

        def matches(p: Path) -> bool:
            return cfg.exts is None or p.suffix.lower() in cfg.exts

        files = []
        if cfg.recurse:
            for root, dirs, names in os.walk(cfg.source):
                if prune:
                    dirs[:] = [d for d in dirs if _norm(Path(root, d)) != dest
                               and not _norm(Path(root, d)).startswith(dest + os.sep)]
                for name in names:
                    p = Path(root, name)
                    if matches(p):
                        files.append(p)
        else:
            for entry in os.scandir(cfg.source):
                p = Path(entry.path)
                if entry.is_file() and matches(p):
                    files.append(p)
        return files

    @Slot()
    def run(self):
        cfg = self.cfg
        ok = err = skipped = 0
        counts = Counter()
        try:
            files = self._collect()
            if not files:
                self.log.emit(f"Kaynak klasörde '{cfg.category}' kategorisine uyan dosya bulunamadı.")
                self.done.emit(0, 0, 0, cfg.dry_run, False)
                return

            need_date = cfg.layout in ("date", "type_date")
            self.log.emit(f"'{cfg.category}' kategorisinde {len(files)} dosya bulundu"
                          + (", tarihler okunuyor…" if need_date else "."))
            dated = []
            for p in files:
                if self._cancel:
                    break
                try:
                    dated.append((get_item_date(p, cfg.use_exif) if need_date else None, p))
                except OSError as e:
                    err += 1
                    self.log.emit(f"HATA ({p.name}): {e}")
            if self._cancel:
                self.log.emit("Durduruldu.")
                self.done.emit(ok, err, skipped, cfg.dry_run, True)
                return

            if need_date:
                dated.sort(key=lambda t: (t[0], str(t[1])), reverse=cfg.reverse)
            else:
                dated.sort(key=lambda t: str(t[1]).lower())

            prefix_map = {}
            if cfg.prefix and cfg.layout == "date":
                order, seen = [], set()
                for dt, _p in dated:
                    name = format_folder_name(dt, cfg.pattern)
                    if name not in seen:
                        seen.add(name)
                        order.append(name)
                width = len(str(len(order)))
                prefix_map = {n: f"{str(i).zfill(width)} - {n}" for i, n in enumerate(order, 1)}

            total = len(dated)
            dest_p = Path(cfg.dest)
            cancelled = False
            for i, (dt, p) in enumerate(dated, 1):
                if self._cancel:
                    cancelled = True
                    self.log.emit("Durduruldu.")
                    break
                try:
                    new_name = p.name
                    parts = []
                    if cfg.layout in ("type", "type_date"):
                        parts, new_name, _sn = type_destination(cfg, p)
                    if cfg.layout in ("date", "type_date") and not (parts and parts[0] == EMPTY_FOLDER):
                        folder = format_folder_name(dt, cfg.pattern)
                        if cfg.prefix and cfg.layout == "date":
                            folder = prefix_map[folder]
                        parts += [x for x in folder.replace("\\", "/").split("/") if x]
                    target_dir = dest_p.joinpath(*parts)
                    target = target_dir / new_name

                    if cfg.dry_run:
                        if total <= 3000 or i % 10 == 0:   # dev listelerde günlüğü şişirme
                            self.log.emit(f"[ÖNİZLEME] {p.name}  →  {'/'.join(parts)}/{new_name}")
                    else:
                        target_dir.mkdir(parents=True, exist_ok=True)
                        if target.exists() and already_in_place(p, target):
                            skipped += 1
                            self.log.emit(f"{p.name}  (hedefte zaten var, atlandı)")
                            if i % 25 == 0 or i == total:
                                self.progress.emit(i, total)
                            continue
                        target = unique_destination(target)
                        if cfg.move:
                            shutil.move(str(p), str(target))
                        else:
                            shutil.copy2(str(p), str(target))
                        if total <= 3000 or i % 10 == 0:
                            self.log.emit(f"{p.name}  →  {target}")
                    counts[parts[0] if parts else ""] += 1
                    ok += 1
                except Exception as e:  # tek dosya hatası tüm işlemi durdurmasın
                    err += 1
                    self.log.emit(f"HATA ({p.name}): {e}")
                if i % 25 == 0 or i == total:   # 36 bin dosyada arayüzü boğma
                    self.progress.emit(i, total)

            if cfg.layout != "date" and counts:
                self.log.emit("\nKlasör özeti:")
                for name, n in counts.most_common():
                    self.log.emit(f"  {name}: {n}")
            if cfg.move and cfg.clean_empty and not cfg.dry_run and not cancelled:
                n = remove_empty_dirs(cfg.source, cfg.dest)
                self.log.emit(f"Boşalan {n} kaynak klasörü silindi.")
            self.done.emit(ok, err, skipped, cfg.dry_run, cancelled)
        except Exception as e:
            self.log.emit(f"BEKLENMEYEN HATA: {e}")
            self.done.emit(ok, err + 1, skipped, cfg.dry_run, False)


# ---------------------------------------------------------------------------
# Özel bileşenler / Custom widgets
# ---------------------------------------------------------------------------
class Card(QFrame):
    LABEL_W = 130

    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("card")
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(18, 16, 18, 18)
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(10)
        self.grid.setColumnStretch(1, 1)
        head = QLabel(title)
        head.setObjectName("cardTitle")
        self.grid.addWidget(head, 0, 0, 1, 3)
        self._r = 1

    def row(self, label: str, field: QWidget, button: Optional[QWidget] = None):
        lab = QLabel(label)
        lab.setObjectName("muted")
        lab.setMinimumWidth(self.LABEL_W)
        self.grid.addWidget(lab, self._r, 0)
        if button is None:
            self.grid.addWidget(field, self._r, 1, 1, 2)
        else:
            self.grid.addWidget(field, self._r, 1)
            self.grid.addWidget(button, self._r, 2)
        self._r += 1

    def wide(self, widget: QWidget):
        self.grid.addWidget(widget, self._r, 0, 1, 3)
        self._r += 1


# ---------------------------------------------------------------------------
# Ana pencere / Main window
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self._thread: Optional[QThread] = None
        self._worker: Optional[SortWorker] = None
        self._running = False

        self.setWindowTitle(f"{APP_TITLE}  v{APP_VERSION}")
        self.resize(860, 900)
        self.setMinimumSize(720, 560)

        self._build_ui()
        saved = self.settings.value("theme", "dark")
        self.apply_theme(saved if saved in PALETTES else "dark")

        if not PIL_AVAILABLE:
            self.append_log("UYARI: Pillow kurulu değil, EXIF okunamayacak; dosya tarihi kullanılacak. "
                            "Kurmak için: pip install pillow")

    # ----- tema -----
    def apply_theme(self, name: str):
        name = name if name in PALETTES else "dark"
        app = QApplication.instance()
        app.setStyleSheet(build_qss(name))   # Breeze paleti (koyu/açık)
        app.setPalette(build_palette())
        self.theme_dark.setChecked(name == "dark")
        self.theme_light.setChecked(name == "light")
        self.settings.setValue("theme", name)
        for w in self.findChildren(QWidget):
            w.update()

    def _make_header(self, subtitle: str) -> QFrame:
        header = QFrame()
        header.setObjectName("header")
        h = QHBoxLayout(header)
        h.setContentsMargins(20, 12, 20, 12)
        h.setSpacing(10)
        left = QVBoxLayout()
        left.setSpacing(1)
        row = QHBoxLayout()
        row.setSpacing(8)
        title = QLabel(APP_TITLE)
        title.setObjectName("title")
        ver = QLabel(f"v{APP_VERSION}")
        ver.setObjectName("version")
        row.addWidget(title)
        row.addWidget(ver, 0, Qt.AlignBottom)
        row.addStretch(1)
        sub = QLabel(subtitle)
        sub.setObjectName("muted")
        left.addLayout(row)
        left.addWidget(sub)
        h.addLayout(left, 1)
        seg = QHBoxLayout()
        seg.setSpacing(0)
        self.theme_dark = QPushButton("Koyu")
        self.theme_dark.setObjectName("segL")
        self.theme_light = QPushButton("Açık")
        self.theme_light.setObjectName("segR")
        group = QButtonGroup(self)
        group.setExclusive(True)
        for b, name in ((self.theme_dark, "dark"), (self.theme_light, "light")):
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            group.addButton(b)
            b.clicked.connect(lambda _=False, n=name: self.apply_theme(n))
            seg.addWidget(b)
        h.addLayout(seg)
        return header

    def _make_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("bar")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(20, 12, 20, 12)
        bl.setSpacing(14)
        self.run_btn = QPushButton("Başlat")
        self.run_btn.setProperty("role", "action")
        self.run_btn.setCursor(Qt.PointingHandCursor)
        self.run_btn.clicked.connect(self.on_run_clicked)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
        self.status_label = QLabel("")
        self.status_label.setObjectName("muted")
        self.status_label.setMinimumWidth(90)
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bl.addWidget(self.run_btn)
        bl.addWidget(self.progress, 1)
        bl.addWidget(self.status_label)
        return bar

    def _set_run_state(self, running: bool):
        self.run_btn.setObjectName("cancel" if running else "")
        self.run_btn.setText("Durdur" if running else "Başlat")
        st = self.run_btn.style()
        st.unpolish(self.run_btn)
        st.polish(self.run_btn)

    # ----- klasör alanları (son kullanılanlar açılır listesi) -----
    def _hist(self, key: str) -> list:
        v = self.settings.value(f"history/{key}", [])
        if isinstance(v, str):
            v = [v]
        return [x for x in (v or []) if x]

    def _hist_add(self, key: str, path: str):
        items = [x for x in self._hist(key) if x != path]
        items.insert(0, path)
        self.settings.setValue(f"history/{key}", items[:10])

    def _hist_del(self, key: str, path: str):
        self.settings.setValue(f"history/{key}", [x for x in self._hist(key) if x != path])

    def _path_field(self, key: str, dialog_title: str, on_pick=None) -> PathField:
        def remember(p):
            self._hist_add(key, p)
            if on_pick:
                on_pick(p)
        f = PathField("", lambda _t: None, lambda: self._hist(key), remember,
                      lambda p: self._hist_del(key, p), "Seç…", "Son kullanılan klasörler",
                      "Henüz geçmiş yok", dialog_title)
        f.edit.setPlaceholderText("Seçin veya klasörü buraya sürükleyin…")
        return f

    @staticmethod
    def _autofill(field: PathField, src: str, name: str):
        if not field.text():
            field.setText(str(Path(src) / name))

    # ----- arayüz -----
    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._make_header("Dosyaları türe ve/veya tarihe göre klasörlere ayırır — veri kurtarma yığınları için de"))

        # Kaydırılabilir kartlar
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.body = QWidget()
        self.body.setObjectName("body")
        body = QVBoxLayout(self.body)
        body.setContentsMargins(24, 6, 24, 20)
        body.setSpacing(14)
        scroll.setWidget(self.body)
        outer.addWidget(scroll, 1)

        # -- Klasörler --
        card = Card("Klasörler")
        self.source_edit = self._path_field(
            "source", "Kaynak klasörü seçin",
            lambda p: self._autofill(self.dest_edit, p, "Türe ve Tarihe Göre Ayrılmış"))
        self.dest_edit = self._path_field("dest", "Hedef klasörü seçin")
        card.row("Kaynak klasör", self.source_edit)
        card.row("Hedef klasör", self.dest_edit)
        self.recurse_cb = Check("Alt klasörleri de tara (recursive)")
        self.recurse_cb.setChecked(True)
        card.wide(self.recurse_cb)
        body.addWidget(card)

        # -- Dosya kategorisi --
        card = Card("Dosya Kategorisi")
        self.category_combo = Combo()
        self.category_combo.addItems(list(CATEGORIES.keys()))
        self.category_combo.currentTextChanged.connect(self._on_category_change)
        card.row("Kategori", self.category_combo)
        self.ext_label = QLabel()
        self.ext_label.setObjectName("hint")
        self.ext_label.setWordWrap(True)
        card.wide(self.ext_label)
        body.addWidget(card)

        # -- Klasörleme düzeni --
        card = Card("Klasörleme Düzeni")
        self.layout_combo = Combo()
        self.layout_combo.addItems(list(LAYOUTS.keys()))
        self.layout_combo.currentTextChanged.connect(self._on_layout_change)
        card.row("Düzen", self.layout_combo)
        self.ext_sub_cb = Check("Uzantıya göre alt klasör aç  (Fotoğraflar/jpg, Belgeler/pdf …)")
        card.wide(self.ext_sub_cb)
        self.sniff_cb = Check("Uzantısız / bilinmeyen dosyaları içeriğinden tanı")
        self.sniff_cb.setChecked(True)
        card.wide(self.sniff_cb)
        self.addext_cb = Check("Uzantısız dosyalara tanınan uzantıyı ekle  (f123 → f123.jpg)")
        card.wide(self.addext_cb)
        self.empty_cb = Check("Boş (0 bayt) dosyaları ayrı klasöre koy")
        self.empty_cb.setChecked(True)
        card.wide(self.empty_cb)
        self.clean_cb = Check("Taşıdıktan sonra boşalan kaynak klasörleri sil")
        card.wide(self.clean_cb)
        self.layout_hint = QLabel("Veri kurtarma çıktıları için: kategoriyi 'Tüm Dosyalar' seçip 'Türe göre' düzenini kullanın.")
        self.layout_hint.setObjectName("hint")
        self.layout_hint.setWordWrap(True)
        card.wide(self.layout_hint)
        body.addWidget(card)

        # -- Tarih ayarları --
        self.date_cards = []
        card = Card("Tarih Ayarları")
        self.date_cards.append(card)
        self.exif_cb = Check("Önce EXIF çekim tarihini kullan (yoksa dosya tarihi)")
        self.exif_cb.setChecked(True)
        card.wide(self.exif_cb)
        self.preset_combo = Combo()
        self.preset_combo.addItems(list(FORMAT_PRESETS.keys()))
        self.preset_combo.currentTextChanged.connect(self._on_preset_change)
        card.row("Klasör formatı", self.preset_combo)
        self.custom_edit = QLineEdit("%Y/%m/%d")
        self.custom_edit.setPlaceholderText("%Y/%m/%d   —   / ile alt klasör açılır")
        self.custom_edit.textChanged.connect(self._update_example)
        card.row("Özel format", self.custom_edit)
        self.example_label = QLabel()
        self.example_label.setObjectName("hint")
        card.wide(self.example_label)
        body.addWidget(card)

        # -- Sıralama --
        card = Card("Sıralama")
        self.date_cards.append(card)
        self.order_combo = Combo()
        self.order_combo.addItems(["Eskiden yeniye", "Yeniden eskiye"])
        card.row("İşlem yönü", self.order_combo)
        self.prefix_cb = Check("Klasör adlarının başına sıra numarası ekle (01 - …, 02 - …)")
        card.wide(self.prefix_cb)
        body.addWidget(card)

        # -- İşlem --
        card = Card("İşlem")
        radios = QHBoxLayout()
        radios.setSpacing(28)
        self.copy_radio = Radio("Kopyala (kaynak dosyalar kalır)")
        self.move_radio = Radio("Taşı (kaynak dosyalar silinir)")
        self.copy_radio.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.copy_radio)
        group.addButton(self.move_radio)
        radios.addWidget(self.copy_radio)
        radios.addWidget(self.move_radio)
        radios.addStretch(1)
        wrap = QWidget()
        wrap.setLayout(radios)
        radios.setContentsMargins(0, 0, 0, 0)
        card.wide(wrap)
        self.dry_cb = Check("Sadece önizleme yap (dosyaları gerçekten taşıma/kopyalama)")
        card.wide(self.dry_cb)
        body.addWidget(card)

        # -- Kayıt --
        card = Card("Kayıt")
        self.log_box = QPlainTextEdit()
        self.log_box.setObjectName("log")
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumBlockCount(5000)
        self.log_box.setMinimumHeight(190)
        card.wide(self.log_box)
        body.addWidget(card)
        body.addStretch(1)

        outer.addWidget(self._make_bar())

        self._on_category_change(self.category_combo.currentText())
        self._on_preset_change(self.preset_combo.currentText())
        self._on_layout_change(self.layout_combo.currentText())

    # ----- olaylar -----
    def _on_category_change(self, name: str):
        exts = CATEGORIES.get(name)
        self.ext_label.setText(format_ext_preview(exts))
        # EXIF yalnızca fotoğraf uzantılarında anlamlı
        exif_useful = exts is None or bool(exts & PHOTO_EXTS)
        self.exif_cb.setEnabled(exif_useful)
        self.exif_cb.update()

    def _on_layout_change(self, label: str):
        layout = LAYOUTS.get(label, "date")
        is_type = layout in ("type", "type_date")
        for w in (self.ext_sub_cb, self.sniff_cb, self.addext_cb, self.empty_cb):
            w.setEnabled(is_type)
            w.update()
        self.layout_hint.setVisible(is_type)
        for card in self.date_cards:          # saf "türe göre"de tarih ayarları anlamsız
            card.setEnabled(layout != "type")
        self.prefix_cb.setEnabled(layout == "date")
        self.prefix_cb.update()
        if is_type and self.category_combo.currentText() != "Tüm Dosyalar":
            self.category_combo.setCurrentText("Tüm Dosyalar")

    def _on_preset_change(self, label: str):
        pattern = FORMAT_PRESETS.get(label, "CUSTOM")
        is_custom = pattern == "CUSTOM"
        self.custom_edit.setEnabled(is_custom)
        if not is_custom:
            self.custom_edit.setText(pattern)
        self._update_example()

    def _update_example(self, *_):
        pattern = self.custom_edit.text().strip()
        if not pattern:
            self.example_label.setText("Örnek klasör: —")
            return
        try:
            example = format_folder_name(datetime.now(), pattern)
            self.example_label.setText(f"Örnek klasör:  {example}")
        except (ValueError, KeyError):
            self.example_label.setText("Örnek klasör: geçersiz format")

    def append_log(self, msg: str):
        self.log_box.appendPlainText(msg)

    # ----- işlem -----
    def on_run_clicked(self):
        if self._running:
            if self._worker:
                self._worker.cancel()
            self.run_btn.setEnabled(False)
            self.run_btn.setText("Durduruluyor…")
            return
        self.start()

    def start(self):
        source = self.source_edit.text().strip()
        dest = self.dest_edit.text().strip()
        pattern = self.custom_edit.text().strip()
        if not source or not Path(source).is_dir():
            QMessageBox.warning(self, "Hata", "Geçerli bir kaynak klasör seçin.")
            return
        if not dest:
            QMessageBox.warning(self, "Hata", "Geçerli bir hedef klasör seçin.")
            return
        if not pattern:
            QMessageBox.warning(self, "Hata", "Klasör formatı boş olamaz.")
            return
        try:
            format_folder_name(datetime.now(), pattern)
        except (ValueError, KeyError):
            QMessageBox.warning(self, "Hata", "Klasör formatı geçersiz.")
            return

        move = self.move_radio.isChecked()
        dry = self.dry_cb.isChecked()
        if move and not dry:
            answer = QMessageBox.question(
                self, "Onay",
                "Dosyalar kaynak klasörden TAŞINACAK (kaynakta kalmayacak).\nDevam edilsin mi?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                return

        category = self.category_combo.currentText()
        exts = CATEGORIES[category]
        cfg = SortConfig(
            source=source, dest=dest, pattern=pattern, category=category,
            exts=None if exts is None else frozenset(exts),
            recurse=self.recurse_cb.isChecked(),
            use_exif=self.exif_cb.isChecked() and self.exif_cb.isEnabled(),
            move=move, dry_run=dry, prefix=self.prefix_cb.isChecked(),
            reverse=self.order_combo.currentText() == "Yeniden eskiye",
            layout=LAYOUTS[self.layout_combo.currentText()],
            ext_sub=self.ext_sub_cb.isChecked(),
            sniff=self.sniff_cb.isChecked(),
            add_ext=self.addext_cb.isChecked(),
            empty_sep=self.empty_cb.isChecked(),
            clean_empty=self.clean_cb.isChecked(),
        )

        self._running = True
        self._set_run_state(True)
        self.progress.setValue(0)
        self.status_label.setText("Hazırlanıyor…")

        if self._thread is not None:  # önceki çalıştırmanın iş parçacığını serbest bırak
            self._thread.deleteLater()
        self._thread = QThread(self)
        self._worker = SortWorker(cfg)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self.append_log)
        self._worker.progress.connect(self.on_progress)
        self._worker.done.connect(self.on_done)
        self._worker.done.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.start()

    @Slot(int, int)
    def on_progress(self, done: int, total: int):
        self.progress.setMaximum(max(total, 1))
        self.progress.setValue(done)
        self.status_label.setText(f"{done} / {total}")

    @Slot(int, int, int, bool, bool)
    def on_done(self, ok: int, err: int, skipped: int, dry: bool, cancelled: bool):
        head = "Durduruldu" if cancelled else "Tamamlandı"
        extra = f", Atlanan: {skipped}" if skipped else ""
        self.append_log(f"\n{head}. Başarılı: {ok}, Hatalı: {err}{extra}.")
        if dry:
            self.append_log("(Önizleme modundaydı, hiçbir dosya taşınmadı/kopyalanmadı.)")
        self._running = False
        self.run_btn.setEnabled(True)
        self._set_run_state(False)
        if not cancelled and self.progress.maximum() > 0:
            self.progress.setValue(self.progress.maximum())

    def closeEvent(self, event):
        if self._running and self._worker:
            self._worker.cancel()
            if self._thread:
                self._thread.quit()
                self._thread.wait(3000)
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    font = QFont()
    font.setFamilies(["Segoe UI Variable Text", "Segoe UI", "SF Pro Text", "Helvetica Neue",
                      "Inter", "Roboto", "Noto Sans", "DejaVu Sans"])
    font.setPixelSize(13)
    app.setFont(font)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
