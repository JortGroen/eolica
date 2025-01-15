#import requests
import httpx

#lines = urllib.request.urlopen(url).read().decode().strip().split("\n")
#url = f'https://api.globalwindatlas.info/gwa3/v1/get-libfile-point?latitude=52.592999&longitude=4.752301'
lat = 48.611803
lon = 16.7412
url_newa = f'https://wps.neweuropeanwindatlas.eu/api/microscale-atlas/v1/get-data-point?latitude={lat}&longitude={lon}&height=100&variable=elevation'#&variable=rix&variable=wind_speed&variable=air_dens&variable=power_dens&variable=weib_k_combined&variable=weib_A_combined'


#response = requests.get(url_newa)

r = httpx.get(url_newa)#, params=query_parameters)


# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    print("Data received:", data)
else:
    print("Failed to retrieve data. Status code:", response.status_code)


print('done')