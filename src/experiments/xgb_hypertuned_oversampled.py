from src.experiments.utils import *
from src.features.feature_engineering_2 import select_features
from sklearn.model_selection import train_test_split
import xgboost as xgb
from imblearn.over_sampling import SMOTE



def main():
    data = pd.read_csv("data/datasets/csv_files/2016-2019-v2.csv")
    X, y = select_features(data, dropna=True)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    smote = SMOTE(random_state=42)

    X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)
    
    model = xgb.XGBClassifier(
        subsample=0.6,
        n_estimators=200,
        min_child_weight=5,
        max_depth=15,
        learning_rate=0.2,
        colsample_bytree=0.5,
    )
    model.fit(X_train_smote, y_train_smote)

    y_pred = model.predict(X_val)
    y_pred_proba = model.predict_proba(X_val)[:, 1]

    exp = create_experiment("xgb_hypertuned_oversampled")
    log_metrics(exp, y_val, y_pred, y_pred_proba)
    log_plots(exp, y_val.values, y_pred_proba)
    log_model(
        exp,
        model,
        "xgb_hypertuned_oversampled",
        ["XGBoost", "Model hypertuned on F1 score", "Features: Q4 set, oversampled using SMOTE"],
    )
    exp.end()


if __name__ == "__main__":
    main()
