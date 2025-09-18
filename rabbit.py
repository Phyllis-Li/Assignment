import pandas as pd
from pyproj import Proj, transform
import plotly.graph_objects as go
import numpy as np
import plotly.express as px

# ---------------------------
# 1. 数据处理
# ---------------------------

df = pd.read_csv('PYRA Locations.csv')

proj_utm = Proj(proj='utm', zone=12, ellps='WGS84')
proj_latlon = Proj(proj='latlong', datum='WGS84')

lats = []
lons = []
for x, y in zip(df['UTMX'], df['UTMY']):
    lon, lat = transform(proj_utm, proj_latlon, x, y)
    lats.append(lat)
    lons.append(lon)

df['Latitude'] = lats
df['Longitude'] = lons
df['Timestamp'] = pd.to_datetime(df['Date'])

df_final = df[['Rabbit_ID', 'Timestamp', 'Latitude', 'Longitude']]
df_final.to_csv('rabbit_gps_data.csv', index=False)
print("CSV 文件生成完成: rabbit_gps_data.csv")

# ---------------------------
# 2. 动态轨迹可视化
# ---------------------------

df_final.sort_values(by='Timestamp', inplace=True)

time_points = df_final['Timestamp'].sort_values().unique()
rabbit_ids = df_final['Rabbit_ID'].unique()

# 使用配色
colors = px.colors.qualitative.Safe
color_map = {rid: colors[i % len(colors)] for i, rid in enumerate(rabbit_ids)}

fig = go.Figure()

# 初始化位置、轨迹
last_pos = {}
trajectory_dict = {}
first_seen = {}

for idx, rid in enumerate(rabbit_ids):
    subset = df_final[df_final['Rabbit_ID'] == rid]
    first_seen[rid] = subset['Timestamp'].min()
    x0, y0 = subset['Longitude'].iloc[0], subset['Latitude'].iloc[0]
    last_pos[rid] = (x0, y0)
    trajectory_dict[rid] = {'x': [x0], 'y': [y0]}

    # 轨迹线
    fig.add_trace(go.Scatter(
        x=[x0],
        y=[y0],
        mode='lines',
        line=dict(color=color_map[rid], width=2),  # 全部实线
        name=f'Rabbit {rid} Path',
        hoverinfo='none'
    ))
    # 兔子图标（统一 🐇）
    fig.add_trace(go.Scatter(
        x=[x0],
        y=[y0],
        mode='markers+text',
        marker=dict(size=35, color='rgba(0,0,0,0)'),
        text="🐇",
        textfont=dict(size=35),
        hovertext=[f"Rabbit ID: {rid}<br>First seen: {first_seen[rid].date()}<br>Points: 1"],
        hoverinfo='text',
        textposition='top center',
        name=f'Rabbit {rid}'
    ))

# ---------------------------
# 构建跳跃动画
# ---------------------------

jump_height = 0.0012
steps_per_jump = 5
frames = []

for i in range(len(time_points) - 1):
    t0 = time_points[i]
    t1 = time_points[i + 1]
    df1 = df_final[df_final['Timestamp'] == t1]
    if df1.empty:
        continue

    for step in range(1, steps_per_jump + 1):
        interp_ratio = step / steps_per_jump
        frame_data = []
        for idx, rid in enumerate(rabbit_ids):
            row1 = df1[df1['Rabbit_ID'] == rid]
            x, y = last_pos[rid]
            if not row1.empty:
                x1, y1 = row1['Longitude'].values[0], row1['Latitude'].values[0]
                x = last_pos[rid][0] + (x1 - last_pos[rid][0]) * interp_ratio
                y = last_pos[rid][1] + (y1 - last_pos[rid][1]) * interp_ratio
                y += np.sin(np.pi * interp_ratio) * jump_height
                if step == steps_per_jump:
                    last_pos[rid] = (x1, y1)
                trajectory_dict[rid]['x'].append(x)
                trajectory_dict[rid]['y'].append(y)
            else:
                trajectory_dict[rid]['x'].append(last_pos[rid][0])
                trajectory_dict[rid]['y'].append(last_pos[rid][1])

            # 轨迹线
            frame_data.append(go.Scatter(
                x=trajectory_dict[rid]['x'],
                y=trajectory_dict[rid]['y'],
                mode='lines',
                line=dict(color=color_map[rid], width=2),
                hoverinfo='none'
            ))
            # 兔子图标（统一 🐇）
            frame_data.append(go.Scatter(
                x=[x],
                y=[y],
                mode='markers+text',
                marker=dict(size=35, color='rgba(0,0,0,0)'),
                text="🐇",
                textfont=dict(size=35),
                hovertext=[f"Rabbit ID: {rid}<br>First seen: {first_seen[rid].date()}<br>Points: {len(trajectory_dict[rid]['x'])}"],
                hoverinfo='text',
                textposition='top center'
            ))
        frames.append(go.Frame(data=frame_data, name=f'{t0}_{step}'))

# ---------------------------
# 控件
# ---------------------------

sliders = [dict(
    steps=[dict(method='animate',
                args=[[f'{t0}_{step}'], dict(mode='immediate', frame=dict(duration=350, redraw=True), transition=dict(duration=0))],
                label=str(t0.date()))
           for t0 in time_points[:-1] for step in range(1, steps_per_jump + 1)],
    transition=dict(duration=0),
    x=0, y=0, currentvalue=dict(font=dict(size=14), prefix="Date: ", visible=True)
)]

updatemenus = [dict(type='buttons',
                    showactive=False,
                    y=1,
                    x=1.05,
                    xanchor='right',
                    yanchor='top',
                    pad=dict(t=0, r=10),
                    buttons=[dict(label='Play',
                                  method='animate',
                                  args=[None, dict(frame=dict(duration=350, redraw=True), fromcurrent=True, mode='immediate')]),
                             dict(label='Pause',
                                  method='animate',
                                  args=[[None], dict(frame=dict(duration=0, redraw=False), mode='immediate')])])]

# ---------------------------
# 布局
# ---------------------------

margin = 0.01
min_lon = df_final['Longitude'].min() - margin
max_lon = df_final['Longitude'].max() + margin
min_lat = df_final['Latitude'].min() - margin
max_lat = df_final['Latitude'].max() + margin

fig.update_layout(
    autosize=True,
    xaxis_title='Longitude',
    yaxis_title='Latitude',
    xaxis=dict(range=[min_lon, max_lon], scaleanchor="y"),
    yaxis=dict(range=[min_lat, max_lat]),
    sliders=sliders,
    updatemenus=updatemenus,
    title="🐇 美国地质局兔子动态轨迹（美化版）",
    margin=dict(l=20, r=20, t=50, b=20),
    template="plotly_white",
    paper_bgcolor="honeydew",  # 浅绿色背景
    plot_bgcolor="mintcream"
)

fig.frames = frames
fig.show()
