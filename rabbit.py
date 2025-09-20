import pandas as pd
from pyproj import Proj, transform
import plotly.graph_objects as go
import numpy as np
import plotly.express as px
import random
from datetime import datetime

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

# 使用更符合兔子主题的柔和配色
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA5A5', '#77DD77', '#FDFD96', '#84B6F4', '#FDCAE1']
# 为rabbit 561指定特定颜色（例如红色）
color_map = {}
for i, rid in enumerate(rabbit_ids):
    if rid == 561:
        color_map[rid] = '#FF0000'  # 红色
    else:
        color_map[rid] = colors[i % len(colors)]

fig = go.Figure()

# 计算地图范围并稍微放大
margin = 0.005
min_lon = df_final['Longitude'].min() - margin
max_lon = df_final['Longitude'].max() + margin
min_lat = df_final['Latitude'].min() - margin
max_lat = df_final['Latitude'].max() + margin

# 获取所有兔子的初始位置
rabbit_initial_positions = []
for rid in rabbit_ids:
    subset = df_final[df_final['Rabbit_ID'] == rid]
    x0, y0 = subset['Longitude'].iloc[0], subset['Latitude'].iloc[0]
    rabbit_initial_positions.append((x0, y0))

# 添加背景元素 - 树木和草丛
num_trees = 20
num_bushes = 30

# 存储背景元素位置
tree_positions = []
bush_positions = []

# 生成树木位置，避免与兔子初始位置重叠
for _ in range(num_trees):
    attempts = 0
    while attempts < 100:
        tree_lon = random.uniform(min_lon, max_lon)
        tree_lat = random.uniform(min_lat, max_lat)
        
        too_close = False
        for rabbit_lon, rabbit_lat in rabbit_initial_positions:
            distance = np.sqrt((tree_lon - rabbit_lon)**2 + (tree_lat - rabbit_lat)**2)
            if distance < 0.002:
                too_close = True
                break
                
        if not too_close:
            tree_positions.append((tree_lon, tree_lat))
            fig.add_trace(go.Scatter(
                x=[tree_lon],
                y=[tree_lat],
                mode='markers+text',
                marker=dict(size=0, color='rgba(0,0,0,0)'),
                text="🌳",
                textfont=dict(size=20),
                hoverinfo='none',
                showlegend=False
            ))
            break
        attempts += 1

# 生成草丛位置，避免与兔子初始位置和树木重叠
for _ in range(num_bushes):
    attempts = 0
    while attempts < 100:
        bush_lon = random.uniform(min_lon, max_lon)
        bush_lat = random.uniform(min_lat, max_lat)
        
        too_close = False
        for rabbit_lon, rabbit_lat in rabbit_initial_positions:
            distance = np.sqrt((bush_lon - rabbit_lon)**2 + (bush_lat - rabbit_lat)**2)
            if distance < 0.0015:
                too_close = True
                break
                
        if not too_close:
            for tree_lon, tree_lat in tree_positions:
                distance = np.sqrt((bush_lon - tree_lon)**2 + (bush_lat - tree_lat)**2)
                if distance < 0.001:
                    too_close = True
                    break
                    
        if not too_close:
            bush_positions.append((bush_lon, bush_lat))
            fig.add_trace(go.Scatter(
                x=[bush_lon],
                y=[bush_lat],
                mode='markers+text',
                marker=dict(size=0, color='rgba(0,0,0,0)'),
                text="🌿",
                textfont=dict(size=15),
                hoverinfo='none',
                showlegend=False
            ))
            break
        attempts += 1

# 初始化位置、轨迹
last_pos = {}
trajectory_dict = {}
first_seen = {}
point_count = {}

# 创建专门用于图例的轨迹（不可见，只用于显示图例）
legend_trace_indices = []  # 存储图例轨迹的索引
for idx, rid in enumerate(rabbit_ids):
    subset = df_final[df_final['Rabbit_ID'] == rid]
    first_seen[rid] = subset['Timestamp'].min()
    point_count[rid] = len(subset)
    x0, y0 = subset['Longitude'].iloc[0], subset['Latitude'].iloc[0]
    last_pos[rid] = (x0, y0)
    trajectory_dict[rid] = {'x': [x0], 'y': [y0]}

    # 专门用于图例的轨迹（不可见）
    fig.add_trace(go.Scatter(
        x=[None],  # 设置为None使其不可见
        y=[None],
        mode='lines',
        line=dict(color=color_map[rid], width=3),
        name=f'Rabbit {rid} 🐰',
        showlegend=True,
        hoverinfo='none'
    ))
    legend_trace_indices.append(len(fig.data) - 1)  # 记录图例轨迹的索引

    # 实际显示的轨迹线 - 移除透明度
    fig.add_trace(go.Scatter(
        x=[x0],
        y=[y0],
        mode='lines',
        line=dict(color=color_map[rid], width=3, shape='spline'),
        name=f'Rabbit {rid}',
        hoverinfo='none',
        showlegend=False,  # 不显示图例，由专门的图例轨迹处理
        opacity=1.0  # 确保完全不透明
    ))
    
    # 兔子图标
    fig.add_trace(go.Scatter(
        x=[x0],
        y=[y0],
        mode='markers+text',
        marker=dict(size=35, color='rgba(0,0,0,0)'),
        text="🐇",
        textfont=dict(size=25),
        hovertext=[f"<b>Rabbit ID: {rid}</b><br>First seen: {first_seen[rid].date()}<br>Total points: {point_count[rid]}"],
        hoverinfo='text',
        textposition='middle center',
        showlegend=False
    ))

# ---------------------------
# 构建跳跃动画
# ---------------------------

jump_height = 0.0015
steps_per_jump = 8
frames = []

# 预先创建背景元素的轨迹 - 修复瞬移问题的关键
background_traces = []
for tree_lon, tree_lat in tree_positions:
    background_traces.append(go.Scatter(
        x=[tree_lon],
        y=[tree_lat],
        mode='markers+text',
        marker=dict(size=0, color='rgba(0,0,0,0)'),
        text="🌳",
        textfont=dict(size=20),
        hoverinfo='none',
        showlegend=False
    ))
    
for bush_lon, bush_lat in bush_positions:
    background_traces.append(go.Scatter(
        x=[bush_lon],
        y=[bush_lat],
        mode='markers+text',
        marker=dict(size=0, color='rgba(0,0,0,0)'),
        text="🌿",
        textfont=dict(size=15),
        hoverinfo='none',
        showlegend=False
    ))

for i in range(len(time_points) - 1):
    t0 = time_points[i]
    t1 = time_points[i + 1]
    df1 = df_final[df_final['Timestamp'] == t1]
    if df1.empty:
        continue

    for step in range(1, steps_per_jump + 1):
        interp_ratio = step / steps_per_jump
        frame_data = []
        
        # 添加固定的背景元素到每一帧 - 修复瞬移
        frame_data.extend(background_traces)
            
        for idx, rid in enumerate(rabbit_ids):
            row1 = df1[df1['Rabbit_ID'] == rid]
            x, y = last_pos[rid]
            if not row1.empty:
                x1, y1 = row1['Longitude'].values[0], row1['Latitude'].values[0]
                x = last_pos[rid][0] + (x1 - last_pos[rid][0]) * interp_ratio
                y = last_pos[rid][1] + (y1 - last_pos[rid][1]) * interp_ratio
                y += np.sin(np.pi * interp_ratio) * jump_height * (1 + 0.2 * np.sin(np.pi * interp_ratio))
                if step == steps_per_jump:
                    last_pos[rid] = (x1, y1)
                trajectory_dict[rid]['x'].append(x)
                trajectory_dict[rid]['y'].append(y)
            else:
                trajectory_dict[rid]['x'].append(last_pos[rid][0])
                trajectory_dict[rid]['y'].append(last_pos[rid][1])

            # 轨迹线 - 移除透明度
            frame_data.append(go.Scatter(
                x=trajectory_dict[rid]['x'],
                y=trajectory_dict[rid]['y'],
                mode='lines',
                line=dict(color=color_map[rid], width=3, shape='spline'),
                hoverinfo='none',
                showlegend=False,
                opacity=1.0  # 确保完全不透明
            ))
            
            # 兔子图标
            frame_data.append(go.Scatter(
                x=[x],
                y=[y],
                mode='markers+text',
                marker=dict(size=35, color='rgba(0,0,0,0)'),
                text="🐇",
                textfont=dict(size=25),
                hovertext=[f"<b>Rabbit ID: {rid}</b><br>First seen: {first_seen[rid].date()}<br>Points: {len(trajectory_dict[rid]['x'])}"],
                hoverinfo='text',
                textposition='middle center',
                showlegend=False
            ))
        
        # 关键修复：在每一帧中都添加图例轨迹（不可见）
        for rid in rabbit_ids:
            frame_data.append(go.Scatter(
                x=[None],
                y=[None],
                mode='lines',
                line=dict(color=color_map[rid], width=3),
                name=f'Rabbit {rid} 🐰',
                showlegend=True,  # 确保图例显示
                hoverinfo='none'
            ))
            
        frames.append(go.Frame(data=frame_data, name=f'{t0}_{step}'))

# ---------------------------
# 控件
# ---------------------------

slider_steps = []
for i, t0 in enumerate(time_points[:-1]):
    for step in range(1, steps_per_jump + 1):
        slider_steps.append(dict(
            method='animate',
            args=[[f'{t0}_{step}'], dict(mode='immediate', frame=dict(duration=300, redraw=True), transition=dict(duration=0))],
            label=str(t0.date())
        ))

sliders = [dict(
    steps=slider_steps,
    transition=dict(duration=0),
    x=0.1,
    y=0, 
    currentvalue=dict(
        font=dict(size=14, family='Arial', color='#5D4037'),
        prefix="",
        visible=True,
        xanchor='left',
        offset=10
    ),
    bgcolor='rgba(232, 245, 233, 0.7)',
    bordercolor='#C8E6C9',
    borderwidth=2,
    ticklen=5,
    len=0.8
)]

updatemenus = [dict(
    type='buttons',
    showactive=False,
    y=0.02,
    x=0.98,
    xanchor='right',
    yanchor='bottom',
    pad=dict(t=10, r=10, b=10, l=10),
    bgcolor='rgba(255, 243, 224, 0.9)',
    bordercolor='#FFCC80',
    borderwidth=2,
    buttons=[
        dict(label='▶️ Play', method='animate', args=[None, dict(frame=dict(duration=300, redraw=True), fromcurrent=True, mode='immediate')]),
        dict(label='⏸️ Pause', method='animate', args=[[None], dict(frame=dict(duration=0, redraw=False), mode='immediate')])
    ]
)]

# ---------------------------
# 布局
# ---------------------------

fig.update_layout(
    autosize=True,
    xaxis_title='Longitude',
    yaxis_title='Latitude',
    xaxis=dict(range=[min_lon, max_lon], scaleanchor="y", showgrid=True, gridcolor='rgba(200, 230, 201, 0.3)', zeroline=False),
    yaxis=dict(range=[min_lat, max_lat], showgrid=True, gridcolor='rgba(200, 230, 201, 0.3)', zeroline=False),
    sliders=sliders,
    updatemenus=updatemenus,
    title=dict(text="🐇 Rabbit Activity Tracking - USGS Data", font=dict(size=24, family='Arial', color='#5D4037'), x=0.5, xanchor='center'),
    margin=dict(l=20, r=20, t=80, b=80),
    paper_bgcolor='#F1F8E9',
    plot_bgcolor='#F1F8E9',
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor='rgba(255, 255, 255, 0.7)', bordercolor='#C8E6C9', borderwidth=1, font=dict(size=12, color='#5D4037'), itemsizing='constant'),
    hoverlabel=dict(bgcolor='white', font_size=14, font_family='Arial', bordercolor='#81C784')
)

fig.add_annotation(x=0.5, y=1.05, xref="paper", yref="paper", text="Dynamic Rabbit Trajectory Tracking", showarrow=False, font=dict(size=12, color="#78909C"), xanchor="center")

fig.frames = frames

# 显示图表
fig.show()

