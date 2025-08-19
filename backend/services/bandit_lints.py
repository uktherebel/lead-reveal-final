import numpy as np
from typing import Any, Dict

class LinTS:
    def __init__(self, n_arms: int, d: int, lam: float=1.0, v: float=0.5):
        self.n, self.d, self.v = n_arms, d, v
        self.A = [lam*np.eye(d) for _ in range(n_arms)]
        self.b = [np.zeros((d,1)) for _ in range(n_arms)]

    def choose(self, x: np.ndarray, allowed=None, rng=None) -> int:
        rng = rng or np.random.default_rng()
        x = x.reshape(-1,1); arms = allowed or list(range(self.n))
        best, arm = -1e9, arms[0]
        for a in arms:
            Ainv = np.linalg.inv(self.A[a])
            theta = Ainv @ self.b[a]
            L = np.linalg.cholesky(Ainv)
            theta_t = theta + self.v * (L @ rng.standard_normal((self.d,1)))
            s = float(x.T @ theta_t)
            if s > best: best, arm = s, a
        return arm

    def update(self, arm: int, x: np.ndarray, r: float):
        x = x.reshape(-1,1)
        self.A[arm] += x @ x.T
        self.b[arm] += r * x

    def to_dict(self) -> Dict[str, Any]:
        return {"n": self.n, "d": self.d, "v": self.v,
                "A": [A.tolist() for A in self.A],
                "b": [b.tolist() for b in self.b]}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LinTS":
        obj = cls(d["n"], d["d"], v=d.get("v",0.5))
        obj.A = [np.array(A) for A in d["A"]]
        obj.b = [np.array(b) for b in d["b"]]
        return obj
