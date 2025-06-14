"""
A file to integrate out the ODE Simulation Model over a timestep

Author: David Bianchi, Enguang Fu
"""

# from pycvodes import integrate_predefined
# from pycvodes import integrate_adaptive

from scipy import integrate
import odecell
import numpy as np



### Constants
step = 0.1 # s
atol = 1e-6 # tolerance
rtol = 1e-6 # tolerance


# def setSolver(model): # Not used anymore
#     """
#     Set the solver for the model

#     Parameters:
         
#         (odecell.model) - the model object

#     Returns:

#         solvFunctor - a functor for the solver

#     """

#     ## We are NOT building for odeint (gives us more room to chose between CVODES and SciPy-ODE).
#     ## We are NOT using a jacobian, since we do not have the partial derivatives for all rate forms.
#     ## We are building with Cython for speed, this is a big model.

#     # Builds the solver using a *Functor* interface
#     solvFunctor = odecell.solver.ModelSolver(model) 
#     solvFunctor.prepareFunctor() #OG uncomment

#     # Set verbosity to 0 for now, below uncomment OG
#     rxnIdList = solvFunctor.buildCall(odeint=False, useJac=False, cythonBuild=True, functor=True, verbose=0)
#     #rxnIdList = solvFunctor.buildCall(odeint=True, useJac=False, cythonBuild=False, functor=False, transpJac=False, verbose=0, noBuild=True)

#     # Sets up the actual solver, with updated parameter values
#     #modelOptSpace, initParamVals=model.getOptSpace()
#     initParamVals = model.getInitVals()
#     solvFunctor = solvFunctor.functor( np.asarray(initParamVals, dtype=np.double) )

#     return solvFunctor

### NOTE: Have to get a callable f(y,t) for scipy.ode without creating the functor
def noCythonSetSolver(model):
    """
    Set the solver without compiling via Cython

    Parameters:

    model (odecell Model object): The model object

    Returns:

    solver (odecell Solver object): The Solver object, to solve the system of ODEs representing metabolic reactions
    """

    # Construct a Model Solver Object
    solver = odecell.solver.ModelSolver(model)

    rxnIdList =solver.buildCall(verbose=0, useJac=False, transpJac=0, nocheck=False, odeint=False, cythonBuild=False, functor=False, noBuild=True)

    return solver 

def f_wrap(solv, t, y, dydt):

    #solv = setSolver(model)
    dydt[:] = solv(0,np.asarray(y))[:]

def getInitVals(model):
    y0=model.getInitVals()
#     print(y0)
    return y0

# def noCythonRunODE():
#     """
#     Run the ODE Model without compiling via Cython

#     Parameters:

#     Returns:
#     None
#     """
#     return 0

def runODE(solv, model, odelength):
    """
    Run the ODE Model after getting initial conditions

    Parameters:

    y0 (seems non-necessary) - can remove
    time (float): the current hybrid simulation time
    delt (float): the communication timestep between stochastic and deterministic simulation
    ts (float): the timestep for the adaptive ODE Solver
    solv (odecell Solver object): The solver object, with call built
    model (odecell Model object): The model object

    Returns:

    results (np.array): the array containing ODE Simulation Results (Maybe only the last time should be passed?)
    """
    
    #y0 = model.getInitVals()
    #print("shape: ",len(y0))
    #y0 = np.asarray(y0,dtype=np.double)

    #modelOptSpace,initParamVals=model.getOptSpace()
    #dydt = np.zeros(len(y0))
    #tout, results, info = integrate_adaptive(f_wrap(solv,time+delt,y0,dydt),None,y0,time,time+delt,atol,rtol,dx0=ts,nsteps=10000)
    #tout, results, info = integrate_adaptive(f_wrap(solv,time,y0,dydt),None,y0,time,time+delt,atol,rtol,dx0=ts,nsteps=10000)

    #tout = 0.0
    #info = "place holder"

    #solv = solv.ModelSolver(model)
    #solv.buildCall(odeint=False, useJac=False, verbose=2)
    integrator = integrate.ode(solv)#, solv.calcJac)

    integrator.set_integrator("lsoda")
    # integrator.set_integrator("vode", method='bdf') # adams is non-stiff, bdf is stiff

    # Set initial values
    integrator.set_initial_value(model.getInitVals())

    ### With fixed timestepping
    step = 0.01
    totalTime = odelength
    
    # ODE concentrations 2D array
    concs = np.empty((0,len(model.getInitVals())), dtype=float)

    # Fluxes 2D array
    fluxes = np.empty((0, len(model.getRxnList())), dtype=float)

    small_step_tolerance = 1E-15

    while integrator.successful() and integrator.t < totalTime:
        currConcentration = integrator.integrate(integrator.t + step)
        # Silence integrator output for now
        #print(integrator.t, currConcentration)
        concs = np.append(concs, [np.asarray(currConcentration)], axis=0)

        flux_transient = solv.calcFlux(0, concs[-1,:]) # List

        fluxes = np.append(fluxes, [np.asarray(flux_transient)], axis=0)


    flux_end = np.asarray(solv.calcFlux(0, concs[-1,:]))

    flux_avg = np.mean(fluxes, axis=0)


    return concs, flux_avg, flux_end
