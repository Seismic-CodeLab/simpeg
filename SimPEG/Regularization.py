from __future__ import print_function

import numpy as np
import scipy.sparse as sp
import warnings

from . import Utils
from . import Maps
from . import Mesh
from . import ObjectiveFunction


class RegularizationMesh(object):
    """
    **Regularization Mesh**

    This contains the operators used in the regularization. Note that these
    are not necessarily true differential operators, but are constructed from
    a SimPEG Mesh.

    :param BaseMesh mesh: problem mesh
    :param numpy.array indActive: bool array, size nC, that is True where we have active cells. Used to reduce the operators so we regularize only on active cells

    """

    def __init__(self, mesh, indActive=None):
        self.mesh = mesh
        assert indActive is None or indActive.dtype == 'bool', (
            'indActive needs to be None or a bool'
        )
        self.indActive = indActive

    @property
    def vol(self):
        """
        reduced volume vector

        :rtype: numpy.array
        :return: reduced cell volume
        """
        if getattr(self, '_vol', None) is None:
            self._vol = self.Pac.T * self.mesh.vol
        return self._vol

    @property
    def nC(self):
        """
        reduced number of cells

        :rtype: int
        :return: number of cells being regularized
        """
        if getattr(self, '_nC', None) is None:
            if self.indActive is None:
                self._nC = self.mesh.nC
            else:
                self._nC = int(sum(self.indActive))
        return self._nC

    @property
    def dim(self):
        """
        dimension of regularization mesh (1D, 2D, 3D)

        :rtype: int
        :return: dimension
        """
        if getattr(self, '_dim', None) is None:
            self._dim = self.mesh.dim
        return self._dim


    @property
    def Pac(self):
        """
        projection matrix that takes from the reduced space of active cells to
        full modelling space (ie. nC x nindActive)

        :rtype: scipy.sparse.csr_matrix
        :return: active cell projection matrix
        """
        if getattr(self, '_Pac', None) is None:
            if self.indActive is None:
                self._Pac = Utils.speye(self.mesh.nC)
            else:
                self._Pac = Utils.speye(self.mesh.nC)[:, self.indActive]
        return self._Pac

    @property
    def Pafx(self):
        """
        projection matrix that takes from the reduced space of active x-faces
        to full modelling space (ie. nFx x nindActive_Fx )

        :rtype: scipy.sparse.csr_matrix
        :return: active face-x projection matrix
        """
        if getattr(self, '_Pafx', None) is None:
            if self.indActive is None:
                self._Pafx = Utils.speye(self.mesh.nFx)
            else:
                indActive_Fx = (self.mesh.aveFx2CC.T * self.indActive) == 1
                self._Pafx = Utils.speye(self.mesh.nFx)[:, indActive_Fx]
        return self._Pafx

    @property
    def Pafy(self):
        """
        projection matrix that takes from the reduced space of active y-faces
        to full modelling space (ie. nFy x nindActive_Fy )

        :rtype: scipy.sparse.csr_matrix
        :return: active face-y projection matrix
        """
        if getattr(self, '_Pafy', None) is None:
            if self.indActive is None:
                self._Pafy = Utils.speye(self.mesh.nFy)
            else:
                indActive_Fy = (self.mesh.aveFy2CC.T * self.indActive) == 1
                self._Pafy = Utils.speye(self.mesh.nFy)[:, indActive_Fy]
        return self._Pafy

    @property
    def Pafz(self):
        """
        projection matrix that takes from the reduced space of active z-faces
        to full modelling space (ie. nFz x nindActive_Fz )

        :rtype: scipy.sparse.csr_matrix
        :return: active face-z projection matrix
        """
        if getattr(self, '_Pafz', None) is None:
            if self.indActive is None:
                self._Pafz = Utils.speye(self.mesh.nFz)
            else:
                indActive_Fz = (self.mesh.aveFz2CC.T * self.indActive) == 1
                self._Pafz = Utils.speye(self.mesh.nFz)[:, indActive_Fz]
        return self._Pafz

    @property
    def aveFx2CC(self):
        """
        averaging from active cell centers to active x-faces

        :rtype: scipy.sparse.csr_matrix
        :return: averaging from active cell centers to active x-faces
        """
        if getattr(self, '_aveFx2CC', None) is None:
            self._aveFx2CC = self.Pac.T * self.mesh.aveFx2CC * self.Pafx
        return self._aveFx2CC

    @property
    def aveCC2Fx(self):
        """
        averaging from active x-faces to active cell centers

        :rtype: scipy.sparse.csr_matrix
        :return: averaging matrix from active x-faces to active cell centers
        """
        if getattr(self, '_aveCC2Fx', None) is None:
            self._aveCC2Fx = (
                Utils.sdiag(1./(self.aveFx2CC.T).sum(1)) * self.aveFx2CC.T
            )
        return self._aveCC2Fx

    @property
    def aveFy2CC(self):
        """
        averaging from active cell centers to active y-faces

        :rtype: scipy.sparse.csr_matrix
        :return: averaging from active cell centers to active y-faces
        """
        if getattr(self, '_aveFy2CC', None) is None:
            self._aveFy2CC = self.Pac.T * self.mesh.aveFy2CC * self.Pafy
        return self._aveFy2CC

    @property
    def aveCC2Fy(self):
        """
        averaging from active y-faces to active cell centers

        :rtype: scipy.sparse.csr_matrix
        :return: averaging matrix from active y-faces to active cell centers
        """
        if getattr(self, '_aveCC2Fy', None) is None:
            self._aveCC2Fy = (
                Utils.sdiag(1./(self.aveFy2CC.T).sum(1)) * self.aveFy2CC.T
            )
        return self._aveCC2Fy

    @property
    def aveFz2CC(self):
        """
        averaging from active cell centers to active z-faces

        :rtype: scipy.sparse.csr_matrix
        :return: averaging from active cell centers to active z-faces
        """
        if getattr(self, '_aveFz2CC', None) is None:
            self._aveFz2CC = self.Pac.T * self.mesh.aveFz2CC * self.Pafz
        return self._aveFz2CC

    @property
    def aveCC2Fz(self):
        """
        averaging from active z-faces to active cell centers

        :rtype: scipy.sparse.csr_matrix
        :return: averaging matrix from active z-faces to active cell centers
        """
        if getattr(self, '_aveCC2Fz', None) is None:
            self._aveCC2Fz = (
                Utils.sdiag(1./(self.aveFz2CC.T).sum(1)) * self.aveFz2CC.T
            )
        return self._aveCC2Fz

    @property
    def cellDiffx(self):
        """
        cell centered difference in the x-direction

        :rtype: scipy.sparse.csr_matrix
        :return: differencing matrix for active cells in the x-direction
        """
        if getattr(self, '_cellDiffx', None) is None:
            self._cellDiffx = self.Pafx.T * self.mesh.cellGradx * self.Pac
        return self._cellDiffx

    @property
    def cellDiffy(self):
        """
        cell centered difference in the y-direction

        :rtype: scipy.sparse.csr_matrix
        :return: differencing matrix for active cells in the y-direction
        """
        if getattr(self, '_cellDiffy', None) is None:
            self._cellDiffy = self.Pafy.T * self.mesh.cellGrady * self.Pac
        return self._cellDiffy

    @property
    def cellDiffz(self):
        """
        cell centered difference in the z-direction

        :rtype: scipy.sparse.csr_matrix
        :return: differencing matrix for active cells in the z-direction
        """
        if getattr(self, '_cellDiffz', None) is None:
            self._cellDiffz = self.Pafz.T * self.mesh.cellGradz * self.Pac
        return self._cellDiffz

    @property
    def faceDiffx(self):
        """
        x-face differences

        :rtype: scipy.sparse.csr_matrix
        :return: differencing matrix for active faces in the x-direction
        """
        if getattr(self, '_faceDiffx', None) is None:
            self._faceDiffx = self.Pac.T * self.mesh.faceDivx * self.Pafx
        return self._faceDiffx

    @property
    def faceDiffy(self):
        """
        y-face differences

        :rtype: scipy.sparse.csr_matrix
        :return: differencing matrix for active faces in the y-direction
        """
        if getattr(self, '_faceDiffy', None) is None:
            self._faceDiffy = self.Pac.T * self.mesh.faceDivy * self.Pafy
        return self._faceDiffy

    @property
    def faceDiffz(self):
        """
        z-face differences

        :rtype: scipy.sparse.csr_matrix
        :return: differencing matrix for active faces in the z-direction
        """
        if getattr(self, '_faceDiffz', None) is None:
            self._faceDiffz = self.Pac.T * self.mesh.faceDivz * self.Pafz
        return self._faceDiffz

    @property
    def cellDiffxStencil(self):
        """
        cell centered difference stencil (no cell lengths include) in the
        x-direction

        :rtype: scipy.sparse.csr_matrix
        :return: differencing matrix for active cells in the x-direction
        """
        if getattr(self, '_cellDiffxStencil', None) is None:

            self._cellDiffxStencil = (
                self.Pafx.T * self.mesh._cellGradxStencil() * self.Pac
            )
        return self._cellDiffxStencil

    @property
    def cellDiffyStencil(self):
        """
        cell centered difference stencil (no cell lengths include) in the
        y-direction

        :rtype: scipy.sparse.csr_matrix
        :return: differencing matrix for active cells in the y-direction
        """
        if self.dim < 2:
            return None
        if getattr(self, '_cellDiffyStencil', None) is None:

            self._cellDiffyStencil = (
                self.Pafy.T * self.mesh._cellGradyStencil() * self.Pac
            )
        return self._cellDiffyStencil

    @property
    def cellDiffzStencil(self):
        """
        cell centered difference stencil (no cell lengths include) in the
        y-direction

        :rtype: scipy.sparse.csr_matrix
        :return: differencing matrix for active cells in the y-direction
        """
        if self.dim < 3:
            return None
        if getattr(self, '_cellDiffzStencil', None) is None:

            self._cellDiffzStencil = (
                self.Pafz.T * self.mesh._cellGradzStencil() * self.Pac
            )
        return self._cellDiffzStencil


class BaseRegularization(ObjectiveFunction.L2ObjectiveFunction):
    """
    Base class for regularization. Inherit this for building your own
    regularization. The base regularization assumes a weighted l2 style of
    regularization. However, if you wish to employ a different norm, the
    methods :meth:`_eval`, :meth:`deriv` and :meth:`deriv2` can be over-written

    **Optional Inputs**

    :param BaseMesh mesh: SimPEG mesh
    :param int nP: number of parameters
    :param IdentityMap mapping: regularization mapping, takes the model from model space to the space you want to regularize in
    :param numpy.ndarray mref: reference model
    :param numpy.ndarray indActive: active cell indices for reducing the size
    of differential operators in the definition of a regularization mesh

    """

    counter = None
    mapPair = Maps.IdentityMap  #: An IdentityMap Class

    mapping = None  #: An IdentityMap instance.
    mref = Utils.Zero()  #: Reference model, :class:`Utils.Zero` default

    indActive = None  #: active indices

    def __init__(self, mesh=None, nP=None, **kwargs):
        super(BaseRegularization, self).__init__(**kwargs)

        # Make sute the mesh is a SimPEG Mesh
        assert isinstance(mesh, Mesh.BaseMesh) or mesh is None, (
            "mesh must be a SimPEG.Mesh object."
        )
        self.mesh = mesh

        # ensure indActive are bools
        if self.indActive is not None:
            if self.indActive.dtype != 'bool':
                tmp = self.indActive
                self.indActive = np.zeros(mesh.nC, dtype=bool)  # This should be handled with properties??
                self.indActive[tmp] = True

            if self.mapping is None:
                self.mapping = Maps.IdentityMap(
                    nP=self.indActive.nonzero()[0].size
                )

        # create regularization mesh if using
        if self.mesh is not None:
            self.regmesh = RegularizationMesh(self.mesh, self.indActive)
        else:
            self.regmesh = None

        # set nP
        if self.mapping is not None:
            if nP is not None:
                warnings("overwriting nP with mapping.nP")
            self._nP = self.mapping.nP
        elif self.mesh is not None:
            if nP is not None:
                warnings("overwriting nP with mesh.nC")
            self._nP = self.regmesh.nC
        else:
            self._nP = nP

        # set mappings and make sure it is a SimPEG map
        self.mapping = self.mapping or self.mapPair(nP=self._nP)
        self.mapping._assertMatchesPair(self.mapPair)

    @Utils.timeIt
    def _eval(self, m):
        """
        We use a weighted 2-norm objective function

        .. math::

            r(m) = \\frac{1}{2}
        """
        r = self.W * (self.mapping * (m - self.mref))
        return 0.5 * r.dot(r)

    @Utils.timeIt
    def deriv(self, m):
        """

        The regularization is:

        .. math::

            R(m) = \\frac{1}{2}\mathbf{(m-m_\\text{ref})^\\top W^\\top
                   W(m-m_\\text{ref})}

        So the derivative is straight forward:

        .. math::

            R(m) = \mathbf{W^\\top W (m-m_\\text{ref})}

        """
        mD = self.mapping.deriv(m - self.mref)
        r = self.W * ( self.mapping * (m - self.mref) )
        return  mD.T * ( self.W.T * r )

    @Utils.timeIt
    def deriv2(self, m, v=None):
        """
        Second derivative

        :param numpy.array m: geophysical model
        :param numpy.array v: vector to multiply
        :rtype: scipy.sparse.csr_matrix
        :return: WtW, or if v is supplied WtW*v (numpy.ndarray)

        The regularization is:

        .. math::

            R(m) = \\frac{1}{2}\mathbf{(m-m_\\text{ref})^\\top W^\\top
            W(m-m_\\text{ref})}

        So the second derivative is straight forward:

        .. math::

            R(m) = \mathbf{W^\\top W}

        """
        mD = self.mapping.deriv(m - self.mref)
        if v is None:
            return mD.T * self.W.T * self.W * mD

        return mD.T * ( self.W.T * ( self.W * ( mD * v) ) )


class Smallness(BaseRegularization):
    """
    Smallness regularization - L2 regularization on the difference between a
    model and a reference model. Cell weights may be included.

    .. math::

        r(m) = \\frac{1}{2}(\mathbf{m} - \mathbf{m_ref})^\top \mathbf{W}^T
        \mathbf{W} (\mathbf{m} - \mathbf{m_{ref}})

    where :math:`\mathbf{m}` is the model, :math:`\mathbf{m_{ref}}` is a
    reference model (default Zero) and :math:`\mathbf{W}` is a weighting
    matrix (default Identity. If cell weights are provided, then it is
    :code:`diag(cell_weights)`)

    **Optional Inputs**

    :param BaseMesh mesh: SimPEG mesh
    :param int nP: number of parameters
    :param IdentityMap mapping: regularization mapping, takes the model from model space to the space you want to regularize in
    :param numpy.ndarray mref: reference model
    :param numpy.ndarray indActive: active cell indices for reducing the size
    of differential operators in the definition of a regularization mesh
    :param numpy.ndarray cell_weights: cell weights

    """

    cell_weights = None  #: apply cell weights?

    def __init__(self, mesh=None, **kwargs):
        if self.cell_weights is None:
            W = Utils.Identity()
        else:
            assert isinstance(self.cell_weights, np.ndarray), (
                "expecting numpy array for cell weights"
            )
            W = Utils.sdiag(self.cell_weights)

        super(Smallness, self).__init__(mesh=mesh, W=W, **kwargs)


class BaseSimpleSmooth(BaseRegularization):
    """
    Base Simple Smooth Regularization. This base class regularizes on the first
    spatial derivative, not considering length scales, in the provided
    orientation

    **Optional Inputs**

    :param BaseMesh mesh: SimPEG mesh
    :param int nP: number of parameters
    :param IdentityMap mapping: regularization mapping, takes the model from model space to the space you want to regularize in
    :param numpy.ndarray mref: reference model
    :param numpy.ndarray indActive: active cell indices for reducing the size of differential operators in the definition of a regularization mesh
    :param numpy.ndarray cell_weights: cell weights
    :param bool mrefInSmooth: include the reference model in the smoothness computation? (eg. look at Deriv of m (False) or Deriv of (m-mref) (True))
    :param numpy.ndarray cell_weights: vector of cell weights (applied in all terms)
    """

    mrefInSmooth = False  #: include mref in the smoothness?
    cell_weights = None  #: apply cell weights?

    def __init__(self, mesh, orientation='x', **kwargs):
        assert orientation in ['x', 'y', 'z'], (
            "Orientation must be 'x', 'y' or 'z'"
        )

        super(BaseSimpleSmooth, self).__init__(mesh=mesh, **kwargs)

        self.W = getattr(
            self.regmesh,
            "cellDiff{orientation}Stencil".format(orientation=orientation)
        )

        if self.mrefInSmooth is False:
            self.mref = Utils.Zero()


class SimpleSmooth_x(BaseSimpleSmooth):
    """
    Simple Smoothness along x. Regularizes on the first spatial derivative in the
    x-direction, not considering length scales
    """

    def __init__(self, mesh, **kwargs):

        super(SimpleSmooth_x, self).__init__(
            mesh=mesh, orientation='x', **kwargs
        )


class SimpleSmooth_y(BaseSimpleSmooth):
    """
    Simple Smoothness along x. Regularizes on the first spatial derivative in the
    y-direction, not considering length scales
    """

    def __init__(self, mesh, **kwargs):
        assert(mesh.dim > 1), (
            "Mesh must have at least 2 dimensions to regularize along the "
            "y-direction"
        )

        super(SimpleSmooth_y, self).__init__(
            mesh=mesh, orientation='y', **kwargs
        )


class SimpleSmooth_z(BaseSimpleSmooth):
    """
    Simple Smoothness along x. Regularizes on the first spatial derivative in the
    z-direction, not considering length scales
    """
    def __init__(self, mesh, **kwargs):

        assert(mesh.dim > 2), (
            "Mesh must have at least 3 dimensions to regularize along the "
            "z-direction"
        )

        super(SimpleSmooth_z, self).__init__(
            mesh=mesh, orientation='z', **kwargs
        )


class Simple(BaseRegularization):

    """
    Simple regularization that does not include length scales in the
    derivatives.

    .. math::

        r(\mathbf{m}) = \\alpha_s \phi_s + \\alpha_x \phi_x + \\alpha_y \phi_y +
            \\alpha_z \phi_z

    where:

    - :math:`\phi_s` is a :class:`SimPEG.Regularization.Smallness` instance
    - :math:`\phi_x` is a :class:`SimPEG.Regularization.SimpleSmooth_x` instance
    - :math:`\phi_y` is a :class:`SimPEG.Regularization.SimpleSmooth_y` instance
    - :math:`\phi_z` is a :class:`SimPEG.Regularization.SimpleSmooth_z` instance


    **Required Inputs**

    :param BaseMesh mesh: a SimPEG mesh

    **Optional Inputs**

    :param IdentityMap mapping: regularization mapping, takes the model from model space to the space you want to regularize in
    :param numpy.ndarray mref: reference model
    :param numpy.ndarray indActive: active cell indices for reducing the size of differential operators in the definition of a regularization mesh
    :param numpy.ndarray cell_weights: cell weights
    :param bool mrefInSmooth: include the reference model in the smoothness computation? (eg. look at Deriv of m (False) or Deriv of (m-mref) (True))
    :param numpy.ndarray cell_weights: vector of cell weights (applied in all terms)

    **Weighting Parameters**

    :param float alpha_s: weighting on the smallness (default 1.)
    :param float alpha_x: weighting on the x-smoothness (default 1.)
    :param float alpha_y: weighting on the y-smoothness (default 1.)
    :param float alpha_z: weighting on the z-smoothness(default 1.)

    """

    mrefInSmooth = False  #: include mref in the smoothness?
    alpha_s = 1.0  #: Smallness weights
    alpha_x = 1.0  #: Weight for the first derivative in the x direction
    alpha_y = 1.0  #: Weight for the first derivative in the y direction
    alpha_z = 1.0  #: Weight for the first derivative in the z direction

    def __init__(self, mesh, **kwargs):
        super(Simple, self).__init__(mesh=mesh, **kwargs)
        self = (
                self.alpha_s * Smallness(mesh=mesh, **kwargs) +
                self.alpha_x * SimpleSmooth_x(mesh=mesh, **kwargs)
        )
        if mesh.dim > 1:
            self += self.alpha_y * SimpleSmooth_y(mesh=mesh, **kwargs)
        if mesh.dim > 2:
            self += self.alpha_z * SimpleSmooth_z(mesh=mesh, **kwargs)


class BaseSmooth(BaseRegularization):
    """
    Base Smooth Regularization. This base class regularizes on the first
    spatial derivative in the provided orientation

    **Optional Inputs**

    :param BaseMesh mesh: SimPEG mesh
    :param int nP: number of parameters
    :param IdentityMap mapping: regularization mapping, takes the model from model space to the space you want to regularize in
    :param numpy.ndarray mref: reference model
    :param numpy.ndarray indActive: active cell indices for reducing the size of differential operators in the definition of a regularization mesh
    :param numpy.ndarray cell_weights: cell weights
    :param bool mrefInSmooth: include the reference model in the smoothness computation? (eg. look at Deriv of m (False) or Deriv of (m-mref) (True))
    :param numpy.ndarray cell_weights: vector of cell weights (applied in all terms)
    """

    mrefInSmooth = False  #: include mref in the smoothness?
    cell_weights = None  #: apply cell weights?

    def __init__(self, mesh, orientation='x', **kwargs):
        assert orientation in ['x', 'y', 'z'], (
                "Orientation must be 'x', 'y' or 'z'"
            )

        super(BaseSmooth, self).__init__(mesh=mesh, **kwargs)

        ave = getattr(
            self.regmesh,
            'aveCC2F{orientation}'.format(orientation=orientation)
        )

        if self.cell_weights is not None:
            Ave_vol = (ave * self.cell_weights * self.regmesh.vol)
        else:
            Ave_vol = ave * self.regmesh.vol
        self.W = (
            Utils.sdiag((Ave_vol)**0.5) *
            getattr(
                self.regmesh,
                "cellDiff{orientation}".format(orientation=orientation)
            )
        )

        if self.mrefInSmooth is False:
            self.mref = Utils.Zero()


class Smooth_x(BaseSmooth):
    """
    Smoothness along x. Regularizes on the first spatial derivative in the
    x-direction
    """

    def __init__(self, mesh, **kwargs):
        super(Smooth_x, self).__init__(mesh=mesh, orientation='x', **kwargs)


class Smooth_y(BaseSmooth):
    """
    Smoothness along y. Regularizes on the first spatial derivative in the
    y-direction
    """

    def __init__(self, mesh, **kwargs):
        assert(mesh.dim > 1), (
            "Mesh must have at least 2 dimensions to regularize along the "
            "y-direction"
        )

        super(Smooth_y, self).__init__(mesh=mesh, orientation='y', **kwargs)


class Smooth_z(BaseSmooth):
    """
    Smoothness along z. Regularizes on the first spatial derivative in the
    z-direction
    """
    def __init__(self, mesh, **kwargs):
        assert(mesh.dim > 2), (
            "Mesh must have at least 3 dimensions to regularize along the "
            "z-direction"
        )

        super(Smooth_z, self).__init__(mesh=mesh, orientation='z', **kwargs)


class BaseSmooth2(BaseRegularization):
    """
    Base Smooth Regularization. This base class regularizes on the second
    spatial derivative in the provided orientation

    **Optional Inputs**

    :param BaseMesh mesh: SimPEG mesh
    :param int nP: number of parameters
    :param IdentityMap mapping: regularization mapping, takes the model from model space to the space you want to regularize in
    :param numpy.ndarray mref: reference model
    :param numpy.ndarray indActive: active cell indices for reducing the size of differential operators in the definition of a regularization mesh
    :param numpy.ndarray cell_weights: cell weights
    :param bool mrefInSmooth: include the reference model in the smoothness computation? (eg. look at Deriv of m (False) or Deriv of (m-mref) (True))
    :param numpy.ndarray cell_weights: vector of cell weights (applied in all terms)
    """

    mrefInSmooth = False  #: include mref in the smoothness?
    cell_weights = None  #: apply cell weights?

    def __init__(self, mesh, orientation='x', **kwargs):
        super(BaseSmooth2, self).__init__(mesh=mesh, **kwargs)

        vol = self.regmesh.vol
        if self.cell_weights is not None:
            vol *= self.cell_weights

        self.W = (
            Utils.sdiag(vol**0.5) *
            getattr(
                self.regmesh,
                'faceDiff{orientation}'.format(orientation=orientation)
            ) *
            getattr(
                self.regmesh,
                'cellDiff{orientation}'.format(orientation=orientation)
            )
        )


class Smooth_xx(BaseSmooth2):
    """
    Second-order smoothness along x. Regularizes on the second spatial
    derivative in the x-direction
    """
    def __init__(self, mesh, **kwargs):
        super(Smooth_xx, self).__init__(mesh=mesh, orientation='x', **kwargs)


class Smooth_yy(BaseRegularization):
    """
    Second-order smoothness along y. Regularizes on the second spatial
    derivative in the y-direction
    """
    def __init__(self, mesh, **kwargs):
        assert(mesh.dim > 1), (
            "Mesh must have at least 2 dimensions to regularize along the "
            "y-direction"
        )
        super(Smooth_yy, self).__init__(mesh=mesh, orientation='y', **kwargs)


class Smooth_zz(BaseRegularization):
    """
    Second-order smoothness along z. Regularizes on the second spatial
    derivative in the z-direction
    """

    def __init__(self, mesh, **kwargs):
        assert(mesh.dim > 2), (
            "Mesh must have at least 3 dimensions to regularize along the "
            "z-direction"
        )
        super(Smooth_zz, self).__init__(mesh=mesh, orientation='z', **kwargs)


class Tikhonov(BaseRegularization, ObjectiveFunction.ComboObjectiveFunction):
    """
    L2 Tikhonov regularization with both smallness and smoothness (first order
    derivative) contributions.

    .. math::
        \phi_m(\mathbf{m}) = \\alpha_s \| W_s (\mathbf{m} - \mathbf{m_{ref}} ) \|^2
        + \\alpha_x \| W_x \\frac{\partial}{\partial x} (\mathbf{m} - \mathbf{m_{ref}} ) \|^2
        + \\alpha_y \| W_y \\frac{\partial}{\partial y} (\mathbf{m} - \mathbf{m_{ref}} ) \|^2
        + \\alpha_z \| W_z \\frac{\partial}{\partial z} (\mathbf{m} - \mathbf{m_{ref}} ) \|^2

    Note if the key word argument `mrefInSmooth` is False, then mref is not
    included in the smoothness contribution.

    :param BaseMesh mesh: SimPEG mesh
    :param IdentityMap mapping: regularization mapping, takes the model from model space to the thing you want to regularize
    :param numpy.ndarray indActive: active cell indices for reducing the size of differential operators in the definition of a regularization mesh
    :param bool mrefInSmooth: (default = False) put mref in the smoothness component?
    :param float alpha_s: (default 1e-6) smallness weight
    :param float alpha_x: (default 1) smoothness weight for first derivative in the x-direction
    :param float alpha_y: (default 1) smoothness weight for first derivative in the y-direction
    :param float alpha_z: (default 1) smoothness weight for first derivative in the z-direction
    :param float alpha_xx: (default 1) smoothness weight for second derivative in the x-direction
    :param float alpha_yy: (default 1) smoothness weight for second derivative in the y-direction
    :param float alpha_zz: (default 1) smoothness weight for second derivative in the z-direction
    """

    mrefInSmooth = False  #: include mref in the smoothness?
    alpha_s = 1e-6  #: Smallness weights
    alpha_x = 1.0  #: Weight for the first derivative in the x direction
    alpha_y = 1.0  #: Weight for the first derivative in the y direction
    alpha_z = 1.0  #: Weight for the first derivative in the z direction
    alpha_xx = Utils.Zero() #: Weight for the second derivative in the x direction
    alpha_yy = Utils.Zero() #: Weight for the second derivative in the y direction
    alpha_zz = Utils.Zero() #: Weight for the second derivative in the z direction

    def __init__(self, mesh, **kwargs):


        objfcts = [
            Smallness(mesh=mesh, **kwargs),
            Smooth_x(mesh=mesh, **kwargs),
            Smooth_xx(mesh=mesh, **kwargs)
        ]
        multipliers = [self.alpha_s, self.alpha_x, self.alpha_xx]

        if mesh.dim > 1:
            objfcts.append(
                [Smooth_y(mesh=mesh, **kwargs), Smooth_yy(mesh=mesh, **kwargs)]
            )
            multipliers.append([self.alpha_y, self.alpha_yy])

        if mesh.dim > 2:
            objfcts.append(
                [Smooth_z(mesh=mesh, **kwargs), Smooth_zz(mesh=mesh, **kwargs)]
            )
            multipliers.append([self.alpha_z, self.alpha_zz])

        super(Tikhonov, self).__init__(
            objfcts=objfcts, multipliers=multipliers, mesh=mesh, **kwargs
        )


class BaseSparse(BaseRegularization):
    """
    The regularization is:

    .. math::

        R(m) = \\frac{1}{2}\mathbf{(m-m_\\text{ref})^\\top W^\\top R^\\top R W(m-m_\\text{ref})}

    where the IRLS weight

    .. math::

        R = \eta TO FINISH LATER!!!

    So the derivative is straight forward:

    .. math::

        R(m) = \mathbf{W^\\top R^\\top R W (m-m_\\text{ref})}

    The IRLS weights are recomputed after each beta solves.
    It is strongly recommended to do a few Gauss-Newton iterations
    before updating.
    """

    # set default values
    eps_p = 1e-1  #: Threshold value for the model norm
    eps_q = 1e-1  #: Threshold value for the model gradient norm
    model = None  #: Requires model to compute the weights
    l2model = None
    gamma = 1.  #: Model norm scaling to smooth out convergence
    # norms = [0., 2., 2., 2.]  #: Values for norm on (m, dmdx, dmdy, dmdz)
    cell_weights = None  #: Consider overwriting with sensitivity weights

    def __init__(self, mesh, **kwargs):
        super(BaseSparse, self).__init__(mesh=mesh, **kwargs)

        if self.cell_weights is None:
            self.cell_weights = np.ones(self.regmesh.nC)
        else:
            assert isinstance(self.cell_weights, np.ndarray), (
                "expecting numpy array for cell weights"
            )

    def R(self, f_m , eps, exponent):

        # Eta scaling is important for mix-norms...do not mess with it
        eta = (eps**(1.-exponent/2.))**0.5
        r = eta / (f_m**2. + eps**2.)**((1.-exponent/2.)/2.)

        return r


class SparseSmallness(BaseSparse):
    """
    Sparse smallness regularization

    **Inputs**

    :param int norm: norm on the smallness
    """

    norm = 0  #: norm on m (smallness)

    def __init__(self, mesh, **kwargs):
        super(SparseSmallness, self).__init__(mesh=mesh, **kwargs)

        if getattr(self, 'model', None) is None:
            R = Utils.speye(self.regmesh.nC)

        else:
            f_m = self.mapping * (self.model - self.mref)
            r = self.R(f_m , self.eps_p, self.norms[0])
            R = Utils.sdiag( self.r )

        self.W = Utils.sdiag((self.gamma*self.cell_weights)**0.5) * R


class Sparse_x(BaseSparse):
    """
    Regularization on the first derivative in the x-direction
    """

    norm = 2  #: norm employed

    def __init__(self, mesh, **kwargs):

        super(Sparse_x, self).__init__(mesh=mesh, **kwargs)

        if getattr(self, 'model', None) is None:
            R = Utils.speye(self.regmesh.cellDiffxStencil.shape[0])

        else:
            f_m = self.regmesh.cellDiffxStencil * (self.mapping * self.model)
            r = self.R(f_m , self.eps_q, self.norm)
            R = Utils.sdiag(r)

        self.W = (
            Utils.sdiag(
                (self.gamma*(self.regmesh.aveCC2Fx*self.cell_weights))**0.5
            ) *
            R * self.regmesh.cellDiffxStencil
        )


class Sparse_y(BaseSparse):
    """
    Regularization on the first derivative in the y-direction
    """

    norm = 2  #: norm employed

    def __init__(self, mesh, **kwargs):

        assert mesh.dim > 1, (
            "Mesh must have at least 2 dimensions to regularize along the "
            "y-direction"
        )

        super(Sparse_y, self).__init__(mesh=mesh, **kwargs)

        if getattr(self, 'model', None) is None:
            R = Utils.speye(self.regmesh.cellDiffyStencil.shape[0])

        else:
            f_m = self.regmesh.cellDiffyStencil * (self.mapping * self.model)
            r = self.R(f_m , self.eps_q, self.norm)
            R = Utils.sdiag(r)

        self.W = (
            Utils.sdiag(
                (self.gamma*(self.regmesh.aveCC2Fy*self.cell_weights))**0.5
            ) *
            R * self.regmesh.cellDiffyStencil
        )


class Sparse_z(BaseSparse):

    norm = 2  #: norm employed

    def __init__(self, mesh, **kwargs):

        assert mesh.dim > 2, (
            "Mesh must have at least 3 dimensions to regularize along the "
            "z-direction"
        )

        super(Sparse_z, self).__init__(mesh=mesh, **kwargs)

        if getattr(self, 'model', None) is None:
                R = Utils.speye(self.regmesh.cellDiffzStencil.shape[0])

        else:
            f_m = self.regmesh.cellDiffzStencil * (self.mapping * self.model)
            r = self.R(f_m , self.eps_q, self.norm)
            R = Utils.sdiag(r)

        self.Wz = (
            Utils.sdiag(
                (self.gamma*(self.regmesh.aveCC2Fz*self.cell_weights))**0.5
            ) *
            R * self.regmesh.cellDiffzStencil
        )


class Sparse(BaseSparse, ObjectiveFunction.ComboObjectiveFunction):

    norms = [0., 2., 2., 2.]
    alpha_s = 1.
    alpha_x = 1.
    alpha_y = 1.
    alpha_z = 1.

    def __init__(self, mesh, **kwargs):

        objfcts = [
            SparseSmallness(mesh=mesh, norm=self.norms[0], **kwargs),
            Sparse_x(mesh=mesh, norm=self.norms[1], **kwargs)
        ]
        multipliers = [
            self.alpha_s,
            self.alpha_x
        ]

        if mesh.dim > 1:
            objfcts.append(
                Sparse_y(mesh=mesh, norm=self.norms[2], **kwargs)
            )
            multipliers.append(self.alpha_y)

        if mesh.dim > 2:
            objfcts.append(
                Sparse_z(mesh=mesh, norm=self.norms[3], **kwargs)
            )
            multipliers.append(self.alpha_z)

        super(Sparse, self).__init__(
            objfcts=objfcts, multipliers=multipliers, mesh=mesh, **kwargs
        )

        # self = (
        #     self.alpha_s * SparseSmallness(
        #         mesh=mesh, norm=self.norms[0], **kwargs
        #     ) +
        #     self.alpha_x * Sparse_x(mesh=mesh, norm=self.norms[1], **kwargs)
        # )
        # if mesh.dim > 1:
        #     self += (
        #         self.alpha_y * Sparse_y(mesh=mesh, norm=self.norms[2], **kwargs)
        #     )
        # if mesh.dim > 2:
        #     self += (
        #         self.alpha_z * Sparse_z(mesh=mesh, norm=self.norms[3], **kwargs)
        #     )

# class Sparse(Simple):
#     """
#         The regularization is:

#         .. math::

#             R(m) = \\frac{1}{2}\mathbf{(m-m_\\text{ref})^\\top W^\\top R^\\top R W(m-m_\\text{ref})}

#         where the IRLS weight

#         .. math::

#             R = \eta TO FINISH LATER!!!

#         So the derivative is straight forward:

#         .. math::

#             R(m) = \mathbf{W^\\top R^\\top R W (m-m_\\text{ref})}

#         The IRLS weights are recomputed after each beta solves.
#         It is strongly recommended to do a few Gauss-Newton iterations
#         before updating.
#     """

#     # set default values
#     eps_p = 1e-1        # Threshold value for the model norm
#     eps_q = 1e-1        # Threshold value for the model gradient norm
#     model = None     # Requires model to compute the weights
#     l2model = None
#     gamma = 1.          # Model norm scaling to smooth out convergence
#     norms = [0., 2., 2., 2.] # Values for norm on (m, dmdx, dmdy, dmdz)
#     cell_weights = 1.        # Consider overwriting with sensitivity weights

#     def __init__(self, mesh, mapping=None, indActive=None, **kwargs):
#         Simple.__init__(self, mesh, mapping=mapping, indActive=indActive, **kwargs)

#         if isinstance(self.cell_weights,float):
#             self.cell_weights = np.ones(self.regmesh.nC) * self.cell_weights

#     @property
#     def Wsmall(self):
#         """Regularization matrix Wsmall"""
#         if getattr(self,'_Wsmall', None) is None:
#             if getattr(self, 'model', None) is None:
#                 self.Rs = Utils.speye(self.regmesh.nC)

#             else:
#                 f_m = self.mapping * (self.model - self.reg.mref)
#                 self.rs = self.R(f_m , self.eps_p, self.norms[0])
#                 self.Rs = Utils.sdiag( self.rs )

#             self._Wsmall = Utils.sdiag((self.alpha_s*self.gamma*self.cell_weights)**0.5)*self.Rs

#         return self._Wsmall

#     @property
#     def Wx(self):
#         """Regularization matrix Wx"""
#         if getattr(self,'_Wx', None) is None:
#             if getattr(self, 'model', None) is None:
#                 self.Rx = Utils.speye(self.regmesh.cellDiffxStencil.shape[0])

#             else:
#                 f_m = self.regmesh.cellDiffxStencil * (self.mapping * self.model)
#                 self.rx = self.R( f_m , self.eps_q, self.norms[1])
#                 self.Rx = Utils.sdiag( self.rx )

#             self._Wx = Utils.sdiag(( self.alpha_x*self.gamma*(self.regmesh.aveCC2Fx*self.cell_weights))**0.5)*self.Rx*self.regmesh.cellDiffxStencil

#         return self._Wx

#     @property
#     def Wy(self):
#         """Regularization matrix Wy"""
#         if getattr(self,'_Wy', None) is None:
#             if getattr(self, 'model', None) is None:
#                 self.Ry = Utils.speye(self.regmesh.cellDiffyStencil.shape[0])

#             else:
#                 f_m = self.regmesh.cellDiffyStencil * (self.mapping * self.model)
#                 self.ry = self.R( f_m , self.eps_q, self.norms[2])
#                 self.Ry = Utils.sdiag( self.ry )

#             self._Wy = Utils.sdiag((self.alpha_y*self.gamma*(self.regmesh.aveCC2Fy*self.cell_weights))**0.5)*self.Ry*self.regmesh.cellDiffyStencil

#         return self._Wy

#     @property
#     def Wz(self):
#         """Regularization matrix Wz"""
#         if getattr(self,'_Wz', None) is None:
#             if getattr(self, 'model', None) is None:
#                 self.Rz = Utils.speye(self.regmesh.cellDiffzStencil.shape[0])

#             else:
#                 f_m = self.regmesh.cellDiffzStencil * (self.mapping * self.model)
#                 self.rz = self.R( f_m , self.eps_q, self.norms[3])
#                 self.Rz = Utils.sdiag( self.rz )

#             self._Wz = Utils.sdiag((self.alpha_z*self.gamma*(self.regmesh.aveCC2Fz*self.cell_weights))**0.5)*self.Rz*self.regmesh.cellDiffzStencil

#         return self._Wz

#     def R(self, f_m , eps, exponent):

#         # Eta scaling is important for mix-norms...do not mess with it
#         eta = (eps**(1.-exponent/2.))**0.5
#         r = eta / (f_m**2.+ eps**2.)**((1.-exponent/2.)/2.)

#         return r
