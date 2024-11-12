from eolica import EolicaPark, EolicaSimulation
import matplotlib.pyplot as plt


def main():
    print('[] --- eolica: hi there!')

    park = EolicaPark('parks/dummyPark.yaml')
    park.plot_turbines_powerCT()
    #print(park)

    simulation = EolicaSimulation(park, config_fn='simulations/dummyPark_weatherSeries.yaml')
    #res = simulation.make_example_plots()
    simulation.simulate_wind_timeseries()
    #res.Power.sel(wt=1).T.plot()
    #plt.show()


    print('[] --- eolica: done!')

    ##latlongs = [utils.get_xy_from_gps(52.592999, 4.752301) ,
    ##            utils.get_xy_from_gps(52.595889, 4.753783) ,
    ##            utils.get_xy_from_gps(52.602287, 4.757099) ,
    ##            utils.get_xy_from_gps(52.605192, 4.758576) ]

    ##wt_x = [i[0] for i in latlongs]
    ##wt_y = [i[1] for i in latlongs]

    ##powers = [ 2., 2.3, 2.3, 2.3 ]

    ##hubheights = [78., 85., 85., 85.]
    ##diameter = 82.

    ##class alkmaarSite(GlobalWindAtlasSite):
    ##    def __init__(self, lat=52.592999, long=4.752301, height=78, roughness=0.5  ): ## roughness from here: https://www.wind-energy-the-facts.org/fundamentals.html
    ##        GlobalWindAtlasSite.__init__(self, lat, long, height, roughness)
    ##        self.initial_position = np.array([wt_x, wt_y]).T

    ##site = alkmaarSite()
    ##x,y = site.initial_position.T
    ##windTurbines = alkmaar2p3MW()

    ##wf_model = Bastankhah_PorteAgel_2014(site, windTurbines)

    ##sim_res = wf_model(x, y,     # wind turbine positions
    ##                   TI=0.0, ## marcc this was me
    ##                   h=None,   # wind turbine heights (defaults to the heights defined in windTurbines)
    ##                   type=0,   # Wind turbine types
    ##                   wd=None,  # Wind direction
    ##                   ws=None,  # Wind speed
    ##                  )



if __name__ == '__main__':
    main()