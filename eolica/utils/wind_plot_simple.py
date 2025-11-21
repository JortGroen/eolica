import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load the CSV file
# muehlviertel df = pd.read_csv("C:/Users/DuenserM/Downloads/Messstationen Stundendaten v2 Datensatz_19900101T0000_20241231T2300.csv")
df = pd.read_csv("C:/Users/DuenserM/Downloads/Messstationen_Ried_im_Innkreis.csv")

# Parse the time column
df['time'] = pd.to_datetime(df['time'])

# Compute the average wind direction from the three direction columns
df['wd'] = df['dd'] #df[['dd32_i', 'dd32_ii', 'dd32_iii']].mean(axis=1)

# Convert wind direction from degrees to radians (meteorological to mathematical)
angle_rad = np.deg2rad(270. - df['wd'])

# Compute U and V components of wind
df['u']  = df['ff'] * np.cos(angle_rad)
df['v']  = df['ff'] * np.sin(angle_rad)
df['ws'] = df['ff'] 

df['ws_100'] = df['ff'] * ( (150./1.) ** 0.25 )#.values[start:end]

df['ws_u']  = df['ws'] * np.cos(np.deg2rad( (270. - df['wd']) % 360 )) #.values[start:end]
df['ws_v']  = df['ws'] * np.sin(np.deg2rad( (270. - df['wd']) % 360 )) #.values[start:end]
df['ws_u_norm']  = df['ws_u'] / df['ws']
df['ws_v_norm']  = df['ws_v'] / df['ws']

# Extract day of year (1 to 366)
df['day_of_year'] = df['time'].dt.dayofyear

# Group by day of year and compute average U and V components
daily_avg = df.groupby('day_of_year')[['u', 'v', 'ff', 'ws', 'wd', 'ws_u_norm', 'ws_v_norm', 'ws_100', 'ws_u', 'ws_v', 'cglo']].mean().reset_index()

# Create a quiver plot
plt.figure(figsize=(16, 4))
x = daily_avg['day_of_year']
y = np.zeros_like(x)

#plt.quiver(x, y, daily_avg['u'], daily_avg['v'], angles='xy', scale_units='xy', scale=1, width=0.002, headwidth=2)
plt.quiver(daily_avg['day_of_year'], daily_avg['ws'], 
           daily_avg['ws_u'], daily_avg['ws_v'], 
           daily_avg['ws'], pivot="middle", cmap='gist_earth', linewidth=1.00, scale=50,width=0.0012)
plt.title("average daily wind speeds in ried im innkreis (1997–2024)")
plt.xlabel("day of year")
plt.ylabel("wind speed (m/s)")
plt.grid(True)
plt.tight_layout()
plt.savefig("C:/Users/DuenserM/Downloads/average_daily_wind_speeds_ried_im_innkreis.png", dpi=300)
plt.close()


plt.figure(figsize=(16, 4))
plt.scatter(daily_avg['day_of_year'], daily_avg['cglo'], c=daily_avg['cglo'], s=7,
            cmap='gist_earth' )
plt.title("average daily global irradiance in ried im innkreis (1997–2024)")
plt.xlabel("day of year")
plt.ylabel("global irradiance (W/m²)")
plt.grid(True)
plt.tight_layout()
plt.savefig("C:/Users/DuenserM/Downloads/average_daily_global_irradiance_ried_im_innkreis.png", dpi=300)
plt.close()

print('done')
