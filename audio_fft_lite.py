import numpy as np

def compute_spectrum(audio: np.ndarray, sr: int = 16000):
    windowed = audio * np.hanning(len(audio))
    fft = np.fft.rfft(windowed)
    mag = np.abs(fft)
    mag_db = 20 * np.log10(mag + 1e-10)
    freqs = np.linspace(0, sr/2, len(mag_db))
    return freqs, mag_db

def drone_band_ratio(freqs, mag_db):
    # 100-500Hz에 에너지 몰리면 드론
    idx = (freqs >= 100) & (freqs <= 500)
    drone = np.mean(mag_db[idx])
    total = np.mean(mag_db)
    return float(drone - total)  # dB 차이
