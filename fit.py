import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

ALL_SQUARE = 1

# test.xlsx
correct_df = pd.read_excel("fit.xlsx", sheet_name="Sheet1")


# Update the intervals and adjust the second segment fitting function
def square_gaussian_with_constant(x, a, mean, sigma, b, c, d):
    # Gaussian with a linear term as the constant
    return a * np.exp(-((x - mean) ** 2) / (2 * sigma ** 2)) + b * x ** 2 + c * x + d

# Update the intervals and adjust the third segment fitting function
def gaussian_with_constant(x, a, mean, sigma, b):
    # Gaussian with constant
    return a * np.exp(-((x - mean) ** 2) / (2 * sigma ** 2)) + b

# Update the intervals and adjust the first segment fitting function
def exponential_with_constant(x, a, b):
    # Exponential with constant
    return a * np.exp(b * x)

# Adjust the intervals
segments_updated = {
    "0-0.2": correct_df[(correct_df["时间"] >= 0) & (correct_df["时间"] < 0.2)],
    "0.2-0.45": correct_df[(correct_df["时间"] >= 0.2) & (correct_df["时间"] < 0.45)],
    "0.45-0.65": correct_df[(correct_df["时间"] >= 0.45) & (correct_df["时间"] < 0.65)],
    "0.65-0.85": correct_df[(correct_df["时间"] >= 0.65) & (correct_df["时间"] < 0.85)],
    "0.85-1.0": correct_df[(correct_df["时间"] >= 0.85) & (correct_df["时间"] <= 1.0)],
}

# Fit each updated segment
fit_results_updated = {}
for segment_name, segment_data in segments_updated.items():
    x = segment_data["时间"].values
    y = segment_data["数量"].values
    if segment_name == "0-0.2":
        # Fit exponential with constant
        popt, _ = curve_fit(exponential_with_constant, x, y, p0=[1, -1])
        fit_results_updated[segment_name] = {"params": popt, "function": exponential_with_constant}
    elif ALL_SQUARE or segment_name == "0.2-0.45" or segment_name == "0.65-0.85":
        # Fit Gaussian with a linear term as the constant
        popt, _ = curve_fit(square_gaussian_with_constant, x, y, p0=[max(y), np.mean(x), np.std(x), 0, 0, 0])
        fit_results_updated[segment_name] = {"params": popt, "function": square_gaussian_with_constant}
    else:
        # Fit Gaussian with constant
        popt, _ = curve_fit(gaussian_with_constant, x, y, p0=[max(y), np.mean(x), np.std(x), 0])
        fit_results_updated[segment_name] = {"params": popt, "function": gaussian_with_constant}


def round_to_fit(params, segment_name):
    if segment_name == "0-0.2":
        return [round(params[0]), round(params[1])]
    elif ALL_SQUARE or segment_name == "0.2-0.45" or segment_name == "0.65-0.85":
        return [round(params[0]), round(params[1], 4), round(params[2], 4), round(params[3]), round(params[4]), round(params[5])]
    else:
        return [round(params[0]), round(params[1], 4), round(params[2], 4), round(params[3])]

# Plot the updated results
plt.figure(figsize=(12, 8))
for segment_name, segment_data in segments_updated.items():
    x = segment_data["时间"].values
    y = segment_data["数量"].values
    plt.scatter(x, y, s=2, label=f"Data {segment_name}")
    
    # Plot the fit curve
    x_fit = np.linspace(min(x), max(x), 100)
    fit_func = fit_results_updated[segment_name]["function"]
    fit_params = round_to_fit(fit_results_updated[segment_name]["params"], segment_name)
    plt.plot(x_fit, fit_func(x_fit, *fit_params), label=f"Fit {segment_name}")

# calculate the total numerical integral
total_integral = 0
for segment_name, segment_fit in fit_results_updated.items():
    fit_func = segment_fit["function"]
    fit_params = segment_fit["params"]
    if segment_name == "0-0.2":
        total_integral += fit_func(1, *fit_params)
    elif ALL_SQUARE or segment_name == "0.2-0.45" or segment_name == "0.65-0.85":
        total_integral += fit_func(1, *fit_params) - fit_func(0.2, *fit_params)
    else:
        total_integral += fit_func(1, *fit_params) - fit_func(0.2, *fit_params)

# print the total numerical integral
print(f"Total numerical integral: {total_integral:.4f}")

# print the fit results(rounded to 1 decimal places, copy to clipboard)
results_str = "Total numerical integral: {:.0f}\n\nFitting Results:\n".format(total_integral)
for segment_name, segment_fit in fit_results_updated.items():
    params = segment_fit["params"]
    if segment_name == "0-0.2":
        results_str += f"{segment_name}: a={params[0]:.0f}, b={params[1]:.0f}\n"
    elif ALL_SQUARE or segment_name == "0.2-0.45" or segment_name == "0.65-0.85":
        results_str += f"{segment_name}: a={params[0]:.0f}, mean={params[1]:.4f}, sigma={params[2]:.4f}, b={params[3]:.0f}, c={params[4]:.0f}, d={params[5]:.0f}\n"
    else:
        results_str += f"{segment_name}: a={params[0]:.0f}, mean={params[1]:.4f}, sigma={params[2]:.4f}, b={params[3]:.0f}\n"

print(results_str)
import pyperclip
pyperclip.copy(results_str)
    

plt.title("Updated Fitting Results for Segments", fontsize=14)
plt.xlabel("时间", fontsize=12)
plt.ylabel("数量", fontsize=12)
plt.legend()
plt.grid()
plt.show()
