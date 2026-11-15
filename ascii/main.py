import sys
import re
import shutil

BANNERS = ["standard", "shadow", "thinkertoy"]

COLORS = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
}

ALIGNMENTS = ["left", "right", "center", "justify"]

USAGE = (
    "Usage: python3 main.py [OPTION] [STRING] [BANNER]\n\n"
    "EX: python3 main.py --align=right something standard"
)

USAGE_REVERSE = (
    "Usage: python3 main.py [OPTION]\n\n"
    "EX: python3 main.py --reverse=<fileName>"
)

def get_color_code(color):
    if color in COLORS:
        return f"\033[{COLORS[color]}m"

    if re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        return f"\033[38;2;{r};{g};{b}m"

    return None

def load_banner(name):
    try:
        with open(f"{name}.txt", "r", encoding="utf-8") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        raise ValueError(f"Error: {name}.txt not found")

def get_glyphs(banner):
    glyphs = {}

    for code in range(32, 127):
        start = (code - 32) * 9
        rows = banner[start:start + 8]

        if len(rows) != 8:
            continue

        width = max(len(row) for row in rows)
        glyphs[chr(code)] = tuple(
            row.ljust(width) for row in rows
        )

    return glyphs

def render_word(word, glyphs):
    rows = [""] * 8

    for char in word:
        if char not in glyphs:
            raise ValueError(f"Unsupported character: {char}")

        char_rows = glyphs[char]

        for i in range(8):
            rows[i] += char_rows[i]

    return rows

def render_text(text, glyphs, alignment="left", color=None,
                target_letters=None):

    terminal_width = shutil.get_terminal_size((80, 24)).columns
    words = text.split("\\n")
    result = []
    colored_result = []

    color_code = get_color_code(color) if color else None

    for line in words:
        line_words = line.split(" ")

        rendered_words = [
            render_word(word, glyphs) for word in line_words
        ]

        word_widths = [
            len(rendered_words[i][0]) for i in range(len(line_words))
        ]

        content_width = sum(word_widths)

        if alignment == "justify" and len(line_words) > 1:
            spaces = max(1, terminal_width - content_width)
            gaps = len(line_words) - 1
            base, extra = divmod(spaces, gaps)
            gap_sizes = [
                base + (1 if i < extra else 0)
                for i in range(gaps)
            ]
        else:
            gap_sizes = [5] * (len(line_words) - 1)

        for row in range(8):
            plain_line = ""
            colored_line = ""

            for i, word_rows in enumerate(rendered_words):
                word = line_words[i]
                part = word_rows[row]

                plain_line += part

                if color_code and (
                    target_letters is None
                    or any(char in target_letters for char in word)
                ):
                    colored_part = ""

                    for j, char in enumerate(word):
                        char_part = glyphs[char][row]

                        if char in target_letters if target_letters is not None else True:
                            colored_part += (
                                color_code + char_part + "\033[0m"
                            )
                        else:
                            colored_part += char_part

                    colored_line += colored_part
                else:
                    colored_line += part

                if i < len(line_words) - 1:
                    gap = " " * gap_sizes[i]
                    plain_line += gap
                    colored_line += gap

            if alignment == "right":
                padding = max(0, terminal_width - len(plain_line))
                plain_line = " " * padding + plain_line
                colored_line = " " * padding + colored_line

            elif alignment == "center":
                padding = max(0, (terminal_width - len(plain_line)) // 2)
                plain_line = " " * padding + plain_line
                colored_line = " " * padding + colored_line

            result.append(plain_line)
            colored_result.append(colored_line)

        result.append("")
        colored_result.append("")

    return result, colored_result

def reverse_text(filename, banner_name):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        print(f"Error: {filename} not found")
        return

    content = re.sub(r"\033\[[0-9;]*m", "", content)
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    try:
        banner = load_banner(banner_name)
    except ValueError as error:
        print(error)
        return

    glyphs = get_glyphs(banner)
    patterns = []

    for char, rows in glyphs.items():
        char_width = len(rows[0])

        if char_width > 0:
            patterns.append((char, rows, char_width))

    lines = content.split("\n")

    while lines and lines[-1] == "":
        lines.pop()

    groups = []
    current_group = []

    for line in lines:
        if line == "":
            if current_group:
                groups.append(current_group)
                current_group = []
        else:
            current_group.append(line)

    if current_group:
        groups.append(current_group)

    decoded_lines = []

    for group in groups:
        if len(group) != 8:
            continue

        width = max(len(row) for row in group)
        rows = [row.ljust(width) for row in group]

        def decode_from(start):
            dp = [None] * (width + 1)
            dp[width] = ""

            for position in range(width - 1, start - 1, -1):
                for char, pattern, char_width in patterns:
                    end = position + char_width

                    if end > width or dp[end] is None:
                        continue

                    matches = all(
                        rows[i][position:end] == pattern[i]
                        for i in range(8)
                    )

                    if matches:
                        dp[position] = char + dp[end]
                        break

                if dp[position] is None:
                    if all(row[position] == " " for row in rows):
                        end = position

                        while (
                            end < width
                            and all(row[end] == " " for row in rows)
                        ):
                            end += 1

                        if dp[end] is not None:
                            dp[position] = " " + dp[end]

            return dp[start]

        decoded = None
        leading_spaces = 0

        while (
            leading_spaces < width
            and all(row[leading_spaces] == " " for row in rows)
        ):
            leading_spaces += 1

        for start in range(leading_spaces + 1):
            decoded = decode_from(start)

            if decoded is not None:
                break

        decoded_lines.append(decoded.rstrip() if decoded is not None else "?")

    print("\n".join(decoded_lines))

def main():
    args = sys.argv[1:]

    if not args:
        return

    output_file = None
    color = None
    align = "left"
    reverse_file = None
    positional = []

    for arg in args:
        if arg.startswith("--output="):
            if output_file is not None:
                print(USAGE)
                return
            output_file = arg[len("--output="):]

        elif arg.startswith("--color="):
            if color is not None:
                print(USAGE)
                return
            color = arg[len("--color="):]

        elif arg.startswith("--align="):
            if align != "left":
                print(USAGE)
                return
            align = arg[len("--align="):]

        elif arg.startswith("--reverse="):
            if reverse_file is not None:
                print(USAGE_REVERSE)
                return
            reverse_file = arg[len("--reverse="):]

        elif arg.startswith("--"):
            print(USAGE)
            return

        else:
            positional.append(arg)

    if align not in ALIGNMENTS:
        print(USAGE)
        return

    if color is not None and get_color_code(color) is None:
        print(USAGE)
        return

    if output_file is not None and not output_file.endswith(".txt"):
        print(USAGE)
        return

    if reverse_file is not None:
        if positional or output_file or color:
            print(USAGE_REVERSE)
            return

        banner_name = "standard"

        reverse_text(reverse_file, banner_name)
        return

    banner_name = "standard"

    if positional and positional[-1] in BANNERS:
        banner_name = positional.pop()

    target_letters = None

    if color is not None:
        if len(positional) == 1:
            user_input = positional[0]
        elif len(positional) == 2:
            target_letters = positional[0]
            user_input = positional[1]
        else:
            print(USAGE)
            return
    else:
        if len(positional) != 1:
            print(USAGE)
            return

        user_input = positional[0]

    if user_input == "":
        return

    try:
        banner = load_banner(banner_name)
        glyphs = get_glyphs(banner)

        plain, colored = render_text(
            user_input,
            glyphs,
            align,
            color,
            target_letters
        )

    except ValueError as error:
        print(error)
        return

    plain_result = "\n".join(plain)
    colored_result = "\n".join(colored)

    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(colored_result if color else plain_result)
        except OSError as error:
            print(f"Error writing file: {error}")
    elif color:
        print(colored_result)
    else:
        print(plain_result)

if __name__ == "__main__":
    main()
