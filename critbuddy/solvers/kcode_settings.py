"""Shared Monte Carlo kcode-style run settings used across MCNP and OpenMC."""

KCODE_SETTINGS = {
    "PARTICLES": 4800,
    "BATCHES": 200,
    "INACTIVE": 50,
}


SMOKE_TEST_KCODE_SETTINGS = {
    "PARTICLES": 5000,
    "BATCHES": 50,
    "INACTIVE": 10,
}
