import autograd.numpy as np  # Thinly-wrapped version of Numpy
from scipy.stats import t


def stddev(v):
    """
    Sample standard deviation of the vector v,
    with Bessel's correction

    :param v: vector of data
    :type v: Numpy ndarray
    :return: Standard deviation with Bessel's correction
    :rtype: float
    """
    return np.std(v, ddof=1)


def tinv(p, nu):
    """
    Returns the inverse of Student's t CDF
    using the degrees of freedom in nu for the corresponding
    probabilities in p.

    Python implementation of Matlab's tinv function:
    https://www.mathworks.com/help/stats/tinv.html

    :param p: Probability
    :type p: float
    :param nu: Degrees of freedom
    :type nu: int
    :return: Inverse of the Student's t CDF
    :rtype: float
    """
    return t.ppf(p, nu)


def weighted_sum_gamma(arr, gamma=0.9):
    """Calculate weighted sum of an array,
    where weights are gamma**(index of arr).
    Used in calculating sum of discounted rewards in RL

    :param arr: An input array
    :type arr: Numpy ndarray
    :param gamma: The constant used for weighting the array,
        also called the discount factor in RL
    :type gamma: float
    :return: The weighted sum
    :rtype: float
    """
    weights = np.power(gamma, range(len(arr)))
    return np.average(arr, weights=weights) * np.sum(weights)


def softmax(x):
    return np.exp(x) / sum(np.exp(x))
