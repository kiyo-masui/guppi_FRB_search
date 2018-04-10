import numpy as np


class DataSource(object):
    """Abstract base class for data sources."""

    # The Subclasses must implement the following.

    def __init__(self, source=None, block=None, overlap=None, scrunch=1,
                 passband=None):
        """
        Parameters
        ----------
        source :
            To be used by subclasses
        block : float
            Target time block, approximate but lower limit.
        overlap : float
            Target overlapping of blocks, approximate but lower limit.
        bandpass : tuple of 2 floats
            Maximum and minimum frequency to supply.

        """

        self._source = source
        self._block = block
        self._overlap = overlap
        self._scrunch = scrunch
        self._passband = passband

    def get_next_block_native(self):
        """Get the next block of data to process without applying time scrunch.

        Returns
        -------
        t0 : float
            Time of first sample, in seconds `self.start_time`.
        data : 2D array
            Data with axes representing frequency, time.

        Raises
        ------
        StopIteration:
            If not data left to process.

        """
        pass

    @property
    def nblocks_left(self):
        """Number of blocks remaining.

        This might not be static if the data source is growing.

        """
        pass

    @property
    def nblocks_fetched(self):
        """Number of blocks yielded so far."""
        pass

    # Initialization must provide data for these parameters.

    @property
    def time_block(self):
        return self._block

    @property
    def overlap(self):
        return self._overlap

    @property
    def delta_t(self):
        return self._delta_t_native * self._scrunch

    @property
    def delta_f(self):
        return self._delta_f

    @property
    def freq0(self):
        return self.freq[0]

    @property
    def nfreq(self):
        return len(self.freq)

    @property
    def mjd(self):
        """Modified Julian date of the data, as integer."""
        return self._mjd

    @property
    def start_time(self):
        """Start time of the data, in seconds since UTC midnight of `self.mjd`.
        """
        return self._start_time

    @property
    def freq(self):
        freq, f_slice = self._freq_native_and_slice()
        return freq[f_slice]

    def _freq_native_and_slice(self):
        freq_native = np.arange(self._nfreq, dtype=float) * self.delta_f
        freq_native += self._freq0
        if self._passband:
            inband = np.logical_and(freq_native > self._passband[0],
                                    freq_native < self._passband[1])
            inband, = np.nonzero(inband)
            inband = np.s_[inband[0]:inband[-1] + 1]
        else:
            inband = np.s_[:]

        return freq_native, inband

    def get_next_block(self):
        """Get the next block of data to process.

        Returns
        -------
        t0 : float
            Time of first sample, in seconds since `self.start_time`.
        data : 2D array
            Data with axes representing frequency, time.

        Raises
        ------
        StopIteration:
            If not data left to process.

        """

        scrunch = self._scrunch
        t0, data_native = self.get_next_block_native()
        _, f_slice = self._freq_native_and_slice()
        data_native = data_native[f_slice]
        if scrunch == 1:
            return t0, data_native
        ntime_native = data_native.shape[1]
        if ntime_native % self._scrunch:
            msg = "Scrunch factor (%d) must divide native time block size (%d)"
            raise NotImplementedError(msg % (scrunch, ntime_native))
        shape = data_native.shape[:1] + (ntime_native // scrunch, scrunch)
        data_native.shape = shape
        t0 += self.delta_t * (1 - 1./scrunch) / 2
        data = np.mean(data_native, -1).astype(data_native.dtype)
        return t0, data
