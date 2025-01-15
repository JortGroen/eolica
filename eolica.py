from eolica import EolicaPark, EolicaSimulation, EolicaDataset
import matplotlib.pyplot as plt
from eolica.utils import utils

def main():
    print('[] --- eolica: hi there!')

    park = EolicaPark('parks/alkmaar.yaml')
    ## plots for the park:
    ## weibull and windrose plots are made upon construction of the park
    park.plot_turbines_powerCT()       ## turbine power-ct curves
    park.plot_windpark_map()           ## schematic map of the windpark with streets
    park.plot_windpark_map_satellite() ## OSM + satellite map of the park

#url = f'https://api.globalwindatlas.info/gwa3/v1/get-libfile-point?latitude=52.592999&longitude=4.752301'
#https://wps.neweuropeanwindatlas.eu/api/microscale-atlas/v1/get-data-point?latitude=48.611803&longitude=16.7412&height=100&variable=elevation&variable=rix&variable=wind_speed&variable=air_dens&variable=power_dens&variable=weib_k_combined&variable=weib_A_combined
    config_sim = 'simulations/dummyPark_weatherSeries.yaml'
    #config_sim = 'simulations/dummyPark_redis.yaml'

    #msg = utils.load_yaml_config(config_sim)
    #msg = msg.simulation.message.data

    simulation = EolicaSimulation(park, config_fn=config_sim)
    #res = simulation.specific_ws_wd(ws=0, wd=10)
    res = simulation.make_example_plots()
    dataset    = EolicaDataset(config_sim)#, message=msg)

    sim_res = simulation.simulate_wind_timeseries(dataset)
    #res.Power.sel(wt=1).T.plot()
    #plt.show()


    print('[] --- eolica: done!')


if __name__ == '__main__':
    main()