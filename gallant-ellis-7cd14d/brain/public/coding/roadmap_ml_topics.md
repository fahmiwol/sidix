# Machine Learning Roadmap — Topic Index + Quick Reference

> Sumber: roadmap.sh/machine-learning (CC BY-SA 4.0)
> Referensi: https://roadmap.sh/machine-learning

## Mathematics Foundations

### Linear Algebra
```python
import numpy as np

# Vectors
v = np.array([1, 2, 3])
dot_product = np.dot(v, v)          # 14
norm = np.linalg.norm(v)            # √14 ≈ 3.74
cosine_sim = np.dot(a, b) / (norm_a * norm_b)  # similarity

# Matrices
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])
C = A @ B                           # matrix multiply
A_T = A.T                           # transpose
A_inv = np.linalg.inv(A)            # inverse

eigenvalues, eigenvectors = np.linalg.eig(A)

# SVD (Singular Value Decomposition) — used in PCA, matrix factorization
U, s, Vt = np.linalg.svd(A)
```

### Probability and Statistics
```python
import numpy as np
from scipy import stats

# Distributions
normal = stats.norm(loc=0, scale=1)   # N(0,1)
normal.pdf(0)                         # probability density at 0
normal.cdf(1.96)                      # P(X <= 1.96) ≈ 0.975

# Descriptive stats
data = np.array([2, 4, 4, 4, 5, 5, 7, 9])
np.mean(data)         # 5.0
np.median(data)       # 4.5
np.var(data)          # 4.0
np.std(data)          # 2.0

# Bayes' Theorem
# P(A|B) = P(B|A) * P(A) / P(B)
# posterior = likelihood * prior / evidence
```

### Calculus for ML
- **Gradient**: vector of partial derivatives; points in direction of steepest ascent
- **Chain rule**: d/dx[f(g(x))] = f'(g(x)) * g'(x) → basis of backpropagation
- **Gradient descent**: θ = θ - α * ∇L(θ) where α = learning rate, L = loss function

## Core ML Concepts

### Types of Machine Learning
| Type | Description | Examples |
|---|---|---|
| Supervised | Labeled data, learn mapping X → y | Classification, regression |
| Unsupervised | Unlabeled data, find structure | Clustering, dimensionality reduction |
| Semi-supervised | Mix of labeled + unlabeled | Self-training, pseudo-labeling |
| Reinforcement | Agent learns from rewards | Game AI, robotics |
| Self-supervised | Labels from data itself | GPT pretraining, BERT |

### Bias-Variance Tradeoff
```
Total Error = Bias² + Variance + Irreducible Noise

High Bias (underfitting):
  → Model too simple, doesn't capture patterns
  → Fix: more complex model, more features

High Variance (overfitting):
  → Model memorizes training data, fails on new data
  → Fix: regularization, more data, simpler model, dropout

Sweet spot: right balance of bias and variance
```

### Train / Validation / Test Split
```python
from sklearn.model_selection import train_test_split

# Split 80/10/10
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.2, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

# Cross-validation (better for small datasets)
from sklearn.model_selection import cross_val_score
scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
print(f"Mean: {scores.mean():.3f} ± {scores.std():.3f}")
```

## Data Processing

### NumPy Essentials
```python
import numpy as np

# Array creation
arr = np.zeros((3, 4))          # 3×4 zeros
arr = np.ones((2, 3))           # 2×3 ones
arr = np.eye(3)                 # 3×3 identity matrix
arr = np.random.randn(100, 10)  # N(0,1) random
arr = np.arange(0, 10, 0.5)    # 0 to 9.5 step 0.5
arr = np.linspace(0, 1, 100)   # 100 evenly spaced from 0 to 1

# Shape operations
arr.shape       # (100, 10)
arr.reshape(1000,)
arr.reshape(-1, 5)  # auto-calculate first dim
arr.flatten()
arr.T           # transpose
np.expand_dims(arr, axis=0)  # add dimension
np.squeeze(arr)              # remove size-1 dimensions

# Indexing
arr[0]          # first row
arr[:, 0]       # first column
arr[2:5, 1:3]   # slice
arr[arr > 0]    # boolean indexing
arr[[0, 2, 4]]  # fancy indexing

# Broadcasting
# Operations on arrays of different shapes
a = np.array([[1], [2], [3]])  # (3, 1)
b = np.array([1, 2, 3])        # (3,) → (1, 3)
a + b  # (3, 3) — broadcasts
```

### Pandas Essentials
```python
import pandas as pd

df = pd.read_csv("data.csv")
df.info()                           # dtypes, nulls, memory
df.describe()                       # summary stats
df.head(10)

# Selection
df["column"]                        # Series
df[["col1", "col2"]]                # DataFrame
df.loc[0:5, "col"]                  # label-based
df.iloc[0:5, 0]                     # position-based
df[df["age"] > 25]                  # boolean filter
df.query("age > 25 and active == True")

# Missing data
df.isnull().sum()                   # count nulls per column
df.dropna()                         # drop rows with any null
df.fillna(0)                        # fill nulls with 0
df["age"].fillna(df["age"].mean())  # fill with mean

# Aggregation
df.groupby("category")["value"].agg(["mean", "std", "count"])
df.pivot_table(values="sales", index="region", columns="quarter", aggfunc="sum")

# Data types and conversion
df["age"] = df["age"].astype(int)
pd.to_datetime(df["date"])
pd.get_dummies(df["category"])      # one-hot encoding

# Apply custom functions
df["score"].apply(lambda x: "pass" if x >= 60 else "fail")
df.apply(lambda row: row["a"] + row["b"], axis=1)
```

## Classical Machine Learning (Scikit-learn)

### Regression
```python
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score

# Linear Regression
model = LinearRegression()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
print(f"R²: {r2_score(y_test, y_pred):.3f}")
print(f"RMSE: {mean_squared_error(y_test, y_pred, squared=False):.3f}")

# Ridge (L2 regularization — shrinks coefficients)
ridge = Ridge(alpha=1.0)
ridge.fit(X_train, y_train)

# Lasso (L1 regularization — sets some coefficients to 0; feature selection)
lasso = Lasso(alpha=0.1)

# Polynomial regression
pipe = Pipeline([
    ("poly", PolynomialFeatures(degree=2, include_bias=False)),
    ("model", LinearRegression()),
])
```

### Classification
```python
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score, accuracy_score)

# Logistic Regression
clf = LogisticRegression(C=1.0, max_iter=1000)
clf.fit(X_train, y_train)
y_pred = clf.predict(X_test)
y_proba = clf.predict_proba(X_test)[:, 1]

print(classification_report(y_test, y_pred))
print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.3f}")

# Random Forest
rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1,
)
rf.fit(X_train, y_train)
print("Feature importance:", rf.feature_importances_)

# Gradient Boosting (XGBoost/LightGBM for production)
import xgboost as xgb
model = xgb.XGBClassifier(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric="auc",
)
model.fit(X_train, y_train, eval_set=[(X_val, y_val)], early_stopping_rounds=50)
```

### Unsupervised Learning
```python
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler

# K-Means clustering
kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
kmeans.fit(X)
labels = kmeans.labels_
centroids = kmeans.cluster_centers_

# Elbow method to find optimal k
inertias = []
for k in range(1, 11):
    km = KMeans(n_clusters=k, random_state=42)
    km.fit(X)
    inertias.append(km.inertia_)

# PCA — dimensionality reduction
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

pca = PCA(n_components=2)
X_2d = pca.fit_transform(X_scaled)
print(f"Explained variance: {pca.explained_variance_ratio_}")

# Find n_components for 95% variance
pca_full = PCA()
pca_full.fit(X_scaled)
n_components = np.argmax(np.cumsum(pca_full.explained_variance_ratio_) >= 0.95) + 1
```

### Feature Engineering
```python
from sklearn.preprocessing import (StandardScaler, MinMaxScaler,
                                   LabelEncoder, OneHotEncoder,
                                   RobustScaler)
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.impute import SimpleImputer, KNNImputer

# Scaling
# StandardScaler: mean=0, std=1 (good for linear models, NNs)
# MinMaxScaler: range [0, 1] (good for bounded distributions)
# RobustScaler: uses median/IQR (robust to outliers)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)   # fit + transform on train
X_test_scaled = scaler.transform(X_test)   # only transform on test!

# Encoding categorical variables
# One-hot: low-cardinality categories
enc = OneHotEncoder(drop="first", sparse_output=False)
X_encoded = enc.fit_transform(X_cat)

# Label encoding: ordinal categories
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Imputation
imputer = SimpleImputer(strategy="median")
X_imputed = imputer.fit_transform(X)

# Feature selection
selector = SelectKBest(score_func=f_classif, k=10)
X_selected = selector.fit_transform(X, y)
selected_features = selector.get_support(indices=True)
```

## Deep Learning

### Neural Network Fundamentals
```
Input layer → Hidden layers → Output layer

Each neuron: output = activation(W · input + bias)

Activation functions:
  ReLU: max(0, x) — default for hidden layers
  Leaky ReLU: x if x>0 else αx — avoid dying ReLU
  Sigmoid: 1/(1+e^-x) — output layer for binary classification
  Softmax: exp(xi)/Σexp(xj) — output layer for multi-class
  Tanh: (e^x - e^-x)/(e^x + e^-x) — range [-1, 1]
  GELU: x * Φ(x) — used in transformers

Loss functions:
  MSE: mean((y_pred - y_true)²) — regression
  Binary cross-entropy: -[y*log(p) + (1-y)*log(1-p)] — binary classification
  Categorical cross-entropy: -Σ y_i * log(p_i) — multi-class
```

### PyTorch
```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# Tensors
x = torch.tensor([1.0, 2.0, 3.0])
x = torch.zeros(3, 4)
x = torch.randn(10, 5)
x = x.to("cuda" if torch.cuda.is_available() else "cpu")

# Custom Dataset
class SIDIXDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.encodings = tokenizer(texts, truncation=True, padding="max_length",
                                  max_length=max_length, return_tensors="pt")
        self.labels = torch.tensor(labels)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return {
            "input_ids": self.encodings["input_ids"][idx],
            "attention_mask": self.encodings["attention_mask"][idx],
            "labels": self.labels[idx],
        }

# Neural Network
class MLP(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, output_dim),
        )
    
    def forward(self, x):
        return self.net(x)

# Training loop
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = MLP(784, 256, 10).to(device)
optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=100)
criterion = nn.CrossEntropyLoss()

for epoch in range(num_epochs):
    model.train()
    total_loss = 0
    for batch in train_loader:
        X, y = batch[0].to(device), batch[1].to(device)
        optimizer.zero_grad()
        output = model(X)
        loss = criterion(output, y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        total_loss += loss.item()
    scheduler.step()
    
    # Validation
    model.eval()
    with torch.no_grad():
        val_output = model(X_val.to(device))
        val_loss = criterion(val_output, y_val.to(device))
    print(f"Epoch {epoch}: train={total_loss/len(train_loader):.4f}, val={val_loss:.4f}")
```

## Natural Language Processing (NLP)

### Text Processing Pipeline
```
Raw text → Tokenization → Normalization → Feature extraction → Model
```

### Transformers (HuggingFace)
```python
from transformers import (AutoTokenizer, AutoModel,
                          AutoModelForSequenceClassification,
                          TrainingArguments, Trainer)
from peft import LoraConfig, get_peft_model, TaskType

# Load pretrained model
model_name = "Qwen/Qwen2.5-7B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# LoRA fine-tuning
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.1,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()  # shows % trainable

# Training arguments
training_args = TrainingArguments(
    output_dir="./checkpoints",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_steps=100,
    lr_scheduler_type="cosine",
    logging_steps=10,
    save_strategy="epoch",
    fp16=True,
    optim="paged_adamw_32bit",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
)
trainer.train()
```

## ML Metrics

### Classification
```
Accuracy    = (TP + TN) / (TP + TN + FP + FN)
Precision   = TP / (TP + FP) — when positive, how often correct?
Recall      = TP / (TP + FN) — how many positives caught?
F1-score    = 2 * Precision * Recall / (Precision + Recall)
ROC-AUC     = area under ROC curve; 0.5=random, 1.0=perfect
PR-AUC      = area under Precision-Recall; better for imbalanced

When to optimize:
  Precision: costly false positives (spam filter, medical diagnosis)
  Recall: costly false negatives (fraud detection, disease screening)
  F1: balance both
```

### Regression
```
MAE  = mean(|y_pred - y_true|)          — robust to outliers
MSE  = mean((y_pred - y_true)²)         — penalizes large errors
RMSE = √MSE                             — same units as target
R²   = 1 - SS_res/SS_tot               — proportion of variance explained
MAPE = mean(|y_pred - y_true| / |y_true|) — relative error
```

## ML Workflow Best Practices

```
1. Problem definition — regression, classification, clustering?
2. Data collection & EDA — understand distribution, missing, outliers
3. Feature engineering — domain knowledge → useful features
4. Baseline model — start simple (linear regression, random forest)
5. Model selection + hyperparameter tuning
6. Error analysis — where does model fail? What patterns?
7. Iteration — add features, try new models, ensemble
8. Deployment — serve predictions via API
9. Monitoring — track performance drift over time
```

### Hyperparameter Tuning
```python
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from scipy.stats import randint, uniform

# Grid search (exhaustive)
param_grid = {
    "n_estimators": [100, 200, 500],
    "max_depth": [5, 10, 15],
    "min_samples_split": [2, 5, 10],
}
search = GridSearchCV(rf, param_grid, cv=5, scoring="f1", n_jobs=-1)
search.fit(X_train, y_train)
print(search.best_params_)

# Random search (faster, usually good enough)
param_dist = {
    "n_estimators": randint(100, 1000),
    "max_depth": randint(3, 20),
    "learning_rate": uniform(0.01, 0.3),
}
search = RandomizedSearchCV(xgb, param_dist, n_iter=50, cv=5, random_state=42)

# Optuna (Bayesian optimization — modern approach)
import optuna

def objective(trial):
    lr = trial.suggest_float("lr", 1e-5, 1e-1, log=True)
    n_layers = trial.suggest_int("n_layers", 1, 4)
    model = build_model(lr=lr, n_layers=n_layers)
    return evaluate(model, X_val, y_val)

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=100)
print(study.best_params)
```

## Referensi Lanjut
- https://roadmap.sh/machine-learning
- https://scikit-learn.org/stable/ — comprehensive ML library
- https://pytorch.org/tutorials/ — deep learning with PyTorch
- https://huggingface.co/docs — transformers, PEFT, datasets
- https://kaggle.com — competitions, datasets, notebooks
- "Hands-On Machine Learning" — Aurélien Géron
- "Deep Learning" — Goodfellow, Bengio, Courville (free PDF)
- fast.ai — practical DL courses
