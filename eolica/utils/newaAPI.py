import requests
import httpx
import urllib.request
import ssl

#lines = urllib.request.urlopen(url).read().decode().strip().split("\n")
lat = 48.611803
lon = 16.7412
url_newa = f'https://wps.neweuropeanwindatlas.eu/api/microscale-atlas/v1/get-data-point?latitude={lat}&longitude={lon}&height=100&variable=elevation'#&variable=rix&variable=wind_speed&variable=air_dens&variable=power_dens&variable=weib_k_combined&variable=weib_A_combined'
#https://wps.neweuropeanwindatlas.eu/api/microscale-atlas/v1/get-data-point?latitude=52.608885&longitude=4.746872&height=100&variable=air_dens&variable=wind_speed&variable=weib_k_combined&variable=weib_A_combined
url_gwa  = f'https://api.globalwindatlas.info/gwa3/v1/get-libfile-point?latitude={lat}&longitude={lon}'

url_gwa = f'https://globalwindatlas.info/api/gwa3/v1/get-libfile-point?latitude={lat}&longitude={lon}'
url_gwa = f'https://globalwindatlas.info/api/gis/country/AUT/combined-Weibull-A/100/get-libfile-point?latitude={lat}&longitude={lon}' ## this works ...?
url_gwa = f'https://globalwindatlas.info/api/gis/global/combined-Weibull-A/100/get-libfile-point?latitude={lat}&longitude={lon}' ## this works ...?
#
response = requests.get(url_gwa)
#context = ssl.create_default_context()
#context.check_hostname = False
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

r = httpx.get(url_gwa)#, verify=context) #verify='eolica/utils/traefik_cert.pem')#, params=query_parameters)
lines = urllib.request.urlopen(url_gwa, context=context).read().decode().strip().split("\n")


# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    print("Data received:", data)
else:
    print("Failed to retrieve data. Status code:", response.status_code)


print('done')