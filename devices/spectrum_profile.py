from typing import List

import yaml


class SpectrumProfile:
    def __init__(self, **kwargs):
        self.name: str = ''
        self.colors: List[int] = []
        self.load_profile(**kwargs)

    def load_profile(self, **kwargs):
        with open('spectrum_profiles_config.yaml') as f:
            dictionary = yaml.load(f, Loader=yaml.FullLoader)
        spectrum_profiles = dictionary['spectrum_profiles']
        for profile in spectrum_profiles:
            if profile['name'] == kwargs.get('profile_name'):
                self.name = profile['name']
                self.colors = profile['colors']
                return
        raise Exception(f"Profile {kwargs.get('profile_name')} must exist - could not found the existing name.")
