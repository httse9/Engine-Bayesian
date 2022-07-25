import os, sys
import autograd.numpy as np  # Thinly-wrapped version of Numpy

from seldonian.seldonian_algorithm import SeldonianAlgorithm
from seldonian.utils.io_utils import load_pickle

if __name__ == '__main__':
    specfile = './seldonian/RL/spec.pkl'
    spec = load_pickle(specfile)

    dataset = spec.dataset
    regime = dataset.regime
    print(regime)
    print(spec.RL_environment_obj)
    print(spec.RL_environment_obj.gamma)

    spec.use_builtin_primary_gradient_fn = False
    spec.optimization_hyperparams['num_iters'] = 40
    spec.optimization_hyperparams['alpha_theta'] = 0.05
    spec.optimization_hyperparams['alpha_lamb'] = 0.05
    # spec.regularization_hyperparams['reg_coef'] = 0.1
    SA = SeldonianAlgorithm(spec)
    passed_safety, candidate_solution = SA.run()
    print(passed_safety, candidate_solution)
