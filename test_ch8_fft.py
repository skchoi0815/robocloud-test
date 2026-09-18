import numpy as np
from audio_fft_lite import compute_spectrum, drone_band_ratio

def make_drone(sr=16000, dur=1.0):
    t = np.linspace(0, dur, int(sr*dur))
    s = np.sin(2*np.pi*200*t) + 0.5*np.sin(2*np.pi*400*t)
    return s / np.max(np.abs(s))

def test_drone_has_band_energy():
    sr = 16000
    audio = make_drone(sr)
    freqs, mag = compute_spectrum(audio, sr)
    ratio = drone_band_ratio(freqs, mag)
    assert ratio > 5.0  # 드론밴드가 평균보다 5dB 높아야 함

def test_silence_no_drone():
    sr = 16000
    noise = np.random.randn(sr) * 0.01
    freqs, mag = compute_spectrum(noise, sr)
    ratio = drone_band_ratio(freqs, mag)
    assert ratio < 5.0
