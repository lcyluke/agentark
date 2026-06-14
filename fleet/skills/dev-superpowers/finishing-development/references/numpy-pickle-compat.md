# NumPy Pickle Compatibility — Loading Old Models on New NumPy

## Problem
`pickle.load()` fails with:
```
ValueError: <class 'numpy.random._mt19937.MT19937'> is not a known BitGenerator module.
```
or
```
ValueError: state is not a legacy MT19937 state
```

This happens when a scikit-learn model was trained with numpy <1.24 and loaded on numpy >=1.26.

## Fix: Retrain (preferred)
If you have the original feature files (X.npy, y.npy), retrain:
```python
from sklearn.ensemble import GradientBoostingClassifier
import numpy as np

X = np.load('X_features.npy')
y = np.load('y_grade.npy')

model = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
model.fit(X, y)

with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)
```

## Fix: Compatibility Shim (fallback)
If retraining isn't possible, patch numpy's pickle loader:
```python
import numpy.random._pickle as rp

_orig = rp.__bit_generator_ctor
def _fixed(bg_name='MT19937'):
    if not isinstance(bg_name, str):
        bg_name = bg_name.__name__
    if bg_name in rp.BitGenerators:
        return rp.BitGenerators[bg_name]()
    return rp.MT19937()
rp.__bit_generator_ctor = _fixed

# Now pickle.load() should work
```

## Key Insight
Old pickle format stored the BitGenerator CLASS object directly, new format expects a string NAME. The shim converts class→name before lookup.
