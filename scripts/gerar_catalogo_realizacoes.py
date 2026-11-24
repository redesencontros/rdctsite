
#!/usr/bin/env python3
"""Gera automaticamente o catálogo das realizações do rdct para GitHub Pages."""

from __future__ import annotations

import json
import mimetypes
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REALIZATIONS_DIR = ROOT / "ativos" / "realizacoes"
THUMBNAILS_DIR = ROOT / "ativos" / "imagens" / "miniaturas"
OUTPUT = REALIZATIONS_DIR / "catalogo.json"
LANGUAGES = ("pt", "en", "es")

VIDEO_EXTENSIONS = {".mp4", ".webm"}
AUDIO_EXTENSIONS = {".mp3", ".ogg", ".oga", ".wav", ".m4a", ".aac"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
NUMBERED_DIR = re.compile(r"^(\d+)-(.+)$")
NUMBERED_FILE = re.compile(r"^(\d+)(?:[-_].*)?$")


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.lower().replace("ç", "c")


def thumbnail_key(value: str) -> str:
    """Gera o nome-base da miniatura a partir do nome da realização."""
    value = re.sub(r"^\d+-", "", value)
    value = re.sub(r"\s*[\[(]\d{4}(?:[-_]\d{2,4})?[\])]\s*$", "", value)
    value = normalized(value)
    return re.sub(r"[^a-z0-9]", "", value)


def find_preview_image(realization_name: str) -> str | None:
    """Procura a miniatura JPG correspondente à realização."""
    if not THUMBNAILS_DIR.is_dir():
        return None

    key = thumbnail_key(realization_name)

    for path in THUMBNAILS_DIR.iterdir():
        if not path.is_file() or path.suffix.lower() != ".jpg":
            continue

        if thumbnail_key(path.stem) == key:
            return media_path(path)

    return None


def order_of(name: str) -> int:
    match = re.match(r"^(\d+)", name)
    return int(match.group(1)) if match else 999999


def humanize_slug(value: str) -> str:
    value = re.sub(r"^\d+-", "", value)
    value = re.sub(r"\s*\(\d{4}\)$", "", value)
    return value.strip()


def get_realization_year(value: str) -> str:
    value = re.sub(r"^\d+-", "", value)

    match = re.search(r"\((\d{4})\)$", value)

    return match.group(1) if match else ""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeError):
        return ""


def parse_labeled_text(text: str) -> dict[str, str]:
    """Lê campos separados por rótulos em linhas isoladas."""
    aliases = {
        "titulo": "title", "título": "title", "title": "title",
        "descricao": "description", "descrição": "description",
        "description": "description", "legenda": "description",
        "credito": "credit", "crédito": "credit", "credit": "credit",
        "fonte": "source", "source": "source",
    }
    result: dict[str, str] = {}
    current: str | None = None
    chunks: dict[str, list[str]] = {}

    for line in text.splitlines():
        key = aliases.get(line.strip().rstrip(":").lower())
        if key:
            current = key
            chunks.setdefault(key, [])
        elif current:
            chunks[current].append(line)

    for key, lines in chunks.items():
        result[key] = "\n".join(lines).strip()
    return result


def language_file(directory: Path, stem: str, language: str) -> Path | None:
    candidates = [
        directory / f"{stem}-{language}.txt",
        directory / f"{stem}_{language}.txt",
    ]
    return next((path for path in candidates if path.is_file()), None)


def localized_content(directory: Path, stem: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for language in LANGUAGES:
        path = language_file(directory, stem, language)
        if path:
            result[language] = read_text(path)
    return result


def localized_metadata(directory: Path, number: int) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    prefix = f"{number:02d}-info-"
    for path in directory.iterdir():
        if path.is_file() and path.name.startswith(prefix) and path.suffix.lower() == ".txt":
            language = path.stem[len(prefix):].lower()
            if language in LANGUAGES:
                result[language] = parse_labeled_text(read_text(path))
    return result


def parse_presentation(path: Path | None) -> dict[str, str]:
    if not path:
        return {}
    fields = parse_labeled_text(read_text(path))
    if not fields:
        return {"description": read_text(path)}
    return fields


def media_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def numbered_items(directory: Path, section_type: str) -> list[dict]:
    items: list[dict] = []

    if section_type in {"video", "audio", "instagram"}:
        for path in directory.iterdir():
            if not path.is_file():
                continue
            name = path.name.lower()
            match = re.match(r"^(\d+)[-_]embed\.txt$", name)
            if match or name == "embed.txt":
                number = int(match.group(1)) if match else 1
                embed_url = read_text(path)
                if embed_url:
                    items.append({
                        "order": number,
                        "kind": "embed",
                        "embed_url": embed_url,
                        "metadata": localized_metadata(directory, number),
                    })
                continue

            ext = path.suffix.lower()
            accepted = VIDEO_EXTENSIONS if section_type == "video" else AUDIO_EXTENSIONS if section_type == "audio" else set()
            if ext not in accepted:
                continue
            match = re.match(r"^(\d+)(?:[-_].*)?\.[^.]+$", name)
            number = int(match.group(1)) if match else 999999
            mime = mimetypes.guess_type(path.name)[0] or ("video/mp4" if ext == ".mp4" else "audio/mpeg")
            items.append({
                "order": number,
                "kind": "file",
                "path": media_path(path),
                "mime": mime,
                "metadata": localized_metadata(directory, number),
            })

    elif section_type == "gallery":
        for path in directory.iterdir():
            if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            match = re.match(r"^(\d+)(?:[-_].*)?\.[^.]+$", path.name.lower())
            number = int(match.group(1)) if match else 999999
            items.append({
                "order": number,
                "kind": "image",
                "path": media_path(path),
                "metadata": localized_metadata(directory, number),
            })

    elif section_type == "text":
        groups: dict[int, dict[str, str]] = {}
        # Ex.: 01-texto-pt.txt / 01-pt.txt. Também aceita conteudo-pt.txt como item único.
        for path in directory.iterdir():
            if not path.is_file() or path.suffix.lower() != ".txt":
                continue
            name = path.name.lower()
            embed_match = re.match(r"^(\d+)[-_]embed\.txt$", name)
            if embed_match or name == "embed.txt":
                number = int(embed_match.group(1)) if embed_match else 1
                embed_url = read_text(path)
                if embed_url:
                    items.append({
                        "order": number,
                        "kind": "embed",
                        "embed_url": embed_url,
                        "metadata": localized_metadata(directory, number),
                    })
                continue
            match = re.match(r"^(\d+)(?:-[^-]+)?-(pt|en|es)\.txt$", name)
            if match:
                number, language = int(match.group(1)), match.group(2)
                groups.setdefault(number, {})[language] = read_text(path)
                continue
            match = re.match(r"^(conteudo|texto)-(pt|en|es)\.txt$", name)
            if match:
                groups.setdefault(1, {})[match.group(2)] = read_text(path)
        for number, content in groups.items():
            items.append({
                "order": number,
                "kind": "text",
                "content": content,
                "metadata": localized_metadata(directory, number),
            })

    return sorted(items, key=lambda item: (item["order"], item.get("path", item.get("kind", ""))))


def section_type_from_name(name: str) -> str:
    slug = normalized(re.sub(r"^\d+-", "", name))
    if "apresentacao" in slug or "introducao" in slug:
        return "presentation"
    if "video" in slug or "filme" in slug:
        return "video"
    if "audio" in slug or "som" in slug:
        return "audio"
    if "galeria" in slug or "imagem" in slug or "foto" in slug:
        return "gallery"
    if "instagram" in slug or "rede-social" in slug:
        return "instagram"
    if "texto" in slug or "publicacao" in slug or "documento" in slug:
        return "text"
    if "credito" in slug or "ficha-tecnica" in slug:
        return "credits"
    return "text"


def build_realization(directory: Path) -> dict:
    presentation_dir = next(
        (
            child for child in directory.iterdir()
            if child.is_dir()
            and section_type_from_name(child.name) == "presentation"
        ),
        None,
    )

    presentation: dict[str, dict[str, str]] = {}
    titles: dict[str, str] = {}

    if presentation_dir:
        for language in LANGUAGES:
            path = language_file(presentation_dir, "conteudo", language)

            if path:
                fields = parse_presentation(path)
                presentation[language] = fields

                if fields.get("title"):
                    titles[language] = fields["title"]

    fallback_title = humanize_slug(directory.name)

    for language in LANGUAGES:
        titles.setdefault(language, titles.get("pt", fallback_title))

    sections = []

    for section_dir in sorted(
        (child for child in directory.iterdir() if child.is_dir()),
        key=lambda item: (order_of(item.name), item.name.lower()),
    ):
        section_type = section_type_from_name(section_dir.name)

        section = {
            "slug": section_dir.name,
            "order": order_of(section_dir.name),
            "type": section_type,
        }

        if section_type == "presentation":
            section["content"] = presentation

        elif section_type == "credits":
            section["content"] = localized_content(section_dir, "creditos")

            if not section["content"]:
                section["content"] = localized_content(section_dir, "conteudo")

        else:
            section["items"] = numbered_items(section_dir, section_type)

        if section_type in {"presentation", "credits"} or section.get("items"):
            sections.append(section)

    realization = {
        "slug": directory.name,
        "order": order_of(directory.name),
        "menu_title": humanize_slug(directory.name),
        "year": get_realization_year(directory.name),
        "titles": titles,
        "sections": sections,
    }

    preview_image = find_preview_image(directory.name)

    if preview_image:
        realization["preview_image"] = preview_image

    return realization


def main() -> None:
    REALIZATIONS_DIR.mkdir(parents=True, exist_ok=True)
    directories = [
        child for child in REALIZATIONS_DIR.iterdir()
        if child.is_dir() and NUMBERED_DIR.match(child.name)
    ]
    realizations = [
        build_realization(directory)
        for directory in sorted(directories, key=lambda item: (order_of(item.name), item.name.lower()))
    ]

    catalog = {"version": 1, "realizations": realizations}
    OUTPUT.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Catálogo gerado: {OUTPUT} ({len(realizations)} realizações)")


if __name__ == "__main__":
    main()
