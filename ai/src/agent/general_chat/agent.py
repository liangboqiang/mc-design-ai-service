from __future__ import annotations

from agent import build_from_page


def build_engine(overrides: dict | None = None):
    return build_from_page("general_chat", overrides)


def main() -> None:
    engine = build_engine()
    print("general_chat agent ready. Enter q to quit.")
    while True:
        try:
            message = input("general> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if message.lower() in {"q", "quit", "exit"}:
            break
        print(engine.chat(message))
        print()


if __name__ == "__main__":
    main()
