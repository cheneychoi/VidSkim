from pathlib import Path

import numpy as np
from faster_whisper.audio import decode_audio


def test_real_mp4_decodes_with_the_installed_pyav_version():
    sample = Path(__file__).resolve().parents[1] / "examples" / "sample.mp4"
    audio = decode_audio(str(sample), sampling_rate=16000)
    assert audio.ndim == 1
    assert len(audio) > 16000
    assert np.isfinite(audio).all()
    assert np.max(np.abs(audio)) > 0
