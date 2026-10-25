"""Check phase-space coordinates against a coherent state of known amplitude."""
import unittest

import dynamiqs as dq
import matplotlib.pyplot as plt
import numpy as np

from src.plotting import wigner_panels


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


if __name__ == "__main__":
    unittest.main()
