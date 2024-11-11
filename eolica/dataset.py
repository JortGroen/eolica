import pandas as pd

class EolicaDataset():

    def __init__(self, config):
        self.config = config
        self.df = None
        self.load_dataset()

    def load_dataset(self):
        '''
        this loads an arbitrary input csv into a somewhat standard dataset that we can use in the simulation
        '''

        infile = self.config.input_data.file

        df = pd.read_csv(infile)

        ## apply the selections from the yaml file
        for k,v in self.config.input_data.selection.items():
            df = df[df[k] == v]

        ## rename the columns to have standard feature names
        ## just need to invert the dirctionary first
        rename_dict = {v: k for k, v in self.config.input_data.features.items()}
        df = df.rename(columns = rename_dict)

        ## now just select the features we need ...
        df = df[self.config.input_data.features.keys()]

        self.df = df