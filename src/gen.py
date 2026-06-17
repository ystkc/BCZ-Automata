'''模拟打卡时间分布来生成随机数'''
import numpy as np

def exponential_with_constant(x, a, b):
    return a * np.exp(b * x)

def square_gaussian_with_constant(x, a, mean, sigma, b, c, d):
    return a * np.exp(-((x - mean) ** 2) / (2 * sigma ** 2)) + b * x ** 2 + c * x + d

# Random number generator(segments: 0 <= u <= 1)
def generate_random(n_start, n_range, segments):
    segment_weights = [0]
    cumulative_weights = [0]
    num_points =8640

    def integrate_segment(func, params, x_min, x_max, num_points, integral_sum):
        # 分成num_points段，每段的积分值
        dx = 1/num_points
        integrals = []
        cumulative_integrals = []
        x = x_min
        while x < x_max:
            integral = max(0, dx * func(x, *params)) # 保证概率值非负
            integral_sum += integral

            integrals.append(integral)
            cumulative_integrals.append(integral_sum)
            x += dx
        return integrals, cumulative_integrals

    weights_calculated = False
    for segment in segments:
        if segment.get("weights") is not None:
            segment_weights=segment["weights"]
            cumulative_weights=segment["cumulative_weights"]
            weights_calculated = True
            break
        if segment.get("integrals") is not None:
            # Use the specified weight for this segment
            integrals = segment["integrals"] # scale: 0.01
            cumulative_integrals = segment["cumulative_integrals"]
        else:
            x_min, x_max = segment["range"]
            func = segment["function"]
            params = segment["params"]
            integrals, cumulative_integrals = integrate_segment(func, params, x_min, x_max, num_points, cumulative_weights[-1])
            # segment["integrals"], segment["cumulative_integrals"] = integrals, cumulative_integrals
        segment_weights.extend(integrals)
        cumulative_weights.extend(cumulative_integrals)
    
    if not weights_calculated:
        total_integral = cumulative_weights[-1]
        segment_weights = [w / total_integral for w in segment_weights]
        cumulative_weights = [w / total_integral for w in cumulative_weights]
        # 记录
        segments[0]["weights"] = segment_weights
        segments[0]["cumulative_weights"] = cumulative_weights

    u_start = round(n_start * num_points)
    u_end = 0
    if n_start + n_range > 1:
        u_end = round((n_start + n_range - 1) * num_points)
        target_weight = segment_weights[u_start:] + segment_weights[:u_end-1]
        # print(sum(target_weight))
        target_weight_sum = cumulative_weights[u_end-2] + cumulative_weights[-1] - cumulative_weights[u_start-1]
        # print(target_weight_sum)
    else:
        u_end = round((n_start + n_range) * num_points)
        target_weight = segment_weights[u_start:u_end]
        target_weight_sum = cumulative_weights[u_end-1] - (cumulative_weights[u_start-1] if u_start > 0 else 0)
    # print(u_start, u_end)

    if target_weight_sum > 0:
        target_weight = [w / target_weight_sum for w in target_weight]  # 归一化
    else:
        raise ValueError("总权重为零，无法进行归一化。")
    target_list = np.arange(n_start, n_start+n_range, 1/num_points)[:len(target_weight)]
    return np.random.choice(a=target_list, p=target_weight)

if __name__ == "__main__":
    import datetime

    # Generate 2000 random numbers and plot their histogram
    now = datetime.datetime.combine(datetime.date.today(), datetime.time(5, 0, 0))
    today_start = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0, 0))
    time_range = 43200 # seconds


    # calc the n_start and n_range
    n_start = 21600 / 86400 # 6.5 hours
    n_range = 1800 / 86400 # 40 minutes
    results = {}
    # Predefined parameters for each segment based on your fitting results
    segments = [
        {"range": (0.0, 0.2), "function": exponential_with_constant, "params": [435, -65]},
        {"range": (0.2, 0.45), "function": square_gaussian_with_constant, "params": [888, 0.2972, 0.0205, -7624, 5541, -828]},
        {"range": (0.45, 0.65), "function": square_gaussian_with_constant, "params": [738, 0.5279, 0.0195, 746, -1003, 426]},
        {"range": (0.65, 0.85), "function": square_gaussian_with_constant, "params": [465, 0.7770, 0.0322, 22537, -27939, 8726]},
        {"range": (0.85, 1.0), "function": square_gaussian_with_constant, "params": [105, 0.9155, 0.0145, -195883, 353421, -157605]},
    ]
    for i in range(5000):
        x = int(generate_random(n_start, n_range, segments) * 86400)
        if x in results:
            results[x] += 1
        else:
            results[x] = 1


    import matplotlib.pyplot as plt
    plt.hist(list(results.keys()), bins=200, weights=list(results.values()), density=True)
    plt.show()


