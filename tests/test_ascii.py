import os
import sys
import pytest
from ascii.main import (
    get_color_code,
    load_banner,
    get_glyphs,
    render_word,
    render_text,
    reverse_text,
    main
)

def create_test_banner():
    banner = []

    for code in range(32, 127):
        char = chr(code)
        banner.extend([char] * 8)
        banner.append("")

    return banner


def save_test_banner(tmp_path):
    banner = create_test_banner()
    banner_path = tmp_path / "test_banner.txt"
    banner_path.write_text("\n".join(banner), encoding="utf-8")
    return banner_path


def test_get_color_code():
    assert get_color_code("red") == "\033[31m"
    assert get_color_code("blue") == "\033[34m"
    assert get_color_code("#FF0000") == "\033[38;2;255;0;0m"
    assert get_color_code("invalid") is None


def test_load_banner(tmp_path, monkeypatch):
    save_test_banner(tmp_path)
    monkeypatch.chdir(tmp_path)

    banner = load_banner("test_banner")

    assert len(banner) == 854

    with pytest.raises(ValueError):
        load_banner("missing_banner")


def test_get_glyphs():
    banner = create_test_banner()
    glyphs = get_glyphs(banner)

    assert "A" in glyphs
    assert "B" in glyphs
    assert len(glyphs["A"]) == 8
    assert glyphs["A"] == ("A",) * 8


def test_render_word():
    glyphs = get_glyphs(create_test_banner())

    result = render_word("AB", glyphs)

    assert result == ["AB"] * 8

    with pytest.raises(ValueError):
        render_word("é", glyphs)


def test_render_text(monkeypatch):
    glyphs = get_glyphs(create_test_banner())

    monkeypatch.setattr(
        "ascii.main.shutil.get_terminal_size",
        lambda size: os.terminal_size((20, 24))
    )

    plain, colored = render_text("A B", glyphs)

    assert plain[0] == "A     B"
    assert len(plain) == 9
    assert len(colored) == 9

    right, _ = render_text("A", glyphs, alignment="right")

    assert right[0].startswith(" ")


def test_reverse_text(tmp_path, monkeypatch, capsys):
    save_test_banner(tmp_path)

    art_path = tmp_path / "art.txt"
    art_path.write_text("\n".join(["A"] * 8), encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    reverse_text("art.txt", "test_banner")

    captured = capsys.readouterr()

    assert captured.out.strip() == "A"


def test_main(tmp_path, monkeypatch, capsys):
    banner_path = tmp_path / "standard.txt"
    banner_path.write_text(
        "\n".join(create_test_banner()),
        encoding="utf-8"
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["main.py", "A"])

    main()

    captured = capsys.readouterr()

    assert captured.out.splitlines()[:8] == ["A"] * 8
