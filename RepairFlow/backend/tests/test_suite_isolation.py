"""The suite must never write into a developer's real backend/data/.

`app_db` repoints DATABASE_PATH at a temp file, but for a long time that
was the only path it moved. RECORDINGS_DIR and DOCUMENTS_DIR still
defaulted to backend/data/, so every run of the voice tests dropped four
files -- "FAKE-MP3-BYTES", "TEST-AUDIO-NOT-A-REAL-RECORDING", "audio",
"x" -- into the real recordings folder. One machine had accumulated 466
of them, indistinguishable by name from genuine call audio, before
anyone looked.
"""

from __future__ import annotations

from app.config import BACKEND_DIR, Settings, get_settings


def test_no_storage_path_points_into_the_real_data_directory() -> None:
    real = (BACKEND_DIR / "data").resolve()
    for settings in (get_settings(), Settings()):
        for name in ("data_dir", "database_path", "recordings_dir", "documents_dir"):
            path = getattr(settings, name).resolve()
            assert not path.is_relative_to(real), (
                f"{name} resolves to {path}, inside the developer's real {real}"
            )
