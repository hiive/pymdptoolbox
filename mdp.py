# -*- coding: utf-8 -*-
"""
Copyright (c) 2011, 2012, 2013 Steven Cordwell
Copyright (c) 2009, Iadine Chadès
Copyright (c) 2009, Marie-Josée Cros
Copyright (c) 2009, Frédérick Garcia
Copyright (c) 2009, Régis Sabbadin

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

  * Redistributions of source code must retain the above copyright notice, this
    list of conditions and the following disclaimer.
  * Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.
  * Neither the name of the <ORGANIZATION> nor the names of its contributors
    may be used to endorse or promote products derived from this software
    without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from numpy import absolute, array, diag, matrix, mean, mod, multiply, ndarray
from numpy import nonzero, ones, zeros
from numpy.random import rand
from math import ceil, log, sqrt
from random import randint, random
from scipy.sparse import csr_matrix as sparse
from time import time

mdperr = {
"mat_nonneg" :
    "PyMDPtoolbox: Probabilities must be non-negative.",
"mat_square" :
    "PyMDPtoolbox: The matrix must be square.",
"mat_stoch" :
    "PyMDPtoolbox: Rows of the matrix must sum to one (1).",
"mask_numpy" :
    "PyMDPtoolbox: mask must be a numpy array or matrix; i.e. type(mask) is "
    "ndarray or type(mask) is matrix.", 
"mask_SbyS" : 
    "PyMDPtoolbox: The mask must have shape SxS; i.e. mask.shape = (S, S).",
"obj_shape" :
    "PyMDPtoolbox: Object arrays for transition probabilities and rewards "
    "must have only 1 dimension: the number of actions A. Each element of "
    "the object array contains an SxS ndarray or matrix.",
"obj_square" :
    "PyMDPtoolbox: Each element of an object array for transition "
    "probabilities and rewards must contain an SxS ndarray or matrix; i.e. "
    "P[a].shape = (S, S) or R[a].shape = (S, S).",
"P_type" :
    "PyMDPtoolbox: The transition probabilities must be in a numpy array; "
    "i.e. type(P) is ndarray.",
"P_shape" :
    "PyMDPtoolbox: The transition probability array must have the shape "
    "(A, S, S)  with S : number of states greater than 0 and A : number of "
    "actions greater than 0. i.e. R.shape = (A, S, S)",
"PR_incompat" :
    "PyMDPtoolbox: Incompatibility between P and R dimensions.",
"prob_in01" :
    "PyMDPtoolbox: Probability p must be in [0; 1].",
"R_type" :
    "PyMDPtoolbox: The rewards must be in a numpy array; i.e. type(R) is "
    "ndarray, or numpy matrix; i.e. type(R) is matrix.",
"R_shape" :
    "PyMDPtoolbox: The reward matrix R must be an array of shape (A, S, S) or "
    "(S, A) with S : number of states greater than 0 and A : number of actions "
    "greater than 0. i.e. R.shape = (S, A) or (A, S, S).",
"R_gt_0" :
    "PyMDPtoolbox: The rewards must be greater than 0.",
"S_gt_1" :
    "PyMDPtoolbox: Number of states S must be greater than 1.",
"SA_gt_1" : 
    "PyMDPtoolbox: The number of states S and the number of actions A must be "
    "greater than 1.",
"discount_rng" : 
    "PyMDPtoolbox: Discount rate must be in ]0; 1]",
"maxi_min" :
    "PyMDPtoolbox: The maximum number of iterations must be greater than 0"
}

def check(P, R):
    """Checks if the matrices P and R define a Markov Decision Process.
    
    Let S = number of states, A = number of actions.
    The transition matrix P must be on the shape (A, S, S) and P[a,:,:]
    must be stochastic.
    The reward matrix R must be on the shape (A, S, S) or (S, A).
    Raises an error if P and R do not define a MDP.
    
    Parameters
    ---------
    P : transition matrix (A, S, S)
        P could be an array with 3 dimensions or a object array (A, ),
        each cell containing a matrix (S, S) possibly sparse
    R : reward matrix (A, S, S) or (S, A)
        R could be an array with 3 dimensions (SxSxA) or a object array
        (A, ), each cell containing a sparse matrix (S, S) or a 2D
        array(S, A) possibly sparse  
    """
    
    # Check of P
    # tranitions must be a numpy array either an AxSxS ndarray (with any 
    # dtype other than "object"); or, a 1xA ndarray with a "object" dtype, 
    # and each element containing an SxS array. An AxSxS array will be
    # be converted to an object array. A numpy object array is similar to a
    # MATLAB cell array.
    if (not type(P) is ndarray):
        raise TypeError(mdperr["P_type"])
    
    if (not type(R) is ndarray):
        raise TypeError(mdperr["R_type"])
    
    # NumPy has an array type of 'object', which is roughly equivalent to
    # the MATLAB cell array. These are most useful for storing sparse
    # matrices as these can only have two dimensions whereas we want to be
    # able to store a transition matrix for each action. If the dytpe of
    # the transition probability array is object then we store this as
    # P_is_object = True.
    # If it is an object array, then it should only have one dimension
    # otherwise fail with a message expalining why.
    # If it is a normal array then the number of dimensions must be exactly
    # three, otherwise fail with a message explaining why.
    if (P.dtype == object):
        if (P.ndim > 1):
            raise ValueError(mdperr["obj_shape"])
        else:
            P_is_object = True
    else:
        if (P.ndim != 3):
            raise ValueError(mdperr["P_shape"])
        else:
            P_is_object = False
    
    # As above but for the reward array. A difference is that the reward
    # array can have either two or 3 dimensions.
    if (R.dtype == object):
        if (R.ndim > 1):
            raise ValueError(mdperr["obj_shape"])
        else:
            R_is_object = True
    else:
        if (not R.ndim in (2, 3)):
            raise ValueError(mdperr["R_shape"])
        else:
            R_is_object = False
    
    # We want to make sure that the transition probability array and the 
    # reward array are in agreement. This means that both should show that
    # there are the same number of actions and the same number of states.
    # Furthermore the probability of transition matrices must be SxS in
    # shape, so we check for that also.
    if P_is_object:
        # If the user has put their transition matrices into a numpy array
        # with dtype of 'object', then it is possible that they have made a
        # mistake and not all of the matrices are of the same shape. So,
        # here we record the number of actions and states that the first
        # matrix in element zero of the object array says it has. After
        # that we check that every other matrix also reports the same
        # number of actions and states, otherwise fail with an error.
        # aP: the number of actions in the transition array. This
        # corresponds to the number of elements in the object array.
        aP = P.shape[0]
        # sP0: the number of states as reported by the number of rows of
        # the transition matrix
        # sP1: the number of states as reported by the number of columns of
        # the transition matrix
        sP0, sP1 = P[0].shape
        # Now we check to see that every element of the object array holds
        # a matrix of the same shape, otherwise fail.
        for aa in range(1, aP):
            # sp0aa and sp1aa represents the number of states in each
            # subsequent element of the object array. If it doesn't match
            # what was found in the first element, then we need to fail
            # telling the user what needs to be fixed.
            sP0aa, sP1aa = P[aa].shape
            if ((sP0aa != sP0) or (sP1aa != sP1)):
                raise ValueError(mdperr["obj_square"])
    else:
        # if we are using a normal array for this, then the first
        # dimension should be the number of actions, and the second and 
        # third should be the number of states
        aP, sP0, sP1 = P.shape
    
    # the first dimension of the transition matrix must report the same
    # number of states as the second dimension. If not then we are not
    # dealing with a square matrix and it is not a valid transition
    # probability. Also, if the number of actions is less than one, or the
    # number of states is less than one, then it also is not a valid
    # transition probability.
    if ((sP0 < 1) or (aP < 1) or (sP0 != sP1)):
        raise ValueError(mdperr["P_shape"])
    
    # now we check that each transition matrix is square-stochastic. For
    # object arrays this is the matrix held in each element, but for
    # normal arrays this is a matrix formed by taking a slice of the array
    for aa in range(aP):
        if P_is_object:
            checkSquareStochastic(P[aa])
        else:
            checkSquareStochastic(P[aa, :, :])
        # aa = aa + 1 # why was this here?
    
    if R_is_object:
        # if the rewarad array has an object dtype, then we check that
        # each element contains a matrix of the same shape as we did 
        # above with the transition array.
        aR = R.shape[0]
        sR0, sR1 = R[0].shape
        for aa in range(1, aR):
            sR0aa, sR1aa = R[aa].shape
            if ((sR0aa != sR0) or (sR1aa != sR1)):
                raise ValueError(mdperr["obj_square"])
    elif (R.ndim == 3):
        # This indicates that the reward matrices are constructed per 
        # transition, so that the first dimension is the actions and
        # the second two dimensions are the states.
        aR, sR0, sR1 = R.shape
    else:
        # then the reward matrix is per state, so the first dimension is 
        # the states and the second dimension is the actions.
        sR0, aR = R.shape
        # this is added just so that the next check doesn't error out
        # saying that sR1 doesn't exist
        sR1 = sR0
    
    # the number of actions must be more than zero, the number of states
    # must also be more than 0, and the states must agree
    if ((sR0 < 1) or (aR < 1) or (sR0 != sR1)):
        raise ValueError(mdperr["R_shape"])
    
    # now we check to see that what the transition array is reporting and
    # what the reward arrar is reporting agree as to the number of actions
    # and states. If not then fail explaining the situation
    if (sP0 != sR0) or (aP != aR):
        raise ValueError(mdperr["PR_incompat"])
        
    # We are at the end of the checks, so if no exceptions have been raised
    # then that means there are (hopefullly) no errors and we return None
    return None

def checkSquareStochastic(Z):
    """Check if Z is a square stochastic matrix
    
    Parameters
    ----------
    Z : a SxS matrix. It could be a numpy ndarray SxS, or a scipy.sparse 
        csr_matrix
    
    Evaluation
    ----------
    Returns None if no error has been detected
    """
    s1, s2 = Z.shape
    if (s1 != s2):
        raise ValueError(mdperr["mat_square"])
    elif (absolute(Z.sum(axis=1) - ones(s2))).max() > 10**(-12):
        raise ValueError(mdperr["mat_stoch"])
    elif ((type(Z) is ndarray) or (type(Z) is matrix)) and (Z < 0).any():
        raise ValueError(mdperr["mat_nonneg"])
    elif (type(Z) is sparse) and (Z.data < 0).any():
        raise ValueError(mdperr["mat_nonneg"]) 
    else:
        return(None)

def exampleForest(S=3, r1=4, r2=2, p=0.1):
    """
    Generates a Markov Decision Process example based on a simple forest
    management.
    
    See the related documentation for more detail.
    
    Parameters
    ---------
    S : number of states (> 0), optional (default 3)
    r1 : reward when forest is in the oldest state and action Wait is performed,
        optional (default 4)
    r2 : reward when forest is in the oldest state and action Cut is performed, 
        optional (default 2)
    p : probability of wild fire occurence, in ]0, 1[, optional (default 0.1)
    
    Evaluation
    ----------
    P : transition probability matrix (A, S, S)
    R : reward matrix (S, A)
    
    Examples
    --------
    >>> import mdp
    >>> P, R = mdp.exampleForest()
    >>> P
    array([[[ 0.1,  0.9,  0. ],
            [ 0.1,  0. ,  0.9],
            [ 0.1,  0. ,  0.9]],

           [[ 1. ,  0. ,  0. ],
            [ 1. ,  0. ,  0. ],
            [ 1. ,  0. ,  0. ]]])
    >>> R
    array([[ 0.,  0.],
           [ 0.,  1.],
           [ 4.,  2.]])
    
    """
    if (S <= 1):
        raise ValueError(mdperr["S_gt_1"])
    if (r1 <= 0) or (r2 <= 0):
        raise ValueError(mdperr["R_gt_0"])
    if (p < 0 or p > 1):
        raise ValueError(mdperr["prob_in01"])
    
    # Definition of Transition matrix P(:,:,1) associated to action Wait (action 1) and
    # P(:,:,2) associated to action Cut (action 2)
    #             | p 1-p 0.......0  |                  | 1 0..........0 |
    #             | .  0 1-p 0....0  |                  | . .          . |
    #  P(:,:,1) = | .  .  0  .       |  and P(:,:,2) =  | . .          . |
    #             | .  .        .    |                  | . .          . |
    #             | .  .         1-p |                  | . .          . |
    #             | p  0  0....0 1-p |                  | 1 0..........0 |
    P = zeros((2, S, S))
    P[0, :, :] = (1 - p) * diag(ones(S - 1), 1)
    P[0, :, 0] = p
    P[0, S - 1, S - 1] = (1 - p)
    P[1, :, :] = zeros((S, S))
    P[1, :, 0] = 1
    
    # Definition of Reward matrix R1 associated to action Wait and 
    # R2 associated to action Cut
    #           | 0  |                   | 0  |
    #           | .  |                   | 1  |
    #  R(:,1) = | .  |  and     R(:,2) = | .  |	
    #           | .  |                   | .  |
    #           | 0  |                   | 1  |                   
    #           | r1 |                   | r2 |
    R = zeros((S, 2))
    R[S - 1, 0] = r1
    R[:, 1] = ones(S)
    R[0, 1] = 0
    R[S - 1, 1] = r2
    
    return (P, R)

def exampleRand(S, A, is_sparse=False, mask=None):
    """Generates a random Markov Decision Process.
    
    Parameters
    ----------
    S : number of states (> 0)
    A : number of actions (> 0)
    is_sparse : false to have matrices in plain format, true to have sparse
        matrices optional (default false).
    mask : matrix with 0 and 1 (0 indicates a place for a zero
           probability), optional (SxS) (default, random)
    
    Returns
    ----------
    P : transition probability matrix (SxSxA)
    R : reward matrix (SxSxA)

    Examples
    --------
    >>> import mdp
    >>> P, R = mdp.exampleRand(5, 3)

    """
    if (S < 1 or A < 1):
        raise ValueError(mdperr["SA_gt_1"])
    
    try:
        if (mask != None) and ((mask.shape[0] != S) or (mask.shape[1] != S)):
            raise ValueError(mdperr["mask_SbyS"])
    except AttributeError:
        raise TypeError(mdperr["mask_numpy"])
    
    if mask == None:
        mask = rand(A, S, S)
        for a in range(A):
            r = random()
            mask[a][mask[a] < r] = 0
            mask[a][mask[a] >= r] = 1
    
    if is_sparse:
        # definition of transition matrix : square stochastic matrix
        P = zeros((A, ), dtype=object)
        # definition of reward matrix (values between -1 and +1)
        R = zeros((A, ), dtype=object)
        for a in range(A):
            PP = mask[a] * rand(S, S)
            for s in range(S):
                if (mask[a, s, :].sum() == 0):
                    PP[s, randint(0, S - 1)] = 1
                PP[s, :] = PP[s, :] / PP[s, :].sum()
            P[a] = sparse(PP)
            R[a] = sparse(mask[a] * (2 * rand(S, S) - ones((S, S))))
    else:
        # definition of transition matrix : square stochastic matrix
        P = zeros((A, S, S))
        # definition of reward matrix (values between -1 and +1)
        R = zeros((A, S, S))
        for a in range(A):
            P[a, :, :] = mask[a] * rand(S, S)
            for s in range(S):
                if (mask[a, s, :].sum() == 0):
                    P[a, s, randint(0, S - 1)] = 1
                P[a, s, :] = P[a, s, :] / P[a, s, :].sum()
            R[a, :, :] = mask[a] * (2 * rand(S, S) - ones((S, S), dtype=int))
    
    return (P, R)

def getSpan(self, W):
    """Returns the span of W
    
    sp(W) = max W(s) - min W(s)
    """
    return (W.max() - W.min())

class MDP(object):
    """The Markov Decision Problem Toolbox."""
    
    def __init__(self, transitions, reward, discount, max_iter):
        """"""
        
        # if the discount is None then the algorithm is assumed to not use it
        # in its computations
        if (type(discount) is int) or (type(discount) is float):
            if (discount <= 0) or (discount > 1):
                raise ValueError(mdperr["discount_rng"])
            else:
                self.discount = discount
        elif not discount is None:
            raise ValueError("PyMDPtoolbox: the discount must be a positive " \
                "real number less than or equal to one.")
        
        # if the max_iter is None then the algorithm is assumed to not use it
        # in its computations
        if (type(max_iter) is int) or (type(max_iter) is float):
            if (max_iter <= 0):
                raise ValueError(mdperr["maxi_min"])
            else:
                self.max_iter = max_iter
        elif not max_iter is None:
            raise ValueError("PyMDPtoolbox: max_iter must be a positive real "\
                "number greater than zero.")
        
        # we run a check on P and R to make sure they are describing an MDP. If
        # an exception isn't raised then they are assumed to be correct.
        check(transitions, reward)
        
        # computePR will assign the variables self.S, self.A, self.P and self.R
        self.computePR(transitions, reward)
        
        # the verbosity is by default turned off
        self.verbose = False
        # Initially the time taken to perform the computations is set to None
        self.time = None
        # set the initial iteration count to zero
        self.iter = 0
        
        self.value = None
        self.policy = None
    
    def bellmanOperator(self):
        """
        Applies the Bellman operator on the value function.
        
        Updates the value function and the Vprev-improving policy.
        
        Returns
        -------
        (policy, value) : tuple of new policy and its value
        """
        Q = matrix(zeros((self.S, self.A)))
        for aa in range(self.A):
            Q[:, aa] = self.R[:, aa] + (self.discount * self.P[aa] * self.value)
        
        # Which way is better? if choose the first way, then the classes that
        # call this function must be changed
        # 1. Return, (policy, value)
        return (Q.argmax(axis=1), Q.max(axis=1))
        # 2. update self.policy and self.value directly
        # self.value = Q.max(axis=1)
        # self.policy = Q.argmax(axis=1)
    
    def computePpolicyPRpolicy(self):
        """Computes the transition matrix and the reward matrix for a policy

        Arguments
        ---------
        Let S = number of states, A = number of actions
        P(SxSxA)  = transition matrix 
             P could be an array with 3 dimensions or 
             a cell array (1xA), each cell containing a matrix (SxS) possibly sparse
        R(SxSxA) or (SxA) = reward matrix
             R could be an array with 3 dimensions (SxSxA) or 
             a cell array (1xA), each cell containing a sparse matrix (SxS) or
             a 2D array(SxA) possibly sparse  
        policy(S) = a policy
        
        Evaluation
        ----------
        Ppolicy(SxS)  = transition matrix for policy
        PRpolicy(S)   = reward matrix for policy
        """
        Ppolicy = matrix(zeros((self.S, self.S)))
        Rpolicy = matrix(zeros((self.S, 1)))
        for aa in range(self.A): # avoid looping over S
        
            # the rows that use action a. .getA1() is used to make sure that
            # ind is a 1 dimensional vector
            ind = nonzero(self.policy == aa)[0].getA1()
            if ind.size > 0: # if no rows use action a, then no point continuing
                Ppolicy[ind, :] = self.P[aa][ind, :]
                
                #PR = self.computePR() # an apparently uneeded line, and
                # perhaps harmful in this implementation c.f.
                # mdp_computePpolicyPRpolicy.m
                Rpolicy[ind] = self.R[ind, aa]
        
        # self.R cannot be sparse with the code in its current condition, but
        # it should be possible in the future. Also, if R is so big that its
        # a good idea to use a sparse matrix for it, then converting PRpolicy
        # from a dense to sparse matrix doesn't seem very memory efficient
        if type(self.R) is sparse:
            Rpolicy = sparse(Rpolicy)
        
        #self.Ppolicy = Ppolicy
        #self.Rpolicy = Rpolicy
        return (Ppolicy, Rpolicy)
    
    def computePR(self, P, R):
        """Computes the reward for the system in one state chosing an action
        
        Arguments
        ---------
        Let S = number of states, A = number of actions
            P(SxSxA)  = transition matrix 
                P could be an array with 3 dimensions or  a cell array (1xA), 
                each cell containing a matrix (SxS) possibly sparse
            R(SxSxA) or (SxA) = reward matrix
                R could be an array with 3 dimensions (SxSxA) or  a cell array 
                (1xA), each cell containing a sparse matrix (SxS) or a 2D 
                array(SxA) possibly sparse  
        Evaluation
        ----------
            PR(SxA)   = reward matrix
        """
        # we assume that P and R define a MDP i,e. assumption is that
        # check(P, R) has already been run and doesn't fail.
        
        # make P be an object array with (S, S) shaped array elements
        if (P.dtype == object):
            self.P = P
            self.A = self.P.shape[0]
            self.S = self.P[0].shape[0]
        else: # convert to an object array
            self.A = P.shape[0]
            self.S = P.shape[1]
            self.P = zeros(self.A, dtype=object)
            for aa in range(self.A):
                self.P[aa] = P[aa, :, :]
        
        # make R have the shape (S, A)
        if ((R.ndim == 2) and (not R.dtype is object)):
            # R already has shape (S, A)
            self.R = R
        else: 
            # R has shape (A, S, S) or object shaped (A,) with each element
            # shaped (S, S)
            self.R = zeros((self.S, self.A))
            if (R.dtype is object):
                for aa in range(self.A):
                    self.R[:, aa] = multiply(P[aa], R[aa]).sum(1)
            else:
                for aa in range(self.A):
                    self.R[:, aa] = multiply(P[aa], R[aa, :, :]).sum(1)
        
        # convert the arrays to numpy matrices
        for aa in range(self.A):
            if (type(self.P[aa]) is ndarray):
                self.P[aa] = matrix(self.P[aa])
        if (type(self.R) is ndarray):
            self.R = matrix(self.R)

    def iterate(self):
        """This is a placeholder method. Child classes should define their own
        iterate() method.
        """
        raise NotImplementedError("You should create an iterate() method.")
    
    def setSilent(self):
        """Ask for running resolution functions of the MDP Toolbox in silent
        mode.
        """
        self.verbose = False
    
    def setVerbose(self):
        """Ask for running resolution functions of the MDP Toolbox in verbose
        mode.
        """
        self.verbose = True

class FiniteHorizon(MDP):
    """Reolution of finite-horizon MDP with backwards induction
    
    Arguments
    ---------
    Let S = number of states, A = number of actions
    P(SxSxA) = transition matrix 
             P could be an array with 3 dimensions or 
             a cell array (1xA), each cell containing a matrix (SxS) possibly sparse
    R(SxSxA) or (SxA) = reward matrix
             R could be an array with 3 dimensions (SxSxA) or 
             a cell array (1xA), each cell containing a sparse matrix (SxS) or
             a 2D array(SxA) possibly sparse  
    discount = discount factor, in ]0, 1]
    N        = number of periods, upper than 0
    h(S)     = terminal reward, optional (default [0; 0; ... 0] )
    Evaluation
    ----------
    V(S,N+1)     = optimal value function
                 V(:,n) = optimal value function at stage n
                        with stage in 1, ..., N
                        V(:,N+1) = value function for terminal stage 
    policy(S,N)  = optimal policy
                 policy(:,n) = optimal policy at stage n
                        with stage in 1, ...,N
                        policy(:,N) = policy for stage N
    cpu_time = used CPU time
  
    Notes
    -----
    In verbose mode, displays the current stage and policy transpose.

    """

    def __init__(self, transitions, reward, discount, N, h=None):
        """"""
        if N < 1:
            raise ValueError('PyMDPtoolbox: N must be greater than 0')
        else:
            self.N = N
        
        MDP.__init__(self, transitions, reward, discount, None)
        
        self.value = zeros(self.S, N + 1)
        
        if not h is None:
            self.value[:, N + 1] = h
        
    def iterate(self):
        """"""
        self.time = time()
        
        for n in range(self.N - 1):
            W, X = self.bellmanOperator(self.P, self.R, self.discount, self.value[:, self.N - n + 1])
            self.value[:, self.N - n] = W
            self.policy[:, self.N - n] = X
            if self.verbose:
                print("stage: %s ... policy transpose : %s") % (self.N - n, self.policy[:, self.N - n].T)
        
        self.time = time() - self.time

class LP(MDP):
    """Resolution of discounted MDP with linear programming

    Arguments
    ---------
    Let S = number of states, A = number of actions
    P(SxSxA) = transition matrix 
             P could be an array with 3 dimensions or 
             a cell array (1xA), each cell containing a matrix (SxS) possibly sparse
    R(SxSxA) or (SxA) = reward matrix
             R could be an array with 3 dimensions (SxSxA) or 
             a cell array (1xA), each cell containing a sparse matrix (SxS) or
             a 2D array(SxA) possibly sparse  
    discount = discount rate, in ]0; 1[
    h(S)     = terminal reward, optional (default [0; 0; ... 0] )
    
    Evaluation
    ----------
    V(S)   = optimal values
    policy(S) = optimal policy
    cpu_time = used CPU time
    
    Notes    
    -----
    In verbose mode, displays the current stage and policy transpose.
    
    Examples
    --------
    """

    def __init__(self, transitions, reward, discount):
        """"""
        
        try:
            from cvxopt import matrix, solvers
            self.linprog = solvers.lp
        except ImportError:
            raise ImportError("The python module cvxopt is required to use " \
                "linear programming functionality.")
        
        from scipy.sparse import eye as speye

        MDP.__init__(self, transitions, reward, discount, None)
        
        # The objective is to resolve : min V / V >= PR + discount*P*V
        # The function linprog of the optimisation Toolbox of Mathworks resolves :
        # min f'* x / M * x <= b
        # So the objective could be expressed as : min V / (discount*P-I) * V <= - PR
        # To avoid loop on states, the matrix M is structured following actions M(A*S,S)
    
        self.f = ones(self.S, 1)
    
        self.M = zeros((self.A * self.S, self.S))
        for aa in range(self.A):
            pos = (aa + 1) * self.S
            self.M[(pos - self.S):pos, :] = discount * self.P[aa] - speye(self.S, self.S)
        
        self.M = matrix(self.M)
    
    def iterate(self):
        """"""
        self.time = time()
        
        self.value = self.linprog(self.f, self.M, -self.R)
        
        self.value, self.policy =  self.bellmanOperator(self.P, self.R, self.discount, self.value)
        
        self.time = time() - self.time

class PolicyIteration(MDP):
    """Resolution of discounted MDP with policy iteration algorithm.
    
    Arguments
    ---------
    Let S = number of states, A = number of actions
    P(SxSxA) = transition matrix 
             P could be an array with 3 dimensions or 
             a cell array (1xA), each cell containing a matrix (SxS) possibly sparse
    R(SxSxA) or (SxA) = reward matrix
             R could be an array with 3 dimensions (SxSxA) or 
             a cell array (1xA), each cell containing a sparse matrix (SxS) or
             a 2D array(SxA) possibly sparse  
    discount = discount rate, in ]0, 1[
    policy0(S) = starting policy, optional 
    max_iter = maximum number of iteration to be done, upper than 0, 
             optional (default 1000)
    eval_type = type of function used to evaluate policy: 
             0 for mdp_eval_policy_matrix, else mdp_eval_policy_iterative
             optional (default 0)
             
    Evaluation
    ----------
    V(S)   = value function 
    policy(S) = optimal policy
    iter     = number of done iterations
    cpu_time = used CPU time
    
    Notes
    -----
    In verbose mode, at each iteration, displays the number 
    of differents actions between policy n-1 and n
    
    Examples
    --------
    >>> import mdp
    >>> P, R = mdp.exampleRand(5, 3)
    >>> pi = mdp.PolicyIteration(P, R, 0.9)
    >>> pi.iterate()
    
    """
    
    def __init__(self, transitions, reward, discount, policy0=None, max_iter=1000, eval_type=0):
        """"""
        
        MDP.__init__(self, transitions, reward, discount, max_iter)
        
        if policy0 == None:
            # initialise the policy to the one which maximises the expected
            # immediate reward
            self.value = matrix(zeros((self.S, 1)))
            self.policy, null = self.bellmanOperator()
            del null
        else:
            policy0 = array(policy0)
            
            if not policy0.shape in ((self.S, ), (self.S, 1), (1, self.S)):
                raise ValueError('PyMDPtolbox: policy0 must a vector with length S')
            
            policy0 = matrix(policy0.reshape(self.S, 1))
            
            if mod(policy0, 1).any() or (policy0 < 0).any() or (policy0 >= self.S).any():
                raise ValueError('PyMDPtoolbox: policy0 must be a vector of integers between 1 and S')
            else:
                self.policy = policy0
        
        # set or reset the initial values to zero
        self.value = matrix(zeros((self.S, 1)))
        
        if eval_type in (0, "matrix"):
            from numpy.linalg import solve
            from scipy.sparse import eye
            self.speye = eye
            self.lin_eq = solve
            self.eval_type = "matrix"
        elif eval_type in (1, "iterative"):
            self.eval_type = "iterative"
        else:
            raise ValueError("PyMDPtoolbox: eval_type should be 0 for matrix "\
                "evaluation or 1 for iterative evaluation. strings 'matrix' " \
                "and 'iterative' can also be used.")
    
    def evalPolicyIterative(self, V0=0, epsilon=0.0001, max_iter=10000):
        """Policy evaluation using iteration
        
        Arguments
        ---------
        Let S = number of states, A = number of actions
        P(SxSxA)  = transition matrix 
            P could be an array with 3 dimensions or 
            a cell array (1xS), each cell containing a matrix possibly sparse
        R(SxSxA) or (SxA) = reward matrix
            R could be an array with 3 dimensions (SxSxA) or 
            a cell array (1xA), each cell containing a sparse matrix (SxS) or
            a 2D array(SxA) possibly sparse  
        discount  = discount rate in ]0; 1[
        policy(S) = a policy
        V0(S)     = starting value function, optional (default : zeros(S,1))
        epsilon   = epsilon-optimal policy search, upper than 0,
            optional (default : 0.0001)
        max_iter  = maximum number of iteration to be done, upper than 0, 
            optional (default : 10000)
            
        Evaluation
        ----------
        Vpolicy(S) = value function, associated to a specific policy
        
        Notes
        -----
        In verbose mode, at each iteration, displays the condition which stopped iterations:
        epsilon-optimum value function found or maximum number of iterations reached.
        """
        if V0 == 0:
            policy_V = zeros((self.S, 1))
        else:
            raise NotImplementedError("evalPolicyIterative: case V0 != 0 not implemented. Use V0=0 instead.")
        
        policy_P, policy_R = self.computePpolicyPRpolicy()
        
        if self.verbose:
            print('  Iteration    V_variation')
        
        itr = 0
        done = False
        while not done:
            itr = itr + 1
            
            Vprev = policy_V
            policy_V = policy_R + self.discount * policy_P * Vprev
            
            variation = absolute(policy_V - Vprev).max()
            if self.verbose:
                print('      %s         %s') % (itr, variation)
                
            if variation < ((1 - self.discount) / self.discount) * epsilon: # to ensure |Vn - Vpolicy| < epsilon
                done = True
                if self.verbose:
                    print('PyMDPtoolbox: iterations stopped, epsilon-optimal value function')
            elif itr == max_iter:
                done = True
                if self.verbose:
                    print('PyMDPtoolbox: iterations stopped by maximum number of iteration condition')
        
        self.value = policy_V
    
    def evalPolicyMatrix(self):
        """Evaluation of the value function of a policy
        
        Arguments 
        ---------
        Let S = number of states, A = number of actions
        P(SxSxA) = transition matrix 
             P could be an array with 3 dimensions or 
             a cell array (1xA), each cell containing a matrix (SxS) possibly sparse
        R(SxSxA) or (SxA) = reward matrix
             R could be an array with 3 dimensions (SxSxA) or 
             a cell array (1xA), each cell containing a sparse matrix (SxS) or
             a 2D array(SxA) possibly sparse  
        discount = discount rate in ]0; 1[
        policy(S) = a policy
        
        Evaluation
        ----------
        Vpolicy(S) = value function of the policy
        """
        
        Ppolicy, Rpolicy = self.computePpolicyPRpolicy()
        # V = PR + gPV  => (I-gP)V = PR  => V = inv(I-gP)* PR
        self.value = self.lin_eq((self.speye(self.S, self.S) - self.discount * Ppolicy) , Rpolicy)
    
    def iterate(self):
        """Run the policy iteration algorithm."""
        
        if self.verbose:
            print('  Iteration  Number_of_different_actions')
        
        done = False
        self.time = time()
        
        while not done:
            self.iter = self.iter + 1
            
            # these evalPolicy* functions will update the classes value
            # attribute
            if self.eval_type == "matrix":
                self.evalPolicyMatrix()
            elif self.eval_type == "iterative":
                self.evalPolicyIterative()
            
            # This should update the classes policy attribute but leave the
            # value alone
            policy_next, null = self.bellmanOperator()
            del null
            
            n_different = (policy_next != self.policy).sum()
            
            if self.verbose:
                print('       %s                 %s') % (self.iter, n_different)
            
            if n_different == 0:
                done = True
                if self.verbose:
                    print("...iterations stopped, unchanging policy found")
            elif (self.iter == self.max_iter):
                done = True 
                if self.verbose:
                    print("...iterations stopped by maximum number of iteration condition")
            else:
                self.policy = policy_next
        
        self.time = time() - self.time
        
        # store value and policy as tuples
        self.value = tuple(array(self.value).reshape(self.S).tolist())
        self.policy = tuple(array(self.policy).reshape(self.S).tolist())

class PolicyIterationModified(MDP):
    """Resolution of discounted MDP  with policy iteration algorithm
    
    Arguments
    ---------
    Let S = number of states, A = number of actions
    P(SxSxA) = transition matrix 
             P could be an array with 3 dimensions or 
             a cell array (1xA), each cell containing a matrix (SxS) possibly sparse
    R(SxSxA) or (SxA) = reward matrix
             R could be an array with 3 dimensions (SxSxA) or 
             a cell array (1xA), each cell containing a sparse matrix (SxS) or
             a 2D array(SxA) possibly sparse  
    discount = discount rate, in ]0, 1[
    policy0(S) = starting policy, optional 
    max_iter = maximum number of iteration to be done, upper than 0, 
             optional (default 1000)
    eval_type = type of function used to evaluate policy: 
             0 for mdp_eval_policy_matrix, else mdp_eval_policy_iterative
             optional (default 0)
    
    Data Attributes
    ---------------
    V(S)   = value function 
    policy(S) = optimal policy
    iter     = number of done iterations
    cpu_time = used CPU time
    
    Notes
    -----
    In verbose mode, at each iteration, displays the number 
    of differents actions between policy n-1 and n
    
    Examples
    --------
    >>> import mdp
    """
    
    def __init__(self, transitions, reward, discount, epsilon=0.01, max_iter=10):
        """"""
        
        MDP.__init__(self, transitions, reward, discount, max_iter)
        
        if epsilon <= 0:
            raise ValueError("epsilon must be greater than 0")
        
        # computation of threshold of variation for V for an epsilon-optimal policy
        if self.discount != 1:
            self.thresh = epsilon * (1 - self.discount) / self.discount
        else:
            self.thresh = epsilon
        
        if discount == 1:
            self.value = matrix(zeros((self.S, 1)))
        else:
            # min(min()) is not right
            self.value = 1 / (1 - discount) * min(min(self.R)) * ones((self.S, 1))
    
    def iterate(self):
        """"""
        
        if self.verbose:
            print('  Iteration  V_variation')
        
        self.time = time()
        
        done = False
        while not done:
            self.iter = self.iter + 1
            
            Vnext, policy = self.bellmanOperator(self.P, self.PR, self.discount, self.V)
            #[Ppolicy, PRpolicy] = mdp_computePpolicyPRpolicy(P, PR, policy);
            
            variation = getSpan(Vnext - self.value);
            if self.verbose:
                print("      %s         %s" % (self.iter, variation))
            
            self.value = Vnext
            if variation < self.thresh:
                done = True
            else:
                is_verbose = False
                if self.verbose:
                    self.setSilent
                    is_verbose = True
                
                self.value = self.evalPolicyIterative()
                
                if is_verbose:
                    self.setVerbose
        
        self.time = time() - self.time

class QLearning(MDP):
    """Evaluates the matrix Q, using the Q learning algorithm.
    
    Let S = number of states, A = number of actions
    
    Parameters
    ----------
    P : transition matrix (SxSxA)
        P could be an array with 3 dimensions or a cell array (1xA), each
        cell containing a sparse matrix (SxS)
    R : reward matrix(SxSxA) or (SxA)
        R could be an array with 3 dimensions (SxSxA) or a cell array
        (1xA), each cell containing a sparse matrix (SxS) or a 2D
        array(SxA) possibly sparse
    discount : discount rate
        in ]0; 1[    
    n_iter : number of iterations to execute (optional).
        Default value = 10000; it is an integer greater than the default value.
    
    Results
    -------
    Q : learned Q matrix (SxA) 
    
    value : learned value function (S).
    
    policy : learned optimal policy (S).
    
    mean_discrepancy : vector of V discrepancy mean over 100 iterations
        Then the length of this vector for the default value of N is 100 
        (N/100).

    ExamplesPP[:, aa] = self.P[aa][:, ss]
    ---------
    >>> import mdp
    >>> P, R = mdp.exampleForest()
    >>> ql = mdp.QLearning(P, R, 0.96)
    >>> ql.iterate()
    >>> ql.Q
    array([[  0.        ,   0.        ],
           [  0.01062959,   0.79870231],
           [ 10.08191776,   0.35309404]])
    >>> ql.value
    array([  0.        ,   0.79870231,  10.08191776])
    >>> ql.policy
    array([0, 1, 0])
    
    >>> import mdp
    >>> import numpy as np
    >>> P = np.array([[[0.5, 0.5],[0.8, 0.2]],[[0, 1],[0.1, 0.9]]])
    >>> R = np.array([[5, 10], [-1, 2]])
    >>> ql = mdp.QLearning(P, R, 0.9)
    >>> ql.iterate()
    >>> ql.Q
    array([[ 94.99525115,  99.99999007],
           [ 53.92930199,   5.57331205]])
    >>> ql.value
    array([ 99.99999007,  53.92930199])
    >>> ql.policy
    array([1, 0])
    >>> ql.time
    0.6501460075378418
    
    """
    
    def __init__(self, transitions, reward, discount, n_iter=10000):
        """Evaluation of the matrix Q, using the Q learning algorithm
        """
        
        # The following check won't be done in MDP()'s initialisation, so let's
        # do it here
        if (n_iter < 10000):
            raise ValueError("PyMDPtoolbox: n_iter should be greater than 10000")
        
        # after this n_iter will be known as self.max_iter
        MDP.__init__(self, transitions, reward, discount, n_iter)
        
        # Initialisations
        self.Q = zeros((self.S, self.A))
        #self.dQ = zeros(self.S, self.A)
        self.mean_discrepancy = []
        self.discrepancy = []
        
    def iterate(self):
        """
        """
        self.time = time()
        
        # initial state choice
        # s = randint(0, self.S - 1)
        
        for n in range(self.max_iter):
            
            # Reinitialisation of trajectories every 100 transitions
            if ((n % 100) == 0):
                s = randint(0, self.S - 1)
            
            # Action choice : greedy with increasing probability
            # probability 1-(1/log(n+2)) can be changed
            pn = random()
            if (pn < (1 - (1 / log(n + 2)))):
                # optimal_action = self.Q[s, :].max()
                a = self.Q[s, :].argmax()
            else:
                a = randint(0, self.A - 1)
            
            # Simulating next state s_new and reward associated to <s,s_new,a>
            p_s_new = random()
            p = 0
            s_new = -1
            while ((p < p_s_new) and (s_new < s)):
                s_new = s_new + 1
                p = p + self.P[a][s, s_new]
            
            if (self.R.dtype == object):
                r = self.R[a][s, s_new]
            elif (self.R.ndim == 3):
                r = self.R[a, s, s_new]
            else:
                r = self.R[s, a]
            
            # Updating the value of Q   
            # Decaying update coefficient (1/sqrt(n+2)) can be changed
            delta = r + self.discount * self.Q[s_new, :].max() - self.Q[s, a]
            dQ = (1 / sqrt(n + 2)) * delta
            self.Q[s, a] = self.Q[s, a] + dQ
            
            # current state is updated
            s = s_new
            
            # Computing and saving maximal values of the Q variation
            self.discrepancy.append(absolute(dQ))
            
            # Computing means all over maximal Q variations values
            if ((n % 100) == 99):
                self.mean_discrepancy.append(mean(self.discrepancy))
                self.discrepancy = []
            
            # compute the value function and the policy
            self.value = self.Q.max(axis=1)
            self.policy = self.Q.argmax(axis=1)
            
        self.time = time() - self.time
        
        # rather than report that we have not done any iterations, assign the
        # value of n_iter to self.iter
        self.iter = self.max_iter

class RelativeValueIteration(MDP):
    """Resolution of MDP with average reward with relative value iteration 
    algorithm 
    
    Arguments
    ---------
    Let S = number of states, A = number of actions
    P(SxSxA) = transition matrix 
             P could be an array with 3 dimensions or 
             a cell array (1xA), each cell containing a matrix (SxS) possibly sparse
    R(SxSxA) or (SxA) = reward matrix
             R could be an array with 3 dimensions (SxSxA) or 
             a cell array (1xA), each cell containing a sparse matrix (SxS) or
             a 2D array(SxA) possibly sparse  
    epsilon  = epsilon-optimal policy search, upper than 0, 
             optional (default: 0.01)
    max_iter = maximum number of iteration to be done, upper than 0,
             optional (default 1000)
    
    Evaluation
    ----------
    policy(S)       = epsilon-optimal policy
    average_reward  = average reward of the optimal policy
    cpu_time = used CPU time
    
    Notes
    -----
    In verbose mode, at each iteration, displays the span of U variation
    and the condition which stopped iterations : epsilon-optimum policy found
    or maximum number of iterations reached.
    
    Examples
    --------
    """
    
    def __init__(self, transitions, reward, epsilon=0.01, max_iter=1000):
        
        MDP.__init__(self,  transitions, reward, None, max_iter)
        
        if epsilon <= 0:
            print('MDP Toolbox ERROR: epsilon must be upper than 0')
    
        self.U = zeros(self.S, 1)
        self.gain = self.U[self.S]
    
    def iterate(self):
        """"""
        
        done = False
        if self.verbose:
            print('  Iteration  U_variation')
        
        self.time = time()
        
        while not done:
            
            self.iter = self.iter + 1;
            
            Unext, policy = self.bellmanOperator(self.P, self.R, 1, self.U)
            Unext = Unext - self.gain
            
            variation = getSpan(Unext - self.U)
            
            if self.verbose:
                print("      %s         %s" % (self.iter, variation))

            if variation < self.epsilon:
                 done = True
                 average_reward = self.gain + min(Unext - self.U)
                 if self.verbose:
                     print('MDP Toolbox : iterations stopped, epsilon-optimal policy found')
            elif self.iter == self.max_iter:
                 done = True 
                 average_reward = self.gain + min(Unext - self.U);
                 if self.verbose:
                     print('MDP Toolbox : iterations stopped by maximum number of iteration condition')
            
            self.U = Unext
            self.gain = self.U(self.S)
        
        self.time = time() - self.time

class ValueIteration(MDP):
    """
    Solves discounted MDP with the value iteration algorithm.
    
    Description
    -----------
    mdp.ValueIteration applies the value iteration algorithm to solve
    discounted MDP. The algorithm consists in solving Bellman's equation
    iteratively.
    Iterating is stopped when an epsilon-optimal policy is found or after a
    specified number (max_iter) of iterations. 
    This function uses verbose and silent modes. In verbose mode, the function
    displays the variation of V (value function) for each iteration and the
    condition which stopped iterations: epsilon-policy found or maximum number
    of iterations reached.
    
    Let S = number of states, A = number of actions.
    
    Parameters
    ----------
    P : transition matrix 
        P could be a numpy ndarray with 3 dimensions (AxSxS) or a 
        numpy ndarray of dytpe=object with 1 dimenion (1xA), each 
        element containing a numpy ndarray (SxS) or scipy sparse matrix. 
    R : reward matrix
        R could be a numpy ndarray with 3 dimensions (AxSxS) or numpy
        ndarray of dtype=object with 1 dimension (1xA), each element
        containing a sparse matrix (SxS). R also could be a numpy 
        ndarray with 2 dimensions (SxA) possibly sparse.
    discount : discount rate
        Greater than 0, less than or equal to 1. Beware to check conditions of
        convergence for discount = 1.
    epsilon : epsilon-optimal policy search
        Greater than 0, optional (default: 0.01).
    max_iter : maximum number of iterations to be done
        Greater than 0, optional (default: computed)
    initial_value : starting value function
        optional (default: zeros(S,1)).
    
    Data Attributes
    ---------------
    value : value function
        A vector which stores the optimal value function. Prior to calling the
        iterate() method it has a value of None. Shape is (S, ).
    policy : epsilon-optimal policy
        A vector which stores the optimal policy. Prior to calling the
        iterate() method it has a value of None. Shape is (S, ).
    iter : number of iterations taken to complete the computation
        An integer
    time : used CPU time
        A float
    
    Methods
    -------
    iterate()
        Starts the loop for the algorithm to be completed.
    setSilent()
        Sets the instance to silent mode.
    setVerbose()
        Sets the instance to verbose mode.
    
    Notes
    -----
    In verbose mode, at each iteration, displays the variation of V
    and the condition which stopped iterations: epsilon-optimum policy found
    or maximum number of iterations reached.
    
    Examples
    --------
    >>> import mdp
    >>> P, R = mdp.exampleForest()
    >>> vi = mdp.ValueIteration(P, R, 0.96)
    >>> vi.verbose
    False
    >>> vi.iterate()
    >>> vi.value
    array([  5.93215488,   9.38815488,  13.38815488])
    >>> vi.policy
    array([0, 0, 0])
    >>> vi.iter
    4
    >>> vi.time
    0.002871990203857422
    
    >>> import mdp
    >>> import numpy as np
    >>> P = np.array([[[0.5, 0.5],[0.8, 0.2]],[[0, 1],[0.1, 0.9]]])
    >>> R = np.array([[5, 10], [-1, 2]])
    >>> vi = mdp.ValueIteration(P, R, 0.9)
    >>> vi.iterate()
    >>> vi.value
    array([ 40.04862539,  33.65371176])
    >>> vi.policy
    array([1, 0])
    >>> vi.iter
    26
    >>> vi.time
    0.010202884674072266
    
    >>> import mdp
    >>> import numpy as np
    >>> from scipy.sparse import csr_matrix as sparse
    >>> P = np.zeros((2, ), dtype=object)
    >>> P[0] = sparse([[0.5, 0.5],[0.8, 0.2]])
    >>> P[1] = sparse([[0, 1],[0.1, 0.9]])
    >>> R = np.array([[5, 10], [-1, 2]])
    >>> vi = mdp.ValueIteration(P, R, 0.9)
    >>> vi.iterate()
    >>> vi.value
    array([ 40.04862539,  33.65371176])
    >>> vi.policy
    array([1, 0])
    
    """
    
    def __init__(self, transitions, reward, discount, epsilon=0.01, max_iter=1000, initial_value=0):
        """Resolution of discounted MDP with value iteration algorithm."""
        
        MDP.__init__(self, transitions, reward, discount, max_iter)
        
        # initialization of optional arguments
        if (initial_value == 0):
            self.value = matrix(zeros((self.S, 1)))
        else:
            if (not initial_value.shape in ((self.S, ), (self.S, 1), (1, self.S))):
                raise ValueError("The initial value must be a vector of length S")
            else:
                self.value = matrix(initial_value)
        
        if (self.discount < 1):
            # compute a bound for the number of iterations and update the
            # stored value of self.max_iter
            self.boundIter(epsilon)
            # computation of threshold of variation for V for an epsilon-
            # optimal policy
            self.thresh = epsilon * (1 - self.discount) / self.discount
        else: # discount == 1
            # threshold of variation for V for an epsilon-optimal policy
            self.thresh = epsilon
    
    def boundIter(self, epsilon):
        """Computes a bound for the number of iterations for the value iteration
        algorithm to find an epsilon-optimal policy with use of span for the 
        stopping criterion
        
        Arguments --------------------------------------------------------------
        Let S = number of states, A = number of actions
            epsilon   = |V - V*| < epsilon,  upper than 0,
                optional (default : 0.01)
        Evaluation -------------------------------------------------------------
            max_iter  = bound of the number of iterations for the value 
            iteration algorithm to find an epsilon-optimal policy with use of
            span for the stopping criterion
            cpu_time  = used CPU time
        """
        # See Markov Decision Processes, M. L. Puterman, 
        # Wiley-Interscience Publication, 1994 
        # p 202, Theorem 6.6.6
        # k =    max     [1 - S min[ P(j|s,a), p(j|s',a')] ]
        #     s,a,s',a'       j
        k = 0
        h = zeros(self.S)
        
        for ss in range(self.S):
            PP = matrix(zeros((self.S, self.A)))
            for aa in range(self.A):
                PP[:, aa] = self.P[aa][:, ss]
            # the function "min()" without any arguments finds the
            # minimum of the entire array.
            h[ss] = PP.min()
        
        k = 1 - h.sum()
        Vprev = self.value
        null, value = self.bellmanOperator()
        # p 201, Proposition 6.6.5
        max_iter = log( (epsilon * (1 - self.discount) / self.discount) / getSpan(value - Vprev) ) / log(self.discount * k)
        #self.value = Vprev
        
        self.max_iter = ceil(max_iter)
    
    def iterate(self):
        """
        """
        
        if self.verbose:
            print('  Iteration  V_variation')
        
        self.time = time()
        done = False
        while not done:
            self.iter = self.iter + 1
            
            Vprev = self.value
            
            # Bellman Operator: compute policy and value functions
            self.policy, self.value = self.bellmanOperator()
            
            # The values, based on Q. For the function "max()": the option
            # "axis" means the axis along which to operate. In this case it
            # finds the maximum of the the rows. (Operates along the columns?)
            variation = getSpan(self.value - Vprev)
            
            if self.verbose:
                print("      %s         %s" % (self.iter, variation))
            
            if variation < self.thresh:
                done = True
                if self.verbose:
                    print("...iterations stopped, epsilon-optimal policy found")
            elif (self.iter == self.max_iter):
                done = True 
                if self.verbose:
                    print("...iterations stopped by maximum number of iteration condition")
        
        # store value and policy as tuples
        self.value = tuple(array(self.value).reshape(self.S).tolist())
        self.policy = tuple(array(self.policy).reshape(self.S).tolist())
        
        self.time = time() - self.time

class ValueIterationGS(ValueIteration):
    """Resolution of discounted MDP with value iteration Gauss-Seidel algorithm
    
    Arguments
    ---------
    Let S = number of states, A = number of actions
    P(SxSxA)  = transition matrix 
             P could be an array with 3 dimensions or 
             a cell array (1xA), each cell containing a matrix (SxS) possibly sparse
    R(SxSxA) or (SxA) = reward matrix
             R could be an array with 3 dimensions (SxSxA) or 
             a cell array (1xA), each cell containing a sparse matrix (SxS) or
             a 2D array(SxA) possibly sparse  
    discount  = discount rate in ]0; 1]
              beware to check conditions of convergence for discount = 1.
    epsilon   = epsilon-optimal policy search, upper than 0,
              optional (default : 0.01)
    max_iter  = maximum number of iteration to be done, upper than 0, 
              optional (default : computed)
    V0(S)     = starting value function, optional (default : zeros(S,1))
    
    Evaluation
    ----------
    policy(S) = epsilon-optimal policy
    iter      = number of done iterations
    cpu_time  = used CPU time
    
    Notes
    -----
    In verbose mode, at each iteration, displays the variation of V
    and the condition which stopped iterations: epsilon-optimum policy found
    or maximum number of iterations reached.
    
    Examples
    --------
    """
    def __init__(self, transitions, reward, discount, epsilon=0.01, max_iter=10, initial_value=0):
        """"""
        
        MDP.__init__(self, transitions, reward, discount, max_iter)
        
        # initialization of optional arguments
        if (initial_value == 0):
            self.value = matrix(zeros((self.S, 1)))
        else:
            if (initial_value.size != self.S):
                raise ValueError("The initial value must be length S")
            self.value = matrix(initial_value)
        if epsilon <= 0:
            raise ValueError("epsilon must be greater than 0")
        
        if discount == 1:
            print('PyMDPtoolbox WARNING: check conditions of convergence.'
                  'With no discount, convergence is not always assumed.')
        
        if (discount < 1):
            # compute a bound for the number of iterations
            self.boundIter(epsilon)
            print('MDP Toolbox WARNING: max_iter is bounded by %s') % self.max_iter
            # computation of threshold of variation for V for an epsilon-optimal policy
            self.thresh = epsilon * (1 - self.discount) / self.discount
        else: # discount == 1
            # threshold of variation for V for an epsilon-optimal policy
            self.thresh = epsilon
        
        self.iter = 0
    
    def iterate(self):
        """"""
        V = self.value
        
        done = False
        
        if self.verbose:
            print('  Iteration  V_variation')
        
        self.time = time()
        
        while not done:
            self.iter = self.iter + 1
            
            Vprev = self.value
            
            for s in range(self.S):
                for a in range(self.A):
                    Q[a] =  self.R[s,a]  +  self.discount * self.P[a][s,:] * self.value
                self.value[s] = max(Q)
            
            variation = getSpan(V - Vprev)
            
            if self.verbose:
                print("      %s         %s" % (self.iter, variation))
            
            if variation < self.thresh: 
                done = True
                if self.verbose:
                    print('MDP Toolbox : iterations stopped, epsilon-optimal policy found')
             
            elif self.iter == self.max_iter:
                done = True 
                if self.verbose: 
                    print('MDP Toolbox : iterations stopped by maximum number of iteration condition')
             
        for s in range(self.S):
            for a in range(self.A):
                Q[a] =  self.R[s,a] + self.P[a][s,:] * self.discount * self.value
            
            self.value[s], self.policy[s,1] = max(Q)

        self.time = time() - self.time
