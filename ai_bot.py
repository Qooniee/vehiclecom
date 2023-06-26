import numpy as np
import IPython

rate = 48000
duration = 1.0
t = np.linspace(0., duration, int(rate*duration))
x = np.sin(2.0*np.pi*440.0*t)
IPython.display.Audio(x, rate=rate, autoplay=True)