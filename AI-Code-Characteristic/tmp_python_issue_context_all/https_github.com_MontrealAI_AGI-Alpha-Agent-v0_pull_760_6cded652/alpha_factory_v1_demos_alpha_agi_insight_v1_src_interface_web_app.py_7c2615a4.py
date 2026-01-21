"""Streamlit dashboard placeholder."""
from __future__ import annotations

try:
    import streamlit as st
except Exception:  # pragma: no cover - optional
    st = None


def main() -> None:  # pragma: no cover
    if st is None:
        print("Streamlit not installed")
        return
    st.title("α‑AGI Insight")
    st.write("Coming soon")


if __name__ == "__main__":
    main()
