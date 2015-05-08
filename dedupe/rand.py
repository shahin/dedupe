"""This module provides a dedupe-local random number generator.

Dedupe uses global random number generators to drive stochastic methods. Long-lived production
systems need (1) deterministic behavior for debugging and (2) module-level local state. This random
number generator can be configured for deterministic behavior and will not leak state into other
modules that use numpy.random or stdlib's random.
"""
import numpy

_rand = numpy.random.RandomState()
seed = _rand.seed

permutation = _rand.permutation
randint = _rand.randint
shuffle = _rand.shuffle
