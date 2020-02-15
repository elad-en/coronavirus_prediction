import operator
import json
import numpy as np
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_squared_error, r2_score

from data_grabber import DataGrabber

def get_training_set_from_file(dataset_type, offline_dataset_date=""):
    filename = DataGrabber().get_dataset_file_name(dataset_type=dataset_type, dataset_date=offline_dataset_date)

    return np.genfromtxt("datasets/" + filename, delimiter=',').astype(np.int32)

def get_training_sets(grab_data_from_server=True, offline_dataset_date=""):
    grabber = DataGrabber()
    dataset_date = ""

    if grab_data_from_server:
        grabber.grab_data()
    else:
        dataset_date = offline_dataset_date

        if offline_dataset_date == "":
            raise Exception("Invalid offline dataset date received. Please update the 'offline_dataset_date' configuration in the config file and try again.")
    
    return (get_training_set_from_file("cases", offline_dataset_date=dataset_date), get_training_set_from_file("deaths", offline_dataset_date=dataset_date))

def train_model(x, y, polynomial_degree):
    polynomial_features = PolynomialFeatures(degree=polynomial_degree)
    x_poly = polynomial_features.fit_transform(x)

    model = LinearRegression()
    model.fit(x_poly, y)

    return model

def get_predictions(x, model, polynomial_degree):
    polynomial_features = PolynomialFeatures(degree=polynomial_degree)
    x_poly = polynomial_features.fit_transform(x)

    return model.predict(x_poly)

def print_stats(model_name, model, x, y, polynomial_degree, days_to_predict):
    y_pred = np.round(get_predictions(x, model, polynomial_degree), 0).astype(np.int32)

    print_forecast(model_name, model, polynomial_degree, beginning_day=len(x), limit=days_to_predict)
    print_model_polynomial(model_name, model)
    plot_graph(model_name, x, y, y_pred)
    print("")

def print_model_polynomial(model_name, model):
    coef = model.coef_
    intercept = model.intercept_
    poly = "{0:.3f}".format(intercept)

    for i in range(1, len(coef)):
        if coef[i] >= 0:
            poly += " + "
        else:
            poly += " - "
        
        poly += "{0:.3f}".format(coef[i]).replace("-", "") + "X^" + str(i)

    print("The " + model_name + " model function is: f(X) = " + poly)

def plot_graph(model_name, x, y, y_pred):
    plt.scatter(x, y, s=10)
    sort_axis = operator.itemgetter(0)
    sorted_zip = sorted(zip(x, y_pred), key=sort_axis)
    x, y_pred = zip(*sorted_zip)
    
    plt.plot(x, y_pred, color='m')
    plt.title("Amount of " + model_name + " in each day")
    plt.xlabel("Day")
    plt.ylabel(model_name)
    plt.show()

def print_forecast(model_name, model, polynomial_degree, beginning_day=0, limit=10):
    next_days_x = np.array(range(beginning_day, beginning_day + limit)).reshape(-1, 1)
    next_days_pred = np.round(get_predictions(next_days_x, model, polynomial_degree), 0).astype(np.int32)

    print("The forecast for " + model_name + " in the following " + str(limit) + " days is:")

    for i in range(0, limit):
        print(str(i + 1) + ": " + str(next_days_pred[i]))

if __name__ == "__main__":
    config = {}

    with open("config.json", "r") as f:
        config = json.load(f)

    (training_set_cases, training_set_deaths) = get_training_sets(config["grab_data_from_server"], config["offline_dataset_date"])
    x_cases = training_set_cases[:, 0].reshape(-1, 1)
    x_deaths = training_set_deaths[:, 0].reshape(-1, 1)
    y_cases = training_set_cases[:, 1]
    y_deaths = training_set_deaths[:, 1]

    cases_model = train_model(x_cases, y_cases, config["cases_polynomial_degree"])
    deaths_model = train_model(x_deaths, y_deaths, config["deaths_polynomial_degree"])

    print_stats("Cases", cases_model, x_cases, y_cases, config["cases_polynomial_degree"], config["days_to_predict"])
    print_stats("Deaths", deaths_model, x_deaths, y_deaths, config["deaths_polynomial_degree"], config["days_to_predict"])