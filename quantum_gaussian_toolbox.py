# -*- coding: utf-8 -*-
"""
Class simulating the time evolution of a gaussian state
Github: https://github.com/IgorBrandao42/Gaussian-Quantum-Information-Numerical-Toolbox-python

Author: Igor Brandão
Contact: igorbrandao@aluno.puc-rio.br
"""


import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import solve_continuous_lyapunov
from scipy.linalg import block_diag
from scipy.linalg import sqrtm
from numpy.linalg import matrix_power
#import types

class gaussian_state:                                                           # Class definning a multimode gaussian state
    """
    Class simulation of a multimode gaussian state
    
    ATRIBUTES:
        self.R       - Mean quadratures vector
        self.V       - Covariance matrix
        self.Omega   - Symplectic form matrix
        self.N_modes - Number of modes
    """    
    
    # Constructor and its auxiliar functions    
    def __init__(self, *args):
        """
        Constructor for a class instance simulating a gaussian state 
        with mean quadratures and covariance matrix
        
        The user can explicitly pass the first two moments of a multimode gaussian state
        or pass a name-value pair argument to choose a single mode gaussian state
        
        PARAMETERS:
            R0 - mean quadratures for gaussian state
            V0 - covariance matrix for gaussian state
            
        Alternatively, the user may pass a name-value pair argument 
        to create an elementary single mode gaussian state, see below.
        
        NAME-VALUE PAIR ARGUMENTS:
          "vacuum"                        - generates vacuum   state
          "thermal" , occupation number   - generates thermal  state
          "coherent", complex amplitude   - generates coherent state
          "squeezed", squeezing parameter - generates squeezed state
        """

        if(len(args) == 0):                                                     # Default constructor (vacuum state)
            self.R = np.array([[0], [0]])                                       # Save mean quadratres   in a class attribute
            self.V = np.identity(2)                                             # Save covariance matrix in a class attribute
            self.N_modes = 1;
             
        elif( isinstance(args[0], str) ):                                       # If the user called for an elementary gaussian state
            self.decide_which_state(args)                                       # Call the proper method to decipher which state the user wants 
        
        elif(isinstance(args[0], np.ndarray) and isinstance(args[1], np.ndarray)): # If the user gave the desired mean quadratures values and covariance matrix
            R0 = args[0];
            V0 = args[1];
            
            R_is_real = all(np.isreal(R0))
            R_is_vector = np.squeeze(R0).ndim == 1
            
            V_is_matrix = np.squeeze(V0).ndim == 2
            V_is_square = V0.shape[0] == V0.shape[1]
            
            R_and_V_match = len(R0) == len(V0)
            
            assert R_is_real and R_is_vector and V_is_matrix and R_and_V_match and V_is_square, "Unexpected first moments when creating gaussian state!"  # Make sure they are a vector and a matrix with same length
        
            self.R = np.vstack(R0);                                             # Save mean quadratres   in a class attribute (vstack to ensure column vector)
            self.V = V0;                                                        # Save covariance matrix in a class attribute
            self.N_modes = int(len(R0)/2);                                           # Save the number of modes of the multimode state in a class attribute
            
        else:
            raise ValueError('Unexpected arguments when creating gaussian state!') # If input arguments do not make sense, call out the user
        
        omega = np.array([[0, 1], [-1, 0]]);                                    # Auxiliar variable
        self.Omega = np.kron(np.eye(self.N_modes,dtype=int), omega)             # Save the symplectic form matrix in a class attribute                                                    
    
    def check_uncertainty_relation(self):
      """
      Check if the generated covariance matrix indeed satisfies the uncertainty principle (debbugging)
      """
      
      V_check = self.V + 1j*self.Omega;
      eigvalue, eigvector = np.linalg.eig(V_check)
      
      assert all(eigvalue>=0), "CM does not satisfy uncertainty relation!"
      
      return V_check
    
    def decide_which_state(self, varargin):
        # If the user provided a name-pair argument to the constructor,
        # this function reads these arguments and creates the first moments of the gaussian state
      
        self.N_modes = 1;
        type_state = varargin[0];                                               # Name of expected type of gaussian state
      
        if(str(type_state) == "vacuum"):                                        # If it is a vacuum state
            self.R = np.array([[0], [0]])                                       # Save mean quadratres   in a class attribute
            self.V = np.identity(2)                                             # Save covariance matrix in a class attribute
            self.N_modes = 1;
            return                                                              # End function
      
                                                                                # Make sure there is an extra parameters that is a number
        assert len(varargin)>1, "Absent amplitude for non-vacuum elementary gaussian state"
        assert isinstance(varargin[1], (int, float, complex)), "Invalid amplitude for non-vacuum elementary gaussian state"
        
        if(str(type_state) == "thermal"):                                       # If it is a thermal state
            nbar = varargin[1];                                                 # Make sure its occuption number is a non-negative number
            assert nbar>=0, "Imaginary or negative occupation number for thermal state"
            self.R = np.array([[0], [0]])
            self.V = np.diag([2.0*nbar+1, 2.0*nbar+1]);                         # Create its first moments
        
        elif(str(type_state) == "coherent"):                                    # If it is a coherent state
           alpha = varargin[1];
           self.R = np.array([[2*alpha.real], [2*alpha.imag]]);
           self.V = np.identity(2);                                             # Create its first moments
        
        elif(str(type_state) == "squeezed"):                                    # If it is a squeezed state
            r = varargin[1];                                                    # Make sure its squeezing parameter is a real number
            assert np.isreal(r), "Unsupported imaginary amplitude for squeezed state"
            self.R = np.array([[0], [0]])
            self.V = np.diag([np.exp(-2*r), np.exp(+2*r)]);                           # Create its first moments
        
        else:
            self.N_modes = [];
            raise ValueError("Unrecognized gaussian state name, please check for typos or explicitely pass its first moments as arguments")
    
    
    # Construct another state, from this base gaussian_state
    def tensor_product(self, rho_list):
        """ Given a list of gaussian states, 
        # calculates the tensor product of the base state and the states in the array
        # 
        # PARAMETERS:
        #    rho_array - array of gaussian_state (multimodes)
        #
         CALCULATES:
            rho - multimode gaussian_state with all of the input states
        """
      
        R_final = self.R;                                                      # First moments of resulting state is the same of rho_A
        V_final = self.V;                                                      # First block diagonal entry is the CM of rho_A
      
        for rho in rho_list:                                                    # Loop through each state that is to appended
            R_final = np.vstack((R_final, rho.R))                               # Create its first moments
            V_final = block_diag(V_final, rho.V);
      
        rho = gaussian_state(R_final, V_final);                                 # Generate the gaussian state with these moments
      
        return rho
    
    def partial_trace(self, indexes):
        """
        Partial trace over specific single modes of the complete gaussian state
        
        PARAMETERS:
           indexes - the modes the user wants to trace out (as in the mathematical notation) 
        
        CALCULATES:
           rho_A - gaussian_state with all of the input state, except of the modes specified in 'indexes'
        """
      
        N_A = int(len(self.R) - 2*len(indexes));                                    # Twice the number of modes in resulting state
        assert N_A>=0, "Partial trace over more states than exists in gaussian state" 
      
        # Shouldn't there be an assert over max(indexes) < obj.N_modes ? -> you cant trace out modes that do not exist
      
        modes = np.arange(self.N_modes)
        entries = np.isin(modes, indexes)
        entries = [not elem for elem in entries]
        modes = modes[entries];
      
        R0 = np.zeros((N_A, 1))
        V0 = np.zeros((N_A,N_A))
      
        for i in range(len(modes)):
            m = modes[i]
            R0[(2*i):(2*i+2)] = self.R[(2*m):(2*m+2)]
        
            for j in range(len(modes)):
                n = modes[j]
                V0[(2*i):(2*i+2), (2*j):(2*j+2)] = self.V[(2*m):(2*m+2), (2*n):(2*n+2)]
      
        rho_A = gaussian_state(R0, V0)
        return rho_A
    
    def only_modes(self, indexes):
      """
      Partial trace over all modes except the ones in indexes of the complete gaussian state
       
       PARAMETERS:
          indexes - the modes the user wants to retrieve from the multimode gaussian state
      
       CALCULATES:
          rho - gaussian_state with all of the specified modes
      """
      
      N_A = len(indexes);                                                       # Number of modes in resulting state
      assert N_A>0 and N_A <= self.N_modes, "Partial trace over more states than exists in gaussian state"
      
      R0 = np.zeros((2*N_A, 1))
      V0 = np.zeros((2*N_A, 2*N_A))
      
      for i in range(len(indexes)):
            m = indexes[i]
            R0[(2*i):(2*i+2)] = self.R[(2*m):(2*m+2)]
        
            for j in range(len(indexes)):
                n = indexes[j]
                V0[(2*i):(2*i+2), (2*j):(2*j+2)] = self.V[(2*m):(2*m+2), (2*n):(2*n+2)]
      
      rho_A = gaussian_state(R0, V0);
      return rho_A
    
    
    # Properties of the gaussian state
    def symplectic_eigenvalues(self):
        """
        Calculates the sympletic eigenvalues of a covariance matrix V with symplectic form Omega
        
        Finds the absolute values ofthe eigenvalues of i\Omega V and removes repeated entries
        
        CALCULATES:
            lambda - array with symplectic eigenvalues
        """  
        H = 1j*np.matmul(self.Omega, self.V);                                   # Auxiliar matrix
        lambda_0, v_0 = np.linalg.eig(H)
        lambda_0 = np.abs( lambda_0 );                                          # Absolute value of the eigenvalues of the auxiliar matrix
        
        lambda_s = np.zeros((self.N_modes, 1));                                 # Variable to store the symplectic eigenvalues
        for i in range(self.N_modes):                                           # Loop over the non-repeated entries of lambda_0
            lambda_s[i] = lambda_0[0]                                         # Get the first value on the repeated array
            lambda_0 = np.delete(lambda_0, 0)                                  # Delete it
            
            idx = np.argmin( np.abs(lambda_0-lambda_s[i]) )                           # Find the next closest value on the array (repeated entry)
            lambda_0 = np.delete(lambda_0, idx)                              # Delete it too
        
        return lambda_s
    
    def purity(self):
      """
      Purity of a gaussian state (pure states have unitary purity)
       
       CALCULATES:
           p - purity
      """
      
      return 1/np.prod( self.symplectic_eigenvalues() );
    
    def squeezing_degree(self):
        """
        Degree of squeezing of the quadratures of a single mode state
        Defined as the ratio of the variance of the squeezed and antisqueezed quadratures
        
        CALCULATES:
            V_sq  - variance of the     squeezed quadrature
            V_asq - variance of the antisqueezed quadrature
            eta   - ratio of the variances above
       
        REFERENCE: 
            Phys. Rev. Research 2, 013052 (2020)
        """
      
        assert self.N_modes == 1, "At the moment, this program only calculates the squeezing degree for a single mode state"
      
        lambda_0, v_0 = np.linalg.eig(self.V)
        
        V_sq  = np.amin(lambda_0);
        V_asq = np.amax(lambda_0);
      
        eta = V_sq/V_asq;
        return eta, V_sq, V_asq
    
    def von_Neumann_Entropy(self):
        """
        Calculation of the von Neumann entropy for a multipartite gaussian system
       
        CALCULATES:
             Entropy - von Neumann entropy of the multimode state
        """
        
        nu = self.symplectic_eigenvalues();                                     # Calculates the sympletic eigenvalues of a covariance matrix V
        
                                                                                # 0*log(0) is NaN, but in the limit that x->0 : x*log(x) -> 0
        nu[np.abs(nu - 1) < 1e-15] = nu[np.abs(nu - 1) < 1e-15] + 1e-15;                                 # Doubles uses a 15 digits precision, I'm adding a noise at the limit of the numerical precision
        
        nu_plus  = (nu + 1)/2.0;                                                # Temporary variables
        nu_minus = (nu - 1)/2.0;
        g_nu = np.multiply(nu_plus,np.log(nu_plus)) - np.multiply(nu_minus, np.log(nu_minus))
      
        Entropy = np.sum( g_nu );                                               # Calculate the entropy
        return Entropy
    
    def mutual_information(self):
        """
         Mutual information for a multipartite gaussian system
        
         CALCULATES:
            I     - mutual information  for the total system of the j-th covariance matrix
            S_tot - von Neumann entropy for the total system of the j-th covariance matrix
            S     - von Neumann entropy for the i-th mode    of the j-th covariance matrix
        """
        S = np.zeros((self.N_modes, 1));                                        # Variable to store the entropy of each mode
      
        for j in range(self.N_modes):                                           # Loop through each mode
            single_mode = self.only_modes([j]);                                   # Get the covariance matrix for only the i-th mode
            S[j] = single_mode.von_Neumann_Entropy();                           # von Neumann Entropy for i-th mode of each covariance matrix
      
        S_tot = self.von_Neumann_Entropy();                                      # von Neumann Entropy for the total system of each covariance matrix
      
        I = np.sum(S) - S_tot;                                                     # Calculation of the mutual information
        return I
    
    def occupation_number(self):
        """
        Occupation number for a each single mode within the multipartite gaussian state (array)
        
        CALCULATES:
            nbar - array with the occupation number for each single mode of the multipartite gaussian state
        """
        
        Variances = np.diag(self.V);                                                # From the current CM, take take the variances
        Variances = np.vstack(Variances)
        
        mean_x = self.R[::2];                                                    # Odd  entries are the mean values of the position
        mean_p = self.R[1::2];                                                   # Even entries are the mean values of the momentum
        
        Var_x = Variances[::2];                                                 # Odd  entries are position variances
        Var_p = Variances[1::2];                                                # Even entries are momentum variances
        
        nbar = 0.25*( Var_x + mean_x**2 + Var_p + mean_p**2 ) - 0.5;            # Calculate occupantion numbers at current time
        return nbar
    
    def coherence(self):
        """
        Coherence of a multipartite gaussian system
         
        CALCULATES:
            C - coherence
        
        REFERENCE: 
            Phys. Rev. A 93, 032111 (2016).
        """
        
        nbar = self.occupation_number();                                        # Array with each single mode occupation number
        
        nbar[nbar==0] = nbar[nbar==0] + 1e-16;                                  # Make sure there is no problem with log(0)!
        
        S_total = self.von_Neumann_Entropy();                                    # von Neumann Entropy for the total system
        
        temp = np.sum( np.multiply(nbar+1, np.log2(nbar+1)) - np.multiply(nbar, np.log2(nbar)) );                # Temporary variable
        
        C = temp - S_total;                                                     # Calculation of the mutual information
        return C
    
    def wigner(self, X, P):
        """
        Calculates the wigner function for a single mode gaussian state
       
        PARAMETERS
            X, P - 2D grid where the wigner function is to be evaluated (use meshgrid)
        
        CALCULATES:
            W - array with Wigner function over the input 2D grid
        """
        
        assert self.N_modes == 1, "At the moment, this program only calculates the wigner function for a single mode state"
        
        N = self.N_modes;                                                       # Number of modes
        W = np.zeros((len(X), len(P)));                                         # Variable to store the calculated wigner function
        
        one_over_purity = 1/self.purity();
        
        inv_V = np.linalg.inv(self.V)
        
        for i in range(len(X)):
            x = np.block([ [X[i,:]] , [P[i,:]] ]);   
            
            for j in range(x.shape[1]):
                dx = np.vstack(x[:, j]) - self.R;                                          # x_mean(:,i) is the i-th point in phase space
                dx_T = np.hstack(dx)
                
                W_num = np.exp( - np.matmul(np.matmul(dx_T, inv_V), dx)/2 );    # Numerator
                
                W_den = (2*np.pi)**N * one_over_purity;                         # Denominator
          
                W[i, j] = W_num/W_den;                                          # Calculate the wigner function at every point on the grid
        return W
    
    def logarithmic_negativity(self, *args):
        """
        Calculation of the logarithmic negativity for a bipartite system
       
        PARAMETERS:
           indexes - array with indices for the bipartition to consider 
           If the system is already bipartite, this parameter is optional !
       
        CALCULATES:
           LN - logarithmic negativity for the bipartition / bipartite states
        """
        
        temp = self.N_modes 
        if(temp == 2):                                                          # If the full system is only comprised of two modes
            V0 = self.V                                                         # Take its full covariance matrix
        elif(len(args) > 0 and temp > 2):
            indexes = args[0]
            
            assert len(indexes) == 2, "Can only calculate the logarithmic negativity for a bipartition!"
                
            bipartition = self.only_modes(indexes)                              # Otherwise, get only the two mode specified by the user
            V0 = bipartition.V                                                  # Take the full Covariance matrix of this subsystem
        else:
            raise TypeError('Unable to decide which bipartite entanglement to infer, please pass the indexes to the desired bipartition')
        
        A = V0[0:2, 0:2]                                                        # Make use of its submatrices
        B = V0[2:4, 2:4] 
        C = V0[0:2, 2:4] 
        
        sigma = np.linalg.det(A) + np.linalg.det(B) - 2.0*np.linalg.det(C)      # Auxiliar variable
        
        ni = sigma/2.0 - np.sqrt( sigma**2 - 4.0*np.linalg.det(V0) )/2.0 ;      # Square of the smallest of the symplectic eigenvalues of the partially transposed covariance matrix
        
        if(ni < 0.0):                                                           # Manually perform a maximum to save computational time (calculation of a sqrt can take too much time and deal with residual numeric imaginary parts)
            LN = 0.0;
        else:
            ni = np.sqrt( ni.real );                                            # Smallest of the symplectic eigenvalues of the partially transposed covariance matrix
        
        LN = np.max([0, -np.log(ni)]);                                          # Calculate the logarithmic negativity at each time
        return LN
    
    def fidelity(self, rho_2):
        """
        Calculates the fidelity between the two arbitrary gaussian states
        
        ARGUMENTS:
            rho_1, rho_2 - gaussian states to be compared through fidelity
         
        CALCULATES:
            F - fidelity between rho_1 and rho_2
        
        REFERENCE:
            Phys. Rev. Lett. 115, 260501.
       
        OBSERVATION:
        The user should note that non-normalized quadratures are expected;
        They are normalized to be in accordance with the notation of Phys. Rev. Lett. 115, 260501.
        """
      
        assert self.N_modes == rho_2.N_modes, "Impossible to calculate the fidelity between gaussian states of diferent sizes!" 
        
        u_1 = self.R/np.sqrt(2.0);                                              # Normalize the mean value of the quadratures
        u_2 = rho_2.R/np.sqrt(2.0);
        
        V_1 = self.V/2.0;                                                       # Normalize the covariance matrices
        V_2 = rho_2.V/2.0;
        
        OMEGA = self.Omega;
        OMEGA_T = np.transpose(OMEGA)
        
        delta_u = u_2 - u_1;                                                    # A bunch of auxiliar variables
        delta_u_T = np.hstack(delta_u)
        
        inv_V = np.linalg.inv(V_1 + V_2);
        
        V_aux = np.matmul( np.matmul(OMEGA_T, inv_V), OMEGA/4 + np.matmul(np.matmul(V_2, OMEGA), V_1) )
        
        identity = np.identity(2*self.N_modes);
        
        F_tot_4 = np.linalg.det( 2*np.matmul(sqrtm(identity + matrix_power(np.matmul(V_aux,OMEGA),-2)/4) + identity, V_aux) );
        
        F_0 = (F_tot_4.real / np.linalg.det(V_1+V_2))**(1.0/4.0);               # We take only the real part of F_tot_4 as there can be a residual complex part from numerical calculations!
        
        F = F_0*np.exp( -np.matmul(np.matmul(delta_u_T,inv_V), delta_u)  / 4);                        # Fidelity
        return F
    
    
    # Gaussian unitaries (applicable to single mode states)
    def displace(self, alpha, modes=[0]):
        """
        Apply displacement operator on a single mode gaussian state
        TO DO: generalize these operation to many modes!
       
        ARGUMENT:
           alpha - complex amplitudes for the displacement operator
           modes - indexes for the modes to be displaced 
        """
        
        if not (isinstance(alpha, list) or isinstance(alpha, np.ndarray)):      # Make sure the input variables are of the correct type
            alpha = [alpha]
        if not (isinstance(modes, list) or isinstance(modes, np.ndarray)):      # Make sure the input variables are of the correct type
            modes = [modes]
        
        assert len(modes) == len(alpha), "Unable to decide which modes to displace nor by how much" # If the size of the inputs are different, there is no way of telling exactly what it is expected to do
        
        for i in range(len(alpha)):                                             # For each displacement amplitude
            idx = modes[i]                                                      # Get its corresponding mode
            
            d = 2.0*np.array([[alpha[i].real], [alpha[i].imag]]);               # Discover by how much this mode is to be displaced
            self.R[2*idx:2*idx+2] = self.R[2*idx:2*idx+2] + d;                  # Displace its mean value (covariance matrix is not altered)
    
    def squeeze(self, r, modes=[0]):
        """
        Apply squeezing operator on a single mode gaussian state
        TO DO: generalize these operation to many modes!
        
        ARGUMENT:
           r     - ampllitude for the squeezing operator
           modes - indexes for the modes to be squeezed
        """
        
        if not (isinstance(r, list) or isinstance(r, np.ndarray)):              # Make sure the input variables are of the correct type
            r = [r]
        if not (isinstance(modes, list) or isinstance(modes, np.ndarray)):      # Make sure the input variables are of the correct type
            modes = [modes]
        
        assert len(modes) == len(r), "Unable to decide which modes to squeeze nor by how much" # If the size of the inputs are different, there is no way of telling exactly what it is expected to do
        
        S = np.eye(2*self.N_modes)                                              # Build the squeezing matrix (initially a identity matrix because there is no squeezing to be applied on other modes)
        for i in range(len(r)):                                                 # For each squeezing parameter
            idx = modes[i]                                                      # Get its corresponding mode
            
            S[2*idx:2*idx+2, 2*idx:2*idx+2] = np.diag([np.exp(-r[i]), np.exp(+r[i])]); # Build the submatrix that squeezes the desired modes
        
        self.R = np.matmul(S, self.R);                                          # Apply squeezing operator on first  moments
        self.V = np.matmul( np.matmul(S,self.V), S);                            # Apply squeezing operator on second moments
        
    def rotate(self, theta, modes=[0]):
        """
        Apply phase rotation on a single mode gaussian state
        TO DO: generalize these operation to many modes!
        
        ARGUMENT:
           theta - ampllitude for the rotation operator
           modes - indexes for the modes to be squeezed
        """
        
        if not (isinstance(theta, list) or isinstance(theta, np.ndarray)):      # Make sure the input variables are of the correct type
            theta = [theta]
        if not (isinstance(modes, list) or isinstance(modes, np.ndarray)):      # Make sure the input variables are of the correct type
            modes = [modes]
        
        assert len(modes) == len(theta), "Unable to decide which modes to rotate nor by how much" # If the size of the inputs are different, there is no way of telling exactly what it is expected to do
        
        Rot = np.eye(2*self.N_modes)                                            # Build the rotation matrix (initially identity matrix because there is no rotation to be applied on other modes)
        for i in range(len(theta)):                                             # For each rotation angle
            idx = modes[i]                                                      # Get its corresponding mode
            
            Rot[2*idx:2*idx+2, 2*idx:2*idx+2] = np.array([[np.cos(theta[i]/2), np.sin(theta[i]/2)], [-np.sin(theta[i]/2), np.cos(theta[i]/2)]]); # Build the submatrix that rotates the desired modes
        
        Rot_T = np.transpose(Rot)
        
        self.R = np.matmul(Rot, self.R);                                        # Apply rotation operator on first  moments
        self.V = np.matmul( np.matmul(Rot, self.V), Rot_T);                     # Apply rotation operator on second moments
        
    def phase(self, theta, modes=[0]):
        """
        Apply phase rotation on a single mode gaussian state
        TO DO: generalize these operation to many modes!
        
        ARGUMENT:
           theta - ampllitude for the rotation operator
           modes - indexes for the modes to be squeezed
        """
        self.rotate(theta, modes)                                               # They are the same method/operator, this is essentially just a alias
    
    # Gaussian unitaries (applicable to two mode states)
    def beam_splitter(self, tau, modes=[0, 1]):
        """
        Apply a beam splitter transformation to pair of modes in a multimode gaussian state
        
        ARGUMENT:
           tau - ampllitude for the beam splitter operator
           modes - indexes for the pair of modes which will receive the beam splitter operator 
        """
        
        if not (isinstance(tau, list) or isinstance(tau, np.ndarray)):          # Make sure the input variables are of the correct type
            tau = [tau]
        if not (isinstance(modes, list) or isinstance(modes, np.ndarray)):      # Make sure the input variables are of the correct type
            modes = [modes]
        
        assert len(modes) == 2, "Unable to decide which modes to apply beam splitter operator nor by how much"
        
        BS = np.eye(2*self.N_modes)
        i = modes[0]
        j = modes[1] 
        
        B = np.sqrt(tau)*np.identity(2)
        S = np.sqrt(1-tau)*np.identity(2)
        
        BS[2*i:2*i+2, 2*i:2*i+2] = B
        BS[2*j:2*j+2, 2*j:2*j+2] = B
        
        BS[2*i:2*i+2, 2*j:2*j+2] =  S
        BS[2*j:2*j+2, 2*i:2*i+2] = -S
        
        # BS = np.block([[B, S], [-S, B]]);
        
        BS_T = np.transpose(BS)
        
        self.R = np.matmul(BS, self.R);
        self.V = np.matmul( np.matmul(BS, self.V), BS_T);
    
    def two_mode_squeezing(self, r, modes=[0, 1]):
        """
        Apply a two mode squeezing operator  in a gaussian state
        r - squeezing parameter
        
        ARGUMENT:
           r - ampllitude for the two-mode squeezing operator
        """
        
        if not (isinstance(r, list) or isinstance(r, np.ndarray)):              # Make sure the input variables are of the correct type
            r = [r]
        if not (isinstance(modes, list) or isinstance(modes, np.ndarray)):      # Make sure the input variables are of the correct type
            modes = [modes]
        
        assert len(modes) == 2, "Unable to decide which modes to apply two-mode squeezing operator nor by how much"
        
        S2 = np.eye(2*self.N_modes)
        i = modes[0]
        j = modes[1] 
        
        S0 = np.cosh(r)*np.identity(2);
        S1 = np.sinh(r)*np.diag([+1,-1]);
        
        S2[2*i:2*i+2, 2*i:2*i+2] = S0
        S2[2*j:2*j+2, 2*j:2*j+2] = S0
        
        S2[2*i:2*i+2, 2*j:2*j+2] = S1
        S2[2*j:2*j+2, 2*i:2*i+2] = S1
        
        # S2 = np.block([[S0, S1], [S1, S0]])
        S2_T = np.transpose(S2)
        
        self.R = np.matmul(S2, self.R);
        self.V = np.matmul( np.matmul(S2, self.V), S2_T)
        
    # Gaussian measurements
    def measurement_general(self, *args):
        """
        After a general gaussian measurement is performed on the last m modes of a (n+m)-mode gaussian state
        this method calculates the conditional state the remaining n modes evolve into
        
        The user must provide the gaussian_state of the measured m-mode state or its mean value and covariance matrix
        
        At the moment, this method can only perform the measurement on the last modes of the global state,
        if you know how to perform this task on a generic mode, contact me so I can implement it! :)
       
        ARGUMENTS:
           R_m      - first moments     of the conditional state after the measurement
           V_m      - covariance matrix of the conditional state after the measurement
           or
           rho_B    - conditional gaussian state after the measurement on the last m modes (rho_B.N_modes = m)
        
        REFERENCE:
           Jinglei Zhang's PhD Thesis - https://phys.au.dk/fileadmin/user_upload/Phd_thesis/thesis.pdf
        """
        if isinstance(args[0], gaussian_state):                                 # If the input argument is a gaussian_state
            R_m = args[0].R;
            V_m = args[0].V;
        else:                                                                   # If the input arguments are the conditional state's mean quadrature vector anc covariance matrix
            R_m = args[0];
            V_m = args[1];
        
        idx_modes = range(int(self.N_modes-len(R_m)/2), self.N_modes);               # Indexes to the modes that are to be measured
        
        rho_B = self.only_modes(idx_modes);                                     # Get the mode measured mode in the global state previous to the measurement
        rho_A = self.partial_trace(idx_modes);                                  # Get the other modes in the global state        previous to the measurement
        
        n = 2*rho_A.N_modes;                                                    # Twice the number of modes in state A
        m = 2*rho_B.N_modes;                                                    # Twice the number of modes in state B
        
        V_AB = self.V[0:n, n:(n+m)];                                            # Get the matrix dictating the correlations      previous to the measurement                           
        
        inv_aux = np.linalg.inv(rho_B.V + V_m)                                  # Auxiliar variable
        
        # Update the other modes conditioned on the measurement results
        rho_A.R = rho_A.R - np.matmul(V_AB, np.linalg.solve(rho_B.V + V_m, rho_B.R - R_m) );
        
        rho_A.V = rho_A.V - np.matmul(V_AB, np.matmul(inv_aux, V_AB.transpose()) );
        
        return rho_A
    
    def measurement_homodyne(self, *args):
        """
        After a homodyne measurement is performed on the last m modes of a (n+m)-mode gaussian state
        this method calculates the conditional state the remaining n modes evolve into
        
        The user must provide the gaussian_state of the measured m-mode state or its mean value
        
        At the moment, this method can only perform the measurement on the last modes of the global state,
        if you know how to perform this task on a generic mode, contact me so I can implement it! :)
       
        ARGUMENTS:
           R_m      - first moments     of the conditional state after the measurement
           V_m      - covariance matrix of the conditional state after the measurement
           or
           rho_B    - conditional gaussian state after the measurement on the last m modes (rho_B.N_modes = m)
        
        REFERENCE:
           Jinglei Zhang's PhD Thesis - https://phys.au.dk/fileadmin/user_upload/Phd_thesis/thesis.pdf
        """
      
        if isinstance(args[0], gaussian_state):                                 # If the input argument is a gaussian_state
            R_m = args[0].R;
        else:                                                                   # If the input argument is the mean quadrature vector
            R_m = args[0];
        
        idx_modes = range(int(self.N_modes-len(R_m)/2), self.N_modes);          # Indexes to the modes that are to be measured
        
        rho_B = self.only_modes(idx_modes);                                     # Get the mode measured mode in the global state previous to the measurement
        rho_A = self.partial_trace(idx_modes);                                  # Get the other modes in the global state        previous to the measurement
        
        n = 2*rho_A.N_modes;                                                    # Twice the number of modes in state A
        m = 2*rho_B.N_modes;                                                    # Twice the number of modes in state B
        
        V_AB = self.V[0:n, n:(n+m)];                                            # Get the matrix dictating the correlations      previous to the measurement
        
        MP_inverse = np.diag([1/rho_B.V[1,1], 0]);                              # Moore-Penrose pseudo-inverse an auxiliar matrix (see reference)
        
        rho_A.R = rho_A.R - np.matmul(V_AB, np.matmul(MP_inverse, rho_B.R - R_m   ) ); # Update the other modes conditioned on the measurement results
        rho_A.V = rho_A.V - np.matmul(V_AB, np.matmul(MP_inverse, V_AB.transpose()) );
        return rho_A
    
    def measurement_heterodyne(self, *args):
        """
        After a heterodyne measurement is performed on the last m modes of a (n+m)-mode gaussian state
        this method calculates the conditional state the remaining n modes evolve into
        
        The user must provide the gaussian_state of the measured m-mode state or the measured complex amplitude of the resulting coherent state
        
        At the moment, this method can only perform the measurement on the last modes of the global state,
        if you know how to perform this task on a generic mode, contact me so I can implement it! :)
       
        ARGUMENTS:
           alpha    - complex amplitude of the coherent state after the measurement
           or
           rho_B    - conditional gaussian state after the measurement on the last m modes (rho_B.N_modes = m)
        
        REFERENCE:
           Jinglei Zhang's PhD Thesis - https://phys.au.dk/fileadmin/user_upload/Phd_thesis/thesis.pdf
        """
        
        if isinstance(args[0], gaussian_state):                                 # If the input argument is  a gaussian_state
            rho_B = args[0];
        else:
            rho_B = gaussian_state("coherent", args[0]);
        
        rho_A = self.measurement_general(rho_B);
        return rho_A
    
   
def is_a_function(maybe_a_function):
    """
    Auxiliar internal function checking if a given variable is a lambda function
    """
    return callable(maybe_a_function)                   # OLD: isinstance(obj, types.LambdaType) and obj.__name__ == "<lambda>"

def lyapunov_ode(t, V_old_vector, A, D):
    """
    Auxiliar internal function defining the Lyapunov equation 
    and calculating the derivative of the covariance matrix
    """
    
    M = A.shape[0];                                                             # System dimension (N_particles + 1 cavity field)partículas  + 1 campo)
    
    A_T = np.transpose(A)                                                       # Transpose of the drift matrix
    
    V_old = np.reshape(V_old_vector, (M, M));                                      # Vector -> matrix
    
    dVdt = np.matmul(A, V_old) + np.matmul(V_old, A_T) + D;                     # Calculate how much the CM derivative in this time step
    
    dVdt_vector = np.reshape(dVdt, (M**2,));                                     # Matrix -> vector
    return dVdt_vector


class gaussian_dynamics:
    """
    Class simulating the time evolution of a gaussian state following a set of 
    Langevin and Lyapunov equations for its first moments dynamics
    
    ATTRIBUTES
        A                     - Drift matrix (can be a lambda functions to have a time dependency!)
        D                     - Diffusion Matrix 
        N                     - Mean values of the noises
        initial_state         - Initial state of the global system
        t                     - Array with timestamps for the time evolution
        
        is_stable             - Boolean telling if the system is stable or not
        R_semi_classical      - Array with semi-classical mean quadratures (Semi-classical time evolution using Monte Carlos method)
        R                     - Array with mean quadratures  for each time
        V                     - Cell  with covariance matrix for each time
        state                 - Gaussian state               for each time
                                                                                    
        N_time                - Length of time array
        Size_matrices         - Size of covariance, diffusion and drift matrices
        steady_state_internal - Steady state
    """
    
    def __init__(self, A_0, D_0, N_0, initial_state_0):
        """
        Class constructor for simulating the time evolution of the global system
        open/closed quantum dynamics dictated by Langevin and Lyapunov equations
        
        Langevin: \dot{R} = A*X + N           : time evolution of the mean quadratures
       
        Lyapunov: \dot{V} = A*V + V*A^T + D   : time evolution of the covariance matrix
       
        PARAMETERS:
           A_0           - Drift matrix     (numerical matrix or lambda functions for a matrix with time dependency
           D_0           - Diffusion Matrix (auto correlation of the noises, assumed to be delta-correlated in time)
           N_0           - Mean values of the noises
           initial_state - Cavity linewidth
       
        CALCULATES:
           self           - instance of a time_evolution class
           self.is_stable - boolean telling if the system is stable or not
        """
      
        self.A = A_0;                                                           # Drift matrix
        self.D = D_0;                                                           # Diffusion Matrix
        self.N = N_0;                                                           # Mean values of the noises
        
        self.initial_state = initial_state_0;                                   # Initial state of the global system
        
        self.Size_matrices = len(self.D);                                       # Size of system and ccupation number for the environment (heat bath)
      
        # assert 2*initial_state_0.N_modes == self.Size_matrices), "Initial state's number of modes does not match the drift and diffusion matrices sizes"              # Check if the initial state and diffusion/drift matrices have appropriate sizes !
      
        if( not is_a_function(self.A) ):
            eigvalue, eigvector = np.linalg.eig(self.A);                        # Calculate the eigenvalues of the drift matrix
            is_not_stable = np.any( eigvalue.real > 0 );                        # Check if any eigenvalue has positive real part (unstability)
            self.is_stable = not is_not_stable                                  # Store the information of the stability of the system in a class attribute
    
    def run(self, t_span):
        """
        Run every time evolution available at the input timestamps.
       
        PARAMETERS:
            self   - class instance
            tspan - Array with time stamps when the calculations should be done
       
        CALCULATES:
            result = array with time evolved gaussian states for each timestamp of the input argument t_span
            each entry of the array is a gaussian_state class instance
        """
      
        status_langevin = self.langevin(t_span);                                                  # Calculate the mean quadratures for each timestamp
      
        status_lyapunov = self.lyapunov(t_span);                                                  # Calculate the CM for each timestamp (perform time integration of the Lyapunov equation)
        
        assert status_langevin != -1 and status_lyapunov != -1, "Unable to perform the time evolution - Integration step failed"         # Make sure they are a vector and a matrix with same length
        
        self.build_states();                                                    # Combine the time evolutions calculated above into an array of gaussian states
      
        result = self.state;
        return result                                                           # Return the array of time evolved gaussian_state
    
    def langevin(self, t_span):
        """
        Solve the Langevin equation for the time evolved mean quadratures of the full system
       
        Uses ode45 to numerically integrate the average Langevin equations (a fourth order Runge-Kutta method)
       
        PARAMETERS:
            self   - class instance
            t_span - timestamps when the time evolution is to be calculated
       
        CALCULATES:
            self.R - a cell with the time evolved mean quadratures where
            self.R(i,j) is the i-th mean quadrature at the j-th timestamp
        """
        self.t = t_span;                                                        # Timestamps for the simulation
        self.N_time = len(t_span);                                              # Number of timestamps
        
        if is_a_function(self.A):                                          # I have to check if there is a time_dependency on the odes :(
            langevin_ode = lambda t, R: np.reshape(np.matmul(self.A(t), R.reshape((len(R),1))) + self.N, (len(R),))        # Function handle that defines the Langevin equation (returns the derivative)
        else:
            langevin_ode = lambda t, R: np.reshape(np.matmul(self.A, np.reshape(R, (len(R),1))) + self.N, (len(R),))           # Function handle that defines the Langevin equation (returns the derivative)
        
        # np.reshape(np.matmul(self.A, R.reshape((len(R),1))) + self.N, (len(R),))
        
        solution_langevin = solve_ivp(langevin_ode, [t_span[0], t_span[-1]], np.reshape(self.initial_state.R, (self.Size_matrices,)), t_eval=t_span) # Solve Langevin eqaution through Runge Kutta(4,5)
        # Each row in R corresponds to the solution at the value returned in the corresponding row of self.t
        
        self.R = solution_langevin.y;                                           # Store the time evolved quadratures in a class attribute
        
        return solution_langevin.status
        #  fprintf("Langevin simulation finished!\n\n")                         # Warn user the heavy calculations ended
    
    def lyapunov(self, t_span):
        """
        Solve the lyapunov equation for the time evolved covariance matrix of the full system
       
        Uses ode45 to numerically integrate, a fourth order Runge-Kutta method
       
        PARAMETERS:
            self   - class instance
            t_span - timestamps when the time evolution is to be calculated
       
        CALCULATES:
            'self.V' - a cell with the time evolved covariance matrix where
             self.V{j} is the covariance matrix at the j-th timestamp
        """
      
        # disp("Lyapunov simulation started...")                                # Warn the user that heavy calculations started (their computer did not freeze!)
        
        self.t = t_span;                                                        # Timestamps for the simulation
        self.N_time = len(t_span);                                           # Number of timestamps
        
        V_0_vector = np.reshape(self.initial_state.V, (self.Size_matrices**2, )); # Reshape the initial condition into a vector (expected input for ode45)
        
        if is_a_function(self.A):                                          # I have to check if there is a time_dependency on the odes :(
            ode = lambda t, V: lyapunov_ode(t, V, self.A(t), self.D);           # Function handle that defines the Langevin equation (returns the derivative)
        else:
            ode = lambda t, V: lyapunov_ode(t, V, self.A, self.D);              # Lambda unction that defines the Lyapunov equation (returns the derivative)
        
        solution_lyapunov = solve_ivp(ode, [t_span[0], t_span[-1]], V_0_vector, t_eval=t_span) # Solve Lyapunov equation through Fourth order Runge Kutta
        
        # Unpack the output of ode45 into a cell where each entry contains the information about the evolved CM at each time
        self.V = [];                                                            # Initialize a cell to store all CMs for each time
        
        for i in range(len(solution_lyapunov.t)):
            V_current_vector = solution_lyapunov.y[:,i];                                  # Take the full Covariance matrix in vector form
            V_current = np.reshape(V_current_vector, (self.Size_matrices, self.Size_matrices)); # Reshape it into a proper matrix
            self.V.append(V_current);                                           # Append it on the class attribute
            
        return solution_lyapunov.status
    
    def build_states(self):
        """
        Builds the gaussian state at each time from their mean values and covariance matrices
        This funciton is completely unnecessary, but it makes the code more readable :)
       
        CALCULATES:
          self.state - array with time evolved gaussian states for each timestamp of the input argument t_span
          each entry of the array is a gaussian_state class instance
        """
      
        assert self.R.size != 0 and self.V != 0, "No mean quadratures or covariance matrices, can not build time evolved states!"
        
        self.state = []
        
        for i in range(self.N_time):
            self.state.append( gaussian_state(self.R[:, i], self.V[i]) );
        
    def steady_state(self, A_0=0, A_c=0, A_s=0, omega=0): # *args -> CONSERTAR !
        """
        Calculates the steady state for the system
       
        PARAMETERS:
          self   - class instance
        
          The next parameters are only necessary if the drift matrix has a time dependency (and it is periodic)
          A_0, A_c, A_s - components of the Floquet decomposition of the drift matrix
          omega - Frequency of the drift matrix
        
        CALCULATES:
          self.steady_state_internal with the steady state (gaussian_state)
          ss - gaussian_state with steady state of the system
        """
      
        if is_a_function(self.A):                                               # If the Langevin and Lyapunov eqs. have a time dependency, move to the Floquet solution
            ss = self.floquet(A_0, A_c, A_s, omega);
            self.steady_state_internal = ss;
        else :                                                                  # If the above odes are time independent, 
            assert self.is_stable, "There is no steady state covariance matrix, as the system is not stable!"  # Check if there exist a steady state!
        
        R_ss = np.linalg.solve(self.A, -self.N);                                # Calculate steady-state mean quadratures
        V_ss = solve_continuous_lyapunov(self.A, -self.D);                      # Calculate steady-state covariance matrix
        
        self.steady_state_internal = gaussian_state(R_ss, V_ss);                # Generate the steady state
        ss = self.steady_state_internal;                                        
        return ss                                                               # Return the gaussian_state with the steady state for this system
        return ss
    
    def floquet(self, A_0, A_c, A_s, omega):
        """
        Calculates the staeady state of a system with periodic Hamiltonin/drift matrix
        Uses first order approximation in Floquet space for this calculation
       
        Higher order approximations will be implemented in the future
        
        PARAMETERS:
          self   - class instance
        
          A_0, A_c, A_s - components of the Floquet decomposition of the drift matrix
          omega - Frequency of the drift matrix
        
        CALCULATES:
          self.steady_state_internal with the steady state (gaussian_state)
          ss - gaussian_state with steady state of the system
        """
      
        M = self.Size_matrices;                                                 # Size of the time-dependent matrix
        Id = np.identity(M);                                                    # Identity matrix for the system size
        
        A_F = np.block([[A_0,    A_c   ,     A_s  ],
                        [A_c,    A_0   , -omega*Id],
                        [A_s, +omega*Id,     A_0  ]])                           # Floquet drift     matrix
        
        D_F = np.kron(np.eye(3,dtype=int), self.D)                              # Floquet diffusion matrix
        
        N_F = np.vstack([self.N, self.N, self.N])                               # Floquet mean noise vector
        
        R_ss_F = np.linalg.solve(A_F, -N_F);                                    # Calculate steady-state Floquet mean quadratures vector
        V_ss_F = solve_continuous_lyapunov(A_F, -D_F);                          # Calculate steady-state Floquet covariance matrix
        
        R_ss = R_ss_F[0:M];                                                     # Get only the first entries
        V_ss = V_ss_F[0:M, 0:M];                                                # Get only the first sub-matrix
        
        self.steady_state_internal = gaussian_state(R_ss, V_ss); # Generate the steady state
        ss = self.steady_state_internal; 
        return ss
    
    def langevin_semi_classical(self, t_span, N_ensemble=2e+2):
        """
        Solve the semi-classical Langevin equation for the expectation value of the quadrature operators
        using a Monte Carlos simulation to numericaly integrate the Langevin equations
        
        The initial conditions follows the initial state probability density in phase space
        The differential stochastic equations are solved through a Euler-Maruyama method
       
        PARAMETERS:
          self   - class instance
          N_ensemble (optional) - number of iterations for Monte Carlos simulation, default value: 200
       
        CALCULATES:
          self.R_semi_classical - matrix with the quadratures expectation values of the time evolved system where 
          self.R_semi_classical(i,j) is the i-th quadrature expectation value at the j-th time
        """
      
        self.t = t_span;                                                        # Timestamps for the simulation
        self.N_time = len(t_span);                                              # Number of timestamps
        
        dt = self.t(2) - self.t(1);                                             # Time step
        sq_dt =  np.sqrt(dt);                                                   # Square root of time step (for Wiener proccess in the stochastic integration)
        
        noise_amplitude = self.N + np.sqrt( np.diag(self.D) );                  # Amplitude for the noises (square root of the auto correlations)
        
        mean_0 = self.initial_state.R;                                          # Initial mean value
        std_deviation_0 =  np.sqrt( np.diag(self.initial_state.V) );            # Initial standard deviation
        
        self.R_semi_classical = np.zeros((self.Size_matrices, self.N_time));    # Matrix to store each quadrature ensemble average at each time
        
        if is_a_function(self.A):                                               # I have to check if there is a time_dependency on the odes
            AA = lambda t: self.A(t);                                           # Rename the function that calculates the drift matrix at each time
        else:
            AA = lambda t: self.A;                                              # If A is does not vary in time, the new function always returns the same value 
      
        for i in range(N_ensemble):                                             # Loop on the random initial positions (# Monte Carlos simulation using Euler-Maruyama method in each iteration)
            
            X = np.zeros((self.Size_matrices, self.N_time));                    # For this iteration, this matrix stores each quadrature at each time (first and second dimensions, respectively)
            X[:,0] = np.random.normal(mean_0, std_deviation_0)                  # Initial Cavity position quadrature (normal distribution for vacuum state)
            
            noise = np.random.standard_normal(X.shape);
            for k in range(self.N_time):                                        # Euler-Maruyama method for stochastic integration
                X[:,k+1] = X[:,k] + np.matmul(AA(self.t[k]), X[:,k])*dt + sq_dt*np.multiply(noise_amplitude, noise[:,k])
                                   
            self.R_semi_classical = self.R_semi_classical + X;                  # Add the new  Monte Carlos iteration quadratures to the same matrix
        
        self.R_semi_classical = self.R_semi_classical/N_ensemble;               # Divide the ensemble sum to obtain the average quadratures at each time
 


