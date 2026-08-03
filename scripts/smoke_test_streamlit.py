"""One-off smoke test for the refactored Streamlit app using AppTest --
simulates login + a few interactions headlessly against the real backend
(must be running on http://127.0.0.1:8000) and prints any exceptions raised
during script execution. Not part of the pytest suite (needs a live server
and demo accounts); run manually: python scripts/smoke_test_streamlit.py
"""

from streamlit.testing.v1 import AppTest


def _print_exceptions(at: AppTest, label: str) -> bool:
    if at.exception:
        print(f"[{label}] EXCEPTIONS:")
        for exc in at.exception:
            print(f"  - {exc.value!r}")
        return True
    print(f"[{label}] OK, no exceptions.")
    return False


def main() -> None:
    at = AppTest.from_file("app/streamlit_app.py", default_timeout=30)
    at.run()
    if _print_exceptions(at, "initial load (login page)"):
        return

    # Streamlit auto-generates keys for unkeyed widgets by label+position; use
    # positional access on the login form instead of guessing keys.
    email_input = at.text_input[0]
    password_input = at.text_input[1]
    email_input.set_value("admin@edu.ai")
    password_input.set_value("Admin@123")
    at.button[0].click()
    at.run()
    if _print_exceptions(at, "after admin login"):
        return

    print("Home page rendered with", len(at.button), "buttons.")

    # Pick the first course card's "enter course" button if any course exists
    # (label has Vietnamese diacritics; matched here but never printed, to
    # dodge this Windows console's cp1258 codec limitation).
    enter_buttons = [b for b in at.button if "Vào môn học" in (b.label or "")]
    if enter_buttons:
        enter_buttons[0].click()
        at.run()
        _print_exceptions(at, "after entering a course")
    else:
        print("No course card found for admin demo account -- skipping workspace check.")


if __name__ == "__main__":
    main()
