import numpy as NP

"""
A module which implements the continuous wavelet transform

---------------------------------------------------------
Code released under the BSD 3-clause licence.

Copyright (c) 2012, R W Fearick, University of Cape Town
All rights reserved.

Wavelet classes:
Morlet
MorletReal
MexicanHat
Paul2      : Paul order 2
Paul4      : Paul order 4
DOG1       : 1st Derivative Of Gaussian
DOG4       : 4th Derivative Of Gaussian
Haar       : Unnormalised version of continuous Haar transform
HaarW      : Normalised Haar

Usage e.g.
wavelet=Morlet(data, largestscale=2, notes=0, order=2, scaling="log")
 data:  Numeric array of data (float), with length ndata.
        Optimum length is a power of 2 (for FFT)
        Worst-case length is a prime
 largestscale:
        largest scale as inverse fraction of length
        scale = len(data)/largestscale
        smallest scale should be >= 2 for meaningful data
 notes: number of scale intervals per octave
        if notes == 0, scales are on a linear increment
 order: order of wavelet for wavelets with variable order
        [Paul, DOG, ..]
 scaling: "linear" or "log" scaling of the wavelet scale.
        Note that feature width in the scale direction
        is constant on a log scale.

Attributes of instance:
wavelet.cwt:       2-d array of Wavelet coefficients, (nscales,ndata)
wavelet.nscale:    Number of scale intervals
wavelet.scales:    Array of scale values
                   Note that meaning of the scale will depend on the family
wavelet.fourierwl: Factor to multiply scale by to get scale
                   of equivalent FFT
                   Using this factor, different wavelet families will
                   have comparable scales

References:
A practical guide to wavelet analysis
C Torrance and GP Compo
Bull Amer Meteor Soc Vol 79 No 1 61-78 (1998)
naming below vaguely follows this.

updates:
(24/2/07):  Fix Morlet so can get MorletReal by cutting out H
(10/04/08): Numeric -> numpy
(25/07/08): log and lin scale increment in same direction!
            swap indices in 2-d coeffiecient matrix
            explicit scaling of scale axis
"""


class Cwt:
    """
    Base class for continuous wavelet transforms
    Implements cwt via the Fourier transform
    Used by subclass which provides the method wf(self,s_omega)
    wf is the Fourier transform of the wavelet function.
    Returns an instance.
    """

    fourierwl = 1.00

    def _log2(self, x):
        # utility function to return (integer) log2
        return int(NP.log(float(x)) /
                   NP.log(2.0) + 0.0001)

    def __init__(self, data, finished, notifyProgress, largestscale=1, notes=0,
                 order=2, scaling='linear', omega0=5.):
        """
        Continuous wavelet transform of data

        data:    data in array to transform, length must be power of 2
        notes:   number of scale intervals per octave
        largestscale: largest scale as inverse fraction of length
                 of data array
                 scale = len(data)/largestscale
                 smallest scale should be >= 2 for meaningful data
        order:   Order of wavelet basis function for some families
        scaling: Linear or log
        """
        ndata = len(data)
        self.order = order
        self.omega0 = omega0
        self.scale = largestscale
        self._setscales(ndata, largestscale, notes, scaling)
        self.cwt = NP.zeros((self.nscale, ndata), NP.complex64)
        omega = NP.array(list(range(0, ndata//2)) +
                         list(range(-ndata // 2, 0)))*(2.0*NP.pi/ndata)
        datahat = NP.fft.fft(data)
        self.fftdata = datahat
        # self.psihat0=self.wf(omega*self.scales[3*self.nscale/4])
        # loop over scales and compute wvelet coeffiecients at each scale
        # using the fft to do the convolution
        for scaleindex in range(self.nscale):
            currentscale = self.scales[scaleindex]
            self.currentscale = currentscale  # for internal use
            s_omega = omega*currentscale
            psihat = self.wf(s_omega)
            psihat = psihat * NP.sqrt(2.0*NP.pi*currentscale)
            convhat = psihat * datahat
            W = NP.fft.ifft(convhat)
            self.cwt[scaleindex, 0:ndata] = W
            notifyProgress.emit(scaleindex*100//self.nscale)
        finished.emit(self)

    def _setscales(self, ndata, largestscale, notes, scaling):
        """
        if notes non-zero, returns a log scale based on notes per ocave
        else a linear scale
        (25/07/08): fix notes!=0 case so smallest scale at [0]
        """
        if scaling == "log":
            if notes <= 0:
                notes = 1
            # adjust nscale so smallest scale is 2
            noctave = self._log2(ndata/largestscale/2)
            self.nscale = notes*noctave
            self.scales = NP.zeros(self.nscale,
                                   float)
            for j in range(self.nscale):
                self.scales[j] = ndata/(self.scale *
                                        (2.0**(float(self.nscale-1-j)/notes)))
        elif scaling == "linear":
            nmax = ndata/largestscale/2
            step = (nmax-2)/2**notes
            self.scales = NP.arange(float(2), float(nmax), step)
            self.nscale = len(self.scales)
        else:
            raise (ValueError, "scaling must be linear or log")
        return

    def getdata(self):
        """
        returns wavelet coefficient array
        """
        return self.cwt

    def getcoefficients(self):
        return self.cwt

    def getpower(self):
        """
        returns square of wavelet coefficient array
        """
        return (self.cwt * NP.conjugate(self.cwt)).real

    def getangle(self):
        """
        returns angle of wavelet coefficient array
        """
        return NP.angle(self.cwt)

    def getscales(self):
        """
        returns array containing scales used in transform
        """
        return self.scales

    def getnscale(self):
        """
        return number of scales
        """
        return self.nscale


# wavelet classes
class Morlet(Cwt):
    """
    Morlet wavelet
    """
    # omega0=5.0
    def wf(self, s_omega):
        Cwt.fourierwl = 4 * NP.pi/(self.omega0 + NP.sqrt(2.0+self.omega0**2))
        H = NP.ones(len(s_omega))
        # n = len(s_omega)
        for i in range(len(s_omega)):
            if s_omega[i] < 0.0:
                H[i] = 0.0
        # !!!! note : was s_omega/8 before 17/6/03
        xhat = 0.75112554*(NP.exp(-(s_omega-self.omega0)**2/2.0))*H
        return xhat


class MorletReal(Cwt):
    """
    Real Morlet wavelet
    """
    # omega0=5.0
    def wf(self, s_omega):
        Cwt.fourierwl = 4 * NP.pi/(self.omega0 + NP.sqrt(2.0+self.omega0**2))
        H = NP.ones(len(s_omega))
        # n = len(s_omega)
        for i in range(len(s_omega)):
            if s_omega[i] < 0.0:
                H[i] = 0.0
        # !!!! note : was s_omega/8 before 17/6/03
        xhat = 0.75112554*(NP.exp(-(s_omega-self.omega0)**2/2.0) +
                           NP.exp(-(s_omega+self.omega0)**2/2.0) -
                           NP.exp(-(self.omega0)**2/2.0) +
                           NP.exp(-(self.omega0)**2/2.0))
        return xhat


class Paul(Cwt):
    """
    Paul order m wavelet
    """
    def wf(self, s_omega):
        Cwt.fourierwl = 4 * NP.pi/(2.*self.order+1.)
        m = self.order
        n = len(s_omega)
        normfactor = float(m)
        for i in range(1, 2*m):
            normfactor = normfactor*i
        normfactor = 2.0**m / NP.sqrt(normfactor)
        xhat = NP.zeros(n)
        xhat[0:n/2] = normfactor*s_omega[0:n/2]**m * NP.exp(-s_omega[0:n/2])
        # return 0.11268723*s_omega**2*exp(-s_omega)*H
        return xhat


class DOG(Cwt):
    """
    Derivative Gaussian wavelet of order m
    but reconstruction seems to work best with +!
    """
    def wf(self, s_omega):
        try:
            from scipy.special import gamma
        except ImportError:
            print ("Requires scipy gamma function")
            raise ImportError
        Cwt.fourierwl = 2 * NP.pi / NP.sqrt(self.order+0.5)
        m = self.order
        dog = 1.0J**m*s_omega**m * NP.exp(-s_omega**2/2)/NP.sqrt(
            gamma(self.order+0.5))
        return dog


class Haar(Cwt):
    """
    Continuous version of Haar wavelet
    """
    #    note: not orthogonal!
    #    note: s_omega/4 matches Lecroix scale defn.
    #          s_omega/2 matches orthogonal Haar
    # 2/8/05 constants adjusted to match artem eim

    fourierwl = 1.0  # 1.83129  #2.0

    def wf(self, s_omega):
        haar = NP.zeros(len(s_omega), NP.complex64)
        om = s_omega[:]/self.currentscale
        om[0] = 1.0  # prevent divide error
        # haar.imag=4.0*sin(s_omega/2)**2/om
        haar.imag = 4.0 * NP.sin(s_omega/4)**2/om
        return haar

## class HaarW(Cwt):
##     """
##     Continuous version of Haar wavelet (norm)
##     """
##     #    note: not orthogonal!
##     #    note: s_omega/4 matches Lecroix scale defn.
##     #          s_omega/2 matches orthogonal Haar
##     # normalised to unit power

##     fourierwl=1.83129*1.2  #2.0
##     def wf(self, s_omega):
##         haar= NP.zeros(len(s_omega),NP.complex64)
##         om = s_omega[:]#/self.currentscale
##         om[0]=1.0  #prevent divide error
##         #haar.imag=4.0*sin(s_omega/2)**2/om
##         haar.imag=4.0* NP.sin(s_omega/2)**2/om
##         return haar


if __name__ == "__main__":
    import numpy as np
    import pylab as mpl

    wavelet = Morlet
    maxscale = 4
    notes = 16
    scaling = "log"  # or "linear"
    scaling = "linear"
    plotpower2d = True

    # set up some data
    Ns = 2048
    # limits of analysis
    Nlo = 0
    Nhi = Ns
    # sinusoids of two periods, 128 and 32.
    x = np.arange(0.0, 1.0*Ns, 1.0)
    A = np.sin(2.0*np.pi*x/128.0)
    B = np.sin(2.0*np.pi*x/256.0)
    A[512:1024] += B[0:512]

    # Wavelet transform the data
    cw = wavelet(A, maxscale, notes, scaling=scaling)
    scales = cw.getscales()
    cwt = cw.getdata()
    # power spectrum
    pwr = cw.getpower()
    scalespec = np.sum(pwr, axis=1) / scales  # calculate scale spectrum
    # scales
    y = cw.fourierwl*scales
    x = np.arange(Nlo*1.0, Nhi*1.0, 1.0)

    fig = mpl.figure(1)

    # 2-d coefficient plot
    ax = mpl.axes([0.4, 0.1, 0.55, 0.4])
    mpl.xlabel('Time [s]')
    plotcwt = np.clip(np.fabs(cwt.real), 0., 1000.)
    if plotpower2d:
        plotcwt = pwr
    im = mpl.imshow(plotcwt,
                    cmap=mpl.cm.jet,
                    extent=[x[0],
                            x[-1],
                            y[-1],
                            y[0]],
                    aspect='auto')
    # colorbar()
    if scaling == "log":
        ax.set_yscale('log')
    mpl.ylim(y[0], y[-1])
    ax.xaxis.set_ticks(np.arange(Nlo*1.0, (Nhi+1)*1.0, 100.0))
    ax.yaxis.set_ticklabels(["", ""])
    theposition = mpl.gca().get_position()

    # data plot
    ax2 = mpl.axes([0.4, 0.54, 0.55, 0.3])
    mpl.ylabel('Data')
    pos = ax.get_position()
    mpl.plot(x, A, 'b-')
    mpl.xlim(Nlo*1.0, Nhi*1.0)
    ax2.xaxis.set_ticklabels(["", ""])
    mpl.text(0.5, 0.9, "Wavelet example with extra panes",
             fontsize=14,
             bbox=dict(facecolor='green', alpha=0.2),
             transform=fig.transFigure, horizontalalignment='center')

    # projected power spectrum
    ax3 = mpl.axes([0.08, 0.1, 0.29, 0.4])
    mpl.xlabel('Power')
    mpl.ylabel('Period [s]')
    vara = 1.0
    if scaling == "log":
        mpl.loglog(scalespec/vara+0.01, y, 'b-')
    else:
        mpl.semilogx(scalespec/vara+0.01, y, 'b-')
    mpl.ylim(y[0], y[-1])
    mpl.xlim(1000.0, 0.01)
    mpl.show()
