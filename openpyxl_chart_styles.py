import openpyxl
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.styles import Font

# 创建一个新的工作簿和工作表
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Scatter Data"

# 填充一些示例数据
data = [
    ["X", "Y"],
    [1, 2],
    [2, 3],
    [3, 5],
    [4, 7],
    [5, 11]
]

for row in data:
    ws.append(row)

def get_chart(style_index):
    # 创建一个散点图
    chart = ScatterChart()

    # 添加数据系列
    xvalues = Reference(ws, min_col=1, min_row=2, max_row=len(data)-1)
    yvalues = Reference(ws, min_col=2, min_row=2, max_row=len(data)-1)
    series = Series(xvalues, yvalues, title="Scatter Series")
    chart.series.append(series)
    chart.style = style_index
    series.marker.symbol = "circle"
    series.marker.size = 5
    # series.graphicalProperties.line.noFill = True

    # 设置图表标题和坐标轴标题
    chart.title = "Scatter Chart Example"
    chart.x_axis.title = "X Axis"
    chart.y_axis.title = "Y Axis"

    # 设置X轴和Y轴的字体样式（可选）
    chart.x_axis.title.font = Font(name='Calibri', size=12, bold=True)
    chart.y_axis.title.font = Font(name='Calibri', size=12, bold=True)
    chart.title.font = Font(name='Calibri', size=14, bold=True)
    return chart

# 将图表添加到工作表中
for i in range(1, 49):
    ws.cell(column=4, row=(i)*10).value = i
    ws.add_chart(get_chart(i), f"E{i}0")

# 保存工作簿
wb.save("openpyxl_chart_styles.xlsx")