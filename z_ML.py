import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix, root_mean_squared_error
from sklearn.preprocessing import OneHotEncoder 
from sklearn.model_selection import KFold, cross_val_score
import json
from datetime import datetime
import statistics
import pandas as pd

def regression():
    with open("high_confidence.json", "r") as f:
        events = json.load(f)

    x_data = []
    y_data = []

    for event in events:
        hour_of_day = datetime.fromisoformat(event["timestamp"]).hour
        x_data.append([hour_of_day, event["confidence"]])
        y_data.append(event["dwell_seconds"])

    x_data_array = np.array(x_data)
    y_data_array = np.array(y_data)

    model = LinearRegression()
    model.fit(x_data_array, y_data_array)

    print("Intercept:", model.intercept_)
    print("Coefficients:", model.coef_)

    test_case = np.array([[datetime.fromisoformat("2023-01-01 12:00:00").hour, 0.9]])
    prediction = model.predict(test_case)
    print("Prediction:", prediction)

def classifier(): #to predict if a event has a dwell time above the median

    x_data = []
    y_data = []
    encoder = OneHotEncoder(sparse_output=False, drop='first') # must be called outside the input_model function so that it remains fitted.
    input_to_model("high_confidence.json", x_data, y_data, encoder, fit_encoder = True)
    
    x_data_array = np.array(x_data)
    y_data_array = np.array(y_data)
    
    model = LogisticRegression(max_iter = 1000) #or DecisionTreeClassifier(max_depth = . . .)

    def cross_val():
        cross_validation = KFold(n_splits = 5, shuffle = True, random_state = 32)  #splits test/training automatically
        scores = cross_val_score(model, x_data_array, y_data_array, cv = cross_validation, scoring = "accuracy")  #fits automatically
        print(scores)
    cross_val()

    model.fit(x_data_array, y_data_array)
    
    print("Intercept:", model.intercept_)
    print("Coefficients:", model.coef_)

    new_data = []
    junk = []
    input_to_model("test_events.json", new_data, junk, encoder, fit_encoder = False)
    
    new_data_array = np.array(new_data)

    for data in new_data_array:
        prediction = model.predict([data])
        if prediction == 1:
            print(f"Prediction for data {data}: Dwell time is above the median.")
            break
        else:
            print(f"Prediction for data {data}: Dwell time is below the median.")
            break

    y_predicted = model.predict(new_data_array)
    return y_predicted


  
def evaluation(y_predicted):

    y_true = []

    with open("test_events.json", "r") as f:
        events = json.load(f)

    for event in events:
        dwell_time_list = [event["dwell_seconds"] for event in events]
        dwell_time_median = statistics.median(dwell_time_list)
        y_true.append(int(event["dwell_seconds"] > dwell_time_median))

    accuracy = accuracy_score(y_true, y_predicted)
    precision = precision_score(y_true, y_predicted)
    recall = recall_score(y_true, y_predicted)
    conf_matrix = confusion_matrix(y_true, y_predicted)
    rmse = root_mean_squared_error(y_true, y_predicted)

    print("Accuracy:", accuracy)
    print("Precision:", precision)
    print("Recall:", recall)
    print("Confusion Matrix:\n", conf_matrix)
    print("RMSE:", rmse)

def input_to_model(json_load, array, test_array, encoder, fit_encoder):

    df = pd.read_json(json_load)
    df = df.sort_values("timestamp")
    df["rolling_average"] = (df.groupby("brand")["dwell_seconds"].transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean()))
    dwell_time_median = df["dwell_seconds"].median()

    if fit_encoder:
        encoded_data = encoder.fit_transform(df[["brand"]])
    else:
        encoded_data = encoder.transform(df[["brand"]])

    encoded_df = pd.DataFrame(encoded_data, columns=encoder.get_feature_names_out(["brand"]), index = df.index)
    df = pd.concat([df, encoded_df], axis = 1)

    for i, row in enumerate(df.itertuples()):
        hour_of_day = row.timestamp.hour
        hour_sin = np.sin(2 * np.pi * hour_of_day / 24)
        hour_cos = np.cos(2 * np.pi * hour_of_day / 24)
        weekday = row.timestamp.weekday()
        rolling_average = row.rolling_average if pd.notna(row.rolling_average) else 0.0
        brand_encoded = encoded_df.iloc[i].tolist() #getattr fails to pull names with special attributes. 
        array.append([hour_sin, hour_cos, weekday, row.confidence, rolling_average] + brand_encoded)
        test_array.append(int(row.dwell_seconds > dwell_time_median))

if __name__ == "__main__":
    regression()
    evaluation(y_predicted = classifier())

        



