#!/usr/bin/env python3

# This code is in no way optimized or even well written.
# It's the outcome of a train-of-thought process playing around
# with decoding ft8. Specifically starting from the premise of
# 256 fft real/positive bins with a 1800Hz bandpass, which is the 32x
# waterfall on the mcHF.

from scipy.io import wavfile
from scipy.stats import mode
from numpy.fft import fft, fftfreq
from numpy.linalg import norm
from numpy import amax, where, abs, arange, hanning, transpose, square, sqrt, mean
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import time
import math

samplerate, data = wavfile.read("ft8-2020-11-22-15-30.wav")

print(f"samplerate: {samplerate}")
print(f"points: {data.shape}")

baud = 25
semitimestep = int(samplerate * 1.0/baud)

nybaud = 2 * baud
nysemitimestep = int(samplerate * 1.0/nybaud)

bincount = 512
freq_per_bin = samplerate / bincount

print(f"baud={baud} semitimestep={semitimestep}")
print(f"nybaud={nybaud} nysemitimestep={nysemitimestep}")

# Decoded by playing the above wav into WSJT-X.
#  3  0.3  558 WT8J W3GRL FM29
# -2  0.3  632 UR3EO VE9MO FN65
# -7  0.6  765 W3YNI KD2TUS R-20
# -4  0.5 1045 KC3FOI WB4RAG 73
# -4  0.3 1555 EA5L K3ZR RR73
# -2  0.3 1632 OK7PJ VE2LOA -15
#-12  0.3  610 5B4AMM VA2CW FN46
#-22  0.6  696 BH4BNQ HG2DX -18
min_freq = 558
reported_snr = 3



freqs = fftfreq(bincount, 1.0/samplerate)

ffts = fft(data, bincount)

bin_550 = int(min_freq / freq_per_bin)
print("freq_of_interest", freqs[bin_550:bin_550+9])

samples_per_40ms = int(0.04 * samplerate)

start_freq_offset = (min_freq - freqs[bin_550])
print(f"start_freq_offset={start_freq_offset}")
assert(start_freq_offset >= 0)

freqs_of_interest = []

top_bin = int(7*(6.25 / freq_per_bin))+1

for i in range(samples_per_40ms, len(data)-samples_per_40ms, samples_per_40ms):
    fft_bins = fft(data[i-samples_per_40ms:i+samples_per_40ms], bincount)

    fft_bins = fft_bins[bin_550:bin_550+top_bin+1]
    fft_bins = [norm(f) for f in fft_bins]
    fft_bins = fft_bins / amax(fft_bins)
    freqs_of_interest.append([norm(f) for f in fft_bins])

def plot_tone_lines(ax, fpb, ymax, xoff):
    min_bin_freq = freqs[bin_550]
    fpt = 6.25 / fpb
    delta_bins = 0
    for i in range(8):
        xmin = xmax = delta_bins + (i*fpt) + xoff
        ymin = 0
        l = mlines.Line2D([xmin, xmax], [ymin, ymax], c="r")
        ax.add_line(l)

costa = [3, 1, 4, 0, 6, 5, 2]
costa_bins = []
for i in costa:
    for j in range(4):
        x = [0 for _ in range(8)]
        if i > 0:
            x[i-1] = 0.8
        x[i] = 1
        if i < 7:
            x[i+1] = 0.8
        costa_bins.append(x)

plt.show()

fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4)

fig.suptitle(f"{min_freq}Hz Offset, Reported SNR={reported_snr}")


ax1.imshow(freqs_of_interest, origin='lower', aspect="auto")
fpb = freq_per_bin
plot_tone_lines(ax1, fpb, len(freqs_of_interest)-1, 6.25/2/fpb)

x = list(range(0, top_bin, 1))
xi = [f"{freqs[bin_550] + (i*freq_per_bin):.04}" for i in x]
ax1.set_xticks(x)
ax1.set_xticklabels(xi, rotation=90)
ax1.set_title("Raw FFT")

y = list(range(0, len(freqs_of_interest), 10))
yi = [f"{0.04 * i:.04}" for i in y]
ax1.set_yticks(y)
ax1.set_yticklabels(yi)

interpolated = []
factor = 7

interpolated_to_tone = int((factor * (6.25 / freq_per_bin))/1)
tone_step = 6.25/2
tones = []
for i in freqs_of_interest:
    # Break each bin into `factor` bins.
    ni = [i[int(j/factor)] for j in range(len(i)*factor)]
    # Iteritivly average the bins with their neighbors.
    # Linear interpolation usually places the value of the original bin
    # in the middle of the range being interpolated, but that's not what
    # we want, we want to let it shift left or right depending on how
    # strong neighboring bins are.
    for blank in range(factor):
        for j in range(1, len(ni) - 1):
            ni[j] = (ni[j-1] + ni[j] + ni[j+1])/3
    interpolated.append(ni/amax(ni))
    ht = []
    # Take the interpolated bins and turn them into tone bins,
    # by averaging a half-tone worth of interpolated bins
    # on each side of the tone, with overlap.
    #
    # As an example:
    #
    # F = FFT Bin
    # I = Interpolated Bin
    # H = Half Tone bin
    # 0-7 = tone bins
    #
    # F     F     F     F     F     F     F
    # III I II II I III III I II II I III IIII
    # HHH H HH HH H HHH HHH H HH HH H HHH HHH
    # 000 0 00 22 2 222 444 4 44 66 6 666
    #     1 11 11 1 333 333 5 55 55 5 777 777
    for j in range(interpolated_to_tone, len(ni)-interpolated_to_tone, interpolated_to_tone):
        ht.append(sum(ni[j-interpolated_to_tone:j+interpolated_to_tone])/interpolated_to_tone/2)
    tones.append(ht)

decoded = []
for i in tones:
    tdt = [0 for j in i]
    selected_tone = where(i == amax(i))[0][0]
    tdt[selected_tone] = 1
    decoded.append(tdt)
print("decoded[0]", decoded[0])

# Look for the costa sequence by subtracting the known costa sequence
# from the received signal and compute the RMS.
#
# I _think_ that at least 2 sec should fit in the UHSDR waterfall with
# 40ms sampling (25Hz @ 2sec = 50 samples < 70 Lines in the waterfall).
min_costa_idx = None
min_costa_rms = 99999
for i in range(0,50):
    xs = [j[0:len(costa_bins)+1] for j in tones[i:i+len(costa_bins)]]
    delta = (np.array(xs) - (np.array(costa_bins)*amax(xs)))
    rms = sqrt(mean(square(delta)))
    if rms < min_costa_rms:
        min_costa_rms = rms
        min_costa_idx = i

print(f"min_costa_idx={min_costa_idx}\tmin_costa_rms={min_costa_rms}")

# Now that we have where the costa sequence started, we know where the
# signal is in time.
timing_idx = min_costa_idx % 4
first_frame = min_costa_idx + (7 * 4)
print(f"timing_idx={timing_idx}\tfirst_frame={first_frame}")

ax2.imshow(interpolated,origin='lower', aspect="auto")
fpb = freq_per_bin/factor
plot_tone_lines(ax2, freq_per_bin/factor, len(interpolated)-1, start_freq_offset/fpb)

x = list(range(0, len(interpolated[0]), 4))
xi = [f"{freqs[bin_550] + (i*fpb):.04}" for i in x]
ax2.set_xticks(x)
ax2.set_xticklabels(xi, rotation=90)
ax2.set_title("Interpolated FFT values")

ax2.set_xticks(x)

ax1.set_yticks(y)
ax1.set_yticklabels(yi)

ax3.imshow(tones,origin='lower', aspect="auto")
fpb = 6.25
plot_tone_lines(ax3, fpb, len(tones)-1, 0)

x = list(range(0, len(tones[0]), 1))
xi = [f"{min_freq + (i*6.25):0.04}" for i in x]
ax3.set_xticks(x)
ax3.set_xticklabels(xi, rotation=90)
ax3.set_title("Tones (with strength)")

ax3.set_yticks(y)
ax3.set_yticklabels(yi)

decoded_tones = [where(i == amax(i))[0][0] for i in decoded]

# Starting from our timing offset frame, consider
# every 4 frames one bit, and take the most represented
# tone as the value.
best_3of4 = [0 for _ in range(int(first_frame/4))]
for i in range(first_frame, len(decoded_tones), 4):
    best_3of4.append(mode(decoded_tones[i-3:i]).mode[0])

best_3of4_to_spectrum = []
for i in best_3of4:
    x = [0 for _ in range(8)]
    x[i] = 1
    best_3of4_to_spectrum.append(x)

ax4.imshow(best_3of4_to_spectrum, origin="lower", aspect="auto")
plot_tone_lines(ax4, fpb, len(best_3of4_to_spectrum)-1, 0)
ax4.set_title("Assigned Tone")

plt.show()
