"""Check Wigner coordinates and the timing/color consistency of encoded GIFs."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json

import dynamiqs as dq
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from src.plotting import wigner_panels, wigner_gif


class WignerCoordinatesTests(unittest.TestCase):
    def test_coherent_peak_and_normalization(self):
        beta = 1 + 0.5j
        fig = wigner_panels(dq.coherent(24, [beta]), [0], xmax=4)
        try:
            image = fig.axes[0].images[0]
            values = np.asarray(image.get_array())
            xmin, xmax, ymin, ymax = image.get_extent()
            row, col = np.unravel_index(values.argmax(), values.shape)
            x = np.linspace(xmin, xmax, values.shape[1])
            y = np.linspace(ymin, ymax, values.shape[0])
            self.assertAlmostEqual(x[col], beta.real, delta=0.06)
            self.assertAlmostEqual(y[row], beta.imag, delta=0.06)
            integral = np.trapezoid(np.trapezoid(values, x=x, axis=1), x=y)
            self.assertAlmostEqual(integral, 1, places=5)
            np.testing.assert_allclose(image.get_clim(), [-2/np.pi, 2/np.pi])
        finally:
            plt.close(fig)


class WignerAnimationTests(unittest.TestCase):
    def test_gif_round_trip_preserves_timing_and_color_scale(self):
        states = dq.coherent(24, [1+0.5j, -1-0.5j, 1-0.5j])
        with TemporaryDirectory() as directory, patch("src.plotting.FIG_DIR", Path(directory)):
            path = wigner_gif(states, [0, 0.01, 0.02], "coherent_motion")
            with Image.open(path) as gif:
                self.assertTrue(gif.is_animated)
                self.assertEqual(gif.n_frames, 3)
                self.assertEqual(gif.info["loop"], 0)
                metadata = json.loads(gif.info["comment"])
                np.testing.assert_allclose(metadata["times_us"], [0, 0.01, 0.02])
                np.testing.assert_allclose(metadata["wigner_limits"], [-2/np.pi, 2/np.pi])
                frames, durations = [], []
                for i in range(gif.n_frames):
                    gif.seek(i)
                    durations.append(gif.info["duration"])
                    frames.append(np.asarray(gif.convert("RGB")).copy())
            self.assertEqual(durations, [800, 40, 800])
            self.assertFalse(np.array_equal(frames[0], frames[1]))
            # Colorbar, labels and background must remain intact after GIF disposal.
            fixed_region = int(0.86 * frames[0].shape[1])
            for frame in frames[1:]:
                np.testing.assert_array_equal(frame[:, fixed_region:], frames[0][:, fixed_region:])

    def test_rejects_nonuniform_physical_time_spacing(self):
        with self.assertRaisesRegex(ValueError, "uniformly"):
            wigner_gif(dq.coherent(24, [0, 1, 2]), [0, 0.01, 0.03], "nonuniform")


if __name__ == "__main__":
    unittest.main()
