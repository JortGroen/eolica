from eolica import EolicaPark, EolicaSimulation, EolicaDataset
import matplotlib.pyplot as plt
from utils import *


def main():
    print('[] --- eolica: hi there!')

    park = EolicaPark('parks/dummyPark.yaml')
    park.plot_turbines_powerCT()
    #print(park)

    #config_sim = 'simulations/dummyPark_weatherSeries.yaml'
    config_sim = 'simulations/dummyPark_redis.yaml'


    simulation = EolicaSimulation(park, config_fn=config_sim)
    dataset    = EolicaDataset(config_sim)
    #res = simulation.make_example_plots()
    simulation.simulate_wind_timeseries(dataset)
    #res.Power.sel(wt=1).T.plot()
    #plt.show()


    print('[] --- eolica: done!')


if __name__ == '__main__':
    main()