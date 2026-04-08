import numpy as np
import random
import os

def setup_determinism(seed: int = 42):
    """
    Set global seeds for all libraries to ensure reproducible results.
    """
    random.seed(seed)
    np.random.seed(seed)
    # Ensure any environment-level randomness is also fixed
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    print(f"[Reproducibility] Global seed set to {seed}")
