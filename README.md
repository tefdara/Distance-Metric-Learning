# Distance-Metric-Learning

This repository contains code for computing the Euclidean distance between sound data based on a database using dataframes. The code is written in Python and uses the pandas library for working with dataframes.

## Installation

To use this code, you will need to have Python 3 and the pandas library installed on your system. You can install pandas using pip:

```
pip install pandas
```

## Usage

To use the code, you can import the `find_n_most_similar` function from the `distance_metric_learning.py` file:

```python
from distance_metric_learning import find_n_most_similar

# Load the sound data into a pandas DataFrame
df = ...

# Find the 5 most similar sounds to sound with ID 'sound1'
most_similar = find_n_most_similar('sound1', df, metric='stats', n=5, weights={'duration': 1.0, 'amplitude': 0.5})
```

In this example, the `find_n_most_similar` function is used to find the 5 most similar sounds to the sound with ID `'sound1'`. The `df` variable is a pandas DataFrame that contains the sound data, and the `metric`, `n`, and `weights` arguments are used to specify the distance metric, the number of similar sounds to find, and the weights to use for each metric.

To generate an example database based on audio files use the `features_extractor.py`. This script uses the [Essentia](https://github.com/MTG/essentia) library to extract audio features from audio files. It takes an audio file as input and outputs a JSON file containing the extracted features.

## Configuration

The `profile.yaml` file contains configuration settings for the `features_extractor.py`. The file specifies the analysis parameters. Here's an example of what the `profile.yaml` file might look like:

```yaml
analysisSampleRate: 48000.0
outputFrames: 0
indent: 4

lowlevel:
    frameSize: 2048
    hopSize: 1024
    windowType: blackmanharris62
    silentFrames: noise
    stats: ['mean']

rhythm:
    minTempo: 40
    maxTempo: 208
    stats: ['mean']

tonal:
    frameSize: 4096
    hopSize: 2048
    windowType: blackmanharris62
    silentFrames: noise
    stats: ['mean']
```

use for computing the distance metric. 

The `metric_ops.yaml` file contains configuration settings for the distance metric operations. The file specifies the distance metric to use and any additional parameters for the metric. The `weights` setting specifies the weights to use for each column. Here's an example of what the `metric_ops.yaml` file might look like:

```yaml
n : 10
class : 'stats'
exclusive_weights : False
max_files : 10

weights :
  length : 2.0
  mfcc : 1.0
```


## Contributing

This is a very basic exmaple. If you find a bug or have a suggestion for improvement, please open an issue or submit a pull request on GitHub.

## License

This code is licensed under the GNU General Public License. See the `LICENSE` file for more information.