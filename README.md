# Dosya Türüne Göre Ayır 🗂️

*(English below)*

Bir klasördeki dosyaları **seçtiğiniz türe** göre filtreleyip (fotoğraf,
görsel, 3D baskı dosyası, video, belge, arşiv, kod... veya tüm dosyalar),
çekim/dosya tarihine göre otomatik olarak klasörlere ayıran, gece/gündüz
temalı bir masaüstü uygulaması.

[**Foto Tarihe Göre Ayır**](../../../foto-tarihe-gore-ayir) projesinin genel
amaçlı fork'udur — aynı tarih motorunu korur, sadece tek bir türe (fotoğraf)
değil, seçtiğiniz herhangi bir dosya türü grubuna uygulamanızı sağlar.

![platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-blue)
![license](https://img.shields.io/badge/license-MIT-green)

<img src="docs/screenshot-dark.png" width="640" alt="Uygulama görünümü (koyu mod)">

*(Not: Yukarıdaki görüntü Linux üzerinde alınmıştır; Windows ve macOS'ta
yazı tipleri sisteminizin kendi fontuyla — Segoe UI / San Francisco — daha
akıcı görünür.)*

## Özellikler

- 🗂️ **Dosya kategorisi seçimi** — Fotoğraf, Görsel (Tasarım/Grafik),
  Görsel + Fotoğraf, 3D Baskı Dosyaları, Video, Ses, Belgeler, Arşivler,
  Kod/Geliştirici Dosyaları, E-posta veya Tüm Dosyalar
- 📅 EXIF çekim tarihi veya dosya değiştirilme tarihine göre ayırma
  (EXIF yalnızca fotoğraf/görsel türlerinde kullanılır)
- 🗓️ Hazır tarih formatları (Yıl/Ay/Gün, Yıl-Ay, sadece Yıl, Türkçe ay adı...)
  veya kendi `strftime` formatınızı yazma
- 📁 `/` ile alt klasör oluşturma desteği (örn. `%Y/%m` → 2026/08)
- 🔢 Klasör adlarına sıra numarası ekleyerek sıralamayı garanti altına alma
- ↔️ Kopyala veya taşı seçeneği
- 👀 Önizleme (dry-run) modu — hiçbir dosyayı değiştirmeden sonucu görme
- 🌙☀️ Gece / Gündüz modu (varsayılan: gece)

## Kategoriler ve uzantıları

| Kategori | Uzantı örnekleri |
|---|---|
| Fotoğraf | jpg, png, heic, tiff, cr2, nef, arw, dng, raw... |
| Görsel (Tasarım/Grafik) | svg, ai, eps, psd, ico, sketch, fig, cdr... |
| Görsel + Fotoğraf | yukarıdaki ikisinin birleşimi |
| 3D Baskı Dosyaları | stl, obj, 3mf, gcode, step, ply, blend... |
| Video | mp4, mov, avi, mkv, webm, flv... |
| Ses | mp3, wav, flac, aac, m4a... |
| Belgeler | doc(x), xls(x), ppt(x), pdf, odt, txt, csv... |
| Arşivler | zip, rar, 7z, tar, gz, iso... |
| Kod / Geliştirici Dosyaları | py, js, ts, html, css, json, java, go... |
| E-posta | pst, eml, msg, mbox... |
| Tüm Dosyalar | filtre yok — her dosya |

Kendi kategorinizi eklemek isterseniz `dosya_turune_gore_ayir.py` dosyasındaki
`CATEGORIES` sözlüğüne yeni bir uzantı kümesi eklemeniz yeterli.

## İndirme (kurulum gerektirmez)

En güncel derlenmiş sürümleri **[Releases](../../releases)** sayfasından
indirebilirsiniz:

- **Windows** → `DosyaTuruneGoreAyir.exe`
- **Mac (Apple Silicon / M1, M2, M3, M4...)** → `DosyaTuruneGoreAyir-macOS-AppleSilicon.zip`

> Not: Intel Mac (x86_64) için ayrı bir derleme sunulmuyor. Eski bir Intel
> Mac'iniz varsa "Kaynaktan çalıştırma" bölümündeki adımlarla uygulamayı
> doğrudan çalıştırabilirsiniz.

Bu dosyalar benim bilgisayarımda değil, **GitHub Actions üzerinde bu
repodaki kaynak koddan otomatik olarak** derlenir — derleme adımlarını ve
günlüklerini [Actions](../../actions) sekmesinden herkes görebilir.

### macOS'ta ilk açılış uyarısı

`.zip` dosyasını açın, `DosyaTuruneGoreAyir.app` dosyasına **sağ tıklayıp
"Aç"** deyin (çift tıklamayın), çıkan uyarıda tekrar **"Aç"** deyin.

### Windows'ta ilk açılış uyarısı

SmartScreen uyarısında **"Ek bilgi"** → **"Yine de çalıştır"** ile devam edin.

## Kaynaktan çalıştırma

```bash
pip install pillow customtkinter
python dosya_turune_gore_ayir.py
```

## Kendi exe/app dosyanızı derlemek isterseniz

### Windows
```bat
pip install pillow customtkinter pyinstaller
pyinstaller --onefile --noconsole --collect-all customtkinter --name "DosyaTuruneGoreAyir" dosya_turune_gore_ayir.py
```

### macOS
```bash
pip3 install pillow customtkinter pyinstaller
pyinstaller --windowed --collect-all customtkinter --name "DosyaTuruneGoreAyir" dosya_turune_gore_ayir.py
```

## Yeni bir sürüm yayınlamak

```bash
git tag v1.0.0
git push origin v1.0.0
```

Bu komut GitHub Actions'ı tetikler; Windows exe ve Apple Silicon için macOS
`.app` dosyası otomatik derlenip bir GitHub Release'e eklenir.

## Lisans

MIT — bkz. [LICENSE](LICENSE)

---

## English

A dark/light-themed desktop app that filters files in a folder by a
**chosen type** (photo, image/design, 3D-print file, video, document,
archive, code... or all files) and automatically sorts them into
date-based folders, using the capture date (EXIF) or file date.

This is a general-purpose fork of the **Foto Tarihe Göre Ayır** ("Sort
Photos by Date") project — it keeps the same date-sorting engine, but lets
you apply it to any file-type group you pick, not just photos.

### Features

- 🗂️ **File category picker** — Photo, Image (Design/Graphics),
  Image + Photo, 3D-Print Files, Video, Audio, Documents, Archives,
  Code/Developer Files, Mail, or All Files
- 📅 Sort by EXIF capture date or file modified date (EXIF only applies
  to photo/image categories)
- 🗓️ Built-in date-folder formats (Year/Month/Day, Year-Month, Year only,
  month name...) or your own custom `strftime` pattern
- 📁 Nested subfolders via `/` in the pattern (e.g. `%Y/%m` → 2026/08)
- 🔢 Optional sequence-number prefix on folder names to guarantee sort order
- ↔️ Copy or move
- 👀 Dry-run preview mode — see the result without touching any files
- 🌙☀️ Dark / Light mode (defaults to dark)

### Download (no install needed)

Grab the latest build from **[Releases](../../releases)**:

- **Windows** → `DosyaTuruneGoreAyir.exe`
- **Mac (Apple Silicon)** → `DosyaTuruneGoreAyir-macOS-AppleSilicon.zip`

These are built transparently by **GitHub Actions directly from this
repo's source** — not a binary from an unknown machine. Build logs are
public under the [Actions](../../actions) tab.

### Run from source

```bash
pip install pillow customtkinter
python dosya_turune_gore_ayir.py
```

### License

MIT — see [LICENSE](LICENSE)
