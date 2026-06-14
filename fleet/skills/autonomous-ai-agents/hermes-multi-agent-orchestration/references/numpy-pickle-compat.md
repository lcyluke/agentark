# NumPy Pickle Cross-Version Compatibility Fix

## Problem

Models pickled with older NumPy versions (≤1.24) fail to load on NumPy 1.26+:

```
ValueError: <class 'numpy.random._mt19937.MT19937'> is not a known BitGenerator module.
```

Or:
```
ValueError: state is not a legacy MT19937 state
```

This happens because NumPy's internal BitGenerator serialization format changed between versions. The pickle contains class references and state that the newer NumPy cannot reconstruct.

## Failed Approaches

1. **Monkey-patching `numpy.random._pickle.__bit_generator_ctor`** — the state format is fundamentally incompatible, not just the class lookup.
2. **Registering legacy BitGenerator classes** — `numpy.random._pickle.BitGenerators` dict already contains `MT19937`, the issue is the state bytes.
3. **`pickletools.dis()` + manual reconstruction** — too fragile, format depends on internal NumPy state layout.

## Solution: Retrain from Features

When the original feature matrix (X) and labels (y) are available as `.npy` files:

```python
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score
import pickle

X = np.load('data/features/X_features.npy')
y = np.load('data/features/y_grade.npy')

# If original model used label remapping (e.g. L3-L6 → 0-3), replicate:
mask = y >= 3
X_filtered = X[mask]
y_remapped = y[mask] - 3

model = GradientBoostingClassifier(
    n_estimators=100, max_depth=3,
    learning_rate=0.1, random_state=42
)
model.fit(X_filtered, y_remapped)

# Verify CV matches original
scores = cross_val_score(model, X_filtered, y_remapped, cv=5)
print(f'CV accuracy: {scores.mean():.1%}')

# Save with current NumPy
with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)
```

## Key Checks

1. **CV score must match original** (±1-2% is acceptable). If significantly different, the feature/label mapping is wrong.
2. **Label remapping**: check if the original model used raw labels (2-6) or remapped (0-3). This is the most common cause of "0/10 prediction match" in UAT.
3. **Filter criteria**: some models only train on a subset (e.g., L3+ for 羽球宝 GBDT). Check the original training data filter.
4. **Random state**: set `random_state=42` for reproducibility.

## When Features Are NOT Available

If only the pickle exists without training data:
- Option A: Install the original NumPy version in a venv, load and re-save
- Option B: Use `numpy.save()` format instead of `pickle.dump()` — `.npy` is more portable
- Option C: Export model parameters manually and reconstruct the model object
